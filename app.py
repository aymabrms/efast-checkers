import streamlit as st

from config import AGENCY_NAME, APP_SUBTITLE, APP_TITLE
from db import init_db
import pages.dashboard as dashboard
import pages.document_review as document_review
import pages.figures_review as figures_review
import pages.historical_company as historical_company
import pages.rankings as rankings
import pages.settings_demo_data as settings_demo_data
import pages.upload_intake as upload_intake
from storage import ensure_all_demo_documents, seed_company_master

PAGES = {
    "Dashboard": dashboard.render,
    "Upload / Intake": upload_intake.render,
    "Document Review": document_review.render,
    "AFS Figures Extraction Review": figures_review.render,
    "Historical Company View": historical_company.render,
    "Rankings / Research View": rankings.render,
    "Settings / Editable Demo Data": settings_demo_data.render,
}

PAGE_NAMES = list(PAGES.keys())


def apply_styles():
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f3f7f4 0%, #f8faf8 42%, #ffffff 100%); }
        section[data-testid="stSidebar"] { background: #0d4f39; }
        section[data-testid="stSidebar"] * { color: #ffffff !important; }
        .main .block-container { padding-top: 1.5rem; max-width: 1440px; }
        .app-hero { background: linear-gradient(135deg, #0f5b3f, #083627); color: #fff; padding: 1.35rem 1.5rem; border-radius: 18px; margin-bottom: 1.25rem; box-shadow: 0 18px 40px rgba(6, 53, 37, .16); }
        .app-hero h1 { margin: 0; color: #fff; font-size: 2rem; letter-spacing: -0.02em; }
        .app-hero p { margin: .35rem 0 0; color: #d9efe5; }
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


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_styles()
    bootstrap()
    st.markdown(
        f"""
        <div class="app-hero">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE} · {AGENCY_NAME}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.title(APP_TITLE)
    st.sidebar.caption("Philippine AFS QA dashboard prototype")

    # Support programmatic navigation (e.g. "Open in Review" from Dashboard)
    nav_to = st.session_state.pop("_nav_to", None)
    default_index = PAGE_NAMES.index(nav_to) if nav_to and nav_to in PAGE_NAMES else 0
    # If we navigated programmatically, keep the radio in sync by storing the selection
    if "_current_page" not in st.session_state:
        st.session_state["_current_page"] = PAGE_NAMES[default_index]
    if nav_to:
        st.session_state["_current_page"] = nav_to

    page = st.sidebar.radio(
        "Navigation",
        PAGE_NAMES,
        index=PAGE_NAMES.index(st.session_state["_current_page"]),
        key="nav_radio",
    )
    st.session_state["_current_page"] = page

    st.sidebar.divider()
    st.sidebar.caption("Demo documents")
    st.sidebar.write("Audentia Fortuna Holdings, Inc.")
    st.sidebar.write("Malaya Northstar Manufacturing Corp.")
    st.sidebar.write("Haraya Logistics and Trade, Inc.")

    PAGES[page]()


if __name__ == "__main__":
    main()
