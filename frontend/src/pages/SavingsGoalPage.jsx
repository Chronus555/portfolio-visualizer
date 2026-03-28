import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { Plus, Trash2, Target, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'

const GOAL_TYPES = [
  { value: 'retirement', label: '🏖️ Retirement',      color: '#3b82f6' },
  { value: 'house',      label: '🏠 Home Down Payment', color: '#10b981' },
  { value: 'emergency',  label: '🛡️ Emergency Fund',   color: '#f59e0b' },
  { value: 'college',    label: '🎓 College Fund',      color: '#8b5cf6' },
  { value: 'car',        label: '🚗 Car',               color: '#ef4444' },
  { value: 'vacation',   label: '✈️ Vacation',          color: '#06b6d4' },
  { value: 'business',   label: '💼 Business',          color: '#ec4899' },
  { value: 'wedding',    label: '💍 Wedding',            color: '#f97316' },
  { value: 'custom',     label: '🎯 Custom Goal',        color: '#6b7280' },
]

const DEFAULT_GOALS = [
  { id: 1, type: 'retirement',  name: 'Retirement at 65',  target_amount: 2_000_000, deadline_years: 30, current_savings: 50_000,  monthly_contribution: 1_500, expected_return: 7.0, priority: 'high' },
  { id: 2, type: 'house',       name: 'Home Down Payment', target_amount: 100_000,   deadline_years: 5,  current_savings: 15_000,  monthly_contribution: 1_000, expected_return: 4.5, priority: 'high' },
  { id: 3, type: 'emergency',   name: '6-Month Emergency', target_amount: 30_000,    deadline_years: 2,  current_savings: 5_000,   monthly_contribution: 800,   expected_return: 4.5, priority: 'high' },
]

let nextId = 4

export default function SavingsGoalPage() {
  const [goals, setGoals] = useState(DEFAULT_GOALS)
  const [expandedGoal, setExpandedGoal] = useState(null)

  const mutation = useMutation({
    mutationFn: () => api.post('/savings/goals', {
      goals: goals.map(({ id, ...g }) => g),
    }).then(r => r.data),
  })

  const addGoal = () => {
    setGoals(p => [...p, {
      id: nextId++, type: 'custom', name: 'New Goal',
      target_amount: 50_000, deadline_years: 5,
      current_savings: 0, monthly_contribution: 500,
      expected_return: 6.0, priority: 'medium',
    }])
  }

  const removeGoal = (id) => setGoals(p => p.filter(g => g.id !== id))

  const updateGoal = (id, field, value) =>
    setGoals(p => p.map(g => g.id === id ? { ...g, [field]: value } : g))

  const data = mutation.data
  const goalResults = data?.goals || []

  const colorFor = (type) => GOAL_TYPES.find(t => t.value === type)?.color || '#6b7280'

  // Build multi-goal projection chart
  const projChart = goalResults.length > 0 ? {
    data: goalResults.map(g => ({
      x: g.projection_path.map(p => p.year),
      y: g.projection_path.map(p => p.balance),
      type: 'scatter', mode: 'lines',
      name: g.name,
      line: { color: g.color, width: 2 },
      hovertemplate: `${g.name}<br>Year %{x}: $%{y:,.0f}<extra></extra>`,
    })),
    layout: {
      title: 'All Goals — Projection to Target',
      xaxis: { title: 'Years from Now' },
      yaxis: { title: 'Savings ($)', tickformat: '$,.0f' },
      height: 320,
    },
  } : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Savings Goal Planner</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Track multiple financial goals simultaneously — see if you're on track and exactly what you need to contribute.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Left: Goal Input ─────────────────────────────────────────── */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <div className="flex justify-between items-center border-b border-[var(--border)] pb-2">
              <h2 className="font-semibold text-sm">Your Goals</h2>
              <button onClick={addGoal} className="flex items-center gap-1 text-xs text-[var(--accent)] hover:opacity-80">
                <Plus size={14} /> Add Goal
              </button>
            </div>
            <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
              {goals.map(goal => (
                <div key={goal.id} className="border border-[var(--border)] rounded-lg overflow-hidden" style={{ borderLeftColor: colorFor(goal.type), borderLeftWidth: 3 }}>
                  <div className="flex items-center justify-between p-2 bg-[var(--bg-card)] cursor-pointer"
                       onClick={() => setExpandedGoal(expandedGoal === goal.id ? null : goal.id)}>
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-sm">{GOAL_TYPES.find(t => t.value === goal.type)?.label.split(' ')[0] || '🎯'}</span>
                      <input value={goal.name} onChange={e => { e.stopPropagation(); updateGoal(goal.id, 'name', e.target.value) }}
                        onClick={e => e.stopPropagation()}
                        className="input text-xs py-0.5 flex-1 min-w-0 font-medium bg-transparent border-0 focus:border focus:border-[var(--border)] px-1" />
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {expandedGoal === goal.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      <button onClick={e => { e.stopPropagation(); removeGoal(goal.id) }} className="text-[var(--text-muted)] hover:text-red-400 p-0.5">
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>

                  {expandedGoal === goal.id && (
                    <div className="p-2 space-y-2 bg-[var(--bg)]">
                      <select value={goal.type} onChange={e => updateGoal(goal.id, 'type', e.target.value)}
                        className="input text-xs py-1 w-full">
                        {GOAL_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                      </select>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { field: 'target_amount',      label: 'Target ($)',    prefix: '$' },
                          { field: 'current_savings',    label: 'Current ($)',   prefix: '$' },
                          { field: 'monthly_contribution',label: 'Monthly ($)', prefix: '$' },
                          { field: 'deadline_years',     label: 'Years',         suffix: 'yr' },
                          { field: 'expected_return',    label: 'Return (%)',    suffix: '%', step: 0.5 },
                        ].map(f => (
                          <div key={f.field}>
                            <label className="text-xs text-[var(--text-muted)]">{f.label}</label>
                            <div className="relative mt-0.5">
                              {f.prefix && <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">{f.prefix}</span>}
                              <input type="number" value={goal[f.field]} onChange={e => updateGoal(goal.id, f.field, parseFloat(e.target.value) || 0)}
                                step={f.step || 1} className={`input text-xs py-1 w-full ${f.prefix ? 'pl-5' : ''} ${f.suffix ? 'pr-6' : ''}`} />
                              {f.suffix && <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">{f.suffix}</span>}
                            </div>
                          </div>
                        ))}
                        <div>
                          <label className="text-xs text-[var(--text-muted)]">Priority</label>
                          <select value={goal.priority} onChange={e => updateGoal(goal.id, 'priority', e.target.value)} className="input text-xs py-1 w-full mt-0.5">
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending || goals.length === 0}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Projecting…' : 'Project My Goals'}
          </button>
          {mutation.isError && (
            <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3">
              {String(mutation.error)}
            </div>
          )}
        </div>

        {/* ── Results ──────────────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          {!data && !mutation.isPending && (
            <div className="empty-state">
              <Target size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Set your financial goals and project them forward</p>
            </div>
          )}
          {mutation.isPending && <div className="empty-state"><div className="spinner mx-auto mb-3" /><p>Projecting your goals…</p></div>}

          {data && (
            <>
              {/* Summary banner */}
              <div className={`card p-4 flex items-center gap-4 border-l-4 ${data.summary.all_funded ? 'border-green-500' : 'border-yellow-500'}`}>
                {data.summary.all_funded
                  ? <CheckCircle size={24} className="text-green-400 shrink-0" />
                  : <AlertCircle size={24} className="text-yellow-400 shrink-0" />}
                <div className="flex-1">
                  <div className="font-semibold">
                    {data.summary.goals_on_track} of {data.summary.total_goals} goals on track
                  </div>
                  <div className="text-xs text-[var(--text-muted)] mt-0.5">
                    Current: ${data.summary.total_monthly_current.toLocaleString()}/mo &nbsp;·&nbsp;
                    Needed: ${data.summary.total_monthly_needed.toLocaleString()}/mo
                    {data.summary.monthly_gap > 0 && (
                      <span className="text-red-400 ml-2">Gap: ${data.summary.monthly_gap.toLocaleString()}/mo</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Goal cards */}
              <div className="space-y-3">
                {goalResults.map(g => {
                  const pct = g.pct_funded
                  return (
                    <div key={g.name} className="card p-4" style={{ borderLeftColor: g.color, borderLeftWidth: 3 }}>
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <span className="text-base font-bold">{g.icon} {g.name}</span>
                          <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${g.on_track ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                            {g.on_track ? 'On Track' : 'Behind'}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">${(g.target / 1e6 >= 1 ? (g.target/1e6).toFixed(2) + 'M' : g.target.toLocaleString())}</div>
                          <div className="text-xs text-[var(--text-muted)]">target in {g.deadline_years}yr</div>
                        </div>
                      </div>

                      {/* Progress bar */}
                      <div className="mb-3">
                        <div className="flex justify-between text-xs mb-1">
                          <span>Projected at deadline: <strong>${g.fv_at_deadline >= 1e6 ? (g.fv_at_deadline/1e6).toFixed(2)+'M' : g.fv_at_deadline.toLocaleString()}</strong></span>
                          <span style={{ color: g.color }}>{pct.toFixed(0)}% funded</span>
                        </div>
                        <div className="h-3 bg-[var(--bg)] rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700"
                               style={{ width: `${Math.min(pct, 100)}%`, background: g.color }} />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3 text-xs">
                        <div className="panel p-2 text-center">
                          <div className="text-[var(--text-muted)]">Monthly Need</div>
                          <div className="font-bold">${g.monthly_needed.toLocaleString()}/mo</div>
                          {g.extra_needed > 0 && <div className="text-red-400">+${g.extra_needed.toLocaleString()} more</div>}
                        </div>
                        <div className="panel p-2 text-center">
                          <div className="text-[var(--text-muted)]">Currently Saving</div>
                          <div className="font-bold">${g.monthly_contribution.toLocaleString()}/mo</div>
                        </div>
                        <div className="panel p-2 text-center">
                          <div className="text-[var(--text-muted)]">Time to Goal</div>
                          <div className="font-bold">
                            {g.years_to_goal_at_current ? `${g.years_to_goal_at_current}yr` : 'Never'}
                          </div>
                          {g.years_to_goal_at_current && g.years_to_goal_at_current > g.deadline_years && (
                            <div className="text-red-400">{(g.years_to_goal_at_current - g.deadline_years).toFixed(1)}yr late</div>
                          )}
                        </div>
                      </div>

                      {/* Sensitivity mini-table */}
                      <details className="mt-3">
                        <summary className="text-xs text-[var(--accent)] cursor-pointer">Contribution Sensitivity</summary>
                        <div className="mt-2 overflow-x-auto">
                          <table className="data-table text-xs w-full">
                            <thead><tr>
                              <th>Contribution</th><th>Monthly Amt</th><th>Projected</th><th>On Track?</th><th>Years to Goal</th>
                            </tr></thead>
                            <tbody>
                              {g.contribution_sensitivity.map(s => (
                                <tr key={s.label}>
                                  <td>{s.label}</td>
                                  <td>${s.monthly.toLocaleString()}</td>
                                  <td>${s.fv_at_deadline >= 1e6 ? (s.fv_at_deadline/1e6).toFixed(2)+'M' : s.fv_at_deadline.toLocaleString()}</td>
                                  <td className={s.on_track ? 'text-green-400' : 'text-red-400'}>{s.on_track ? '✓' : '✗'}</td>
                                  <td>{s.years_to_goal ? `${s.years_to_goal}yr` : '—'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    </div>
                  )
                })}
              </div>

              {projChart && <div className="card p-4"><PlotlyChart data={projChart.data} layout={projChart.layout} /></div>}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
