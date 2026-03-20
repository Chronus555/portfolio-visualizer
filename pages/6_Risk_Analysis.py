"""Risk Analysis — VaR, CVaR, stress testing, risk decomposition, and tail risk."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data import fetch_prices
from utils.ui_helpers import (
    inject_css, COLORS, get_plotly_layout, sidebar_portfolio_input,
    sidebar_etf_reference, metric_with_tooltip, download_dataframe,
)
from utils.metrics import (
    compute_portfolio_returns, var_historic, cvar_historic,
    max_drawdown, drawdown_series, annual_volatility, cagr,
)

st.set_page_config(page_title="Risk Analysis", page_icon="⚠️", layout="wide")
inject_css()
st.title("⚠️ Risk Analysis")
st.caption("Comprehensive risk assessment: VaR, CVaR, drawdowns, risk contribution, stress testing, and tail risk analysis.")

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📦 Portfolio")
    tickers, weights, valid = sidebar_portfolio_input("risk", "SPY, AGG, GLD", "60, 30, 10")

    st.header("📅 Period")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", value=pd.Timestamp("2005-01-01"))
    end_date = col2.date_input("End", value=pd.Timestamp.today())

    with st.expander("Advanced Options"):
        confidence = st.select_slider("VaR confidence", options=[0.90, 0.95, 0.99], value=0.95,
                                       format_func=lambda x: f"{x:.0%}")
        rebalance = st.selectbox("Rebalancing", ["monthly", "quarterly", "annually"])
        var_method = st.radio("VaR method", ["Historical", "Parametric (Normal)", "Cornish-Fisher"],
                               horizontal=True,
                               help="Historical=empirical quantile, Parametric=assumes normal, Cornish-Fisher=adjusts for skew/kurtosis.")
        var_horizon = st.selectbox("VaR horizon", ["1-day", "1-week", "1-month"],
                                    help="Time horizon for VaR calculation.")

    with st.expander("Custom Stress Scenarios"):
        st.caption("Add custom date ranges to stress test.")
        custom_name = st.text_input("Scenario name", value="", key="custom_stress_name")
        cs1, cs2 = st.columns(2)
        custom_start = cs1.date_input("From", value=pd.Timestamp("2020-02-19"), key="cs")
        custom_end = cs2.date_input("To", value=pd.Timestamp("2020-03-23"), key="ce")

    sidebar_etf_reference()

# ── Run ─────────────────────────────────────────────────────────────────────
if st.button("🚀 Analyze Risk", type="primary", use_container_width=True) and valid:
    with st.spinner("Fetching data..."):
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

    port_returns = compute_portfolio_returns(prices, available, rebalance)
    asset_returns = prices[list(available.keys())].pct_change().dropna()

    if len(port_returns) == 0:
        st.error("No return data available.")
        st.stop()

    # Horizon scaling
    horizon_days = {"1-day": 1, "1-week": 5, "1-month": 21}[var_horizon]

    # VaR calculation
    alpha = 1 - confidence
    if var_method == "Historical":
        var_val = var_historic(port_returns, alpha) * np.sqrt(horizon_days)
        cvar_val = cvar_historic(port_returns, alpha) * np.sqrt(horizon_days)
    elif var_method == "Parametric (Normal)":
        mu = port_returns.mean() * horizon_days
        sigma = port_returns.std() * np.sqrt(horizon_days)
        var_val = mu + stats.norm.ppf(alpha) * sigma
        cvar_val = mu - sigma * stats.norm.pdf(stats.norm.ppf(alpha)) / alpha
    else:  # Cornish-Fisher
        z = stats.norm.ppf(alpha)
        s = port_returns.skew()
        k = port_returns.kurtosis()
        z_cf = z + (z**2 - 1) * s / 6 + (z**3 - 3*z) * k / 24 - (2*z**3 - 5*z) * s**2 / 36
        mu = port_returns.mean() * horizon_days
        sigma = port_returns.std() * np.sqrt(horizon_days)
        var_val = mu + z_cf * sigma
        cvar_val = var_val * 1.15  # approximate

    mdd = max_drawdown(port_returns)
    vol = annual_volatility(port_returns)

    # ── Summary Cards ───────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    cols = st.columns(6)
    with cols[0]: metric_with_tooltip(f"VaR ({confidence:.0%})", f"{var_val:.2%}", "VaR (5%)")
    with cols[1]: metric_with_tooltip(f"CVaR ({confidence:.0%})", f"{cvar_val:.2%}", "CVaR (5%)")
    with cols[2]: metric_with_tooltip("Max Drawdown", f"{mdd:.2%}", "Max Drawdown")
    with cols[3]: metric_with_tooltip("Annual Vol", f"{vol:.2%}", "Annual Volatility")
    with cols[4]: metric_with_tooltip("CAGR", f"{cagr(port_returns):.2%}", "CAGR")
    with cols[5]: metric_with_tooltip("Skewness", f"{port_returns.skew():.3f}", "Skewness")

    st.caption(f"VaR method: {var_method} | Horizon: {var_horizon} | Confidence: {confidence:.0%}")

    # ── Tabs ────────────────────────────────────────────────────────────────
    tab_dist, tab_dd, tab_risk, tab_stress, tab_tail = st.tabs([
        "Return Distribution", "Drawdown Analysis", "Risk Contribution", "Stress Testing", "Tail Risk"
    ])

    with tab_dist:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=port_returns, nbinsx=120, marker_color="#636EFA", opacity=0.7, name="Returns"))

        # Overlay normal distribution
        x_range = np.linspace(port_returns.min(), port_returns.max(), 200)
        normal_pdf = stats.norm.pdf(x_range, port_returns.mean(), port_returns.std())
        # Scale to histogram
        bin_width = (port_returns.max() - port_returns.min()) / 120
        normal_scaled = normal_pdf * len(port_returns) * bin_width
        fig.add_trace(go.Scatter(x=x_range, y=normal_scaled, mode="lines",
                                  name="Normal fit", line=dict(color="#FFA15A", width=2, dash="dash")))

        fig.add_vline(x=var_val / np.sqrt(horizon_days) if horizon_days > 1 else var_val,
                       line_color="#EF553B", line_width=2,
                       annotation_text=f"VaR: {var_val:.2%}")
        fig.add_vline(x=cvar_val / np.sqrt(horizon_days) if horizon_days > 1 else cvar_val,
                       line_color="#AB63FA", line_width=2, line_dash="dash",
                       annotation_text=f"CVaR: {cvar_val:.2%}")
        ld = get_plotly_layout(height=500)
        ld["xaxis_title"] = "Daily Return"
        ld["yaxis_title"] = "Frequency"
        ld["xaxis"]["tickformat"] = ".1%"
        fig.update_layout(**ld)
        st.plotly_chart(fig, use_container_width=True)

    with tab_dd:
        dd = drawdown_series(port_returns)
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=dd.index, y=dd.values,
            fill="tozeroy", fillcolor="rgba(239,85,59,0.25)",
            line=dict(color="#EF553B", width=1), name="Drawdown",
        ))
        ldd = get_plotly_layout(height=450)
        ldd["yaxis"]["tickformat"] = ".1%"
        ldd["yaxis_title"] = "Drawdown"
        fig_dd.update_layout(**ldd)
        st.plotly_chart(fig_dd, use_container_width=True)

        # Find drawdown events
        cum = (1 + port_returns).cumprod()
        running_max = cum.cummax()
        dd_pct = (cum - running_max) / running_max
        in_dd = dd_pct < -0.02
        events = []
        start_idx = None
        for i in range(len(in_dd)):
            if in_dd.iloc[i] and start_idx is None:
                start_idx = i
            elif not in_dd.iloc[i] and start_idx is not None:
                period = dd_pct.iloc[start_idx:i]
                events.append({
                    "Start": dd_pct.index[start_idx].strftime("%Y-%m-%d"),
                    "Trough": period.idxmin().strftime("%Y-%m-%d"),
                    "Recovery": dd_pct.index[i].strftime("%Y-%m-%d"),
                    "Max DD": f"{period.min():.2%}",
                    "Duration": f"{(dd_pct.index[i] - dd_pct.index[start_idx]).days}d",
                    "Recovery Time": f"{(dd_pct.index[i] - period.idxmin()).days}d",
                })
                start_idx = None
        if start_idx is not None:
            period = dd_pct.iloc[start_idx:]
            events.append({
                "Start": dd_pct.index[start_idx].strftime("%Y-%m-%d"),
                "Trough": period.idxmin().strftime("%Y-%m-%d"),
                "Recovery": "Ongoing",
                "Max DD": f"{period.min():.2%}",
                "Duration": f"{(dd_pct.index[-1] - dd_pct.index[start_idx]).days}d",
                "Recovery Time": "—",
            })
        events.sort(key=lambda x: float(x["Max DD"].strip("%")) / 100)
        st.markdown("**Top 10 Drawdowns**")
        st.dataframe(pd.DataFrame(events[:10]), hide_index=True, use_container_width=True)

    with tab_risk:
        w_arr = np.array(list(available.values()))
        cov_mat = asset_returns.cov() * 252
        port_vol_ann = np.sqrt(w_arr @ cov_mat.values @ w_arr)

        mcr = cov_mat.values @ w_arr / port_vol_ann
        ccr = w_arr * mcr
        pcr = ccr / port_vol_ann * 100

        col1, col2 = st.columns([2, 1])
        with col1:
            risk_df = pd.DataFrame({
                "Asset": list(available.keys()),
                "Weight": w_arr,
                "Marginal Risk": mcr,
                "Risk Contrib": ccr,
                "% of Risk": pcr,
            })
            display_risk = risk_df.copy()
            display_risk["Weight"] = display_risk["Weight"].map("{:.1%}".format)
            display_risk["Marginal Risk"] = display_risk["Marginal Risk"].map("{:.4f}".format)
            display_risk["Risk Contrib"] = display_risk["Risk Contrib"].map("{:.4f}".format)
            display_risk["% of Risk"] = display_risk["% of Risk"].map("{:.1f}%".format)
            st.dataframe(display_risk, hide_index=True, use_container_width=True)

            download_dataframe(risk_df, "risk_contribution.csv", "📥 Download risk contribution")

        with col2:
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(available.keys()), values=np.abs(pcr),
                hole=0.4, marker=dict(colors=COLORS),
            )])
            fig_pie.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                                   margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Rolling volatility
        st.markdown("**Rolling Annualized Volatility**")
        roll_opts = {21: "1M", 63: "3M", 126: "6M", 252: "1Y"}
        roll_win = st.select_slider("Window", options=list(roll_opts.keys()), value=63,
                                     format_func=lambda x: roll_opts[x], key="risk_roll_win")
        rolling_vol = port_returns.rolling(roll_win).std() * np.sqrt(252)
        rolling_vol = rolling_vol.dropna()

        fig_rv = go.Figure()
        fig_rv.add_trace(go.Scatter(
            x=rolling_vol.index, y=rolling_vol.values,
            fill="tozeroy", fillcolor="rgba(99,110,250,0.15)",
            line=dict(color="#636EFA", width=1.5),
        ))
        lrv = get_plotly_layout(height=350)
        lrv["yaxis"]["tickformat"] = ".1%"
        lrv["yaxis_title"] = "Annualized Volatility"
        fig_rv.update_layout(**lrv)
        st.plotly_chart(fig_rv, use_container_width=True)

    with tab_stress:
        scenarios = {
            "2008 Financial Crisis": ("2008-09-01", "2008-11-30"),
            "2008-09 Bear Market (Full)": ("2007-10-01", "2009-03-09"),
            "Flash Crash (May 2010)": ("2010-05-06", "2010-05-07"),
            "Euro Debt Crisis (2011)": ("2011-07-01", "2011-09-30"),
            "Taper Tantrum (2013)": ("2013-05-01", "2013-06-30"),
            "China Deval / Oil (2015-16)": ("2015-08-01", "2016-02-11"),
            "Q4 2018 Selloff": ("2018-10-01", "2018-12-24"),
            "COVID Crash": ("2020-02-19", "2020-03-23"),
            "2022 Rate Hike Bear": ("2022-01-03", "2022-10-12"),
            "SVB / Banking Crisis (2023)": ("2023-03-08", "2023-03-15"),
        }

        # Add custom scenario
        if custom_name:
            scenarios[custom_name] = (str(custom_start), str(custom_end))

        results = []
        for name, (s, e) in scenarios.items():
            mask = (port_returns.index >= s) & (port_returns.index <= e)
            period = port_returns[mask]
            if len(period) > 0:
                total_ret = (1 + period).prod() - 1
                results.append({
                    "Scenario": name,
                    "Period": f"{s} to {e}",
                    "Return": f"{total_ret:.2%}",
                    "Max Daily Loss": f"{period.min():.2%}",
                    "Best Day": f"{period.max():.2%}",
                    "Volatility (Ann.)": f"{period.std() * np.sqrt(252):.2%}",
                    "Days": len(period),
                })

        if results:
            st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True, height=450)

            # Bar chart of scenario returns
            fig_stress = go.Figure()
            names = [r["Scenario"] for r in results]
            rets = [float(r["Return"].strip("%")) / 100 for r in results]
            fig_stress.add_trace(go.Bar(
                x=names, y=rets,
                marker_color=["#EF553B" if r < 0 else "#00CC96" for r in rets],
                text=[f"{r:.1%}" for r in rets], textposition="outside",
            ))
            ls = get_plotly_layout(height=400)
            ls["yaxis"]["tickformat"] = ".1%"
            ls["yaxis_title"] = "Return"
            ls["xaxis"]["tickangle"] = -35
            fig_stress.update_layout(**ls)
            st.plotly_chart(fig_stress, use_container_width=True)
        else:
            st.info("Portfolio data does not overlap with any stress scenarios.")

    with tab_tail:
        st.markdown("**Tail Risk Analysis**")

        col1, col2 = st.columns(2)
        with col1:
            # Left tail
            threshold = np.percentile(port_returns, 5)
            tail_returns = port_returns[port_returns <= threshold]
            st.markdown(f"**Left Tail (worst 5% of days)** — {len(tail_returns)} observations")
            st.markdown(f"- Threshold: **{threshold:.2%}**")
            st.markdown(f"- Average loss: **{tail_returns.mean():.2%}**")
            st.markdown(f"- Worst day: **{tail_returns.min():.2%}**")
            st.markdown(f"- Tail std dev: **{tail_returns.std():.4%}**")

        with col2:
            # Right tail
            threshold_r = np.percentile(port_returns, 95)
            tail_r = port_returns[port_returns >= threshold_r]
            st.markdown(f"**Right Tail (best 5% of days)** — {len(tail_r)} observations")
            st.markdown(f"- Threshold: **{threshold_r:.2%}**")
            st.markdown(f"- Average gain: **{tail_r.mean():.2%}**")
            st.markdown(f"- Best day: **{tail_r.max():.2%}**")
            st.markdown(f"- Tail std dev: **{tail_r.std():.4%}**")

        # Q-Q Plot
        st.markdown("**Q-Q Plot (Normal Distribution)**")
        sorted_returns = np.sort(port_returns.values)
        theoretical = stats.norm.ppf(np.linspace(0.001, 0.999, len(sorted_returns)))

        fig_qq = go.Figure()
        fig_qq.add_trace(go.Scatter(
            x=theoretical, y=sorted_returns, mode="markers",
            marker=dict(size=2, color="#636EFA", opacity=0.5),
            name="Returns",
        ))
        qq_min = min(theoretical.min(), sorted_returns.min())
        qq_max = max(theoretical.max(), sorted_returns.max())
        fig_qq.add_trace(go.Scatter(
            x=[qq_min, qq_max], y=[qq_min * port_returns.std() + port_returns.mean(),
                                    qq_max * port_returns.std() + port_returns.mean()],
            mode="lines", name="Normal reference",
            line=dict(color="#EF553B", dash="dash", width=2),
        ))
        lq = get_plotly_layout(height=450)
        lq["xaxis_title"] = "Theoretical Quantiles (Normal)"
        lq["yaxis_title"] = "Sample Quantiles"
        lq["yaxis"]["tickformat"] = ".1%"
        lq["hovermode"] = "closest"
        fig_qq.update_layout(**lq)
        st.plotly_chart(fig_qq, use_container_width=True)

        st.caption(f"Skewness: **{port_returns.skew():.3f}** | Kurtosis: **{port_returns.kurtosis():.3f}** — "
                   f"{'Fat tails detected (kurtosis > 3)' if port_returns.kurtosis() > 3 else 'Near-normal tails'}")
