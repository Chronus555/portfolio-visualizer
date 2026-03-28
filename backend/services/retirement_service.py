"""
Retirement Planner — Monte Carlo simulation with sequence-of-returns risk analysis.
"""
import numpy as np
from typing import Optional


def run_retirement_plan(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    annual_contribution: float,
    expected_return: float,          # % nominal
    volatility: float,               # % std dev
    inflation: float,                # % annual
    annual_expenses_in_retirement: float,
    life_expectancy: int,
    contribution_growth: float = 2.0, # % annual raise on contributions
    simulations: int = 1000,
    social_security: float = 0.0,     # annual SS benefit at retirement
) -> dict:
    np.random.seed(None)
    simulations = int(simulations)

    accumulation_years = int(retirement_age - current_age)
    withdrawal_years   = int(life_expectancy - retirement_age)

    r_mean  = expected_return / 100.0
    r_sigma = volatility / 100.0
    inf_r   = inflation / 100.0
    ss_real = social_security  # already in today's dollars

    # ── Accumulation phase ──────────────────────────────────────────────────
    # For accumulation we use deterministic (expected return) for the median
    # projection, but add Monte Carlo noise for the distribution.

    final_balances = []
    success_count  = 0
    all_paths_retire = []   # sampled 100 paths for charting
    all_paths_full   = []

    for sim in range(simulations):
        # Accumulation
        balance = float(current_savings)
        contrib = float(annual_contribution)
        for yr in range(accumulation_years):
            ret = float(np.clip(np.random.normal(r_mean, r_sigma), -0.60, 0.60))
            balance = balance * (1 + ret) + contrib
            contrib *= (1 + contribution_growth / 100.0)
        balance_at_retirement = balance

        # Withdrawal (inflation-adjusted expenses, net of SS)
        net_expense = max(annual_expenses_in_retirement - ss_real, 0)
        expense = net_expense
        survived = True
        path = [balance_at_retirement]
        for yr in range(withdrawal_years):
            ret = float(np.clip(np.random.normal(r_mean - 0.5 * r_sigma ** 2, r_sigma), -0.60, 0.60))
            balance = balance * (1 + ret) - expense
            expense *= (1 + inf_r)
            if balance <= 0:
                balance = 0
                survived = False
                # fill rest with 0
                path.extend([0] * (withdrawal_years - yr - 1))
                break
            path.append(balance)

        final_balances.append(balance_at_retirement)
        if survived:
            success_count += 1
        if sim < 100:
            all_paths_full.append(path)

    # ── Percentile bands ────────────────────────────────────────────────────
    final_balances = np.array(final_balances)
    p10 = float(np.percentile(final_balances, 10))
    p25 = float(np.percentile(final_balances, 25))
    p50 = float(np.percentile(final_balances, 50))
    p75 = float(np.percentile(final_balances, 75))
    p90 = float(np.percentile(final_balances, 90))

    # ── Deterministic accumulation path for chart ────────────────────────────
    accum_path = []
    balance = float(current_savings)
    contrib = float(annual_contribution)
    for yr in range(accumulation_years + 1):
        accum_path.append({
            "age": current_age + yr,
            "year": yr,
            "balance": round(balance, 2),
        })
        if yr < accumulation_years:
            balance = balance * (1 + r_mean) + contrib
            contrib *= (1 + contribution_growth / 100.0)

    # ── Deterministic withdrawal paths (optimistic / median / pessimistic) ──
    def det_withdrawal(annual_return_override):
        bal   = p50
        exp   = max(annual_expenses_in_retirement - ss_real, 0)
        pts   = []
        for yr in range(withdrawal_years + 1):
            pts.append({"age": retirement_age + yr, "year": yr, "balance": round(max(bal, 0), 2)})
            if yr < withdrawal_years:
                bal = bal * (1 + annual_return_override / 100.0) - exp
                exp *= (1 + inf_r)
        return pts

    withdrawal_median      = det_withdrawal(expected_return)
    withdrawal_optimistic  = det_withdrawal(expected_return + volatility)
    withdrawal_pessimistic = det_withdrawal(expected_return - volatility)

    # ── Withdrawal percentile paths from MC ─────────────────────────────────
    # Run quick 500-sim withdrawal phase from median retirement balance
    wdraw_paths = []
    for _ in range(500):
        bal = p50
        exp = max(annual_expenses_in_retirement - ss_real, 0)
        path = [round(bal, 2)]
        for yr in range(withdrawal_years):
            ret = float(np.clip(np.random.normal(r_mean - 0.5 * r_sigma ** 2, r_sigma), -0.60, 0.60))
            bal = bal * (1 + ret) - exp
            exp *= (1 + inf_r)
            path.append(round(max(bal, 0), 2))
        wdraw_paths.append(path)
    wdraw_arr = np.array(wdraw_paths)
    wdraw_p10 = np.percentile(wdraw_arr, 10, axis=0).tolist()
    wdraw_p25 = np.percentile(wdraw_arr, 25, axis=0).tolist()
    wdraw_p50 = np.percentile(wdraw_arr, 50, axis=0).tolist()
    wdraw_p75 = np.percentile(wdraw_arr, 75, axis=0).tolist()
    wdraw_p90 = np.percentile(wdraw_arr, 90, axis=0).tolist()

    ages_withdrawal = [retirement_age + y for y in range(withdrawal_years + 1)]

    # ── Sequence-of-returns risk ─────────────────────────────────────────────
    # Compare early-bad vs late-bad returns
    def sor_scenario(bad_years_early: bool):
        """Simulate 10 years of bad returns then good, or vice versa."""
        bal = p50
        exp = max(annual_expenses_in_retirement - ss_real, 0)
        path = [round(bal, 2)]
        bad_ret  = (r_mean - 1.5 * r_sigma)
        good_ret = (r_mean + 0.5 * r_sigma)
        for yr in range(withdrawal_years):
            if bad_years_early:
                ret = bad_ret if yr < 5 else good_ret
            else:
                ret = good_ret if yr < (withdrawal_years - 5) else bad_ret
            bal = bal * (1 + ret) - exp
            exp *= (1 + inf_r)
            path.append(round(max(bal, 0), 2))
        return path

    sor_bad_early = sor_scenario(True)
    sor_bad_late  = sor_scenario(False)

    # ── Summary metrics ─────────────────────────────────────────────────────
    prob_success  = round(success_count / simulations * 100, 1)
    years_to_retire = accumulation_years

    # How much you need (25× rule / target)
    target_nest_egg = max(annual_expenses_in_retirement - ss_real, 0) * 25
    on_track_pct    = round(p50 / target_nest_egg * 100, 1) if target_nest_egg > 0 else 100.0

    total_contributions = (annual_contribution * accumulation_years)  # simplified
    investment_growth   = max(p50 - current_savings - total_contributions, 0)

    return {
        "summary": {
            "probability_of_success": prob_success,
            "median_retirement_balance": round(p50, 2),
            "target_nest_egg": round(target_nest_egg, 2),
            "on_track_pct": on_track_pct,
            "years_to_retirement": years_to_retire,
            "withdrawal_years": withdrawal_years,
            "annual_retirement_income": round(annual_expenses_in_retirement, 2),
            "net_annual_expense": round(max(annual_expenses_in_retirement - ss_real, 0), 2),
            "total_contributions_est": round(total_contributions, 2),
            "investment_growth_est": round(investment_growth, 2),
        },
        "retirement_balance_percentiles": {
            "p10": round(p10, 2),
            "p25": round(p25, 2),
            "p50": round(p50, 2),
            "p75": round(p75, 2),
            "p90": round(p90, 2),
        },
        "accumulation_path": accum_path,
        "withdrawal_chart": {
            "ages": ages_withdrawal,
            "p10": [round(v, 2) for v in wdraw_p10],
            "p25": [round(v, 2) for v in wdraw_p25],
            "p50": [round(v, 2) for v in wdraw_p50],
            "p75": [round(v, 2) for v in wdraw_p75],
            "p90": [round(v, 2) for v in wdraw_p90],
        },
        "sequence_of_returns": {
            "ages": ages_withdrawal,
            "bad_early": [round(v, 2) for v in sor_bad_early],
            "bad_late":  [round(v, 2) for v in sor_bad_late],
            "median":    [round(v, 2) for v in wdraw_p50],
        },
        "inputs": {
            "current_age": current_age,
            "retirement_age": retirement_age,
            "life_expectancy": life_expectancy,
            "current_savings": current_savings,
            "annual_contribution": annual_contribution,
            "expected_return": expected_return,
            "volatility": volatility,
            "inflation": inflation,
            "annual_expenses_in_retirement": annual_expenses_in_retirement,
            "social_security": social_security,
            "simulations": simulations,
        }
    }
