from pathlib import Path
from typing import Dict, List


def extract_pdf_pages(file_path: Path) -> List[Dict]:
    pages = []
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
                "text_preview": text[:1200],
                "orientation": orientation,
                "width": rect.width,
                "height": rect.height,
            })
        document.close()
    except Exception:
        pages = []
    if pages:
        return pages
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                orientation = "Landscape" if page.width > page.height else "Portrait"
                pages.append({
                    "page_number": index,
                    "text": text,
                    "text_preview": text[:1200],
                    "orientation": orientation,
                    "width": page.width,
                    "height": page.height,
                })
    except Exception:
        pages = []
    return pages


def quality_flag(text: str) -> str:
    length = len((text or "").strip())
    if length < 25:
        return "Failed"
    if length < 140:
        return "Warning"
    return "Passed"


def prepare_uploaded_file(uploaded_file, uploads_dir: Path) -> Path:
    uploads_dir.mkdir(parents=True, exist_ok=True)
    target = uploads_dir / uploaded_file.name
    target.write_bytes(uploaded_file.getbuffer())
    return target
