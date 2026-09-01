# Presentation Polish and Multi-Year Display V1 — Validation

## 1. Exact files changed

- `app.py`
  - Removes the repeated main-content brand hero.
  - Keeps the system name and updated description in the sidebar.
- `config.py`
  - Updates the configured system subtitle.
- `ui_helpers.py`
  - Replaces the shared unsafe-HTML Currently Reviewing banner with native Streamlit containers, columns, captions, and text.
- `pages/figures_review.py`
  - Shows all declared reporting years in the fiscal-year filter.
  - Displays a clear empty state when a reporting year has no extracted figures.
  - Preserves separate Current and Comparative rows and buckets.
  - Applies display-only comma and two-decimal peso formatting to normalized values and bucket totals.
- `storage.py`
  - Idempotently backfills only comparative demo rows explicitly recovered by the existing extraction engine from seeded page text.
- `docs/PRESENTATION_POLISH_MULTIYEAR_DISPLAY_V1_VALIDATION.md`
  - Records the implementation and validation results.

The SQLite database received additional seeded comparative figure rows, but its schema was not changed.

`demo_data.json` was not changed.

## 2. Banner removal result

The large dark-green main-content banner that repeated:

- SEC eFAST Checkers
- AFS Validation and Figure Extraction MVP
- Securities and Exchange Commission

was removed.

The associated unused `.app-hero` styles were also removed.

Each main page now begins directly with its existing page title, including:

- Dashboard
- Upload / Intake
- Document Review
- AFS Figures Extraction Review
- Historical Company View
- Rankings / Research View

The normal page titles were not removed or renamed.

## 3. Sidebar subtitle change

The sidebar still displays the main system name:

`SEC eFAST Checkers`

The subtitle is now:

`GIS & AFS Reviewer Assistance Prototype`

The word `Philippine` is not used in this subtitle.

## 4. Raw HTML root cause and fix

### Root cause

The shared `reviewing_banner()` helper assembled GIS-specific `<div>` elements as one HTML string and interpolated them inside a second multiline HTML block. Streamlit could expose portions of this nested markup as reviewer-visible raw text.

The helper was shared by:

- Document Review
- AFS Figures Extraction Review

### Fix

The shared helper now uses native Streamlit components:

- `st.container(border=True)`
- `st.columns`
- `st.caption`
- `st.write`

No `unsafe_allow_html` call remains inside `reviewing_banner()`.

The section displays:

- Company
- SEC Registration No.
- Period
- Report Type
- Submission

For GIS, it additionally displays:

- Corporation Type
- Period Covered

Browser validation confirmed that no HTML tags or markup are visible in either review screen.

## 5. Multi-year figure-display root cause

The issue had two parts:

1. The seeded Audentia and Malaya documents declared reporting years `2025 · 2024 · 2023`, but their stored extracted-figure rows contained only 2025 values.
2. The fiscal-year selector was built only from years already present in extracted figures. As a result, a declared reporting year with no extracted rows could not be selected to show an explicit empty state.

The existing table and bucket filter already operated on the selected dataframe. Once valid comparative rows were available, it correctly supported year-specific display.

## 6. Seeded demo data adjustment

A small idempotent reconciliation now runs only for seeded demo documents.

It:

- reads the existing stored seeded page text;
- uses the existing extraction engine and declared reporting years;
- inserts only missing rows for years earlier than the current period;
- reuses the curated seeded normalized label for the same raw label;
- preserves existing current-year rows;
- preserves reviewer edits and reviewer dispositions; and
- does not create duplicate rows on later restarts.

Results:

- Audentia: seven explicit 2024 comparative rows added.
- Malaya: seven explicit 2024 comparative rows added.
- Haraya: no rows added because its stored seeded page text does not contain extractable comparative figure values.
- 2023: no rows added for any document.

The three seeded demo documents themselves were not replaced or deleted.

## 7. Confirmation no comparative figure was invented

No comparative amount was estimated, interpolated, copied from Historical View, copied from Rankings, or generated from a current-year value.

Every added 2024 row was recovered by the existing deterministic extraction engine from explicit year/value evidence in the seeded AFS page text.

No 2023 amount was created because no supported 2023 financial figure was extracted from those seeded pages.

## 8. All Years behavior

When `View Fiscal Year = All Years`:

- all actually stored extracted years are displayed;
- Audentia and Malaya show 2025 rows as `Current`;
- Audentia and Malaya show recovered 2024 rows as `Comparative`;
- no synthetic 2023 rows appear;
- the Extracted Figures Review Table includes Fiscal Year and Year Role; and
- Normalized Figure Buckets group independently by Field, Fiscal Year, and Year Role.

Current Revenue remains calculated from the document’s current Period Covered Year only.

## 9. Specific-year filter behavior

The selector now includes the union of:

- declared reporting years; and
- years with actually extracted rows.

Behavior:

- `2025 — Current` shows only 2025 rows and 2025 buckets.
- `2024 — Comparative` shows only 2024 rows and 2024 buckets.
- `2023 — Comparative` shows:

  `No extracted figures are available for fiscal year 2023. No comparative values were generated for this year.`

No empty-year values are generated.

## 10. Normalized Figure Buckets behavior

Normalized Figure Buckets continue to aggregate only safely normalized numeric values.

The displayed columns are:

- Field
- Fiscal Year
- Year Role
- Total (₱)

All Years distinguishes Current and Comparative rows. A selected fiscal year restricts buckets to that year. A year without extracted figures displays the explicit empty state instead of an empty or fabricated bucket table.

## 11. Peso display formatting

Display-only formatting now uses:

- peso symbol;
- comma separators; and
- two decimal places.

Example:

`₱1,248,900,000.00`

This formatting applies to:

- normalized peso values in the figure review table;
- normalized bucket totals; and
- the existing Current Revenue summary.

Stored numeric values remain numeric and unchanged.

Raw source `Displayed Value` text remains unchanged so reviewers can compare the source representation.

## 12. Regression test results A–K

| Test | Expected | Actual | Result |
|---|---|---|---|
| A. Dashboard | Dashboard still works | Dashboard loaded directly without the repeated hero | Pass |
| B. Upload / Intake AFS and GIS | Both modes remain operational | Existing AFS and GIS field sets rendered and switched correctly | Pass |
| C. AFS Completeness Check | Unchanged | Existing AFS completeness UI and rules remained available | Pass |
| D. GIS Review Lite | Unchanged | GIS upload completed, completeness passed, and BOD remained Conditional / Legacy | Pass |
| E. OCR source traceability | Unchanged | Page review continued to display Text Source evidence | Pass |
| F. Computed Confidence + HITL | Unchanged | Confidence score, classification, explanation, and review controls rendered | Pass |
| G. Reviewer Disposition | Human-controlled | Reviewer disposition controls remained available; no automatic recommendation was saved | Pass |
| H. Figure corrections | Corrections still save | A temporary Audentia correction saved successfully and was then fully restored | Pass |
| I. Fiscal-year filtering | All Years, 2025, 2024, and empty 2023 behave correctly | All filter states matched the required behavior | Pass |
| J. Three seeded demos | Preserved | Audentia, Malaya, and Haraya remained listed and protected | Pass |
| K. No visible raw HTML | No markup visible | Native Currently Reviewing fields rendered in both review screens | Pass |

Database verification after testing confirmed the temporary correction was restored to:

- `reviewed_value = ""`
- `reviewer_edited = 0`
- `review_status = "Needs Review"`

Temporary GIS uploads were deleted through Test Upload Management.

## 13. Known limitations

1. Comparative backfill is limited to rows recoverable by the existing supported-label extraction engine.
2. Some narrative values present in page text may remain unextracted when they fall outside existing extraction behavior; this patch does not change the extraction engine.
3. A reporting year may be declared in metadata without having extractable figures; the UI now represents this honestly with an empty state.
4. Raw source values retain their original display text and punctuation.
5. The Current Revenue card continues to choose the highest supported current-year revenue field under the existing logic.
6. Existing Streamlit/Vega empty-chart scale warnings remain non-blocking and were not changed in this scope.
7. Historical View and Rankings remain seeded projection views and were not changed.

## 14. Final assessment

**Safe for prototype testing**

The repeated hero was removed, sidebar branding was updated, raw HTML was eliminated from the shared review banner, multi-year rows and filters now reflect actual extracted evidence, empty reporting years are explicit, and financial display formatting is presentation-only. GIS/AFS rules, OCR, confidence/HITL, reviewer disposition, database schema, Historical View, Rankings, and BOD behavior remain unchanged.