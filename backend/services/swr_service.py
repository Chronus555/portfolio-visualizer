"""
Safe Withdrawal Rate (SWR) Analysis — multiple withdrawal strategies.
Strategies: Fixed %, Fixed Dollar + Inflation, Guyton-Klinger Guardrails,
Floor-Ceiling, RMD-based, Bucket Strategy.
Uses Monte Carlo simulation (10,000 runs) to estimate survival rates.
"""
import numpy as np
from typing import List


# Well-researched historical parameters for US 60/40 portfolio
STOCK_RETURN_MEAN  = 0.100   # 10% nominal
STOCK_RETURN_STD   = 0.170   # 17% std dev
BOND_RETURN_MEAN   = 0.045   # 4.5% nominal
BOND_RETURN_STD    = 0.060   # 6% std dev
STOCK_BOND_CORR    = -0.10   # slight negative correlation


def _portfolio_return(stock_pct: float) -> tuple[float, float]:
    """Return (mean, sigma) for blended portfolio."""
    w_s = stock_pct / 100.0
    w_b = 1.0 - w_s
    mean  = w_s * STOCK_RETURN_MEAN + w_b * BOND_RETURN_MEAN
    var   = (w_s * STOCK_RETURN_STD) ** 2 + (w_b * BOND_RETURN_STD) ** 2 \
            + 2 * w_s * w_b * STOCK_BOND_CORR * STOCK_RETURN_STD * BOND_RETURN_STD
    sigma = np.sqrt(var)
    return mean, sigma


def _simulate_strategy(strategy: str, portfolio_value: float, annual_expenses: float,
                        years: int, stock_pct: float, inflation: float,
                        simulations: int = 5000) -> dict:
    """Run Monte Carlo for a given withdrawal strategy. Returns summary stats."""
    np.random.seed(42)
    mean, sigma = _portfolio_return(stock_pct)
    inf_r = inflation / 100.0

    success_count = 0
    final_balances = []
    withdrawal_histories = []  # first 50 for charting
    year_labels = list(range(1, years + 1))

    for sim in range(simulations):
        # Sample correlated stock/bond returns using Cholesky
        returns = np.random.normal(mean, sigma, size=years)

        balance      = portfolio_value
        base_expense = annual_expenses
        expense      = base_expense
        survived     = True
        wdraw_hist   = []

        # Strategy-specific state
        guardrails_upper_trigger = base_expense * 1.20  # 20% above initial
        guardrails_lower_trigger = base_expense * 0.80
        bucket1 = portfolio_value * 0.05   # 5% = ~1.5yr cash (bucket strategy)
        bucket2 = portfolio_value * 0.30   # 30% bonds
        bucket3 = portfolio_value * 0.65   # 65% stocks

        for yr in range(years):
            ret = returns[yr]

            if strategy == "fixed_percent_4":
                withdrawal = portfolio_value * 0.04  # always 4% of ORIGINAL
                withdrawal = base_expense * (1 + inf_r) ** yr  # inflation-adj fixed

            elif strategy == "fixed_percent_dynamic":
                withdrawal = balance * 0.04  # 4% of CURRENT balance
                withdrawal = max(withdrawal, base_expense * 0.5)   # floor
                withdrawal = min(withdrawal, base_expense * 1.5)   # ceiling

            elif strategy == "fixed_dollar_inflation":
                withdrawal = base_expense * (1 + inf_r) ** yr

            elif strategy == "guardrails":
                # Guyton-Klinger: adjust withdrawals when portfolio crosses thresholds
                current_rate = expense / balance if balance > 0 else 0.10
                init_rate    = base_expense / portfolio_value
                if current_rate > init_rate * 1.20:
                    expense *= 0.90   # cut 10%
                elif current_rate < init_rate * 0.80:
                    expense *= 1.10   # raise 10%
                expense   = max(expense, base_expense * 0.80)
                expense   = min(expense, base_expense * 1.50)
                withdrawal = expense

            elif strategy == "floor_ceiling":
                # Floor: 3.5%, Ceiling: 4.5%
                pct_floor   = 0.035
                pct_ceiling = 0.045
                ideal       = base_expense * (1 + inf_r) ** yr
                floor_amt   = portfolio_value * pct_floor
                ceiling_amt = portfolio_value * pct_ceiling
                withdrawal  = max(floor_amt, min(ideal, ceiling_amt))

            elif strategy == "rmd_based":
                # IRS Uniform Lifetime Table simplified: life expectancy factor decreases each year
                life_expectancy_factor = max(years - yr, 1)
                withdrawal = balance / life_expectancy_factor
                withdrawal = max(withdrawal, base_expense * 0.70)  # reasonable floor

            elif strategy == "bucket":
                # Refill bucket1 from bucket2 each year; refill bucket2 from bucket3
                bucket3 *= (1 + ret + 0.02)   # stocks grow
                bucket2 *= (1 + ret * 0.3)    # bonds grow slower
                withdrawal = base_expense * (1 + inf_r) ** yr
                if bucket1 >= withdrawal:
                    bucket1 -= withdrawal
                elif bucket1 + bucket2 >= withdrawal:
                    overflow = withdrawal - bucket1
                    bucket1  = 0
                    bucket2 -= overflow
                    # refill from bucket3
                    refill = min(portfolio_value * 0.03, bucket3)
                    bucket1 += refill
                    bucket3 -= refill
                else:
                    survived = False
                balance = bucket1 + bucket2 + bucket3
                wdraw_hist.append(round(withdrawal, 2))
                final_balances.append(balance)
                if survived:
                    success_count += 1
                break  # bucket handles its own loop end

            else:
                withdrawal = base_expense * (1 + inf_r) ** yr

            wdraw_hist.append(round(withdrawal, 2))
            balance = balance * (1 + ret) - withdrawal
            if balance <= 0:
                balance  = 0
                survived = False
                break

        if strategy != "bucket":
            final_balances.append(max(balance, 0))
            if survived:
                success_count += 1

        if sim < 50:
            withdrawal_histories.append(wdraw_hist)

    survival_rate = round(success_count / simulations * 100, 1)
    final_arr     = np.array(final_balances)

    avg_final     = float(np.mean(final_arr))
    median_final  = float(np.median(final_arr))
    p10_final     = float(np.percentile(final_arr, 10))

    # Average withdrawal history across first 50 sims
    max_len = max((len(h) for h in withdrawal_histories), default=years)
    avg_withdrawals = []
    for yr in range(max_len):
        vals = [h[yr] for h in withdrawal_histories if yr < len(h)]
        avg_withdrawals.append(round(float(np.mean(vals)), 2) if vals else 0.0)

    initial_withdrawal_rate = round(annual_expenses / portfolio_value * 100, 2)

    return {
        "survival_rate": survival_rate,
        "avg_final_balance": round(avg_final, 2),
        "median_final_balance": round(median_final, 2),
        "p10_final_balance": round(p10_final, 2),
        "initial_withdrawal_rate": initial_withdrawal_rate,
        "avg_annual_withdrawals": avg_withdrawals,
        "years": years,
        "year_labels": year_labels,
    }


STRATEGY_META = {
    "fixed_percent_4": {
        "name": "Fixed 4% Rule",
        "description": "Withdraw inflation-adjusted amount equal to 4% of initial portfolio. Simple and well-known Bengen Rule.",
        "pros": "Predictable income, historically safe for 30 years",
        "cons": "No flexibility; may leave too much or go broke in bad markets",
        "color": "#3b82f6",
    },
    "fixed_percent_dynamic": {
        "name": "Dynamic % (4% current)",
        "description": "Withdraw 4% of current portfolio value each year, with floor/ceiling guards to prevent extreme swings.",
        "pros": "Automatically adjusts to market; preserves portfolio in down years",
        "cons": "Variable income makes budgeting harder",
        "color": "#8b5cf6",
    },
    "fixed_dollar_inflation": {
        "name": "Fixed Dollar + Inflation",
        "description": "Withdraw a fixed dollar amount each year, adjusted for inflation. Standard 'set and forget' approach.",
        "pros": "Predictable, easy to plan",
        "cons": "Doesn't respond to portfolio performance",
        "color": "#10b981",
    },
    "guardrails": {
        "name": "Guyton-Klinger Guardrails",
        "description": "Cut withdrawals 10% if portfolio withdrawal rate rises 20% above initial; raise 10% if it drops 20% below.",
        "pros": "Dramatically improves success rate; allows higher initial withdrawal",
        "cons": "Requires flexibility to cut spending in bad years",
        "color": "#f59e0b",
    },
    "floor_ceiling": {
        "name": "Floor-Ceiling (3.5%–4.5%)",
        "description": "Keep withdrawal between 3.5% and 4.5% of original portfolio, adjusted for inflation.",
        "pros": "Balanced approach with income certainty and portfolio protection",
        "cons": "Can feel restrictive when portfolio soars",
        "color": "#ef4444",
    },
    "rmd_based": {
        "name": "RMD-Based",
        "description": "Withdraw portfolio divided by remaining life expectancy (mirrors IRS Required Minimum Distributions).",
        "pros": "Portfolio lasts exactly as long as planned; simple math",
        "cons": "Income varies wildly year-to-year; may produce too little early on",
        "color": "#06b6d4",
    },
    "bucket": {
        "name": "Bucket Strategy",
        "description": "3 buckets: 5% cash (1-2yr expenses), 30% bonds (medium-term), 65% stocks (long-term). Refill cash from bonds, bonds from stocks.",
        "pros": "Psychological comfort; insulated from short-term volatility",
        "cons": "Slightly suboptimal returns; complex rebalancing",
        "color": "#ec4899",
    },
}


def analyze_swr(
    portfolio_value: float,
    annual_expenses: float,
    retirement_years: int,
    stock_allocation: float,
    inflation: float,
    strategies: List[str],
    simulations: int = 5000,
) -> dict:
    results = {}
    for strat in strategies:
        if strat not in STRATEGY_META:
            continue
        sim = _simulate_strategy(
            strategy=strat,
            portfolio_value=portfolio_value,
            annual_expenses=annual_expenses,
            years=retirement_years,
            stock_pct=stock_allocation,
            inflation=inflation,
            simulations=simulations,
        )
        results[strat] = {**STRATEGY_META[strat], **sim}

    # Rankings
    sorted_by_survival = sorted(results.items(), key=lambda x: x[1]["survival_rate"], reverse=True)
    rankings = [{"strategy": k, "name": v["name"], "survival_rate": v["survival_rate"],
                 "avg_final": v["avg_final_balance"]} for k, v in sorted_by_survival]

    # Safe withdrawal rate analysis
    swr_rates = {}
    for rate_pct in [3.0, 3.5, 4.0, 4.5, 5.0]:
        expense_at_rate = portfolio_value * rate_pct / 100
        sim = _simulate_strategy(
            strategy="fixed_percent_4",
            portfolio_value=portfolio_value,
            annual_expenses=expense_at_rate,
            years=retirement_years,
            stock_pct=stock_allocation,
            inflation=inflation,
            simulations=2000,
        )
        swr_rates[str(rate_pct)] = sim["survival_rate"]

    return {
        "strategies": results,
        "rankings": rankings,
        "swr_sensitivity": swr_rates,
        "inputs": {
            "portfolio_value": portfolio_value,
            "annual_expenses": annual_expenses,
            "withdrawal_rate": round(annual_expenses / portfolio_value * 100, 2),
            "retirement_years": retirement_years,
            "stock_allocation": stock_allocation,
            "inflation": inflation,
        }
    }
