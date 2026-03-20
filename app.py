"""Portfolio Visualizer — Main entry point and home dashboard."""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from utils.ui_helpers import inject_css, PORTFOLIO_TEMPLATES, ETF_CATEGORIES

st.set_page_config(
    page_title="Portfolio Visualizer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 1rem 0 0.5rem 0;">
    <h1 style="margin-bottom:0.2rem;">💼 Portfolio Visualizer</h1>
    <p style="color:#94a3b8; font-size:1.1rem; margin-top:0;">
        Open-source portfolio analysis, backtesting &amp; optimization suite
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Tool cards ──────────────────────────────────────────────────────────────
st.subheader("Analysis Tools")
tools = [
    ("📊", "Portfolio Backtest", "Compare up to 5 portfolios with 20+ metrics, drawdown analysis, rolling returns, monthly heatmaps, and contribution tracking."),
    ("📈", "Efficient Frontier", "Mean-Variance Optimization with tangency portfolio, minimum variance, risk parity, Capital Market Line, and custom constraints."),
    ("🎲", "Monte Carlo Simulation", "Project future outcomes with bootstrap resampling, fan charts, contributions/withdrawals, inflation adjustment, and success rates."),
    ("🔗", "Asset Correlation", "Correlation heatmaps, rolling correlations, scatter plots, return distributions, and time-period comparisons."),
    ("🔬", "Factor Analysis", "Fama-French style regression with rolling exposures, residual diagnostics, confidence intervals, and R² decomposition."),
    ("⚠️", "Risk Analysis", "VaR/CVaR, drawdown tables, risk contribution, rolling volatility, stress testing with custom scenarios, and tail risk analysis."),
]

cols = st.columns(3)
for i, (icon, name, desc) in enumerate(tools):
    with cols[i % 3]:
        st.markdown(f"""
        <div class="info-card">
            <h3 style="margin:0 0 6px 0;">{icon} {name}</h3>
            <p style="color:#94a3b8; font-size:0.85rem; margin:0;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ── Quick-start templates ───────────────────────────────────────────────────
st.subheader("Portfolio Templates")
st.markdown("Use these as starting points in any analysis tool.")

template_cols = st.columns(4)
templates_display = [
    ("60/40 Stocks/Bonds", "SPY 60%, AGG 40%", "The classic balanced portfolio."),
    ("Three-Fund", "VTI 50%, VXUS 30%, BND 20%", "Bogleheads favorite — simple, diversified."),
    ("All-Weather", "SPY 30%, TLT 40%, IEF 15%, GLD 7.5%, DBC 7.5%", "Ray Dalio's risk-balanced approach."),
    ("Golden Butterfly", "SPY 20%, IWM 20%, TLT 20%, IEF 20%, GLD 20%", "Equal-weight across asset classes."),
    ("Permanent Portfolio", "SPY 25%, TLT 25%, GLD 25%, BIL 25%", "Harry Browne's all-weather strategy."),
    ("Aggressive Growth", "QQQ 40%, SPY 25%, IWM 15%, EEM 10%, EFA 10%", "High equity, high growth focus."),
    ("Conservative Income", "AGG 40%, TLT 20%, SPY 25%, VNQ 10%, GLD 5%", "Income-focused with low volatility."),
    ("Global 60/40", "VTI 35%, VXUS 25%, BND 25%, BNDX 15%", "Globally diversified balanced portfolio."),
]
for i, (name, alloc, desc) in enumerate(templates_display):
    with template_cols[i % 4]:
        st.markdown(f"""
        <div class="info-card">
            <p style="margin:0 0 4px 0; font-weight:600;">{name}</p>
            <p style="color:#636EFA; font-size:0.8rem; margin:0 0 4px 0; font-family:monospace;">{alloc}</p>
            <p style="color:#64748b; font-size:0.75rem; margin:0;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── ETF Reference ───────────────────────────────────────────────────────────
st.subheader("ETF Reference Guide")
for category, etfs in ETF_CATEGORIES.items():
    with st.expander(f"**{category}** — {len(etfs)} ETFs"):
        cols = st.columns(len(etfs))
        for j, (ticker, name) in enumerate(etfs.items()):
            with cols[j]:
                st.markdown(f"**`{ticker}`**")
                st.caption(name)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Glossary ────────────────────────────────────────────────────────────────
with st.expander("Glossary of Terms"):
    glossary = {
        "CAGR": "Compound Annual Growth Rate — annualized return assuming reinvestment.",
        "Sharpe Ratio": "Risk-adjusted return = (Return - Rf) / Volatility. >1 good, >2 excellent.",
        "Sortino Ratio": "Like Sharpe but only penalizes downside volatility.",
        "Max Drawdown": "Largest peak-to-trough decline — worst-case loss from peak.",
        "VaR (Value at Risk)": "The loss threshold exceeded only X% of days.",
        "CVaR / Expected Shortfall": "Average loss on the worst X% of days. More conservative than VaR.",
        "Beta": "Sensitivity to the market. 1.0 = moves with market, <1 defensive, >1 aggressive.",
        "Alpha": "Excess return after adjusting for market exposure (beta).",
        "Calmar Ratio": "CAGR / |Max Drawdown|. Higher = better return per unit of drawdown.",
        "Information Ratio": "Active return / Tracking Error. Measures outperformance consistency.",
        "Efficient Frontier": "Set of portfolios offering highest return for each risk level.",
        "Tangency Portfolio": "Point on efficient frontier with the highest Sharpe Ratio.",
        "Monte Carlo": "Simulation technique that randomly samples historical returns to project future outcomes.",
        "Risk Parity": "Allocation where each asset contributes equally to total portfolio risk.",
    }
    for term, definition in glossary.items():
        st.markdown(f"**{term}:** {definition}")

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💼 Portfolio Visualizer")
    st.caption("Select a tool from the pages above.")
    st.markdown("---")
    st.markdown("**Data:** Yahoo Finance (real-time)")
    st.markdown("**Charts:** Plotly (interactive)")
    st.caption("Past performance ≠ future results.")
