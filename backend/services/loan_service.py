"""Loan & Mortgage Calculator — amortization, extra payments, rent-vs-buy, refinancing."""
import math
from typing import List, Dict, Optional


def _monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    if annual_rate <= 0:
        return principal / max(years * 12, 1)
    r = annual_rate / 100 / 12
    n = years * 12
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def _amortize(principal: float, annual_rate: float, years: int, extra: float = 0) -> List[Dict]:
    r = annual_rate / 100 / 12
    base_pmt = _monthly_payment(principal, annual_rate, years)
    balance = principal
    rows = []
    cum_interest = 0.0
    for month in range(1, years * 12 + 1):
        interest = balance * r
        principal_paid = min(base_pmt - interest + extra, balance)
        balance = max(balance - principal_paid, 0)
        cum_interest += interest
        rows.append({
            "month": month,
            "year": math.ceil(month / 12),
            "payment": round(base_pmt + extra, 2),
            "principal_paid": round(principal_paid, 2),
            "interest_paid": round(interest, 2),
            "balance": round(balance, 2),
            "cum_interest": round(cum_interest, 2),
        })
        if balance <= 0:
            break
    return rows


def analyze_loan(
    principal: float,
    annual_rate: float,
    years: int,
    extra_monthly: float = 0,
    property_value: Optional[float] = None,
    monthly_rent: Optional[float] = None,
    home_appreciation: float = 3.0,
    new_rate: Optional[float] = None,   # for refi analysis
    closing_costs: float = 0,
) -> Dict:
    monthly = _monthly_payment(principal, annual_rate, years)
    schedule = _amortize(principal, annual_rate, years, extra_monthly)
    base_schedule = _amortize(principal, annual_rate, years, 0)

    total_paid = sum(r["payment"] for r in schedule)
    total_interest = sum(r["interest_paid"] for r in schedule)
    base_interest = sum(r["interest_paid"] for r in base_schedule)
    interest_saved = round(base_interest - total_interest, 2)
    months_saved = len(base_schedule) - len(schedule)

    # Yearly summary for chart (year-end balance)
    yearly = {}
    for row in schedule:
        yearly[row["year"]] = {"year": row["year"], "balance": row["balance"], "cum_interest": row["cum_interest"]}
    yearly_list = list(yearly.values())

    result: Dict = {
        "monthly_payment": round(monthly, 2),
        "monthly_with_extra": round(monthly + extra_monthly, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "payoff_months": len(schedule),
        "payoff_years": round(len(schedule) / 12, 1),
        "months_saved": months_saved,
        "interest_saved": interest_saved,
        "schedule": schedule,
        "yearly": yearly_list,
    }

    # Rent vs Buy
    if property_value and monthly_rent:
        yrs = len(schedule) / 12
        down_payment = property_value - principal
        maintenance = property_value * 0.01 * yrs
        prop_val_end = property_value * (1 + home_appreciation / 100) ** yrs
        equity = prop_val_end - schedule[-1]["balance"]
        net_cost_buy = down_payment + total_paid + maintenance - (prop_val_end - property_value)
        net_cost_rent = monthly_rent * 12 * yrs

        result["rent_vs_buy"] = {
            "home_value_end": round(prop_val_end, 0),
            "equity_built": round(equity, 0),
            "net_cost_buy": round(net_cost_buy, 0),
            "net_cost_rent": round(net_cost_rent, 0),
            "advantage": round(net_cost_rent - net_cost_buy, 0),
        }

    # Refinancing break-even
    if new_rate is not None and closing_costs >= 0:
        current_remaining = base_schedule  # full term at old rate
        remaining_months = len(current_remaining)
        remaining_principal = principal  # simplified: use original for comparison
        old_monthly = monthly
        new_monthly = _monthly_payment(principal, new_rate, years)
        monthly_savings = old_monthly - new_monthly
        if monthly_savings > 0:
            breakeven_months = math.ceil(closing_costs / monthly_savings)
        else:
            breakeven_months = None
        result["refinance"] = {
            "new_monthly": round(new_monthly, 2),
            "monthly_savings": round(monthly_savings, 2),
            "closing_costs": round(closing_costs, 2),
            "breakeven_months": breakeven_months,
            "breakeven_years": round(breakeven_months / 12, 1) if breakeven_months else None,
            "worthwhile": breakeven_months is not None and breakeven_months < remaining_months,
        }

    return result
