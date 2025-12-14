from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def latexmk_available() -> bool:
    return shutil.which("latexmk") is not None


def compile_latex(latex_content: str, output_dir: Path, output_basename: str) -> Path:
    """
    Compile LaTeX content using latexmk. Raises if latexmk is missing.
    """
    if not latexmk_available():
        raise RuntimeError("latexmk is not installed. Install TeX Live or MikTeX.")

    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / f"{output_basename}.tex"
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)

    # Run latexmk quietly.
    subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", tex_path.name],
        cwd=output_dir,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pdf_path = output_dir / f"{output_basename}.pdf"
    return pdf_path


def compile_to_tempfile(latex_content: str) -> Optional[Path]:
    if not latexmk_available():
        return None
    tmpdir = Path(tempfile.mkdtemp(prefix="resume_tailor_"))
    try:
        return compile_latex(latex_content, tmpdir, "tailored_resume")
    except subprocess.CalledProcessError as exc:  # pragma: no cover - external tool
        logger.error("latexmk failed: %s", exc.stderr)
        raise
