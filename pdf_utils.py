import sys
from pathlib import Path
from typing import Dict, List, Tuple

from config import TEXT_PREVIEW_MAX_CHARS


def quality_flag(text: str) -> str:
    length = len((text or "").strip())
    if length < 25:
        return "Failed"
    if length < 140:
        return "Warning"
    return "Passed"


def extract_pdf_pages(file_path: Path) -> Tuple[List[Dict], List[str]]:
    """
    Extract pages from a PDF file.

    Returns a tuple of (pages, errors) where errors is a list of human-readable
    messages describing any parser failures that occurred. pages may be non-empty
    even when errors is non-empty (partial extraction via fallback).
    """
    errors: List[str] = []
    pages: List[Dict] = []

    try:
        import fitz
        document = fitz.open(str(file_path))
        for index, page in enumerate(document, start=1):
            text = page.get_text("text") or ""
            rect = page.rect
            orientation = "Landscape" if rect.width > rect.height else "Portrait"
            pages.append({
                "page_number": index,
                "text": text,
                "text_preview": text[:TEXT_PREVIEW_MAX_CHARS],
                "orientation": orientation,
                "width": rect.width,
                "height": rect.height,
            })
        document.close()
    except Exception as exc:
        msg = f"PyMuPDF extraction failed: {exc}"
        print(msg, file=sys.stderr)
        errors.append(msg)
        pages = []

    if pages:
        return pages, errors

    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                orientation = "Landscape" if page.width > page.height else "Portrait"
                pages.append({
                    "page_number": index,
                    "text": text,
                    "text_preview": text[:TEXT_PREVIEW_MAX_CHARS],
                    "orientation": orientation,
                    "width": page.width,
                    "height": page.height,
                })
    except Exception as exc:
        msg = f"pdfplumber extraction failed: {exc}"
        print(msg, file=sys.stderr)
        errors.append(msg)
        pages = []

    return pages, errors


def prepare_uploaded_file(uploaded_file, uploads_dir: Path) -> Path:
    uploads_dir.mkdir(parents=True, exist_ok=True)
    target = uploads_dir / uploaded_file.name
    target.write_bytes(uploaded_file.getbuffer())
    return target
