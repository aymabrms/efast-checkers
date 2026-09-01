# NLP-Assisted Evidence Extraction V1 — Validation

## 1. Scope

P2-B was scoped as a lightweight, deterministic NLP evidence layer for common AFS wording variations from both PDF Text Layer and OCR Fallback text.

Implementation was intentionally stopped before adding runtime NLP behavior because the required spaCy dependency could not be installed cleanly in the current environment.

No partial NLP module, UI change, schema change, validation change, or extraction change was added.

## 2. NLP approach intended

The intended low-risk implementation was:

- spaCy blank English pipeline via `spacy.blank("en")`;
- `PhraseMatcher` for configured AFS statement and financial-label aliases;
- small deterministic token patterns for reporting-period/date evidence;
- token-based company-name evidence normalization only;
- existing deterministic validator, fuzzy company matcher, normalized label mapping, confidence calculator, and HITL decisions remaining authoritative;
- no trained model, pretrained pipeline, LLM, external API, vector database, ML classifier, or background worker.

Because spaCy could not be enabled cleanly, none of this runtime approach was implemented.

## 3. spaCy/environment status

Initial availability check:

`ModuleNotFoundError: No module named 'spacy'`

First supported package-manager attempt:

`installLanguagePackages({ language: "python", packages: ["spacy"] })`

The package manager attempted:

`pip install spacy fitz`

The install failed because the deprecated `fitz` package is deactivated:

`Package 'fitz' has been deactivated and cannot be installed. Please install 'pymupdf' instead.`

The project already declares `pymupdf`, not `fitz`. The installed `fitz` import is provided by PyMuPDF; there is no installed `fitz` distribution and no `fitz` entry in `requirements.txt`.

One clean retry explicitly included the existing PDF dependency:

`installLanguagePackages({ language: "python", packages: ["spacy", "pymupdf"] })`

The package manager still attempted:

`pip install spacy pymupdf fitz`

and failed at the same deactivated `fitz` package.

Final status:

- spaCy unavailable;
- no spaCy model downloaded;
- no pretrained NLP model downloaded;
- no NLP dependency was added;
- existing PyMuPDF installation remains available.

## 4. Exact files changed

For P2-B, only this validation document was created:

- `docs/NLP_ASSISTED_EVIDENCE_EXTRACTION_V1_VALIDATION.md`

No application source files were changed for P2-B. The existing `.replit` OCR dependency configuration and prior P2-A files were left unchanged.

## 5. PhraseMatcher / Matcher concepts

Not implemented because spaCy was unavailable.

The planned configured concepts were:

- `MANAGEMENT_RESPONSIBILITY`
- `AUDITOR_REPORT`
- `FINANCIAL_POSITION`
- `INCOME`
- `COMPREHENSIVE_INCOME`
- `CHANGES_IN_EQUITY`
- `CASH_FLOWS`
- `NOTES`

No matcher logic is active in the application.

## 6. AFS statement variations

Not implemented. The intended aliases included the requested variations such as:

- Statement of Management's Responsibility;
- Independent Auditor's Report;
- Statement(s) of Financial Position;
- Balance Sheet;
- Statement(s) of Income;
- Income Statement;
- Statement(s) of Profit or Loss;
- Statement(s) of Comprehensive Income;
- Other Comprehensive Income;
- Statement(s) of Changes in Equity;
- Changes in Shareholders' Equity;
- Statement(s) of Cash Flows;
- Cash Flow Statement; and
- Notes to Financial Statements.

The underlying required AFS component list was not modified.

## 7. Period/date evidence behavior

Not implemented. Existing period/business rules remain unchanged.

No NLP candidate-year evidence is currently produced for phrases such as:

- `for the fiscal year ended 31 December 2025`;
- `as at December 31, 2025`; or
- `December 31, 2025 and 2024`.

Multi-Year AFS Support was not changed.

## 8. Company-name evidence behavior

Not implemented. The existing fuzzy company-name matcher remains unchanged.

No token normalization for punctuation, repeated spaces, or suffix variants such as `Inc.`, `Incorporated`, `Corp.`, or `Corporation` was added.

## 9. Financial-label evidence behavior

Not implemented. `label_mapping.json` and the existing normalized-label/business mapping remain authoritative and unchanged.

No new accounting equivalence or alias was introduced.

## 10. OCR compatibility

The existing P2 Simple OCR Fallback V1 behavior was not modified.

OCR-derived text continues to use the existing effective page-text path and preserves:

- `original_text`;
- `ocr_text`; and
- `extraction_source`.

No separate OCR-specific NLP rule was added.

## 11. Page-classification integration

Not implemented. The existing deterministic page classifier remains unchanged.

No NLP evidence is currently supplemental, and no conflict-resolution behavior was introduced.

## 12. Auditor-report false-positive safeguard

No changes were made to AFS completeness logic.

The existing rule remains intact:

Reference text does not equal actual component presence.

An `Independent Auditor's Report` page must not satisfy Financial Position, Income, Comprehensive Income, Changes in Equity, or Cash Flows merely because its narrative mentions those concepts.

## 13. Confidence compatibility

Computed Confidence + HITL was not changed.

No arbitrary confidence points, NLP factor, or opaque score was added. Existing deterministic factors, safety caps, routing, reviewer corrections, and final human-controlled disposition remain unchanged.

## 14. Reviewer-facing NLP evidence behavior

Not implemented. No `NLP Evidence` expander or other UI element was added.

The existing Document Review OCR source visibility remains unchanged.

## 15. Test results A–N

Because the required spaCy dependency could not be installed cleanly, P2-B runtime tests were not run and no NLP behavior is claimed.

| Scenario | Expected | Actual | Pass/Fail |
|---|---|---|---|
| A. Exact existing statement title | Recognized normally | NLP layer not implemented | Blocked |
| B. `Cash Flow Statement` | Normalized to Statement of Cash Flows evidence | NLP layer not implemented | Blocked |
| C. `Statements of Financial Position` | Recognized as Financial Position evidence | NLP layer not implemented | Blocked |
| D. Combined Profit or Loss and OCI phrase | Income and OCI evidence recognized | NLP layer not implemented | Blocked |
| E. Auditor narrative references components | Must not count as component presence | No completeness code changed; existing safeguard preserved, but P2-B NLP test not run | Blocked |
| F. Fiscal-year-ended wording | Candidate year 2025 recognized | NLP layer not implemented | Blocked |
| G. Comparative-year wording | Candidate years 2025 and 2024 recognized | NLP layer not implemented | Blocked |
| H. Company punctuation/suffix variation | Evidence supports existing matcher | NLP layer not implemented | Blocked |
| I. OCR-derived supported variation | Same evidence behavior as Text Layer | NLP layer not implemented; existing OCR path unchanged | Blocked |
| J. Unsupported/ambiguous phrase | No invented concept | No NLP layer active; no invented concept added | Blocked |
| K. Existing three demo documents | Remain intact | No P2-B source changes; existing demos remain intact | Pass |
| L. AFS Completeness Check | Prior false-positive fix remains correct | No completeness code changed; safeguard remains in place | Pass |
| M. Multi-Year AFS | Current/comparative behavior remains intact | No multi-year code changed | Pass |
| N. Computed Confidence + HITL | Continues and remains human-controlled | No confidence or reviewer-disposition code changed | Pass |

The Pass results above are compatibility confirmations only; they do not represent completed NLP coverage.

## 16. Demo-data impact

No demo JSON, seeded document, seeded figure, or reviewer disposition was changed.

The existing three seeded demo documents remain intact.

## 17. Database/schema impact

No database or schema change was made for P2-B.

Existing P2-A page-analysis fields and data remain unchanged.

## 18. Known limitations and blocker

The supported package manager currently resolves or appends the deprecated `fitz` distribution when installing spaCy, even though the project uses `pymupdf`.

The failure occurs before spaCy is installed. Adding a different NLP library, downloading a model, manually copying packages, or bypassing the package firewall would violate the requested low-risk scope.

## 19. Explicit confirmation

- No trained NLP model was added.
- No pretrained spaCy model was downloaded.
- No LLM was added.
- No ML classifier was added.
- No external NLP API was added.
- No vector database was added.
- No background worker was added.
- No runtime NLP evidence is active.
- NLP evidence remains unimplemented because spaCy is unavailable.
- Existing final validation remains rule-based/HITL.
- Existing OCR behavior remains unchanged.

## 20. Recommended next option

Resolve the environment/package-manager mapping that appends deprecated `fitz`, while retaining the existing `pymupdf` dependency. Then install only spaCy and verify `import spacy` plus `spacy.blank("en")` without downloading a pretrained model.

After that environment issue is corrected, P2-B can be revisited with the planned small shared module and deterministic tests.

## 21. Final assessment

**spaCy environment unavailable — implementation stopped as required.**

The current application remains in its prior working state. No partial NLP behavior, schema migration, or UI redesign was introduced.