"""Dollar-Cost Averaging vs Lump Sum backtester."""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from services.data_service import fetch_price_data, current_year


def simulate_dca(
    ticker: str,
    monthly_amount: float,
    start_year: int,
    end_year: Optional[int] = None,
) -> Dict:
    end_y = end_year or current_year()
    prices = fetch_price_data([ticker], start_year, end_y, frequency="M")

    if ticker not in prices.columns:
        raise ValueError(f"No price data for {ticker}")

    price_series = prices[ticker].dropna()
    if len(price_series) < 2:
        raise ValueError("Not enough price data for the selected range")

    total_investment = monthly_amount * len(price_series)

    # ── DCA: buy $monthly_amount every month ──
    dca_shares = 0.0
    dca_cost = 0.0
    dca_history = []

    for date, price in price_series.items():
        shares = monthly_amount / price
        dca_shares += shares
        dca_cost += monthly_amount
        dca_history.append({
            "date": date.strftime("%Y-%m"),
            "value": round(dca_shares * price, 2),
            "invested": round(dca_cost, 2),
        })

    dca_final = dca_shares * price_series.iloc[-1]

    # ── Lump Sum: invest all upfront ──
    ls_shares = total_investment / price_series.iloc[0]
    ls_history = []
    for date, price in price_series.items():
        ls_history.append({
            "date": date.strftime("%Y-%m"),
            "value": round(ls_shares * price, 2),
        })
    ls_final = ls_shares * price_series.iloc[-1]

    # ── Annual return stats ──
    monthly_returns = price_series.pct_change().dropna()
    annual_return = (1 + monthly_returns.mean()) ** 12 - 1
    annual_vol = monthly_returns.std() * np.sqrt(12)

    return {
        "ticker": ticker,
        "start_year": start_year,
        "end_year": end_y,
        "months": len(price_series),
        "monthly_amount": monthly_amount,
        "total_invested": round(total_investment, 2),
        "dca": {
            "final_value": round(dca_final, 2),
            "total_return_pct": round((dca_final / total_investment - 1) * 100, 2),
            "history": dca_history,
        },
        "lump_sum": {
            "final_value": round(ls_final, 2),
            "total_return_pct": round((ls_final / total_investment - 1) * 100, 2),
            "history": ls_history,
        },
        "dca_wins": bool(dca_final > ls_final),
        "asset_stats": {
            "annual_return_pct": round(annual_return * 100, 2),
            "annual_volatility_pct": round(annual_vol * 100, 2),
        },
    }
