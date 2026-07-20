from pathlib import Path

APP_TITLE = "SEC eFAST Checkers"
APP_SUBTITLE = "AFS Validation and Figure Extraction MVP"
AGENCY_NAME = "Securities and Exchange Commission"
DEFAULT_COMPANY = "Audentia Fortuna Holdings, Inc."
DEFAULT_REPORT_TYPE = "AFS"
DEFAULT_SUBMISSION_TYPE = "Annual Financial Statements"
DEFAULT_PERIOD_YEAR = 2025
DEFAULT_COMPARATIVE_YEARS = "2024, 2023"
DEFAULT_FILING_YEAR = 2026

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
DB_PATH = DATA_DIR / "sec_efast_checkers.sqlite"
DEMO_DATA_PATH = BASE_DIR / "demo_data.json"
LABEL_MAPPING_PATH = BASE_DIR / "label_mapping.json"
REVERT_REASONS_PATH = BASE_DIR / "revert_reasons.json"
COMPANY_MASTER_PATH = BASE_DIR / "sample_company_master.json"

PAGE_PRIORITY = [
    "Independent Auditor’s Report",
    "Statement of Management’s Responsibility",
    "Notes to Financial Statements",
    "Statement of Financial Position / Balance Sheet",
]

RANKING_METRICS = [
    "Gross Revenue",
    "Total Revenue",
    "Gross Receipts",
    "Net Sales",
]

STATUS_ORDER = ["Passed", "Warning", "Failed", "Needs Review"]

TEXT_PREVIEW_MAX_CHARS = 2000
