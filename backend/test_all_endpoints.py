"""Full integration test of all 4 new financial planning endpoints."""
import requests
import json

BASE = "http://localhost:8001/api"

def ok(name, r):
    if r.status_code == 200:
        print(f"  PASS {name}")
        return r.json()
    else:
        print(f"  FAIL {name} -- HTTP {r.status_code}: {r.text[:300]}")
        return None

print("\n=== RETIREMENT PLANNER ===")
r = requests.post(f"{BASE}/retirement/plan", json={
    "current_age": 35, "retirement_age": 65, "life_expectancy": 90,
    "current_savings": 150000, "annual_contribution": 24000,
    "contribution_growth": 2.0, "expected_return": 7.0, "volatility": 15.0,
    "inflation": 3.0, "annual_expenses_in_retirement": 80000,
    "social_security": 18000, "simulations": 500
})
d = ok("POST /api/retirement/plan", r)
if d:
    s = d["summary"]
    print(f"    prob_success={s['probability_of_success']}%  median=${s['median_retirement_balance']:,.0f}")
    print(f"    target=${s['target_nest_egg']:,.0f}  on_track={s['on_track_pct']}%")
    assert "accumulation_path" in d and len(d["accumulation_path"]) > 0
    assert "withdrawal_chart" in d
    assert "sequence_of_returns" in d
    print(f"    accumulation_path: {len(d['accumulation_path'])} points")
    print(f"    withdrawal_chart ages: {len(d['withdrawal_chart']['ages'])} points")

# Edge cases
print("\n  Edge cases:")
r2 = requests.post(f"{BASE}/retirement/plan", json={
    "current_age": 55, "retirement_age": 60, "life_expectancy": 85,
    "current_savings": 500000, "annual_contribution": 50000,
    "expected_return": 5.0, "volatility": 10.0, "inflation": 2.5,
    "annual_expenses_in_retirement": 120000, "social_security": 30000, "simulations": 200
})
ok("  Short horizon (55->60, 25yr withdrawal)", r2)

r3 = requests.post(f"{BASE}/retirement/plan", json={
    "current_age": 25, "retirement_age": 65, "life_expectancy": 95,
    "current_savings": 0, "annual_contribution": 6000,
    "expected_return": 8.0, "volatility": 18.0, "inflation": 3.0,
    "annual_expenses_in_retirement": 60000, "social_security": 0, "simulations": 200
})
ok("  Zero savings, 40yr accumulation", r3)

print("\n=== SAFE WITHDRAWAL RATE ===")
r = requests.get(f"{BASE}/swr/strategies")
d = ok("GET /api/swr/strategies", r)
if d:
    print(f"    strategies: {list(d['strategies'].keys())}")

r = requests.post(f"{BASE}/swr/analyze", json={
    "portfolio_value": 1_000_000, "annual_expenses": 40_000,
    "retirement_years": 30, "stock_allocation": 60,
    "inflation": 3.0, "simulations": 1000,
    "strategies": ["fixed_percent_4", "fixed_percent_dynamic", "fixed_dollar_inflation",
                   "guardrails", "floor_ceiling", "rmd_based", "bucket"]
})
d = ok("POST /api/swr/analyze (all 7 strategies)", r)
if d:
    print(f"    rankings (survival rate):")
    for r2 in d["rankings"]:
        print(f"      {r2['name']}: {r2['survival_rate']}%")
    print(f"    SWR sensitivity: {d['swr_sensitivity']}")

# Edge: aggressive withdrawal
r = requests.post(f"{BASE}/swr/analyze", json={
    "portfolio_value": 500_000, "annual_expenses": 40_000,
    "retirement_years": 40, "stock_allocation": 80,
    "inflation": 4.0, "simulations": 500,
    "strategies": ["guardrails", "floor_ceiling"]
})
ok("  Aggressive 8% WR, 40yr", r)

print("\n=== BUDGET PLANNER ===")
r = requests.post(f"{BASE}/budget/analyze", json={
    "monthly_income": 8000,
    "expenses": [
        {"category": "Housing/Rent",   "amount": 2000, "type": "needs"},
        {"category": "Utilities",      "amount": 200,  "type": "needs"},
        {"category": "Groceries",      "amount": 600,  "type": "needs"},
        {"category": "Transportation", "amount": 400,  "type": "needs"},
        {"category": "Insurance",      "amount": 300,  "type": "needs"},
        {"category": "Dining Out",     "amount": 400,  "type": "wants"},
        {"category": "Entertainment",  "amount": 200,  "type": "wants"},
        {"category": "Subscriptions",  "amount": 100,  "type": "wants"},
        {"category": "Savings/Investing","amount": 500,"type": "savings"},
        {"category": "Retirement 401k","amount": 500,  "type": "savings"},
    ],
    "existing_savings": 25000, "emergency_fund": 5000,
    "projection_years": 30, "expected_return": 7.0
})
d = ok("POST /api/budget/analyze (balanced budget)", r)
if d:
    s = d["summary"]
    print(f"    health_score={s['health_score']} grade={s['grade']} savings_rate={s['savings_rate']}%")
    print(f"    surplus=${s['monthly_surplus']:,.0f}  emergency={s['emergency_months']}mo")
    assert "breakdown_503020" in d
    assert "projections" in d
    assert "recommendations" in d
    print(f"    recommendations: {len(d['recommendations'])}")
    print(f"    projection points: {len(d['projections']['current_habits'])}")

# Edge: overspending
r = requests.post(f"{BASE}/budget/analyze", json={
    "monthly_income": 5000,
    "expenses": [
        {"category": "Housing", "amount": 3000, "type": "needs"},
        {"category": "Food",    "amount": 1500, "type": "needs"},
        {"category": "Fun",     "amount": 1000, "type": "wants"},
    ],
    "existing_savings": 0, "emergency_fund": 0,
    "projection_years": 20, "expected_return": 6.0
})
d2 = ok("  Overspending scenario (deficit)", r)
if d2:
    print(f"    surplus=${d2['summary']['monthly_surplus']:,.0f}  score={d2['summary']['health_score']}")

# Edge: high saver
r = requests.post(f"{BASE}/budget/analyze", json={
    "monthly_income": 15000,
    "expenses": [
        {"category": "Housing", "amount": 2000, "type": "needs"},
        {"category": "Food",    "amount": 500,  "type": "needs"},
        {"category": "Savings", "amount": 5000, "type": "savings"},
    ],
    "existing_savings": 200000, "emergency_fund": 30000,
    "projection_years": 30, "expected_return": 8.0
})
d3 = ok("  High saver scenario", r)
if d3:
    print(f"    grade={d3['summary']['grade']}  score={d3['summary']['health_score']}")

print("\n=== SAVINGS GOALS ===")
r = requests.post(f"{BASE}/savings/goals", json={
    "goals": [
        {"type": "retirement",  "name": "Retire at 65",    "target_amount": 2_000_000,
         "deadline_years": 30, "current_savings": 50_000, "monthly_contribution": 1_500,
         "expected_return": 7.0, "priority": "high"},
        {"type": "house",       "name": "Home Down Payment","target_amount": 100_000,
         "deadline_years": 5,  "current_savings": 15_000, "monthly_contribution": 1_000,
         "expected_return": 4.5, "priority": "high"},
        {"type": "emergency",   "name": "6-Month Fund",    "target_amount": 30_000,
         "deadline_years": 2,  "current_savings": 5_000,  "monthly_contribution": 800,
         "expected_return": 4.5, "priority": "high"},
        {"type": "college",     "name": "College Fund",    "target_amount": 150_000,
         "deadline_years": 18, "current_savings": 10_000, "monthly_contribution": 300,
         "expected_return": 6.0, "priority": "medium"},
    ]
})
d = ok("POST /api/savings/goals (4 goals)", r)
if d:
    print(f"    total={d['summary']['total_goals']}  on_track={d['summary']['goals_on_track']}")
    for g in d["goals"]:
        print(f"    {g['icon']} {g['name']}: {g['pct_funded']:.0f}% funded, on_track={g['on_track']}, monthly_needed=${g['monthly_needed']:,.0f}")
    assert all("projection_path" in g for g in d["goals"])
    assert all("contribution_sensitivity" in g for g in d["goals"])
    assert all("return_sensitivity" in g for g in d["goals"])

# Edge: already funded goal
r = requests.post(f"{BASE}/savings/goals", json={
    "goals": [
        {"type": "custom", "name": "Already Done", "target_amount": 10_000,
         "deadline_years": 5, "current_savings": 50_000, "monthly_contribution": 0,
         "expected_return": 5.0, "priority": "low"},
    ]
})
d2 = ok("  Already-funded goal", r)
if d2:
    g = d2["goals"][0]
    print(f"    pct_funded={g['pct_funded']}%  on_track={g['on_track']}")

# Edge: impossible goal (no contribution)
r = requests.post(f"{BASE}/savings/goals", json={
    "goals": [
        {"type": "custom", "name": "Impossible", "target_amount": 1_000_000,
         "deadline_years": 1, "current_savings": 0, "monthly_contribution": 0,
         "expected_return": 5.0, "priority": "low"},
    ]
})
d3 = ok("  Impossible goal (no savings/contributions)", r)
if d3:
    g = d3["goals"][0]
    print(f"    pct_funded={g['pct_funded']}%  monthly_needed=${g['monthly_needed']:,.0f}")

print("\n=== ALL TESTS COMPLETE ===\n")
