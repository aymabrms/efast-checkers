import pandas as pd
import streamlit as st

from db import query
from storage import get_documents
from ui_helpers import metric_card, status_badge


def render():
    st.header("Dashboard")
    st.caption("SEC Philippines AFS intake, validation, and extraction overview for reviewer operations.")

    documents = get_documents()
    validations = query("SELECT status, COUNT(*) AS count FROM validations GROUP BY status")
    figures_count = query("SELECT COUNT(*) AS count FROM extracted_figures")
    reviewer_edits = query("SELECT COUNT(*) AS count FROM extracted_figures WHERE reviewer_edited = 1")
    actions = query("SELECT final_recommendation, COUNT(*) AS count FROM reviewer_actions GROUP BY final_recommendation")

    validation_counts = {row["status"]: row["count"] for row in validations}
    action_counts = {row["final_recommendation"]: row["count"] for row in actions}
    needs_review = validation_counts.get("Warning", 0) + validation_counts.get("Failed", 0)

    cols = st.columns(6)
    cards = [
        ("Uploaded Documents", len(documents), "Stored intake records"),
        ("Needing Review", needs_review, "Warnings or failed rules"),
        ("Accepted", action_counts.get("Accept", 0), "Reviewer recommendations"),
        ("Revert", action_counts.get("Revert", 0), "Reviewer recommendations"),
        ("Extracted Figures", figures_count[0]["count"] if figures_count else 0, "Rows in reusable database"),
        ("Corrected Entries", reviewer_edits[0]["count"] if reviewer_edits else 0, "Reviewer-edited values"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    st.subheader("Recent Document Queue")
    if documents:
        df = pd.DataFrame(documents)[["id", "filename", "company_name", "sec_registration_no", "period_covered_year", "submission_type", "uploaded_at"]]
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("The queue is empty. Load the demo document or upload a readable PDF.")

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Validation Summary")
        if validations:
            df = pd.DataFrame(validations)
            df["Status"] = df["status"].map(status_badge)
            st.bar_chart(df.set_index("status")["count"])
            st.markdown(" ".join(df["Status"].tolist()), unsafe_allow_html=True)
        else:
            st.info("No validation results yet.")
    with right:
        st.subheader("Extraction Volume by Field")
        rows = query("SELECT normalized_label, COUNT(*) AS count FROM extracted_figures GROUP BY normalized_label ORDER BY count DESC")
        if rows:
            st.bar_chart(pd.DataFrame(rows).set_index("normalized_label")["count"])
        else:
            st.info("No extracted figures yet.")
