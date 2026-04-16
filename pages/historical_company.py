import pandas as pd
import streamlit as st

from storage import load_company_master, load_demo_data
from ui_helpers import dataframe_download, format_peso


def render():
    st.header("Historical Company View")
    st.caption("One-company historical financial data view showing long-term value from structured AFS extraction.")

    master = load_company_master()
    demo = load_demo_data()
    df = pd.DataFrame(demo["historical_data"])

    st.subheader(master["company_name"])
    c1, c2, c3 = st.columns(3)
    c1.metric("SEC Registration No.", master["sec_registration_no"])
    c2.metric("Coverage", f"{df['year'].min()}–{df['year'].max()}")
    c3.metric("Latest Total Assets", format_peso(df.iloc[-1]["Total Assets"]))

    st.dataframe(df, width="stretch", hide_index=True)
    dataframe_download(df, "audentia_fortuna_historical_figures.csv", "Export Historical CSV")

    st.subheader("Trend Charts")
    chart_df = df.set_index("year")
    st.line_chart(chart_df[["Gross Revenue", "Total Assets", "Net Income"]])
