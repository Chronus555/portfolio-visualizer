"""
Centralised data-fetching layer.

All market data comes from Yahoo Finance via yfinance.
Fama-French factor data comes from Ken French's data library via pandas_datareader.
"""

import logging
import threading
from datetime import datetime, date
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web

logger = logging.getLogger(__name__)

_cache: Dict[str, pd.DataFrame] = {}
_cache_lock = threading.Lock()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _cache_key(tickers: List[str], start: str, end: str) -> str:
    return f"{','.join(sorted(tickers))}|{start}|{end}"


def current_year() -> int:
    return datetime.now().year


# ── Price / return data ────────────────────────────────────────────────────────

def fetch_price_data(
    tickers: List[str],
    start_year: int,
    end_year: Optional[int] = None,
    frequency: str = "M",   # 'M' monthly, 'D' daily
) -> pd.DataFrame:
    """
    Return adjusted-close prices resampled to the requested frequency.
    Index is a DatetimeIndex; columns are ticker symbols.
    """
    end_y = end_year or current_year()
    start_str = f"{start_year}-01-01"
    end_str = f"{end_y}-12-31"

    key = _cache_key(tickers, f"{start_str}_{frequency}", end_str)
    with _cache_lock:
        if key in _cache:
            return _cache[key]

    try:
        raw = yf.download(
            tickers,
            start=start_str,
            end=end_str,
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        logger.error("yfinance download error: %s", e)
        raise ValueError(f"Failed to download data: {e}")

    if raw.empty:
        raise ValueError(f"No data returned for tickers: {tickers}")

    # Extract Close prices
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers

    # Resample
    if frequency == "M":
        prices = prices.resample("ME").last()
    elif frequency == "Y":
        prices = prices.resample("YE").last()

    prices = prices.dropna(how="all")

    # Drop columns that are entirely NaN (ticker didn't trade in range)
    prices = prices.dropna(axis=1, how="all")

    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        logger.warning("No data for: %s", missing)

    with _cache_lock:
        _cache[key] = prices

    return prices


def fetch_returns(
    tickers: List[str],
    start_year: int,
    end_year: Optional[int] = None,
    frequency: str = "M",
) -> pd.DataFrame:
    """Return periodic returns (pct_change)."""
    prices = fetch_price_data(tickers, start_year, end_year, frequency)
    return prices.pct_change().dropna()


def fetch_benchmark_returns(
    benchmark: str,
    start_year: int,
    end_year: Optional[int] = None,
) -> pd.Series:
    """Return monthly total returns for a benchmark ticker."""
    if not benchmark or benchmark.lower() == "none":
        return pd.Series(dtype=float)
    try:
        returns = fetch_returns([benchmark], start_year, end_year, "M")
        if benchmark in returns.columns:
            return returns[benchmark]
        return returns.iloc[:, 0]
    except Exception:
        return pd.Series(dtype=float)


# ── Ticker metadata ────────────────────────────────────────────────────────────

@lru_cache(maxsize=512)
def get_ticker_info(ticker: str) -> Dict:
    try:
        info = yf.Ticker(ticker).info
        return {
            "name": info.get("longName") or info.get("shortName", ticker),
            "expense_ratio": info.get("annualReportExpenseRatio"),
            "category": info.get("category"),
            "fund_family": info.get("fundFamily"),
            "asset_class": info.get("quoteType"),
        }
    except Exception:
        return {"name": ticker}


def validate_tickers(tickers: List[str]) -> Tuple[List[str], List[str]]:
    """Return (valid_tickers, invalid_tickers)."""
    valid, invalid = [], []
    for t in tickers:
        try:
            info = yf.Ticker(t).history(period="5d")
            if info.empty:
                invalid.append(t)
            else:
                valid.append(t)
        except Exception:
            invalid.append(t)
    return valid, invalid


# ── Fama-French factor data ────────────────────────────────────────────────────

_FF_CACHE: Dict[str, pd.DataFrame] = {}


def fetch_fama_french_factors(
    model: str = "ff3",
    start_year: int = 1926,
    end_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Return monthly Fama-French factors as decimals (not percentages).

    model options: 'ff3', 'ff5', 'carhart4'
    Columns returned:
      ff3:      Mkt-RF, SMB, HML, RF
      ff5:      Mkt-RF, SMB, HML, RMW, CMA, RF
      carhart4: Mkt-RF, SMB, HML, MOM, RF
    """
    cache_key = f"{model}_{start_year}_{end_year}"
    if cache_key in _FF_CACHE:
        return _FF_CACHE[cache_key]

    end_y = end_year or current_year()

    try:
        if model in ("ff3", "carhart4"):
            df = web.DataReader(
                "F-F_Research_Data_Factors",
                "famafrench",
                start=f"{start_year}-01-01",
                end=f"{end_y}-12-31",
            )[0]
        elif model == "ff5":
            df = web.DataReader(
                "F-F_Research_Data_5_Factors_2x3",
                "famafrench",
                start=f"{start_year}-01-01",
                end=f"{end_y}-12-31",
            )[0]
        else:
            raise ValueError(f"Unknown factor model: {model}")

        df = df / 100.0  # convert from % to decimal
        df.index = pd.to_datetime(df.index.to_timestamp())
        df.index = df.index + pd.offsets.MonthEnd(0)   # align to month-end

        if model == "carhart4":
            # Also fetch momentum factor
            mom = web.DataReader(
                "F-F_Momentum_Factor",
                "famafrench",
                start=f"{start_year}-01-01",
                end=f"{end_y}-12-31",
            )[0]
            mom = mom / 100.0
            mom.index = pd.to_datetime(mom.index.to_timestamp())
            mom.index = mom.index + pd.offsets.MonthEnd(0)
            mom.columns = ["MOM"]
            df = df.join(mom, how="inner")

        _FF_CACHE[cache_key] = df
        return df

    except Exception as e:
        logger.error("Fama-French data fetch error: %s", e)
        # Return empty DataFrame with correct columns on failure
        cols = {
            "ff3": ["Mkt-RF", "SMB", "HML", "RF"],
            "ff5": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"],
            "carhart4": ["Mkt-RF", "SMB", "HML", "MOM", "RF"],
        }
        return pd.DataFrame(columns=cols.get(model, []))


# ── Utility ────────────────────────────────────────────────────────────────────

def align_series(*series: pd.Series) -> List[pd.Series]:
    """Align multiple Series to their common date index."""
    df = pd.concat(series, axis=1).dropna()
    return [df.iloc[:, i] for i in range(len(series))]


def annualise_return(monthly_return: float) -> float:
    return (1 + monthly_return) ** 12 - 1


def annualise_vol(monthly_vol: float) -> float:
    return monthly_vol * np.sqrt(12)
