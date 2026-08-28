# SEC eFAST Checkers — Current Prototype Documentation

**Documentation basis:** current workspace files and the current SQLite database inspected on 28 August 2026. This document describes implemented behavior only. It does not describe a proposed production architecture or future roadmap.

## A. Prototype Purpose

SEC eFAST Checkers is an internal Streamlit MVP for demonstrating an Annual Financial Statements (AFS) review workflow in an SEC-oriented context. Its main demonstration areas are:

- registering an AFS intake record;
- extracting text from a PDF;
- classifying pages using keyword rules;
- validating company, period, submission, orientation, completeness, and text readability signals;
- showing evidence and validation results to a reviewer;
- extracting a limited set of financial figures into structured rows;
- allowing a reviewer to correct extracted values and statuses;
- saving reviewer disposition and remarks; and
- exporting selected data as CSV.

The primary user is an internal SEC reviewer or reviewer-operations user. The current scope is AFS-focused: it does not connect to a live SEC filing system, perform OCR, authenticate users, or implement a production filing decision workflow.

## B. Current End-to-End Workflow

The sidebar navigation exposes seven Streamlit screens. A typical review path is:

```text
Dashboard
  -> Upload / Intake
  -> Document Review
       -> Validation Results
       -> Page Review
       -> Reviewer Disposition
  -> AFS Figures Extraction Review
  -> Historical Company View
  -> Rankings / Research View
```

The screens are independently selectable; the arrows describe the intended review sequence, not a server-side workflow engine.

### Dashboard

`pages/dashboard.py` reads live intake, validation, figure, and reviewer-action data from SQLite. It shows:

- document count;
- counts of warning/failed validation rows;
- counts of saved Accept and Revert recommendations;
- extracted-figure and reviewer-edited counts;
- a recent document queue with company, SEC registration number, period, submission type, recommendation, source, and formatted upload time;
- validation and extraction-volume charts; and
- a document selector with an **Open in Review** button.

The dashboard button stores the selected `active_document_id`, sets `_nav_to` to `Document Review`, and reruns the app. Recommendations in the queue are derived from the latest action per document. The source label is inferred from the seeded demo filenames; all other filenames are labeled `Uploaded`.

### Upload / Intake

`pages/upload_intake.py` provides metadata fields and an optional PDF uploader. On submission it:

1. creates a `documents` row;
2. saves an uploaded file under `uploads/` when a file was provided;
3. attempts PyMuPDF text extraction, with pdfplumber fallback;
4. analyzes extracted pages;
5. validates the document;
6. extracts supported financial figures; and
7. replaces the document's page, validation, and figure analysis rows in SQLite.

If extraction produces no pages, the screen uses the demo sample pages, validations, and figures as fallback data. If pages are readable but no figure matches are found, it keeps the analyzed pages and validations but substitutes demo figures. A warning is shown in either fallback case. The active document is set to the newly inserted document.

The **Load Demo Document** button calls the legacy-compatible `ensure_demo_document()` path for the primary Audentia case. Application bootstrap calls `ensure_all_demo_documents()` to ensure the full demo suite exists.

### Document Review

`pages/document_review.py` resolves the current document from `st.session_state["active_document_id"]`, or shows a document selector when none is active. It displays:

- a **Currently Reviewing** banner;
- validation results as color-coded cards;
- page accordions with page number, page type, source classification tag, orientation, company/period match indicators, readability status, and highlighted text evidence;
- a reviewer disposition form; and
- reviewer action history.

The disposition form starts with the rule-based system recommendation and suggested revert reason. It saves the final recommendation, selected revert reason, and remarks to `reviewer_actions`. The current database method updates the existing action for a document rather than creating a new history row.

The **Switch document** expander uses a separate selector and reruns after the reviewer clicks **Load selected document**. A missing selected document clears the active ID and returns to a clean warning state.

### Page Review

Page review is part of Document Review rather than a separate page. It reads `page_analysis` rows. Primary AFS pages receive a `Primary Source` tag; notes, cover pages, and `Other` receive a `Supporting` tag. The page text displayed is the stored `text_preview`, not a rendered PDF page image.

### Reviewer Disposition

The disposition is also part of Document Review. The engine's recommendation is:

- `Revert` if any validation is `Failed`;
- `Needs Review` if no validation failed but at least one is `Warning`;
- `Accept` otherwise.

The reviewer may override this recommendation. The reviewer can choose one of the configured revert reasons, enter free-text remarks, and save the action.

### AFS Figures Extraction Review

`pages/figures_review.py` reads figures for the active document from `extracted_figures`. It displays:

- rows extracted;
- normalized fields;
- fiscal years;
- current revenue;
- rows with `Needs Review`;
- an editable figure table; and
- normalized figure buckets.

The editable table allows `review_status` and `reviewed_value` changes. Other extraction fields are disabled. **Save Corrections** calls `update_figure_reviews()`. It updates the reviewer value, reviewer-edited flag, and review status by figure ID, constrained by document ID. **Export Figures CSV** downloads the current displayed table without the internal figure ID.

Confidence is shown as a human-readable estimated percentage. It is not computed from a statistical model.

### Historical Company View

`pages/historical_company.py` shows a demo-only five-year financial history for the fictional Audentia company. It reads `historical_data` from `demo_data.json`, not reviewed figures from SQLite. It provides a table, CSV export, headline metrics, and trend charts.

### Rankings / Research View

`pages/rankings.py` shows a demo-only ranking of five fictional companies. It reads `ranking_data` from `demo_data.json`, lets the user choose one configured revenue metric, sorts descending, generates a display rank, shows the highest-ranked company, and provides a chart and CSV export. The stored `rank_hint` values are not used to calculate the displayed rank.

### Settings / Editable Demo Data

`pages/settings_demo_data.py` is a read-only reference screen despite its title. It lists the editable content files, displays current JSON/config values, and shows demo dataset counts. It does not write files or provide a live editor.

## C. Current Modules

| Module | Purpose and main functions | Data source | Current implementation status |
|---|---|---|---|
| `app.py` | Page registry, page configuration, CSS theme, bootstrap, sidebar radio navigation, programmatic navigation | SQLite initialization plus JSON seed/config modules | Working Streamlit shell |
| `pages/dashboard.py` | Live operational summary, document queue, navigation into review, charts | SQLite tables | Working and database-driven |
| `pages/upload_intake.py` | Metadata intake, PDF save/extraction, analysis, fallback behavior | Uploaded PDF, company master JSON, demo JSON, SQLite | Partial MVP; real text extraction with demo fallback |
| `pages/document_review.py` | Validation cards, page review, evidence highlighting, disposition, action display | SQLite `page_analysis`, `validations`, `reviewer_actions`; JSON revert reasons | Working reviewer UI with heuristic analysis |
| `pages/figures_review.py` | Structured figure table, corrections, CSV export, buckets | SQLite `extracted_figures` | Working for the supported row model |
| `pages/historical_company.py` | Historical metrics and trends | Seeded `demo_data.json` | Demo / seeded |
| `pages/rankings.py` | Selectable revenue-metric ranking and export | Seeded `demo_data.json` | Demo / seeded |
| `pages/settings_demo_data.py` | Reference display of configuration and demo content | JSON/config files | Working read-only reference |
| `validation_engine.py` | Company, period, submission, orientation, completeness, and readability rules | Analyzed page dictionaries and company master | Working rule-based engine |
| `extraction_engine.py` | Mandatory-label/year regex extraction and fiscal-year candidate generation | Page text previews and metadata | Partial, intentionally limited |
| `normalization.py` | Label alias mapping, amount parsing, unit detection | `label_mapping.json` and page text | Working for supported patterns |
| `pdf_utils.py` | PyMuPDF extraction, pdfplumber fallback, quality proxy | Uploaded local PDF | Partial text-layer PDF support |
| `storage.py` | JSON loading, demo seeding, SQLite read helpers | JSON files and SQLite | Working persistence/seed helpers |
| `db.py` | SQLite schema creation and CRUD/update helpers | `data/sec_efast_checkers.sqlite` | Working prototype persistence |
| `ui_helpers.py` | Shared badges, metrics, formatting, selectors, banner, CSV download | Streamlit state/UI values | Working presentation helpers |

## D. Current Validation Rules

All current validation rules are deterministic rules or heuristics. They do not use OCR, machine learning, external company data, or a production filing rules service.

### Company matching and SEC registration number

The company master match combines:

- a fuzzy name match between the concatenated page text and the company master name; and
- a literal check that the company-master SEC registration number occurs in the concatenated page text.

Name matching lowercases and simplifies common `corporation`/`corp` and `incorporated`/`inc` variants, then uses substring, first-three-word containment, or `SequenceMatcher` similarity of at least `0.74`. This check uses the company master loaded from `sample_company_master.json`, which currently describes Audentia Fortuna Holdings, Inc.

There is no separate validation row named only “SEC registration number.” The registration number is part of the **Company master data match** rule.

### Period covered

The expected year comes from the intake metadata, falling back to the company master year. The validation passes if the year appears on any of the hard-coded priority pages—Auditor's Report, Management's Responsibility, or Notes—or anywhere in the combined page previews.

### Comparative year

There is no standalone comparative-year validation rule in the current code. Comparative years are:

- accepted as intake metadata;
- parsed into fiscal-year candidates for extraction; and
- shown in seeded sample text and demo data.

The validation engine does not independently confirm every comparative year.

### Submission type

The rule passes if the combined page preview contains the phrase `financial statements` or if the intake `report_type` is `AFS`. Otherwise it fails.

### Page classification

The classifier scans lowercased page text in rule order and returns the first page type whose keyword list contains a match. The exact page types and keywords are documented in Section E.

### Page orientation

PDF geometry determines orientation: a page is `Landscape` when width is greater than height, otherwise `Portrait`. Any landscape page produces a `Warning`; no landscape pages produces `Passed`. The warning is not an automatic rejection.

### Readability / image-quality proxy

`quality_flag()` uses the length of stripped extracted text:

- fewer than 25 characters: `Failed`;
- 25–139 characters: `Warning`;
- 140 or more characters: `Passed`.

This is a text-volume proxy, not an image-quality or OCR confidence measurement.

### Completeness

The engine compares the exact set of analyzed page-type strings to these required sections:

- Statement of Management's Responsibility;
- Independent Auditor's Report;
- Statement of Financial Position / Balance Sheet;
- Statement of Income / Receipts and Expenses;
- Statement of Comprehensive Income;
- Statement of Changes in Equity / Fund Balance;
- Statement of Cash Flows; and
- Notes to Financial Statements.

Missing sections produce a `Warning`. The check is based on page classification labels and can therefore miss content whose wording does not classify to the expected exact label.

### Suggested revert reasons

`suggested_revert_reason()` returns the first non-empty suggested reason in validation order. The configured dropdown options are:

- Wrong company profile
- Wrong period covered
- Wrong submission type
- Poor image quality
- Wrong page orientation
- Incomplete pages
- Incorrect document filed
- Erroneous document

### Final recommendation

`final_recommendation()` reduces validation statuses using the precedence `Failed` → `Revert`, then `Warning` → `Needs Review`, otherwise `Accept`.

## E. Page Classification

`validation_engine.py` recognizes the following page types and checks the following keywords, in this order:

| Page type returned | Any matching keyword |
|---|---|
| Statement of Management's Responsibility | `management`, `responsibility`, `financial statements` |
| Cover Sheet | `cover sheet`, `sec registration`, `company information` |
| Independent Auditor's Report | `independent auditor`, `we have audited`, `auditor's report`, `auditor’s report` |
| Statement of Financial Position / Balance Sheet | `financial position`, `balance sheet`, `total assets`, `total liabilities` |
| Statement of Income / Receipts and Expenses | `statement of income`, `receipts and expenses`, `net income`, `gross revenue` |
| Statement of Comprehensive Income | `comprehensive income`, `other comprehensive` |
| Statement of Changes in Equity / Fund Balance | `changes in equity`, `fund balance`, `retained earnings` |
| Statement of Cash Flows | `cash flows`, `operating activities`, `financing activities` |
| Notes to Financial Statements | `notes to financial statements`, `summary of significant accounting`, `basis of preparation` |
| `Other / Unclassified` | no keyword match |

Because the first matching rule wins, generic terms can classify a page before a more specific later rule. Classification operates on the available page text, normally the first 2,000 characters stored as `text_preview`.

## F. Reviewer / HITL Workflow

### System recommendation

The system derives a starting recommendation from validation statuses:

- any `Failed` → `Revert`;
- otherwise any `Warning` → `Needs Review`;
- otherwise → `Accept`.

The reviewer can override the starting recommendation in the disposition form.

### Accept, Needs Review, and Revert

These are string values stored in `reviewer_actions.final_recommendation` and displayed in the review UI and dashboard queue. They represent the reviewer's current recommendation, not an enforced downstream filing action.

### Suggested revert reason and remarks

The engine can suggest the first configured reason associated with a failed/warning rule. The reviewer can select a reason from the configured list and enter free-text remarks. Both are persisted with the recommendation.

### Reviewer corrections

In Figures Review, a reviewer edits `reviewed_value` and/or `review_status`. The database update recalculates `reviewer_edited` by comparing the reviewed value with the original displayed value. The current update path does not change `normalized_peso_value`.

### Reviewer action history

The UI reads `reviewer_actions` and renders the stored recommendation, `final_revert_reason`, `reviewer_remarks`, and `updated_at`. The table has a unique `document_id`, and `save_reviewer_action()` updates the existing row when present. Consequently, the visible action history is effectively the current/latest saved action per document, not an append-only audit log.

### Active document handling

The app stores the selected integer ID in `st.session_state["active_document_id"]`. Dashboard navigation sets that ID before routing to Document Review. Document Review and Figures Review both prefer the active ID and otherwise show a selector. If an active ID no longer resolves to a document, the page warns, clears the ID, and returns.

### Switching documents

Each review page has a collapsed **Switch document** expander. A different selected document is applied only after **Load selected document** is clicked; then the page reruns. The current implementation does not provide an unsaved-form warning before switching.

## G. AFS Figure Extraction

### Supported labels

The regex extractor scans these mandatory labels:

- Total Assets
- Total Liabilities
- Total Equity
- Fund Balance
- Cash and Cash Equivalents
- Revenue
- Gross Revenue
- Gross Receipts
- Total Revenue
- Net Sales
- Net Income
- Net Loss
- Operating Cash Flow
- Net Cash Provided by Operating Activities

The label mapping additionally supports aliases for normalized fields, including assets, liabilities, equity/fund balance, cash, revenue, gross revenue/receipts, total revenue, net sales, net income/loss, and operating cash flow. See `label_mapping.json` for the full alias lists.

### Extracted row fields

Each extracted or seeded figure row can contain:

- `page_number`: source page;
- `statement_type`: analyzed page type;
- `raw_label`: text label matched in the source;
- `normalized_label`: mapped internal field name;
- `fiscal_year`: matched current/comparative year;
- `displayed_value`: source-formatted numeric text;
- `normalized_peso_value`: parsed amount converted to pesos;
- `unit_basis`: `Pesos`, `Thousands`, or `Millions`;
- `source_snippet`: approximately 45 characters before and after the match;
- `confidence`: a prototype confidence number;
- `review_status`: current row status;
- `reviewed_value`: optional reviewer-entered replacement; and
- `reviewer_edited`: persisted edit flag.

### Extraction implementation

For each analyzed page, each mandatory label, and each fiscal-year candidate, the engine uses a case-insensitive regular expression requiring:

```text
label + whitespace + year + whitespace + numeric value
```

Values may include a peso sign, commas, decimal digits, parentheses, or a minus sign. The extractor scans `text_preview`, not the full PDF text.

`detect_unit_basis()` looks for `in thousands` or `in millions` anywhere on the page and applies one basis to all matches on that page. Otherwise the basis is `Pesos`. `parse_amount()` removes commas and the peso sign, interprets parentheses as negative, and multiplies by 1,000 or 1,000,000 when applicable.

### Limitations

The extractor is intentionally narrow:

- it requires a supported label/year/value layout;
- it reads only extracted text, not table geometry;
- it does not understand arbitrary column layouts, OCR text, or merged cells;
- it uses one detected unit basis per page;
- it may miss labels with spelling/layout differences;
- it does not independently cross-check totals or accounting equations; and
- when no figures are found, the upload flow can substitute seeded demo figures with a warning.

## H. Confidence

Confidence is currently prototype metadata, not a calculated prediction.

- Dynamically extracted rows receive a fixed `0.82` in `extraction_engine.py`.
- Seeded demo rows contain manually assigned values such as `0.51` through `0.95`.
- Figures Review renders the value as a percentage followed by `· Est.`; missing/non-numeric values render as `—`.
- There is no current formula based on OCR quality, label match quality, table position, cross-field consistency, or reviewer outcomes.

No future confidence model is implemented in the current codebase. Confidence should therefore be treated as an estimated demonstration field and not as a production score.

## I. Historical and Rankings Features

Historical and ranking screens are explicitly demo projections:

- Historical Company View reads the five-year `historical_data` array in `demo_data.json` for Audentia Fortuna Holdings, Inc.
- Rankings / Research View reads the five-company `ranking_data` array in `demo_data.json`.
- Neither screen queries uploaded documents or reviewed figures from SQLite.
- The screens provide display, sorting/charting, and CSV export around those seeded arrays.

The dashboard, Document Review, and Figures Review are the portions currently backed by SQLite.

## J. Database

### SQLite usage

The prototype uses the file configured as `data/sec_efast_checkers.sqlite`. `db.py` opens a normal SQLite connection per operation and uses `sqlite3.Row` to return dictionary-like rows. `init_db()` creates tables if they do not exist.

The current inspection snapshot contained:

| Table | Rows observed |
|---|---:|
| `company_master` | 1 |
| `documents` | 3 |
| `page_analysis` | 20 |
| `validations` | 17 |
| `extracted_figures` | 19 |
| `reviewer_actions` | 2 |

Counts change when users upload documents or save corrections.

### Tables and important fields

#### `documents`

`id`, `filename`, `company_name`, `sec_registration_no`, `report_type`, `period_covered_year`, `comparative_years`, `submission_type`, `filing_year`, `uploaded_at`.

#### `company_master`

`id`, `company_name`, `sec_registration_no`, `period_covered_year`, `comparative_years`.

The JSON company master includes additional descriptive fields, but only the fields above are stored in SQLite.

#### `page_analysis`

`id`, `document_id`, `page_number`, `page_type`, `orientation`, `text_preview`, `detected_company_match`, `detected_period_match`, `image_quality_flag`.

#### `validations`

`id`, `document_id`, `rule_name`, `status`, `message`, `suggested_revert_reason`.

#### `extracted_figures`

`id`, `document_id`, `page_number`, `statement_type`, `raw_label`, `normalized_label`, `fiscal_year`, `displayed_value`, `normalized_peso_value`, `unit_basis`, `source_snippet`, `reviewer_edited`, `reviewed_value`, `review_status`, `confidence`.

#### `reviewer_actions`

`id`, `document_id` (unique), `reviewer_remarks`, `final_recommendation`, `final_revert_reason`, `updated_at`.

### Relationships and persistence

The application treats `document_id` in `page_analysis`, `validations`, `extracted_figures`, and `reviewer_actions` as the relationship to `documents`. The schema does not declare foreign-key constraints or database cascades.

- `replace_document_analysis()` deletes and reinserts all three analysis sets for one document.
- `update_figure_reviews()` updates figure rows by both figure ID and document ID.
- `save_reviewer_action()` inserts once and then updates the unique document action.
- `get_reviewer_actions()` orders the available row by `updated_at`.

## K. Demo Data

The current `demo_suite` contains three fictional companies:

| Company | Intended scenario | Current seeded characteristics |
|---|---|---|
| Audentia Fortuna Holdings, Inc. | Needs Review | Landscape balance-sheet page and a completeness warning for a separately undetected Comprehensive Income section; default recommendation `Needs Review` |
| Malaya Northstar Manufacturing Corp. | Accept | All seeded validation rows pass; default recommendation `Accept` |
| Haraya Logistics and Trade, Inc. | Revert | Key pages reference Haraya Transport Services, period text says 2024 rather than submitted 2025, and one balance-sheet page is unreadable; default recommendation `Revert` |

The current database inspection showed these as document IDs 1, 2, and 3 respectively. The IDs are database state, not a contract for future databases.

`storage.ensure_all_demo_documents()` loops over `demo_suite`. For an existing filename, it checks whether page analysis exists and avoids replacing the existing analysis. It also creates the default reviewer action only when one does not already exist. This presence-guard behavior is intended to keep seeded demo content and reviewer work from being overwritten on normal app restarts.

The JSON file also retains legacy top-level `demo_document`, `sample_pages`, `sample_validations`, and `sample_figures` values used by fallback and compatibility paths.

## L. Editable Configuration

| File | Current role |
|---|---|
| `config.py` | App title/subtitle/agency wording, intake defaults, file paths, page-priority list, ranking metric options, status order, and text-preview length (`2000`) |
| `demo_data.json` | Legacy sample document content, three-document demo suite, seeded figures/validations, five-year historical data, and five-company ranking data |
| `label_mapping.json` | Raw financial-label aliases mapped to normalized fields |
| `revert_reasons.json` | Reviewer revert-reason dropdown values |
| `sample_company_master.json` | Fictional Audentia master identity, registration number, year, and descriptive reference data |
| `.streamlit/config.toml` | Streamlit server defaults, theme colors, headless address, CORS/XSRF settings, and local port |
| `.replit` | Replit modules, deployment target, workflows, ports, and Python Streamlit workflow command |
| `requirements.txt` | Python package dependencies for the prototype |

Settings / Editable Demo Data displays these values but does not edit them.

## M. Current Display / Formatting Rules

- **Agency wording:** the hero uses `AFS Validation and Figure Extraction MVP · Securities and Exchange Commission`. Other seeded/demo text can still say `SEC Philippines`, and the sidebar caption says `Philippine AFS QA dashboard prototype`.
- **Timestamps:** dashboard upload timestamps are formatted by `format_timestamp_pst()` as `16 Jul 2026, 9:59 AM PST` style. The helper parses the stored ISO-like string and appends `PST`; it does not perform timezone conversion.
- **Peso values:** `format_peso()` displays full values with the peso sign, comma grouping, and two decimal places, for example `₱2,901,400,000.00`. Underlying numeric values are unchanged.
- **Theme:** `app.py` and `.streamlit/config.toml` use a green SEC/eFAST-inspired theme with a dark-green sidebar, green hero, white cards, and green chart colors.
- **Live/demo disclosures:** the dashboard labels its database metrics `Live DB Data`; Historical and Rankings show `Demo Projection`; Settings shows `Reference Only — No Live Editing`; fallback analysis shows a warning that demo data was substituted.
- **Review banner:** Document Review and Figures Review show the active company, registration number, period, report type, and submission in a `Currently Reviewing` card.
- **Evidence safety:** dynamic page text and reviewer-history values are HTML-escaped before being placed into custom markup.

## N. Known Limitations

The current implementation supports only a prototype review experience:

- extracted text is required for normal page analysis and figure extraction;
- scanned/image-only PDFs have no general OCR path;
- PDF extraction is text-based and table/layout understanding is limited;
- page classification and validation use keywords, exact labels, and heuristics;
- the readability signal is text length, not image inspection;
- confidence is fixed or seeded estimated metadata rather than a calculated score;
- demo figure fallback can display values that do not come from the uploaded document;
- the Audentia company master is the only master record used by the current validation engine;
- historical and ranking views are seeded JSON projections, not database-driven;
- reviewer action storage is an upsert per document, not an append-only audit trail;
- replacing analysis on reprocessing deletes and reinserts analysis rows for that document;
- there are no declared foreign keys or cascading deletes;
- SQLite and per-operation connections are suitable for prototype scale, not demonstrated concurrent production workloads;
- there is no user authentication, authorization, reviewer identity, or production audit identity;
- there is no live SEC/eFAST integration, API integration, background queue, or production monitoring;
- the upload filename is used as the local storage target without an application-level filename policy; and
- session state is in-memory per Streamlit session and is not a shared workflow state service.

## O. Current Technology Stack

### SEC eFAST Checkers implementation

- Python 3.11 runtime in Replit
- Streamlit
- pandas
- SQLite via Python's standard-library `sqlite3`
- PyMuPDF (`fitz`) for primary PDF text extraction
- pdfplumber for fallback PDF text extraction
- Python standard-library modules including `json`, `re`, `pathlib`, `datetime`, `sqlite3`, and `difflib`

### Declared Python dependencies

`requirements.txt` declares `streamlit`, `pandas`, `pymupdf`, `pdfplumber`, `pillow`, and `openpyxl`. Pillow and openpyxl are declared but are not directly imported by the current SEC Python modules inspected.

### Broader workspace

The repository also contains a pnpm/TypeScript workspace with an Express/PostgreSQL/Drizzle API scaffold and a React/Vite artifact package. The current Streamlit app does not import or call those modules. The SEC artifact package is used as the workflow directory while the workflow starts the root `app.py`.

## P. Current Project Structure

```text
.
├── app.py                         # Streamlit entry point and navigation
├── config.py                      # App/config constants and paths
├── db.py                          # SQLite schema and persistence helpers
├── storage.py                     # JSON loading, demo seeding, read helpers
├── pdf_utils.py                   # PDF extraction and quality proxy
├── validation_engine.py            # Page classification and validation rules
├── extraction_engine.py           # Regex-based figure extraction
├── normalization.py                # Label mapping and amount normalization
├── ui_helpers.py                   # Shared UI and formatting helpers
├── pages/
│   ├── dashboard.py
│   ├── upload_intake.py
│   ├── document_review.py
│   ├── figures_review.py
│   ├── historical_company.py
│   ├── rankings.py
│   └── settings_demo_data.py
├── demo_data.json                  # Demo suite and seeded projection data
├── label_mapping.json              # Figure-label aliases
├── revert_reasons.json             # Revert dropdown values
├── sample_company_master.json      # Fictional company master
├── data/
│   └── sec_efast_checkers.sqlite   # Runtime SQLite database
├── uploads/                        # Local uploaded-file directory
├── requirements.txt                # Python dependencies
├── README.md                       # Short run and behavior guide
├── .streamlit/config.toml          # Streamlit server/theme settings
├── .replit                         # Replit workflows/deployment settings
└── artifacts/
    ├── sec-efast-checkers/         # Replit artifact/workflow metadata
    ├── api-server/                 # Separate TypeScript API artifact
    └── mockup-sandbox/             # Separate design-preview artifact
```

## Q. How to Run the Prototype

### Local/manual command

From the repository root:

```bash
streamlit run app.py --server.port 5000
```

The command is documented in `README.md`. The Streamlit config also defaults to address `0.0.0.0`, headless mode, and port `5000`.

### Replit workflow

The configured SEC workflow is:

```text
cwd: ./artifacts/sec-efast-checkers
streamlit run ../../app.py --server.port $PORT --server.address 0.0.0.0
```

Replit supplies the workflow `PORT` value. The workflow is path-routed through the `artifacts/sec-efast-checkers` artifact. The separate API-server and mockup-sandbox workflows are not required by the Streamlit prototype.

On each Streamlit session start, `app.py` calls `init_db()`, seeds the company master if needed, and ensures the demo suite. The app therefore expects the JSON files and the `data/`/`uploads/` paths to be available relative to the project root.
