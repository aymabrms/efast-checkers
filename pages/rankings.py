import pandas as pd
import streamlit as st

from config import RANKING_METRICS
from storage import load_demo_data
from ui_helpers import dataframe_download, format_peso


def render():
    st.header("Rankings / Research View")
    st.caption("Future-ready research screen for ranked company extraction, including Top 1000-style institutional use cases.")

    demo = load_demo_data()
    df = pd.DataFrame(demo["ranking_data"])
    metric = st.selectbox("Ranking Metric", RANKING_METRICS, index=0)
    ranked = df.sort_values(metric, ascending=False).reset_index(drop=True)
    ranked.insert(0, "Rank", ranked.index + 1)
    ranked["Display Value"] = ranked[metric].map(format_peso)

    st.metric("Highest Ranked Company", ranked.iloc[0]["company_name"], ranked.iloc[0]["Display Value"])
    st.dataframe(ranked[["Rank", "company_name", "sec_registration_no", metric, "Display Value"]], width="stretch", hide_index=True)
    st.bar_chart(ranked.set_index("company_name")[metric])
    dataframe_download(ranked, f"research_ranking_{metric.lower().replace(' ', '_')}.csv", "Export Ranking CSV")
