import json
import logging
import os
from pathlib import Path
from typing import Optional

import streamlit as st

from llm.pipeline import run_pipeline
from render.latex import compile_to_tempfile, latexmk_available
from render.templates import list_templates, render_template
from resume_parser.parser import parse_resume_pdf
from schemas.resume import Resume, TailoredResume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume_tailor")

APP_TITLE = "ResumeTailor"
LOCAL_KEY_PATH = Path.home() / ".resume_tailor_key"


def load_api_key() -> Optional[str]:
    try:
        import keyring  # type: ignore

        return keyring.get_password(APP_TITLE, "api_key")
    except Exception:
        if LOCAL_KEY_PATH.exists():
            try:
                return LOCAL_KEY_PATH.read_text().strip()
            except Exception:
                return None
    return None


def save_api_key(key: str) -> None:
    try:
        import keyring  # type: ignore

        keyring.set_password(APP_TITLE, "api_key", key)
        return
    except Exception:
        LOCAL_KEY_PATH.write_text(key)


def clear_api_key() -> None:
    try:
        import keyring  # type: ignore

        keyring.delete_password(APP_TITLE, "api_key")
    except Exception:
        pass
    if LOCAL_KEY_PATH.exists():
        LOCAL_KEY_PATH.unlink()


def ensure_state():
    st.session_state.setdefault("latex_content", "")
    st.session_state.setdefault("resume_json", {})
    st.session_state.setdefault("tailored", None)
    st.session_state.setdefault("raw_text", "")
    st.session_state.setdefault("logs", [])


def log(message: str):
    st.session_state.logs.append(message)
    st.session_state.logs = st.session_state.logs[-8:]


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    ensure_state()

    st.title(APP_TITLE)
    st.write("Generate tailored resumes with grounded extraction and LaTeX rendering.")

    stored_key = load_api_key()
    col1, col2 = st.columns(2)
    with col1:
        job_description = st.text_area("Job Description", height=220)
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=stored_key or "",
            help="Stored securely via system keychain when available.",
        )
        save_key = st.checkbox("Save locally", value=bool(stored_key))
        model = st.text_input("Model name", value="gpt-4o-mini")
        template_names = list(list_templates().keys())
        template_choice = st.selectbox(
            "Template", options=template_names, index=0 if template_names else 0
        )
        if st.button("Clear stored key"):
            clear_api_key()
            st.success("Stored key cleared.")
    with col2:
        uploaded_file = st.file_uploader("Upload Resume PDF", type=["pdf"])
        st.markdown("**Output Preview**")
        st.code(st.session_state.get("latex_content", ""), language="latex")
        st.markdown("**Logs**")
        st.text("\n".join(st.session_state.get("logs", [])))

    if st.button("Generate Tailored Resume"):
        if not api_key:
            st.error("API key required.")
            return
        if not uploaded_file:
            st.error("Please upload a resume PDF.")
            return
        if not job_description.strip():
            st.error("Job description required.")
            return

        if save_key:
            save_api_key(api_key)

        with st.spinner("Parsing resume PDF..."):
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_pdf = Path(tmp.name)

            result = parse_resume_pdf(str(temp_pdf))
            st.session_state["raw_text"] = result.raw_text
            log(f"Extracted text using {result.method}")

        with st.spinner("Running LLM pipeline..."):
            template_map = list_templates()
            template_source = template_map[template_choice].read_text(encoding="utf-8")
            resume, tailored = run_pipeline(
                api_key=api_key,
                model=model,
                raw_text=result.raw_text,
                job_description=job_description,
                template_name=template_choice,
                template_source=template_source,
            )
            st.session_state["resume_json"] = json.loads(resume.json())
            st.session_state["tailored"] = tailored

            context = tailored.tailored_resume.dict()
            rendered = render_template(template_choice, context)
            tailored.latex_content = rendered
            st.session_state["latex_content"] = rendered
            log("Pipeline completed.")

    tailored: TailoredResume = st.session_state.get("tailored")
    resume_data = st.session_state.get("resume_json")

    if tailored:
        st.subheader("Missing / Needs Confirmation")
        st.write(tailored.missing_items or ["None"])

        st.subheader("Questions for user")
        st.write(tailored.questions or ["None"])

        st.subheader("Keyword alignment")
        st.json(tailored.keyword_alignment.dict())

    col_export1, col_export2 = st.columns(2)
    with col_export1:
        if st.session_state.get("latex_content"):
            st.download_button(
                "Export .tex",
                data=st.session_state["latex_content"],
                file_name="tailored_resume.tex",
                mime="application/x-tex",
            )
    with col_export2:
        if st.session_state.get("latex_content"):
            if latexmk_available():
                pdf_path = compile_to_tempfile(st.session_state["latex_content"])
                if pdf_path and pdf_path.exists():
                    st.download_button(
                        "Export PDF",
                        data=pdf_path.read_bytes(),
                        file_name="tailored_resume.pdf",
                        mime="application/pdf",
                    )
            else:
                st.info("latexmk not installed. PDF export disabled. See README.")

    st.subheader("Generated LaTeX")
    st.code(st.session_state.get("latex_content", ""), language="latex")

    st.subheader("Resume JSON")
    if resume_data:
        st.json(resume_data)
    else:
        st.text("Run the pipeline to view parsed resume JSON.")


if __name__ == "__main__":
    main()
