# Test Upload Management V1 — Validation

## 1. Scope

Test Upload Management V1 adds a compact management section to Upload / Intake for temporary real or test PDF uploads.

It supports:

- listing only non-demo uploaded documents;
- showing their company, report type, period, analysis status or reviewer recommendation, and upload timestamp;
- deleting one test upload after explicit confirmation;
- removing that document's analysis and reviewer data;
- removing its local PDF when the file is not referenced by another document;
- safely clearing the active-document state when the deleted upload was active;
- permanently protecting the three seeded demo documents from this interface.

The optional Clear All Test Uploads action was intentionally not added. Single-document deletion meets the requested V1 scope with less risk.

No validation, extraction, completeness, Historical View, Rankings, reviewer-decision logic, demo records, or OCR behavior was changed.

## 2. Exact files changed

- `db.py` — adds the atomic document-and-dependent-record deletion operation.
- `storage.py` — adds demo identification, test-upload summary, protected deletion, and local-file cleanup behavior.
- `pages/upload_intake.py` — adds the Test Uploads section and its confirmation/cancel/delete flow.
- `docs/TEST_UPLOAD_MANAGEMENT_V1_VALIDATION.md` — records the implementation and validation results.

## 3. How demo documents are protected

Demo protection does not depend on company display names.

The app reads the configured filenames from `demo_data.json` and treats documents with those seeded filenames as protected:

- `audentia_fortuna_afs_2025_demo.pdf`
- `malaya_northstar_afs_2025_demo.pdf`
- `haraya_logistics_afs_2025_demo.pdf`

Protection is enforced in two places:

1. The Test Uploads section filters demo records out, so it never renders a Delete action for them.
2. The storage deletion function independently refuses to delete a document whose filename belongs to the configured demo suite.

This second guard protects the records even if the deletion function is called outside the current interface.

## 4. How test uploads are identified

A stored document is considered a test upload when its filename is not one of the configured demo-suite filenames.

The Test Uploads section therefore shows only real/test intake records and excludes all three seeded records. Each listed upload shows:

- Company Name
- Report Type
- Period Covered
- Analysis Status / Recommendation
- Uploaded At
- Delete action

Analysis status is summarized from stored validation statuses using the priority Failed, Warning, Needs Review, then Passed. The latest reviewer recommendation is appended when one exists.

## 5. Delete behavior and related tables

Deletion requires two user actions:

1. Select `Delete`.
2. Respond to `Delete this test upload and its analysis data?` with either:
   - `Confirm Delete`
   - `Cancel`

Cancel leaves the document and all related data unchanged.

Confirm Delete rechecks demo protection and then deletes records in one SQLite transaction, in this order:

1. `reviewer_actions`
2. `extracted_figures`
3. `validations`
4. `page_analysis`
5. `documents`

If the document row does not exist, or is protected as a seeded demo, deletion does not proceed.

After a successful deletion:

- the Test Uploads list is refreshed;
- a success message is shown;
- the pending confirmation state is removed;
- `active_document_id` is set to `None` when it pointed to the deleted document.

## 6. Uploaded-file cleanup behavior

The current prototype associates a local upload with its document through the stored filename.

After the SQLite transaction succeeds, the app checks the corresponding file under the local `uploads` directory. The PDF is removed only when:

- the target document was a non-demo upload;
- the filename resolves inside the uploads directory using its basename;
- no other stored document references the same filename; and
- the file currently exists.

When another document references the same filename, the file is preserved.

If local file removal fails because of a filesystem error, the database deletion remains committed and the app reports that the local PDF could not be removed instead of crashing or silently hiding the issue.

## 7. Test results A–E

| Scenario | Expected | Actual | Result |
|---|---|---|---|
| A. Upload a temporary PDF | Upload appears under Test Uploads | `/tmp/test-upload-management-v1.pdf` was uploaded as Temporary Test Upload Co. V1; document #7 appeared with the required columns and Delete action | Pass |
| B. Delete temporary upload | Document and related analysis rows disappear | Cancel first preserved the row; Confirm Delete then removed the document, `reviewer_actions`, `extracted_figures`, `validations`, `page_analysis`, and the local uploaded PDF | Pass |
| C. Delete active test document | Active document state clears safely | The deleted upload was active; deletion set the active state to `None`, the app remained stable, and Document Review subsequently opened without a stale-document crash | Pass |
| D. Seeded demo documents | Remain present and cannot be deleted | All three demos were excluded from Test Uploads; a direct protected-delete check for Audentia was rejected; documents 1–3 remained unchanged | Pass |
| E. Restart/reload app | Three demos remain intact | After workflow restart and browser reload, Audentia, Malaya, and Haraya remained present and no temporary Test Uploads remained | Pass |

Additional verification:

- Python compilation passed.
- `git diff --check` passed.
- The isolated SQLite deletion test confirmed all five table cleanups and local-file removal.
- The live database contained only seeded document IDs 1, 2, and 3 after the browser test.
- The uploads directory contained only its existing `.gitkeep` file after cleanup.
- The Streamlit workflow remained running with no visible traceback or in-app crash state.

## 8. Known limitations

1. Demo/test classification uses configured filenames because the current documents schema has no dedicated source flag. A user upload that deliberately uses an exact seeded demo filename will be protected and excluded from Test Uploads.
2. Local file association also relies on the stored filename. If two documents share a filename, the physical file is preserved until no other document references that filename.
3. Deletion is permanent and has no in-app restore action; the explicit confirmation is the V1 safeguard.
4. Clear All Test Uploads was skipped to keep this enhancement low-risk.
5. This remains a local SQLite/filesystem prototype without authentication or per-user permissions.
6. Existing non-blocking chart warnings may appear in browser logs; they are unrelated to upload management.

## 9. Final assessment

**Safe for prototype testing.**

The requested single-upload management flow works end to end, dependent records and eligible local files are removed safely, active-state deletion does not crash the app, and the three configured seeded demo documents remain protected.