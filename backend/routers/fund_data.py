"""
Fund screener / ticker search / metadata endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import yfinance as yf
import pandas as pd
import numpy as np

from services.data_service import fetch_returns, get_ticker_info, current_year
from services.backtest_service import (
    compute_cagr,
    compute_max_drawdown,
    compute_sharpe,
    compute_sortino,
)

router = APIRouter(prefix="/api/funds", tags=["Fund Data"])


@router.get("/search")
async def search_ticker(q: str = Query(..., min_length=1)):
    """Quick ticker info lookup."""
    try:
        ticker = yf.Ticker(q.upper())
        info = ticker.info
        return {
            "ticker": q.upper(),
            "name": info.get("longName") or info.get("shortName", q.upper()),
            "type": info.get("quoteType"),
            "exchange": info.get("exchange"),
            "currency": info.get("currency"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception:
        raise HTTPException(status_code=404, detail=f"Ticker '{q}' not found")


@router.post("/screener")
async def screen_funds(
    tickers: List[str],
    start_year: int = 2010,
    end_year: Optional[int] = None,
):
    """Return performance metrics for a list of tickers."""
    end_y = end_year or current_year()
    results = []

    for ticker in tickers:
        try:
            info = get_ticker_info(ticker)
            rets = fetch_returns([ticker], start_year, end_y, "M")
            if ticker not in rets.columns or rets[ticker].empty:
                continue
            s = rets[ticker].dropna()
            # Build cumulative value series
            cum = (1 + s).cumprod()

            def cagr_n(years):
                if len(cum) < years * 12:
                    return None
                sub = cum.iloc[-(years * 12):]
                return round(compute_cagr(sub) * 100, 2)

            results.append({
                "ticker": ticker,
                "name": info.get("name", ticker),
                "cagr_1yr": cagr_n(1),
                "cagr_3yr": cagr_n(3),
                "cagr_5yr": cagr_n(5),
                "cagr_10yr": cagr_n(10),
                "stdev": round(float(s.std() * np.sqrt(12)) * 100, 2),
                "sharpe": round(compute_sharpe(s), 3),
                "sortino": round(compute_sortino(s), 3),
                "max_drawdown": round(compute_max_drawdown(cum) * 100, 2),
                "expense_ratio": info.get("expense_ratio"),
            })
        except Exception:
            continue

    return results


@router.get("/validate")
async def validate_ticker(ticker: str = Query(...)):
    """Check if a ticker symbol looks valid.

    Cloud hosts are blocked/rate-limited by Yahoo Finance so we cannot
    fetch live data to verify existence.  We validate the symbol format
    only; the analysis endpoints will surface a proper error if the ticker
    truly has no data on Yahoo Finance.
    """
    import re
    sym = ticker.strip().upper()
    _TICKER_RE = re.compile(r'^[A-Z0-9][A-Z0-9.\-]{0,9}$')
    if not sym or not _TICKER_RE.match(sym):
        return {"valid": False, "ticker": sym, "reason": "Invalid ticker format"}
    return {"valid": True, "ticker": sym}
