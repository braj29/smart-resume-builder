import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import gradio as gr

from llm.pipeline import run_pipeline
from render.latex import compile_to_tempfile, latexmk_available
from render.templates import list_templates, render_template
from resume_parser.parser import parse_resume_pdf
from schemas.resume import TailoredResume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_resume_builder")

APP_TITLE = "Smart Resume Builder"
LOCAL_KEY_PATH = Path.home() / ".smart_resume_builder_key"


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


def clear_api_key() -> str:
    try:
        import keyring  # type: ignore

        keyring.delete_password(APP_TITLE, "api_key")
    except Exception:
        pass
    if LOCAL_KEY_PATH.exists():
        LOCAL_KEY_PATH.unlink()
    return ""


def _render_latex_from_tailored(tailored: TailoredResume, template_choice: str) -> str:
    context = tailored.tailored_resume.dict()
    return render_template(template_choice, context)


def _extract_pdf_bytes(pdf_file) -> bytes:
    """Support both file objects and filepath strings from Gradio."""
    if pdf_file is None:
        raise ValueError("No PDF uploaded.")
    # type="binary" returns bytes directly
    if isinstance(pdf_file, (bytes, bytearray)):
        return bytes(pdf_file)
    # When type="file", Gradio returns a file-like object with .read()
    if hasattr(pdf_file, "read"):
        return pdf_file.read()
    # Some environments provide a str path instead.
    if isinstance(pdf_file, str) and Path(pdf_file).exists():
        return Path(pdf_file).read_bytes()
    raise ValueError("Unsupported PDF input; please re-upload the file.")


def generate_tailored_resume(
    job_description: str,
    pdf_file,
    api_key: str,
    model: str,
    template_choice: str,
    save_key: bool,
) -> Tuple[str, str, str, str, str, Optional[str], Optional[str], str]:
    logs = []

    def log(msg: str):
        logs.append(msg)

    if not api_key:
        return ("", "API key required.", "", {}, "\n".join(logs), None, None, {})
    if not pdf_file:
        return ("", "Please upload a resume PDF.", "", {}, "\n".join(logs), None, None, {})
    if not job_description.strip():
        return ("", "Job description required.", "", {}, "\n".join(logs), None, None, {})

    if save_key:
        save_api_key(api_key)

    try:
        pdf_bytes = _extract_pdf_bytes(pdf_file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            pdf_path = Path(tmp.name)
        result = parse_resume_pdf(str(pdf_path))
        log(f"Extracted text using {result.method}")
        log("Starting OpenAI pipeline...")

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
        log("LLM pipeline complete.")

        rendered_latex = _render_latex_from_tailored(tailored, template_choice)
        tailored.latex_content = rendered_latex
        tex_file_path: Optional[str] = None
        pdf_file_path: Optional[str] = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tex") as tex_tmp:
            tex_tmp.write(rendered_latex.encode("utf-8"))
            tex_file_path = tex_tmp.name

        if latexmk_available():
            try:
                pdf_out = compile_to_tempfile(rendered_latex)
                if pdf_out:
                    pdf_file_path = str(pdf_out)
            except Exception as exc:  # pragma: no cover - external tool
                log(f"latexmk failed: {exc}")
        else:
            log("latexmk not installed; PDF export disabled.")

        missing_text = "\n".join(tailored.missing_items) or "None"
        questions_text = "\n".join(tailored.questions) or "None"

        return (
            rendered_latex,
            missing_text,
            questions_text,
            json.dumps(tailored.keyword_alignment.dict(), indent=2),
            "\n".join(logs),
            tex_file_path,
            pdf_file_path,
            resume.json(indent=2),
        )
    except Exception as exc:
        log(f"Error: {exc}")
        log(
            "If this persists, verify your OpenAI API key/model and that outbound network access is allowed."
        )
        return ("", f"An error occurred: {exc}", "", {}, "\n".join(logs), None, None, {})


def build_ui():
    stored_key = load_api_key() or ""
    templates = list_templates()
    template_names = list(templates.keys()) or ["modern"]

    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown(f"# {APP_TITLE}\nTailor resumes with grounded extraction and LaTeX rendering.")
        with gr.Row():
            with gr.Column():
                jd = gr.Textbox(label="Job Description", lines=12, placeholder="Paste JD here")
                api = gr.Textbox(label="OpenAI API Key", type="password", value=stored_key)
                save_key = gr.Checkbox(label="Save key locally (keyring preferred)", value=bool(stored_key))
                model = gr.Textbox(label="Model name", value="gpt-4o-mini")
                template_choice = gr.Dropdown(
                    label="Template", choices=template_names, value=template_names[0]
                )
                clear_btn = gr.Button("Clear stored key")
            with gr.Column():
                pdf = gr.File(label="Upload Resume PDF", file_types=[".pdf"], type="binary")
                logs_box = gr.Textbox(label="Logs", lines=10, interactive=False)

        generate_btn = gr.Button("Generate Tailored Resume")
        latex_preview = gr.Code(label="LaTeX Output", language="markdown")
        missing_panel = gr.Textbox(label="Missing / Needs Confirmation", lines=6)
        questions_panel = gr.Textbox(label="Questions for user", lines=4)
        keyword_alignment = gr.Textbox(label="Keyword alignment", lines=6)
        resume_json = gr.Textbox(label="Resume JSON (parsed)", lines=10)
        tex_download = gr.File(label="Export .tex")
        pdf_download = gr.File(label="Export PDF (requires latexmk)")

        generate_btn.click(
            fn=generate_tailored_resume,
            inputs=[jd, pdf, api, model, template_choice, save_key],
            outputs=[
                latex_preview,
                missing_panel,
                questions_panel,
                keyword_alignment,
                logs_box,
                tex_download,
                pdf_download,
                resume_json,
            ],
        )

        clear_btn.click(fn=clear_api_key, inputs=None, outputs=api)

    return demo


if __name__ == "__main__":
    app = build_ui()
    # On Spaces, share=False is preferred; HF handles routing.
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
    )
