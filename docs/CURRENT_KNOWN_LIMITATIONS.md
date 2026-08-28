# SEC eFAST Checkers — Current Known Limitations

Prioritized by impact on correctness, production readiness, and scale. These are current-state observations only; this document is not a roadmap.

## 1. Correctness and extraction limitations

1. **No general OCR path.** Image-only or scanned PDFs are not converted into reliable text. When no pages or no figure matches are available, the upload flow can substitute seeded demo data, which may not represent the uploaded filing.
2. **Regex/text-preview extraction is narrow.** Figure extraction requires supported labels, a year, and a numeric value in a simple sequence. It does not parse arbitrary table geometry, merged cells, multi-line labels, or varied financial-statement layouts.
3. **Only the first 2,000 characters of each page are retained for analysis.** Text, validation evidence, classification, and figure extraction beyond that preview are unavailable to those flows.
4. **Page-level units are simplified.** One `Pesos`, `Thousands`, or `Millions` basis is inferred for an entire page. Mixed-unit pages are not modeled.
5. **Validation is heuristic.** Company matching, period checks, submission checks, completeness, and readability use fuzzy matching, substring checks, keyword rules, exact labels, or text length. They are not authoritative filing determinations.
6. **Comparative years are not independently validated.** They are parsed for figure extraction and represented in sample text, but there is no dedicated rule confirming each comparative year.
7. **Confidence is not calculated.** Dynamic rows get a fixed confidence value and demo rows get seeded values. The displayed percentage is explicitly an estimate, not a calibrated score.

## 2. Product and workflow limitations

1. **The primary company master is fictional and singular.** The current validation path loads the Audentia master record, so uploaded companies are not resolved through a real multi-company master system.
2. **Historical and rankings screens are seeded projections.** They do not use uploaded or reviewed SQLite figures and therefore should not be treated as live institutional analytics.
3. **Reviewer history is not an append-only audit trail.** Each document has one unique reviewer-action row; saving again updates it. The UI presents the current saved action rather than a complete sequence of reviewer decisions.
4. **No reviewer identity or access control exists.** There is no authentication, authorization, user identity, role model, or production audit attribution.
5. **There is no live SEC/eFAST connection.** The app has no filing ingestion API, filing-status synchronization, or external registry lookup.
6. **There is no PDF image viewer.** Page review exposes extracted text previews and metadata, not rendered page images or table overlays.
7. **The settings page is reference-only.** Demo/config data must be changed in files; no live editor is implemented.
8. **Unsaved changes are not guarded.** Switching documents can discard unsaved form/editor state in the current Streamlit session.

## 3. Data integrity and persistence limitations

1. **No declared foreign keys or cascades.** `document_id` relationships are enforced by application queries rather than SQLite constraints.
2. **Reprocessing replaces analysis rows.** `replace_document_analysis()` deletes and reinserts a document's page, validation, and figure rows, so re-analysis can discard figure-review changes for that document.
3. **Uploaded files use the original filename as the local target.** There is no application-level uniqueness or sanitization policy around the upload path.
4. **SQLite operations use per-operation connections.** This is adequate for the current prototype but has not been designed or demonstrated for concurrent reviewer traffic, large filing volumes, or distributed deployment.
5. **Session state is local to a Streamlit session.** The active document and fallback warning are not shared across users or persisted as workflow state.

## 4. Production-readiness gaps

1. No authentication, authorization, reviewer identity, or immutable audit logging.
2. No production database migration strategy or operational backup/restore workflow in the application.
3. No external object storage, malware scanning, retention policy, or document lifecycle controls for uploaded PDFs.
4. No background processing, job status, retry queue, or timeout model for large PDFs.
5. No automated end-to-end test suite or production monitoring is present in the inspected prototype files.
6. Streamlit server settings disable CORS and XSRF protection in `.streamlit/config.toml`; these settings are part of the current prototype configuration and require deployment-specific security review.
7. The broader workspace contains separate TypeScript/API/PostgreSQL scaffolding, but the current SEC Streamlit app does not use it, so those components do not provide production services for this prototype.
