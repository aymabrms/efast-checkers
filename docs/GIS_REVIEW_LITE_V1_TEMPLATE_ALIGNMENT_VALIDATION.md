# GIS Review Lite V1 — Template Alignment Validation

## 1. Scope

This patch makes two small, deterministic template-alignment corrections to GIS Review Lite V1:

1. Corporate Secretary Attestation / Notarization is required for both Stock and Non-Stock GIS completeness.
2. Annual Meeting Period Covered detection supports both actual-meeting template labels while excluding the separate By-Laws meeting-date field.

No UI redesign, dependency, OCR engine, NLP, ML, API, BOD feature, QR behavior, Annex A behavior, AFS behavior, figure-extraction behavior, confidence behavior, Historical View behavior, or Rankings behavior was added or changed.

## 2. Exact files changed

- `validation_engine.py`
  - Adds Corporate Secretary / Notarization to both required GIS completeness profiles.
  - Preserves the existing page-pattern evidence for that required component.
  - Supports `ACTUAL DATE OF ANNUAL MEETING` and `DATE OF ACTUAL MEETING`.
  - Excludes `DATE OF ANNUAL MEETING PER BY-LAWS` from normal Annual Meeting date evidence.
- `docs/GIS_REVIEW_LITE_V1_VALIDATION.md`
  - Corrects the earlier description of Corporate Secretary / Notarization from optional to required.
- `docs/GIS_REVIEW_LITE_V1_TEMPLATE_ALIGNMENT_VALIDATION.md`
  - Records this alignment patch and its regression results.

No other source file was changed for this patch.

## 3. Required Corporate Secretary / Notarization rule

Corporate Secretary Attestation / Notarization is now a required GIS completeness component for:

- GIS Stock
- GIS Non-Stock

The component uses existing text evidence, including:

- Corporate Secretary
- Secretary’s attestation
- declare under penalty of perjury
- hereby attest
- SUBSCRIBED AND SWORN
- ACKNOWLEDGMENT
- ACKNOWLEDGEMENT
- NOTARY PUBLIC
- DOC. NO.
- PAGE NO.
- BOOK NO.
- SERIES OF

Behavior:

- Missing component → `Corporate Secretary / Notarization = Missing`
- Missing component → `GIS Completeness = Failed`
- Detected component → `Corporate Secretary / Notarization = Detected`

The component is detected from text evidence only. It does not establish legal sufficiency.

## 4. Machine-detectable evidence versus visual confirmation

The existing separate validation message remains in place:

`Signature / Notarial Stamp: Visual Confirmation Required`

The rule does not claim automated verification of:

- Corporate Secretary signature
- Notary signature
- stamp
- seal
- authenticity
- legal sufficiency

The required completeness rule only confirms that expected attestation/notarization text appears to be present.

## 5. Stock Actual Meeting Date label

For Annual Meeting submissions, GIS Period Covered detection supports:

`ACTUAL DATE OF ANNUAL MEETING`

The detected date is normalized as:

`ACTUAL_MEETING_DATE`

When it matches Intake → Period Covered, the existing Period Covered validation passes. A clear mismatch remains a failure, and missing/unclear evidence remains Needs Review.

## 6. Non-Stock Actual Meeting Date label

For Annual Meeting submissions, GIS Period Covered detection also supports:

`DATE OF ACTUAL MEETING`

This is normalized to the same `ACTUAL_MEETING_DATE` evidence concept and uses the same existing comparison behavior.

## 7. By-Laws date exclusion

The separate template field:

`DATE OF ANNUAL MEETING PER BY-LAWS`

is explicitly excluded from normal Annual Meeting Period Covered detection.

If both a By-Laws date and an Actual Meeting date are present, only the actual meeting date is used for the normal Annual Meeting comparison.

The patch does not change Special Meeting, Amendment, or No Meeting / ANHAM behavior.

## 8. Confirmation BOD behavior remains unchanged

BOD remains:

- Conditional / Legacy
- detected separately
- excluded from GIS completeness PASS/FAIL
- absent without causing GIS completeness failure
- eligible for reviewer-controlled page selection
- eligible for accepted QA copy status when absent from an accepted copy
- without substantive BOD validation
- without actual external forwarding

The BOD phrase:

`This page is not for uploading on the SEC iView`

does not change this behavior.

## 9. Test results A–K

| Scenario | Expected | Actual | Result |
|---|---|---|---|
| A. Stock GIS with complete body including attestation/notarization | Completeness can Pass | Required Stock components, including Corporate Secretary / Notarization, were detected | Pass |
| B. Stock GIS missing attestation/notarization | Component Missing; completeness Failed | Corporate Secretary / Notarization was Missing and completeness Failed | Pass |
| C. Non-Stock GIS with complete body including attestation/notarization | Completeness can Pass | Required Non-Stock components, including Corporate Secretary / Notarization, were detected | Pass |
| D. Non-Stock GIS missing attestation/notarization | Completeness Failed | Corporate Secretary / Notarization was Missing and completeness Failed | Pass |
| E. Attestation/notarial text without machine-verifiable signature/stamp | Component Detected; visual confirmation remains | Component passed from text evidence and visual-confirmation message remained | Pass |
| F. Stock label `ACTUAL DATE OF ANNUAL MEETING` | Actual Meeting Date detected | Period Covered validation passed against the date after the label | Pass |
| G. Non-Stock label `DATE OF ACTUAL MEETING` | Actual Meeting Date detected | Period Covered validation passed against the date after the label | Pass |
| H. By-Laws label alongside Actual Meeting Date | By-Laws date excluded | Only the Actual Meeting date was used; the By-Laws date was absent from the validation evidence | Pass |
| I. BOD page detected | BOD stays outside completeness | BOD was detected while completeness remained Passed | Pass |
| J. Existing GIS Review Lite scenarios | Existing behavior remains operational | Stock/Non-Stock, QR, Annex, OCR, period, company, and routing scenarios remained operational | Pass |
| K. Existing AFS workflows | AFS unchanged | AFS completeness safeguard, figures, Multi-Year, confidence/HITL, OCR traceability, dispositions, and demos remained intact | Pass |

## 10. GIS regression results

The existing GIS regression suite continued to pass:

- Stock required profile
- Non-Stock required profile
- Single stockholders section
- Optional Annex A
- Raw GIS without BOD
- Raw GIS with BOD
- Accepted QA copy with QR cover and no BOD
- Content-based page classification
- Text Layer source display
- OCR Fallback source display
- Period Year match/mismatch
- Annual Meeting match/mismatch
- Special Meeting
- Amendment
- No Meeting / ANHAM
- Company and SEC registration checks
- Reviewer-controlled BOD routing representation
- Signature and stamp visual-confirmation limitation

The only intentional behavior change is that missing Corporate Secretary / Notarization now fails GIS completeness for both corporation types.

## 11. AFS regression results

AFS behavior remains intact:

- AFS intake controls remain available.
- AFS comparative-year controls remain unchanged.
- AFS completeness still excludes Auditor’s Report narrative from satisfying statement components.
- Multi-Year AFS current/comparative controls still render.
- Computed Confidence and HITL explanation still render.
- Existing OCR Text Layer/OCR Fallback source traceability remains.
- Reviewer disposition remains human-controlled.
- Seeded AFS demos, figures, and historical reviewer actions remain unchanged.

## 12. Known limitations

1. Attestation/notarization detection is phrase-based and does not authenticate documents.
2. Signature, notarial signature, stamp, seal, authenticity, and legal sufficiency remain visual/legal review items.
3. `ACTUAL_MEETING_DATE` is inferred from supported text labels and nearby parseable dates only.
4. Arbitrary template paraphrases may route to Needs Review.
5. By-Laws exclusion is based on the explicit supported label; unclear OCR text may still require reviewer inspection.
6. Special Meeting, Amendment, and No Meeting / ANHAM logic remains deterministic and reviewer-assisted.
7. BOD remains conditional/legacy and is not substantively validated or externally routed.

## 13. Final assessment

**Safe for prototype testing**

The two requested template-alignment corrections are implemented with no new dependencies and no changes to BOD, QR, Annex A, AFS, figure extraction, confidence, Historical View, Rankings, OCR, or reviewer-disposition behavior.