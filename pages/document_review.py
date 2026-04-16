import pandas as pd
import streamlit as st

from db import save_reviewer_action
from storage import get_document, get_documents, get_pages, get_validations, load_revert_reasons
from ui_helpers import highlight_terms, render_status, show_document_selector, status_badge
from validation_engine import final_recommendation, suggested_revert_reason


def render():
    st.header("Document Review")
    st.caption("Reviewer view for page classification, text evidence, period checks, suggested revert reasons, and final recommendation.")

    document_id = st.session_state.get("active_document_id") or show_document_selector(get_documents(), "doc_review_selector")
    if not document_id:
        return
    st.session_state["active_document_id"] = document_id
    document = get_document(document_id)
    pages = get_pages(document_id)
    validations = get_validations(document_id)
    if not document:
        st.warning("Selected document was not found.")
        return

    st.subheader(f"{document['company_name']} — {document['period_covered_year']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("SEC Registration No.", document["sec_registration_no"])
    col2.metric("Submission Type", document["submission_type"])
    col3.metric("Report Type", document["report_type"])

    st.subheader("Validation Results")
    if validations:
        df = pd.DataFrame(validations)
        df["status_badge"] = df["status"].map(status_badge)
        st.dataframe(df[["rule_name", "status", "message", "suggested_revert_reason"]], width="stretch", hide_index=True)
    else:
        st.info("No validation rows are available yet.")

    st.subheader("Page Review")
    for page in pages:
        title = f"Page {page['page_number']} — {page['page_type']}"
        with st.expander(title, expanded=page["page_number"] in [1, 3, 4]):
            cols = st.columns(4)
            cols[0].write("Orientation")
            cols[0].markdown(f"**{page['orientation']}**")
            cols[1].write("Company Match")
            cols[1].success("Matched") if page["detected_company_match"] else cols[1].warning("Review")
            cols[2].write("Period Match")
            cols[2].success("Matched") if page["detected_period_match"] else cols[2].warning("Review")
            cols[3].write("Readability")
            with cols[3]:
                render_status(page["image_quality_flag"])
            terms = [document["company_name"], str(document["period_covered_year"]), document["sec_registration_no"]]
            st.markdown(f"<div class='text-preview'>{highlight_terms(page['text_preview'], terms)}</div>", unsafe_allow_html=True)

    recommendation = final_recommendation(validations)
    suggested = suggested_revert_reason(validations)
    reasons = load_revert_reasons()
    st.subheader("Reviewer Disposition")
    with st.form("reviewer_disposition"):
        col1, col2 = st.columns(2)
        with col1:
            final = st.selectbox("Final Recommendation", ["Accept", "Revert", "Needs Review"], index=["Accept", "Revert", "Needs Review"].index(recommendation))
        with col2:
            reason_options = [""] + reasons
            reason_index = reason_options.index(suggested) if suggested in reason_options else 0
            revert_reason = st.selectbox("Suggested Revert Reason", reason_options, index=reason_index)
        remarks = st.text_area("Reviewer Remarks", placeholder="Add reviewer notes, issue details, or basis for override.")
        saved = st.form_submit_button("Save Reviewer Recommendation")
    if saved:
        save_reviewer_action(document_id, remarks, final, revert_reason)
        st.success("Reviewer recommendation saved.")
