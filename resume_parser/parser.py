from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ResumeParseResult:
    raw_text: str
    method: str
    metadata: Optional[dict] = None


def _extract_with_pdfplumber(path: str) -> Optional[str]:
    try:
        import pdfplumber
    except Exception as exc:  # pragma: no cover - import guard
        logger.info("pdfplumber unavailable: %s", exc)
        return None

    try:
        text_chunks = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text_chunks.append(page.extract_text() or "")
        text = "\n".join(text_chunks).strip()
        return text or None
    except Exception as exc:  # pragma: no cover - safety
        logger.warning("pdfplumber failed, will fallback: %s", exc)
        return None


def _extract_with_pymupdf(path: str) -> Optional[str]:
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        logger.info("pymupdf unavailable: %s", exc)
        return None

    try:
        doc = fitz.open(path)
        text_chunks = [page.get_text() for page in doc]
        text = "\n".join(text_chunks).strip()
        return text or None
    except Exception as exc:  # pragma: no cover - safety
        logger.warning("pymupdf failed: %s", exc)
        return None


def parse_resume_pdf(path: str) -> ResumeParseResult:
    """
    Extract resume text preferring pdfplumber first, then falling back to pymupdf.
    """
    text = _extract_with_pdfplumber(path)
    method_used = "pdfplumber"

    if not text or _is_low_quality(text):
        fallback_text = _extract_with_pymupdf(path)
        if fallback_text:
            text = fallback_text
            method_used = "pymupdf"

    if not text:
        raise ValueError("Unable to extract text from PDF with available extractors")

    return ResumeParseResult(raw_text=text, method=method_used, metadata={"path": path})


def _is_low_quality(text: str) -> bool:
    # Basic heuristic: very few unique words implies extraction failed.
    words = [w for w in text.split() if w.isalpha()]
    unique_ratio = len(set(words)) / max(len(words), 1)
    return unique_ratio < 0.15 or len(text) < 100
