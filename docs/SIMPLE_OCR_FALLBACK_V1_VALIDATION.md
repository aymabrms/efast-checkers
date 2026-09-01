# Simple OCR Fallback V1 — Validation

## 1. Scope

Simple OCR Fallback V1 allows real uploaded PDF pages with little or no usable text-layer content to pass through a bounded Tesseract OCR fallback before entering the existing SEC eFAST Checkers analysis pipeline.

Normal PDF text extraction remains the primary path. OCR is attempted only for low-text pages and is adopted only when it improves usable text content.

The implementation does not add a separate OCR validation engine and does not change GIS, Historical View, Rankings, AFS completeness business rules, demo seeding, final reviewer disposition, Multi-Year AFS Support, Computed Confidence weights, or Test Upload Management.

## 2. OCR engine and environment

- OCR engine: Tesseract OCR 5.5.0
- PDF rendering: existing PyMuPDF
- Render resolution: approximately 200 DPI
- OCR invocation: direct bounded Tesseract command
- Default Tesseract language behavior: English
- Python OCR wrapper: none required

No external API, hosted OCR service, ML integration, or background worker is used.

## 3. Availability and enablement

Tesseract was not initially present in the runtime:

`tesseract: command not found`

It was enabled through Replit's supported Nix system-dependency mechanism. The resulting `.replit` configuration includes `tesseract` in the existing Nix package list.

Verification after enablement:

`tesseract 5.5.0`

## 4. Exact files changed

- `.replit` — adds the Tesseract system dependency.
- `pdf_utils.py` — adds bounded per-page OCR rendering, invocation, improvement comparison, source labeling, and rotation-metadata handling.
- `validation_engine.py` — carries original text, OCR text, and extraction source into analyzed page records.
- `db.py` — adds the minimum traceability columns and persists their values.
- `pages/upload_intake.py` — wraps PDF extraction/OCR processing in a simple working spinner.
- `pages/document_review.py` — displays Text Layer versus OCR Fallback source and the OCR fallback note.
- `docs/SIMPLE_OCR_FALLBACK_V1_VALIDATION.md` — records implementation and A–K validation.

## 5. OCR fallback trigger

For every real uploaded PDF page:

1. PyMuPDF attempts normal text extraction first.
2. If extracted text contains at least 140 non-whitespace characters, the page remains on the Text Layer path and Tesseract is not invoked.
3. If extracted text contains fewer than 140 characters, only that page is rendered and passed to Tesseract.
4. OCR text is compared with the original using a deterministic usable-text score based on alphanumeric content.
5. OCR text becomes the effective page text only when its usable-text score is greater than the original text score.
6. If OCR is empty, fails, times out, or does not improve the page, the original text remains effective.

This reuses the prototype's existing 140-character low-text / possible-scan threshold.

## 6. Text-layer and OCR-source handling

The effective text used by the existing pipeline remains in `text_preview`.

Reviewer traceability is stored separately:

- `original_text` — original PDF text-layer extraction;
- `ocr_text` — Tesseract output when OCR was attempted; and
- `extraction_source` — `Text Layer` or `OCR Fallback`.

For a readable text-layer PDF:

- source remains `Text Layer`;
- OCR is not invoked;
- OCR text remains empty; and
- normal extracted text is preserved.

For an image-only page with useful OCR:

- original text remains empty or low-text;
- OCR output is stored separately;
- source becomes `OCR Fallback`; and
- OCR output becomes the effective pipeline text.

## 7. Rotation handling

Before OCR, the renderer uses the existing PDF page rotation metadata.

PyMuPDF's rendered page already reflects that metadata, so the OCR render matrix applies the inverse stored rotation to normalize the final pixels. Tests confirmed a page carrying 90-degree metadata produced upright OCR text and retained `rotation_degrees = 90`.

No visual orientation model or image-content orientation detector was added.

Current limitation:

`Image-content rotation not represented in PDF metadata is not yet automatically detected.`

## 8. How OCR feeds existing validation and extraction

When OCR improves the page, its effective text is passed unchanged through the existing:

- page classification;
- company and period checks;
- AFS completeness evaluation;
- BIR text-evidence evaluation;
- financial-label extraction;
- selected-year and multi-year extraction;
- numeric safety validation; and
- Computed Confidence + HITL workflow.

No OCR-specific business rules or OCR-only figure extractor were created.

## 9. Numeric safety behavior

OCR text uses the same existing numeric parser and safety rules as text-layer content.

Actual Tesseract test output preserved:

- `6.837.912.90`
- `A8849,399.68`

For both values:

- displayed raw value remained unchanged;
- normalized peso value remained NULL;
- Computed Confidence was capped at 49% Low;
- review status was Check Source; and
- no automatic correction was attempted.

OCR does not manufacture missing figures, fiscal years, or normalized values.

## 10. Computed Confidence compatibility

The existing confidence formula and weights were not changed.

OCR source is visible to the reviewer but does not itself add confidence points and is not treated as an ML probability.

Each OCR-derived row is scored from its existing:

- effective page quality;
- label match;
- fiscal-year association;
- numeric parse;
- unit basis; and
- source snippet.

A clean OCR-derived row may receive High confidence when all existing deterministic evidence is strong. OCR does not automatically produce High confidence merely because Tesseract ran: malformed OCR-derived values received 49% Low and Check Source.

If OCR remains unusable, the original low-text page retains the existing Failed/Poor Readability result and confidence safety behavior.

## 11. Performance safeguards

- OCR only runs for pages below 140 extracted-text characters.
- Pages are processed sequentially.
- Each low-text page is rendered at approximately 200 DPI.
- Each Tesseract invocation has a 15-second timeout.
- OCR text is adopted only when it improves usable content.
- Upload / Intake shows a working spinner during PDF text extraction and possible OCR.
- No queues, workers, batch OCR service, or very-high-resolution rendering were added.

## 12. Test results A–K

| Scenario | Expected | Actual | Pass/Fail |
|---|---|---|---|
| A. Readable text-layer PDF | Normal extraction; OCR not invoked | A 387-character text-layer page remained `Text Layer`; an instrumented test proved the OCR function was not called | Pass |
| B. Image-only / very-low-text page | OCR invoked | Image-only PDF had empty original text; Tesseract recovered 281 characters and source became `OCR Fallback` | Pass |
| C. OCR recovers useful heading/text | Existing classification uses OCR text | OCR-recovered SEC and financial-statement heading text populated the existing classifier and validation pipeline rather than remaining unclassified | Pass |
| D. OCR financial page | Existing figure extraction attempted; no demo figures | OCR-derived Total Assets and Gross Revenue rows were extracted from the uploaded page; values matched the test image and no demo values appeared | Pass |
| E. OCR malformed amount | Check Source; unsafe value not normalized | Both malformed examples remained raw, NULL-normalized, 49% Low, and Check Source | Pass |
| F. PDF rotation metadata | Rotation respected for OCR | A 90-degree metadata test retained rotation 90 and produced upright OCR text after deterministic inverse-metadata normalization | Pass |
| G. OCR remains unusable | Poor Readability / manual review; no fabricated result | Blank PDF page remained empty, `Failed` quality, and produced zero figures | Pass |
| H. Multi-year selected document | OCR text participates in selected-year extraction | OCR-derived Total Assets produced independent 2025 and 2024 rows and both fiscal-year filters worked | Pass |
| I. Computed Confidence | Continues; OCR alone does not force High | Existing calculator ran unchanged; clean rows used normal evidence, while malformed OCR rows were capped at 49% Low | Pass |
| J. Test Upload Management | OCR test document deletes safely | Browser-created OCR document, analysis rows, figures, and local file were deleted through Delete → Confirm Delete | Pass |
| K. Existing three demos | Remain intact and unchanged | Documents 1–3, 19 seeded figures, and existing Malaya Accept / Haraya Revert actions remained intact | Pass |

## 13. Demo-data impact

No demo JSON or seeded document content was changed.

The three seeded demo documents remain:

1. Audentia Fortuna Holdings, Inc.
2. Malaya Northstar Manufacturing Corp.
3. Haraya Logistics and Trade, Inc.

Existing seeded figures and reviewer dispositions remain unchanged. Existing seeded pages default to `Text Layer`.

No demo fallback is used for OCR failures or empty extraction.

## 14. Database/schema impact

A small backward-compatible migration adds three nullable/defaulted columns to `page_analysis`:

- `original_text TEXT`
- `ocr_text TEXT`
- `extraction_source TEXT DEFAULT 'Text Layer'`

No existing table, document, validation, figure, correction, or reviewer-action field was removed or rewritten.

The source field defaults old and non-OCR rows to `Text Layer`.

## 15. Known limitations

1. OCR uses Tesseract's default English behavior without custom language packs.
2. There is no image preprocessing, deskewing, denoising, handwriting recognition, or advanced layout recovery.
3. There is no table-cell recognition or geometry-aware column association.
4. Image-content rotation absent from PDF metadata is not automatically detected.
5. OCR is available on the primary PyMuPDF rendering path; if PyMuPDF cannot open/render the PDF and the system falls back entirely to pdfplumber, no image-render OCR pass is available.
6. OCR quality depends on scan resolution, contrast, font, and layout.
7. The spinner may be too brief to observe on fast single-page documents, but remains active during extraction/OCR processing.
8. Tesseract's own confidence output is not used or displayed.

## 16. Explicit confirmations

- OCR is fallback-only.
- Existing usable PDF text remains the primary source.
- No ML model was added.
- No NLP library or external API was added.
- No advanced table-recognition framework was added.
- OCR output is not automatically authoritative.
- OCR output does not automatically Accept or Revert a filing.
- Unsafe OCR-derived numbers remain uncorrected and require human review.

## 17. Final assessment

**Safe for prototype testing.**

The fallback is bounded, traceable, and integrated into the existing workflow without introducing a parallel validation path. Text-layer behavior remains primary, OCR-derived multi-year figures use the existing safety and confidence rules, temporary OCR uploads remain deletable, and seeded demos remain intact.