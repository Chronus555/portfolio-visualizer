"""Roth vs Traditional IRA & Roth Conversion Optimizer."""
import math
from typing import Dict, List


TAX_BRACKETS_2024 = [
    (11600,  0.10),
    (47150,  0.12),
    (100525, 0.22),
    (191950, 0.24),
    (243725, 0.32),
    (609350, 0.35),
    (float('inf'), 0.37),
]


def marginal_rate(income: float) -> float:
    prev = 0.0
    for ceiling, rate in TAX_BRACKETS_2024:
        if income <= ceiling:
            return rate
        prev = ceiling
    return 0.37


def effective_rate(income: float) -> float:
    tax = 0.0
    prev = 0.0
    for ceiling, rate in TAX_BRACKETS_2024:
        taxable = min(income, ceiling) - prev
        if taxable <= 0:
            break
        tax += taxable * rate
        prev = ceiling
        if income <= ceiling:
            break
    return tax / income if income > 0 else 0.0


def compare_roth_vs_traditional(
    current_income: float,
    retirement_income: float,
    annual_contribution: float,
    years_to_retirement: int,
    years_in_retirement: int,
    expected_return: float,
) -> Dict:
    r = expected_return / 100

    # Future value of contributions
    fv = annual_contribution * ((1 + r) ** years_to_retirement - 1) / r if r > 0 else annual_contribution * years_to_retirement

    current_marginal = marginal_rate(current_income)
    current_effective = effective_rate(current_income)
    retirement_marginal = marginal_rate(retirement_income)

    # Traditional: pay tax on withdrawal
    trad_pre_tax = fv  # grows pre-tax
    trad_after_tax = fv * (1 - retirement_marginal)

    # Roth: pay tax now on contributions (contributions are post-tax)
    roth_contribution = annual_contribution * (1 - current_marginal)
    roth_fv = roth_contribution * ((1 + r) ** years_to_retirement - 1) / r if r > 0 else roth_contribution * years_to_retirement
    roth_after_tax = roth_fv  # grows and withdraws tax-free

    # Annual retirement income from each
    withdrawal_rate = 1 / years_in_retirement  # simplified
    trad_annual = trad_after_tax * withdrawal_rate
    roth_annual = roth_after_tax * withdrawal_rate

    # Yearly projection
    yearly = []
    trad_bal = 0.0
    roth_bal = 0.0
    for yr in range(1, years_to_retirement + 1):
        trad_bal = (trad_bal + annual_contribution) * (1 + r)
        roth_bal = (roth_bal + annual_contribution * (1 - current_marginal)) * (1 + r)
        yearly.append({
            "year": yr,
            "traditional_balance": round(trad_bal, 0),
            "roth_balance": round(roth_bal, 0),
            "traditional_after_tax": round(trad_bal * (1 - retirement_marginal), 0),
            "roth_after_tax": round(roth_bal, 0),
        })

    winner = "Roth" if roth_after_tax > trad_after_tax else "Traditional"

    return {
        "current_marginal_rate": round(current_marginal * 100, 1),
        "current_effective_rate": round(current_effective * 100, 1),
        "retirement_marginal_rate": round(retirement_marginal * 100, 1),
        "traditional": {
            "pre_tax_balance": round(trad_pre_tax, 0),
            "after_tax_balance": round(trad_after_tax, 0),
            "annual_retirement_income": round(trad_annual, 0),
        },
        "roth": {
            "balance": round(roth_fv, 0),
            "after_tax_balance": round(roth_after_tax, 0),
            "annual_retirement_income": round(roth_annual, 0),
        },
        "winner": winner,
        "roth_advantage": round(roth_after_tax - trad_after_tax, 0),
        "yearly": yearly,
    }


def optimize_roth_conversion(
    trad_balance: float,
    current_income: float,
    top_bracket_ceiling: float,
    expected_return: float,
    years_to_retirement: int,
    retirement_rate: float,
) -> Dict:
    """Find optimal annual conversion amount to fill up to a target bracket."""
    r = expected_return / 100
    conversion_space = max(0, top_bracket_ceiling - current_income)

    # If we convert the full space, what's the tax bill?
    tax_on_conversion = conversion_space * marginal_rate(current_income + conversion_space)
    fv_converted = conversion_space * (1 + r) ** years_to_retirement
    fv_not_converted = conversion_space * (1 + r) ** years_to_retirement * (1 - retirement_rate / 100)

    # Yearly conversion plan
    remaining = trad_balance
    plan = []
    for yr in range(1, years_to_retirement + 1):
        convert = min(conversion_space, remaining)
        tax = convert * marginal_rate(current_income + convert)
        remaining -= convert
        plan.append({
            "year": yr,
            "convert_amount": round(convert, 0),
            "tax_due": round(tax, 0),
            "remaining_traditional": round(remaining, 0),
        })
        if remaining <= 0:
            break

    return {
        "annual_conversion_space": round(conversion_space, 0),
        "tax_on_conversion": round(tax_on_conversion, 0),
        "fv_roth_tax_free": round(fv_converted, 0),
        "fv_trad_after_tax": round(fv_not_converted, 0),
        "roth_advantage": round(fv_converted - fv_not_converted, 0),
        "conversion_plan": plan,
        "years_to_convert": len(plan),
    }
