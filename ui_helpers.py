import html
from typing import Dict, Iterable, List

import pandas as pd
import streamlit as st


def status_badge(status: str) -> str:
    status = status or "Needs Review"
    palette = {
        "Passed": ("#d9f7e8", "#0f6b43"),
        "Warning": ("#fff4cc", "#8a5a00"),
        "Failed": ("#fde2df", "#9b1c1c"),
        "Needs Review": ("#e8eef2", "#314653"),
        "Accept": ("#d9f7e8", "#0f6b43"),
        "Revert": ("#fde2df", "#9b1c1c"),
    }
    bg, fg = palette.get(status, ("#e8eef2", "#314653"))
    return f"<span class='badge' style='background:{bg};color:{fg}'>{html.escape(status)}</span>"


def render_status(status: str) -> None:
    st.markdown(status_badge(status), unsafe_allow_html=True)


def metric_card(label: str, value, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-caption">{html.escape(str(caption))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_peso(value) -> str:
    try:
        f = float(value)
        if f != f:
            return "—"
        return "₱{:,.0f}".format(f)
    except Exception:
        return str(value)


def dataframe_download(df: pd.DataFrame, filename: str, label: str = "Export CSV") -> None:
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), filename, "text/csv")


def highlight_terms(text: str, terms: Iterable[str]) -> str:
    safe = html.escape(text or "")
    for term in terms:
        if not term:
            continue
        escaped = html.escape(str(term))
        safe = safe.replace(escaped, f"<mark>{escaped}</mark>")
    return safe


def show_document_selector(documents: List[Dict], key: str):
    if not documents:
        st.info("No documents are stored yet. Use Upload / Intake or load the demo document.")
        return None
    labels = [f"#{doc['id']} — {doc['company_name']} — {doc['period_covered_year']}" for doc in documents]
    id_by_label = {label: doc["id"] for label, doc in zip(labels, documents)}
    selected = st.selectbox("Document", labels, key=key)
    return id_by_label[selected]
