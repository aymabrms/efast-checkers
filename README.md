# SEC eFAST Checkers – AFS Validation and Figure Extraction MVP

A Streamlit prototype for SEC Philippines-style Annual Financial Statements review. It demonstrates AFS document validation, page review, extracted financial figure review, reviewer corrections, historical storage, and ranking/research views.

## How to run

```bash
streamlit run app.py --server.port 5000
```

## Editable demo content

- `config.py` — app labels, defaults, ranking metrics, paths
- `demo_data.json` — sample pages, validations, extracted figures, historical data, rankings
- `label_mapping.json` — raw financial statement labels mapped to normalized fields
- `revert_reasons.json` — reviewer revert reason dropdown values
- `sample_company_master.json` — fictional company master record

## What is working

- Seven-screen Streamlit navigation
- SQLite tables for documents, company master, page analysis, validations, extracted figures, and reviewer actions
- PDF upload and local file storage
- Text extraction using PyMuPDF with pdfplumber fallback
- Keyword-based AFS page classification
- Metadata/company/period/submission validations
- Page review with company/year highlighting
- Editable extracted figures review table
- Reviewer corrections saved to SQLite
- CSV export for extracted figures, historical data, and ranking data
- Five-year historical trend charts for the fictional demo company
- Ranking screen with selectable revenue metrics

## Simulated or demo-mode behavior

- OCR is represented by a safe demo fallback when PDF text extraction is weak or unavailable
- The default sample AFS document content is fictional and stored in `demo_data.json`
- Historical and ranking datasets are fictional demonstration data
- Figure extraction uses simple rules suitable for an MVP, with demo rows loaded when parsing confidence is insufficient

## Context note

This prototype uses SEC Philippines context and avoids unrelated regulator branding or references.
