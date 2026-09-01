import math

import pandas as pd
import streamlit as st

from db import update_figure_reviews
from extraction_engine import fiscal_year_candidates
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


def _current_revenue_value(df: pd.DataFrame, current_year):
    if current_year is None:
        return None
    current_revenue = df[
        (df["fiscal_year"] == current_year)
        & (df["normalized_label"].isin(REVENUE_LABELS))
    ]["normalized_peso_value"].dropna()
    current_revenue = current_revenue[
        current_revenue.apply(lambda value: not math.isnan(float(value)) if value is not None else False)
    ]
    return current_revenue.max() if not current_revenue.empty else None


def _normalized_figure_buckets(df: pd.DataFrame, current_year) -> pd.DataFrame:
    bucket_source = df.dropna(subset=["normalized_peso_value"]).copy()
    if bucket_source.empty:
        return pd.DataFrame(columns=["Field", "Fiscal Year", "Year Role", "Total (₱)"])
    bucket_source["Fiscal Year"] = bucket_source["fiscal_year"].astype(int)
    bucket_source["Year Role"] = bucket_source["Fiscal Year"].apply(
        lambda year: "Current" if current_year is not None and year == current_year else "Comparative"
    )
    bucket = (
        bucket_source.groupby(["normalized_label", "Fiscal Year", "Year Role"], as_index=False)["normalized_peso_value"]
        .sum()
        .sort_values("normalized_peso_value", ascending=False)
    )
    return bucket.rename(columns={"normalized_label": "Field", "normalized_peso_value": "Total (₱)"})


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

    current_year = int(document["period_covered_year"]) if document.get("period_covered_year") else None
    reporting_years = fiscal_year_candidates(document)
    reporting_years_display = " · ".join(str(year) for year in reporting_years) if reporting_years else "—"
    st.markdown(f"**Reporting Years:** {reporting_years_display}")
    if reporting_years:
        st.caption(
            " · ".join(
                f"{year} = {'Current' if year == current_year else 'Comparative'}"
                for year in reporting_years
            )
        )

    figures = get_figures(document_id)
    if not figures:
        st.warning("No supported financial figures were reliably extracted from this document.")
        return

    df = pd.DataFrame(figures)
    check_source_count = int((df["review_status"] == "Check Source").sum())
    if check_source_count:
        st.warning(
            f"{check_source_count} figure row(s) have **Check Source** status. "
            "Ambiguous numeric formatting detected. Original raw values are retained and normalized peso values "
            "remain blank until the reviewer verifies the source."
        )

    available_years = sorted(df["fiscal_year"].dropna().astype(int).unique(), reverse=True)
    year_options = ["All Years"] + [
        f"{year} — {'Current' if year == current_year else 'Comparative'}"
        for year in available_years
    ]
    selected_year = st.selectbox(
        "View Fiscal Year",
        year_options,
        key=f"figures_year_filter_{document_id}",
    )
    selected_year_value = None if selected_year == "All Years" else int(selected_year.split(" ", 1)[0])
    view_df = df if selected_year_value is None else df[df["fiscal_year"] == selected_year_value].copy()

    # Current Revenue is intentionally limited to the document's Period Covered Year.
    current_revenue = _current_revenue_value(df, current_year)
    rev_display = format_peso(current_revenue) if current_revenue is not None else "No detected revenue"

    fiscal_years_display = " · ".join(str(year) for year in reporting_years) if reporting_years else "—"

    needs_review_count = int(df["review_status"].isin(["Needs Review", "Check Source"]).sum())

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
    editable = view_df[review_cols].copy()
    editable["reviewed_value"] = editable["reviewed_value"].fillna("")
    editable["year_role"] = editable["fiscal_year"].apply(
        lambda year: "Current" if current_year is not None and int(year) == current_year else "Comparative"
    )

    # Add human-readable confidence display column
    editable["conf_display"] = editable["confidence"].apply(_safe_conf_display)

    # Sort: Needs Review first, then by page_number
    sort_key = editable["review_status"].apply(lambda s: 0 if s in ("Needs Review", "Check Source") else 1)
    editable = editable.assign(_sort=sort_key).sort_values(["_sort", "page_number"]).drop(columns=["_sort"])

    # Columns shown to reviewer (conf_display replaces raw confidence)
    display_cols = [
        "id", "page_number", "statement_type", "raw_label", "normalized_label",
        "fiscal_year", "year_role", "displayed_value", "normalized_peso_value", "unit_basis",
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
            "year_role": st.column_config.TextColumn("Year Role", disabled=True, width="small"),
            "displayed_value": st.column_config.TextColumn("Displayed Value", disabled=True),
            "normalized_peso_value": st.column_config.NumberColumn(
                "Normalized (₱)", disabled=True, format="₱%.0f"
            ),
            "unit_basis": st.column_config.TextColumn("Unit Basis", disabled=True, width="small"),
            "source_snippet": st.column_config.TextColumn("Source Snippet", disabled=True),
            "conf_display": st.column_config.TextColumn("Confidence (Est.)", disabled=True, width="medium"),
            "review_status": st.column_config.SelectboxColumn(
                "Status", options=["Needs Review", "Check Source", "Reviewed", "Corrected", "Rejected"]
            ),
            "reviewer_edited": st.column_config.CheckboxColumn("Edited?", disabled=True, width="small"),
            "reviewed_value": st.column_config.TextColumn("Reviewed / Corrected Value"),
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
    bucket = _normalized_figure_buckets(view_df, current_year)
    if bucket.empty:
        st.info("No safely normalized peso values are available for aggregation yet.")
    else:
        st.dataframe(
            bucket,
            width="stretch",
            hide_index=True,
            column_config={
                "Fiscal Year": st.column_config.NumberColumn("Fiscal Year", format="%d"),
                "Total (₱)": st.column_config.NumberColumn("Total (₱)", format="₱%.0f"),
            },
        )
