"""
Historical Stress Test Service
Tests portfolio performance against named historical crisis scenarios.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from services.data_service import fetch_price_data, fetch_returns

logger = logging.getLogger(__name__)

# Named scenarios: (label, start_date, end_date, description)
SCENARIOS = [
    {
        "id": "dotcom",
        "label": "Dot-Com Crash",
        "start": "2000-03-01",
        "end":   "2002-10-31",
        "description": "NASDAQ fell 78%. S&P 500 dropped 49%. Lasted 2.5 years.",
        "spy_return": -0.491,
    },
    {
        "id": "gfc",
        "label": "2008 Global Financial Crisis",
        "start": "2007-10-01",
        "end":   "2009-03-31",
        "description": "S&P 500 fell 57%. Worst crisis since Great Depression.",
        "spy_return": -0.569,
    },
    {
        "id": "covid",
        "label": "COVID-19 Crash",
        "start": "2020-02-01",
        "end":   "2020-03-31",
        "description": "Fastest 30% decline in market history. Recovered in 5 months.",
        "spy_return": -0.338,
    },
    {
        "id": "rate_hike_2022",
        "label": "2022 Rate Hike Bear Market",
        "start": "2022-01-01",
        "end":   "2022-12-31",
        "description": "Fed raised rates 425bps. S&P -19%, Bonds -13%. Nowhere to hide.",
        "spy_return": -0.196,
    },
    {
        "id": "black_monday",
        "label": "1987 Black Monday",
        "start": "1987-08-01",
        "end":   "1987-12-31",
        "description": "Dow fell 22.6% in a single day (Oct 19). Worst single-day crash.",
        "spy_return": -0.338,
    },
    {
        "id": "stagflation_70s",
        "label": "1970s Stagflation",
        "start": "1973-01-01",
        "end":   "1974-12-31",
        "description": "Oil embargo + inflation. S&P fell 48% in real terms.",
        "spy_return": -0.421,
    },
    {
        "id": "flash_crash_2010",
        "label": "2010 Flash Crash Recovery",
        "start": "2010-04-01",
        "end":   "2010-07-31",
        "description": "Dow dropped 1,000 points intraday. Market-wide liquidity shock.",
        "spy_return": -0.143,
    },
    {
        "id": "eu_debt",
        "label": "European Debt Crisis",
        "start": "2011-05-01",
        "end":   "2011-10-31",
        "description": "Greece, Ireland, Portugal debt contagion fears. S&P fell 19%.",
        "spy_return": -0.189,
    },
]


def run_stress_test(
    allocations: List[Dict],  # [{"ticker": "SPY", "weight": 60}, ...]
    initial_amount: float = 100000,
    scenario_ids: Optional[List[str]] = None,
) -> Dict:
    """
    For each scenario, compute portfolio return, dollar loss, and recovery time.
    """
    tickers = [a["ticker"] for a in allocations]
    weights = np.array([a["weight"] / 100.0 for a in allocations])

    scenarios_to_run = [s for s in SCENARIOS if scenario_ids is None or s["id"] in scenario_ids]
    results = []

    for scenario in scenarios_to_run:
        try:
            start_year = int(scenario["start"][:4])
            end_year   = int(scenario["end"][:4]) + 1   # fetch one extra year for recovery

            prices = fetch_price_data(tickers, start_year, end_year, frequency="M")

            # Filter to scenario window
            start_dt = pd.Timestamp(scenario["start"])
            end_dt   = pd.Timestamp(scenario["end"])

            scenario_prices = prices[(prices.index >= start_dt) & (prices.index <= end_dt)]
            available_tickers = [t for t in tickers if t in scenario_prices.columns]

            if scenario_prices.empty or len(available_tickers) == 0:
                results.append(_unavailable_scenario(scenario, initial_amount))
                continue

            # Reindex weights for available tickers
            avail_idx = [tickers.index(t) for t in available_tickers]
            avail_weights = weights[avail_idx]
            if avail_weights.sum() > 0:
                avail_weights = avail_weights / avail_weights.sum()

            s_prices = scenario_prices[available_tickers]
            s_returns = s_prices.pct_change().dropna()

            if s_returns.empty:
                results.append(_unavailable_scenario(scenario, initial_amount))
                continue

            portfolio_returns = s_returns.dot(avail_weights)
            cumulative = (1 + portfolio_returns).cumprod()
            total_return = float(cumulative.iloc[-1] - 1)
            max_dd = float(_max_drawdown(cumulative))
            dollar_loss = initial_amount * total_return
            dollar_at_bottom = initial_amount * (1 + max_dd)

            # Recovery: how many months after scenario end until recovery?
            recovery_months = _estimate_recovery(
                tickers, available_tickers, avail_idx, weights, avail_weights,
                end_dt, end_year + 3, max_dd
            )

            # Monthly path for chart
            path = [{"date": str(d.date()), "value": round(initial_amount * c, 2)}
                    for d, c in zip(cumulative.index, cumulative.values)]

            results.append({
                "scenario_id":       scenario["id"],
                "label":             scenario["label"],
                "description":       scenario["description"],
                "period":            f"{scenario['start'][:7]} → {scenario['end'][:7]}",
                "portfolio_return":  round(total_return * 100, 2),
                "max_drawdown":      round(max_dd * 100, 2),
                "dollar_change":     round(dollar_loss, 2),
                "dollar_at_bottom":  round(dollar_at_bottom, 2),
                "spy_return":        round(scenario["spy_return"] * 100, 2),
                "recovery_months":   recovery_months,
                "available":         True,
                "path":              path,
            })

        except Exception as e:
            logger.warning("Stress test error for %s: %s", scenario["id"], e)
            results.append(_unavailable_scenario(scenario, initial_amount))

    return {
        "scenarios": results,
        "initial_amount": initial_amount,
        "tickers": tickers,
    }


def _max_drawdown(cumulative: pd.Series) -> float:
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    return float(drawdown.min())


def _estimate_recovery(tickers, available_tickers, avail_idx, weights, avail_weights,
                        crash_end: pd.Timestamp, look_years: int, max_dd: float) -> Optional[int]:
    """Estimate months to recovery after crash bottom."""
    if max_dd >= -0.01:
        return 0
    try:
        prices = fetch_price_data(available_tickers, crash_end.year, look_years, frequency="M")
        prices = prices[prices.index >= crash_end]
        if prices.empty:
            return None
        rets = prices.pct_change().dropna()
        portfolio_rets = rets.dot(avail_weights)
        cumulative = (1 + portfolio_rets).cumprod()
        # Recovery = when cumulative crosses pre-crash level (1.0 relative to crash end)
        # We approximate: recovery when cumulative > (1 / (1 + max_dd))
        recovery_threshold = 1 / (1 + max_dd)
        recovered = cumulative[cumulative >= recovery_threshold]
        if recovered.empty:
            return None
        first_recovery = recovered.index[0]
        months = max(1, int((first_recovery - crash_end).days / 30))
        return months
    except Exception:
        return None


def _unavailable_scenario(scenario: Dict, initial_amount: float) -> Dict:
    return {
        "scenario_id":      scenario["id"],
        "label":            scenario["label"],
        "description":      scenario["description"],
        "period":           f"{scenario['start'][:7]} → {scenario['end'][:7]}",
        "portfolio_return": None,
        "max_drawdown":     None,
        "dollar_change":    None,
        "dollar_at_bottom": None,
        "spy_return":       round(scenario["spy_return"] * 100, 2),
        "recovery_months":  None,
        "available":        False,
        "path":             [],
    }
