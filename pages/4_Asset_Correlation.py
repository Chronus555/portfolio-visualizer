"""Asset Correlation — analyze relationships between assets with time comparisons."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data import fetch_prices
from utils.ui_helpers import (
    inject_css, COLORS, get_plotly_layout, sidebar_etf_reference, download_dataframe,
)
from utils.metrics import asset_correlation, rolling_correlation

st.set_page_config(page_title="Asset Correlation", page_icon="🔗", layout="wide")
inject_css()
st.title("🔗 Asset Correlation")
st.caption("Analyze correlations between assets, track how relationships change over time, and compare across periods.")

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    tickers_str = st.text_input("Assets (comma-separated)", value="SPY, QQQ, EFA, AGG, GLD, VNQ, TLT",
                                 help="Enter ticker symbols to analyze.")
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]

    st.markdown("**Date Range**")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", value=pd.Timestamp("2010-01-01"))
    end_date = col2.date_input("End", value=pd.Timestamp.today())

    with st.expander("Advanced Options"):
        method = st.selectbox("Correlation method", ["pearson", "spearman", "kendall"],
                               help="Pearson=linear, Spearman=rank, Kendall=concordance.")
        rolling_window = st.select_slider(
            "Rolling window",
            options=[21, 42, 63, 126, 252, 504],
            value=63,
            format_func=lambda x: {21: "1 month", 42: "2 months", 63: "3 months",
                                    126: "6 months", 252: "1 year", 504: "2 years"}[x],
        )
        return_freq = st.radio("Return frequency", ["Daily", "Weekly", "Monthly"], horizontal=True,
                                help="Frequency for computing returns before correlation.")

    with st.expander("Period Comparison"):
        compare_periods = st.checkbox("Compare two time periods", value=False,
                                       help="Compare correlations between two different periods.")
        if compare_periods:
            st.markdown("**Period 2**")
            c1, c2 = st.columns(2)
            start_date_2 = c1.date_input("Start ", value=pd.Timestamp("2020-01-01"))
            end_date_2 = c2.date_input("End ", value=pd.Timestamp.today())

    sidebar_etf_reference()

# ── Run ─────────────────────────────────────────────────────────────────────
if st.button("🚀 Analyze Correlations", type="primary", use_container_width=True) and len(tickers) >= 2:
    fetch_start = str(start_date)
    fetch_end = str(end_date)
    if compare_periods:
        fetch_start = str(min(start_date, start_date_2))
        fetch_end = str(max(end_date, end_date_2))

    with st.spinner("Fetching data..."):
        prices = fetch_prices(tickers, fetch_start, fetch_end)

    if prices.empty:
        st.error("Could not fetch data.")
        st.stop()

    available = [t for t in tickers if t in prices.columns]
    if len(available) < 2:
        st.error("Need at least 2 valid tickers.")
        st.stop()

    prices_full = prices[available]

    def compute_returns(p, freq):
        if freq == "Weekly":
            return p.resample("W").last().pct_change().dropna()
        elif freq == "Monthly":
            return p.resample("ME").last().pct_change().dropna()
        return p.pct_change().dropna()

    # Period 1 data
    p1 = prices_full[(prices_full.index >= str(start_date)) & (prices_full.index <= str(end_date))]
    ret1 = compute_returns(p1, return_freq)
    corr1 = ret1.corr(method=method)

    # ── Tabs ────────────────────────────────────────────────────────────────
    tabs = ["Correlation Matrix", "Rolling Correlation", "Scatter Analysis", "Return Distributions"]
    if compare_periods:
        tabs.insert(1, "Period Comparison")
    active_tabs = st.tabs(tabs)

    tab_idx = 0

    # ── Heatmap ─────────────────────────────────────────────────────────────
    with active_tabs[tab_idx]:
        fig = go.Figure(data=go.Heatmap(
            z=corr1.values, x=available, y=available,
            colorscale="RdBu_r", zmin=-1, zmax=1, zmid=0,
            text=np.round(corr1.values, 2), texttemplate="%{text}",
            textfont=dict(size=12, color="white"),
        ))
        fig.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                           margin=dict(l=60, r=20, t=20, b=60))
        st.plotly_chart(fig, use_container_width=True)

        # Top/bottom pairs
        pairs = []
        for i in range(len(available)):
            for j in range(i + 1, len(available)):
                pairs.append((available[i], available[j], corr1.iloc[i, j]))
        pairs.sort(key=lambda x: x[2])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔻 Most Negatively Correlated**")
            for t1, t2, c in pairs[:3]:
                color = "#EF553B" if c < -0.3 else "#94a3b8"
                st.markdown(f"<span style='color:{color}'>{t1} / {t2}: **{c:.3f}**</span>", unsafe_allow_html=True)
        with col2:
            st.markdown("**🔺 Most Positively Correlated**")
            for t1, t2, c in pairs[-3:][::-1]:
                color = "#00CC96" if c > 0.7 else "#94a3b8"
                st.markdown(f"<span style='color:{color}'>{t1} / {t2}: **{c:.3f}**</span>", unsafe_allow_html=True)

        download_dataframe(corr1, "correlation_matrix.csv", "📥 Download correlation matrix")
    tab_idx += 1

    # ── Period Comparison ───────────────────────────────────────────────────
    if compare_periods:
        with active_tabs[tab_idx]:
            p2 = prices_full[(prices_full.index >= str(start_date_2)) & (prices_full.index <= str(end_date_2))]
            ret2 = compute_returns(p2, return_freq)
            corr2 = ret2.corr(method=method)
            diff = corr2 - corr1

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Period 1:** {start_date} to {end_date}")
                fig1 = go.Figure(data=go.Heatmap(
                    z=corr1.values, x=available, y=available,
                    colorscale="RdBu_r", zmin=-1, zmax=1,
                    text=np.round(corr1.values, 2), texttemplate="%{text}",
                    textfont=dict(size=10),
                ))
                fig1.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                                    margin=dict(l=40, r=10, t=10, b=40))
                st.plotly_chart(fig1, use_container_width=True)

            with c2:
                st.markdown(f"**Period 2:** {start_date_2} to {end_date_2}")
                fig2 = go.Figure(data=go.Heatmap(
                    z=corr2.values, x=available, y=available,
                    colorscale="RdBu_r", zmin=-1, zmax=1,
                    text=np.round(corr2.values, 2), texttemplate="%{text}",
                    textfont=dict(size=10),
                ))
                fig2.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                                    margin=dict(l=40, r=10, t=10, b=40))
                st.plotly_chart(fig2, use_container_width=True)

            with c3:
                st.markdown("**Change (P2 − P1)**")
                fig3 = go.Figure(data=go.Heatmap(
                    z=diff.values, x=available, y=available,
                    colorscale="RdBu_r", zmin=-0.5, zmax=0.5, zmid=0,
                    text=np.round(diff.values, 2), texttemplate="%{text}",
                    textfont=dict(size=10),
                ))
                fig3.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                                    margin=dict(l=40, r=10, t=10, b=40))
                st.plotly_chart(fig3, use_container_width=True)

            # Biggest changes
            changes = []
            for i in range(len(available)):
                for j in range(i + 1, len(available)):
                    changes.append((available[i], available[j], diff.iloc[i, j]))
            changes.sort(key=lambda x: abs(x[2]), reverse=True)
            st.markdown("**Largest Correlation Changes:**")
            for t1, t2, d in changes[:5]:
                direction = "↑" if d > 0 else "↓"
                st.write(f"{t1} / {t2}: {direction} **{d:+.3f}** ({corr1.loc[t1, t2]:.3f} → {corr2.loc[t1, t2]:.3f})")

        tab_idx += 1

    # ── Rolling Correlation ─────────────────────────────────────────────────
    with active_tabs[tab_idx]:
        # Auto-select interesting pairs
        default_pairs = []
        if len(pairs) >= 2:
            default_pairs = [f"{pairs[0][0]} / {pairs[0][1]}", f"{pairs[-1][0]} / {pairs[-1][1]}"]

        selected = st.multiselect("Select pairs", [f"{p[0]} / {p[1]}" for p in pairs],
                                   default=default_pairs[:3])
        if selected:
            fig_r = go.Figure()
            for idx, pair_str in enumerate(selected):
                t1, t2 = pair_str.split(" / ")
                rc = rolling_correlation(p1, t1, t2, rolling_window)
                fig_r.add_trace(go.Scatter(
                    x=rc.index, y=rc.values, name=pair_str,
                    line=dict(color=COLORS[idx % len(COLORS)], width=1.5),
                ))
            fig_r.add_hline(y=0, line_color="#475569", line_dash="dash", opacity=0.5)
            lr = get_plotly_layout(height=450)
            lr["yaxis_title"] = "Correlation"
            lr["yaxis"]["range"] = [-1, 1]
            fig_r.update_layout(**lr)
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info("Select at least one pair to see rolling correlation.")
    tab_idx += 1

    # ── Scatter Analysis ────────────────────────────────────────────────────
    with active_tabs[tab_idx]:
        pair_opts = [f"{p[0]} vs {p[1]} (ρ={p[2]:.3f})" for p in pairs]
        sel = st.selectbox("Select pair", pair_opts, index=len(pairs) - 1)
        pair_idx = pair_opts.index(sel)
        t1, t2, c = pairs[pair_idx]

        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(
            x=ret1[t1], y=ret1[t2], mode="markers",
            marker=dict(size=3.5, color="#636EFA", opacity=0.4),
            name=f"{t1} vs {t2}",
        ))
        m, b = np.polyfit(ret1[t1], ret1[t2], 1)
        x_line = np.linspace(ret1[t1].min(), ret1[t1].max(), 100)
        fig_s.add_trace(go.Scatter(
            x=x_line, y=m * x_line + b, mode="lines",
            name=f"Fit (β={m:.2f})", line=dict(color="#EF553B", width=2),
        ))
        ls = get_plotly_layout(height=500)
        ls["xaxis_title"] = f"{t1} Return"
        ls["yaxis_title"] = f"{t2} Return"
        ls["xaxis"]["tickformat"] = ".1%"
        ls["yaxis"]["tickformat"] = ".1%"
        ls["hovermode"] = "closest"
        fig_s.update_layout(**ls)
        st.plotly_chart(fig_s, use_container_width=True)

        st.caption(f"Correlation: **{c:.4f}** | Regression slope (β): **{m:.4f}** | Intercept: **{b:.6f}** | N={len(ret1)}")
    tab_idx += 1

    # ── Return Distributions ────────────────────────────────────────────────
    with active_tabs[tab_idx]:
        display_tickers = st.multiselect("Assets to display", available, default=available[:4])
        if display_tickers:
            fig_d = go.Figure()
            for idx, t in enumerate(display_tickers):
                fig_d.add_trace(go.Histogram(
                    x=ret1[t], nbinsx=80, name=t, opacity=0.5,
                    marker_color=COLORS[idx % len(COLORS)],
                ))
            ld = get_plotly_layout(height=450)
            ld["barmode"] = "overlay"
            ld["xaxis_title"] = "Return"
            ld["yaxis_title"] = "Frequency"
            ld["xaxis"]["tickformat"] = ".1%"
            fig_d.update_layout(**ld)
            st.plotly_chart(fig_d, use_container_width=True)

            # Stats table
            stats = {}
            for t in display_tickers:
                stats[t] = {
                    "Mean": f"{ret1[t].mean():.4%}",
                    "Std Dev": f"{ret1[t].std():.4%}",
                    "Skewness": f"{ret1[t].skew():.3f}",
                    "Kurtosis": f"{ret1[t].kurtosis():.3f}",
                    "Min": f"{ret1[t].min():.2%}",
                    "Max": f"{ret1[t].max():.2%}",
                }
            st.dataframe(pd.DataFrame(stats), use_container_width=True)

elif len(tickers) < 2:
    st.info("Enter at least 2 tickers to analyze correlations.")
