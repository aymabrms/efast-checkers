import pandas as pd
import streamlit as st

from db import save_reviewer_action
from storage import get_document, get_documents, get_pages, get_reviewer_actions, get_validations, load_revert_reasons
from ui_helpers import highlight_terms, render_status, reviewing_banner, show_document_selector, status_badge
from validation_engine import final_recommendation, suggested_revert_reason


def render():
    st.header("Document Review")
    st.caption("Reviewer view for page classification, text evidence, period checks, suggested revert reasons, and final recommendation.")

    documents = get_documents()

    # Resolve active document — prefer session state, fall back to selector
    active_id = st.session_state.get("active_document_id")
    if not active_id:
        active_id = show_document_selector(documents, "doc_review_selector")
        if not active_id:
            return
        st.session_state["active_document_id"] = active_id
    else:
        # Show a compact inline switcher so the reviewer can change documents without losing context
        with st.expander("Switch document", expanded=False):
            switched_id = show_document_selector(documents, "doc_review_switcher")
            if switched_id and switched_id != active_id:
                if st.button("Load selected document", key="doc_review_switch_btn"):
                    st.session_state["active_document_id"] = switched_id
                    st.rerun()

    document_id = st.session_state["active_document_id"]
    document = get_document(document_id)

    if not document:
        st.warning("Selected document was not found. Please choose another from the selector below.")
        st.session_state.pop("active_document_id", None)
        return

    # ── Persistent "Currently Reviewing" banner ──────────────────────────────
    reviewing_banner(document)

    pages = get_pages(document_id)
    validations = get_validations(document_id)

    # ── Validation Results ────────────────────────────────────────────────────
    st.subheader("Validation Results")
    if validations:
        df = pd.DataFrame(validations)
        df["status_badge"] = df["status"].map(status_badge)
        st.dataframe(df[["rule_name", "status", "message", "suggested_revert_reason"]], width="stretch", hide_index=True)
    else:
        st.info("No validation rows are available yet.")

    # ── Page Review ───────────────────────────────────────────────────────────
    st.subheader("Page Review")
    if not pages:
        st.info("No page analysis data is available for this document.")
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

    # ── Reviewer Disposition ──────────────────────────────────────────────────
    recommendation = final_recommendation(validations)
    suggested = suggested_revert_reason(validations)
    reasons = load_revert_reasons()

    st.subheader("Reviewer Disposition")
    with st.form("reviewer_disposition"):
        col1, col2 = st.columns(2)
        with col1:
            final = st.selectbox(
                "Final Recommendation",
                ["Accept", "Revert", "Needs Review"],
                index=["Accept", "Revert", "Needs Review"].index(recommendation),
            )
        with col2:
            reason_options = [""] + reasons
            reason_index = reason_options.index(suggested) if suggested in reason_options else 0
            revert_reason = st.selectbox("Suggested Revert Reason", reason_options, index=reason_index)
        remarks = st.text_area("Reviewer Remarks", placeholder="Add reviewer notes, issue details, or basis for override.")
        saved = st.form_submit_button("Save Reviewer Recommendation", type="primary")
    if saved:
        save_reviewer_action(document_id, remarks, final, revert_reason)
        st.success("Reviewer recommendation saved.")

    # ── Reviewer Action History ───────────────────────────────────────────────
    st.subheader("Reviewer Action History")
    actions = get_reviewer_actions(document_id)
    if not actions:
        st.info("No reviewer actions have been saved for this document yet.")
    else:
        for action in actions:
            rec = action.get("final_recommendation") or "—"
            revert = action.get("revert_reason") or ""
            notes = action.get("remarks") or ""
            ts = action.get("updated_at") or action.get("created_at") or "—"
            rec_colors = {
                "Accept": ("#d9f7e8", "#0f6b43"),
                "Revert": ("#fde8e8", "#b91c1c"),
                "Needs Review": ("#e8eef7", "#1a3a6b"),
            }
            bg, fg = rec_colors.get(rec, ("#f5f5f5", "#333"))
            revert_row = f"<div style='margin-top:.35rem;color:#587267;font-size:.82rem;'><span style='font-weight:700;color:#103f2d;'>Revert reason:</span> {rec if revert else '—'} {revert}</div>" if revert else ""
            notes_row = f"<div style='margin-top:.25rem;color:#444;font-size:.84rem;font-style:italic;'>&ldquo;{notes}&rdquo;</div>" if notes else ""
            st.markdown(
                f"""
                <div style="background:#fff;border:1px solid #dfe9e3;border-left:4px solid {fg};border-radius:12px;padding:.75rem 1rem;margin-bottom:.6rem;">
                    <div style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap;">
                        <span style="background:{bg};color:{fg};border-radius:999px;font-size:.78rem;font-weight:700;padding:.2rem .6rem;">{rec}</span>
                        <span style="color:#aaa;font-size:.78rem;">{ts}</span>
                    </div>
                    {revert_row}
                    {notes_row}
                </div>
                """,
                unsafe_allow_html=True,
            )
