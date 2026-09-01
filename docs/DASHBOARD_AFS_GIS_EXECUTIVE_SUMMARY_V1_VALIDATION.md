# Dashboard AFS / GIS Executive Summary V1 — Validation

## 1. Scope

This focused update changes the Dashboard from a document-review launcher into an executive and operational summary of stored AFS and GIS records.

Implemented:

- an All Reports / AFS / GIS Report View filter;
- report-level summary cards;
- a filtered informational Recent Document Queue;
- Reports by Type;
- Review Outcomes by Report Type;
- Top Validation Issues; and
- removal of Dashboard document-opening controls and AFS-only default charts.

No other module was redesigned.

## 2. Exact files changed

- `app.py`
- `pages/dashboard.py`
- `docs/DASHBOARD_AFS_GIS_EXECUTIVE_SUMMARY_V1_VALIDATION.md`

## 3. Dashboard filter behavior

The Dashboard provides a horizontal `Report View` control with:

- All Reports
- AFS
- GIS

The default is All Reports.

The selected view filters:

- summary-card calculations;
- Reports by Type;
- Review Outcomes by Report Type;
- Top Validation Issues; and
- Recent Document Queue rows.

The filter operates on in-memory query results and does not update document metadata or any database row.

## 4. All Reports cards

All Reports displays:

| Card | Calculation | Current seeded value |
|---|---|---:|
| Total Reports | Count of filtered stored documents | 4 |
| AFS Reports | Documents with stored Report Type `AFS` | 3 |
| GIS Reports | Documents with stored Report Type `GIS` | 1 |
| Needs Review | Explicit Needs Review recommendations plus documents without a saved final recommendation | 2 |
| Accepted | Stored final recommendation `Accept` | 1 |
| Reverted | Stored final recommendation `Revert` | 1 |

Extracted Figures is not shown as a primary All Reports metric.

## 5. AFS cards

AFS displays:

| Card | Calculation | Current seeded value |
|---|---|---:|
| AFS Reports | Filtered AFS documents | 3 |
| Needs Review | Explicit Needs Review or pending AFS documents | 1 |
| Accepted | Stored AFS recommendation `Accept` | 1 |
| Reverted | Stored AFS recommendation `Revert` | 1 |
| Extracted Figures | Stored figure rows joined to AFS documents | 33 |
| Corrected Figures / Entries | AFS figure rows with `reviewer_edited = 1` | 0 |

The Dashboard’s 33 figures are an aggregate across all three AFS records. Figures Extraction Review remains intentionally per-document.

## 6. GIS cards

GIS displays:

| Card | Calculation | Current seeded value |
|---|---|---:|
| GIS Reports | Filtered GIS documents | 1 |
| Needs Review | Explicit Needs Review or pending GIS documents | 1 |
| Accepted | Stored GIS recommendation `Accept` | 0 |
| Reverted | Stored GIS recommendation `Revert` | 0 |
| Completeness Issues | GIS completeness validation rows with Warning, Failed, or Needs Review status | 0 |
| Quality / Orientation Issues | GIS quality/orientation validation rows with Warning, Failed, or Needs Review status | 0 |

The current GIS demo has Passed validations, so issue counts correctly remain zero.

## 7. Recent Document Queue behavior

The queue remains informational and includes:

- ID
- Company Name
- SEC Registration No.
- Report Type
- Period
- Submission Type
- Recommendation
- Source
- Uploaded At

Filter behavior:

- All Reports shows AFS and GIS rows;
- AFS shows AFS rows only;
- GIS shows GIS rows only.

Documents without a saved reviewer action display `No Final Recommendation / Pending`.

No document selector or Open in Review button appears on the Dashboard.

## 8. Reports by Type chart

Reports by Type counts stored documents by stored Report Type.

- All Reports compares AFS and GIS.
- AFS shows the AFS subset.
- GIS shows the GIS subset.

The chart does not infer report type from filenames, validation results, or page text.

## 9. Review Outcomes chart

Review Outcomes by Report Type uses only saved reviewer recommendations and the absence of a saved recommendation.

Categories:

- Needs Review
- Accepted
- Reverted
- No Final Recommendation / Pending

Mapping:

- `Accept` → Accepted
- `Revert` → Reverted
- `Needs Review` → Needs Review
- no recognized saved final recommendation → No Final Recommendation / Pending

Validation warnings are not converted into Accept or Revert outcomes.

## 10. Validation Issues chart

Top Validation Issues aggregates existing rows from the `validations` table.

Only these stored statuses are included:

- Warning
- Failed
- Needs Review

Results are grouped by existing `rule_name` and status. Passed validations are excluded.

For the current GIS-only view, the chart presents a clear empty state because all stored GIS validation results are Passed.

No new validation rule or validation interpretation was added.

## 11. Old Dashboard controls/charts removed

Removed:

- `Open a document for review`
- Dashboard document selector
- Open in Review button
- `dashboard_doc_pick` session widget state
- Dashboard-created `_nav_to` navigation state
- old Validation Summary chart
- default Extraction Volume by Field chart

Specific review remains available through:

- AFS Reports → Document Review
- GIS Reports → Document Review

AFS Figures Extraction Review remains available through the AFS Reports section.

## 12. Confirmation no metrics were fabricated

All values are derived from existing stored records:

- report counts from `documents`;
- recommendations from `reviewer_actions`;
- validation issues from `validations`;
- figure counts and correction flags from `extracted_figures`; and
- demo/upload source labels from configured protected demo filenames.

No value is inferred from unsupported timing, reviewer, productivity, trend, or financial data.

The Needs Review card explicitly includes pending documents because they require an operational review action. The outcome chart preserves pending as a separate category so the distinction remains visible.

## 13. Test results A–O

| Scenario | Expected | Actual | Pass/Fail |
|---|---|---|---|
| A. All Reports view | AFS + GIS totals and records shown | Six All Reports cards, combined queue, and combined charts rendered | Pass |
| B. AFS view | AFS-only counts, queue, and metrics | 3 AFS, 1 needs review, 1 accepted, 1 reverted, 33 figures, 0 corrected | Pass |
| C. GIS view | GIS-only counts, queue, and metrics | 1 GIS, 1 needs review, no final decisions, and zero stored GIS issues | Pass |
| D. Total Reports | Equals stored document count | Dashboard 4 matched database count 4 | Pass |
| E. AFS + GIS count | Equals Total Reports | 3 + 1 = 4 | Pass |
| F. Recent queue filter | Matches selected Report View | All, AFS-only, and GIS-only rows rendered correctly | Pass |
| G. Review outcome chart | Uses stored recommendations only | Accept 1, Revert 1, Pending 2; no validation-based disposition inference | Pass |
| H. Validation issue chart | Uses existing validations only | Stored Warning/Failed/Needs Review rows aggregated; GIS empty state shown | Pass |
| I. Dashboard document selector | Removed | No selector, opener label, or Open in Review button rendered | Pass |
| J. AFS Document Review | Unchanged | Existing AFS-only review page remained operational | Pass |
| K. GIS Document Review | Unchanged | Protected Stock GIS review, completeness, BOD, and notarization remained operational | Pass |
| L. AFS Figures Extraction Review | Unchanged | AFS-only document selector and per-document figures remained operational | Pass |
| M. Historical / Rankings | Unchanged | Existing AFS historical and ranking views remained operational | Pass |
| N. Existing 3 AFS + 1 GIS demo | Intact and protected | Four seeded demo records remained present and protected | Pass |
| O. App startup | No blocking errors | Workflow restarted and all tested transitions completed | Pass |

## 14. Database/schema impact

No database schema change was made.

No database record was inserted, updated, or deleted by this enhancement.

## 15. Demo-data impact

No demo-data file was changed.

The existing protected records remain:

- three AFS demos; and
- one GIS demo.

## 16. Known limitations

Not implemented in this iteration:

- reviewer productivity analytics;
- date-range filtering;
- reviewer/personnel filtering;
- average processing or turnaround time;
- backlog aging;
- daily or monthly trends;
- GIS financial analytics; and
- historical GIS analytics.

Existing non-blocking Streamlit/Vega warnings for empty or discrete chart extents remain outside this focused scope.

## Final assessment

**Safe for prototype testing**

The Dashboard now summarizes the stored AFS/GIS system without becoming dependent on a selected document and without changing validation, review, extraction, historical, ranking, or persistence behavior.