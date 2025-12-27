---
title: Smart Resume Builder
emoji: 📄
colorFrom: gray
colorTo: blue
sdk: gradio
sdk_version: "4.44.1"
app_file: app.py
pinned: false
license: mit
---

# Smart Resume Builder

Generate grounded, tailored resumes from a job description and a PDF resume using Gradio, OpenAI or Hugging Face models, and LaTeX templates. Suitable for local runs or Hugging Face Spaces. 

## Features
- PDF parsing with `pdfplumber` and `pymupdf` fallback
- Strict, evidence-backed JSON extraction via OpenAI or Hugging Face router (OpenAI-compatible)
- Tailoring step that rewrites bullets without fabrication and reports missing items
- Two LaTeX templates (modern single-column and classic two-column)
- Streamlit UI with API key storage (keyring preferred), template selector, and export buttons
- Keyword alignment and missing/needs-confirmation panel

## Quickstart (local with uv)
```bash
# install uv if needed: curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv
uv pip install -r requirements.txt
uv run app.py
```

## Using the app
1. Paste the job description.
2. Upload a resume PDF.
3. Pick a provider and enter your API key/token (optionally save it locally; system keychain is used when available).
4. Choose a model name and LaTeX template.
5. Click **Generate Tailored Resume**.
6. Review the LaTeX preview, missing/needs-confirmation list, and keyword alignment.
7. Export `.tex` or PDF. PDF export requires `latexmk`.

## Docker
```bash
make docker-build
make docker-run PORT=7860
```
Then open http://localhost:7860.

## LaTeX compilation
- PDF export uses `latexmk -pdf`. Install TeX Live or MikTeX and ensure `latexmk` is on your PATH.
- If `latexmk` is missing, PDF export is disabled but `.tex` export works.

## Security notes
- API keys are stored via `keyring` when available; otherwise a local fallback file `~/.smart_resume_builder_key` is used.
- Keys are never written to logs.
- Use the **Clear stored key** button to remove saved credentials.

## Tests
```bash
uv run pytest
```

## Troubleshooting
- Missing `latexmk`: install TeX Live/MikTeX.
- If PDF parsing is poor, ensure the resume PDF is text-based; image-only scans are harder to extract.
- For provider errors, verify the API key/token and model name in the UI.
