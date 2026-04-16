import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from config import LABEL_MAPPING_PATH


def load_label_mapping(path: Path = LABEL_MAPPING_PATH) -> Dict[str, List[str]]:
    return json.loads(path.read_text())


def clean_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def normalize_label(raw_label: str, mapping: Optional[Dict[str, List[str]]] = None) -> str:
    mapping = mapping or load_label_mapping()
    cleaned = clean_label(raw_label)
    for normalized, labels in mapping.items():
        for label in labels:
            if clean_label(label) == cleaned or clean_label(label) in cleaned:
                return normalized
    return clean_label(raw_label).replace(" ", "_")


def parse_amount(displayed_value: str, unit_basis: str = "Pesos") -> float:
    text = str(displayed_value).replace("₱", "").replace(",", "").strip()
    negative = "(" in text and ")" in text
    text = text.replace("(", "").replace(")", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    amount = float(match.group(0))
    if negative:
        amount = -amount
    basis = unit_basis.lower()
    if "thousand" in basis:
        amount *= 1000
    if "million" in basis:
        amount *= 1000000
    return amount


def detect_unit_basis(text: str) -> str:
    lowered = text.lower()
    if "amounts in thousands" in lowered or "in thousands" in lowered:
        return "Thousands"
    if "amounts in millions" in lowered or "in millions" in lowered:
        return "Millions"
    return "Pesos"
