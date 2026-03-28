"""
Dividend Analysis Service
Tracks dividend yield, growth, history, and income projections.
"""
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def analyze_dividends(
    holdings: List[Dict],   # [{"ticker": str, "shares": float, "value": float}, ...]
    years_history: int = 5,
    project_years: int = 10,
    dividend_growth_assumption: float = 0.05,  # 5% annual growth
) -> Dict:
    """
    Full dividend analysis: yield, history, growth, income projection.
    """
    total_value = sum(h.get("value", 0) for h in holdings)
    portfolio_income = 0.0
    ticker_results = []
    dividend_history_combined = {}

    for holding in holdings:
        ticker = holding["ticker"]
        value  = float(holding.get("value", 0))
        shares = float(holding.get("shares", 0))

        try:
            result = _analyze_single(ticker, value, shares, years_history)
            if result:
                portfolio_income += result.get("annual_income", 0)
                ticker_results.append(result)
                # Merge dividend history
                for entry in result.get("history", []):
                    dt = entry["date"]
                    if dt not in dividend_history_combined:
                        dividend_history_combined[dt] = 0.0
                    dividend_history_combined[dt] += entry.get("income", 0)
        except Exception as e:
            logger.warning("Dividend analysis error for %s: %s", ticker, e)
            ticker_results.append({
                "ticker": ticker,
                "name": ticker,
                "value": value,
                "annual_income": 0,
                "dividend_yield": None,
                "available": False,
            })

    # Sort combined history
    sorted_history = [
        {"date": k, "income": round(v, 2)}
        for k, v in sorted(dividend_history_combined.items())
    ]

    # Income projection
    projection = _project_income(portfolio_income, project_years, dividend_growth_assumption)

    portfolio_yield = (portfolio_income / total_value * 100) if total_value > 0 else 0

    ticker_results.sort(key=lambda x: x.get("annual_income", 0), reverse=True)

    return {
        "summary": {
            "total_portfolio_value": round(total_value, 2),
            "annual_income":         round(portfolio_income, 2),
            "monthly_income":        round(portfolio_income / 12, 2),
            "portfolio_yield":       round(portfolio_yield, 4),
            "income_payers":         sum(1 for t in ticker_results if (t.get("annual_income") or 0) > 0),
            "non_payers":            sum(1 for t in ticker_results if (t.get("annual_income") or 0) == 0),
        },
        "holdings":           ticker_results,
        "combined_history":   sorted_history[-24:],  # last 24 quarters
        "income_projection":  projection,
    }


def _analyze_single(ticker: str, value: float, shares: float, years: int) -> Optional[Dict]:
    """Analyze dividends for a single ticker."""
    t = yf.Ticker(ticker)
    info = t.info

    name = info.get("longName") or info.get("shortName", ticker)
    _raw_yield = info.get("dividendYield")
    ttm_div   = info.get("trailingAnnualDividendRate") or 0.0
    payout_ratio = info.get("payoutRatio")
    ex_div_date  = info.get("exDividendDate")

    # yfinance is inconsistent: sometimes returns dividendYield as decimal (0.033)
    # and sometimes as percentage (3.3). Normalise to decimal.
    if _raw_yield is not None:
        div_yield = _raw_yield / 100 if _raw_yield > 1 else _raw_yield
    else:
        div_yield = None

    # Convert ex-div timestamp
    ex_div_str = None
    if ex_div_date:
        try:
            ex_div_str = datetime.fromtimestamp(ex_div_date).strftime("%Y-%m-%d")
        except Exception:
            pass

    # Get dividend history
    start = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
    divs = t.dividends
    divs = divs[divs.index >= start] if not divs.empty else divs

    history = []
    if not divs.empty:
        for date_idx, amount in divs.items():
            dt_str = date_idx.strftime("%Y-%m-%d") if hasattr(date_idx, "strftime") else str(date_idx)[:10]
            income = float(amount) * shares if shares > 0 else float(amount) * (value / (info.get("previousClose") or 1))
            history.append({
                "date":       dt_str,
                "dividend":   round(float(amount), 4),
                "income":     round(income, 2),
            })

    # Calculate annual income
    annual_income = 0.0
    if shares > 0 and ttm_div:
        annual_income = shares * ttm_div
    elif div_yield and value:
        annual_income = value * div_yield

    # Compute dividend growth rate (CAGR over available history)
    div_cagr = _compute_div_growth(divs)

    # Quality score
    quality = _dividend_quality_score(info, div_cagr)

    return {
        "ticker":           ticker,
        "name":             name,
        "value":            round(value, 2),
        "shares":           shares,
        "dividend_yield":   round(div_yield * 100, 4) if div_yield else None,
        "ttm_dividend":     round(ttm_div, 4) if ttm_div else None,
        "annual_income":    round(annual_income, 2),
        "monthly_income":   round(annual_income / 12, 2),
        "payout_ratio":     round(payout_ratio * 100, 2) if payout_ratio else None,
        "ex_dividend_date": ex_div_str,
        "dividend_cagr_5y": div_cagr,
        "quality_score":    quality,
        "history":          history[-20:],  # last 20 distributions
        "available":        True,
    }


def _compute_div_growth(divs: pd.Series) -> Optional[float]:
    """Calculate 5-year dividend CAGR."""
    if divs.empty or len(divs) < 4:
        return None
    try:
        # Annual totals
        annual = divs.resample("YE").sum()
        annual = annual[annual > 0]
        if len(annual) < 2:
            return None
        n_years = len(annual) - 1
        cagr = (float(annual.iloc[-1]) / float(annual.iloc[0])) ** (1 / n_years) - 1
        return round(cagr * 100, 2)
    except Exception:
        return None


def _dividend_quality_score(info: Dict, div_cagr: Optional[float]) -> Dict:
    """Score dividend quality: Yield, Growth, Payout Safety, Consistency."""
    score = 0
    max_score = 100
    details = []

    # Yield score (0–25): sweet spot 1–6%
    _raw_dy = info.get("dividendYield", 0) or 0
    # Normalise: yfinance sometimes returns 3.3 instead of 0.033
    dy = _raw_dy / 100 if _raw_dy > 1 else _raw_dy
    if dy > 0:
        dy_pct = dy * 100
        if 1 <= dy_pct <= 3:
            score += 20; details.append({"factor": "Yield", "score": 20, "note": f"{dy_pct:.2f}% — healthy"})
        elif 3 < dy_pct <= 6:
            score += 25; details.append({"factor": "Yield", "score": 25, "note": f"{dy_pct:.2f}% — attractive"})
        elif dy_pct > 6:
            score += 10; details.append({"factor": "Yield", "score": 10, "note": f"{dy_pct:.2f}% — high, may be unsustainable"})
        else:
            score += 5;  details.append({"factor": "Yield", "score": 5,  "note": f"{dy_pct:.2f}% — low"})
    else:
        details.append({"factor": "Yield", "score": 0, "note": "No dividend"})

    # Growth score (0–25)
    if div_cagr is not None:
        if div_cagr >= 8:
            score += 25; details.append({"factor": "Growth", "score": 25, "note": f"{div_cagr:.1f}%/yr CAGR — excellent"})
        elif div_cagr >= 5:
            score += 20; details.append({"factor": "Growth", "score": 20, "note": f"{div_cagr:.1f}%/yr CAGR — good"})
        elif div_cagr >= 0:
            score += 10; details.append({"factor": "Growth", "score": 10, "note": f"{div_cagr:.1f}%/yr CAGR — slow"})
        else:
            score += 0;  details.append({"factor": "Growth", "score": 0,  "note": f"{div_cagr:.1f}%/yr — declining"})
    else:
        details.append({"factor": "Growth", "score": 0, "note": "Insufficient history"})

    # Payout ratio score (0–25): lower is safer
    pr = info.get("payoutRatio", None)
    if pr is not None:
        pr_pct = pr * 100
        if 20 <= pr_pct <= 60:
            score += 25; details.append({"factor": "Safety", "score": 25, "note": f"{pr_pct:.0f}% payout — safe"})
        elif pr_pct < 20:
            score += 15; details.append({"factor": "Safety", "score": 15, "note": f"{pr_pct:.0f}% payout — low (room to grow)"})
        elif 60 < pr_pct <= 80:
            score += 10; details.append({"factor": "Safety", "score": 10, "note": f"{pr_pct:.0f}% payout — elevated"})
        else:
            score += 0;  details.append({"factor": "Safety", "score": 0,  "note": f"{pr_pct:.0f}% payout — unsustainable risk"})
    else:
        details.append({"factor": "Safety", "score": 0, "note": "No payout data"})

    # Streak estimate from info
    streak = info.get("dividendRate")
    if streak:
        score += 25
        details.append({"factor": "Consistency", "score": 25, "note": "Currently paying dividends"})
    else:
        details.append({"factor": "Consistency", "score": 0, "note": "No current dividend"})

    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D" if score >= 20 else "F"
    return {"total": score, "max": max_score, "grade": grade, "details": details}


def _project_income(
    current_annual: float,
    years: int,
    growth_rate: float,
) -> List[Dict]:
    """Project dividend income over N years with assumed growth."""
    projection = []
    income = current_annual
    for y in range(1, years + 1):
        income *= (1 + growth_rate)
        projection.append({
            "year":          y,
            "annual_income": round(income, 2),
            "monthly_income": round(income / 12, 2),
        })
    return projection
