# Stock Corporation AFS Completeness Check V1 — Updated Validation

## 1. Scope of the correction

This correction addresses only the documented false-positive behavior in which an Independent Auditor's Report could be treated as evidence that the underlying financial-statement components were present.

The correction does not redesign the interface or change page classification, Proof of BIR Filing, reviewer disposition, figure extraction, Historical View, Rankings, or demo seeding.

## 2. Exact files changed

- `validation_engine.py` — excludes Independent Auditor's Report pages from evidence for five financial-statement components.
- `docs/AFS_COMPLETENESS_CHECK_V1_VALIDATION_UPDATED.md` — records the corrected rules, tests, demo impact, and remaining limitations.

The existing completeness table in `pages/document_review.py` was not changed.

## 3. Previous issue

The completeness evaluator previously searched the page type and full extracted text of every page for each component.

An Independent Auditor's Report commonly contains narrative wording such as:

> the financial statements comprise the statements of financial position, income, comprehensive income, changes in equity and cash flows

The component regular expressions interpreted those references as evidence that the actual financial-statement pages were present. As a result, the auditor page could be reported as the detected page for Financial Position, Income, Comprehensive Income, Changes in Equity, and Cash Flows.

This could incorrectly produce a Passed completeness result when an actual component page—especially Statement of Cash Flows—was missing.

## 4. Updated business rule

**Reference text does not equal actual component presence.**

A page classified as `Independent Auditor's Report` (including the curly-apostrophe form `Independent Auditor’s Report`):

- still counts normally as evidence for the Independent Auditor's Report requirement;
- cannot provide strong evidence for the five affected financial-statement components;
- cannot provide weak evidence for those components;
- is not included in their detected page numbers.

Page order remains flexible. No fixed page numbers are required.

## 5. Updated detection logic

### Common page-number behavior

For each component, the evaluator collects page numbers only from pages that remain eligible for that component and match its classification, strong rules, or weak rules. Page numbers are deduplicated, sorted, and formatted as a single page or range.

An excluded auditor page is never added to the matching-page list for the five affected components.

### Statement of Financial Position / Balance Sheet

**Allowed evidence**

- Exact page classification:
  - `Statement of Financial Position / Balance Sheet`
  - `Statement of Financial Position`
  - `Balance Sheet`
- Strong evidence on a non-auditor page:
  - `Statement of Financial Position`
  - `Statements of Financial Position`
  - `Balance Sheet`
- Weak evidence on a non-auditor page:
  - `total assets`
  - `total liabilities`

**Excluded evidence**

- All strong and weak matches found on a page classified as `Independent Auditor's Report`.

### Statement of Profit or Loss / Statement of Income

**Allowed evidence**

- Exact page classification:
  - `Statement of Income / Receipts and Expenses`
  - `Statement of Income`
  - `Income Statement`
  - `Statement of Operations`
- Strong evidence on a non-auditor page:
  - `Statement of Profit or Loss`
  - `Statement of Income`
  - `Statement of Operations`
  - `Income Statement`
  - `Profit or Loss`
- Weak evidence on a non-auditor page:
  - `net income`
  - `net loss`
  - `gross revenue`

**Excluded evidence**

- All strong and weak matches found on a page classified as `Independent Auditor's Report`.

### Other Comprehensive Income

**Allowed evidence**

- Exact page classification:
  - `Statement of Comprehensive Income`
  - `Other Comprehensive Income`
- Strong evidence on a non-auditor page:
  - `Other Comprehensive Income`
  - `Statement of Comprehensive Income`
  - `Statements of Comprehensive Income`
  - `Comprehensive Income`
- Weak evidence on a non-auditor page:
  - `comprehensive`

**Excluded evidence**

- All strong and weak matches found on a page classified as `Independent Auditor's Report`.

### Statement of Changes in Equity

**Allowed evidence**

- Exact page classification:
  - `Statement of Changes in Equity / Fund Balance`
  - `Statement of Changes in Equity`
- Strong evidence on a non-auditor page:
  - `Statement of Changes in Equity`
  - `Statements of Changes in Equity`
  - `Changes in Equity`
- Weak evidence on a non-auditor page:
  - `fund balance`
  - `shareholder equity`
  - `shareholders' equity`

**Excluded evidence**

- All strong and weak matches found on a page classified as `Independent Auditor's Report`.

### Statement of Cash Flows

**Allowed evidence**

- Exact page classification:
  - `Statement of Cash Flows`
- Strong evidence on a non-auditor page:
  - `Statement of Cash Flows`
  - `Statements of Cash Flows`
  - `Cash Flows`
- Weak evidence on a non-auditor page:
  - `operating activities`
  - `financing activities`

**Excluded evidence**

- All strong and weak matches found on a page classified as `Independent Auditor's Report`.

## 6. Auditor's Report exclusion behavior

An Independent Auditor's Report page cannot satisfy:

1. Statement of Financial Position / Balance Sheet
2. Statement of Profit or Loss / Statement of Income
3. Other Comprehensive Income
4. Statement of Changes in Equity
5. Statement of Cash Flows

This exclusion happens before strong or weak component text is evaluated.

The page still satisfies the Independent Auditor's Report requirement through its existing classification and detection rules. Statement of Management's Responsibility, Notes to Financial Statements, and Proof of BIR Filing behavior remain unchanged.

## 7. Combined Income + OCI behavior

A legitimate combined statement remains supported.

A non-auditor page containing a heading such as:

> Statement of Profit or Loss and Other Comprehensive Income

satisfies both:

- Statement of Profit or Loss / Statement of Income
- Other Comprehensive Income

Both rows report the same combined statement page as evidence. A separate Other Comprehensive Income page is not required.

## 8. Test results

| Scenario | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|
| A. Full AFS with all required components | Completeness Passed | Passed with all eight components detected; shuffled page order did not affect the result | Pass |
| B. Auditor mentions all statements, but actual Cash Flows page is missing | Cash Flows Missing; completeness Failed; reason Incomplete pages | Cash Flows was Missing with no detected page; completeness was Failed; suggested reason was Incomplete pages | Pass |
| C. Only SMR and Auditor's Report | Other financial statements are Missing | Only Management's Responsibility and Auditor's Report were Detected; the other six components were Missing | Pass |
| D. Combined Income + OCI statement | Both requirements Detected | Income and Other Comprehensive Income were both Detected on the same combined page | Pass |
| E. Actual Financial Position page | Position Detected from the actual page, not the auditor page | Financial Position was Detected only on Page 4; the auditor page was excluded | Pass |
| F. Existing three demo documents | App remains operational and demo records remain intact | All three records remained intact; corrected completeness results were Audentia Failed, Malaya Passed, and Haraya Failed | Pass |

## 9. Demo impact

No seeded page, validation, figure, or reviewer-action records were modified.

The Document Review completeness table is computed from the stored page evidence, so one displayed result changed after the correction:

| Demo document | Before correction | After correction | Reason |
|---|---|---|---|
| Audentia Fortuna Holdings, Inc. | Passed | Failed | Auditor Page 3 no longer supplies Comprehensive Income or Changes in Equity evidence; no separate eligible pages provide those components |
| Malaya Northstar Manufacturing Corp. | Passed | Passed | It has eligible statement evidence, including its combined Comprehensive Income statement and Changes in Equity page |
| Haraya Logistics and Trade, Inc. | Failed | Failed | Required components remain missing after auditor-reference evidence is excluded |

The database remains at documents 1–3 with 19 seeded figure rows. Existing reviewer dispositions remain unchanged: Malaya is Accept and Haraya is Revert.

## 10. Known remaining limitations

1. The exclusion relies on the page being classified as an Independent Auditor's Report. Straight and curly apostrophes are normalized, but an auditor page assigned a different page type may still contribute text evidence to another component.
2. Strong component phrases on other narrative page types can still be treated as component evidence because the evaluator does not model document section boundaries.
3. Exact page classification is accepted as Detected even when the stored text preview is sparse.
4. The page classifier uses ordered keyword matching and returns the first matching page type.
5. The intake metadata does not independently verify that the filer is legally a stock corporation; the check is scoped to submissions identified as AFS.
6. Proof of BIR Filing detects text indicators only and does not authenticate stamps, signatures, dates, or filing status.
7. Image-only pages without useful extracted text cannot be reliably evaluated by the text-based rules.
8. Seeded validation-card wording remains unchanged even when the new completeness table recomputes a stricter result from the stored pages.

## 11. Final assessment

**Safe for prototype demonstration.**

The specific auditor-report false positive documented in the original validation has been corrected, the required scenarios pass, combined Income/OCI remains supported, and the demo data and reviewer workflow remain intact. The completeness result should still be presented as a rule-based prototype signal rather than a production-grade document-authentication decision.