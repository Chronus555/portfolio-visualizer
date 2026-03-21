"""Portfolio Backtest — compare up to 5 portfolios with full analytics."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data import fetch_prices
from utils.ui_helpers import (
    inject_css, COLORS, get_plotly_layout, PORTFOLIO_TEMPLATES,
    metric_with_tooltip, download_dataframe, sidebar_etf_reference,
)
from utils.metrics import (
    compute_portfolio_returns, compute_growth, compute_all_metrics,
    drawdown_series, annual_returns, monthly_returns_table, rolling_returns,
    cagr, annual_volatility, sharpe_ratio, max_drawdown,
)

st.set_page_config(page_title="Portfolio Backtest", page_icon="📊", layout="wide")
inject_css()
st.title("📊 Portfolio Backtest")
st.caption("Compare up to 5 portfolios with historical performance analytics, risk metrics, and detailed return breakdowns.")

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    n_portfolios = st.slider("Number of portfolios", 1, 5, 2,
                              help="Compare up to 5 different allocations side by side.")

    st.markdown("**Date Range**")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", value=pd.Timestamp("2007-01-01"))
    end_date = col2.date_input("End", value=pd.Timestamp.today())

    initial_investment = st.number_input("Initial investment ($)", value=10000, min_value=100, step=1000)

    with st.expander("Advanced Options", expanded=False):
        rebalance = st.selectbox("Rebalancing frequency",
                                  ["monthly", "quarterly", "annually", "daily", "none"],
                                  help="How often to reset portfolio weights to target allocation.")
        benchmark_ticker = st.text_input("Benchmark ticker", value="SPY",
                                          help="Compare portfolios against this benchmark.")
        log_scale = st.checkbox("Logarithmic scale", value=False,
                                 help="Use log scale for growth chart — better for long time periods.")
        show_inflation = st.checkbox("Inflation-adjusted returns", value=False,
                                      help="Adjust returns for CPI inflation (approx 2.5%/yr).")
        inflation_rate = 0.025
        if show_inflation:
            inflation_rate = st.number_input("Annual inflation rate (%)", value=2.5, min_value=0.0,
                                              max_value=20.0, step=0.1) / 100
        annual_contribution = st.number_input("Annual contribution ($)", value=0, min_value=0, step=1000,
                                               help="Amount added at the start of each year.")

    sidebar_etf_reference()

# ── Portfolio Definition ────────────────────────────────────────────────────
portfolios = []
all_tickers = set()

for i in range(n_portfolios):
    with st.expander(f"Portfolio {i + 1}", expanded=(i < 2)):
        pcol1, pcol2 = st.columns([1, 3])
        with pcol1:
            name = st.text_input("Name", value=f"Portfolio {i + 1}", key=f"name_{i}")
            template = st.selectbox(
                "Template",
                list(PORTFOLIO_TEMPLATES.keys()),
                key=f"template_{i}",
                help="Pick a preset or choose Custom.",
            )
        with pcol2:
            tmpl = PORTFOLIO_TEMPLATES[template]
            default_t = ", ".join(tmpl.keys()) if tmpl else ("SPY, AGG" if i == 0 else "QQQ, AGG")
            default_w = ", ".join(str(v) for v in tmpl.values()) if tmpl else "60, 40"

            tickers_str = st.text_input("Tickers (comma-separated)", value=default_t, key=f"tickers_{i}")
            tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]

            weights_str = st.text_input("Weights (sum to 100)", value=default_w, key=f"weights_{i}")
            try:
                weights = [float(w.strip()) / 100 for w in weights_str.split(",") if w.strip()]
            except ValueError:
                st.error("Weights must be numbers.")
                weights = []

        if len(tickers) != len(weights):
            st.warning(f"Ticker count ({len(tickers)}) ≠ weight count ({len(weights)})")
        elif weights and abs(sum(weights) - 1.0) > 0.011:
            st.warning(f"Weights sum to {sum(weights)*100:.1f}% — should be 100%")
        elif tickers and weights:
            portfolios.append({"name": name, "tickers": tickers, "weights": dict(zip(tickers, weights))})
            all_tickers.update(tickers)

if benchmark_ticker:
    all_tickers.add(benchmark_ticker.strip().upper())

# ── Run Backtest ────────────────────────────────────────────────────────────
if st.button("🚀 Run Backtest", type="primary", use_container_width=True) and portfolios:
    with st.spinner("Fetching price data from Yahoo Finance..."):
        prices = fetch_prices(list(all_tickers), str(start_date), str(end_date))

    if prices.empty:
        st.error("Could not fetch data. Check tickers and date range.")
        st.stop()

    missing = all_tickers - set(prices.columns)
    if missing:
        st.warning(f"Missing data for: {', '.join(missing)}. Excluded from analysis.")

    # Compute returns
    port_results = []
    for p in portfolios:
        available = {t: w for t, w in p["weights"].items() if t in prices.columns}
        if not available:
            st.error(f"No valid tickers for {p['name']}")
            continue
        total_w = sum(available.values())
        available = {t: w / total_w for t, w in available.items()}
        ret = compute_portfolio_returns(prices, available, rebalance)

        if show_inflation:
            daily_inf = (1 + inflation_rate) ** (1/252) - 1
            ret = ret - daily_inf

        port_results.append({"name": p["name"], "returns": ret, "weights": available})

    benchmark_returns = None
    if benchmark_ticker and benchmark_ticker.upper() in prices.columns:
        benchmark_returns = prices[benchmark_ticker.upper()].pct_change().dropna()
        if show_inflation:
            daily_inf = (1 + inflation_rate) ** (1/252) - 1
            benchmark_returns = benchmark_returns - daily_inf

    if not port_results:
        st.stop()

    # Pre-compute growth and drawdowns once so tabs can reuse them
    for p in port_results:
        p["growth"] = compute_growth(p["returns"], initial_investment)
        p["drawdown"] = drawdown_series(p["returns"])

    # ── Summary Metrics (top cards) ─────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    for p in port_results:
        st.markdown(f"**{p['name']}**")
        cols = st.columns(6)
        r = p["returns"]
        with cols[0]: metric_with_tooltip("CAGR", f"{cagr(r):.2%}", "CAGR")
        with cols[1]: metric_with_tooltip("Volatility", f"{annual_volatility(r):.2%}", "Annual Volatility")
        with cols[2]: metric_with_tooltip("Sharpe", f"{sharpe_ratio(r):.2f}", "Sharpe Ratio")
        with cols[3]: metric_with_tooltip("Max DD", f"{max_drawdown(r):.2%}", "Max Drawdown")
        with cols[4]:
            growth_val = p["growth"]
            final_val = growth_val.iloc[-1] if len(growth_val) > 0 else initial_investment
            metric_with_tooltip("Final Value", f"${final_val:,.0f}")
        with cols[5]:
            total_ret = (1 + r).prod() - 1
            metric_with_tooltip("Total Return", f"{total_ret:.2%}")

    # ── Tabs for different views ────────────────────────────────────────────
    tab_growth, tab_metrics, tab_drawdown, tab_annual, tab_rolling, tab_monthly, tab_alloc = st.tabs([
        "Growth", "Metrics Table", "Drawdowns", "Annual Returns", "Rolling Returns", "Monthly Heatmap", "Allocation"
    ])

    # ── Growth Chart ────────────────────────────────────────────────────────
    with tab_growth:
        fig = go.Figure()
        growth_data = {}
        for idx, p in enumerate(port_results):
            growth = p["growth"]

            # Add annual contributions (only when we have a real DatetimeIndex)
            if annual_contribution > 0 and isinstance(growth.index, pd.DatetimeIndex) and len(growth) > 0:
                growth_adj = growth.copy()
                years_seen = set()
                for date in growth_adj.index:
                    yr = date.year
                    if yr not in years_seen and date != growth_adj.index[0]:
                        years_seen.add(yr)
                        growth_adj.loc[date:] += annual_contribution * (growth_adj.loc[date:] / growth_adj.loc[date])
                growth = growth_adj

            growth_data[p["name"]] = growth
            fig.add_trace(go.Scatter(
                x=growth.index, y=growth.values,
                name=p["name"], line=dict(color=COLORS[idx % len(COLORS)], width=2.5),
            ))
        if benchmark_returns is not None:
            bm_growth = compute_growth(benchmark_returns, initial_investment)
            growth_data[benchmark_ticker.upper()] = bm_growth
            fig.add_trace(go.Scatter(
                x=bm_growth.index, y=bm_growth.values,
                name=benchmark_ticker.upper(), line=dict(color="#64748b", width=1.5, dash="dash"),
            ))
        layout = get_plotly_layout(height=550)
        layout["yaxis"]["tickformat"] = "$,.0f"
        if log_scale:
            layout["yaxis"]["type"] = "log"
        layout["xaxis_title"] = "Date"
        layout["yaxis_title"] = "Portfolio Value ($)" + (" (inflation-adjusted)" if show_inflation else "")
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

        download_dataframe(pd.DataFrame(growth_data), "portfolio_growth.csv", "📥 Download growth data")

    # ── Metrics Table ───────────────────────────────────────────────────────
    with tab_metrics:
        metrics_data = {}
        for p in port_results:
            m = compute_all_metrics(p["returns"], benchmark_returns)
            metrics_data[p["name"]] = m
        if benchmark_returns is not None:
            m_bm = compute_all_metrics(benchmark_returns)
            metrics_data[benchmark_ticker.upper()] = m_bm

        metrics_df = pd.DataFrame(metrics_data)
        format_pct = {"CAGR", "Annual Volatility", "Max Drawdown", "Best Year", "Worst Year", "VaR (5%)", "CVaR (5%)", "Alpha"}
        display_df = metrics_df.copy()
        for col in display_df.columns:
            for row in display_df.index:
                val = display_df.loc[row, col]
                if row in format_pct:
                    display_df.loc[row, col] = f"{val:.2%}"
                else:
                    display_df.loc[row, col] = f"{val:.3f}"

        st.dataframe(display_df, use_container_width=True, height=520)
        download_dataframe(metrics_df, "portfolio_metrics.csv", "📥 Download metrics")

        # Tooltips below
        with st.expander("Metric Definitions"):
            from utils.ui_helpers import METRIC_TOOLTIPS
            for k, v in METRIC_TOOLTIPS.items():
                if k in metrics_df.index:
                    st.markdown(f"**{k}:** {v}")

    # ── Drawdown Chart ──────────────────────────────────────────────────────
    with tab_drawdown:
        fig_dd = go.Figure()
        dd_data = {}
        for idx, p in enumerate(port_results):
            dd = p["drawdown"]
            dd_data[p["name"]] = dd
            fig_dd.add_trace(go.Scatter(
                x=dd.index, y=dd.values,
                name=p["name"], fill="tozeroy",
                line=dict(color=COLORS[idx % len(COLORS)], width=1),
            ))
        layout_dd = get_plotly_layout(height=450)
        layout_dd["yaxis"]["tickformat"] = ".1%"
        layout_dd["yaxis_title"] = "Drawdown"
        fig_dd.update_layout(**layout_dd)
        st.plotly_chart(fig_dd, use_container_width=True)

        # Underwater period table
        for p in port_results:
            dd = p["drawdown"]
            if len(dd) > 0:
                min_dd_date = dd.idxmin()
                st.caption(f"**{p['name']}** worst drawdown: **{dd.min():.2%}** on {min_dd_date.strftime('%Y-%m-%d')}")

    # ── Annual Returns ──────────────────────────────────────────────────────
    with tab_annual:
        chart_type = st.radio("View", ["Bar Chart", "Table"], horizontal=True, key="annual_view")

        yr_data = {}
        for p in port_results:
            yr_data[p["name"]] = annual_returns(p["returns"])
        if benchmark_returns is not None:
            yr_data[benchmark_ticker.upper()] = annual_returns(benchmark_returns)

        if chart_type == "Bar Chart":
            fig_yr = go.Figure()
            for idx, (name, yr) in enumerate(yr_data.items()):
                color = COLORS[idx % len(COLORS)] if idx < len(port_results) else "#64748b"
                fig_yr.add_trace(go.Bar(x=yr.index.astype(str), y=yr.values, name=name, marker_color=color))
            layout_yr = get_plotly_layout(height=450)
            layout_yr["barmode"] = "group"
            layout_yr["yaxis"]["tickformat"] = ".1%"
            layout_yr["yaxis_title"] = "Annual Return"
            fig_yr.update_layout(**layout_yr)
            st.plotly_chart(fig_yr, use_container_width=True)
        else:
            yr_df = pd.DataFrame(yr_data)
            styled = yr_df.style.format("{:.2%}").background_gradient(cmap="RdYlGn", vmin=-0.3, vmax=0.3)
            st.dataframe(styled, use_container_width=True)

        download_dataframe(pd.DataFrame(yr_data), "annual_returns.csv", "📥 Download annual returns")

    # ── Rolling Returns ─────────────────────────────────────────────────────
    with tab_rolling:
        roll_window = st.select_slider("Rolling window",
                                        options=[63, 126, 252, 504, 756],
                                        value=252,
                                        format_func=lambda x: {63: "3 months", 126: "6 months", 252: "1 year", 504: "2 years", 756: "3 years"}[x],
                                        key="roll_window")
        fig_roll = go.Figure()
        for idx, p in enumerate(port_results):
            roll = rolling_returns(p["returns"], roll_window)
            fig_roll.add_trace(go.Scatter(
                x=roll.index, y=roll.values,
                name=p["name"], line=dict(color=COLORS[idx % len(COLORS)], width=1.5),
            ))
        fig_roll.add_hline(y=0, line_color="#475569", line_dash="dash", opacity=0.5)
        layout_roll = get_plotly_layout(height=450)
        layout_roll["yaxis"]["tickformat"] = ".1%"
        layout_roll["yaxis_title"] = f"Rolling {roll_window}-Day Return (Ann.)"
        fig_roll.update_layout(**layout_roll)
        st.plotly_chart(fig_roll, use_container_width=True)

    # ── Monthly Heatmap ─────────────────────────────────────────────────────
    with tab_monthly:
        selected_port = st.selectbox("Portfolio", [p["name"] for p in port_results], key="monthly_port")
        for p in port_results:
            if p["name"] == selected_port:
                mt = monthly_returns_table(p["returns"])
                # Add YTD column
                mt["YTD"] = (1 + mt.fillna(0)).prod(axis=1) - 1
                styled = mt.style.format("{:.1%}", na_rep="—").background_gradient(cmap="RdYlGn", vmin=-0.08, vmax=0.08)
                st.dataframe(styled, use_container_width=True, height=600)
                download_dataframe(mt, f"monthly_returns_{selected_port}.csv", "📥 Download monthly returns")
                break

    # ── Allocation ──────────────────────────────────────────────────────────
    with tab_alloc:
        alloc_cols = st.columns(min(len(port_results), 3))
        for idx, p in enumerate(port_results):
            with alloc_cols[idx % 3]:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(p["weights"].keys()),
                    values=[v * 100 for v in p["weights"].values()],
                    hole=0.4,
                    marker=dict(colors=COLORS),
                    textinfo="label+percent",
                    textposition="inside",
                )])
                fig_pie.update_layout(
                    title=dict(text=p["name"], font=dict(size=14)),
                    height=350, showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                st.plotly_chart(fig_pie, use_container_width=True)
