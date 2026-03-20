"""Data fetching utilities using Yahoo Finance."""

import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Fetch adjusted close prices for a list of tickers.

    Returns a DataFrame with dates as index and tickers as columns.
    """
    tickers = [t.strip().upper() for t in tickers if t.strip()]
    if not tickers:
        return pd.DataFrame()

    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data[["Close"]].rename(columns={"Close": tickers[0]})

    prices = prices.dropna(how="all").ffill()
    return prices


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_risk_free_rate(start: str, end: str) -> pd.Series:
    """Fetch 3-month T-bill rate as a proxy for risk-free rate."""
    try:
        tbill = yf.download("^IRX", start=start, end=end, auto_adjust=True, progress=False)
        if tbill.empty:
            return pd.Series(dtype=float)
        if isinstance(tbill.columns, pd.MultiIndex):
            rate = tbill["Close"].squeeze() / 100 / 252  # daily rate
        else:
            rate = tbill["Close"] / 100 / 252
        return rate.ffill()
    except Exception:
        return pd.Series(dtype=float)


def get_common_etfs() -> dict[str, str]:
    """Return a dictionary of common ETFs for quick selection."""
    return {
        "SPY": "S&P 500",
        "QQQ": "Nasdaq 100",
        "IWM": "Russell 2000",
        "EFA": "International Developed",
        "EEM": "Emerging Markets",
        "AGG": "US Aggregate Bond",
        "TLT": "20+ Year Treasury",
        "GLD": "Gold",
        "VNQ": "Real Estate (REITs)",
        "DBC": "Commodities",
        "BND": "Total Bond Market",
        "VTI": "Total US Stock Market",
        "VXUS": "Total International Stock",
        "IEF": "7-10 Year Treasury",
        "TIP": "TIPS (Inflation Protected)",
        "LQD": "Investment Grade Corporate Bond",
        "HYG": "High Yield Corporate Bond",
        "VWO": "Emerging Markets (Vanguard)",
    }
