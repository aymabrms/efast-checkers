import math

import pandas as pd
import streamlit as st

from db import update_figure_reviews
from storage import get_document, get_documents, get_figures
from ui_helpers import dataframe_download, format_peso, metric_card, reviewing_banner, show_document_selector

REVENUE_LABELS = {"gross_revenue", "total_revenue", "revenue"}


def _safe_conf_display(val) -> str:
    """Format a 0–1 confidence float as '91% · Est.' or '—' if missing."""
    try:
        v = float(val)
        if math.isnan(v):
            return "—"
        return f"{v * 100:.0f}% · Est."
    except (TypeError, ValueError):
        return "—"


def render():
    st.header("AFS Figures Extraction Review")
    st.caption("Hero workflow for structured extraction, reviewer correction, and database-ready AFS financial figures.")

    documents = get_documents()

    # Resolve active document — prefer session state, fall back to selector
    active_id = st.session_state.get("active_document_id")
    if not active_id:
        active_id = show_document_selector(documents, "figures_doc_selector")
        if not active_id:
            return
        st.session_state["active_document_id"] = active_id
    else:
        with st.expander("Switch document", expanded=False):
            switched_id = show_document_selector(documents, "figures_doc_switcher")
            if switched_id and switched_id != active_id:
                if st.button("Load selected document", key="figures_switch_btn"):
                    st.session_state["active_document_id"] = switched_id
                    st.rerun()

    document_id = st.session_state["active_document_id"]
    document = get_document(document_id)

    if not document:
        st.warning("Selected document was not found. Please choose another document.")
        st.session_state.pop("active_document_id", None)
        return

    # ── Persistent "Currently Reviewing" banner ──────────────────────────────
    reviewing_banner(document)

    if st.session_state.get("last_fallback_doc_id") == document_id:
        st.warning(
            "Prototype Fallback Data Applied — The figures below were not extracted from the uploaded PDF. "
            "Demo data was substituted because extraction did not produce results. "
            "Review and correct values as needed before treating them as authoritative."
        )

    figures = get_figures(document_id)
    if not figures:
        st.info("No extracted figures are available for this document yet.")
        return

    df = pd.DataFrame(figures)

    # Guard NaN in revenue display
    rev_raw = df[df["normalized_label"].isin(REVENUE_LABELS)]["normalized_peso_value"].dropna()
    rev_raw = rev_raw[rev_raw.apply(lambda x: not math.isnan(float(x)) if x is not None else False)]
    rev_display = format_peso(rev_raw.max()) if not rev_raw.empty else "No detected revenue"

    fiscal_years = sorted(df["fiscal_year"].dropna().unique(), reverse=True)
    fiscal_years_display = ", ".join(str(int(y)) for y in fiscal_years) if fiscal_years else "—"

    needs_review_count = int((df["review_status"] == "Needs Review").sum())

    hero_cols = st.columns(5)
    with hero_cols[0]:
        metric_card("Rows Extracted", len(df), "Ready for reviewer validation")
    with hero_cols[1]:
        metric_card("Normalized Fields", df["normalized_label"].nunique(), "Reusable figure buckets")
    with hero_cols[2]:
        metric_card("Fiscal Years", fiscal_years_display, "Current and comparative")
    with hero_cols[3]:
        metric_card("Current Revenue", rev_display, "Normalized peso value")
    with hero_cols[4]:
        metric_card("Needs Review", needs_review_count, "Rows pending reviewer action")

    st.subheader(f"Extracted Figures Review Table — {document['company_name']}")
    st.caption(
        "Confidence values are rule-based estimates from the prototype extraction engine — not ML model scores. "
        "Review and correct as needed before treating figures as authoritative."
    )

    # Build editable view — sort Needs Review rows to the top for easy scanning
    review_cols = [
        "id", "page_number", "statement_type", "raw_label", "normalized_label",
        "fiscal_year", "displayed_value", "normalized_peso_value", "unit_basis",
        "source_snippet", "confidence", "review_status", "reviewer_edited", "reviewed_value",
    ]
    editable = df[review_cols].copy()
    editable["reviewed_value"] = editable["reviewed_value"].fillna("")

    # Add human-readable confidence display column
    editable["conf_display"] = editable["confidence"].apply(_safe_conf_display)

    # Sort: Needs Review first, then by page_number
    sort_key = editable["review_status"].apply(lambda s: 0 if s == "Needs Review" else 1)
    editable = editable.assign(_sort=sort_key).sort_values(["_sort", "page_number"]).drop(columns=["_sort"])

    # Columns shown to reviewer (conf_display replaces raw confidence)
    display_cols = [
        "id", "page_number", "statement_type", "raw_label", "normalized_label",
        "fiscal_year", "displayed_value", "normalized_peso_value", "unit_basis",
        "source_snippet", "conf_display", "review_status", "reviewer_edited", "reviewed_value",
    ]
    editable_view = editable[display_cols].copy()

    edited = st.data_editor(
        editable_view,
        width="stretch",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "page_number": st.column_config.NumberColumn("Page", disabled=True, width="small"),
            "statement_type": st.column_config.TextColumn("Statement Type", disabled=True),
            "raw_label": st.column_config.TextColumn("Raw Label", disabled=True),
            "normalized_label": st.column_config.TextColumn("Normalized Label", disabled=True),
            "fiscal_year": st.column_config.NumberColumn("Fiscal Year", disabled=True, width="small"),
            "displayed_value": st.column_config.TextColumn("Displayed Value", disabled=True),
            "normalized_peso_value": st.column_config.NumberColumn(
                "Normalized (₱)", disabled=True, format="₱%.0f"
            ),
            "unit_basis": st.column_config.TextColumn("Unit Basis", disabled=True, width="small"),
            "source_snippet": st.column_config.TextColumn("Source Snippet", disabled=True),
            "conf_display": st.column_config.TextColumn("Confidence (Est.)", disabled=True, width="medium"),
            "review_status": st.column_config.SelectboxColumn(
                "Status", options=["Needs Review", "Reviewed", "Corrected", "Rejected"]
            ),
            "reviewer_edited": st.column_config.CheckboxColumn("Edited?", disabled=True, width="small"),
            "reviewed_value": st.column_config.TextColumn("Reviewed Value"),
        },
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Save Corrections", type="primary"):
            # Map edits back using the original df index via id column
            records = edited.rename(columns={"conf_display": "confidence"}).to_dict("records")
            # Restore raw confidence from original df for DB writes
            conf_map = dict(zip(df["id"], df["confidence"]))
            for r in records:
                r["confidence"] = conf_map.get(r["id"], r.get("confidence"))
            update_figure_reviews(document_id, records)
            st.success("Figure review updates saved.")
    with col2:
        export_df = edited.drop(columns=["id"], errors="ignore")
        dataframe_download(export_df, f"sec_efast_figures_document_{document_id}.csv", "Export Figures CSV")

    st.subheader("Normalized Figure Buckets")
    bucket = (
        df.groupby("normalized_label", as_index=False)["normalized_peso_value"]
        .sum()
        .sort_values("normalized_peso_value", ascending=False)
    )
    st.dataframe(
        bucket.rename(columns={"normalized_label": "Field", "normalized_peso_value": "Total (₱)"}),
        width="stretch",
        hide_index=True,
        column_config={
            "Total (₱)": st.column_config.NumberColumn("Total (₱)", format="₱%.0f"),
        },
    )
