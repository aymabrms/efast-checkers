import streamlit as st

from config import APP_SUBTITLE, APP_TITLE
from db import init_db
import pages.dashboard as dashboard
import pages.document_review as document_review
import pages.figures_review as figures_review
import pages.historical_company as historical_company
import pages.rankings as rankings
import pages.settings_demo_data as settings_demo_data
import pages.upload_intake as upload_intake
from storage import ensure_all_demo_documents, get_documents, is_demo_document, seed_company_master

PAGES = {
    "Dashboard": dashboard.render,
    "Upload / Intake": upload_intake.render,
    "Document Review": document_review.render,
    "AFS Figures Extraction Review": figures_review.render,
    "Historical Company View": historical_company.render,
    "Rankings / Research View": rankings.render,
    "Demo Data & Configuration": settings_demo_data.render,
}

AFS_NAV = [
    ("Upload / Intake", "Upload / Intake"),
    ("Document Review", "Document Review"),
    ("Figures Extraction Review", "AFS Figures Extraction Review"),
    ("Historical Company View", "Historical Company View"),
]
GIS_NAV = [
    ("Upload / Intake", "Upload / Intake"),
    ("Document Review", "Document Review"),
]


def apply_styles():
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f3f7f4 0%, #f8faf8 42%, #ffffff 100%); }
        section[data-testid="stSidebar"] { background: #0d4f39; }
        section[data-testid="stSidebar"] * { color: #ffffff !important; }
        section[data-testid="stSidebar"] .stButton button {
            background: rgba(255, 255, 255, .08);
            border-color: rgba(255, 255, 255, .24);
            justify-content: flex-start;
        }
        section[data-testid="stSidebar"] .stButton button:disabled {
            background: #ffffff;
            border-color: #ffffff;
            opacity: 1;
        }
        section[data-testid="stSidebar"] .stButton button:disabled,
        section[data-testid="stSidebar"] .stButton button:disabled * {
            color: #0d4f39 !important;
        }
        [data-testid="stSidebarNav"] { display: none !important; }
        .main .block-container { padding-top: 1.5rem; max-width: 1440px; }
        .metric-card { background: #fff; border: 1px solid #dfe9e3; border-radius: 16px; padding: 1rem; min-height: 122px; box-shadow: 0 10px 24px rgba(19, 42, 31, .07); }
        .metric-label { color: #587267; font-size: .76rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; }
        .metric-value { color: #103f2d; font-size: 1.55rem; font-weight: 800; margin-top: .3rem; line-height: 1.15; }
        .metric-caption { color: #71867d; font-size: .82rem; margin-top: .4rem; }
        .badge { display: inline-block; border-radius: 999px; font-size: .78rem; font-weight: 700; padding: .22rem .62rem; margin: .1rem .2rem .1rem 0; }
        .text-preview { background: #ffffff; border: 1px solid #dfe9e3; border-left: 4px solid #0f5b3f; border-radius: 12px; padding: 1rem; line-height: 1.65; color: #17231f; }
        mark { background: #dff6cb; color: #103f2d; padding: .08rem .2rem; border-radius: 4px; }
        div[data-testid="stDataFrame"] { border: 1px solid #dfe9e3; border-radius: 14px; overflow: hidden; }
        .stButton button { border-radius: 999px; font-weight: 700; }
        h1, h2, h3 { color: #103f2d; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def bootstrap():
    init_db()
    seed_company_master()
    if "active_document_id" not in st.session_state:
        st.session_state["active_document_id"] = ensure_all_demo_documents()


def _navigate(page: str, context: str = None) -> None:
    st.session_state["_current_page"] = page
    if context:
        st.session_state["review_context"] = context
        if page == "Upload / Intake":
            st.session_state["intake_report_type"] = context
    st.rerun()


def _sidebar_nav_button(label: str, page: str, context: str = None) -> None:
    active = (
        st.session_state.get("_current_page") == page
        and (context is None or st.session_state.get("review_context") == context)
    )
    if st.sidebar.button(
        label,
        key=f"nav_{context or 'main'}_{page}",
        type="primary" if active else "secondary",
        use_container_width=True,
        disabled=active,
    ):
        _navigate(page, context)


def _render_sidebar_navigation() -> None:
    st.sidebar.markdown("**MAIN**")
    _sidebar_nav_button("Dashboard", "Dashboard")

    st.sidebar.markdown("**AFS REPORTS**")
    for label, page in AFS_NAV:
        _sidebar_nav_button(label, page, "AFS")

    st.sidebar.markdown("**GIS REPORTS**")
    for label, page in GIS_NAV:
        _sidebar_nav_button(label, page, "GIS")

    st.sidebar.markdown("**RESEARCH**")
    _sidebar_nav_button("Rankings / Research View", "Rankings / Research View")

    st.sidebar.markdown("**PROTOTYPE ADMIN**")
    _sidebar_nav_button("Demo Data & Configuration", "Demo Data & Configuration")


def _render_demo_documents() -> None:
    st.sidebar.divider()
    st.sidebar.markdown("**DEMO DOCUMENTS**")
    demo_documents = [document for document in get_documents() if is_demo_document(document)]
    afs_documents = [document for document in demo_documents if document.get("report_type") == "AFS"]
    gis_documents = [document for document in demo_documents if document.get("report_type") == "GIS"]
    if afs_documents:
        st.sidebar.caption("AFS")
        for document in afs_documents:
            st.sidebar.write(
                f"• {document['company_name']} — {document['period_covered_year']}"
            )
    if gis_documents:
        st.sidebar.caption("GIS")
        for document in gis_documents:
            corporation_type = document.get("corporation_type") or "GIS"
            st.sidebar.write(
                f"• {document['company_name']} — {document['period_covered_year']} {corporation_type} GIS"
            )


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_styles()
    bootstrap()
    st.sidebar.title(APP_TITLE)
    st.sidebar.caption(APP_SUBTITLE)

    if "_current_page" not in st.session_state:
        st.session_state["_current_page"] = "Dashboard"
    if "review_context" not in st.session_state:
        st.session_state["review_context"] = "AFS"

    _render_sidebar_navigation()
    _render_demo_documents()

    PAGES[st.session_state["_current_page"]]()


if __name__ == "__main__":
    main()
