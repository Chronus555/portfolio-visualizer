"""Factor Analysis — Fama-French style regression with confidence intervals and diagnostics."""

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
from utils.metrics import compute_portfolio_returns

st.set_page_config(page_title="Factor Analysis", page_icon="🔬", layout="wide")
inject_css()
st.title("🔬 Factor Analysis")
st.caption("Decompose portfolio returns into factor exposures using regression analysis.")

# Factor definitions with descriptions
FACTOR_INFO = {
    "Market": {"proxy": "SPY", "desc": "Overall equity market exposure (S&P 500)", "construction": "SPY returns"},
    "Size (SMB)": {"proxy_long": "IWM", "proxy_short": "SPY", "desc": "Small-cap premium: small minus large", "construction": "IWM − SPY"},
    "Value (HML)": {"proxy_long": "IWD", "proxy_short": "IWF", "desc": "Value premium: value minus growth", "construction": "IWD − IWF"},
    "Momentum": {"proxy": "MTUM", "desc": "Momentum factor: recent winners outperform losers", "construction": "MTUM returns"},
    "Quality": {"proxy": "QUAL", "desc": "Quality factor: profitable, stable companies", "construction": "QUAL returns"},
    "Low Volatility": {"proxy": "USMV", "desc": "Low-vol anomaly: less volatile stocks", "construction": "USMV returns"},
    "Dividend": {"proxy": "SCHD", "desc": "Dividend yield factor", "construction": "SCHD returns"},
}

ALL_FACTOR_TICKERS = ["SPY", "IWM", "IWD", "IWF", "MTUM", "QUAL", "USMV", "SCHD"]

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📦 Portfolio")
    tickers, weights, valid = sidebar_portfolio_input("fa", "QQQ", "100", show_template=True)

    st.header("📅 Period")
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", value=pd.Timestamp("2014-01-01"))
    end_date = col2.date_input("End", value=pd.Timestamp.today())

    st.header("🔬 Factors")
    selected_factors = st.multiselect(
        "Factors to include",
        list(FACTOR_INFO.keys()),
        default=["Market", "Size (SMB)", "Value (HML)"],
        help="Select risk factors for the regression model.",
    )

    with st.expander("Factor Details"):
        for name, info in FACTOR_INFO.items():
            st.markdown(f"**{name}** — {info['desc']}")
            st.caption(f"Proxy: {info['construction']}")

    with st.expander("Advanced"):
        regression_freq = st.radio("Regression frequency", ["Monthly", "Weekly"], horizontal=True,
                                    help="Monthly is standard for factor analysis.")
        rolling_window = st.slider("Rolling window (months)", 12, 60, 36,
                                    help="Window for rolling factor exposure analysis.")
        conf_level = st.select_slider("Confidence level", options=[0.90, 0.95, 0.99], value=0.95,
                                       format_func=lambda x: f"{x:.0%}")

    sidebar_etf_reference()

# ── Run ─────────────────────────────────────────────────────────────────────
if st.button("🚀 Run Factor Analysis", type="primary", use_container_width=True) and valid and selected_factors:
    all_needed = list(set(tickers + ALL_FACTOR_TICKERS))

    with st.spinner("Fetching data..."):
        prices = fetch_prices(all_needed, str(start_date), str(end_date))

    if prices.empty:
        st.error("Could not fetch data.")
        st.stop()

    available = {t: w for t, w in zip(tickers, weights) if t in prices.columns}
    if not available:
        st.error("No valid portfolio tickers.")
        st.stop()
    total_w = sum(available.values())
    available = {t: w / total_w for t, w in available.items()}

    port_returns = compute_portfolio_returns(prices, available, "monthly")
    returns_daily = prices.pct_change().dropna()

    # Build factor returns
    factor_daily = {}
    missing_factors = []
    for fname in selected_factors:
        info = FACTOR_INFO[fname]
        if "proxy_long" in info:
            if info["proxy_long"] in returns_daily.columns and info["proxy_short"] in returns_daily.columns:
                factor_daily[fname] = returns_daily[info["proxy_long"]] - returns_daily[info["proxy_short"]]
            else:
                missing_factors.append(fname)
        else:
            if info["proxy"] in returns_daily.columns:
                factor_daily[fname] = returns_daily[info["proxy"]]
            else:
                missing_factors.append(fname)

    if missing_factors:
        st.warning(f"Missing data for factors: {', '.join(missing_factors)}. They will be excluded.")

    if not factor_daily:
        st.error("No factor data available.")
        st.stop()

    # Resample
    resample_rule = "ME" if regression_freq == "Monthly" else "W"
    port_periodic = port_returns.resample(resample_rule).apply(lambda x: (1 + x).prod() - 1)
    factor_periodic = {}
    for name, daily in factor_daily.items():
        factor_periodic[name] = daily.resample(resample_rule).apply(lambda x: (1 + x).prod() - 1)

    factors_df = pd.DataFrame(factor_periodic).dropna()
    aligned = pd.concat([port_periodic.rename("Portfolio"), factors_df], axis=1).dropna()

    if len(aligned) < 12:
        st.error("Not enough data. Try a longer time period.")
        st.stop()

    # ── OLS Regression ──────────────────────────────────────────────────────
    y = aligned["Portfolio"].values
    factor_names = [c for c in aligned.columns if c != "Portfolio"]
    X = aligned[factor_names].values
    X_c = np.column_stack([np.ones(len(X)), X])

    coeffs = np.linalg.lstsq(X_c, y, rcond=None)[0]
    y_pred = X_c @ coeffs
    resid = y - y_pred
    n, p = len(y), X_c.shape[1]

    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else r2
    mse = ss_res / (n - p) if n > p else ss_res

    try:
        cov_matrix = mse * np.linalg.inv(X_c.T @ X_c)
        se = np.sqrt(np.diag(cov_matrix))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)

    t_stats = coeffs / se
    t_crit = stats.t.ppf(1 - (1 - conf_level) / 2, n - p)
    p_vals = [2 * (1 - stats.t.cdf(abs(t), n - p)) for t in t_stats]
    ci_low = coeffs - t_crit * se
    ci_high = coeffs + t_crit * se

    alpha_val = coeffs[0]
    betas = coeffs[1:]
    periods_per_year = 12 if regression_freq == "Monthly" else 52

    # ── Summary Metrics ─────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]: metric_with_tooltip("R-Squared", f"{r2:.4f}", "R-Squared")
    with cols[1]: metric_with_tooltip("Adjusted R²", f"{adj_r2:.4f}")
    with cols[2]: metric_with_tooltip("Ann. Alpha", f"{alpha_val * periods_per_year:.2%}", "Alpha")
    with cols[3]: metric_with_tooltip("Observations", f"{n}")

    # ── Tabs ────────────────────────────────────────────────────────────────
    tab_reg, tab_exp, tab_rolling, tab_fit, tab_resid = st.tabs([
        "Regression Results", "Factor Exposures", "Rolling Exposures", "Model Fit", "Residual Diagnostics"
    ])

    with tab_reg:
        reg_rows = []
        labels = ["Alpha (Intercept)"] + factor_names
        for i in range(len(labels)):
            sig = "***" if p_vals[i] < 0.001 else "**" if p_vals[i] < 0.01 else "*" if p_vals[i] < 0.05 else ""
            reg_rows.append({
                "Factor": labels[i],
                "Coefficient": f"{coeffs[i]:.5f}",
                "Std Error": f"{se[i]:.5f}",
                "t-Stat": f"{t_stats[i]:.2f}",
                "p-Value": f"{p_vals[i]:.4f}",
                f"CI Low ({conf_level:.0%})": f"{ci_low[i]:.5f}",
                f"CI High ({conf_level:.0%})": f"{ci_high[i]:.5f}",
                "Sig": sig,
            })
        reg_df = pd.DataFrame(reg_rows)
        st.dataframe(reg_df, hide_index=True, use_container_width=True, height=350)
        st.caption("Significance: \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001")

        download_dataframe(reg_df, "factor_regression.csv", "📥 Download regression results")

        # Interpretation
        with st.expander("📖 How to interpret"):
            st.markdown(f"""
            - **Alpha ({alpha_val * periods_per_year:.2%} annualized):** {'Positive' if alpha_val > 0 else 'Negative'} alpha suggests the portfolio
              {'outperforms' if alpha_val > 0 else 'underperforms'} what the factor model predicts, though
              {'this is' if p_vals[0] < 0.05 else 'this is NOT'} statistically significant.
            - **R² = {r2:.2%}:** The factors explain {r2:.0%} of portfolio return variation.
              {f'The remaining {1-r2:.0%} is unexplained (stock-specific or other factors).' if r2 < 0.95 else ''}
            """)
            for i, fname in enumerate(factor_names):
                b = betas[i]
                sig = "statistically significant" if p_vals[i + 1] < 0.05 else "not statistically significant"
                st.markdown(f"- **{fname} (β={b:.3f}):** {'Positive' if b > 0 else 'Negative'} exposure, {sig}.")

    with tab_exp:
        fig_b = go.Figure()
        bar_colors = [("#00CC96" if b >= 0 else "#EF553B") for b in betas]
        error_y = [ci_high[i+1] - betas[i] for i in range(len(betas))]

        fig_b.add_trace(go.Bar(
            x=factor_names, y=betas,
            marker_color=bar_colors,
            error_y=dict(type="data", array=error_y, visible=True, color="#94a3b8"),
            text=[f"{b:.3f}" for b in betas],
            textposition="outside",
        ))
        fig_b.add_hline(y=0, line_color="#475569", line_dash="dash")
        lb = get_plotly_layout(height=450)
        lb["yaxis_title"] = f"Beta (with {conf_level:.0%} CI)"
        fig_b.update_layout(**lb)
        st.plotly_chart(fig_b, use_container_width=True)

        # Contribution to R²
        st.markdown("**Variance Explanation by Factor**")
        # Approximate contribution
        var_contrib = {}
        for i, fname in enumerate(factor_names):
            factor_col = aligned[fname].values
            contrib = betas[i] ** 2 * np.var(factor_col) / np.var(y) * 100
            var_contrib[fname] = contrib
        var_contrib["Unexplained"] = (1 - r2) * 100

        fig_vc = go.Figure(data=[go.Pie(
            labels=list(var_contrib.keys()),
            values=list(var_contrib.values()),
            hole=0.4,
            marker=dict(colors=COLORS[:len(var_contrib)]),
        )])
        fig_vc.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
                              margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_vc, use_container_width=True)

    with tab_rolling:
        if len(aligned) >= rolling_window:
            roll_betas = {f: [] for f in factor_names}
            roll_alpha = []
            roll_dates = []

            for end in range(rolling_window, len(aligned)):
                start_i = end - rolling_window
                y_w = aligned["Portfolio"].iloc[start_i:end].values
                X_w = aligned[factor_names].iloc[start_i:end].values
                X_wc = np.column_stack([np.ones(len(X_w)), X_w])
                try:
                    c = np.linalg.lstsq(X_wc, y_w, rcond=None)[0]
                    roll_alpha.append(c[0] * periods_per_year)
                    for j, f in enumerate(factor_names):
                        roll_betas[f].append(c[j + 1])
                    roll_dates.append(aligned.index[end])
                except Exception:
                    pass

            fig_rb = go.Figure()
            for idx, (fname, vals) in enumerate(roll_betas.items()):
                fig_rb.add_trace(go.Scatter(
                    x=roll_dates, y=vals, name=fname,
                    line=dict(color=COLORS[idx % len(COLORS)], width=2),
                ))
            fig_rb.add_hline(y=0, line_color="#475569", line_dash="dash")
            lr = get_plotly_layout(height=450)
            lr["yaxis_title"] = "Beta"
            lr["xaxis_title"] = "Date"
            fig_rb.update_layout(**lr)
            st.plotly_chart(fig_rb, use_container_width=True)

            # Rolling alpha
            st.markdown(f"**Rolling {rolling_window}-Month Annualized Alpha**")
            fig_ra = go.Figure()
            fig_ra.add_trace(go.Scatter(
                x=roll_dates, y=roll_alpha,
                fill="tozeroy",
                fillcolor="rgba(0,204,150,0.2)" if np.mean(roll_alpha) > 0 else "rgba(239,85,59,0.2)",
                line=dict(color="#00CC96" if np.mean(roll_alpha) > 0 else "#EF553B", width=1.5),
            ))
            fig_ra.add_hline(y=0, line_color="#475569", line_dash="dash")
            la = get_plotly_layout(height=300)
            la["yaxis"]["tickformat"] = ".1%"
            la["yaxis_title"] = "Annualized Alpha"
            fig_ra.update_layout(**la)
            st.plotly_chart(fig_ra, use_container_width=True)
        else:
            st.warning(f"Need at least {rolling_window} observations for rolling analysis.")

    with tab_fit:
        fig_f = go.Figure()
        fig_f.add_trace(go.Scatter(
            x=y_pred, y=y, mode="markers",
            marker=dict(size=5, color="#636EFA", opacity=0.6),
            name="Observations",
        ))
        lim_min = min(y.min(), y_pred.min())
        lim_max = max(y.max(), y_pred.max())
        fig_f.add_trace(go.Scatter(
            x=[lim_min, lim_max], y=[lim_min, lim_max],
            mode="lines", name="Perfect Fit",
            line=dict(color="#EF553B", dash="dash", width=2),
        ))
        lf = get_plotly_layout(height=500)
        lf["xaxis_title"] = "Model Predicted Return"
        lf["yaxis_title"] = "Actual Return"
        lf["xaxis"]["tickformat"] = ".1%"
        lf["yaxis"]["tickformat"] = ".1%"
        lf["hovermode"] = "closest"
        fig_f.update_layout(**lf)
        st.plotly_chart(fig_f, use_container_width=True)

    with tab_resid:
        col1, col2 = st.columns(2)
        with col1:
            fig_rt = go.Figure()
            fig_rt.add_trace(go.Scatter(
                x=aligned.index, y=resid, mode="markers+lines",
                marker=dict(size=4, color="#636EFA"), line=dict(width=0.5),
            ))
            fig_rt.add_hline(y=0, line_color="#EF553B", line_dash="dash")
            lrt = get_plotly_layout("Residuals Over Time", height=350)
            lrt["yaxis"]["tickformat"] = ".1%"
            fig_rt.update_layout(**lrt)
            st.plotly_chart(fig_rt, use_container_width=True)

        with col2:
            fig_rh = go.Figure()
            fig_rh.add_trace(go.Histogram(x=resid, nbinsx=30, marker_color="#636EFA", opacity=0.7))
            lrh = get_plotly_layout("Residual Distribution", height=350)
            lrh["xaxis"]["tickformat"] = ".1%"
            fig_rh.update_layout(**lrh)
            st.plotly_chart(fig_rh, use_container_width=True)

        # Diagnostic stats
        from scipy.stats import jarque_bera, shapiro
        jb_stat, jb_p = jarque_bera(resid)
        if len(resid) <= 5000:
            sw_stat, sw_p = shapiro(resid)
        else:
            sw_stat, sw_p = np.nan, np.nan

        # Durbin-Watson
        dw = np.sum(np.diff(resid) ** 2) / np.sum(resid ** 2)

        diag_data = {
            "Test": ["Jarque-Bera (normality)", "Shapiro-Wilk (normality)", "Durbin-Watson (autocorrelation)"],
            "Statistic": [f"{jb_stat:.3f}", f"{sw_stat:.3f}" if not np.isnan(sw_stat) else "N/A", f"{dw:.3f}"],
            "p-value": [f"{jb_p:.4f}", f"{sw_p:.4f}" if not np.isnan(sw_p) else "N/A", "~2 = no autocorr"],
            "Result": [
                "Normal ✓" if jb_p > 0.05 else "Non-normal ✗",
                ("Normal ✓" if sw_p > 0.05 else "Non-normal ✗") if not np.isnan(sw_p) else "N/A",
                "OK ✓" if 1.5 < dw < 2.5 else "Possible autocorrelation ✗",
            ],
        }
        st.dataframe(pd.DataFrame(diag_data), hide_index=True, use_container_width=True)
