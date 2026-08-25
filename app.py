"""
app.py
Stock Portfolio Diversification Tracker — main Streamlit app.

Ties together:
  sample_data.py       -> demo portfolios (fallback / testing only)
  allocation.py         -> value + allocation % calculations
  risk_engine.py         -> flags, HHI, diversification score
  market_data.py         -> LIVE prices + sector via yfinance (default path)
  stock_list.py           -> friendly company name -> NSE ticker dropdown
  sheets_fetch.py         -> Google Sheets input mode
  portfolio_history.py    -> 1-month value trend chart

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from sample_data import sample_holdings, concentrated_holdings
from allocation import calculate_allocation, calculate_sector_allocation
from risk_engine import (
    generate_flags,
    add_hhi_flag,
    calculate_hhi,
    classify_hhi,
    calculate_diversification_score,
    classify_score,
)
from market_data import fetch_stock_info
from portfolio_history import portfolio_value_trend
from stock_list import STOCK_TICKERS

# NOTE: MySQL data source (mysql_fetch.py) is deliberately not wired in
# yet — prototype is running off Manual Entry / CSV / Sample Data for
# now. To re-enable: uncomment the import below and the "MySQL Database"
# block further down (also marked with the same NOTE tag).
# from mysql_fetch import list_portfolios, fetch_portfolio_from_mysql

# ---------- Page setup ----------
st.set_page_config(page_title="Portfolio Diversification Tracker", layout="wide")

COLORS = ['#6ef2ff', '#ff4fd8', '#7dffb3', '#ffd166', '#9b7cff', '#ff8fab']


def render_score_gauge(score, verdict):
    """Color-coded gauge for the Diversification Score, bands matching
    risk_engine.classify_score(): >=80 green, 50-79 amber, <50 red."""
    if score >= 80:
        bar_color = "#22c55e"
    elif score >= 50:
        bar_color = "#ffd166"
    else:
        bar_color = "#ef4444"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"color": "#f8fafc", "size": 36}},
        title={"text": verdict, "font": {"color": "#d8faff", "size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
            "bar": {"color": bar_color},
            "bgcolor": "#0f1024",
            "borderwidth": 1,
            "bordercolor": "#333f55",
            "steps": [
                {"range": [0, 50], "color": "#2a1418"},
                {"range": [50, 80], "color": "#2a2414"},
                {"range": [80, 100], "color": "#142a1e"},
            ],
        },
    ))
    fig.update_layout(
        paper_bgcolor="#0f1024",
        margin=dict(l=20, r=20, t=40, b=10),
        height=220,
    )
    return fig


# ---------- Core response builder (same as pipeline_test.py) ----------
def build_analysis_response(holdings):
    allocation_result = calculate_allocation(holdings)
    sector_result = calculate_sector_allocation(holdings)

    stock_hhi = calculate_hhi([h["allocation_percent"] for h in allocation_result["holdings"]])
    sector_hhi = calculate_hhi([s["allocation_percent"] for s in sector_result["sectors"]])

    flags = generate_flags(allocation_result["holdings"], sector_result["sectors"])
    flags = add_hhi_flag(flags, sector_hhi)

    score_result = calculate_diversification_score(flags, sector_hhi)

    return {
        "portfolio_summary": {
            "total_value": allocation_result["total_value"],
            "num_stocks": len(allocation_result["holdings"]),
            "num_sectors": len(sector_result["sectors"]),
        },
        "holdings": allocation_result["holdings"],
        "sectors": sector_result["sectors"],
        "flags": flags,
        "hhi": {
            "stock_level": {"value": stock_hhi, "label": classify_hhi(stock_hhi)},
            "sector_level": {"value": sector_hhi, "label": classify_hhi(sector_hhi)},
        },
        "diversification_score": {
            "score": score_result["score"],
            "verdict": classify_score(score_result["score"]),
            "deductions": score_result["deductions"],
        },
    }


# ---------- Sidebar: data source selection ----------
st.sidebar.title("Portfolio Input")
source = st.sidebar.radio(
    "Choose data source",
    # NOTE: "MySQL Database" is temporarily removed from this list while
    # that data source is being finished — see mysql_fetch.py and the
    # commented-out block this used to be, further up this file.
    ["Manual Entry (Live Prices)", "Upload CSV", "Google Sheets", "Sample Data (Demo)"],
)

holdings = []

# ----- Manual Entry with LIVE price/sector fetch -----
if source == "Manual Entry (Live Prices)":
    st.sidebar.write("Pick a company, enter quantity — price & sector are fetched live.")

    if "live_holdings" not in st.session_state:
        st.session_state.live_holdings = []

    with st.sidebar.form("add_stock_form", clear_on_submit=True):
        company = st.selectbox("Company", list(STOCK_TICKERS.keys()))
        quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
        submitted = st.form_submit_button("Add / Fetch Live Price")

    if submitted:
        ticker = STOCK_TICKERS[company]
        with st.spinner(f"Fetching live price for {company}..."):
            info = fetch_stock_info(ticker)

        if info.get("price") is None:
            st.sidebar.error(f"Could not fetch price for {ticker}: {info.get('error', 'unknown error')}")
        else:
            st.session_state.live_holdings.append({
                "ticker": ticker,
                "quantity": quantity,
                "price": info["price"],
                "sector": info["sector"],
            })
            st.sidebar.success(f"Added {company} @ ₹{info['price']}")

    if st.session_state.live_holdings:
        st.sidebar.write("Current holdings:")
        st.sidebar.dataframe(pd.DataFrame(st.session_state.live_holdings), use_container_width=True)
        if st.sidebar.button("Clear all holdings"):
            st.session_state.live_holdings = []

    holdings = st.session_state.live_holdings

# ----- CSV Upload -----
elif source == "Upload CSV":
    st.sidebar.caption("Columns needed: Ticker, Quantity, Price, Sector")
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file is not None:
        df = pd.read_csv(file)
        df.columns = [c.strip().lower() for c in df.columns]
        holdings = df.to_dict(orient="records")

# ----- Google Sheets -----
elif source == "Google Sheets":
    st.sidebar.caption("Sheet must have columns: Ticker, Quantity, Price, Sector")
    sheet_name = st.sidebar.text_input("Sheet name", "Portfolio_Data")
    worksheet_name = st.sidebar.text_input("Worksheet name", "Holdings")
    if st.sidebar.button("Fetch from Google Sheets"):
        try:
            from sheets_fetch import fetch_from_sheet
            st.session_state.gsheet_holdings = fetch_from_sheet(sheet_name, worksheet_name)
        except Exception as e:
            st.sidebar.error(f"Could not fetch sheet: {e}")
    holdings = st.session_state.get("gsheet_holdings", [])

# ----- Sample Data (fallback/demo only) -----
elif source == "Sample Data (Demo)":
    demo_choice = st.sidebar.selectbox(
        "Sample dataset", ["Balanced (6 holdings)", "Concentrated (risky)"]
    )
    holdings = sample_holdings if demo_choice.startswith("Balanced") else concentrated_holdings


# ---------- Main area ----------
st.title("📊 Stock Portfolio Diversification Tracker")

if not holdings:
    st.info("Add holdings from the sidebar to see your analysis.")
    st.stop()

response = build_analysis_response(holdings)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Allocation", "Risk Analysis", "Value Trend"])

# ----- Tab 1: Overview -----
with tab1:
    summary = response["portfolio_summary"]
    score = response["diversification_score"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Value", f"₹{summary['total_value']:,.0f}")
    col2.metric("Holdings", summary["num_stocks"])
    col3.metric("Sectors", summary["num_sectors"])

    chart_col, gauge_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Sector Allocation")
        sectors = response["sectors"]
        fig = go.Figure(data=[go.Pie(
            labels=[s["sector"] for s in sectors],
            values=[s["allocation_percent"] for s in sectors],
            customdata=[s["value"] for s in sectors],
            hole=0.35,
            marker=dict(colors=COLORS, line=dict(color="#0f1024", width=2)),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>₹%{customdata:,.0f}<br>%{percent}<extra></extra>",
        )])
        fig.update_layout(template="plotly_dark", paper_bgcolor="#0f1024", font=dict(color="#d8faff"))
        st.plotly_chart(fig, use_container_width=True)

    with gauge_col:
        st.subheader("Diversification Score")
        st.plotly_chart(render_score_gauge(score["score"], score["verdict"]), use_container_width=True)
        if response["flags"]:
            worst = max(response["flags"], key=lambda f: {"High": 2, "Medium": 1, "Low": 0}[f["severity"]])
            st.caption(f"Top concern: {worst['detail']}")
        else:
            st.caption("No concentration risks flagged.")

# ----- Tab 2: Allocation -----
with tab2:
    st.subheader("Stock-wise Allocation")
    holdings_df = pd.DataFrame(response["holdings"])
    st.dataframe(holdings_df, use_container_width=True)

    fig2 = px.bar(
        holdings_df, x="ticker", y="allocation_percent",
        color="ticker", color_discrete_sequence=COLORS,
        title="Stock Allocation %",
    )
    fig2.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Sector-wise Allocation")
    sectors_df = pd.DataFrame(response["sectors"])
    st.dataframe(sectors_df, use_container_width=True)

# ----- Tab 3: Risk Analysis -----
with tab3:
    st.subheader("Risk Flags")
    flags = response["flags"]
    if not flags:
        st.success("No risk flags triggered — portfolio looks well diversified.")
    for f in flags:
        if f["severity"] == "High":
            st.error(f"🚨 **{f['flag_type']}** — {f['detail']}")
        elif f["severity"] == "Medium":
            st.warning(f"⚠️ **{f['flag_type']}** — {f['detail']}")
        else:
            st.info(f"ℹ️ **{f['flag_type']}** — {f['detail']}")

    st.subheader("Concentration (HHI)")
    hhi = response["hhi"]
    col1, col2 = st.columns(2)
    col1.metric("Stock-level HHI", hhi["stock_level"]["value"], hhi["stock_level"]["label"])
    col2.metric("Sector-level HHI", hhi["sector_level"]["value"], hhi["sector_level"]["label"])

    st.subheader("Diversification Score Breakdown")
    st.metric("Score", f"{score['score']}/100", score["verdict"])
    for d in score["deductions"]:
        st.write(f"{d['points']:+d} — {d['reason']}")

# ----- Tab 4: Value Trend -----
with tab4:
    st.subheader("Portfolio Value Trend (Last 1 Month)")
    st.caption("Assumes quantities stayed constant over the period. Requires internet + valid NSE tickers.")
    try:
        trend_holdings = [
            {"ticker": h["ticker"], "quantity": h["quantity"]}
            for h in holdings if h.get("ticker") and h.get("quantity")
        ]
        with st.spinner("Fetching historical prices..."):
            trend = portfolio_value_trend(trend_holdings)
        if trend:
            trend_df = pd.DataFrame(trend)
            fig3 = px.line(trend_df, x="date", y="value", title="Portfolio Value Over Time")
            fig3.update_layout(template="plotly_dark")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No trend data returned — check tickers are valid NSE symbols.")
    except Exception as e:
        st.warning(f"Could not fetch value trend right now. ({e})")