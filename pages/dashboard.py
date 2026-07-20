import pandas as pd
import streamlit as st

from db import query
from storage import get_documents
from ui_helpers import format_timestamp_pst, metric_card, recommendation_badge, status_badge

# Filenames that belong to seeded demo documents
_DEMO_FILENAMES = {
    "audentia_fortuna_afs_2025_demo.pdf",
    "malaya_northstar_afs_2025_demo.pdf",
    "haraya_logistics_afs_2024_demo.pdf",
}


def render():
    st.header("Dashboard")
    st.caption("AFS intake, validation, and extraction overview for reviewer operations.")

    st.markdown(
        "<span class='badge' style='background:#d9f7e8;color:#0f6b43'>Live DB Data</span> "
        "All metrics and queues below reflect documents currently stored in the database.",
        unsafe_allow_html=True,
    )

    documents = get_documents()
    validations = query("SELECT status, COUNT(*) AS count FROM validations GROUP BY status")
    figures_count = query("SELECT COUNT(*) AS count FROM extracted_figures")
    reviewer_edits = query("SELECT COUNT(*) AS count FROM extracted_figures WHERE reviewer_edited = 1")
    actions = query("SELECT final_recommendation, COUNT(*) AS count FROM reviewer_actions GROUP BY final_recommendation")

    # Per-document latest recommendation for queue display
    doc_actions = query(
        "SELECT document_id, final_recommendation FROM reviewer_actions "
        "WHERE id IN (SELECT MAX(id) FROM reviewer_actions GROUP BY document_id)"
    )
    rec_by_doc = {row["document_id"]: row["final_recommendation"] for row in doc_actions}

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
        # Build a presentation-friendly display dataframe
        rows = []
        for doc in documents:
            rec = rec_by_doc.get(doc["id"], "")
            source = "Demo" if doc.get("filename", "") in _DEMO_FILENAMES else "Uploaded"
            rows.append({
                "ID": doc["id"],
                "Company Name": doc["company_name"],
                "SEC Registration No.": doc["sec_registration_no"],
                "Period Covered Year": doc["period_covered_year"],
                "Submission Type": doc["submission_type"],
                "Recommendation": rec or "—",
                "Source": source,
                "Uploaded At": format_timestamp_pst(doc.get("uploaded_at") or ""),
            })
        display_df = pd.DataFrame(rows)

        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Company Name": st.column_config.TextColumn("Company Name"),
                "SEC Registration No.": st.column_config.TextColumn("SEC Registration No."),
                "Period Covered Year": st.column_config.NumberColumn("Period", width="small"),
                "Submission Type": st.column_config.TextColumn("Submission Type", width="medium"),
                "Recommendation": st.column_config.TextColumn("Recommendation", width="medium"),
                "Source": st.column_config.TextColumn("Source", width="small"),
                "Uploaded At": st.column_config.TextColumn("Uploaded At", width="medium"),
            },
        )

        # Recommendation badge legend
        st.markdown(
            "<div style='margin:.4rem 0 .75rem;font-size:.82rem;color:#587267;'>"
            "Recommendations: "
            + recommendation_badge("Accept")
            + "&nbsp;"
            + recommendation_badge("Revert")
            + "&nbsp;"
            + recommendation_badge("Needs Review")
            + "&nbsp;&nbsp;·&nbsp;&nbsp;"
            "<span class='badge' style='background:#f0f0f0;color:#555;font-size:.78rem;padding:.2rem .55rem;'>Demo</span> = seeded demo document"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("**Open a document for review:**")
        doc_labels = {
            f"#{doc['id']} — {doc['company_name']} — {doc['period_covered_year']}": doc
            for doc in documents
        }
        col_sel, col_btn = st.columns([4, 1])
        with col_sel:
            chosen_label = st.selectbox(
                "Select document",
                list(doc_labels.keys()),
                label_visibility="collapsed",
                key="dashboard_doc_pick",
            )
        with col_btn:
            if st.button("Open in Review →", type="primary", use_container_width=True):
                chosen_doc = doc_labels[chosen_label]
                st.session_state["active_document_id"] = chosen_doc["id"]
                st.session_state["_nav_to"] = "Document Review"
                st.rerun()
    else:
        st.info("The queue is empty. Load the demo document or upload a readable PDF.")

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Validation Summary")
        if validations:
            df = pd.DataFrame(validations)
            df["Status"] = df["status"].map(status_badge)
            st.bar_chart(df.set_index("status")["count"], color="#0f5b3f")
            st.markdown(" ".join(df["Status"].tolist()), unsafe_allow_html=True)
        else:
            st.info("No validation results yet.")
    with right:
        st.subheader("Extraction Volume by Field")
        rows = query(
            "SELECT normalized_label, COUNT(*) AS count FROM extracted_figures "
            "GROUP BY normalized_label ORDER BY count DESC"
        )
        if rows:
            st.bar_chart(pd.DataFrame(rows).set_index("normalized_label")["count"])
        else:
            st.info("No extracted figures yet.")
