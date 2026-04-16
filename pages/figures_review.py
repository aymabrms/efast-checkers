import pandas as pd
import streamlit as st

from db import update_figure_reviews
from storage import get_document, get_documents, get_figures
from ui_helpers import dataframe_download, format_peso, metric_card, show_document_selector


def render():
    st.header("AFS Figures Extraction Review")
    st.caption("Hero workflow for structured extraction, reviewer correction, and database-ready AFS financial figures.")

    document_id = st.session_state.get("active_document_id") or show_document_selector(get_documents(), "figures_doc_selector")
    if not document_id:
        return
    st.session_state["active_document_id"] = document_id
    document = get_document(document_id)
    figures = get_figures(document_id)
    if not figures:
        st.info("No extracted figures are available for this document yet.")
        return

    df = pd.DataFrame(figures)
    hero_cols = st.columns(4)
    with hero_cols[0]:
        metric_card("Rows Extracted", len(df), "Ready for reviewer validation")
    with hero_cols[1]:
        metric_card("Normalized Fields", df["normalized_label"].nunique(), "Reusable figure buckets")
    with hero_cols[2]:
        metric_card("Fiscal Years", ", ".join(str(x) for x in sorted(df["fiscal_year"].unique(), reverse=True)), "Current and comparative")
    with hero_cols[3]:
        metric_card("Current Revenue", format_peso(df[df["normalized_label"].isin(["gross_revenue", "total_revenue", "revenue"])] ["normalized_peso_value"].max()), "Normalized peso value")

    st.subheader(f"Extracted Figures Review Table — {document['company_name']}")
    review_cols = ["id", "page_number", "statement_type", "raw_label", "normalized_label", "fiscal_year", "displayed_value", "normalized_peso_value", "unit_basis", "source_snippet", "confidence", "review_status", "reviewer_edited", "reviewed_value"]
    editable = df[review_cols].copy()
    editable["reviewed_value"] = editable["reviewed_value"].fillna("")
    edited = st.data_editor(
        editable,
        width="stretch",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "page_number": st.column_config.NumberColumn("Page", disabled=True),
            "statement_type": st.column_config.TextColumn("Statement Type", disabled=True),
            "raw_label": st.column_config.TextColumn("Raw Label", disabled=True),
            "normalized_label": st.column_config.TextColumn("Normalized Label", disabled=True),
            "fiscal_year": st.column_config.NumberColumn("Fiscal Year", disabled=True),
            "displayed_value": st.column_config.TextColumn("Displayed Value", disabled=True),
            "normalized_peso_value": st.column_config.NumberColumn("Normalized Peso Value", disabled=True, format="₱%.0f"),
            "unit_basis": st.column_config.TextColumn("Unit Basis", disabled=True),
            "source_snippet": st.column_config.TextColumn("Source Snippet", disabled=True),
            "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, disabled=True),
            "review_status": st.column_config.SelectboxColumn("Status", options=["Needs Review", "Reviewed", "Corrected", "Rejected"]),
            "reviewer_edited": st.column_config.CheckboxColumn("Reviewer Edited?", disabled=True),
            "reviewed_value": st.column_config.TextColumn("Reviewed Value"),
        },
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Save Corrections", type="primary"):
            update_figure_reviews(document_id, edited.to_dict("records"))
            st.success("Figure review updates saved.")
    with col2:
        export_df = edited.drop(columns=["id"], errors="ignore")
        dataframe_download(export_df, f"sec_efast_figures_document_{document_id}.csv", "Export Figures CSV")

    st.subheader("Normalized Figure Buckets")
    bucket = df.groupby("normalized_label", as_index=False)["normalized_peso_value"].sum().sort_values("normalized_peso_value", ascending=False)
    st.dataframe(bucket, width="stretch", hide_index=True)
