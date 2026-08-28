# SEC eFAST Checkers — Current Feature Status

This matrix reflects the current implementation, not a proposed roadmap.

| Feature | Status | Implementation Type | Current Data Source | Notes |
|---|---|---|---|---|
| Seven-screen Streamlit navigation | Working | Live UI/session state | `app.py` page registry | Sidebar radio navigation |
| Duplicate auto-generated top navigation suppression | Working | CSS presentation cleanup | `app.py` styles | Hides Streamlit sidebar nav block; does not change page logic |
| Dashboard metrics | Working | Database-driven | SQLite documents, validations, figures, actions | Counts are current database aggregates |
| Dashboard document queue | Working | Database-driven | SQLite `documents` plus latest `reviewer_actions` | Source label is filename-based Demo/Uploaded inference |
| Dashboard Open in Review | Working | Session-state navigation | Streamlit session state | Sets active document and reruns |
| PDF upload and local save | Working | Real local file handling | Uploaded PDF and `uploads/` | Filename is used as local target |
| PyMuPDF PDF text extraction | Working | Real parser integration | Uploaded PDF text layer | No general OCR |
| pdfplumber fallback | Partial | Real parser fallback | Uploaded PDF | Used only when primary extraction returns no pages |
| Demo fallback after weak/no extraction | Partial | Seeded/demo fallback | `demo_data.json` | Warning is displayed; substituted figures may not represent upload |
| AFS page classification | Working | Keyword heuristic | Page text preview | First matching keyword rule wins |
| Company master validation | Partial | Fuzzy/literal heuristic | Audentia `sample_company_master.json` plus page text | No multi-company master lookup |
| SEC registration validation | Partial | Literal substring check | Page text plus company master | Included in company-master rule, not a separate rule |
| Period-covered validation | Working | Year-presence heuristic | Intake metadata and page previews | No standalone comparative-year check |
| Comparative-year validation | Not Implemented | — | — | Comparative years feed extraction candidates/display only |
| Submission-type validation | Working | Phrase/metadata heuristic | Page previews and intake metadata | Checks `financial statements` or report type `AFS` |
| Page orientation validation | Working | Geometry rule | PDF page dimensions or seeded orientation | Any landscape page creates a warning |
| Readability/image-quality signal | Partial | Text-length proxy | Extracted text or seeded flag | Not actual image analysis |
| Completeness validation | Partial | Exact page-type comparison | Classified page types | Sensitive to classification labels and wording |
| Suggested revert reasons | Working | Configured rule output | `revert_reasons.json`, validation rows | Returns the first non-empty suggestion |
| System recommendation | Working | Deterministic rule reduction | Validation statuses | Failed → Revert; Warning → Needs Review; otherwise Accept |
| Document Review evidence | Working | Database-driven UI | SQLite page/validation rows | Text preview only; no PDF image viewer |
| Document Review page source tags | Working | Presentation helper | Page type values | Primary vs Supporting labels |
| Reviewer disposition save | Working | SQLite upsert | `reviewer_actions` | Saves recommendation, reason, remarks |
| Reviewer action history | Partial | Database-backed current action | SQLite `reviewer_actions` | Unique document ID means latest action replaces prior action |
| Active document state | Working | Streamlit session state | `active_document_id` | Shared across pages in one session |
| Switch document control | Working | Session-state selector | SQLite `documents` | No unsaved-change warning |
| AFS figure label extraction | Partial | Regex-based parser | Page text previews | Limited mandatory label/year/value pattern |
| Figure label normalization | Working | Alias mapping | `label_mapping.json` | Unknown labels fall back to cleaned snake_case |
| Peso/unit normalization | Working | Deterministic parser | Displayed value and page unit text | Handles Pesos, Thousands, Millions and parentheses |
| Figure source snippets | Working | Text-window extraction | Page text preview | Approximately ±45 characters around match |
| Figure confidence display | Partial | Fixed/seeded estimate | Extractor default or demo JSON | Displayed as `x% · Est.`; no calculated model |
| Figure review table | Working | Streamlit editable data table | SQLite figures | Reviewer edits status and reviewed value |
| Save figure corrections | Working | ID/document-constrained updates | SQLite `extracted_figures` | Does not revise normalized numeric value |
| Extracted figures CSV export | Working | In-memory CSV export | Current displayed figure table | Internal ID omitted |
| Normalized figure buckets | Working | Runtime aggregation | Current document figure rows | Groups and sums normalized peso values |
| Historical Company View | Demo / Seeded | Seeded projection UI | `demo_data.json` historical data | Does not query uploaded/reviewed figures |
| Historical CSV export | Demo / Seeded | Seeded projection export | `demo_data.json` | Fictional Audentia history |
| Rankings / Research View | Demo / Seeded | Seeded projection UI | `demo_data.json` ranking data | Sorts five fictional companies |
| Ranking CSV export | Demo / Seeded | Seeded projection export | `demo_data.json` | Selectable configured revenue metric |
| Settings / Editable Demo Data | Working | Read-only reference UI | JSON/config files | No live editing despite page title |
| Three-company demo suite | Demo / Seeded | Presence-guarded seed data | `demo_data.json` and SQLite | Audentia Needs Review, Malaya Accept, Haraya Revert |
| Demo seed preservation | Working | Seed guard | SQLite analysis/action presence | Avoids normal restart overwrite of seeded analysis/reviewer work |
| User authentication | Not Implemented | — | — | No authentication or authorization flow |
| OCR | Not Implemented | — | — | Fallback uses demo data rather than OCR |
| Live SEC/eFAST integration | Not Implemented | — | — | No external API/filing connectivity |
| Production audit trail | Not Implemented | — | — | Reviewer actions are per-document upserts |
| Background processing/queue | Not Implemented | — | — | Processing occurs during Streamlit interaction |
