import json
from pathlib import Path
from typing import Dict, List, Optional

from config import COMPANY_MASTER_PATH, DEMO_DATA_PATH, REVERT_REASONS_PATH, UPLOADS_DIR
from db import (
    delete_document_records,
    execute,
    insert_document,
    query,
    replace_document_analysis,
    save_reviewer_action,
)


def load_json(path: Path):
    return json.loads(path.read_text())


def load_demo_data() -> Dict:
    return load_json(DEMO_DATA_PATH)


def load_company_master() -> Dict:
    return load_json(COMPANY_MASTER_PATH)


def load_revert_reasons() -> List[str]:
    return load_json(REVERT_REASONS_PATH)


def demo_document_filenames() -> set:
    """Return filenames from the configured demo suite, not display names."""
    demo = load_demo_data()
    suite = demo.get("demo_suite", [])
    if suite:
        return {entry["metadata"]["filename"] for entry in suite}
    return {demo["demo_document"]["filename"]}


def is_demo_document(document: Dict) -> bool:
    return str(document.get("filename") or "") in demo_document_filenames()


def document_analysis_summary(document_id: int) -> str:
    """Build a compact status/recommendation label for the upload-management list."""
    validations = get_validations(document_id)
    status_priority = ("Failed", "Warning", "Needs Review", "Passed")
    statuses = {str(row.get("status") or "") for row in validations}
    analysis_status = next((status for status in status_priority if status in statuses), "")
    actions = get_reviewer_actions(document_id)
    recommendation = str(actions[0].get("final_recommendation") or "") if actions else ""
    values = [value for value in (analysis_status, recommendation) if value]
    return " / ".join(values) if values else "—"


def delete_test_document(document_id: int) -> Dict:
    """
    Delete a non-demo document and its dependent data.

    The stored filename is the only current association between a document and
    its local upload. A same-named document keeps the file from being removed.
    """
    document = get_document(document_id)
    if not document:
        return {"deleted": False, "reason": "Document not found."}
    if is_demo_document(document):
        return {"deleted": False, "reason": "Seeded demo documents are protected."}

    filename = str(document.get("filename") or "")
    referenced_elsewhere = bool(
        query(
            "SELECT id FROM documents WHERE filename = ? AND id != ? LIMIT 1",
            (filename, document_id),
        )
    )
    local_file = UPLOADS_DIR / Path(filename).name if filename else None
    if not delete_document_records(document_id):
        return {"deleted": False, "reason": "Document could not be deleted."}

    file_removed = False
    file_cleanup_warning = ""
    if local_file and not referenced_elsewhere and local_file.is_file():
        try:
            local_file.unlink()
            file_removed = True
        except OSError:
            file_cleanup_warning = "The analysis data was deleted, but the local PDF could not be removed."
    return {
        "deleted": True,
        "file_removed": file_removed,
        "file_cleanup_warning": file_cleanup_warning,
    }


def seed_company_master() -> None:
    master = load_company_master()
    existing = query("SELECT id FROM company_master WHERE sec_registration_no = ?", (master.get("sec_registration_no"),))
    if existing:
        return
    execute(
        "INSERT INTO company_master (company_name, sec_registration_no, period_covered_year, comparative_years) VALUES (?, ?, ?, ?)",
        (master.get("company_name"), master.get("sec_registration_no"), master.get("period_covered_year"), ", ".join(str(x) for x in master.get("comparative_years", []))),
    )


def _seed_one_demo_document(entry: Dict) -> int:
    """
    Seed a single demo suite entry. Guards against overwriting existing analysis
    data or reviewer actions so that reviewer work survives restarts.
    Returns the document_id.
    """
    metadata = entry["metadata"]
    existing = query(
        "SELECT id FROM documents WHERE filename = ? ORDER BY id DESC LIMIT 1",
        (metadata["filename"],),
    )
    if existing:
        document_id = existing[0]["id"]
        has_analysis = query(
            "SELECT 1 FROM page_analysis WHERE document_id = ? LIMIT 1",
            (document_id,),
        )
        if has_analysis:
            return document_id
    else:
        document_id = insert_document(metadata)

    pages = []
    for page in entry["pages"]:
        text = page["text_preview"]
        pages.append({
            **page,
            "detected_company_match": metadata["company_name"].replace(",", "")[:18].lower()
                in text.replace(",", "").lower(),
            "detected_period_match": str(metadata["period_covered_year"]) in text,
        })
    replace_document_analysis(document_id, pages, entry["validations"], entry["figures"])

    existing_action = query(
        "SELECT id FROM reviewer_actions WHERE document_id = ?", (document_id,)
    )
    if not existing_action:
        save_reviewer_action(
            document_id,
            entry.get("default_remarks", ""),
            entry.get("default_recommendation", "Needs Review"),
            entry.get("default_revert_reason", ""),
        )

    return document_id


def ensure_demo_document() -> int:
    """Seed the primary demo document (Audentia Fortuna). Kept for backward compat."""
    demo = load_demo_data()
    suite = demo.get("demo_suite", [])
    if suite:
        return _seed_one_demo_document(suite[0])
    metadata = demo["demo_document"]
    existing = query(
        "SELECT id FROM documents WHERE filename = ? ORDER BY id DESC LIMIT 1",
        (metadata["filename"],),
    )
    if existing:
        document_id = existing[0]["id"]
        has_analysis = query(
            "SELECT 1 FROM page_analysis WHERE document_id = ? LIMIT 1", (document_id,)
        )
        if has_analysis:
            return document_id
    else:
        document_id = insert_document(metadata)
    pages = []
    for page in demo["sample_pages"]:
        text = page["text_preview"]
        pages.append({
            **page,
            "detected_company_match": metadata["company_name"].replace(",", "")[:18].lower()
                in text.replace(",", "").lower(),
            "detected_period_match": str(metadata["period_covered_year"]) in text,
        })
    replace_document_analysis(document_id, pages, demo["sample_validations"], demo["sample_figures"])
    return document_id


def ensure_all_demo_documents() -> int:
    """
    Seed all documents in demo_suite. Each document is only seeded once;
    subsequent calls are no-ops if analysis data already exists.
    Reviewer actions are also seeded once and never overwritten on restart.
    Returns the ID of the first (primary) demo document.
    """
    demo = load_demo_data()
    suite = demo.get("demo_suite", [])
    if not suite:
        return ensure_demo_document()
    first_id = None
    for entry in suite:
        doc_id = _seed_one_demo_document(entry)
        if first_id is None:
            first_id = doc_id
    return first_id


def get_document(document_id: Optional[int]) -> Optional[Dict]:
    if not document_id:
        return None
    rows = query("SELECT * FROM documents WHERE id = ?", (document_id,))
    return rows[0] if rows else None


def get_documents() -> List[Dict]:
    return query("SELECT * FROM documents ORDER BY uploaded_at DESC, id DESC")


def get_pages(document_id: int) -> List[Dict]:
    return query(
        "SELECT * FROM page_analysis WHERE document_id = ? ORDER BY page_number",
        (document_id,),
    )


def get_validations(document_id: int) -> List[Dict]:
    return query(
        "SELECT * FROM validations WHERE document_id = ? ORDER BY id",
        (document_id,),
    )


def get_figures(document_id: int) -> List[Dict]:
    return query(
        "SELECT * FROM extracted_figures WHERE document_id = ? ORDER BY page_number, normalized_label, fiscal_year DESC",
        (document_id,),
    )


def get_reviewer_actions(document_id: int) -> List[Dict]:
    return query(
        "SELECT * FROM reviewer_actions WHERE document_id = ? ORDER BY updated_at DESC",
        (document_id,),
    )
