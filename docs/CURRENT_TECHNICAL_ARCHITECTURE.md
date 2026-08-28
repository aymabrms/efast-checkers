# SEC eFAST Checkers — Current Technical Architecture

This document describes the architecture currently implemented by the Python Streamlit prototype.

## 1. Architectural Summary

The prototype is a single-process Streamlit application. Page modules call shared Python helpers directly. SQLite is the persistence layer for uploaded-document metadata, analysis results, extracted figures, and the current reviewer action. JSON files provide configuration, the fictional company master, demo-suite content, label aliases, revert reasons, historical data, and rankings.

```text
                         Replit Streamlit workflow
                                   |
                                   v
                              app.py
        +-----------------------+------------------------+
        |                       |                        |
        v                       v                        v
   Sidebar/page            bootstrap()             shared UI helpers
   registry + state       init_db() + seed         ui_helpers.py
        |                  company/demo data
        v
  pages/*.py
        |
        +-------------------------+--------------------------+
        |                         |                          |
        v                         v                          v
  pdf_utils.py             validation_engine.py       extraction_engine.py
  PDF text/geometry        page rules/checks          regex figure rows
        |                         |                          |
        +-------------------------+--------------------------+
                                  |
                                  v
                         db.py / SQLite file
                       data/sec_efast_checkers.sqlite
```

The application does not currently use the separate TypeScript API server, PostgreSQL/Drizzle packages, or external integrations.

## 2. Application Entry and Navigation

`app.py`:

1. configures Streamlit for a wide layout;
2. injects the green theme CSS;
3. initializes SQLite;
4. seeds the company master and demo suite;
5. renders the hero and custom sidebar;
6. resolves the current page from session state; and
7. calls the selected page's `render()` function.

The `PAGES` dictionary maps these labels to page functions:

```text
Dashboard
Upload / Intake
Document Review
AFS Figures Extraction Review
Historical Company View
Rankings / Research View
Settings / Editable Demo Data
```

Programmatic navigation uses:

- `_nav_to`: a one-shot target set by Dashboard and consumed with `pop()`;
- `_current_page`: the current sidebar page label; and
- `nav_radio`: the Streamlit widget key.

The selected document is stored separately as `active_document_id`. It is not stored in the database as a current-session concept.

## 3. Configuration and Seed Bootstrapping

At session startup:

```text
main()
  -> apply_styles()
  -> bootstrap()
       -> init_db()
       -> seed_company_master()
       -> ensure_all_demo_documents()
```

`config.py` supplies paths and defaults. `storage.py` loads:

- `demo_data.json`;
- `sample_company_master.json`; and
- `revert_reasons.json`.

The demo seed helper identifies existing demo documents by filename. If analysis exists for that document, it leaves the existing analysis alone. It also creates the default reviewer action only when one is absent. This is the current mechanism used to preserve reviewer work across normal restarts.

## 4. Intake and PDF Processing Flow

```text
Streamlit file_uploader + metadata
              |
              v
       insert_document()
              |
              v
   prepare_uploaded_file()
       uploads/<filename>
              |
              v
       extract_pdf_pages()
          /             \
   PyMuPDF succeeds   no pages
        |                |
        v                v
  page dictionaries   pdfplumber fallback
        |                |
        +-------+--------+
                |
                v
         analyze_pages()
```

Each extracted page contains page number, full extracted text in the temporary page dictionary, a `text_preview` capped at `TEXT_PREVIEW_MAX_CHARS` (currently 2,000), orientation, and dimensions.

PyMuPDF is attempted first. If it produces no pages, pdfplumber is attempted. Parser errors are collected and shown as warnings. The upload flow does not store the original PDF bytes in SQLite; the local file is stored in `uploads/`.

If no pages are available, the upload flow analyzes `demo_data.json` sample pages and substitutes demo validations and figures. If pages exist but figure extraction returns no rows, it substitutes demo figures while preserving the analyzed pages/validations. `last_fallback_doc_id` is held in session state so Figures Review can show the fallback warning for that document.

## 5. Page Analysis and Validation Flow

```text
raw PDF page dictionaries
          |
          v
validation_engine.analyze_pages()
  - page type from keyword classifier
  - orientation
  - quality flag
  - fuzzy company match
  - expected-year presence
  - stored text preview
          |
          v
validation_engine.validate_document()
  - company master + SEC registration
  - period
  - submission type
  - orientation
  - completeness
  - readability
          |
          v
validation rows + final recommendation
```

`validate_document()` operates on `text_preview` values. It builds the combined text, applies deterministic checks, and writes validation rows through `replace_document_analysis()` along with page and figure rows.

The rule outcome reduction is:

```text
any Failed  -> Revert
else any Warning -> Needs Review
else         -> Accept
```

Validation is not an external rules service and does not use a production company registry.

## 6. Page Classification

`classify_page()` lowercases text and iterates through the ordered `PAGE_RULES` list. It returns the first matching page type or `Other / Unclassified`. The recognized labels and keywords are documented in `CURRENT_PROTOTYPE_DOCUMENTATION.md`, Section E.

Classification and completeness are coupled: completeness compares the returned strings to exact required labels. A content section can therefore be present in text but absent from the completeness result if it does not match the classifier's expected wording.

## 7. Figure Extraction and Normalization Flow

```text
analyzed page.text_preview + intake years
                  |
                  v
       fiscal_year_candidates()
                  |
                  v
       detect_unit_basis(page text)
                  |
                  v
  for each mandatory label and year:
      case-insensitive regex search
                  |
                  v
        parse_amount(displayed value)
                  |
                  v
        normalize_label(raw label)
                  |
                  v
  figure row: source fields + normalized fields
```

`fiscal_year_candidates()` combines the current period year with years parsed from the comparative-years input and returns unique years descending.

The extractor requires a label followed by a year followed by a numeric value. It supports a fixed mandatory label list. Amount parsing removes commas and `₱`, treats parentheses as negative, and scales values based on one page-level unit basis (`Pesos`, `Thousands`, or `Millions`).

`normalize_label()` compares cleaned aliases from `label_mapping.json`. If no alias matches, it converts the cleaned raw label to snake_case. The current extractor assigns `confidence = 0.82` to dynamically extracted rows; seeded rows carry their own fixed values.

## 8. Reviewer Correction Flow

```text
get_figures(document_id)
          |
          v
figures_review.py builds editable DataFrame
  - disables source/extraction fields
  - enables review_status
  - enables reviewed_value
  - displays confidence as estimated percent
          |
          v
Save Corrections
          |
          v
update_figure_reviews(document_id, rows)
  - update by figure id AND document id
  - set reviewed_value
  - set reviewer_edited
  - set review_status
```

The correction path restores the original raw confidence from the pre-display DataFrame before preparing update records. It does not change the stored normalized numeric amount.

Reviewer disposition follows a separate path:

```text
validation rows
    |
    v
system recommendation + suggested reason
    |
    v
reviewer selects recommendation/reason and enters remarks
    |
    v
save_reviewer_action()
    |
    v
reviewer_actions row, one current row per document
```

The `reviewer_actions.document_id` uniqueness constraint and upsert logic mean repeated saves update the current row rather than forming a complete append-only action history.

## 9. Database Persistence

`db.py` creates these tables:

```text
company_master
documents
page_analysis
validations
extracted_figures
reviewer_actions
```

Logical relationships:

```text
documents.id
  ├── page_analysis.document_id
  ├── validations.document_id
  ├── extracted_figures.document_id
  └── reviewer_actions.document_id
```

These are application-level relationships. The current schema does not declare foreign-key constraints or cascades.

`replace_document_analysis()` performs deletes and inserts for the three analysis tables for one document in one SQLite connection/commit. `execute()` and `query()` open a new connection for each operation. The code does not implement connection pooling or concurrent job processing.

## 10. Historical, Rankings, and Settings Data Flow

```text
demo_data.json
  ├── historical_data -> Historical Company View
  ├── ranking_data    -> Rankings / Research View
  ├── demo_suite      -> bootstrap seed -> SQLite
  └── legacy samples  -> upload fallback / compatibility paths
```

Historical and ranking screens do not read the SQLite figure tables. Settings reads and displays JSON/config values without writing them.

## 11. Module Dependencies

```text
app.py
  -> config.py
  -> db.py
  -> storage.py
  -> pages/*.py

pages/upload_intake.py
  -> pdf_utils.py
  -> validation_engine.py
  -> extraction_engine.py
  -> storage.py
  -> db.py

pages/document_review.py
  -> storage.py
  -> db.py
  -> validation_engine.py
  -> ui_helpers.py

pages/figures_review.py
  -> storage.py
  -> db.py
  -> ui_helpers.py

validation_engine.py
  -> pdf_utils.py
  -> config.py

extraction_engine.py
  -> normalization.py

normalization.py
  -> config.py
  -> label_mapping.json

storage.py
  -> config.py
  -> db.py
  -> demo_data.json
  -> sample_company_master.json
  -> revert_reasons.json
```

## 12. Runtime Boundaries

The configured Replit workflow runs:

```text
cwd: ./artifacts/sec-efast-checkers
streamlit run ../../app.py --server.port $PORT --server.address 0.0.0.0
```

The working application source is the root Python app. The `artifacts/sec-efast-checkers` directory contains artifact/workflow metadata and package metadata; it is not the source of the current Streamlit pages.
