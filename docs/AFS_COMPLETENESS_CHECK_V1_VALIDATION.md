# Stock Corporation AFS Completeness Check V1 — Validation

## Scope

This document describes the current implementation of the Stock Corporation AFS Completeness Check V1. This was a documentation and validation pass only. No application code, demo data, database records, or reviewer data were changed.

## 1. Files changed for this feature

The current implementation of this feature is contained in:

- `validation_engine.py` — component definitions, text/classification evidence matching, completeness and BIR evaluation, page-number formatting, and validation/recommendation integration.
- `pages/document_review.py` — the compact **AFS Completeness Check** table and the BIR stamp-verification note.

The feature does not add a database table or a new application page. The existing `validations` rows for newly analyzed AFS uploads include `AFS Completeness Check` and `Proof of BIR Filing`. The Document Review table recomputes the component evidence from stored page-analysis rows.

## 2. Required AFS components currently checked

For submissions identified as AFS or Annual Financial Statements, the current check includes:

1. Statement of Management's Responsibility
2. Independent Auditor's Report
3. Statement of Financial Position / Balance Sheet
4. Statement of Profit or Loss / Statement of Income
5. Other Comprehensive Income
6. Statement of Changes in Equity
7. Statement of Cash Flows
8. Notes to Financial Statements
9. Proof of BIR Filing as a separate check

The current intake metadata does not contain a separate legal-form field. Consequently, the implementation scopes the check to the prototype's AFS path (`report_type` equal to `AFS`, or a submission type containing Annual Financial Statement) rather than independently verifying that an entity is legally a stock corporation.

## 3. Exact detection logic

### Common evidence behavior

For each stored page, the evaluator creates one lowercase evidence string from:

1. the stored `page_type`; and
2. `text_preview`, or the raw `text` value when a preview is not available.

The evaluator then:

- marks a component **Detected** when the page type exactly matches one of that component's configured page-type aliases, or when a strong regular-expression rule matches the combined evidence string;
- marks a component **Needs Review** when no strong rule matches but a weaker indicator matches;
- marks a component **Missing** when neither type nor text evidence matches.

Detected page numbers are taken from every matching page, deduplicated, sorted, and formatted into single pages or contiguous ranges such as `Page 5` or `Pages 3–5`. Page order is not used to determine a component.

### Component rules

| Component | Page classification used | Strong raw-text rules | Weak rules | Evidence/page behavior |
|---|---|---|---|---|
| Statement of Management's Responsibility | Exact page type `Statement of Management's Responsibility` | `statement of management's responsibility`; `management's responsibility` (apostrophe variants are accepted) | `responsibility` | A matching page is Detected; a page with only the weak word is Needs Review. |
| Independent Auditor's Report | Exact page type `Independent Auditor's Report` | `independent auditor`; `auditor's report`; `we have audited` | `auditor` | The report page is Detected from its classification or strong text. |
| Statement of Financial Position / Balance Sheet | Exact aliases `Statement of Financial Position / Balance Sheet`, `Statement of Financial Position`, or `Balance Sheet` | `statement(s) of financial position`; `balance sheet` | `total assets`; `total liabilities` | Strong text or an exact classification is Detected; total-assets/liabilities-only evidence is Needs Review. |
| Statement of Profit or Loss / Statement of Income | Exact aliases `Statement of Income / Receipts and Expenses`, `Statement of Income`, `Income Statement`, or `Statement of Operations` | `statement(s) of profit or loss`; `statement(s) of income`; `statement(s) of operations`; `income statement`; `profit or loss` | `net income`; `net loss`; `gross revenue` | A standalone `income` word is not enough. Strong text/classification is Detected; weak financial-result wording is Needs Review. |
| Other Comprehensive Income | Exact aliases `Statement of Comprehensive Income` or `Other Comprehensive Income` | `other comprehensive income`; `statement(s) of comprehensive income`; `comprehensive income` | `comprehensive` | Strong text/classification is Detected; the word `comprehensive` alone is Needs Review. |
| Statement of Changes in Equity | Exact aliases `Statement of Changes in Equity / Fund Balance` or `Statement of Changes in Equity` | `statement(s) of changes in equity`; `changes in equity` | `fund balance`; `shareholders' equity` | Strong text/classification is Detected; weaker equity wording is Needs Review. |
| Statement of Cash Flows | Exact page type `Statement of Cash Flows` | `statement(s) of cash flows`; `cash flows` | `operating activities`; `financing activities` | Strong text/classification is Detected; activity-only evidence is Needs Review. |
| Notes to Financial Statements | Exact page type `Notes to Financial Statements` | `notes to financial statements`; `summary of significant accounting`; `basis of preparation` | `accounting policies` | Strong text/classification is Detected; accounting-policies-only evidence is Needs Review. |

The upstream `classify_page()` function is also used for real PDF pages. It uses the existing ordered `PAGE_RULES` list and returns the first matching page type. Completeness evaluation then uses that resulting page type plus the stored page text.

### Completeness result

The component result is:

- **Passed** when all eight required components are Detected.
- **Needs Review** when no required component is Missing, but at least one is only uncertain evidence.
- **Failed** when at least one required component is Missing.

If no required AFS component has any evidence, the stronger message is used:

> The uploaded document does not appear to contain a complete Annual Financial Statement.

That case suggests **Incorrect document filed**. Other missing-component failures suggest **Incomplete pages**. The validation row is included in the existing recommendation logic, where Failed produces a Revert recommendation and Needs Review produces a Needs Review recommendation unless another Failed rule takes precedence.

## 4. False-positive check: auditor-report summary wording

### Finding

**Yes, false-positive component detection exists.**

An Independent Auditor's Report containing wording like:

> the financial statements comprise the statements of financial position, income, comprehensive income, changes in equity and cash flows

can cause the following separate components to be marked **Detected** from Page 3:

- Independent Auditor's Report — from the page classification and auditor-report text.
- Statement of Financial Position / Balance Sheet — from `statement(s) of financial position`.
- Other Comprehensive Income — from `comprehensive income`.
- Statement of Changes in Equity — from `changes in equity`.
- Statement of Cash Flows — from `cash flows`.

With the closely related wording `statements of income`, the Statement of Profit or Loss / Statement of Income rule is also satisfied. The exact sentence above contains standalone `income`, which is not itself a strong Income rule match.

### Why it happens

The evaluator searches the full page text for component phrases and does not distinguish between:

- a statement's own heading or body; and
- an auditor's report describing which statements comprise the financial statements.

The raw-text regular expressions listed above therefore treat the auditor's summary sentence as evidence for the underlying statements. The existing page classifier identifies the page as an Independent Auditor's Report, but the completeness evaluator does not exclude auditor-report pages from evidence for other components.

### Current impact

This can make a document appear complete even when one or more actual statement pages are absent. In particular, an AFS with no standalone Cash Flows page can still be marked complete when the auditor report includes the phrase `cash flows`.

This issue was observed directly: a test document containing management, auditor, position, income, equity, and notes pages—but no Cash Flows page—was evaluated as **Passed**, with Statement of Cash Flows reported on the auditor-report page.

No correction was made in this validation-only task.

## 5. Combined Income + Other Comprehensive Income

Combined presentation is currently supported through independent content rules:

- `Statement of Profit or Loss / Statement of Income` is Detected by phrases such as `statement of profit or loss`, `statement of income`, or `profit or loss`.
- `Other Comprehensive Income` is Detected by `other comprehensive income`, `statement of comprehensive income`, or `comprehensive income`.

Therefore, a single page containing text such as `Combined Statement of Profit or Loss and Other Comprehensive Income` satisfies both requirements. Both rows show the same detected page number. A separate Other Comprehensive Income page is not required.

The auditor-summary false positive described above can also satisfy the Comprehensive Income requirement, which is a current limitation rather than intended combined-statement evidence.

## 6. Proof of BIR Filing

The separate `Proof of BIR Filing` check searches the page classification and extracted text for:

- `Bureau of Internal Revenue`
- `BIR`
- `Income Tax Return`
- `Annual Income Tax Return`
- `tax return`
- `proof of filing`
- `received for filing`

When a matching page is found, the result is **Detected** and the matching page numbers are displayed. When none is found, the result is **Needs Review** and no page numbers are shown.

The implementation does not inspect pixels, authenticate a stamp, or determine whether a document is genuinely received by BIR. The current note is:

> Visual verification of a BIR received stamp is not yet automated in this prototype.

## 7. Scenario validation

The following scenarios were executed against the current evaluator without changing application data.

| Scenario | Current result | Validation |
|---|---|---|
| Complete AFS | **Passed** | A document with all eight components, including a combined Income/Comprehensive Income page, passes. The current demo Audentia result also passes, but some evidence is supplied by the auditor-report summary false positive. |
| Only Statement of Management's Responsibility | **Failed** | Management's Responsibility is Detected and the other seven components are listed as Missing. Suggested reason: **Incomplete pages**. |
| Only BIR/tax-return pages | **Failed** | The stronger incomplete-AFS message is shown. Suggested reason: **Incorrect document filed**. Proof of BIR Filing itself is Detected. |
| AFS missing Cash Flows | **Incorrectly Passed in the false-positive case** | If the auditor report mentions `cash flows`, that page supplies Detected evidence even with no standalone Cash Flows page. This is the main reliability issue. |
| Combined Income/OCI | **Passed** | Both Income and Other Comprehensive Income are Detected from the same combined page. |
| No BIR text evidence | **Needs Review** | Proof of BIR Filing is Needs Review, with no detected pages and the required stamp-verification limitation note. |

## 8. Current demo behavior

The existing `demo_data.json` and SQLite demo records were not modified. The new Document Review table evaluates the stored demo pages using the current rules:

- **Audentia Fortuna Holdings, Inc.** — completeness displays Passed; BIR displays Needs Review. Page 3 is reported as evidence for several components because its auditor-report text lists the underlying statements.
- **Malaya Northstar Manufacturing Corp.** — completeness displays Passed; BIR displays Needs Review. Page 3 similarly contributes false-positive evidence, alongside actual statement pages.
- **Haraya Logistics and Trade, Inc.** — completeness displays Failed; BIR displays Needs Review. It still receives false-positive Position and Income evidence from the auditor report, but remains missing Comprehensive Income, Changes in Equity, and Cash Flows.

The stored seeded reviewer dispositions remain unchanged: Malaya is Accept and Haraya is Revert.

## 9. Known limitations

1. Auditor reports are not excluded from evidence searches, so descriptive statement lists can create false-positive component detections.
2. A missing standalone Cash Flows page can be hidden by `cash flows` in an auditor report.
3. The evaluator is heuristic and does not understand document section boundaries or whether a phrase is a heading versus narrative text.
4. The stock-corporation legal form is not independently captured or verified; the check is scoped to the available AFS metadata.
5. The first-match page classifier can assign a broad page type before later, more specific wording is considered.
6. Scanned or image-only pages without useful extracted text cannot be reliably classified because OCR is not present.
7. BIR detection indicates textual evidence only. It does not authenticate a received stamp, signature, date, or filing status.
8. The completeness table recomputes evidence from stored page analysis, while seeded demo validation rows retain their original demo wording and status.
9. “Detected” means text/classification evidence was found; it does not prove that the component is complete, valid, or presented in the expected accounting format.

## 10. Conclusion

**Requires correction before relying on the completeness result.**

The feature is suitable for showing the intended reviewer workflow in a demo, and the combined Income/Comprehensive Income behavior and BIR limitation are clearly represented. However, the auditor-report summary false positive is material: it can cause missing statement components—especially Cash Flows—to appear present. The current result should therefore be treated as a preliminary display rather than a reliable completeness determination until the evidence rules are refined.