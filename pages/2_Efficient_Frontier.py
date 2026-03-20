"""Efficient Frontier — Mean-Variance Optimization with advanced options."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data import fetch_prices
from utils.ui_helpers import (
    inject_css, COLORS, get_plotly_layout, sidebar_etf_reference,
    metric_with_tooltip, download_dataframe,
)
from utils.metrics import (
    efficient_frontier, tangency_portfolio, min_variance_portfolio,
    asset_correlation, sharpe_ratio, cagr, annual_volatility,
)

st.set_page_config(page_title="Efficient Frontier", page_icon="📈", layout="wide")
inject_css()
st.title("📈 Efficient Frontier")
st.caption("Find optimal asset allocations using Mean-Variance Optimization. Identify the tangency portfolio (max Sharpe) and minimum variance portfolio.")

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    tickers_str = st.text_input("Assets (comma-separated)", value="SPY, EFA, AGG, GLD, VNQ",
                                 help="Enter tickers for the assets to optimize across.")
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]

    st.markdown("**Date Range**")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", value=pd.Timestamp("2010-01-01"))
    end_date = col2.date_input("End", value=pd.Timestamp.today())

    st.markdown("**Optimization Parameters**")
    rf_rate = st.number_input("Risk-free rate (%)", value=4.5, min_value=0.0, max_value=20.0, step=0.1,
                               help="Current risk-free rate for Sharpe calculations.") / 100
    n_points = st.slider("Frontier resolution", 20, 200, 60,
                          help="Number of points along the efficient frontier.")

    with st.expander("Constraints", expanded=False):
        short_selling = st.checkbox("Allow short selling", value=False,
                                     help="Allow negative weights (shorting assets).")
        use_max_weight = st.checkbox("Maximum weight per asset", value=False)
        max_weight = 1.0
        if use_max_weight:
            max_weight = st.slider("Max weight (%)", 10, 100, 40, step=5) / 100
        use_min_weight = st.checkbox("Minimum weight per asset", value=False)
        min_weight = 0.0
        if use_min_weight:
            min_weight = st.slider("Min weight (%)", 0, 50, 5, step=1) / 100

    show_random = st.checkbox("Show random portfolios", value=True,
                               help="Scatter plot of 2000 random allocations for context.")

    sidebar_etf_reference()

# ── Run ─────────────────────────────────────────────────────────────────────
if st.button("🚀 Compute Efficient Frontier", type="primary", use_container_width=True) and len(tickers) >= 2:
    with st.spinner("Fetching data and running optimization..."):
        prices = fetch_prices(tickers, str(start_date), str(end_date))

    if prices.empty:
        st.error("Could not fetch data.")
        st.stop()

    available = [t for t in tickers if t in prices.columns]
    if len(available) < 2:
        st.error("Need at least 2 valid tickers.")
        st.stop()

    returns = prices[available].pct_change().dropna()
    mean_rets = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    # Override bounds if custom constraints
    from scipy import optimize

    def custom_bounds():
        lo = -1 if short_selling else min_weight
        hi = max_weight
        return tuple((lo, hi) for _ in range(len(available)))

    # Compute frontier with custom bounds
    n_assets = len(available)
    bounds = custom_bounds()
    w0 = np.ones(n_assets) / n_assets
    constraints_base = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

    def port_stats(w):
        pr = np.dot(w, mean_rets)
        pv = np.sqrt(np.dot(w.T, np.dot(cov_matrix.values, w)))
        return pr, pv

    # Find range
    min_r = optimize.minimize(lambda w: np.dot(w, mean_rets), w0, method="SLSQP",
                               bounds=bounds, constraints=constraints_base)
    max_r = optimize.minimize(lambda w: -np.dot(w, mean_rets), w0, method="SLSQP",
                               bounds=bounds, constraints=constraints_base)

    targets = np.linspace(np.dot(min_r.x, mean_rets), np.dot(max_r.x, mean_rets), n_points)
    f_risks, f_rets, f_weights = [], [], []
    for t in targets:
        cons = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, target=t: np.dot(w, mean_rets) - target},
        ]
        res = optimize.minimize(lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix.values, w))),
                                 w0, method="SLSQP", bounds=bounds, constraints=cons)
        if res.success:
            pr, pv = port_stats(res.x)
            f_risks.append(pv)
            f_rets.append(pr)
            f_weights.append(res.x)

    f_risks = np.array(f_risks)
    f_rets = np.array(f_rets)

    # Tangency (max Sharpe)
    def neg_sharpe(w):
        pr, pv = port_stats(w)
        return -(pr - rf_rate) / pv if pv > 0 else 0
    tang_res = optimize.minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=constraints_base)
    tang_ret, tang_vol = port_stats(tang_res.x)

    # Min variance
    minv_res = optimize.minimize(lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix.values, w))),
                                  w0, method="SLSQP", bounds=bounds, constraints=constraints_base)
    minv_ret, minv_vol = port_stats(minv_res.x)

    # ── Plot ────────────────────────────────────────────────────────────────
    fig = go.Figure()

    # Random portfolios
    if show_random:
        rand_risks, rand_rets = [], []
        for _ in range(2000):
            w = np.random.dirichlet(np.ones(n_assets))
            if use_max_weight:
                w = np.clip(w, min_weight, max_weight)
                w /= w.sum()
            pr, pv = port_stats(w)
            rand_risks.append(pv)
            rand_rets.append(pr)
        fig.add_trace(go.Scatter(
            x=rand_risks, y=rand_rets, mode="markers",
            name="Random Portfolios",
            marker=dict(size=2.5, color="#475569", opacity=0.4),
            hoverinfo="skip",
        ))

    # Efficient frontier
    fig.add_trace(go.Scatter(
        x=f_risks, y=f_rets, mode="lines",
        name="Efficient Frontier",
        line=dict(color="#636EFA", width=4),
        hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>",
    ))

    # Individual assets
    asset_vols = returns.std() * np.sqrt(252)
    fig.add_trace(go.Scatter(
        x=asset_vols.values, y=mean_rets.values, mode="markers+text",
        name="Individual Assets",
        text=available, textposition="top center", textfont=dict(size=11),
        marker=dict(size=12, color="#EF553B", line=dict(width=1, color="white")),
        hovertemplate="%{text}<br>Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>",
    ))

    # Tangency
    tang_sharpe = (tang_ret - rf_rate) / tang_vol if tang_vol > 0 else 0
    fig.add_trace(go.Scatter(
        x=[tang_vol], y=[tang_ret], mode="markers",
        name=f"Max Sharpe (SR={tang_sharpe:.2f})",
        marker=dict(size=18, color="#00CC96", symbol="star", line=dict(width=2, color="white")),
    ))

    # Min variance
    fig.add_trace(go.Scatter(
        x=[minv_vol], y=[minv_ret], mode="markers",
        name="Min Variance",
        marker=dict(size=16, color="#AB63FA", symbol="diamond", line=dict(width=2, color="white")),
    ))

    # Capital Market Line
    cml_x = np.linspace(0, max(f_risks) * 1.15, 100)
    cml_y = rf_rate + tang_sharpe * cml_x
    fig.add_trace(go.Scatter(
        x=cml_x, y=cml_y, mode="lines",
        name="Capital Market Line",
        line=dict(color="#94a3b8", width=1.5, dash="dot"),
    ))

    layout = get_plotly_layout(height=600)
    layout["xaxis_title"] = "Annual Volatility (Risk)"
    layout["yaxis_title"] = "Annual Expected Return"
    layout["xaxis"]["tickformat"] = ".1%"
    layout["yaxis"]["tickformat"] = ".1%"
    layout["hovermode"] = "closest"
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

    # ── Portfolio Details ───────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⭐ Max Sharpe Ratio Portfolio")
        cols = st.columns(3)
        with cols[0]: metric_with_tooltip("Exp. Return", f"{tang_ret:.2%}")
        with cols[1]: metric_with_tooltip("Volatility", f"{tang_vol:.2%}")
        with cols[2]: metric_with_tooltip("Sharpe", f"{tang_sharpe:.3f}", "Sharpe Ratio")

        tang_df = pd.DataFrame({"Ticker": available, "Weight": tang_res.x})
        tang_df = tang_df[tang_df["Weight"].abs() > 0.005].sort_values("Weight", ascending=False)
        tang_df["Weight"] = tang_df["Weight"].map("{:.1%}".format)
        st.dataframe(tang_df, hide_index=True, use_container_width=True)

    with col2:
        st.subheader("💎 Min Variance Portfolio")
        cols = st.columns(3)
        minv_sharpe = (minv_ret - rf_rate) / minv_vol if minv_vol > 0 else 0
        with cols[0]: metric_with_tooltip("Exp. Return", f"{minv_ret:.2%}")
        with cols[1]: metric_with_tooltip("Volatility", f"{minv_vol:.2%}")
        with cols[2]: metric_with_tooltip("Sharpe", f"{minv_sharpe:.3f}", "Sharpe Ratio")

        minv_df = pd.DataFrame({"Ticker": available, "Weight": minv_res.x})
        minv_df = minv_df[minv_df["Weight"].abs() > 0.005].sort_values("Weight", ascending=False)
        minv_df["Weight"] = minv_df["Weight"].map("{:.1%}".format)
        st.dataframe(minv_df, hide_index=True, use_container_width=True)

    # ── Tabs: Weights, Correlation, Individual Stats ────────────────────────
    tab_weights, tab_corr, tab_stats = st.tabs(["Weights Along Frontier", "Correlation Matrix", "Asset Statistics"])

    with tab_weights:
        fig_w = go.Figure()
        weights_arr = np.array(f_weights)
        for j, ticker in enumerate(available):
            fig_w.add_trace(go.Scatter(
                x=f_risks, y=weights_arr[:, j], mode="lines",
                name=ticker, stackgroup="one",
                line=dict(color=COLORS[j % len(COLORS)]),
            ))
        lw = get_plotly_layout(height=400)
        lw["xaxis_title"] = "Annual Volatility"
        lw["yaxis_title"] = "Weight"
        lw["xaxis"]["tickformat"] = ".1%"
        lw["yaxis"]["tickformat"] = ".0%"
        fig_w.update_layout(**lw)
        st.plotly_chart(fig_w, use_container_width=True)

    with tab_corr:
        corr = returns.corr()
        fig_c = go.Figure(data=go.Heatmap(
            z=corr.values, x=available, y=available,
            colorscale="RdBu_r", zmin=-1, zmax=1, zmid=0,
            text=np.round(corr.values, 2), texttemplate="%{text}",
            textfont=dict(size=12),
        ))
        fig_c.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_c, use_container_width=True)

    with tab_stats:
        stats_df = pd.DataFrame({
            "Ticker": available,
            "Ann. Return": mean_rets.values,
            "Ann. Volatility": asset_vols.values,
            "Sharpe Ratio": [(r - rf_rate) / v if v > 0 else 0 for r, v in zip(mean_rets, asset_vols)],
        }).sort_values("Sharpe Ratio", ascending=False)
        stats_df["Ann. Return"] = stats_df["Ann. Return"].map("{:.2%}".format)
        stats_df["Ann. Volatility"] = stats_df["Ann. Volatility"].map("{:.2%}".format)
        stats_df["Sharpe Ratio"] = stats_df["Sharpe Ratio"].map("{:.3f}".format)
        st.dataframe(stats_df, hide_index=True, use_container_width=True)

elif len(tickers) < 2:
    st.info("Enter at least 2 tickers to compute the efficient frontier.")
