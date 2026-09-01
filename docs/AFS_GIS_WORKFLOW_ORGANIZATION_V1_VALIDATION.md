# AFS / GIS Workflow Organization V1 — Validation

## 1. Scope

This update visibly organizes SEC eFAST Checkers into separate AFS and GIS reviewer workstreams while preserving the existing shared Streamlit framework.

Implemented scope:

- grouped sidebar navigation;
- session-based AFS/GIS context;
- shared context-aware Upload / Intake routing;
- shared context-filtered Document Review routing;
- AFS-only figure-review isolation;
- one protected fictional Stock GIS demo;
- unambiguous AFS/GIS demo labels;
- display-only source-snippet cleanup; and
- the Demo Data & Configuration rename.

No validation engine, OCR, confidence/HITL, BOD rule, reviewer-disposition rule, financial aggregation rule, dependency, or database-schema change was made.

## 2. Exact files changed

- `app.py`
- `demo_data.json`
- `pages/dashboard.py`
- `pages/document_review.py`
- `pages/figures_review.py`
- `pages/settings_demo_data.py`
- `pages/upload_intake.py`
- `storage.py`
- `ui_helpers.py`
- `docs/AFS_GIS_WORKFLOW_ORGANIZATION_V1_VALIDATION.md`

## 3. Final sidebar/navigation hierarchy

```text
SEC eFAST Checkers
GIS & AFS Reviewer Assistance Prototype

MAIN
  Dashboard

AFS REPORTS
  Upload / Intake
  Document Review
  Figures Extraction Review
  Historical Company View

GIS REPORTS
  Upload / Intake
  Document Review

RESEARCH
  Rankings / Research View

PROTOTYPE ADMIN
  Demo Data & Configuration
```

Native Streamlit sidebar buttons are used. The active route is visually indicated without creating duplicate page implementations.

The Demo Documents section is grouped by report type:

- AFS
  - Audentia Fortuna Holdings, Inc. — 2025
  - Malaya Northstar Manufacturing Corp. — 2025
  - Haraya Logistics and Trade, Inc. — 2025
- GIS
  - Audentia Fortuna Holdings, Inc. — 2025 Stock GIS

All four demo records are protected from Test Upload Management deletion.

## 4. Shared AFS/GIS intake routing

Both navigation entries render the existing `pages/upload_intake.py` page.

The sidebar route stores `review_context` in Streamlit session state:

- AFS navigation sets `review_context = "AFS"`;
- GIS navigation sets `review_context = "GIS"`.

When entering the shared intake page, that context sets the Report Type widget:

- AFS route preselects AFS and displays AFS fields;
- GIS route preselects GIS and displays GIS fields.

The reviewer may still switch Report Type inside the shared intake form. Navigation context does not modify any stored document metadata.

The existing Load Demo Document action is also context-aware:

- AFS loads the first configured AFS demo;
- GIS loads the configured GIS demo.

## 5. Shared AFS/GIS Document Review routing

Both navigation entries render the existing `pages/document_review.py` page.

The page reads `review_context` and filters the document list:

- AFS Document Review shows AFS records only;
- GIS Document Review shows GIS records only.

If the active document belongs to the other report type, the page clears that session selection and presents the correct context-filtered selector. The underlying review engine, completeness rendering, page review, BOD routing, and reviewer disposition remain shared.

Dashboard Open in Review infers context from the selected document’s stored Report Type.

## 6. GIS seeded demo metadata

| Field | Value |
|---|---|
| Company | Audentia Fortuna Holdings, Inc. |
| SEC Registration Number | CS202102938 |
| Report Type | GIS |
| Corporation Type | Stock |
| Period Year | 2025 |
| Submission Type | Annual Meeting |
| Actual Meeting / Period Covered | 2025-04-22 |
| Filename | `audentia_fortuna_gis_2025_stock_demo.pdf` |

The record uses synthetic text only and reuses Audentia’s fictional SEC Registration Number to demonstrate cross-report company consistency.

No real GIS PDF or real company data was added.

## 7. GIS seeded demo page/component structure

| Page | Stored page type | Evidence |
|---|---|---|
| 1 | Corporate / Profile / Meeting Information | GIS heading, 2025, company, SEC number, by-laws date, actual annual meeting date, address, contact |
| 2 | AMLA Information | AMLA and beneficial-ownership information |
| 3 | Capital Structure | Authorized, subscribed, and paid-up capital terms |
| 4 | Directors / Officers | Directors and officers terms |
| 5 | Stockholders' Information | One stockholders information page |
| 6 | Investments / Other Corporate Information | Investments, treasury shares, retained earnings, dividends, licenses, manpower |
| 7 | Corporate Secretary Attestation / Notarization | Corporate Secretary, attestation, subscribed and sworn, notary, document/page/book/series references |
| 8 | Beneficial Ownership Declaration | Explicit BOD heading |

Annex A is intentionally absent.

## 8. GIS completeness results

The existing `evaluate_gis_completeness()` logic returns `Passed`.

Required Stock components:

- Corporate / Profile / Meeting Information — Detected
- AMLA Information — Detected
- Capital Structure — Detected
- Directors / Officers — Detected
- Stockholders' Information — Detected
- Investments / Other Corporate Information — Detected
- Corporate Secretary / Notarization — Detected

## 9. Annex A behavior

Annex A / Primary Purpose is:

- `Optional`;
- `Not Present`; and
- excluded from GIS completeness PASS/FAIL.

Its absence does not fail the seeded GIS demo.

## 10. BOD behavior

Beneficial Ownership Declaration is:

- `Conditional / Legacy`;
- detected on Page 8;
- excluded from GIS completeness PASS/FAIL; and
- available in the existing reviewer-controlled BOD routing selector.

No BOD routing choice is automatically saved and no external routing occurs.

## 11. Corporate Secretary/notarization behavior

The existing validation reports:

- Corporate Secretary text — Detected;
- notarization text — Detected; and
- validation status — Passed.

The existing warning remains intact: visual signature and notarial-stamp appearance still require reviewer confirmation. No signature, seal, stamp, or legal authentication is claimed.

## 12. GIS isolation from AFS Figures

The GIS seed contains an empty `figures` collection.

Storage includes an explicit report-type guard so comparative financial backfill runs only for AFS demo documents.

AFS Figures Extraction Review filters its document list to stored `report_type = "AFS"`.

Database verification confirmed:

- GIS extracted figure rows: `0`;
- GIS records do not appear in the AFS figure selector; and
- existing AFS normalized buckets remain unchanged.

## 13. GIS isolation from Historical View and Rankings

Historical Company View and Rankings / Research View continue reading the existing AFS financial projection arrays:

- `historical_data`
- `ranking_data`

The GIS demo does not add or modify any entry in either array and no GIS analytics were introduced.

## 14. Source-snippet root cause and display fix

### Root cause

The extraction engine stores a fixed character window around a detected figure. A character-based window can begin or end in the middle of a word.

### Display fix

The stored source and extraction decision remain unchanged.

AFS Figures Extraction Review now builds the displayed evidence from the stored page text when the raw label can be located, then:

- normalizes surrounding whitespace;
- limits the display to approximately 140 characters;
- moves crop boundaries to complete-word boundaries;
- adds `…` when the beginning or end is cropped; and
- falls back safely to the stored source snippet.

No source text is fabricated.

## 15. Demo Data & Configuration rename

The navigation label and page title were renamed from:

`Settings / Editable Demo Data`

to:

`Demo Data & Configuration`

The page remains reference-only and retains its No Live Editing notice. Its summary now reports four seeded documents: three AFS and one GIS.

## 16. Test results A–P

| Scenario | Expected | Actual | Pass/Fail |
|---|---|---|---|
| A. Sidebar grouping | Five organized sections | Main, AFS Reports, GIS Reports, Research, and Prototype Admin rendered distinctly | Pass |
| B. AFS Upload / Intake | Shared page, AFS preselected | Existing shared intake opened with AFS selected | Pass |
| C. GIS Upload / Intake | Shared page, GIS preselected | Same intake opened with GIS selected and GIS fields | Pass |
| D. AFS Document Review | AFS review operational | Shared review displayed only AFS records | Pass |
| E. GIS Document Review | Protected GIS demo reviewable | Shared review opened the seeded Audentia Stock GIS | Pass |
| F. Stock GIS completeness | All required components detected | Existing completeness logic returned Passed | Pass |
| G. Annex A | Optional / Not Present | Displayed as optional and did not fail completeness | Pass |
| H. BOD | Conditional, detected Page 8 | Detected on Page 8; excluded; routing remained reviewer-controlled | Pass |
| I. Secretary / notarization | Text detected; visual confirmation required | Existing validation passed and retained visual-confirmation notice | Pass |
| J. AFS figure isolation | GIS absent from AFS Figures | Selector contained only the three AFS demos; GIS had zero figures | Pass |
| K. Historical / Rankings isolation | No GIS financial analytics | Existing AFS projection views remained unchanged | Pass |
| L. Source snippet | Word boundaries and ellipses | Long-page evidence rendered with normalized whitespace and boundary-safe cropping | Pass |
| M. Existing AFS demos | Three intact and protected | Audentia, Malaya, and Haraya remained protected | Pass |
| N. AFS multi-year figures | Existing 2025/2024 behavior unchanged | Current/Comparative rows and 2023 empty state remained correct | Pass |
| O. Test Upload Management | Temporary uploads deletable; demos protected | Temporary GIS upload was created, listed, deleted, and cleaned up | Pass |
| P. Application startup | No blocking errors | Workflow restarted and all navigation transitions completed | Pass |

## 17. Database/data changes

No schema changes were made.

Seeded data additions:

- one GIS document row;
- eight GIS page-analysis rows;
- nine validation rows generated by the existing GIS validator;
- zero extracted financial figure rows; and
- zero reviewer-action rows.

The GIS seed is idempotent and protected by its configured demo filename.

## 18. Existing AFS demo impact

The existing three AFS demos remain:

- present;
- protected;
- available in AFS Document Review;
- available in AFS Figures Extraction Review; and
- unchanged in their existing 2025/2024 financial behavior.

Existing reviewer actions remain intact.

## 19. Known limitations

1. Navigation context is session-based and does not create separate URLs for AFS and GIS.
2. Dashboard remains a combined operational overview; no AFS/GIS dashboard filters or separate GIS charts were added.
3. Historical Company View and Rankings remain seeded AFS projections.
4. The GIS demo uses synthetic page text, not a generated PDF.
5. Signature, seal, stamp, QR authentication, and legal sufficiency remain outside automated validation.
6. BOD routing remains local reviewer reference only.
7. Existing non-blocking Streamlit/Vega empty-chart scale warnings remain unchanged.

## Final assessment

**Safe for prototype testing**

The prototype now presents distinct AFS and GIS reviewer workstreams while reusing the current shared modules. The protected GIS seed demonstrates the existing Stock GIS completeness, optional Annex A, conditional BOD, and notarization behavior without entering AFS financial data.