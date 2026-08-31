import re
from difflib import SequenceMatcher
from typing import Dict, List

from config import TEXT_PREVIEW_MAX_CHARS
from pdf_utils import quality_flag

AFS_COMPONENT_DEFINITIONS = [
    {
        "name": "Statement of Management's Responsibility",
        "page_types": {"statement of management's responsibility"},
        "strong": [
            r"statement\s+of\s+management(?:'|’)?s?\s+responsibility",
            r"management(?:'|’)?s?\s+responsibility",
        ],
        "weak": [r"\bresponsibility\b"],
    },
    {
        "name": "Independent Auditor's Report",
        "page_types": {"independent auditor's report"},
        "strong": [
            r"independent\s+auditor",
            r"auditor(?:'|’)?s?\s+report",
            r"we\s+have\s+audited",
        ],
        "weak": [r"\bauditor\b"],
    },
    {
        "name": "Statement of Financial Position / Balance Sheet",
        "page_types": {"statement of financial position / balance sheet", "statement of financial position", "balance sheet"},
        "strong": [
            r"statement(?:s)?\s+of\s+financial\s+position",
            r"\bbalance\s+sheet\b",
        ],
        "weak": [r"\btotal\s+assets\b", r"\btotal\s+liabilities\b"],
    },
    {
        "name": "Statement of Profit or Loss / Statement of Income",
        "page_types": {
            "statement of income / receipts and expenses",
            "statement of income",
            "income statement",
            "statement of operations",
        },
        "strong": [
            r"statement(?:s)?\s+of\s+(?:profit\s+or\s+loss|income|operations)",
            r"\bincome\s+statement\b",
            r"\bprofit\s+or\s+loss\b",
        ],
        "weak": [r"\bnet\s+(?:income|loss)\b", r"\bgross\s+revenue\b"],
    },
    {
        "name": "Other Comprehensive Income",
        "page_types": {"statement of comprehensive income", "other comprehensive income"},
        "strong": [
            r"other\s+comprehensive\s+income",
            r"statement(?:s)?\s+of\s+comprehensive\s+income",
            r"\bcomprehensive\s+income\b",
        ],
        "weak": [r"\bcomprehensive\b"],
    },
    {
        "name": "Statement of Changes in Equity",
        "page_types": {"statement of changes in equity / fund balance", "statement of changes in equity"},
        "strong": [
            r"statement(?:s)?\s+of\s+changes\s+in\s+equity",
            r"\bchanges\s+in\s+equity\b",
        ],
        "weak": [r"\bfund\s+balance\b", r"\bshareholders?'?\s+equity\b"],
    },
    {
        "name": "Statement of Cash Flows",
        "page_types": {"statement of cash flows"},
        "strong": [
            r"statement(?:s)?\s+of\s+cash\s+flows",
            r"\bcash\s+flows\b",
        ],
        "weak": [r"\boperating\s+activities\b", r"\bfinancing\s+activities\b"],
    },
    {
        "name": "Notes to Financial Statements",
        "page_types": {"notes to financial statements"},
        "strong": [
            r"notes\s+to\s+financial\s+statements",
            r"summary\s+of\s+significant\s+accounting",
            r"basis\s+of\s+preparation",
        ],
        "weak": [r"\baccounting\s+policies\b"],
    },
]

REQUIRED_SECTIONS = [item["name"] for item in AFS_COMPONENT_DEFINITIONS]

BIR_EVIDENCE_PATTERNS = [
    r"\bbureau\s+of\s+internal\s+revenue\b",
    r"\bbir\b",
    r"\bincome\s+tax\s+return\b",
    r"\bannual\s+income\s+tax\s+return\b",
    r"\btax\s+return\b",
    r"\bproof\s+of\s+filing\b",
    r"\breceived\s+for\s+filing\b",
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


def is_afs_submission(metadata: Dict) -> bool:
    report_type = str(metadata.get("report_type") or "").strip().lower()
    submission_type = str(metadata.get("submission_type") or "").strip().lower()
    return report_type == "afs" or "annual financial statement" in submission_type


def _page_evidence_text(page: Dict) -> str:
    return " ".join([
        str(page.get("page_type") or ""),
        str(page.get("text_preview") or page.get("text") or ""),
    ]).lower()


def _component_evidence(page: Dict, definition: Dict) -> str:
    page_type = str(page.get("page_type") or "").strip().lower()
    text = _page_evidence_text(page)
    if page_type in definition["page_types"] or any(re.search(pattern, text) for pattern in definition["strong"]):
        return "Detected"
    if any(re.search(pattern, text) for pattern in definition["weak"]):
        return "Needs Review"
    return ""


def format_page_numbers(page_numbers: List[int]) -> str:
    numbers = sorted({int(number) for number in page_numbers if number is not None})
    if not numbers:
        return "—"
    ranges = []
    start = previous = numbers[0]
    for number in numbers[1:]:
        if number == previous + 1:
            previous = number
            continue
        ranges.append(f"{start}–{previous}" if start != previous else str(start))
        start = previous = number
    ranges.append(f"{start}–{previous}" if start != previous else str(start))
    prefix = "Page" if len(numbers) == 1 else "Pages"
    return f"{prefix} " + ", ".join(ranges)


def evaluate_afs_completeness(pages: List[Dict]) -> Dict:
    components = []
    for definition in AFS_COMPONENT_DEFINITIONS:
        detected_pages = []
        review_pages = []
        for page in pages:
            evidence = _component_evidence(page, definition)
            if evidence == "Detected":
                detected_pages.append(page.get("page_number"))
            elif evidence == "Needs Review":
                review_pages.append(page.get("page_number"))
        status = "Detected" if detected_pages else "Needs Review" if review_pages else "Missing"
        components.append({
            "component": definition["name"],
            "status": status,
            "page_numbers": detected_pages or review_pages,
            "detected_pages": format_page_numbers(detected_pages or review_pages),
        })

    missing = [item["component"] for item in components if item["status"] == "Missing"]
    uncertain = [item["component"] for item in components if item["status"] == "Needs Review"]
    evidence_count = sum(item["status"] != "Missing" for item in components)
    if evidence_count == 0:
        status = "Failed"
        message = "The uploaded document does not appear to contain a complete Annual Financial Statement."
        suggested_revert_reason = "Incorrect document filed"
    elif missing:
        status = "Failed"
        message = "Missing required AFS component(s): " + ", ".join(missing) + "."
        if uncertain:
            message += " Needs review: " + ", ".join(uncertain) + "."
        suggested_revert_reason = "Incomplete pages"
    elif uncertain:
        status = "Needs Review"
        message = "AFS component evidence needs reviewer confirmation: " + ", ".join(uncertain) + "."
        suggested_revert_reason = ""
    else:
        status = "Passed"
        message = "All required AFS components were detected."
        suggested_revert_reason = ""
    return {
        "status": status,
        "message": message,
        "suggested_revert_reason": suggested_revert_reason,
        "components": components,
    }


def evaluate_bir_filing(pages: List[Dict]) -> Dict:
    detected_pages = [
        page.get("page_number")
        for page in pages
        if any(re.search(pattern, _page_evidence_text(page)) for pattern in BIR_EVIDENCE_PATTERNS)
    ]
    if detected_pages:
        status = "Detected"
        message = f"BIR-related text evidence detected on {format_page_numbers(detected_pages)}."
    else:
        status = "Needs Review"
        message = "No BIR-related text evidence was detected."
    return {
        "status": status,
        "message": message,
        "detected_pages": format_page_numbers(detected_pages),
        "note": "Visual verification of a BIR received stamp is not yet automated in this prototype.",
    }


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
    validations = []
    if is_afs_submission(metadata):
        completeness = evaluate_afs_completeness(pages)
        validations.append({
            "rule_name": "AFS Completeness Check",
            "status": completeness["status"],
            "message": completeness["message"],
            "suggested_revert_reason": completeness["suggested_revert_reason"],
        })
        bir = evaluate_bir_filing(pages)
        validations.append({
            "rule_name": "Proof of BIR Filing",
            "status": bir["status"],
            "message": bir["message"] + " " + bir["note"],
            "suggested_revert_reason": "",
        })
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
    if "Warning" in statuses or "Needs Review" in statuses:
        return "Needs Review"
    return "Accept"


def suggested_revert_reason(validations: List[Dict]) -> str:
    for item in validations:
        if item.get("suggested_revert_reason"):
            return item["suggested_revert_reason"]
    return ""
