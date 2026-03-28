import sys
sys.path.insert(0, '.')

from services.retirement_service import run_retirement_plan
r = run_retirement_plan(35, 65, 90, 100000, 20000, 7.0, 15.0, 3.0, 80000, 90, 2.0, 200)
print('Retirement prob of success:', r['summary']['probability_of_success'])
print('Median nest egg:', r['summary']['median_retirement_balance'])

from services.swr_service import analyze_swr
s = analyze_swr(1_000_000, 40_000, 30, 60, 3.0, ['fixed_percent_4', 'guardrails'], 500)
print('SWR strategies:', list(s['strategies'].keys()))
print('4% rule survival:', s['strategies']['fixed_percent_4']['survival_rate'])
print('Guardrails survival:', s['strategies']['guardrails']['survival_rate'])

from services.budget_service import analyze_budget
b = analyze_budget(8000, [
    {'category': 'Housing', 'amount': 2000, 'type': 'needs'},
    {'category': 'Groceries', 'amount': 600, 'type': 'needs'},
    {'category': 'Dining Out', 'amount': 400, 'type': 'wants'},
    {'category': 'Savings', 'amount': 500, 'type': 'savings'},
])
print('Budget score:', b['summary']['health_score'], 'Grade:', b['summary']['grade'])
print('Savings rate:', b['summary']['savings_rate'])

from services.savings_service import analyze_savings_goals
sg = analyze_savings_goals([
    {'type': 'retirement', 'name': 'Retire at 65', 'target_amount': 1_000_000,
     'deadline_years': 30, 'current_savings': 50000, 'monthly_contribution': 1000,
     'expected_return': 7.0, 'priority': 'high'},
    {'type': 'house', 'name': 'House', 'target_amount': 80000,
     'deadline_years': 5, 'current_savings': 10000, 'monthly_contribution': 800,
     'expected_return': 4.5, 'priority': 'high'},
])
print('Goals total:', sg['summary']['total_goals'])
print('Goals on track:', sg['summary']['goals_on_track'])

print('\nAll services OK!')
