"""
Fee Drag Analyzer Service
Shows the real dollar cost of expense ratios and advisor fees over time.
"""
import numpy as np
from typing import List, Dict, Optional


def analyze_fees(
    holdings: List[Dict],      # [{"ticker": str, "name": str, "expense_ratio": float, "value": float}]
    initial_amount: float,
    years: int = 30,
    annual_return: float = 0.07,
    annual_contribution: float = 0.0,
    advisor_fee: float = 0.0,  # AUM-based advisor fee
) -> Dict:
    """
    Project portfolio growth with and without fees, showing drag in dollar terms.
    """
    # Weighted average expense ratio
    total_value = sum(h.get("value", 0) for h in holdings)
    if total_value == 0:
        # Treat all equal weight
        total_value = len(holdings) if holdings else 1
        for h in holdings:
            h["value"] = 1.0

    weighted_er = sum(
        h.get("expense_ratio", 0) * h.get("value", 0) / total_value
        for h in holdings
    )
    total_fee_rate = weighted_er + advisor_fee

    # Year-by-year projections
    gross_path = []   # no fees
    net_path = []     # with expense ratio
    comparison_path = []  # hypothetical with Vanguard-level 0.03% fees

    VANGUARD_BENCHMARK_FEE = 0.0003   # 0.03% hypothetical low-cost alternative

    pv_gross = initial_amount
    pv_net   = initial_amount
    pv_bench = initial_amount

    year_labels = list(range(0, years + 1))

    gross_path.append(round(pv_gross, 2))
    net_path.append(round(pv_net, 2))
    comparison_path.append(round(pv_bench, 2))

    for y in range(1, years + 1):
        pv_gross = pv_gross * (1 + annual_return) + annual_contribution
        pv_net   = pv_net   * (1 + annual_return - total_fee_rate) + annual_contribution
        pv_bench = pv_bench * (1 + annual_return - VANGUARD_BENCHMARK_FEE) + annual_contribution
        gross_path.append(round(pv_gross, 2))
        net_path.append(round(pv_net, 2))
        comparison_path.append(round(pv_bench, 2))

    total_fee_drag   = round(gross_path[-1] - net_path[-1], 2)
    vs_low_cost_drag = round(comparison_path[-1] - net_path[-1], 2)

    # Annual fee breakdown
    breakdown = []
    pv = initial_amount
    for y in range(1, min(years, 30) + 1):
        beginning_balance = pv * (1 + annual_return - total_fee_rate) + annual_contribution
        fee_paid_this_year = round(pv * total_fee_rate, 2)
        pv = beginning_balance
        if y <= 10 or y % 5 == 0:
            breakdown.append({
                "year": y,
                "balance": round(pv, 2),
                "fees_paid_this_year": fee_paid_this_year,
                "cumulative_opportunity_cost": round(gross_path[y] - net_path[y], 2),
            })

    # Per-holding analysis
    holding_analysis = []
    for h in holdings:
        er = h.get("expense_ratio", 0) or 0
        val = h.get("value", 0) or 0
        weight_pct = (val / total_value * 100) if total_value > 0 else 0
        annual_cost = round(val * er, 2)
        thirty_yr_drag = _single_holding_drag(val, er, annual_return, years)
        holding_analysis.append({
            "ticker":         h.get("ticker", ""),
            "name":           h.get("name", ""),
            "expense_ratio":  round(er * 100, 4),
            "value":          round(val, 2),
            "weight_pct":     round(weight_pct, 2),
            "annual_cost":    annual_cost,
            "projected_drag": thirty_yr_drag,
        })

    holding_analysis.sort(key=lambda x: x["projected_drag"], reverse=True)

    return {
        "summary": {
            "weighted_expense_ratio":  round(weighted_er * 100, 4),
            "advisor_fee":             round(advisor_fee * 100, 4),
            "total_fee_rate":          round(total_fee_rate * 100, 4),
            "initial_amount":          initial_amount,
            "years":                   years,
            "assumed_return":          round(annual_return * 100, 2),
            "gross_final_value":       gross_path[-1],
            "net_final_value":         net_path[-1],
            "total_fee_drag":          total_fee_drag,
            "fee_drag_pct":            round(total_fee_drag / gross_path[-1] * 100, 2) if gross_path[-1] else 0,
            "vs_low_cost_drag":        vs_low_cost_drag,
            "low_cost_final":          comparison_path[-1],
        },
        "chart_data": {
            "years":       year_labels,
            "gross":       gross_path,
            "net":         net_path,
            "low_cost":    comparison_path,
        },
        "breakdown":   breakdown,
        "holdings":    holding_analysis,
    }


def _single_holding_drag(value, er, r, years):
    final_with   = value * (1 + r) ** years
    final_without= value * (1 + r - er) ** years
    return round(final_with - final_without, 2)


def lookup_expense_ratios(tickers: List[str]) -> List[Dict]:
    """Fetch expense ratio info for a list of tickers from yfinance."""
    import yfinance as yf
    results = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            er_raw = info.get("annualReportExpenseRatio") or info.get("totalExpenseRatio")
            er = float(er_raw) if er_raw else None
            results.append({
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName", ticker),
                "expense_ratio": er,
                "fund_family": info.get("fundFamily"),
                "category": info.get("category"),
                "quote_type": info.get("quoteType"),
            })
        except Exception:
            results.append({"ticker": ticker, "name": ticker, "expense_ratio": None})
    return results
