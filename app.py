"""Streamlit app for AI-Assisted Valuation."""
from __future__ import annotations

import json
from io import BytesIO

import pandas as pd
import streamlit as st

from ai_advisor import ai_enhance_recommendations, build_recommendations
from forecast import build_ufcf, forecast_statements
from normalize import canonicalize_long_format, map_facts_to_statements
from report import generate_report
from sec_ingest import (
    build_ticker_index,
    flatten_company_facts,
    get_company_facts_by_ticker,
    load_ticker_cik_mapping,
    search_tickers,
)
from valuation_comps import CompInput, comps_valuation
from valuation_dcf import DCFInputs, dcf_valuation, terminal_value_exit_multiple
from sensitivity import dcf_sensitivity

st.set_page_config(page_title="AI-Assisted Valuation", layout="wide")

st.title("AI-Assisted Valuation")
st.caption("Educational tool only — not investment advice.")

with st.sidebar:
    st.header("Company Profile")
    sector = st.selectbox("Sector", ["", "Technology", "Healthcare", "Industrials", "Financials", "Consumer"]) 
    business_model = st.selectbox("Business model", ["", "SaaS", "Consumer", "Industrial", "Bank/Insurance", "REIT"]) 
    size = st.selectbox("Size", ["", "Micro", "Small", "Mid", "Large", "Mega"]) 
    stage = st.selectbox("Stage", ["", "High growth", "Mature", "Cyclical", "Turnaround"]) 
    notes = st.text_area("Notes")

profile = {
    "sector": sector,
    "business_model": business_model,
    "size": size,
    "stage": stage,
    "notes": notes,
}

st.subheader("1) Data Input")
mode = st.radio("Input mode", ["Ticker Search", "Upload Excel"], horizontal=True)

historicals = pd.DataFrame()
company_summary = {}
source_trace = pd.DataFrame()

if mode == "Ticker Search":
    ticker_query = st.text_input("Search ticker", "AAPL")
    if st.button("Load SEC Data"):
        mapping = load_ticker_cik_mapping()
        index = build_ticker_index(mapping)
        matches = search_tickers(index, ticker_query)
        if not matches:
            st.error("No matching tickers found.")
        else:
            ticker = matches[0].ticker
            profile_info, facts = get_company_facts_by_ticker(ticker)
            flat = flatten_company_facts(facts)
            mapped = map_facts_to_statements(flat)
            historicals = canonicalize_long_format(mapped)
            source_trace = mapped
            company_summary = {
                "ticker": profile_info.ticker,
                "name": profile_info.title,
                "source": "SEC Company Facts",
            }
            st.success(f"Loaded {len(historicals)} rows from SEC Company Facts.")
            st.dataframe(historicals.head(20))
else:
    uploaded = st.file_uploader("Upload historicals (.xlsx)", type=["xlsx"])
    if uploaded:
        df = pd.read_excel(uploaded)
        historicals = df
        company_summary = {"ticker": "Uploaded", "name": "Custom", "source": "User Excel"}
        st.dataframe(historicals.head(20))

if not historicals.empty:
    st.subheader("2) Forecasting")
    forecast_years = st.number_input("Forecast years", min_value=3, max_value=10, value=5)
    revenue_growth = st.slider("Base revenue growth", min_value=-0.1, max_value=0.3, value=0.06, step=0.01)

    assumptions = {"revenue_growth": {"path": [revenue_growth] * int(forecast_years)}}

    if st.button("Run Forecast"):
        result = forecast_statements(historicals, list(range(2024, 2024 + int(forecast_years))), assumptions)
        combined = pd.concat([historicals, result.forecast], ignore_index=True)
        st.dataframe(result.forecast.head(20))

        st.subheader("3) AI Advisor")
        history_metrics = {"gross_margin": 0.45}
        recs = build_recommendations(profile, history_metrics)
        recs = ai_enhance_recommendations(recs)
        st.json(recs)

        st.subheader("4) Valuation")
        tax_rate = st.slider("Tax rate", min_value=0.05, max_value=0.4, value=0.21, step=0.01)
        ufcf_df = build_ufcf(result.forecast, tax_rate)
        ufcf = ufcf_df["UFCF"].tolist()
        wacc = st.slider("WACC", min_value=0.05, max_value=0.2, value=0.1, step=0.005)
        terminal_multiple = st.slider("Exit multiple", min_value=5.0, max_value=25.0, value=12.0, step=0.5)
        ebitda_terminal = ufcf[-1] * 1.3 if ufcf else 0.0
        tv = terminal_value_exit_multiple(ebitda_terminal, terminal_multiple)
        dcf_inputs = DCFInputs(
            ufcf=ufcf,
            wacc=wacc,
            terminal_method="exit_multiple",
            terminal_value=tv,
            debt=0.0,
            cash=0.0,
            shares=1.0,
        )
        dcf_result = dcf_valuation(dcf_inputs)
        st.metric("DCF Share Price", f"{dcf_result.share_price:,.2f}")

        peers = [CompInput(peer="PEER1", multiple_type="EV/EBITDA", multiple=10.0)]
        comps_result = comps_valuation(ebitda_terminal, peers)
        st.metric("Comps EV", f"{comps_result.implied_value:,.0f}")

        st.subheader("5) Sensitivity")
        grid = dcf_sensitivity(
            dcf_inputs,
            wacc_range=(wacc - 0.02, wacc + 0.02),
            terminal_range=(terminal_multiple - 2, terminal_multiple + 2),
            size=7,
            terminal_method="exit_multiple",
        )
        sens_df = pd.DataFrame(grid.grid, index=grid.x_values, columns=grid.y_values)
        st.dataframe(sens_df)

        st.subheader("6) Export Excel")
        output = BytesIO()
        statements = {
            "Income Statement": combined[combined["statement"] == "IS"],
            "Balance Sheet": combined[combined["statement"] == "BS"],
            "Cash Flow": combined[combined["statement"] == "CF"],
        }
        valuation_tables = {
            "Valuation – DCF": pd.DataFrame([dcf_result.__dict__]),
            "Valuation – Comps": pd.DataFrame([comps_result.stats]),
        }
        diagnostics = {"plugs": result.diagnostics.get("plugs", [])}
        generate_report(
            output_path="/tmp/model.xlsx",
            company_summary=company_summary,
            statements=statements,
            assumptions=recs,
            valuation_tables=valuation_tables,
            sensitivity_df=sens_df.reset_index(),
            diagnostics=diagnostics,
            source_trace=source_trace if not source_trace.empty else pd.DataFrame(),
        )
        with open("/tmp/model.xlsx", "rb") as f:
            st.download_button("Download Excel", f, file_name="valuation_model.xlsx")
