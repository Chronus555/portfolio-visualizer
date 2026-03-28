import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { Plus, Trash2, PiggyBank, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react'

const CATEGORIES = [
  { name: 'Housing/Rent',     type: 'needs' },
  { name: 'Utilities',        type: 'needs' },
  { name: 'Groceries',        type: 'needs' },
  { name: 'Transportation',   type: 'needs' },
  { name: 'Insurance',        type: 'needs' },
  { name: 'Healthcare',       type: 'needs' },
  { name: 'Phone',            type: 'needs' },
  { name: 'Dining Out',       type: 'wants' },
  { name: 'Entertainment',    type: 'wants' },
  { name: 'Subscriptions',    type: 'wants' },
  { name: 'Shopping',         type: 'wants' },
  { name: 'Travel',           type: 'wants' },
  { name: 'Gym/Hobbies',      type: 'wants' },
  { name: 'Savings/Investing',type: 'savings' },
  { name: 'Emergency Fund',   type: 'savings' },
  { name: 'Retirement 401k',  type: 'savings' },
  { name: 'Debt Payoff',      type: 'savings' },
]

const DEFAULT_EXPENSES = [
  { id: 1, category: 'Housing/Rent',   type: 'needs',   amount: 2000 },
  { id: 2, category: 'Utilities',      type: 'needs',   amount: 200 },
  { id: 3, category: 'Groceries',      type: 'needs',   amount: 600 },
  { id: 4, category: 'Transportation', type: 'needs',   amount: 400 },
  { id: 5, category: 'Insurance',      type: 'needs',   amount: 300 },
  { id: 6, category: 'Dining Out',     type: 'wants',   amount: 400 },
  { id: 7, category: 'Entertainment',  type: 'wants',   amount: 200 },
  { id: 8, category: 'Subscriptions',  type: 'wants',   amount: 100 },
  { id: 9, category: 'Savings/Investing', type: 'savings', amount: 500 },
  { id: 10,category: 'Retirement 401k',   type: 'savings', amount: 500 },
]

const TYPE_COLORS = { needs: '#3b82f6', wants: '#f59e0b', savings: '#10b981' }
const TYPE_LABELS = { needs: 'Needs', wants: 'Wants', savings: 'Savings' }

let nextId = 11

export default function BudgetPlannerPage() {
  const [income, setIncome] = useState(8000)
  const [expenses, setExpenses] = useState(DEFAULT_EXPENSES)
  const [existingSavings, setExistingSavings] = useState(25000)
  const [emergencyFund, setEmergencyFund] = useState(5000)
  const [projYears, setProjYears] = useState(30)

  const mutation = useMutation({
    mutationFn: () => api.post('/budget/analyze', {
      monthly_income: income,
      expenses: expenses.map(({ category, amount, type }) => ({ category, amount, type })),
      existing_savings: existingSavings,
      emergency_fund: emergencyFund,
      projection_years: projYears,
      expected_return: 7.0,
    }).then(r => r.data),
  })

  const addExpense = () => {
    setExpenses(p => [...p, { id: nextId++, category: 'Other', type: 'wants', amount: 0 }])
  }
  const removeExpense = (id) => setExpenses(p => p.filter(e => e.id !== id))
  const updateExpense = (id, field, val) =>
    setExpenses(p => p.map(e => e.id === id ? { ...e, [field]: val } : e))

  const totalExpenses = expenses.reduce((s, e) => s + (parseFloat(e.amount) || 0), 0)
  const surplus = income - totalExpenses

  const data = mutation.data

  // ── Charts ───────────────────────────────────────────────────────────────
  const pieChart = data ? {
    data: [{
      labels: data.category_totals.map(c => c.category),
      values: data.category_totals.map(c => c.amount),
      type: 'pie', hole: 0.45,
      textinfo: 'label+percent',
      textfont: { size: 11 },
    }],
    layout: { title: 'Spending Breakdown', height: 320, showlegend: false },
  } : null

  const barChart = data ? {
    data: [
      { x: ['Needs', 'Wants', 'Savings'], y: [data.breakdown_503020.needs.actual, data.breakdown_503020.wants.actual, data.breakdown_503020.savings.actual], type: 'bar', name: 'Actual', marker: { color: ['#3b82f6', '#f59e0b', '#10b981'] } },
      { x: ['Needs', 'Wants', 'Savings'], y: [data.breakdown_503020.needs.target, data.breakdown_503020.wants.target, data.breakdown_503020.savings.target], type: 'bar', name: 'Target (50/30/20)', marker: { color: ['rgba(59,130,246,0.3)', 'rgba(245,158,11,0.3)', 'rgba(16,185,129,0.3)'] } },
    ],
    layout: {
      title: '50/30/20 Budget — Actual vs Target',
      xaxis: { title: 'Category' },
      yaxis: { title: 'Monthly Amount ($)', tickformat: '$,.0f' },
      barmode: 'group', height: 280,
    },
  } : null

  const projChart = data ? {
    data: [
      {
        x: data.projections.current_habits.map(p => p.year),
        y: data.projections.current_habits.map(p => p.balance),
        type: 'scatter', mode: 'lines', name: 'Current Habits',
        line: { color: '#3b82f6', width: 2 },
      },
      {
        x: data.projections.optimized_503020.map(p => p.year),
        y: data.projections.optimized_503020.map(p => p.balance),
        type: 'scatter', mode: 'lines', name: '50/30/20 Optimized',
        line: { color: '#10b981', width: 2, dash: 'dash' },
      },
    ],
    layout: {
      title: `${projYears}-Year Wealth Projection`,
      xaxis: { title: 'Years' },
      yaxis: { title: 'Net Worth ($)', tickformat: '$,.0f' },
      height: 280,
    },
  } : null

  const score = data?.summary?.health_score || 0
  const grade = data?.summary?.grade || '—'
  const scoreColor = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Budget Planner</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          50/30/20 analysis, financial health score, and wealth projection from your current spending habits.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Left panel ─────────────────────────────────────────────── */}
        <div className="space-y-4">
          {/* Income */}
          <div className="card p-4 space-y-3">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Monthly Income</h2>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[var(--text-muted)]">$</span>
              <input type="number" value={income} onChange={e => setIncome(parseFloat(e.target.value) || 0)}
                className="input w-full pl-7" placeholder="Monthly take-home" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-[var(--text-muted)]">Existing Savings</label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">$</span>
                  <input type="number" value={existingSavings} onChange={e => setExistingSavings(parseFloat(e.target.value) || 0)} className="input w-full pl-7 text-sm" />
                </div>
              </div>
              <div>
                <label className="text-xs text-[var(--text-muted)]">Emergency Fund</label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">$</span>
                  <input type="number" value={emergencyFund} onChange={e => setEmergencyFund(parseFloat(e.target.value) || 0)} className="input w-full pl-7 text-sm" />
                </div>
              </div>
            </div>
            <div>
              <label className="text-xs text-[var(--text-muted)]">Projection Years</label>
              <input type="number" value={projYears} onChange={e => setProjYears(parseInt(e.target.value) || 30)}
                min={1} max={50} className="input w-full mt-1 text-sm" />
            </div>
          </div>

          {/* Expenses */}
          <div className="card p-4 space-y-2">
            <div className="flex justify-between items-center border-b border-[var(--border)] pb-2">
              <h2 className="font-semibold text-sm">Monthly Expenses</h2>
              <button onClick={addExpense} className="flex items-center gap-1 text-xs text-[var(--accent)] hover:opacity-80">
                <Plus size={14} /> Add
              </button>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {expenses.map(exp => (
                <div key={exp.id} className="flex items-center gap-2">
                  <select value={exp.type} onChange={e => updateExpense(exp.id, 'type', e.target.value)}
                    className="input text-xs py-1 w-20" style={{ color: TYPE_COLORS[exp.type] }}>
                    <option value="needs">Need</option>
                    <option value="wants">Want</option>
                    <option value="savings">Save</option>
                  </select>
                  <input value={exp.category} onChange={e => updateExpense(exp.id, 'category', e.target.value)}
                    className="input text-xs py-1 flex-1 min-w-0" placeholder="Category" />
                  <div className="relative w-20">
                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">$</span>
                    <input type="number" value={exp.amount} onChange={e => updateExpense(exp.id, 'amount', parseFloat(e.target.value) || 0)}
                      className="input text-xs py-1 pl-5 w-full" />
                  </div>
                  <button onClick={() => removeExpense(exp.id)} className="text-[var(--text-muted)] hover:text-red-400">
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
            <div className="pt-2 border-t border-[var(--border)] text-xs flex justify-between">
              <span className="text-[var(--text-muted)]">Total</span>
              <span className={surplus < 0 ? 'text-red-400 font-bold' : 'font-medium'}>
                ${totalExpenses.toLocaleString()} / ${income.toLocaleString()} income
                {' '}({surplus >= 0 ? '+' : ''}{surplus.toLocaleString()} surplus)
              </span>
            </div>
          </div>

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Analyzing…' : 'Analyze Budget'}
          </button>
        </div>

        {/* ── Results ──────────────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          {!data && !mutation.isPending && (
            <div className="empty-state">
              <PiggyBank size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Enter your income and expenses to get started</p>
            </div>
          )}
          {mutation.isPending && <div className="empty-state"><div className="spinner mx-auto mb-3" /><p>Analyzing your budget…</p></div>}

          {data && (
            <>
              {/* Health Score */}
              <div className="card p-5 flex items-center gap-6">
                <div className="relative w-20 h-20 flex-shrink-0">
                  <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--border)" strokeWidth="3" />
                    <circle cx="18" cy="18" r="15.9" fill="none" strokeWidth="3"
                      stroke={scoreColor}
                      strokeDasharray={`${score} ${100 - score}`}
                      strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold leading-none">{grade}</span>
                    <span className="text-xs text-[var(--text-muted)]">{score}/100</span>
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-lg">Financial Health Score</h3>
                  <div className="grid grid-cols-2 gap-1 mt-2">
                    {Object.values(data.score_breakdown).map(s => (
                      <div key={s.label} className="text-xs flex gap-2 items-center">
                        <div className="h-1.5 w-12 bg-[var(--bg)] rounded-full overflow-hidden">
                          <div className="h-full bg-[var(--accent)] rounded-full" style={{ width: `${s.score / s.max * 100}%` }} />
                        </div>
                        <span className="text-[var(--text-muted)]">{s.label}: <strong>{s.score}/{s.max}</strong></span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Summary metrics */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  { label: 'Monthly Surplus', value: `$${data.summary.monthly_surplus.toLocaleString()}`, color: data.summary.monthly_surplus >= 0 ? 'text-green-400' : 'text-red-400' },
                  { label: 'Savings Rate', value: `${data.summary.savings_rate}%`, color: data.summary.savings_rate >= 20 ? 'text-green-400' : 'text-yellow-400' },
                  { label: 'Emergency Fund', value: `${data.summary.emergency_months}mo`, color: data.summary.emergency_months >= 3 ? 'text-green-400' : 'text-red-400' },
                  { label: 'Total Expenses', value: `$${data.summary.total_expenses.toLocaleString()}`, color: '' },
                ].map(m => (
                  <div key={m.label} className="card p-3 text-center">
                    <div className={`text-2xl font-bold ${m.color}`}>{m.value}</div>
                    <div className="text-xs text-[var(--text-muted)] mt-0.5">{m.label}</div>
                  </div>
                ))}
              </div>

              {/* 50/30/20 breakdown */}
              <div className="card p-4">
                <h3 className="font-semibold text-sm mb-3">50/30/20 Budget Analysis</h3>
                <div className="space-y-3">
                  {Object.entries(data.breakdown_503020).map(([key, val]) => {
                    const target = { needs: 50, wants: 30, savings: 20 }[key]
                    const ok = val.gap <= 0
                    return (
                      <div key={key}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-medium capitalize">{key} (Target: {target}%)</span>
                          <div className="flex gap-3">
                            <span style={{ color: TYPE_COLORS[key] }}>${val.actual.toLocaleString()} ({val.pct}%)</span>
                            <span className={ok ? 'text-green-400' : 'text-red-400'}>
                              {ok ? '✓' : `+$${val.gap.toLocaleString()} over`}
                            </span>
                          </div>
                        </div>
                        <div className="h-3 bg-[var(--bg)] rounded-full overflow-hidden relative">
                          <div className="h-full rounded-full transition-all duration-700"
                               style={{ width: `${Math.min(val.pct, 100)}%`, background: TYPE_COLORS[key] }} />
                          <div className="absolute top-0 h-full border-l-2 border-white/40"
                               style={{ left: `${target}%` }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Recommendations */}
              {data.recommendations.length > 0 && (
                <div className="space-y-2">
                  {data.recommendations.map((r, i) => (
                    <div key={i} className={`card p-3 flex gap-3 items-start border-l-4 ${
                      r.priority === 'critical' ? 'border-red-500'
                      : r.priority === 'high' ? 'border-orange-500'
                      : r.priority === 'medium' ? 'border-yellow-500'
                      : 'border-green-500'
                    }`}>
                      {r.priority === 'low' ? <CheckCircle size={16} className="text-green-400 shrink-0 mt-0.5" />
                        : <AlertCircle size={16} className="text-orange-400 shrink-0 mt-0.5" />}
                      <div>
                        <div className="text-sm font-semibold">{r.title}</div>
                        <div className="text-xs text-[var(--text-muted)] mt-0.5">{r.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {barChart  && <div className="card p-4"><PlotlyChart data={barChart.data}  layout={barChart.layout}  /></div>}
              {pieChart  && <div className="card p-4"><PlotlyChart data={pieChart.data}  layout={pieChart.layout}  /></div>}
              {projChart && (
                <div className="card p-4">
                  <PlotlyChart data={projChart.data} layout={projChart.layout} />
                  <div className="grid grid-cols-2 gap-3 mt-3 text-xs text-[var(--text-muted)]">
                    <div>Current savings/mo: <strong className="text-[var(--text)]">${data.projections.effective_monthly_savings.toLocaleString()}</strong></div>
                    <div>50/30/20 savings/mo: <strong className="text-green-400">${data.projections.optimized_monthly_savings.toLocaleString()}</strong></div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
