import shutil
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import fitz

from config import TEXT_PREVIEW_MAX_CHARS


def quality_flag(text: str) -> str:
    length = len((text or "").strip())
    if length < 25:
        return "Failed"
    if length < 140:
        return "Warning"
    return "Passed"


def normalize_rotation(rotation) -> int:
    try:
        value = int(rotation or 0) % 360
    except (TypeError, ValueError):
        return 0
    return value if value in (0, 90, 180, 270) else 0


def quality_label(text_length: int, flag: str = "") -> str:
    """Return a reviewer-facing preliminary text quality signal."""
    try:
        length = int(text_length or 0)
    except (TypeError, ValueError):
        length = 0
    if flag == "Failed" or length < 25:
        return "Poor Readability"
    if flag == "Warning" or length < 140:
        return "Low Text / Possible Scan"
    return "Readable"


OCR_TRIGGER_TEXT_LENGTH = 140
OCR_RENDER_DPI = 200
OCR_TIMEOUT_SECONDS = 15


def _usable_text_score(text: str) -> int:
    return sum(character.isalnum() for character in (text or ""))


def _ocr_page_text(page, rotation: int) -> Tuple[str, str]:
    """Render one low-text page and run bounded Tesseract OCR on the image."""
    if not shutil.which("tesseract"):
        return "", "Tesseract is not available in the current environment."
    try:
        scale = OCR_RENDER_DPI / 72
        matrix = fitz.Matrix(scale, scale)
        # Normalize the pixels with the inverse of the PDF rotation metadata.
        # This is metadata-based only; no visual orientation detection is used.
        if rotation:
            matrix = matrix.prerotate(-rotation)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        result = subprocess.run(
            ["tesseract", "stdin", "stdout", "--psm", "6"],
            input=pixmap.tobytes("png"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=OCR_TIMEOUT_SECONDS,
            check=False,
        )
        text = result.stdout.decode("utf-8", errors="replace").strip()
        if result.returncode != 0 and not text:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            return "", error or f"Tesseract exited with status {result.returncode}."
        return text, ""
    except subprocess.TimeoutExpired:
        return "", f"Tesseract timed out after {OCR_TIMEOUT_SECONDS} seconds."
    except Exception as exc:
        return "", f"OCR fallback failed: {exc}"


def _apply_ocr_fallback(page, text: str) -> Tuple[str, str, str, str, str]:
    """Return effective text plus original/OCR text and source label."""
    original_text = text or ""
    ocr_text = ""
    extraction_source = "Text Layer"
    if len(original_text.strip()) >= OCR_TRIGGER_TEXT_LENGTH:
        return original_text, original_text, ocr_text, extraction_source, ""

    rotation = normalize_rotation(getattr(page, "rotation", 0))
    ocr_text, ocr_error = _ocr_page_text(page, rotation)
    if _usable_text_score(ocr_text) > _usable_text_score(original_text):
        return ocr_text, original_text, ocr_text, "OCR Fallback", ocr_error
    return original_text, original_text, ocr_text, extraction_source, ocr_error


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
            effective_text, original_text, ocr_text, extraction_source, ocr_error = _apply_ocr_fallback(page, text)
            if ocr_error:
                errors.append(f"Page {index} OCR fallback issue: {ocr_error}")
            rect = page.rect
            orientation = "Landscape" if rect.width > rect.height else "Portrait"
            pages.append({
                "page_number": index,
                "text": effective_text,
                "text_preview": effective_text[:TEXT_PREVIEW_MAX_CHARS],
                "original_text": original_text,
                "ocr_text": ocr_text,
                "extraction_source": extraction_source,
                "orientation": orientation,
                "rotation_degrees": normalize_rotation(getattr(page, "rotation", 0)),
                "text_length": len(effective_text.strip()),
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
                "original_text": text,
                "ocr_text": "",
                "extraction_source": "Text Layer",
                    "orientation": orientation,
                    "rotation_degrees": normalize_rotation(getattr(page, "rotation", 0)),
                    "text_length": len(text.strip()),
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
