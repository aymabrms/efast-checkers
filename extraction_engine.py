import re
from typing import Dict, List

from normalization import detect_unit_basis, normalize_label, parse_amount, validate_numeric_string

MANDATORY_LABELS = [
    "Total Assets",
    "Total Liabilities",
    "Total Equity",
    "Fund Balance",
    "Cash and Cash Equivalents",
    "Revenue",
    "Gross Revenue",
    "Gross Receipts",
    "Total Revenue",
    "Net Sales",
    "Net Income",
    "Net Loss",
    "Operating Cash Flow",
    "Net Cash Provided by Operating Activities",
]

LABEL_PATTERN = re.compile(
    r"(" + "|".join(re.escape(label) for label in sorted(MANDATORY_LABELS, key=len, reverse=True)) + r")",
    re.IGNORECASE,
)


def extract_figures_from_pages(pages: List[Dict], fiscal_years: List[int]) -> List[Dict]:
    results = []
    for page in pages:
        text = page.get("text_preview") or ""
        unit_basis = detect_unit_basis(text)
        label_matches = list(LABEL_PATTERN.finditer(text))
        page_seen = set()
        for index, label_match in enumerate(label_matches):
            segment_end = label_matches[index + 1].start() if index + 1 < len(label_matches) else len(text)
            segment = text[label_match.end():segment_end][:300]
            normalized_label = normalize_label(label_match.group(1))
            for year in fiscal_years:
                year_match = re.search(rf"\b{year}\b\s+([^\s]+)", segment)
                row_key = (normalized_label, int(year))
                if year_match and row_key not in page_seen:
                    page_seen.add(row_key)
                    displayed = year_match.group(1)
                    numeric_candidate = displayed.rstrip(".,;:")
                    numeric_safe, numeric_note = validate_numeric_string(numeric_candidate)
                    source_end = label_match.end() + year_match.end()
                    results.append({
                        "page_number": page.get("page_number"),
                        "statement_type": page.get("page_type", "Other / Unclassified"),
                        "raw_label": label_match.group(1),
                        "normalized_label": normalized_label,
                        "fiscal_year": year,
                        "displayed_value": displayed,
                        "normalized_peso_value": parse_amount(numeric_candidate, unit_basis) if numeric_safe else None,
                        "unit_basis": unit_basis,
                        "source_snippet": text[max(0, label_match.start() - 45):source_end + 45],
                        "status": "Needs Review" if numeric_safe else "Check Source",
                        "review_note": numeric_note,
                        "confidence": 0.82,
                    })
    return results


def fiscal_year_candidates(metadata: Dict) -> List[int]:
    years = []
    current = metadata.get("period_covered_year")
    if current:
        years.append(int(current))
    comparative = metadata.get("comparative_years", "")
    if isinstance(comparative, list):
        years.extend(int(year) for year in comparative)
    else:
        years.extend(int(year) for year in re.findall(r"20\d{2}", str(comparative)))
    return sorted(set(years), reverse=True)
