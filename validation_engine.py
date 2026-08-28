import re
from difflib import SequenceMatcher
from typing import Dict, List

from config import TEXT_PREVIEW_MAX_CHARS
from pdf_utils import quality_flag

REQUIRED_SECTIONS = [
    "Statement of Management's Responsibility",
    "Independent Auditor's Report",
    "Statement of Financial Position / Balance Sheet",
    "Statement of Income / Receipts and Expenses",
    "Statement of Comprehensive Income",
    "Statement of Changes in Equity / Fund Balance",
    "Statement of Cash Flows",
    "Notes to Financial Statements",
]

PAGE_RULES = [
    ("Statement of Management's Responsibility", ["management", "responsibility", "financial statements"]),
    ("Cover Sheet", ["cover sheet", "sec registration", "company information"]),
    ("Independent Auditor's Report", ["independent auditor", "we have audited", "auditor's report", "auditor\u2019s report"]),
    ("Statement of Financial Position / Balance Sheet", ["financial position", "balance sheet", "total assets", "total liabilities"]),
    ("Statement of Income / Receipts and Expenses", ["statement of income", "receipts and expenses", "net income", "gross revenue"]),
    ("Statement of Comprehensive Income", ["comprehensive income", "other comprehensive"]),
    ("Statement of Changes in Equity / Fund Balance", ["changes in equity", "fund balance", "retained earnings"]),
    ("Statement of Cash Flows", ["cash flows", "operating activities", "financing activities"]),
    ("Notes to Financial Statements", ["notes to financial statements", "summary of significant accounting", "basis of preparation"]),
]


def simplify_name(value: str) -> str:
    value = value.lower()
    value = value.replace("corporation", "corp").replace("corp.", "corp")
    value = value.replace("incorporated", "inc").replace("inc.", "inc")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fuzzy_company_match(source: str, target: str) -> bool:
    source_clean = simplify_name(source)
    target_clean = simplify_name(target)
    if target_clean in source_clean:
        return True
    words = target_clean.split()
    if len(words) >= 3 and all(word in source_clean for word in words[:3]):
        return True
    return SequenceMatcher(None, source_clean, target_clean).ratio() >= 0.74


def classify_page(text: str) -> str:
    lowered = (text or "").lower()
    for page_type, keywords in PAGE_RULES:
        if any(keyword in lowered for keyword in keywords):
            return page_type
    return "Other / Unclassified"


def has_period(text: str, year: int) -> bool:
    return str(year) in (text or "")


def analyze_pages(raw_pages: List[Dict], metadata: Dict, company_master: Dict) -> List[Dict]:
    analyzed = []
    company_name = metadata.get("company_name") or company_master.get("company_name", "")
    period_year = int(metadata.get("period_covered_year") or company_master.get("period_covered_year", 0))
    for page in raw_pages:
        text = page.get("text") or page.get("text_preview") or ""
        page_type = page.get("page_type") or classify_page(text)
        flag = page.get("image_quality_flag") or quality_flag(text)
        text_length = page.get("text_length")
        if text_length is None:
            text_length = len(text.strip())
        analyzed.append({
            "page_number": page.get("page_number"),
            "page_type": page_type,
            "orientation": page.get("orientation", "Portrait"),
            "text_preview": page.get("text_preview") or text[:TEXT_PREVIEW_MAX_CHARS],
            "detected_company_match": fuzzy_company_match(text, company_name),
            "detected_period_match": has_period(text, period_year),
            "image_quality_flag": flag,
            "rotation_degrees": page.get("rotation_degrees", page.get("rotation", 0)) or 0,
            "text_length": text_length,
        })
    return analyzed


def validate_document(pages: List[Dict], metadata: Dict, company_master: Dict) -> List[Dict]:
    all_text = "\n".join(page.get("text_preview", "") for page in pages)
    page_types = {page.get("page_type") for page in pages}
    validations = []
    company_ok = fuzzy_company_match(all_text, company_master.get("company_name", "")) and company_master.get("sec_registration_no", "") in all_text
    validations.append({
        "rule_name": "Company master data match",
        "status": "Passed" if company_ok else "Failed",
        "message": "Company name and SEC registration number align with master record." if company_ok else "Company name or SEC registration number needs reviewer confirmation.",
        "suggested_revert_reason": "" if company_ok else "Wrong company profile",
    })
    year = int(metadata.get("period_covered_year") or company_master.get("period_covered_year", 0))
    priority_pages = [page for page in pages if page.get("page_type") in ["Independent Auditor's Report", "Statement of Management's Responsibility", "Notes to Financial Statements"]]
    period_ok = any(str(year) in page.get("text_preview", "") for page in priority_pages) or str(year) in all_text
    validations.append({
        "rule_name": "AFS period covered",
        "status": "Passed" if period_ok else "Failed",
        "message": f"Priority pages support period covered {year}." if period_ok else f"Priority pages do not clearly support period covered {year}.",
        "suggested_revert_reason": "" if period_ok else "Wrong period covered",
    })
    submission_ok = "financial statements" in all_text.lower() or metadata.get("report_type") == "AFS"
    validations.append({
        "rule_name": "Submission type",
        "status": "Passed" if submission_ok else "Failed",
        "message": "Document content is consistent with Annual Financial Statements." if submission_ok else "Submission type is not clearly consistent with AFS.",
        "suggested_revert_reason": "" if submission_ok else "Wrong submission type",
    })
    landscape_pages = [page for page in pages if page.get("orientation") == "Landscape"]
    validations.append({
        "rule_name": "Orientation review",
        "status": "Warning" if landscape_pages else "Passed",
        "message": f"{len(landscape_pages)} landscape page(s) detected; review if these are legitimate wide financial tables." if landscape_pages else "No landscape pages detected.",
        "suggested_revert_reason": "Wrong page orientation" if landscape_pages else "",
    })
    rotated_pages = [
        page for page in pages
        if int(page.get("rotation_degrees") or 0) in (90, 180, 270)
    ]
    validations.append({
        "rule_name": "Rotation metadata review",
        "status": "Warning" if rotated_pages else "Passed",
        "message": (
            f"Rotation metadata detected on {len(rotated_pages)} page(s); reviewer confirmation is required."
            if rotated_pages
            else "No non-zero PDF rotation metadata detected."
        ),
        "suggested_revert_reason": "",
    })
    missing = [section for section in REQUIRED_SECTIONS if section not in page_types]
    validations.append({
        "rule_name": "Completeness check",
        "status": "Passed" if not missing else "Warning",
        "message": "All key AFS sections are detected." if not missing else "Missing or not separately detected: " + ", ".join(missing[:4]),
        "suggested_revert_reason": "" if not missing else "Incomplete pages",
    })
    quality_failed = [page for page in pages if page.get("image_quality_flag") == "Failed"]
    validations.append({
        "rule_name": "Image readability",
        "status": "Failed" if quality_failed else "Passed",
        "message": f"{len(quality_failed)} page(s) have very low extracted text." if quality_failed else "Extracted text is adequate for MVP review.",
        "suggested_revert_reason": "Poor image quality" if quality_failed else "",
    })
    return validations


def final_recommendation(validations: List[Dict]) -> str:
    statuses = [item.get("status") for item in validations]
    if "Failed" in statuses:
        return "Revert"
    if "Warning" in statuses:
        return "Needs Review"
    return "Accept"


def suggested_revert_reason(validations: List[Dict]) -> str:
    for item in validations:
        if item.get("suggested_revert_reason"):
            return item["suggested_revert_reason"]
    return ""
