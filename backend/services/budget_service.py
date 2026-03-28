"""
Budget Planner & Financial Health Analyzer.
Analyzes spending by 50/30/20 rule, computes savings rate, financial health score,
and projects wealth growth from current savings habits.
"""
from typing import List, Dict
import numpy as np


CATEGORY_TYPES = {
    # Needs (50%)
    "Housing": "needs", "Rent": "needs", "Mortgage": "needs",
    "Utilities": "needs", "Groceries": "needs", "Transportation": "needs",
    "Insurance": "needs", "Healthcare": "needs", "Minimum Payments": "needs",
    "Childcare": "needs", "Phone": "needs",
    # Wants (30%)
    "Dining Out": "wants", "Entertainment": "wants", "Subscriptions": "wants",
    "Shopping": "wants", "Travel": "wants", "Hobbies": "wants",
    "Personal Care": "wants", "Gym": "wants", "Clothing": "wants",
    # Savings (20%)
    "Savings": "savings", "Investments": "savings", "Emergency Fund": "savings",
    "Retirement (401k/IRA)": "savings", "Debt Payoff": "savings",
}

BENCHMARKS = {
    "savings_rate": {"excellent": 20, "good": 15, "fair": 10, "poor": 5},
    "housing_pct":  {"excellent": 25, "good": 30, "fair": 35, "poor": 40},
    "food_pct":     {"excellent": 10, "good": 15, "fair": 20, "poor": 25},
}


def _score_savings_rate(rate: float) -> int:
    """0–25 points for savings rate."""
    if rate >= 20: return 25
    if rate >= 15: return 20
    if rate >= 10: return 15
    if rate >= 5:  return 8
    return 0


def _score_needs(needs_pct: float) -> int:
    """0–25 points: lower needs% = better."""
    if needs_pct <= 50: return 25
    if needs_pct <= 60: return 18
    if needs_pct <= 70: return 10
    if needs_pct <= 80: return 5
    return 0


def _score_wants(wants_pct: float) -> int:
    """0–25 points."""
    if wants_pct <= 20: return 25
    if wants_pct <= 30: return 20
    if wants_pct <= 40: return 12
    if wants_pct <= 50: return 5
    return 0


def _score_emergency(months: float) -> int:
    """0–25 points for emergency fund coverage."""
    if months >= 6:  return 25
    if months >= 3:  return 18
    if months >= 1:  return 8
    return 0


def _grade(score: int) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def _project_wealth(monthly_savings: float, existing_savings: float,
                    years: int = 30, annual_return: float = 7.0) -> List[dict]:
    """Project future wealth given monthly savings."""
    r = annual_return / 100.0 / 12
    points = []
    balance = existing_savings
    for mo in range(years * 12 + 1):
        yr = mo / 12
        if mo % 12 == 0:
            points.append({"year": round(yr, 1), "balance": round(balance, 2)})
        balance = balance * (1 + r) + monthly_savings
    return points


def analyze_budget(
    monthly_income: float,
    expenses: List[Dict],
    existing_savings: float = 0.0,
    emergency_fund: float = 0.0,
    projection_years: int = 30,
    expected_return: float = 7.0,
) -> dict:
    if monthly_income <= 0:
        raise ValueError("Monthly income must be > 0")

    # ── Categorize expenses ─────────────────────────────────────────────────
    total_needs  = 0.0
    total_wants  = 0.0
    total_savings = 0.0
    total_expenses = 0.0
    categorized = []

    for exp in expenses:
        category = exp.get("category", "Other")
        amount   = float(exp.get("amount", 0))
        # Determine type: use provided or look up default
        exp_type = exp.get("type") or CATEGORY_TYPES.get(category, "wants")
        total_expenses += amount
        if exp_type == "needs":
            total_needs += amount
        elif exp_type == "wants":
            total_wants += amount
        else:
            total_savings += amount
        categorized.append({
            "category": category,
            "amount": round(amount, 2),
            "type": exp_type,
            "pct_income": round(amount / monthly_income * 100, 1),
        })

    monthly_surplus = monthly_income - total_expenses
    savings_rate    = (total_savings + max(monthly_surplus, 0)) / monthly_income * 100

    needs_pct    = round(total_needs    / monthly_income * 100, 1)
    wants_pct    = round(total_wants    / monthly_income * 100, 1)
    savings_pct  = round(total_savings  / monthly_income * 100, 1)
    surplus_pct  = round(max(monthly_surplus, 0) / monthly_income * 100, 1)

    # ── 50/30/20 Targets ────────────────────────────────────────────────────
    target_needs   = monthly_income * 0.50
    target_wants   = monthly_income * 0.30
    target_savings = monthly_income * 0.20

    needs_gap   = round(total_needs  - target_needs, 2)
    wants_gap   = round(total_wants  - target_wants, 2)
    savings_gap = round(total_savings - target_savings, 2)

    # ── Emergency fund ───────────────────────────────────────────────────────
    monthly_needs_expenses = total_needs
    emergency_months = emergency_fund / monthly_needs_expenses if monthly_needs_expenses > 0 else 0
    emergency_target = monthly_needs_expenses * 6

    # ── Financial Health Score ───────────────────────────────────────────────
    score_sr  = _score_savings_rate(savings_rate)
    score_nd  = _score_needs(needs_pct)
    score_wt  = _score_wants(wants_pct)
    score_em  = _score_emergency(emergency_months)
    total_score = score_sr + score_nd + score_wt + score_em
    grade       = _grade(total_score)

    # ── Recommendations ──────────────────────────────────────────────────────
    recommendations = []
    if needs_pct > 60:
        recommendations.append({
            "priority": "high",
            "title": "Reduce Essential Expenses",
            "detail": f"Your needs consume {needs_pct}% of income (target: 50%). Consider refinancing, moving, or reducing recurring bills.",
        })
    if wants_pct > 35:
        recommendations.append({
            "priority": "medium",
            "title": "Trim Discretionary Spending",
            "detail": f"Wants are {wants_pct}% of income (target: 30%). Review subscriptions and dining/entertainment.",
        })
    if savings_rate < 10:
        recommendations.append({
            "priority": "high",
            "title": "Increase Savings Rate",
            "detail": f"You're saving {round(savings_rate,1)}% (target: 20%). Even small increases compound dramatically over time.",
        })
    if emergency_months < 3:
        recommendations.append({
            "priority": "high",
            "title": "Build Emergency Fund",
            "detail": f"You have {round(emergency_months, 1)} months of expenses saved (target: 3–6 months = ${emergency_target:,.0f}).",
        })
    if monthly_surplus < 0:
        recommendations.append({
            "priority": "critical",
            "title": "You're Spending More Than You Earn",
            "detail": f"Monthly deficit: ${abs(monthly_surplus):,.2f}. Identify and cut the highest-impact expense categories immediately.",
        })
    if not recommendations:
        recommendations.append({
            "priority": "low",
            "title": "Great Job!",
            "detail": "Your finances look healthy. Consider maximizing tax-advantaged accounts (401k, Roth IRA, HSA) and increasing investment contributions.",
        })

    # ── Projections ─────────────────────────────────────────────────────────
    effective_monthly_savings = total_savings + max(monthly_surplus, 0)
    projection_current = _project_wealth(effective_monthly_savings, existing_savings,
                                          projection_years, expected_return)
    projection_optimized = _project_wealth(target_savings, existing_savings,
                                            projection_years, expected_return)

    # ── Pie chart data ───────────────────────────────────────────────────────
    # Group by category for pie
    category_totals = {}
    for exp in categorized:
        cat = exp["category"]
        category_totals[cat] = category_totals.get(cat, 0) + exp["amount"]

    return {
        "summary": {
            "monthly_income": round(monthly_income, 2),
            "total_expenses": round(total_expenses, 2),
            "monthly_surplus": round(monthly_surplus, 2),
            "savings_rate": round(savings_rate, 1),
            "health_score": total_score,
            "grade": grade,
            "emergency_months": round(emergency_months, 1),
            "emergency_target": round(emergency_target, 2),
        },
        "breakdown_503020": {
            "needs":   {"actual": round(total_needs, 2), "target": round(target_needs, 2), "pct": needs_pct, "gap": needs_gap},
            "wants":   {"actual": round(total_wants, 2), "target": round(target_wants, 2), "pct": wants_pct, "gap": wants_gap},
            "savings": {"actual": round(total_savings, 2), "target": round(target_savings, 2), "pct": savings_pct, "gap": savings_gap},
        },
        "score_breakdown": {
            "savings_rate":    {"score": score_sr,  "max": 25, "label": "Savings Rate"},
            "needs_spending":  {"score": score_nd,  "max": 25, "label": "Essential Spending"},
            "wants_spending":  {"score": score_wt,  "max": 25, "label": "Discretionary Spending"},
            "emergency_fund":  {"score": score_em,  "max": 25, "label": "Emergency Fund"},
        },
        "expenses_categorized": sorted(categorized, key=lambda x: x["amount"], reverse=True),
        "category_totals": [{"category": k, "amount": round(v, 2)} for k, v in
                             sorted(category_totals.items(), key=lambda x: x[1], reverse=True)],
        "recommendations": recommendations,
        "projections": {
            "current_habits": projection_current,
            "optimized_503020": projection_optimized,
            "effective_monthly_savings": round(effective_monthly_savings, 2),
            "optimized_monthly_savings": round(target_savings, 2),
        },
    }
