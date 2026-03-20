"""Shared UI helpers — CSS, portfolio templates, metric tooltips, export utilities."""

import streamlit as st
import pandas as pd
import numpy as np
import io
import base64


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
/* Global refinements */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1724 0%, #151d2e 100%);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.9rem;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a2236 0%, #1e293b 100%);
    border: 1px solid #2d3a4f;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #636EFA 0%, #5055d0 100%);
    border: none;
    border-radius: 8px;
    padding: 0.5rem 2rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99,110,250,0.4);
}

/* Expanders */
[data-testid="stExpander"] {
    border: 1px solid #2d3a4f;
    border-radius: 8px;
    background: #1a2236;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
}

/* Section dividers */
.section-divider {
    border-top: 1px solid #2d3a4f;
    margin: 1.5rem 0;
}

/* Info cards */
.info-card {
    background: linear-gradient(135deg, #1a2236 0%, #1e293b 100%);
    border: 1px solid #2d3a4f;
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
}

/* Tooltip styling */
.metric-help {
    color: #64748b;
    font-size: 0.75rem;
    font-style: italic;
    margin-top: 2px;
}
</style>
"""


def inject_css():
    """Inject custom CSS into the page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Portfolio templates
# ---------------------------------------------------------------------------

PORTFOLIO_TEMPLATES = {
    "Custom": {},
    "60/40 (Stocks/Bonds)": {"SPY": 60, "AGG": 40},
    "Three-Fund Portfolio": {"VTI": 50, "VXUS": 30, "BND": 20},
    "All-Weather (Ray Dalio)": {"SPY": 30, "TLT": 40, "IEF": 15, "GLD": 7.5, "DBC": 7.5},
    "Golden Butterfly": {"SPY": 20, "IWM": 20, "TLT": 20, "IEF": 20, "GLD": 20},
    "Permanent Portfolio": {"SPY": 25, "TLT": 25, "GLD": 25, "BIL": 25},
    "Classic 80/20": {"SPY": 80, "AGG": 20},
    "Conservative Income": {"AGG": 40, "TLT": 20, "SPY": 25, "VNQ": 10, "GLD": 5},
    "Aggressive Growth": {"QQQ": 40, "SPY": 25, "IWM": 15, "EEM": 10, "EFA": 10},
    "Risk Parity Approx": {"SPY": 20, "TLT": 30, "GLD": 20, "VNQ": 15, "AGG": 15},
    "Dividend Focus": {"VYM": 30, "SCHD": 30, "VNQ": 20, "AGG": 20},
    "US Total Market": {"VTI": 100},
    "Global 60/40": {"VTI": 35, "VXUS": 25, "BND": 25, "BNDX": 15},
}


def portfolio_template_selector(key_prefix: str = "template") -> tuple[str, str]:
    """Render a template dropdown. Returns (tickers_str, weights_str) or ('', '') if custom."""
    template = st.selectbox(
        "Quick template",
        list(PORTFOLIO_TEMPLATES.keys()),
        key=f"{key_prefix}_select",
        help="Select a pre-built portfolio template or choose Custom to define your own.",
    )
    alloc = PORTFOLIO_TEMPLATES[template]
    if alloc:
        tickers_str = ", ".join(alloc.keys())
        weights_str = ", ".join(str(v) for v in alloc.values())
        return tickers_str, weights_str
    return "", ""


# ---------------------------------------------------------------------------
# Metric tooltips / glossary
# ---------------------------------------------------------------------------

METRIC_TOOLTIPS = {
    "CAGR": "Compound Annual Growth Rate — the annualized return assuming profits are reinvested.",
    "Annual Volatility": "Annualized standard deviation of daily returns — measures total risk.",
    "Sharpe Ratio": "Risk-adjusted return: (Return - Risk-Free Rate) / Volatility. Higher is better. >1 is good, >2 is very good.",
    "Sortino Ratio": "Like Sharpe but only penalizes downside volatility. Higher is better.",
    "Max Drawdown": "Largest peak-to-trough decline. Shows worst-case loss if you bought at the top.",
    "Calmar Ratio": "CAGR divided by |Max Drawdown|. Measures return per unit of drawdown risk.",
    "Best Year": "Highest calendar year total return.",
    "Worst Year": "Lowest calendar year total return.",
    "VaR (5%)": "Value at Risk — the daily loss that is exceeded only 5% of the time.",
    "CVaR (5%)": "Conditional VaR (Expected Shortfall) — average loss on the worst 5% of days.",
    "Tail Ratio": "Ratio of gains at 95th percentile to losses at 5th percentile. >1 means positive skew in tails.",
    "Beta": "Sensitivity to benchmark. Beta=1 means moves with market; <1 is defensive; >1 is aggressive.",
    "Alpha": "Excess return after adjusting for beta. Positive alpha = outperformance vs benchmark.",
    "Information Ratio": "Active return per unit of tracking error. Measures consistency of outperformance.",
    "Skewness": "Measures return distribution asymmetry. Negative = more extreme losses than gains.",
    "Kurtosis": "Measures tail thickness. Higher = more extreme events than a normal distribution.",
    "R-Squared": "Percentage of portfolio variance explained by the factors. 1.0 = fully explained.",
    "Treynor Ratio": "Excess return per unit of systematic risk (beta). Higher is better.",
}


def metric_with_tooltip(label: str, value: str, tooltip_key: str = None):
    """Display a metric with an optional tooltip."""
    key = tooltip_key or label
    help_text = METRIC_TOOLTIPS.get(key, "")
    st.metric(label, value, help=help_text if help_text else None)


# ---------------------------------------------------------------------------
# Export utilities
# ---------------------------------------------------------------------------

def download_dataframe(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Add a download button for a DataFrame."""
    csv = df.to_csv(index=True)
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def download_chart_data(fig, df: pd.DataFrame, chart_name: str):
    """Add download button for chart underlying data."""
    csv = df.to_csv(index=True)
    st.download_button(
        label=f"Download {chart_name} data",
        data=csv,
        file_name=f"{chart_name.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Common sidebar helpers
# ---------------------------------------------------------------------------

def sidebar_date_range(default_start: str = "2010-01-01"):
    """Render start/end date pickers in sidebar. Returns (start_date, end_date)."""
    col1, col2 = st.columns(2)
    start = col1.date_input("Start date", value=pd.Timestamp(default_start))
    end = col2.date_input("End date", value=pd.Timestamp.today())
    return start, end


def sidebar_portfolio_input(key_prefix: str = "port", default_tickers: str = "SPY, AGG",
                             default_weights: str = "60, 40", show_template: bool = True):
    """Render portfolio ticker/weight inputs. Returns (tickers, weights, valid)."""
    if show_template:
        tmpl_tickers, tmpl_weights = portfolio_template_selector(key_prefix)
        if tmpl_tickers:
            default_tickers = tmpl_tickers
            default_weights = tmpl_weights

    tickers_str = st.text_input(
        "Tickers (comma-separated)", value=default_tickers, key=f"{key_prefix}_tickers",
        help="Enter ticker symbols separated by commas, e.g. SPY, AGG, GLD",
    )
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]

    weights_str = st.text_input(
        "Weights (must sum to 100)", value=default_weights, key=f"{key_prefix}_weights",
        help="Allocation percentages matching each ticker, e.g. 60, 40",
    )
    try:
        weights = [float(w.strip()) / 100 for w in weights_str.split(",") if w.strip()]
    except ValueError:
        st.error("Weights must be numbers.")
        return tickers, [], False

    valid = True
    if len(tickers) != len(weights):
        st.warning(f"Ticker count ({len(tickers)}) doesn't match weight count ({len(weights)}).")
        valid = False
    elif abs(sum(weights) - 1.0) > 0.011:
        st.warning(f"Weights sum to {sum(weights)*100:.1f}% — should be 100%.")
        valid = False

    return tickers, weights, valid


# ---------------------------------------------------------------------------
# Common ETF reference
# ---------------------------------------------------------------------------

ETF_CATEGORIES = {
    "US Equity": {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "IWM": "Russell 2000", "VTI": "Total Market", "DIA": "Dow Jones"},
    "International": {"EFA": "Developed Markets", "EEM": "Emerging Markets", "VXUS": "Total Intl", "VEA": "FTSE Developed"},
    "Fixed Income": {"AGG": "US Agg Bond", "BND": "Total Bond", "TLT": "20+ Yr Treasury", "IEF": "7-10 Yr Treasury", "TIP": "TIPS", "LQD": "IG Corporate", "HYG": "High Yield", "BIL": "1-3M T-Bill"},
    "Alternatives": {"GLD": "Gold", "VNQ": "REITs", "DBC": "Commodities", "BITO": "Bitcoin Futures"},
    "Factors": {"MTUM": "Momentum", "QUAL": "Quality", "USMV": "Low Vol", "IWD": "Value", "IWF": "Growth", "SCHD": "Dividend", "VYM": "High Dividend"},
}


def sidebar_etf_reference():
    """Show collapsible ETF reference in sidebar."""
    with st.expander("ETF Reference", expanded=False):
        for category, etfs in ETF_CATEGORIES.items():
            st.markdown(f"**{category}**")
            st.markdown(" ".join(f"`{t}`" for t in etfs.keys()))


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

COLORS = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
          "#FF6692", "#19D3F3", "#B6E880", "#FF97FF", "#FECB52"]


def get_plotly_layout(title: str = "", height: int = 500, **kwargs) -> dict:
    """Return a consistent Plotly layout dict."""
    layout = {
        "height": height,
        "hovermode": "x unified",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font": dict(color="#e2e8f0"),
        "xaxis": dict(gridcolor="#1e293b", zerolinecolor="#334155"),
        "yaxis": dict(gridcolor="#1e293b", zerolinecolor="#334155"),
        "legend": dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
        "margin": dict(l=60, r=20, t=40, b=60),
    }
    if title:
        layout["title"] = dict(text=title, font=dict(size=16))
    layout.update(kwargs)
    return layout
