
# Computed Confidence + HITL V1 — Validation

## 1. Scope

Computed Confidence + HITL V1 replaces the fixed/unexplained extracted-figure confidence presentation with one deterministic, rule-based calculator using evidence already present in the SEC eFAST Checkers prototype.

The enhancement adds:

- a 0–100 computed confidence score;
- High, Medium, and Low classifications;
- initial Human-in-the-Loop review routing;
- safety caps for unsafe numeric values and very poor source pages;
- a compact confidence explanation panel;
- a reliable selected-row correction panel; and
- year-aware confidence/export fields.

It does not add OCR, OCR confidence, NLP, ML, external APIs, or dependencies. It does not automatically Accept or Revert a filing.

## 2. Exact files changed

- `confidence.py` — shared deterministic confidence calculator, factor weights, thresholds, safety caps, and initial HITL routing.
- `extraction_engine.py` — calls the shared calculator for each newly extracted fiscal-year row instead of assigning fixed `0.82` confidence.
- `pages/figures_review.py` — recomputes reviewer-facing confidence from current evidence, displays classification/routing, provides explanations and selected-row review controls, and extends CSV export.
- `docs/COMPUTED_CONFIDENCE_HITL_V1_VALIDATION.md` — implementation and A–J validation record.

No GIS, Historical View, Rankings, AFS completeness, demo seeding, final disposition, or Test Upload Management code was changed.

## 3. Exact confidence formula and weights

The raw score is the sum of six independent factors:

| Factor | Maximum |
|---|---:|
| Source Page Quality | 20 |
| Financial Label Match | 25 |
| Fiscal Year Association | 20 |
| Numeric Parse Quality | 20 |
| Unit Basis Certainty | 10 |
| Source Evidence / Snippet | 5 |
| **Total** | **100** |

Safety caps are applied after summing the factors:

`final score = min(raw score, all applicable safety caps)`

The final score is clamped to the range 0–100.

## 4. Exact evidence used for each factor

### A. Source Page Quality — 20 points

Uses the existing `page_analysis.image_quality_flag`, `page_analysis.text_length`, and source-page text.

- 20: `Passed` and at least 140 extracted-text characters
- 12: `Warning`, or at least 25 usable extracted-text characters
- 5: failed/very low extracted text
- 0: no usable source-page evidence

### B. Financial Label Match — 25 points

Uses the existing extractor-supported labels and `label_mapping.json`.

- 25: exact label supported by the current extraction rules
- 20: exact configured alias
- 12: weaker deterministic alias containment/normalized variation
- 0: unsupported or insufficient label evidence

No fuzzy ML similarity is used.

### C. Fiscal Year Association — 20 points

Calculated independently for every figure row.

- 20: the row's fiscal year is explicitly followed by a value token in its source snippet
- 12: the fiscal year is present in the snippet but not directly associated
- 5: the row has a fiscal year but no reliable snippet association
- 0: no fiscal-year evidence

### D. Numeric Parse Quality — 20 points

Uses the existing safe numeric validator and parser.

- 20: displayed value is already safely formatted and has a normalized value
- 15: value becomes safely parseable only after ordinary trailing punctuation cleanup
- 0: suspicious, ambiguous, missing, or unsafe numeric formatting

Values such as `6.837.912.90` and `A8849,399.68` remain uncorrected and retain NULL normalized values.

### E. Unit Basis Certainty — 10 points

Uses the stored unit basis plus current page/snippet text.

- 10: explicit context such as `Amounts in Philippine pesos`, `in thousands`, or `in millions`
- 3: a non-empty default/inferred unit basis without explicit current text evidence
- 0: no unit basis

The suggested 7-point “reliably inherited” level is intentionally not assigned because the current prototype does not retain separate provenance proving that distinction. This avoids fabricating a signal.

### F. Source Evidence / Snippet — 5 points

- 5: snippet contains the row's raw label, fiscal year, and displayed value
- 2: partial non-empty snippet
- 0: no useful snippet

## 5. Safety caps

### Suspicious or unsafe numeric formatting

- Maximum confidence: 49
- Applies when Numeric Parse is 0/20
- Also applies when the value cannot be safely normalized
- Initial routing remains `Check Source`
- Raw values are not repaired automatically

### Failed or very poor source-page readability

- Maximum confidence: 69
- Applies when Source Page Quality is 5/20
- Routes to `Check Source` under the Low threshold

When both caps apply, the lower cap controls.

No confidence rule creates a missing figure or missing fiscal-year value.

## 6. High / Medium / Low thresholds

| Score | Classification |
|---:|---|
| 90–100 | High |
| 75–89 | Medium |
| 0–74 | Low |

Reviewer-facing examples use:

- `100% · High`
- `84% · Medium`
- `49% · Low`

## 7. HITL routing rules

Initial review routing is:

| Classification | Initial review status |
|---|---|
| High | Ready for Quick Validation |
| Medium | Needs Review |
| Low | Check Source |

Unsafe numeric formatting always routes to `Check Source`.

These are prioritization statuses only:

- every row remains human-reviewable;
- High does not Accept a filing;
- Low does not Revert a filing;
- confidence does not change validation results; and
- final reviewer disposition remains controlled by the existing document-review workflow.

## 8. Explainability UI behavior

AFS Figures Extraction Review now uses `Computed Confidence` terminology and displays score plus classification in the main table.

The page states:

`Computed confidence uses deterministic prototype rules — it is not an ML probability.`

The `Explain Computed Confidence` expander lets the reviewer select one visible figure row and shows:

- computed score and classification;
- initial HITL routing;
- source page;
- unit basis;
- displayed value;
- all six factor scores and denominators;
- applicable safety-cap text; and
- the stored source snippet.

Source detail was kept out of the compact main grid to avoid making reviewer controls unnecessarily wide.

## 9. Multi-year behavior

Confidence is calculated from each row's own:

- fiscal year;
- displayed value;
- normalized value;
- source snippet; and
- source page.

The same normalized label for 2025, 2024, and 2023 receives three independent calculations. No confidence result is copied between fiscal years.

The existing Reporting Years display, Current/Comparative roles, fiscal-year filter, year-specific buckets, and current-year revenue behavior remain intact.

## 10. Reviewer correction behavior

The main review table keeps Computed Confidence, Review Status, and Reviewed / Corrected Value close together.

The `Review / Correct Selected Figure` expander provides a reliable selected-row editor with:

- figure selector;
- Review Status;
- Reviewed / Corrected Value; and
- `Save Selected Figure Review`.

It uses the existing `update_figure_reviews()` persistence path.

When a row has already been edited or has a reviewer-finalized row status (`Reviewed`, `Corrected`, or `Rejected`):

- its reviewed value is not overwritten by confidence recomputation;
- its reviewer status is preserved; and
- computed evidence remains visible alongside the human decision.

## 11. Export behavior

The existing row-oriented CSV export now includes:

- `fiscal_year`
- `year_role`
- `computed_confidence_score`
- `confidence_classification`
- `review_status`
- `reviewed_value`

It also retains the existing figure/source fields.

The browser test downloaded and inspected `sec_efast_figures_document_12.csv`. The expected headers were present, and the corrected Total Assets row contained:

- `review_status`: `Corrected`
- `reviewed_value`: `1,250,000,000`

## 12. Test results A–J

| Scenario | Expected | Actual | Pass/Fail |
|---|---|---|---|
| A. Clean figure | High confidence | Readable page + exact Total Assets label + explicit 2025 + safe number + explicit pesos context scored 100% High and routed to Ready for Quick Validation | Pass |
| B. Valid figure with inferred unit | Lower than otherwise identical explicit-unit figure | Explicit unit scored 100; default/inferred unit scored 93 with Unit Basis 3/10 | Pass |
| C. Weak label variation | Medium or appropriately reduced | `Assets - restated` received Label Match 12/25 and total 84% Medium | Pass |
| D. `6.837.912.90` | Low / Check Source; normalized value NULL | Raw value was preserved, Numeric Parse was 0/20, score capped at 49% Low, normalized value remained blank, and status was Check Source | Pass |
| E. `A8849,399.68` | Low / Check Source; no repair | Raw value was preserved, Numeric Parse was 0/20, score capped at 49% Low, and no correction was manufactured | Pass |
| F. Low-quality source page | Capped and routed for review | 21-character failed-readability page received Page Quality 5/20, Unit Basis 3/10, final cap 69% Low, and Check Source | Pass |
| G. Same normalized label for 2025/2024/2023 | Independent confidence per row | Three Total Assets rows retained separate fiscal years, each was calculated from its own year/value association, and each displayed its own score/status | Pass |
| H. Reviewer-corrected figure | Human correction remains preserved | Total Assets 2025 was corrected to `1,250,000,000`, marked Corrected, rerun through year filters, and verified persisted with computed evidence still visible | Pass |
| I. Existing three demo documents | Remain intact and usable | Documents 1–3, 19 seeded figure rows, and the existing Malaya Accept / Haraya Revert actions remained intact | Pass |
| J. Final reviewer disposition | No automatic Accept or Revert | Existing `final_recommendation()` behavior remained unchanged; confidence routing did not call or alter final disposition | Pass |

## 13. Demo-data impact

No seeded demo JSON, document, page, figure, validation, reviewer-action, or disposition record was changed.

Legacy seeded `extracted_figures.confidence` values remain in the database for compatibility. AFS Figures Extraction Review supersedes them with the shared calculator when sufficient current page/figure evidence exists.

Newly extracted rows store the computed score divided by 100 in the existing 0–1 `confidence` column, preserving the column's established representation without a migration.

All temporary browser-test uploads and their dependent records/files were removed through Test Upload Management.

## 14. Known limitations

1. The score is a deterministic prototype heuristic, not a statistical probability.
2. OCR is not implemented, so OCR confidence is not available or used.
3. Page quality is limited to current extracted-text length and existing quality flags.
4. The prototype cannot reliably distinguish inherited report-level unit provenance, so non-explicit units receive the conservative default/inferred score of 3/10.
5. Fiscal-year association is based on current source-snippet text, not table-cell geometry.
6. Advanced table-aware multi-column extraction remains out of scope.
7. Legacy confidence remains stored but is not labeled as computed in the UI.
8. Reviewer status and corrected values are row-level human inputs; they do not rewrite the computed evidence.

## 15. Explicit method confirmation

- This confidence is deterministic and rule-based.
- It is not an ML probability.
- It is not an automatic filing decision.
- OCR confidence is not used because OCR is not implemented.
- No external API or new dependency is involved.

## 16. Final assessment

**Safe for prototype testing.**

Computed Confidence + HITL V1 provides explainable row-level prioritization, preserves unsafe-value safeguards and human corrections, remains compatible with Multi-Year AFS Support V1, and leaves final reviewer disposition unchanged.