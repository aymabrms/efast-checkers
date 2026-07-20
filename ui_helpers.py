import html
from typing import Dict, Iterable, List, Optional

import pandas as pd
import streamlit as st


def status_badge(status: str) -> str:
    status = status or "Needs Review"
    colors = {
        "Passed": ("#d9f7e8", "#0f6b43"),
        "Warning": ("#fff7d9", "#856404"),
        "Failed": ("#fde8e8", "#b91c1c"),
        "Needs Review": ("#e8eef7", "#1a3a6b"),
    }
    bg, fg = colors.get(status, ("#f0f0f0", "#333"))
    return f"<span class='badge' style='background:{bg};color:{fg}'>{status}</span>"


def metric_card(label: str, value, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_peso(value) -> str:
    try:
        v = float(value)
        if abs(v) >= 1_000_000_000:
            return f"₱{v/1_000_000_000:.2f}B"
        if abs(v) >= 1_000_000:
            return f"₱{v/1_000_000:.2f}M"
        if abs(v) >= 1_000:
            return f"₱{v/1_000:.2f}K"
        return f"₱{v:,.0f}"
    except (TypeError, ValueError):
        return "₱—"


def highlight_terms(text: str, terms: List[str]) -> str:
    safe = html.escape(str(text or ""))
    for term in terms:
        if not term:
            continue
        escaped_term = html.escape(term)
        safe = safe.replace(escaped_term, f"<mark>{escaped_term}</mark>")
    return safe


def render_status(flag: str) -> None:
    flag = (flag or "").lower()
    if flag in ("ok", "good"):
        st.success("Good")
    elif flag in ("low", "poor", "bad"):
        st.error("Low Quality")
    else:
        st.warning(flag or "Unknown")


def dataframe_download(df: pd.DataFrame, filename: str, label: str = "Download CSV") -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv")


def show_document_selector(documents: List[Dict], key: str) -> Optional[int]:
    if not documents:
        st.info("No documents found. Load the demo document or upload a PDF from the Upload / Intake page.")
        return None
    id_by_label = {
        f"#{doc['id']} — {doc['company_name']} — {doc['period_covered_year']}": doc["id"]
        for doc in documents
    }
    labels = list(id_by_label.keys())
    selected = st.selectbox("Document", labels, key=key)
    return id_by_label[selected]


def reviewing_banner(document: Optional[Dict]) -> None:
    """Render a persistent 'Currently Reviewing' info card."""
    if not document:
        st.info("No document is currently selected. Use the selector below or open a document from the Dashboard.")
        return
    st.markdown(
        f"""
        <div style="background:#e8f5ee;border:1.5px solid #0f5b3f;border-radius:14px;padding:.85rem 1.2rem;margin-bottom:1rem;display:flex;gap:2.5rem;align-items:center;flex-wrap:wrap;">
            <div>
                <div style="font-size:.72rem;font-weight:700;color:#587267;text-transform:uppercase;letter-spacing:.08em;">Currently Reviewing</div>
                <div style="font-size:1.05rem;font-weight:800;color:#0f5b3f;margin-top:.15rem;">{html.escape(str(document.get('company_name','—')))}</div>
            </div>
            <div style="color:#587267;font-size:.82rem;">
                <span style="font-weight:700;color:#103f2d;">SEC Reg No.</span>&nbsp;{html.escape(str(document.get('sec_registration_no','—')))}
            </div>
            <div style="color:#587267;font-size:.82rem;">
                <span style="font-weight:700;color:#103f2d;">Period</span>&nbsp;{html.escape(str(document.get('period_covered_year','—')))}
            </div>
            <div style="color:#587267;font-size:.82rem;">
                <span style="font-weight:700;color:#103f2d;">Report Type</span>&nbsp;{html.escape(str(document.get('report_type','—')))}
            </div>
            <div style="color:#587267;font-size:.82rem;">
                <span style="font-weight:700;color:#103f2d;">Submission</span>&nbsp;{html.escape(str(document.get('submission_type','—')))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
