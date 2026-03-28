"""
Savings Goal Planner — project multiple financial goals simultaneously.
Goals: retirement, house down payment, emergency fund, college, custom.
"""
import numpy as np
from typing import List, Dict


GOAL_ICONS = {
    "retirement":    "🏖️",
    "house":         "🏠",
    "emergency":     "🛡️",
    "college":       "🎓",
    "car":           "🚗",
    "vacation":      "✈️",
    "business":      "💼",
    "wedding":       "💍",
    "custom":        "🎯",
}

GOAL_COLORS = {
    "retirement": "#3b82f6",
    "house":      "#10b981",
    "emergency":  "#f59e0b",
    "college":    "#8b5cf6",
    "car":        "#ef4444",
    "vacation":   "#06b6d4",
    "business":   "#ec4899",
    "wedding":    "#f97316",
    "custom":     "#6b7280",
}


def _future_value(current: float, monthly_contribution: float,
                  annual_return: float, months: int) -> float:
    """Future value of lump sum + annuity."""
    r = annual_return / 100.0 / 12
    if r == 0:
        return current + monthly_contribution * months
    fv_lump    = current * (1 + r) ** months
    fv_annuity = monthly_contribution * ((1 + r) ** months - 1) / r
    return fv_lump + fv_annuity


def _monthly_payment_needed(target: float, current: float,
                              annual_return: float, months: int) -> float:
    """Monthly payment needed to hit target in given months."""
    if months <= 0:
        return 0.0
    r = annual_return / 100.0 / 12
    fv_lump = current * (1 + r) ** months
    remaining = target - fv_lump
    if remaining <= 0:
        return 0.0
    if r == 0:
        return remaining / months
    return remaining * r / ((1 + r) ** months - 1)


def _months_to_goal(target: float, current: float, monthly: float,
                     annual_return: float) -> int:
    """How many months until goal is reached at given contribution."""
    if monthly <= 0 and current >= target:
        return 0
    r = annual_return / 100.0 / 12
    balance = current
    for mo in range(1, 12 * 100):
        balance = balance * (1 + r) + monthly
        if balance >= target:
            return mo
    return -1   # never reached


def _projection_path(current: float, monthly: float, annual_return: float,
                      target: float, max_years: int = 40) -> List[dict]:
    r = annual_return / 100.0 / 12
    balance = current
    path = [{"month": 0, "year": 0.0, "balance": round(balance, 2)}]
    reached_month = None
    for mo in range(1, max_years * 12 + 1):
        balance = balance * (1 + r) + monthly
        if mo % 6 == 0:
            path.append({"month": mo, "year": round(mo / 12, 1), "balance": round(balance, 2)})
        if reached_month is None and balance >= target:
            reached_month = mo
    return path, reached_month


def analyze_savings_goals(goals: List[Dict]) -> dict:
    results = []
    total_monthly_needed = 0.0
    total_monthly_current = 0.0

    for goal in goals:
        goal_type      = goal.get("type", "custom")
        name           = goal.get("name", "Goal")
        target         = float(goal.get("target_amount", 0))
        deadline_years = float(goal.get("deadline_years", 10))
        current        = float(goal.get("current_savings", 0))
        monthly        = float(goal.get("monthly_contribution", 0))
        annual_return  = float(goal.get("expected_return", 6.0))
        priority       = goal.get("priority", "medium")

        deadline_months = int(deadline_years * 12)

        # Current trajectory
        fv_current = _future_value(current, monthly, annual_return, deadline_months)
        gap        = target - fv_current
        on_track   = fv_current >= target

        # Monthly needed to hit target exactly by deadline
        monthly_needed = _monthly_payment_needed(target, current, annual_return, deadline_months)
        extra_needed   = max(monthly_needed - monthly, 0)

        # Time to goal at current contribution
        months_at_current  = _months_to_goal(target, current, monthly, annual_return)
        years_at_current   = months_at_current / 12 if months_at_current > 0 else None

        # Projection path
        path, reached_month = _projection_path(current, monthly, annual_return, target, max_years=max(int(deadline_years) + 10, 10))

        # Sensitivity: what if contribution changes
        sensitivity = []
        for multiplier, label in [(0.5, "Half"), (0.75, "75%"), (1.0, "Current"), (1.5, "150%"), (2.0, "Double")]:
            adj_monthly = monthly * multiplier
            fv = _future_value(current, adj_monthly, annual_return, deadline_months)
            mtg = _months_to_goal(target, current, adj_monthly, annual_return)
            sensitivity.append({
                "label": label,
                "monthly": round(adj_monthly, 2),
                "fv_at_deadline": round(fv, 2),
                "on_track": fv >= target,
                "years_to_goal": round(mtg / 12, 1) if mtg and mtg > 0 else None,
            })

        # Return scenarios
        return_sensitivity = []
        for ret, label in [(3.0, "Conservative (3%)"), (5.0, "Moderate (5%)"),
                            (7.0, "Expected (7%)"), (10.0, "Optimistic (10%)")]:
            fv = _future_value(current, monthly, ret, deadline_months)
            return_sensitivity.append({
                "label": label,
                "return_rate": ret,
                "fv_at_deadline": round(fv, 2),
                "on_track": fv >= target,
            })

        total_monthly_needed  += monthly_needed
        total_monthly_current += monthly

        results.append({
            "type":             goal_type,
            "name":             name,
            "icon":             GOAL_ICONS.get(goal_type, "🎯"),
            "color":            GOAL_COLORS.get(goal_type, "#6b7280"),
            "priority":         priority,
            "target":           round(target, 2),
            "current_savings":  round(current, 2),
            "monthly_contribution": round(monthly, 2),
            "deadline_years":   deadline_years,
            "expected_return":  annual_return,

            "fv_at_deadline":   round(fv_current, 2),
            "gap":              round(gap, 2),
            "on_track":         on_track,
            "pct_funded":       round(min(fv_current / target * 100, 100), 1) if target > 0 else 100.0,

            "monthly_needed":   round(monthly_needed, 2),
            "extra_needed":     round(extra_needed, 2),
            "years_to_goal_at_current": round(years_at_current, 1) if years_at_current else None,

            "projection_path":  path,
            "contribution_sensitivity": sensitivity,
            "return_sensitivity": return_sensitivity,
        })

    # Summary across all goals
    all_funded   = all(g["on_track"] for g in results)
    goals_on_track  = sum(1 for g in results if g["on_track"])

    return {
        "goals": results,
        "summary": {
            "total_goals": len(results),
            "goals_on_track": goals_on_track,
            "all_funded": all_funded,
            "total_monthly_current": round(total_monthly_current, 2),
            "total_monthly_needed": round(total_monthly_needed, 2),
            "monthly_gap": round(max(total_monthly_needed - total_monthly_current, 0), 2),
        }
    }
