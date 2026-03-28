import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { ShieldCheck, TrendingDown, Info } from 'lucide-react'

const ALL_STRATEGIES = [
  { id: 'fixed_percent_4',       label: '4% Rule' },
  { id: 'fixed_percent_dynamic', label: 'Dynamic 4%' },
  { id: 'fixed_dollar_inflation',label: 'Fixed + Inflation' },
  { id: 'guardrails',            label: 'Guardrails' },
  { id: 'floor_ceiling',         label: 'Floor-Ceiling' },
  { id: 'rmd_based',             label: 'RMD-Based' },
  { id: 'bucket',                label: 'Bucket Strategy' },
]

const DEFAULT = {
  portfolio_value: 1_000_000,
  annual_expenses: 40_000,
  retirement_years: 30,
  stock_allocation: 60,
  inflation: 3.0,
  simulations: 5000,
  strategies: ALL_STRATEGIES.map(s => s.id),
}

export default function SWRPage() {
  const [form, setForm] = useState(DEFAULT)

  const mutation = useMutation({
    mutationFn: () => api.post('/swr/analyze', form).then(r => r.data),
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(p => ({ ...p, [name]: parseFloat(value) || 0 }))
  }

  const toggleStrategy = (id) => {
    setForm(p => ({
      ...p,
      strategies: p.strategies.includes(id)
        ? p.strategies.filter(s => s !== id)
        : [...p.strategies, id],
    }))
  }

  const data = mutation.data
  const stratResults = data?.strategies || {}
  const rankings = data?.rankings || []
  const swr = data?.swr_sensitivity || {}

  // Colors for strategies
  const colorMap = {
    'fixed_percent_4':        '#3b82f6',
    'fixed_percent_dynamic':  '#8b5cf6',
    'fixed_dollar_inflation': '#10b981',
    'guardrails':             '#f59e0b',
    'floor_ceiling':          '#ef4444',
    'rmd_based':              '#06b6d4',
    'bucket':                 '#ec4899',
  }

  // Withdrawal history chart
  const wdChart = data ? {
    data: Object.entries(stratResults).map(([id, res]) => ({
      x: res.year_labels,
      y: res.avg_annual_withdrawals,
      type: 'scatter', mode: 'lines',
      name: res.name,
      line: { color: colorMap[id] || '#6b7280', width: 2 },
      hovertemplate: 'Year %{x}: $%{y:,.0f}/yr<extra>' + res.name + '</extra>',
    })),
    layout: {
      title: 'Average Annual Withdrawal by Strategy',
      xaxis: { title: 'Year of Retirement' },
      yaxis: { title: 'Annual Withdrawal ($)', tickformat: '$,.0f' },
      height: 300,
    },
  } : null

  // SWR sensitivity bar chart
  const swrChart = data ? {
    data: [{
      x: Object.keys(swr).map(k => `${k}% SWR`),
      y: Object.values(swr),
      type: 'bar',
      marker: { color: Object.values(swr).map(v => v >= 90 ? '#10b981' : v >= 75 ? '#f59e0b' : '#ef4444') },
      text: Object.values(swr).map(v => `${v}%`),
      textposition: 'outside',
      hovertemplate: '%{x}: %{y:.1f}% survival<extra></extra>',
    }],
    layout: {
      title: 'Survival Rate by Withdrawal Rate',
      xaxis: { title: 'Withdrawal Rate' },
      yaxis: { title: 'Survival Rate (%)', range: [0, 105] },
      height: 260,
      shapes: [{ type: 'line', x0: -0.5, x1: 4.5, y0: 90, y1: 90,
                  line: { color: '#10b981', dash: 'dash', width: 1 } }],
    },
  } : null

  const wr = form.portfolio_value > 0 ? (form.annual_expenses / form.portfolio_value * 100).toFixed(1) : '—'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Safe Withdrawal Rate Analyzer</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Compare 7 withdrawal strategies with Monte Carlo simulation. Find the right balance of income certainty vs portfolio longevity.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Inputs ───────────────────────────────────────────────────── */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Portfolio Setup</h2>
            {[
              { label: 'Portfolio Value', name: 'portfolio_value', prefix: '$' },
              { label: 'Annual Expenses', name: 'annual_expenses', prefix: '$' },
              { label: 'Retirement Duration (years)', name: 'retirement_years', min: 5, max: 60 },
              { label: 'Stock Allocation', name: 'stock_allocation', suffix: '%', min: 0, max: 100 },
              { label: 'Inflation Rate', name: 'inflation', suffix: '%', min: 0, max: 15, step: 0.1 },
              { label: 'Simulations', name: 'simulations', min: 500, max: 20000, step: 500 },
            ].map(f => (
              <div key={f.name}>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">{f.label}</label>
                <div className="relative flex items-center">
                  {f.prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{f.prefix}</span>}
                  <input type="number" name={f.name} value={form[f.name]} onChange={handleChange}
                    min={f.min} max={f.max} step={f.step || 1}
                    className={`input w-full text-sm ${f.prefix ? 'pl-7' : ''} ${f.suffix ? 'pr-8' : ''}`} />
                  {f.suffix && <span className="absolute right-3 text-sm text-[var(--text-muted)]">{f.suffix}</span>}
                </div>
              </div>
            ))}
            <div className="text-xs text-[var(--text-muted)] bg-[var(--bg)] rounded p-2 flex gap-2 items-start">
              <Info size={12} className="mt-0.5 shrink-0" />
              Current withdrawal rate: <strong className={parseFloat(wr) > 4.5 ? 'text-red-400' : 'text-green-400'}>{wr}%</strong>
            </div>
          </div>

          <div className="card p-4 space-y-2">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Strategies to Compare</h2>
            {ALL_STRATEGIES.map(s => (
              <label key={s.id} className="flex items-center gap-2 cursor-pointer py-0.5">
                <input type="checkbox" checked={form.strategies.includes(s.id)} onChange={() => toggleStrategy(s.id)}
                  className="rounded accent-[var(--accent)]" />
                <span className="text-sm" style={{ color: colorMap[s.id] }}>{s.label}</span>
              </label>
            ))}
          </div>

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending || form.strategies.length === 0}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Simulating…' : 'Analyze Strategies'}
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
              <ShieldCheck size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Select strategies and run the simulation</p>
            </div>
          )}
          {mutation.isPending && (
            <div className="empty-state">
              <div className="spinner mx-auto mb-3" />
              <p>Running {form.simulations.toLocaleString()} Monte Carlo simulations per strategy…</p>
            </div>
          )}

          {data && (
            <>
              {/* Rankings */}
              <div className="card p-4">
                <h3 className="font-semibold text-sm mb-3">Strategy Rankings — Survival Rate</h3>
                <div className="space-y-2">
                  {rankings.map((r, i) => (
                    <div key={r.strategy} className="flex items-center gap-3">
                      <span className="text-xs font-mono w-4 text-[var(--text-muted)]">#{i+1}</span>
                      <div className="flex-1">
                        <div className="flex justify-between text-xs mb-0.5">
                          <span className="font-medium">{r.name}</span>
                          <span className={r.survival_rate >= 90 ? 'text-green-400' : r.survival_rate >= 75 ? 'text-yellow-400' : 'text-red-400'}>
                            {r.survival_rate}% survival
                          </span>
                        </div>
                        <div className="h-2 bg-[var(--bg)] rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700"
                               style={{ width: `${r.survival_rate}%`, background: colorMap[r.strategy] }} />
                        </div>
                      </div>
                      <span className="text-xs text-[var(--text-muted)] w-20 text-right">
                        avg end: ${(r.avg_final / 1e6).toFixed(2)}M
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Strategy detail cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(stratResults).map(([id, res]) => (
                  <div key={id} className="card p-4" style={{ borderLeftColor: colorMap[id], borderLeftWidth: 3 }}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-sm">{res.name}</span>
                      <span className={`text-lg font-bold ${res.survival_rate >= 90 ? 'text-green-400' : res.survival_rate >= 75 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {res.survival_rate}%
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-muted)] mb-2">{res.description}</p>
                    <div className="grid grid-cols-2 gap-1 text-xs">
                      <div>Avg Final: <span className="font-medium">${(res.avg_final_balance/1e6).toFixed(2)}M</span></div>
                      <div>Median Final: <span className="font-medium">${(res.median_final_balance/1e6).toFixed(2)}M</span></div>
                      <div>10th %ile: <span className="font-medium text-red-400">${(res.p10_final_balance/1e6).toFixed(2)}M</span></div>
                      <div>Initial WR: <span className="font-medium">{res.initial_withdrawal_rate}%</span></div>
                    </div>
                    <div className="mt-2 pt-2 border-t border-[var(--border)] grid grid-cols-2 gap-1 text-xs text-[var(--text-muted)]">
                      <div title={res.pros}>✅ {res.pros?.substring(0, 50)}{res.pros?.length > 50 ? '…' : ''}</div>
                      <div title={res.cons}>⚠️ {res.cons?.substring(0, 50)}{res.cons?.length > 50 ? '…' : ''}</div>
                    </div>
                  </div>
                ))}
              </div>

              {wdChart  && <div className="card p-4"><PlotlyChart data={wdChart.data}  layout={wdChart.layout}  /></div>}
              {swrChart && <div className="card p-4">
                <PlotlyChart data={swrChart.data} layout={swrChart.layout} />
                <p className="text-xs text-[var(--text-muted)] mt-1 flex gap-1.5 items-start">
                  <Info size={12} className="mt-0.5 shrink-0" />
                  Green dashed line = 90% survival threshold. Portfolio: {form.stock_allocation}% stocks / {100 - form.stock_allocation}% bonds, {form.retirement_years}-year retirement.
                </p>
              </div>}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
