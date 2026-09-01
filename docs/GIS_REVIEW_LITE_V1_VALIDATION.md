# GIS Review Lite V1 — Validation

## 1. Scope

GIS Review Lite V1 adds a small, rule-based reviewer-assistance path for General Information Sheet PDF filings inside the existing SEC eFAST Checkers workflow:

`Upload / Intake → Document Review → Reviewer Disposition`

The implementation reuses:

- existing PDF Text Layer extraction;
- existing Tesseract OCR Fallback;
- existing page geometry, orientation, rotation, and readability signals;
- existing deterministic company-name matching;
- existing validation storage;
- existing reviewer recommendation and remarks workflow; and
- existing Test Upload Management.

No trained AI/ML system, spaCy, LLM, external API, heavy dependency, background worker, Excel parser, or separate GIS application was added.

## 2. Exact files changed

- `validation_engine.py` — adds the isolated GIS classifier, evidence rules, completeness profiles, period/company checks, QR/Annex/BOD handling, and notarization-text review.
- `db.py` — adds the minimum GIS metadata and BOD routing fields plus routing-selection persistence.
- `pages/upload_intake.py` — adds the AFS/GIS report selector, conditional GIS fields, GIS analysis branch, and GIS-specific completion message.
- `pages/document_review.py` — adds GIS validation/completeness rendering and the reviewer-controlled BOD routing selector.
- `ui_helpers.py` — conditionally displays GIS metadata in the existing Currently Reviewing banner.
- `docs/GIS_REVIEW_LITE_V1_VALIDATION.md` — records the implementation and validation results.

No AFS demo-data, label-mapping, confidence, OCR, ranking, historical-view, or figure-review source file was changed.

## 3. GIS intake fields

Upload / Intake now provides a Report Type selector:

- AFS
- GIS

When AFS is selected, the existing fields remain:

- Company Name
- SEC Registration Number
- Period Covered Year
- Comparative Figures Included
- comparative-year controls where selected
- Submission Type
- Filing Year

When GIS is selected, the form displays:

- Company Name
- SEC Registration Number
- Report Type: GIS
- Corporation Type: Stock / Non-Stock
- Period Year
- Period Covered
- Submission Type:
  - Annual Meeting
  - Special Meeting
  - Amendment / Amended GIS
  - No Meeting / Non-Holding of Annual Meeting

AFS comparative-year controls are not displayed for GIS.

GIS uploads do not enter the AFS financial-figure extraction path and therefore do not receive a misleading missing-financial-figures warning.

## 4. Stock completeness profile

GIS Stock completeness requires content evidence for these component groups:

1. Corporate / Profile / Meeting Information
2. AMLA Information
3. Capital Structure
4. Directors / Officers
5. Stockholders' Information
6. Investments / Other Corporate Information

Corporate Secretary / Notarization is displayed as an optional/informational component and also receives a separate text-evidence validation.

Stockholders' information is content-based. At least one valid stockholders section is sufficient. Pages 5, 6, and 7 are not hard-coded or individually required.

Annex A and Beneficial Ownership Declaration are excluded from completeness PASS/FAIL.

## 5. Non-Stock completeness profile

GIS Non-Stock completeness requires:

1. Corporate / Profile / Meeting Information
2. AMLA Information
3. Directors / Officers
4. Investments / Other Corporate Information, including affiliation, fund-balance, secondary-license, or manpower evidence where present

Non-Stock does not require:

- Capital Structure
- Stockholders' Information

Corporate Secretary / Notarization, Annex A, and BOD remain optional or conditional items and do not alter the required-profile calculation.

## 6. Period Year logic

The GIS rule engine looks for clear GIS heading evidence such as:

`FOR THE YEAR 2026`

The detected heading year is compared with Intake → Period Year.

- matching year → Passed
- clearly different detected year → Failed
- no clear heading year → Needs Review

The logic does not replace Multi-Year AFS behavior and is only active for Report Type GIS.

## 7. Period Covered / Submission Type logic

### Annual Meeting

The rule engine looks for an explicit label such as:

`ACTUAL DATE OF ANNUAL MEETING`

The detected date is compared with Intake → Period Covered.

- equal date → Passed
- clearly different date → Failed
- unavailable or unclear date → Needs Review

### Special Meeting

Special Meeting submissions use explicit special-meeting labels and compare the detected special-meeting date with Intake → Period Covered.

Annual Meeting rules are not applied blindly when Special Meeting evidence is present.

### Amendment / Amended GIS

Amendment wording is detected deterministically. When a meeting date is available, it is compared with Intake → Period Covered. When the date is unavailable, the result is Needs Review.

### No Meeting / ANHAM

Evidence such as:

- No Meeting
- No Meeting Held
- Non-Holding of Annual Meeting
- ANHAM

routes the period/submission check to Needs Review. Absence of an annual-meeting date does not automatically fail this case.

## 8. Company-profile logic

GIS pages are checked against the Intake metadata for:

- Company Name
- SEC Registration Number

The existing deterministic/fuzzy company-name matcher is reused.

SEC registration comparison normalizes case, punctuation, spaces, and hyphens before comparison. For example, `GIS-123` and `GIS 123` provide matching evidence.

Results:

- Passed for matching evidence;
- Needs Review when usable evidence is insufficient; and
- Failed when substantial text is present but does not match Intake metadata.

QR/acceptance-cover text is excluded from company-profile evidence.

## 9. QR/accepted-cover handling

Likely SEC acceptance or QR covers are detected only from available text evidence, such as:

- SEC acceptance/accepted/received wording;
- acceptance page, notice, or reference wording;
- accepted filing/report/GIS wording; or
- QR Code text together with SEC wording.

Detected pages are classified:

`SEC Acceptance / QR Cover`

These pages:

- are excluded from GIS completeness;
- cannot satisfy Corporate / Profile / Meeting Information;
- do not shift or break component detection;
- may appear in any position, although accepted copies commonly place them first.

No visual QR-code detection or QR authentication is claimed.

## 10. Annex A handling

A page with explicit Annex A plus Primary Purpose or purpose-continuation evidence is classified:

`Annex A / Primary Purpose`

Annex A is displayed as optional:

- Detected when present
- Not Present when absent

Its absence never fails GIS completeness.

## 11. Beneficial Ownership Declaration logic

BOD detection requires strong explicit evidence:

- Beneficial Ownership Declaration
- Declaration of Beneficial Ownership
- Beneficial Owner(s) together with Declaration wording

An incidental phrase such as “beneficial owner” alone does not classify an ordinary page as BOD.

The reviewer-facing item is:

`Beneficial Ownership Declaration (Conditional / Legacy)`

Possible statuses:

- Detected
- Not Detected
- Not Applicable / Accepted QA Copy

Detected page numbers are shown.

BOD is always excluded from normal GIS completeness PASS/FAIL. Its absence alone never makes GIS completeness fail.

## 12. BOD routing-page behavior

Document Review includes:

`BOD Page for Routing`

Options include:

- None / Not Applicable
- Page 1 through Page N

When an explicit BOD page is detected and no prior selection exists, the first detected BOD page is preselected. The reviewer can change or clear it.

The selection is stored for reviewer reference only.

No external forwarding, transmission, workflow integration, or substantive BOD validation occurs.

## 13. Raw GIS vs Accepted/QA GIS behavior

### Raw GIS

Raw GIS completeness is based on detected body components. A legacy BOD page may be detected and selected for routing, but remains excluded from completeness.

### Accepted / QA GIS

A likely SEC Acceptance / QR Cover is excluded from completeness. If no BOD remains in the accepted copy, the BOD status becomes:

`Not Applicable / Accepted QA Copy`

The required GIS body components still determine completeness. A QR cover alone cannot make an incomplete GIS pass.

## 14. Corporate Secretary / notarization behavior

The rule engine detects text evidence for:

- Corporate Secretary
- Secretary's attestation
- SUBSCRIBED AND SWORN
- ACKNOWLEDGMENT / ACKNOWLEDGEMENT
- NOTARY PUBLIC
- DOC. NO.
- PAGE NO.
- BOOK NO.
- SERIES OF

The reviewer message separately reports:

- Corporate Secretary text: Detected / Not Detected
- Notarization text: Detected / Not Detected

It explicitly states that signature or notarial-stamp appearance requires visual confirmation.

The prototype does not authenticate:

- handwritten signatures;
- notarial signatures;
- stamps;
- seals; or
- legal validity of notarization.

## 15. Text Layer vs OCR behavior

GIS uses the existing shared PDF extraction behavior:

1. PDF Text Layer first
2. Existing Tesseract OCR Fallback only for low-text pages
3. OCR adopted only when it improves usable content

No GIS-specific OCR engine or rule set was introduced.

The existing fields remain preserved:

- `original_text`
- `ocr_text`
- `extraction_source`

Document Review continues to show:

- Text Source: Text Layer
- Text Source: OCR Fallback

An actual image-only GIS fixture was processed through Tesseract and classified as Corporate / Profile / Meeting Information using the recovered effective text.

## 16. Test results A–N

| Scenario | Expected | Actual | Pass/Fail |
|---|---|---|---|
| A. GIS Stock regular Annual Meeting | Core Stock components detected; period rules run | Required Stock groups detected; Period Year and Annual Meeting Period Covered passed | Pass |
| B. GIS Non-Stock | Capital Structure and Stockholders not required | Non-Stock passed without either component in the requirements table | Pass |
| C. Stock GIS with one Stockholders page | Stockholders completeness satisfied | One Stockholders' Information page satisfied the group | Pass |
| D. GIS with optional Annex A | Annex detected; absence would not fail | Annex A detected and labeled optional; no required calculation includes it | Pass |
| E. Legacy/raw GIS containing BOD | BOD detected with page; excluded; reviewer routing control | BOD detected on Page 9, excluded from completeness, preselected in routing control, and saved by reviewer | Pass |
| F. GIS without BOD | Absence does not fail completeness | Raw Stock GIS remained Passed; BOD displayed Not Detected | Pass |
| G. Accepted GIS with QR cover and no BOD | QR excluded; BOD not applicable; body determines completeness | QR page classified/excluded; BOD became Not Applicable / Accepted QA Copy; required body still passed | Pass |
| H. Text-layer GIS converted from Excel | Normal text extraction used | Browser fixture pages displayed Text Source: Text Layer and content-based GIS page types | Pass |
| I. Scanned notarized GIS | Existing OCR fallback used where needed | Image-only GIS test used OCR Fallback and recovered company/year/profile evidence | Pass |
| J. Period Year mismatch | Failed/reviewer finding | Detected 2026 versus Intake 2025 produced Failed | Pass |
| K. Annual Meeting Period Covered mismatch | Failed/reviewer finding | Detected 2026-05-15 versus Intake 2026-05-16 produced Failed | Pass |
| L. No Meeting / ANHAM wording | Needs Review, not automatic failure | No Meeting Held / ANHAM routed to Needs Review | Pass |
| M. Corporate Secretary/notarial text | Text detected; signature/stamp visual | Both text categories detected; message retained visual-confirmation limitation | Pass |
| N. Existing AFS workflows | Unchanged and operational | AFS controls, completeness, multi-year figures, confidence explanation, HITL controls, OCR source, and protected demos rendered successfully | Pass |

Additional deterministic checks passed for:

- Special Meeting date matching;
- Amendment / Amended GIS date matching;
- SEC Registration Number punctuation variation;
- incidental `beneficial owner` text not becoming BOD;
- QR page position not controlling body-component detection; and
- AFS Auditor's Report references remaining excluded from AFS component presence.

## 17. Existing AFS regression results

Verified after GIS implementation:

- AFS intake fields and comparative-year controls remain available.
- AFS Completeness Check remains on the AFS branch.
- The Auditor's Report false-positive safeguard remains correct.
- Multi-Year AFS shows 2025 Current and 2024/2023 Comparative controls.
- Computed Confidence and confidence explanation still render.
- Reviewer corrections/status and human-controlled disposition remain available.
- Simple OCR Fallback remains operational.
- AFS Figures Extraction Review remains operational.
- GIS uploads do not enter AFS figure extraction.
- Test Upload Management deletes both AFS and GIS temporary uploads.

## 18. Database/schema changes

A backward-compatible migration adds three nullable GIS fields to `documents`:

- `corporation_type TEXT`
- `period_covered TEXT`
- `gis_bod_routing_page INTEGER`

No existing table or column was removed.

Existing AFS rows receive NULL for these GIS-only fields and continue using the same AFS metadata.

The BOD routing-page field stores reviewer selection only; it does not trigger external routing.

## 19. Demo-data impact

No demo JSON or seeded AFS content was modified.

The three seeded AFS documents remain intact:

1. Audentia Fortuna Holdings, Inc.
2. Malaya Northstar Manufacturing Corp.
3. Haraya Logistics and Trade, Inc.

The existing 19 seeded figures and Malaya Accept / Haraya Revert actions remain unchanged.

Temporary GIS uploads created during browser testing were deleted through Test Upload Management.

## 20. Known limitations

1. GIS evidence is phrase/regex based and does not understand arbitrary semantic paraphrases.
2. PDF text is limited to the existing stored preview length per page.
3. There is no full officer-name, stockholder, share-count, AMLA field-value, investment-amount, or BOD substantive validation.
4. There is no Excel/XLSX parsing; converted PDFs are supported through their PDF text layer.
5. OCR quality remains dependent on scan quality and the existing Tesseract safeguards.
6. Image-content rotation absent from PDF metadata is not automatically detected.
7. QR detection is text-based only and does not inspect or authenticate QR symbols.
8. Signature, notarial signature, stamp, and seal authentication do not exist.
9. Optional/conditional component status does not establish legal sufficiency.
10. BOD routing is a stored reviewer selection only and performs no transmission.
11. Page classification assigns one primary GIS type per page; multi-section pages may still require reviewer inspection.
12. Company/registration mismatches are deterministic text findings, not authoritative master-data adjudication.

## 21. Explicit confirmations

- BOD is conditional/legacy.
- BOD absence does not fail GIS completeness.
- Accepted GIS may legitimately contain a QR cover but no BOD.
- No signature or stamp authentication exists.
- No QR authentication exists.
- No BOD substantive-value validation exists.
- No external BOD routing exists.
- No trained NLP or ML was added.
- No spaCy dependency was added.
- No LLM or external API was added.
- Final reviewer disposition remains human-controlled.

## 22. Final assessment

**Safe for prototype testing.**

GIS Review Lite V1 is content-based, deterministic, reviewer-facing, and isolated from existing AFS validation and figure extraction. The required stock/non-stock rules, QR/Annex/BOD safeguards, period checks, OCR compatibility, reviewer routing representation, and AFS regressions all passed.