"""Monte Carlo Simulation — project future portfolio outcomes with contributions, withdrawals, and inflation."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data import fetch_prices
from utils.ui_helpers import (
    inject_css, COLORS, get_plotly_layout, sidebar_portfolio_input,
    sidebar_etf_reference, metric_with_tooltip, download_dataframe,
)
from utils.metrics import (
    compute_portfolio_returns, cagr, annual_volatility, max_drawdown,
)

st.set_page_config(page_title="Monte Carlo Simulation", page_icon="🎲", layout="wide")
inject_css()
st.title("🎲 Monte Carlo Simulation")
st.caption("Project future portfolio outcomes using bootstrap resampling with contributions, withdrawals, and inflation adjustment.")

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📦 Portfolio")
    tickers, weights, valid = sidebar_portfolio_input("mc", "SPY, AGG", "60, 40")

    st.header("📅 Historical Period")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", value=pd.Timestamp("2005-01-01"))
    end_date = col2.date_input("End", value=pd.Timestamp.today())

    st.header("🎯 Simulation Settings")
    n_years = st.slider("Projection years", 1, 50, 10)
    n_sims = st.select_slider("Simulations", options=[200, 500, 1000, 2500, 5000, 10000], value=1000)
    initial_investment = st.number_input("Initial investment ($)", value=10000, min_value=100, step=1000)

    with st.expander("💰 Contributions & Withdrawals"):
        cashflow_type = st.radio("Cash flow type", ["None", "Contributions", "Withdrawals"], horizontal=True)
        annual_cashflow = 0
        if cashflow_type == "Contributions":
            annual_cashflow = st.number_input("Annual contribution ($)", value=6000, min_value=0, step=1000,
                                               help="Added monthly (divided by 12).")
        elif cashflow_type == "Withdrawals":
            withdraw_mode = st.radio("Withdrawal mode", ["Fixed amount", "Percentage"], horizontal=True)
            if withdraw_mode == "Fixed amount":
                annual_cashflow = -st.number_input("Annual withdrawal ($)", value=4000, min_value=0, step=1000,
                                                    help="Withdrawn monthly (divided by 12).")
            else:
                withdraw_pct = st.number_input("Annual withdrawal (%)", value=4.0, min_value=0.1,
                                                max_value=20.0, step=0.1) / 100
                annual_cashflow = None  # signal to use percentage mode

    with st.expander("📈 Inflation"):
        adjust_inflation = st.checkbox("Adjust for inflation", value=False)
        inflation_rate = 0.0
        if adjust_inflation:
            inflation_rate = st.number_input("Annual inflation (%)", value=2.5, min_value=0.0,
                                              max_value=15.0, step=0.1) / 100
            inflate_cashflows = st.checkbox("Inflation-adjust cash flows", value=True,
                                             help="Increase contributions/withdrawals with inflation each year.")

    with st.expander("🎯 Goal Planning"):
        use_goal = st.checkbox("Set a target goal", value=False)
        goal_amount = 0
        if use_goal:
            goal_amount = st.number_input("Target amount ($)", value=100000, min_value=1000, step=10000)

    sidebar_etf_reference()

# ── Run Simulation ──────────────────────────────────────────────────────────
if st.button("🚀 Run Simulation", type="primary", use_container_width=True) and valid and tickers:
    with st.spinner("Fetching historical data..."):
        prices = fetch_prices(tickers, str(start_date), str(end_date))

    if prices.empty:
        st.error("Could not fetch data.")
        st.stop()

    available = {t: w for t, w in zip(tickers, weights) if t in prices.columns}
    if not available:
        st.error("No valid tickers.")
        st.stop()
    total_w = sum(available.values())
    available = {t: w / total_w for t, w in available.items()}

    with st.spinner("Computing historical portfolio returns..."):
        port_returns = compute_portfolio_returns(prices, available, "monthly")

    # Historical stats
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]: metric_with_tooltip("Historical CAGR", f"{cagr(port_returns):.2%}", "CAGR")
    with cols[1]: metric_with_tooltip("Historical Vol", f"{annual_volatility(port_returns):.2%}", "Annual Volatility")
    with cols[2]: metric_with_tooltip("Max Drawdown", f"{max_drawdown(port_returns):.2%}", "Max Drawdown")
    with cols[3]: metric_with_tooltip("Data Points", f"{len(port_returns):,} days")

    # Run simulation
    with st.spinner(f"Running {n_sims:,} simulations over {n_years} years..."):
        trading_days = n_years * 252
        returns_arr = port_returns.values
        results = np.zeros((n_sims, trading_days + 1))
        results[:, 0] = initial_investment

        for i in range(n_sims):
            sampled = np.random.choice(returns_arr, size=trading_days, replace=True)
            balance = initial_investment
            for day in range(trading_days):
                balance *= (1 + sampled[day])

                # Monthly cash flows (every ~21 trading days)
                if (day + 1) % 21 == 0:
                    year = day // 252
                    if annual_cashflow is not None:
                        cf = annual_cashflow / 12
                        if adjust_inflation and inflate_cashflows and cf != 0:
                            cf *= (1 + inflation_rate) ** year
                        balance += cf
                    elif cashflow_type == "Withdrawals":
                        # Percentage withdrawal
                        cf = -(balance * withdraw_pct / 12)
                        balance += cf

                    balance = max(balance, 0)  # can't go below 0

                # Inflation adjustment on value
                if adjust_inflation:
                    daily_inf = (1 + inflation_rate) ** (1/252) - 1
                    balance /= (1 + daily_inf)

                results[i, day + 1] = balance

    # Percentiles
    pcts = {p: np.percentile(results, p, axis=0) for p in [5, 10, 25, 50, 75, 90, 95]}
    years_axis = np.arange(results.shape[1]) / 252

    # ── Fan Chart ───────────────────────────────────────────────────────────
    tab_fan, tab_dist, tab_stats, tab_yearly = st.tabs(["Projection", "Distribution", "Statistics", "Year-by-Year"])

    with tab_fan:
        fig = go.Figure()
        bands = [(5, 95, "rgba(99,110,250,0.08)"), (10, 90, "rgba(99,110,250,0.12)"), (25, 75, "rgba(99,110,250,0.22)")]
        for low, high, color in bands:
            fig.add_trace(go.Scatter(
                x=np.concatenate([years_axis, years_axis[::-1]]),
                y=np.concatenate([pcts[high], pcts[low][::-1]]),
                fill="toself", fillcolor=color, line=dict(width=0),
                name=f"{low}th–{high}th pctile", hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(x=years_axis, y=pcts[50], name="Median",
                                  line=dict(color="#636EFA", width=3)))
        fig.add_trace(go.Scatter(x=years_axis, y=pcts[10], name="10th pctile",
                                  line=dict(color="#EF553B", width=1.5, dash="dash")))
        fig.add_trace(go.Scatter(x=years_axis, y=pcts[90], name="90th pctile",
                                  line=dict(color="#00CC96", width=1.5, dash="dash")))

        if use_goal and goal_amount > 0:
            fig.add_hline(y=goal_amount, line_dash="dot", line_color="#FFA15A",
                          annotation_text=f"Goal: ${goal_amount:,.0f}")

        layout = get_plotly_layout(height=550)
        layout["xaxis_title"] = "Years"
        layout["yaxis_title"] = "Portfolio Value" + (" (real $)" if adjust_inflation else " ($)")
        layout["yaxis"]["tickformat"] = "$,.0f"
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with tab_dist:
        terminal = results[:, -1]
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(x=terminal, nbinsx=80, marker_color="#636EFA", opacity=0.7))
        fig_hist.add_vline(x=np.median(terminal), line_dash="dash", line_color="red",
                           annotation_text=f"Median: ${np.median(terminal):,.0f}")
        if use_goal and goal_amount > 0:
            fig_hist.add_vline(x=goal_amount, line_dash="dot", line_color="#FFA15A",
                               annotation_text=f"Goal: ${goal_amount:,.0f}")
        lh = get_plotly_layout(height=450)
        lh["xaxis_title"] = "Terminal Value ($)"
        lh["yaxis_title"] = "Frequency"
        lh["xaxis"]["tickformat"] = "$,.0f"
        lh["hovermode"] = "x"
        fig_hist.update_layout(**lh)
        st.plotly_chart(fig_hist, use_container_width=True)

    with tab_stats:
        terminal = results[:, -1]
        stats = [
            ("Mean", f"${np.mean(terminal):,.0f}"),
            ("Median", f"${np.median(terminal):,.0f}"),
            ("Std Dev", f"${np.std(terminal):,.0f}"),
            ("5th Percentile", f"${np.percentile(terminal, 5):,.0f}"),
            ("10th Percentile", f"${np.percentile(terminal, 10):,.0f}"),
            ("25th Percentile", f"${np.percentile(terminal, 25):,.0f}"),
            ("75th Percentile", f"${np.percentile(terminal, 75):,.0f}"),
            ("90th Percentile", f"${np.percentile(terminal, 90):,.0f}"),
            ("95th Percentile", f"${np.percentile(terminal, 95):,.0f}"),
            ("Min", f"${np.min(terminal):,.0f}"),
            ("Max", f"${np.max(terminal):,.0f}"),
            (f"Prob of Loss (< ${initial_investment:,.0f})", f"{(terminal < initial_investment).mean():.1%}"),
            (f"Prob of Doubling (> ${initial_investment * 2:,.0f})", f"{(terminal > initial_investment * 2).mean():.1%}"),
        ]
        if use_goal and goal_amount > 0:
            stats.append((f"Prob of Reaching Goal (${goal_amount:,.0f})", f"{(terminal >= goal_amount).mean():.1%}"))
        if cashflow_type == "Withdrawals":
            stats.append(("Prob of Ruin ($0)", f"{(terminal <= 0).mean():.1%}"))

        stats_df = pd.DataFrame(stats, columns=["Metric", "Value"])
        st.dataframe(stats_df, hide_index=True, use_container_width=True, height=550)

    with tab_yearly:
        yearly_data = {}
        for year in range(1, n_years + 1):
            idx = min(year * 252, results.shape[1] - 1)
            vals = results[:, idx]
            yearly_data[f"Year {year}"] = {
                "5th": f"${np.percentile(vals, 5):,.0f}",
                "25th": f"${np.percentile(vals, 25):,.0f}",
                "Median": f"${np.percentile(vals, 50):,.0f}",
                "75th": f"${np.percentile(vals, 75):,.0f}",
                "95th": f"${np.percentile(vals, 95):,.0f}",
            }
            if use_goal and goal_amount > 0:
                yearly_data[f"Year {year}"]["P(Goal)"] = f"{(vals >= goal_amount).mean():.1%}"

        st.dataframe(pd.DataFrame(yearly_data), use_container_width=True)
