import json

import streamlit as st

from config import COMPANY_MASTER_PATH, DEMO_DATA_PATH, LABEL_MAPPING_PATH, RANKING_METRICS, REVERT_REASONS_PATH
from storage import load_company_master, load_demo_data, load_revert_reasons


def render_json(title, data):
    st.subheader(title)
    st.json(data, expanded=False)


def render():
    st.header("Demo Data & Configuration")
    st.caption("Reference guide for the demo content files that control presentation values in this prototype.")

    st.info(
        "**Reference Only — No Live Editing** — This page documents the editable demo content files used by this prototype. "
        "To change company names, SEC registration numbers, filing years, sample figures, or ranking data, "
        "edit the JSON and config files listed below directly on the server. "
        "A future version of this page will expose a live configuration editor."
    )

    st.subheader("Editable Content Files")
    st.table([
        {"File": "config.py", "What it controls": "App labels, default years, default company, ranking metric options"},
        {"File": str(DEMO_DATA_PATH.name), "What it controls": "Sample document pages, validation rows, extracted figures, historical data, rankings"},
        {"File": str(LABEL_MAPPING_PATH.name), "What it controls": "Raw AFS labels mapped to normalized internal fields"},
        {"File": str(REVERT_REASONS_PATH.name), "What it controls": "Reviewer revert reason dropdown values"},
        {"File": str(COMPANY_MASTER_PATH.name), "What it controls": "Fictional company master data record"},
    ])

    render_json("Current Company Master Record", load_company_master())
    render_json("Current Revert Reasons", load_revert_reasons())
    render_json("Current Ranking Metrics", RANKING_METRICS)
    render_json("Current Label Mapping", json.loads(LABEL_MAPPING_PATH.read_text()))

    demo = load_demo_data()
    suite = demo.get("demo_suite", [])
    afs_demo_count = sum(entry.get("metadata", {}).get("report_type") == "AFS" for entry in suite)
    gis_demo_count = sum(entry.get("metadata", {}).get("report_type") == "GIS" for entry in suite)
    st.subheader("Demo Dataset Summary")
    st.write(f"Seeded demo documents: {len(suite)} ({afs_demo_count} AFS, {gis_demo_count} GIS)")
    st.write(f"Sample pages: {len(demo['sample_pages'])}")
    st.write(f"Sample extracted figure rows: {len(demo['sample_figures'])}")
    st.write(f"Historical years: {len(demo['historical_data'])}")
    st.write(f"Ranking companies: {len(demo['ranking_data'])}")
