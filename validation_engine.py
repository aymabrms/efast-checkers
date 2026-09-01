import re
from datetime import date, datetime
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

AUDITOR_EXCLUDED_COMPONENTS = {
    "Statement of Financial Position / Balance Sheet",
    "Statement of Profit or Loss / Statement of Income",
    "Other Comprehensive Income",
    "Statement of Changes in Equity",
    "Statement of Cash Flows",
}

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

GIS_PAGE_TYPES = {
    "SEC Acceptance / QR Cover",
    "Annex A / Primary Purpose",
    "Beneficial Ownership Declaration",
    "Corporate / Profile / Meeting Information",
    "AMLA Information",
    "Capital Structure",
    "Directors / Officers",
    "Stockholders' Information",
    "Investments / Other Corporate Information",
    "Corporate Secretary Attestation / Notarization",
}

GIS_PAGE_PATTERNS = {
    "Corporate / Profile / Meeting Information": [
        r"\bgeneral\s+information\s+sheet\b",
        r"\bcorporate\s+name\b",
        r"\bsec\s+(?:registration|file)\s+(?:no|number)\b",
        r"\bactual\s+date\s+of\s+(?:annual|special)\s+meeting\b",
        r"\bprincipal\s+office\b",
        r"\bcorporate\s+address\b",
        r"\bperiod\s+covered\b",
    ],
    "AMLA Information": [
        r"\bamla\b",
        r"\banti[-\s]?money\s+laundering\b",
        r"\bbeneficial\s+ownership\s+information\b",
    ],
    "Capital Structure": [
        r"\bcapital\s+structure\b",
        r"\bauthorized\s+capital\s+stock\b",
        r"\bsubscribed\s+capital\s+stock\b",
        r"\bpaid[-\s]?up\s+capital\b",
    ],
    "Directors / Officers": [
        r"\bdirectors?\s+and\s+officers?\b",
        r"\bdirectors?\s*/\s*officers?\b",
        r"\bname(?:s)?\s+of\s+(?:the\s+)?directors?\b",
        r"\bname(?:s)?\s+of\s+(?:the\s+)?officers?\b",
    ],
    "Stockholders' Information": [
        r"\bstockholders?'?\s+(?:information|list|ownership)\b",
        r"\bstockholders?\b",
        r"\bnumber\s+of\s+shares\s+(?:subscribed|owned)\b",
    ],
    "Investments / Other Corporate Information": [
        r"\binvestments?\b",
        r"\baffiliations?\b",
        r"\btreasury\s+shares?\b",
        r"\bretained\s+earnings?\b",
        r"\bdividends?\b",
        r"\bsecondary\s+licen[cs]e\b",
        r"\bmanpower\b",
        r"\bfund\s+balance\b",
        r"\bother\s+corporate\s+information\b",
    ],
    "Corporate Secretary Attestation / Notarization": [
        r"\bcorporate\s+secretary\b",
        r"\bsecretary(?:'|’)?s?\s+attestation\b",
        r"\bsubscribed\s+and\s+sworn\b",
        r"\backnowledg(?:e)?ment\b",
        r"\bnotary\s+public\b",
        r"\bdoc\.?\s*no\.?\b",
        r"\bpage\s+no\.?\b",
        r"\bbook\s+no\.?\b",
        r"\bseries\s+of\b",
    ],
}

GIS_STOCK_REQUIRED = [
    "Corporate / Profile / Meeting Information",
    "AMLA Information",
    "Capital Structure",
    "Directors / Officers",
    "Stockholders' Information",
    "Investments / Other Corporate Information",
]

GIS_NON_STOCK_REQUIRED = [
    "Corporate / Profile / Meeting Information",
    "AMLA Information",
    "Directors / Officers",
    "Investments / Other Corporate Information",
]

GIS_OPTIONAL_COMPONENTS = [
    "Corporate Secretary / Notarization",
    "Annex A / Primary Purpose",
]

GIS_PERIOD_YEAR_PATTERNS = [
    r"\bfor\s+(?:the\s+)?year\s+(?:ended\s+)?(?:\w+\s+\d{1,2},?\s+)?(\d{4})\b",
    r"\bfor\s+the\s+year\s*[:\-]?\s*(\d{4})\b",
]

GIS_MEETING_DATE_LABELS = {
    "Annual Meeting": [
        r"actual\s+date\s+of\s+annual\s+meeting",
        r"date\s+of\s+annual\s+meeting",
    ],
    "Special Meeting": [
        r"actual\s+date\s+of\s+special\s+meeting",
        r"date\s+of\s+special\s+meeting",
    ],
}

GIS_NO_MEETING_PATTERNS = [
    r"\bno\s+meeting\b",
    r"\bno\s+meeting\s+held\b",
    r"\bnon[-\s]?holding\s+of\s+(?:the\s+)?annual\s+meeting\b",
    r"\banham\b",
]

GIS_AMENDMENT_PATTERNS = [r"\bamend(?:ment|ed)\b", r"\bamended\s+gis\b"]

GIS_BOD_HEADING_PATTERNS = [
    r"\bbeneficial\s+ownership\s+declaration\b",
    r"\bdeclaration\s+of\s+beneficial\s+ownership\b",
]

GIS_ACCEPTANCE_PATTERNS = [
    r"\bsec\s+(?:acceptance|accepted|received)\b",
    r"\bacceptance\s+(?:page|notice|reference)\b",
    r"\baccepted\s+(?:filing|report|gis)\b",
    r"\breceived\s+filing\s+(?:information|reference)\b",
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


def is_gis_submission(metadata: Dict) -> bool:
    return str(metadata.get("report_type") or "").strip().lower() == "gis"


def _gis_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _has_explicit_bod_heading(text: str) -> bool:
    lowered = _gis_text(text).lower()
    if any(re.search(pattern, lowered) for pattern in GIS_BOD_HEADING_PATTERNS):
        return True
    return bool(
        re.search(r"\bbeneficial\s+owners?\b", lowered)
        and re.search(r"\bdeclaration\b", lowered)
    )


def is_gis_acceptance_cover(text: str) -> bool:
    lowered = _gis_text(text).lower()
    has_acceptance = any(re.search(pattern, lowered) for pattern in GIS_ACCEPTANCE_PATTERNS)
    has_qr = bool(re.search(r"\bqr(?:\s+code)?\b", lowered))
    return has_acceptance or (has_qr and bool(re.search(r"\bsec\b", lowered)))


def classify_gis_page(text: str) -> str:
    lowered = _gis_text(text).lower()
    if is_gis_acceptance_cover(lowered):
        return "SEC Acceptance / QR Cover"
    if _has_explicit_bod_heading(lowered):
        return "Beneficial Ownership Declaration"
    if re.search(r"\bannex\s+a\b", lowered) and re.search(
        r"\bprimary\s+purpose\b|\bpurpose\s+continuation\b|\battached\s+annex\b",
        lowered,
    ):
        return "Annex A / Primary Purpose"
    for page_type, patterns in GIS_PAGE_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            return page_type
    if re.search(r"\bgeneral\s+information\s+sheet\b|\bgis\b", lowered):
        return "Corporate / Profile / Meeting Information"
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
    page_type = str(page.get("page_type") or "").strip().lower().replace("’", "'")
    if (
        definition["name"] in AUDITOR_EXCLUDED_COMPONENTS
        and page_type == "independent auditor's report"
    ):
        return ""
    text = _page_evidence_text(page)
    if page_type in definition["page_types"] or any(re.search(pattern, text) for pattern in definition["strong"]):
        return "Detected"
    if any(re.search(pattern, text) for pattern in definition["weak"]):
        return "Needs Review"
    return ""


def _gis_page_is_usable(page: Dict) -> bool:
    return page.get("page_type") != "SEC Acceptance / QR Cover"


def _gis_component_pages(pages: List[Dict], component: str) -> List[int]:
    patterns = GIS_PAGE_PATTERNS.get(component, [])
    matches = []
    for page in pages:
        if not _gis_page_is_usable(page):
            continue
        page_type = str(page.get("page_type") or "")
        text = _gis_text(page.get("text_preview") or page.get("text") or "").lower()
        if page_type == component or any(re.search(pattern, text) for pattern in patterns):
            matches.append(page.get("page_number"))
    return matches


def _gis_bod_pages(pages: List[Dict]) -> List[int]:
    return [
        page.get("page_number")
        for page in pages
        if _gis_page_is_usable(page)
        and (
            page.get("page_type") == "Beneficial Ownership Declaration"
            or _has_explicit_bod_heading(page.get("text_preview") or page.get("text") or "")
        )
    ]


def _gis_annex_pages(pages: List[Dict]) -> List[int]:
    return [
        page.get("page_number")
        for page in pages
        if _gis_page_is_usable(page)
        and (
            page.get("page_type") == "Annex A / Primary Purpose"
            or (
                re.search(r"\bannex\s+a\b", _gis_text(page.get("text_preview") or page.get("text") or ""), re.I)
                and re.search(r"\bprimary\s+purpose\b|\bpurpose\s+continuation\b", _gis_text(page.get("text_preview") or page.get("text") or ""), re.I)
            )
        )
    ]


def _gis_all_text(pages: List[Dict], include_acceptance: bool = False) -> str:
    selected = pages if include_acceptance else [page for page in pages if _gis_page_is_usable(page)]
    return "\n".join(str(page.get("text_preview") or page.get("text") or "") for page in selected)


def evaluate_gis_bod(pages: List[Dict]) -> Dict:
    detected_pages = _gis_bod_pages(pages)
    acceptance_pages = [
        page.get("page_number")
        for page in pages
        if page.get("page_type") == "SEC Acceptance / QR Cover"
    ]
    if detected_pages:
        status = "Detected"
        message = f"Beneficial Ownership Declaration evidence detected on {format_page_numbers(detected_pages)}."
    elif acceptance_pages:
        status = "Not Applicable / Accepted QA Copy"
        message = (
            "No Beneficial Ownership Declaration was detected; the accepted QA copy includes "
            f"{format_page_numbers(acceptance_pages)}."
        )
    else:
        status = "Not Detected"
        message = "No explicit Beneficial Ownership Declaration heading was detected."
    return {
        "status": status,
        "message": message,
        "page_numbers": detected_pages,
        "detected_pages": format_page_numbers(detected_pages),
    }


def evaluate_gis_completeness(pages: List[Dict], corporation_type: str = "Stock") -> Dict:
    required = GIS_NON_STOCK_REQUIRED if str(corporation_type or "").lower() == "non-stock" else GIS_STOCK_REQUIRED
    components = []
    for component in required:
        page_numbers = _gis_component_pages(pages, component)
        components.append({
            "component": component,
            "status": "Detected" if page_numbers else "Missing",
            "page_numbers": page_numbers,
            "detected_pages": format_page_numbers(page_numbers),
            "required": True,
        })

    for component in GIS_OPTIONAL_COMPONENTS:
        page_numbers = _gis_component_pages(
            pages,
            "Corporate Secretary Attestation / Notarization"
            if component == "Corporate Secretary / Notarization"
            else component,
        )
        components.append({
            "component": component,
            "status": "Detected" if page_numbers else "Not Present",
            "page_numbers": page_numbers,
            "detected_pages": format_page_numbers(page_numbers),
            "required": False,
        })

    bod = evaluate_gis_bod(pages)
    components.append({
        "component": "Beneficial Ownership Declaration",
        "status": bod["status"],
        "page_numbers": bod["page_numbers"],
        "detected_pages": bod["detected_pages"],
        "required": False,
    })

    missing = [item["component"] for item in components if item["required"] and item["status"] == "Missing"]
    if missing:
        status = "Failed"
        message = (
            f"Missing required GIS {corporation_type or 'Stock'} component(s): "
            + ", ".join(missing)
            + ". Optional Annex A and conditional BOD are excluded from this result."
        )
    else:
        status = "Passed"
        message = (
            f"All required GIS {corporation_type or 'Stock'} component groups were detected. "
            "Optional Annex A and conditional BOD are excluded from completeness."
        )
    return {
        "status": status,
        "message": message,
        "suggested_revert_reason": "Incomplete pages" if missing else "",
        "components": components,
    }


def extract_gis_period_years(text: str) -> List[int]:
    years = []
    lowered = _gis_text(text).lower()
    for pattern in GIS_PERIOD_YEAR_PATTERNS:
        years.extend(int(match) for match in re.findall(pattern, lowered))
    return sorted(set(years))


def _parse_gis_date(value: str):
    value = re.sub(r"\s+", " ", str(value or "").strip()).strip(" .,:;-")
    formats = (
        "%B %d, %Y",
        "%B %d %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d %b %Y",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _extract_gis_meeting_dates(text: str, meeting_type: str) -> List[date]:
    lowered = _gis_text(text).lower()
    labels = GIS_MEETING_DATE_LABELS.get(meeting_type, [])
    dates = []
    date_pattern = (
        r"([a-z]+\s+\d{1,2},?\s+\d{4}|"
        r"\d{1,2}\s+[a-z]+\s+\d{4}|"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{4}|"
        r"\d{4}-\d{1,2}-\d{1,2})"
    )
    for label in labels:
        for match in re.finditer(label + r"\s*[:\-]?\s*" + date_pattern, lowered, re.I):
            parsed = _parse_gis_date(match.group(1))
            if parsed:
                dates.append(parsed)
    return sorted(set(dates))


def _metadata_period_date(metadata: Dict):
    value = metadata.get("period_covered")
    if isinstance(value, date):
        return value
    return _parse_gis_date(value)


def _gis_meeting_validation(pages: List[Dict], metadata: Dict) -> Dict:
    all_text = _gis_all_text(pages)
    submission_type = str(metadata.get("submission_type") or "").strip()
    target_date = _metadata_period_date(metadata)
    if any(re.search(pattern, all_text, re.I) for pattern in GIS_NO_MEETING_PATTERNS):
        return {
            "status": "Needs Review",
            "message": "No Meeting / non-holding evidence was detected; reviewer confirmation is required.",
            "suggested_revert_reason": "",
        }

    if submission_type == "Special Meeting" or re.search(r"\bspecial\s+meeting\b", all_text, re.I):
        meeting_type = "Special Meeting"
    else:
        meeting_type = "Annual Meeting"
    dates = _extract_gis_meeting_dates(all_text, meeting_type)

    if submission_type in ("Amendment / Amended GIS", "Amended GIS") or any(
        re.search(pattern, all_text, re.I) for pattern in GIS_AMENDMENT_PATTERNS
    ):
        if dates and target_date:
            status = "Passed" if target_date in dates else "Failed"
            message = (
                f"Amendment evidence shows {meeting_type.lower()} date(s) "
                f"{', '.join(item.isoformat() for item in dates)}; "
                f"Intake Period Covered is {target_date.isoformat()}."
            )
        else:
            status = "Needs Review"
            message = "Amendment evidence was detected; confirm the meeting date against Intake Period Covered."
        return {
            "status": status,
            "message": message,
            "suggested_revert_reason": "Wrong period covered" if status == "Failed" else "",
        }

    if not dates or not target_date:
        return {
            "status": "Needs Review",
            "message": (
                f"{meeting_type} evidence was not paired with a clearly readable actual meeting date "
                "and Intake Period Covered."
            ),
            "suggested_revert_reason": "",
        }
    status = "Passed" if target_date in dates else "Failed"
    return {
        "status": status,
        "message": (
            f"{meeting_type} date evidence: {', '.join(item.isoformat() for item in dates)}. "
            f"Intake Period Covered: {target_date.isoformat()}."
        ),
        "suggested_revert_reason": "Wrong period covered" if status == "Failed" else "",
    }


def _gis_company_validation(pages: List[Dict], metadata: Dict) -> List[Dict]:
    body_text = _gis_all_text(pages)
    company_name = str(metadata.get("company_name") or "").strip()
    sec_no = str(metadata.get("sec_registration_no") or "").strip()
    insufficient = len(_gis_text(body_text)) < 40
    company_match = bool(company_name) and fuzzy_company_match(body_text, company_name)
    normalized_sec = re.sub(r"[^a-z0-9]", "", sec_no.lower())
    normalized_body = re.sub(r"[^a-z0-9]", "", body_text.lower())
    sec_match = bool(normalized_sec) and normalized_sec in normalized_body
    company_status = "Passed" if company_match else "Needs Review" if insufficient else "Failed"
    sec_status = "Passed" if sec_match else "Needs Review" if insufficient else "Failed"
    return [
        {
            "rule_name": "GIS Company Name",
            "status": company_status,
            "message": (
                "Company name evidence matches Intake metadata."
                if company_match
                else "Company name evidence is insufficient or does not match Intake metadata."
            ),
            "suggested_revert_reason": "Wrong company profile" if company_status == "Failed" else "",
        },
        {
            "rule_name": "GIS SEC Registration Number",
            "status": sec_status,
            "message": (
                "SEC Registration Number evidence matches Intake metadata."
                if sec_match
                else "SEC Registration Number evidence is insufficient or does not match Intake metadata."
            ),
            "suggested_revert_reason": "Wrong company profile" if sec_status == "Failed" else "",
        },
    ]


def _gis_corporate_secretary_validation(pages: List[Dict]) -> Dict:
    text = _gis_all_text(pages)
    secretary = bool(re.search(r"\bcorporate\s+secretary\b|\bsecretary(?:'|’)?s?\s+attestation\b", text, re.I))
    notarization = any(
        re.search(pattern, text, re.I)
        for pattern in GIS_PAGE_PATTERNS["Corporate Secretary Attestation / Notarization"][2:]
    )
    if secretary and notarization:
        status = "Passed"
    elif secretary or notarization:
        status = "Needs Review"
    else:
        status = "Needs Review"
    return {
        "rule_name": "Corporate Secretary / Notarization Evidence",
        "status": status,
        "message": (
            f"Corporate Secretary text: {'Detected' if secretary else 'Not Detected'}; "
            f"notarization text: {'Detected' if notarization else 'Not Detected'}. "
            "Signature or notarial-stamp appearance still requires visual confirmation."
        ),
        "suggested_revert_reason": "",
    }


def validate_gis_document(pages: List[Dict], metadata: Dict) -> List[Dict]:
    all_text = _gis_all_text(pages)
    validations = _gis_company_validation(pages, metadata)
    year = int(metadata.get("period_covered_year") or 0)
    detected_years = extract_gis_period_years(all_text)
    if year in detected_years:
        year_status = "Passed"
        year_message = f"GIS heading evidence supports Period Year {year}."
    elif detected_years:
        year_status = "Failed"
        year_message = f"GIS heading evidence shows year(s) {', '.join(map(str, detected_years))}, not Intake Period Year {year}."
    else:
        year_status = "Needs Review"
        year_message = f"No clear 'FOR THE YEAR' GIS heading was detected for Intake Period Year {year}."
    validations.append({
        "rule_name": "GIS Period Year",
        "status": year_status,
        "message": year_message,
        "suggested_revert_reason": "Wrong period covered" if year_status == "Failed" else "",
    })
    validations.append({
        "rule_name": "GIS Period Covered / Submission Type",
        **_gis_meeting_validation(pages, metadata),
    })

    completeness = evaluate_gis_completeness(pages, metadata.get("corporation_type", "Stock"))
    validations.append({
        "rule_name": "GIS Completeness Check",
        "status": completeness["status"],
        "message": completeness["message"],
        "suggested_revert_reason": completeness["suggested_revert_reason"],
    })

    acceptance_pages = [
        page.get("page_number")
        for page in pages
        if page.get("page_type") == "SEC Acceptance / QR Cover"
    ]
    validations.append({
        "rule_name": "SEC Acceptance / QR Cover",
        "status": "Detected" if acceptance_pages else "Passed",
        "message": (
            f"Likely SEC acceptance/QR cover detected on {format_page_numbers(acceptance_pages)}; "
            "excluded from GIS completeness."
            if acceptance_pages
            else "No likely SEC acceptance/QR cover detected; review remains content-based."
        ),
        "suggested_revert_reason": "",
    })

    quality_failed = [page for page in pages if page.get("image_quality_flag") == "Failed"]
    quality_warning = [page for page in pages if page.get("image_quality_flag") == "Warning"]
    validations.append({
        "rule_name": "GIS Image Quality",
        "status": "Failed" if quality_failed else "Warning" if quality_warning else "Passed",
        "message": (
            f"{len(quality_failed)} page(s) have very low extracted text."
            if quality_failed
            else f"{len(quality_warning)} page(s) have low extracted text; review Text Layer/OCR source."
            if quality_warning
            else "Extracted text is adequate for preliminary GIS review."
        ),
        "suggested_revert_reason": "Poor image quality" if quality_failed else "",
    })
    rotated_pages = [
        page for page in pages
        if int(page.get("rotation_degrees") or 0) in (90, 180, 270)
    ]
    landscape_pages = [page for page in pages if page.get("orientation") == "Landscape"]
    validations.append({
        "rule_name": "GIS Page Orientation / Rotation",
        "status": "Warning" if rotated_pages or landscape_pages else "Passed",
        "message": (
            f"{len(rotated_pages)} rotated and {len(landscape_pages)} landscape page(s) detected; "
            "review page geometry and orientation."
            if rotated_pages or landscape_pages
            else "No non-zero rotation metadata or landscape pages detected."
        ),
        "suggested_revert_reason": "",
    })
    validations.append(_gis_corporate_secretary_validation(pages))
    return validations


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
        page_type = page.get("page_type") or (
            classify_gis_page(text) if is_gis_submission(metadata) else classify_page(text)
        )
        flag = page.get("image_quality_flag") or quality_flag(text)
        text_length = page.get("text_length")
        if text_length is None:
            text_length = len(text.strip())
        analyzed.append({
            "page_number": page.get("page_number"),
            "page_type": page_type,
            "orientation": page.get("orientation", "Portrait"),
            "text_preview": page.get("text_preview") or text[:TEXT_PREVIEW_MAX_CHARS],
            "original_text": page.get("original_text", text),
            "ocr_text": page.get("ocr_text", ""),
            "extraction_source": page.get("extraction_source", "Text Layer"),
            "detected_company_match": fuzzy_company_match(text, company_name),
            "detected_period_match": has_period(text, period_year),
            "image_quality_flag": flag,
            "rotation_degrees": page.get("rotation_degrees", page.get("rotation", 0)) or 0,
            "text_length": text_length,
        })
    return analyzed


def validate_document(pages: List[Dict], metadata: Dict, company_master: Dict) -> List[Dict]:
    if is_gis_submission(metadata):
        return validate_gis_document(pages, metadata)
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
