# Multi-Year AFS Support V1 — Validation

## 1. Scope

Multi-Year AFS Support V1 adds structured reporting-year intake and year-aware AFS figure review for:

- current period only;
- current period plus one comparative year; and
- current period plus two comparative years.

The enhancement reuses the existing `documents.comparative_years` metadata field and `extracted_figures.fiscal_year` column. It does not redesign the schema or modify GIS, Historical View, Rankings, demo seeding, AFS completeness rules, reviewer disposition, or Test Upload Management.

No OCR, NLP, ML, external API, or new dependency was added.

## 2. Exact files changed

- `extraction_engine.py` — extends the existing text-based figure matcher to capture selected year/value pairs within one detected financial-label segment.
- `pages/upload_intake.py` — replaces the free-text comparative-year field with structured controls and year validation.
- `pages/figures_review.py` — adds reporting-year roles, fiscal-year filtering, year-specific buckets, and current-year-only revenue.
- `docs/MULTI_YEAR_AFS_SUPPORT_V1_VALIDATION.md` — records the implementation and validation results.

## 3. Updated Upload / Intake year controls

Upload / Intake retains `Period Covered Year` and replaces the comma-separated Comparative Years input with:

1. `Comparative Figures Included?`
   - No
   - Yes
2. `Number of Comparative Years`, shown only when Yes is selected:
   - 1
   - 2
3. `Comparative Year 1`
4. `Comparative Year 2`, shown only when 2 comparative years are selected

For a 2025 period, the editable comparative defaults are:

- Comparative Year 1: 2024
- Comparative Year 2: 2023

When No is selected, no comparative-year inputs are shown and no comparative years are stored or passed to extraction.

## 4. Year validation rules

Submission is blocked before a document record or file is created when:

- more than two comparative years are supplied;
- comparative years are duplicates;
- a comparative year equals the Period Covered Year; or
- a comparative year is later than the Period Covered Year.

The interface itself exposes a maximum of two comparative years.

## 5. How reporting years are stored and passed to extraction

No database migration was required.

The existing `documents.comparative_years` text field is preserved for backward compatibility:

- Current only: empty string
- One comparative: `2024`
- Two comparatives: `2024, 2023`

The existing `fiscal_year_candidates()` helper builds a descending, deduplicated reporting-year list from the Period Covered Year and comparative metadata.

Examples:

- `2025` → `[2025]`
- `2025` plus `2024` → `[2025, 2024]`
- `2025` plus `2024, 2023` → `[2025, 2024, 2023]`

Existing documents with comma-separated comparative-year metadata and callers supplying a year list remain supported.

## 6. How `extracted_figures.fiscal_year` is used

The extraction engine receives all selected reporting years.

For each supported financial label, it limits year/value matching to that label's text segment, ending at the next supported financial label. It creates one row for each selected fiscal year that has a recognized adjacent value in that segment.

Each created row preserves its detected year in `extracted_figures.fiscal_year`.

The engine does not:

- create a row for an absent year/value;
- copy a current-year value into a comparative year;
- copy one comparative value into another year; or
- search another financial label's segment to fill a missing value.

## 7. Figures Review multi-year behavior

Near the top of AFS Figures Extraction Review, the page now displays reporting-year metadata such as:

`Reporting Years: 2025 · 2024 · 2023`

The role caption identifies:

- 2025 = Current
- 2024 = Comparative
- 2023 = Comparative

`View Fiscal Year` provides:

- All Years
- one Current option for the Period Covered Year when extracted rows exist for it;
- Comparative options only for other fiscal years that have extracted rows.

The filter changes the review table and Normalized Figure Buckets while preserving the current-year hero metric.

The review table retains:

- Normalized Label
- Fiscal Year
- Year Role
- Displayed Value
- Normalized Peso Value
- Confidence
- Status
- Reviewed / Corrected Value

Existing corrections continue to save by figure-row ID, so filtering does not change the database update contract.

## 8. Normalized bucket grouping behavior

Normalized Figure Buckets are now grouped by:

- `normalized_label`
- `fiscal_year`
- displayed Year Role

Values from different fiscal years are never summed into one cross-year total.

Example:

| Field | Fiscal Year | Year Role | Total |
|---|---:|---|---:|
| total_assets | 2025 | Current | ₱1,248,900,000 |
| total_assets | 2024 | Comparative | ₱1,074,500,000 |
| total_assets | 2023 | Comparative | ₱991,200,000 |

## 9. Current-year hero metric behavior

`Current Revenue` now filters figure rows to the selected document's `period_covered_year` before evaluating supported revenue labels.

It does not use a comparative-year amount even when the comparative amount is larger.

The browser test used:

- 2025 revenue: ₱100,000,000
- 2024 revenue: ₱999,000,000
- 2023 revenue: ₱888,000,000

The displayed Current Revenue remained ₱100,000,000.00 in All Years and comparative-year filtered views.

## 10. CSV export behavior

The main figure export remains row-oriented and is not pivoted.

`fiscal_year` remains included in the exported data. The added `year_role` field is also included in the current review export.

The browser test successfully initiated an export named `sec_efast_figures_document_9.csv`. Production data-frame verification confirmed that `fiscal_year` is retained in the exported column set.

## 11. Test results A–I

| Scenario | Expected | Actual | Pass/Fail |
|---|---|---|---|
| A. 2025 only | Reporting Years is 2025 with no comparative controls/results | Comparative controls were hidden when No was selected; the uploaded PDF contained other years but only 2025 rows were extracted and only 2025 was filterable | Pass |
| B. 2025 + 2024 | Both years stored and available | Reporting-year construction returned `[2025, 2024]`; one-comparative UI showed only Comparative Year 1 and the extractor produced separate rows for both selected years | Pass |
| C. 2025 + 2024 + 2023 | All three years recognized and filterable | Reporting Years showed `2025 · 2024 · 2023`; all three year-role filter options appeared and each filter showed only its fiscal-year rows | Pass |
| D. Duplicate comparative year | Submission prevented | `2024 / 2024` was blocked with `Comparative years must not be duplicates.` and no success/document creation occurred | Pass |
| E. Comparative year equal to or later than current | Submission prevented | `2025 / 2023` was blocked as equal; `2026 / 2023` was blocked as later than 2025 | Pass |
| F. Same label across current and comparative years | Separate extracted rows by fiscal year | Total Assets, Total Liabilities, Revenue, Net Income, and Operating Cash Flow produced independent rows for each available selected year; absent year/value pairs were not created | Pass |
| G. Normalized Figure Buckets | Same label remains separate by fiscal year | All Years displayed separate 2025, 2024, and 2023 buckets for the same normalized labels with no cross-year sum | Pass |
| H. Current Revenue | Uses Period Covered Year only | Current Revenue displayed ₱100,000,000.00 and ignored larger 2024/2023 comparative revenue amounts | Pass |
| I. Existing demo documents | Three demos remain intact and app runs normally | Documents 1–3, 19 seeded figure rows, and original Malaya/Haraya reviewer actions remained intact; the app and demo navigation continued to run | Pass |

## 12. Demo-data impact

No seeded demo metadata, pages, validations, figures, reviewer actions, or source JSON were changed.

Final live database verification showed:

- Document 1: Audentia Fortuna Holdings, Inc.
- Document 2: Malaya Northstar Manufacturing Corp.
- Document 3: Haraya Logistics and Trade, Inc.
- Seeded extracted figures: 19
- Existing reviewer actions: Malaya Accept and Haraya Revert

The two browser-created test uploads were deleted through Test Upload Management after validation. Their document, page, validation, figure, reviewer, and local-file data were removed.

## 13. Known limitations

1. Advanced table-aware, multi-column extraction is not implemented.
2. OCR is not implemented. Image-only or low-text comparative tables remain unsupported.
3. Multi-year extraction requires recognizable year/value text within the same short financial-label segment.
4. Only selected reporting years are considered; other years visible in the PDF are intentionally ignored.
5. The prototype supports a maximum of two comparative years.
6. Demo records may list comparative metadata even when their pre-seeded figure rows contain only one fiscal year. Reporting Years reflects metadata, while filter options reflect fiscal years with actual extracted rows.
7. Existing label normalization behavior is unchanged; some detailed revenue labels may normalize to the broader `revenue` bucket.
8. The Test Uploads analysis status may show an existing validation failure when a synthetic test PDF does not match company/master or completeness rules. This is independent of multi-year extraction.

## 14. Final assessment

**Safe for prototype testing.**

The requested current-only, one-comparative, and two-comparative flows work without a schema migration. Year/value rows remain distinct, cross-year bucket aggregation is prevented, current revenue is period-specific, existing demos remain intact, and Test Upload Management continues to clean up temporary records safely.

Advanced table-aware multi-column extraction and OCR are explicitly not implemented in this V1.