import streamlit as st

from config import DEFAULT_COMPARATIVE_YEARS, DEFAULT_COMPANY, DEFAULT_FILING_YEAR, DEFAULT_PERIOD_YEAR, DEFAULT_REPORT_TYPE, DEFAULT_SUBMISSION_TYPE, UPLOADS_DIR
from db import insert_document, replace_document_analysis
from extraction_engine import extract_figures_from_pages, fiscal_year_candidates
from pdf_utils import extract_pdf_pages, prepare_uploaded_file
from storage import ensure_demo_document, load_company_master
from validation_engine import analyze_pages, validate_document


def render():
    st.header("Upload / Intake")
    st.caption("Register AFS metadata, upload a PDF, or load the fictional demonstration case.")

    with st.form("intake_form"):
        uploaded = st.file_uploader("AFS PDF", type=["pdf"])
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", DEFAULT_COMPANY)
            sec_no = st.text_input("SEC Registration Number", "")
            report_type = st.text_input("Report Type", DEFAULT_REPORT_TYPE)
            period_year = st.number_input("Period Covered Year", min_value=2000, max_value=2100, value=DEFAULT_PERIOD_YEAR)
        with col2:
            comparative_years = st.text_input("Comparative Years", DEFAULT_COMPARATIVE_YEARS)
            submission_type = st.text_input("Submission Type", DEFAULT_SUBMISSION_TYPE)
            filing_year = st.number_input("Filing Year", min_value=2000, max_value=2100, value=DEFAULT_FILING_YEAR)
        submitted = st.form_submit_button("Save Intake and Analyze")

    if submitted:
        if not uploaded:
            st.error("Upload a PDF to analyze, or choose Load Demo Document for the explicit demo workflow.")
            return

        metadata = {
            "filename": uploaded.name,
            "company_name": company_name,
            "sec_registration_no": sec_no,
            "report_type": report_type,
            "period_covered_year": int(period_year),
            "comparative_years": comparative_years,
            "submission_type": submission_type,
            "filing_year": int(filing_year),
        }
        document_id = insert_document(metadata)
        saved_path = prepare_uploaded_file(uploaded, UPLOADS_DIR)
        raw_pages, extraction_errors = extract_pdf_pages(saved_path)
        if extraction_errors:
            for err in extraction_errors:
                st.warning(f"PDF parser issue: {err}")
        company_master = load_company_master()
        if raw_pages:
            pages = analyze_pages(raw_pages, metadata, company_master)
            validations = validate_document(pages, metadata, company_master)
            figures = extract_figures_from_pages(pages, fiscal_year_candidates(metadata))
            low_text = any(page.get("image_quality_flag") in ("Warning", "Failed") for page in pages)
            has_check_source = any(row.get("status") == "Check Source" for row in figures)
            if low_text:
                analysis_outcome = "Possible Scanned / Low-Text PDF"
                outcome_message = (
                    "Real PDF pages were analyzed, but one or more pages have low extracted text. "
                    "This is a preliminary text-quality signal; image-content rotation not represented "
                    "in PDF metadata is not automatically detected."
                )
                st.warning(f"**{analysis_outcome}** — {outcome_message}")
            elif not figures or has_check_source:
                analysis_outcome = "Real PDF Analysis Completed — Figures Need Review"
                outcome_message = (
                    "No supported financial figures were reliably extracted from this document."
                    if not figures
                    else "Ambiguous numeric formatting was detected in one or more figures; verify the original source."
                )
                st.warning(f"**{analysis_outcome}** — {outcome_message}")
            else:
                analysis_outcome = "Real PDF Analysis Completed"
                outcome_message = "Real PDF pages, validations, and supported figure extraction were completed."
                st.success(f"**{analysis_outcome}** — {outcome_message}")
            if not figures:
                st.warning("No supported financial figures were reliably extracted from this document.")
            elif has_check_source:
                st.warning(
                    "Some extracted values have ambiguous numeric formatting. Original raw values were retained; "
                    "normalized peso values are blank until the reviewer verifies the source."
                )
        else:
            pages = []
            figures = []
            analysis_outcome = "Extraction Failed — Manual Review Required"
            outcome_message = (
                "No page text could be extracted from the uploaded PDF. No demo pages or demo figures were inserted."
            )
            validations = []
            st.error(f"**{analysis_outcome}** — {outcome_message}")

        validations.append({
            "rule_name": "PDF analysis outcome",
            "status": "Passed" if analysis_outcome == "Real PDF Analysis Completed" else "Needs Review",
            "message": f"{analysis_outcome}. {outcome_message}",
            "suggested_revert_reason": (
                "Poor image quality"
                if analysis_outcome in ("Possible Scanned / Low-Text PDF", "Extraction Failed — Manual Review Required")
                else ""
            ),
        })
        replace_document_analysis(document_id, pages, validations, figures)
        st.session_state["active_document_id"] = document_id
        st.success(f"Document #{document_id} saved and analyzed.")

    if st.button("Load Demo Document", type="primary"):
        document_id = ensure_demo_document()
        st.session_state["active_document_id"] = document_id
        st.success(f"Demo document #{document_id} loaded for Audentia Fortuna Holdings, Inc.")

    st.info("Uploaded files are saved in the local uploads folder. Metadata and reviewer work are stored in SQLite.")
