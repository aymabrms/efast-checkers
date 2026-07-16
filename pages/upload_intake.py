import streamlit as st

from config import DEFAULT_COMPARATIVE_YEARS, DEFAULT_COMPANY, DEFAULT_FILING_YEAR, DEFAULT_PERIOD_YEAR, DEFAULT_REPORT_TYPE, DEFAULT_SUBMISSION_TYPE, UPLOADS_DIR
from db import insert_document, replace_document_analysis
from extraction_engine import extract_figures_from_pages, fiscal_year_candidates
from pdf_utils import extract_pdf_pages, prepare_uploaded_file
from storage import ensure_demo_document, load_company_master, load_demo_data
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
        metadata = {
            "filename": uploaded.name if uploaded else "manual_demo_fallback.pdf",
            "company_name": company_name,
            "sec_registration_no": sec_no,
            "report_type": report_type,
            "period_covered_year": int(period_year),
            "comparative_years": comparative_years,
            "submission_type": submission_type,
            "filing_year": int(filing_year),
        }
        document_id = insert_document(metadata)
        raw_pages: list = []
        if uploaded:
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
            if not figures:
                figures = load_demo_data()["sample_figures"]
                st.warning("Readable text was found, but figure extraction was limited. Demo extraction rows were loaded for reviewer simulation.")
        else:
            demo = load_demo_data()
            pages = analyze_pages(demo["sample_pages"], metadata, company_master)
            validations = validate_document(pages, metadata, company_master)
            figures = demo["sample_figures"]
            if uploaded:
                st.warning("PDF text extraction produced no pages. Demo fallback data has been loaded for reviewer simulation — actual document content was not extracted.")
            else:
                st.warning("No PDF was uploaded. Demo fallback mode is active.")
        replace_document_analysis(document_id, pages, validations, figures)
        st.session_state["active_document_id"] = document_id
        st.success(f"Document #{document_id} saved and analyzed.")

    if st.button("Load Demo Document", type="primary"):
        document_id = ensure_demo_document()
        st.session_state["active_document_id"] = document_id
        st.success(f"Demo document #{document_id} loaded for Audentia Fortuna Holdings, Inc.")

    st.info("Uploaded files are saved in the local uploads folder. Metadata and reviewer work are stored in SQLite.")
