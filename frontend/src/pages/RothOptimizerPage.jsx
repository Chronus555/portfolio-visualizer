import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { ShieldCheck, ArrowRightLeft } from 'lucide-react'

const DEFAULTS = {
  current_income: 120000,
  retirement_income: 70000,
  annual_contribution: 7000,
  years_to_retirement: 25,
  years_in_retirement: 30,
  expected_return: 7.0,
  // conversion
  trad_balance: 200000,
  top_bracket_ceiling: 100525,
  retirement_rate: 22.0,
}

const TAX_BRACKETS = [
  { label: '10% bracket ceiling', value: 11600 },
  { label: '12% bracket ceiling', value: 47150 },
  { label: '22% bracket ceiling', value: 100525 },
  { label: '24% bracket ceiling', value: 191950 },
  { label: '32% bracket ceiling', value: 243725 },
]

export default function RothOptimizerPage() {
  const [form, setForm] = useState(DEFAULTS)
  const [mode, setMode] = useState('compare') // 'compare' | 'conversion'
  const num = (k, e) => setForm(p => ({ ...p, [k]: parseFloat(e.target.value) || 0 }))

  const compareMut = useMutation({ mutationFn: () => api.post('/roth/compare', form).then(r => r.data) })
  const convMut = useMutation({ mutationFn: () => api.post('/roth/conversion', form).then(r => r.data) })
  const mutation = mode === 'compare' ? compareMut : convMut
  const runAnalysis = () => mode === 'compare' ? compareMut.mutate() : convMut.mutate()

  const d = mode === 'compare' ? compareMut.data : convMut.data

  const compareChart = compareMut.data ? {
    data: [
      { x: compareMut.data.yearly.map(r => r.year), y: compareMut.data.yearly.map(r => r.traditional_after_tax), type: 'scatter', mode: 'lines', name: 'Traditional (after-tax)', line: { color: '#f59e0b', width: 2 }, hovertemplate: 'Year %{x}: $%{y:,.0f}<extra></extra>' },
      { x: compareMut.data.yearly.map(r => r.year), y: compareMut.data.yearly.map(r => r.roth_after_tax), type: 'scatter', mode: 'lines', name: 'Roth (tax-free)', line: { color: '#3b82f6', width: 2 }, hovertemplate: 'Year %{x}: $%{y:,.0f}<extra></extra>' },
    ],
    layout: { title: 'After-Tax Balance: Roth vs Traditional', xaxis: { title: 'Years' }, yaxis: { title: 'After-Tax Value ($)', tickformat: '$,.0f' }, height: 300 },
  } : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Roth vs Traditional IRA Optimizer</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Compare after-tax outcomes and find the optimal Roth conversion strategy based on 2024 tax brackets.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-4">
          {/* Mode toggle */}
          <div className="card p-1 flex gap-1">
            {[{ id: 'compare', label: 'Roth vs Traditional' }, { id: 'conversion', label: 'Conversion Optimizer' }].map(m => (
              <button key={m.id} onClick={() => setMode(m.id)}
                className={`flex-1 text-xs py-2 rounded-md font-medium transition-colors ${mode === m.id ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-muted)] hover:text-[var(--text)]'}`}>
                {m.label}
              </button>
            ))}
          </div>

          {mode === 'compare' ? (
            <div className="card p-4 space-y-3">
              <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Your Situation</h2>
              {[
                { label: 'Current Annual Income', key: 'current_income', prefix: '$' },
                { label: 'Expected Retirement Income', key: 'retirement_income', prefix: '$' },
                { label: 'Annual IRA Contribution', key: 'annual_contribution', prefix: '$' },
                { label: 'Years to Retirement', key: 'years_to_retirement', suffix: 'yr' },
                { label: 'Years in Retirement', key: 'years_in_retirement', suffix: 'yr' },
                { label: 'Expected Return', key: 'expected_return', suffix: '%', step: 0.5 },
              ].map(f => (
                <div key={f.key}>
                  <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">{f.label}</label>
                  <div className="relative flex items-center">
                    {f.prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{f.prefix}</span>}
                    <input type="number" value={form[f.key]} onChange={e => num(f.key, e)}
                      step={f.step || 1} className={`input w-full text-sm ${f.prefix ? 'pl-7' : ''} ${f.suffix ? 'pr-10' : ''}`} />
                    {f.suffix && <span className="absolute right-3 text-sm text-[var(--text-muted)]">{f.suffix}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card p-4 space-y-3">
              <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Conversion Setup</h2>
              {[
                { label: 'Traditional IRA Balance', key: 'trad_balance', prefix: '$' },
                { label: 'Current Annual Income', key: 'current_income', prefix: '$' },
                { label: 'Expected Return', key: 'expected_return', suffix: '%', step: 0.5 },
                { label: 'Years to Retirement', key: 'years_to_retirement', suffix: 'yr' },
                { label: 'Retirement Tax Rate', key: 'retirement_rate', suffix: '%', step: 1 },
              ].map(f => (
                <div key={f.key}>
                  <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">{f.label}</label>
                  <div className="relative flex items-center">
                    {f.prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{f.prefix}</span>}
                    <input type="number" value={form[f.key]} onChange={e => num(f.key, e)}
                      step={f.step || 1} className={`input w-full text-sm ${f.prefix ? 'pl-7' : ''} ${f.suffix ? 'pr-10' : ''}`} />
                    {f.suffix && <span className="absolute right-3 text-sm text-[var(--text-muted)]">{f.suffix}</span>}
                  </div>
                </div>
              ))}
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">Convert Up To Bracket</label>
                <select value={form.top_bracket_ceiling} onChange={e => setForm(p => ({ ...p, top_bracket_ceiling: parseFloat(e.target.value) }))}
                  className="input w-full text-sm">
                  {TAX_BRACKETS.map(b => <option key={b.value} value={b.value}>{b.label} (${b.value.toLocaleString()})</option>)}
                </select>
              </div>
            </div>
          )}

          <button onClick={runAnalysis} disabled={mutation.isPending}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Analyzing…' : 'Analyze'}
          </button>
          {mutation.isError && <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3">{String(mutation.error)}</div>}
        </div>

        <div className="lg:col-span-2 space-y-5">
          {!d && !mutation.isPending && (
            <div className="empty-state">
              <ArrowRightLeft size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Compare Roth vs Traditional or optimize your conversion strategy</p>
            </div>
          )}
          {mutation.isPending && <div className="empty-state"><div className="spinner mx-auto mb-3" /><p>Analyzing…</p></div>}

          {mode === 'compare' && compareMut.data && (() => {
            const cd = compareMut.data
            return (
              <>
                <div className={`card p-4 flex items-center gap-4 border-l-4 ${cd.winner === 'Roth' ? 'border-blue-500' : 'border-yellow-500'}`}>
                  <ShieldCheck size={24} className={cd.winner === 'Roth' ? 'text-blue-400 shrink-0' : 'text-yellow-400 shrink-0'} />
                  <div>
                    <div className="font-semibold">{cd.winner} is better by ${Math.abs(cd.roth_advantage).toLocaleString()} after-tax</div>
                    <div className="text-xs text-[var(--text-muted)] mt-0.5">
                      Current marginal rate: {cd.current_marginal_rate}% · Retirement rate: {cd.retirement_marginal_rate}%
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Traditional IRA', k: 'traditional', color: '#f59e0b' },
                    { label: 'Roth IRA', k: 'roth', color: '#3b82f6' },
                  ].map(({ label, k, color }) => (
                    <div key={k} className="card p-4" style={{ borderLeftColor: color, borderLeftWidth: 3 }}>
                      <div className="font-semibold text-sm mb-3">{label}</div>
                      <div className="space-y-1.5 text-xs">
                        <div className="flex justify-between"><span className="text-[var(--text-muted)]">Balance at Retirement</span><span className="font-bold">${(cd[k].pre_tax_balance ?? cd[k].balance ?? 0).toLocaleString()}</span></div>
                        <div className="flex justify-between"><span className="text-[var(--text-muted)]">After-Tax Value</span><span className="font-bold" style={{ color }}>${cd[k].after_tax_balance.toLocaleString()}</span></div>
                        <div className="flex justify-between"><span className="text-[var(--text-muted)]">Annual Income</span><span className="font-bold">${cd[k].annual_retirement_income.toLocaleString()}/yr</span></div>
                      </div>
                    </div>
                  ))}
                </div>

                {compareChart && <div className="card p-4"><PlotlyChart data={compareChart.data} layout={compareChart.layout} /></div>}
              </>
            )
          })()}

          {mode === 'conversion' && convMut.data && (() => {
            const cv = convMut.data
            return (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: 'Annual Conversion', value: `$${cv.annual_conversion_space.toLocaleString()}` },
                    { label: 'Tax Due This Year', value: `$${cv.tax_on_conversion.toLocaleString()}`, color: 'text-red-400' },
                    { label: 'Roth FV (tax-free)', value: `$${cv.fv_roth_tax_free.toLocaleString()}`, color: 'text-blue-400' },
                    { label: 'Roth Advantage', value: `$${cv.roth_advantage.toLocaleString()}`, color: 'text-green-400' },
                  ].map(m => (
                    <div key={m.label} className="card p-3 text-center">
                      <div className="text-xs text-[var(--text-muted)] mb-1">{m.label}</div>
                      <div className={`text-base font-bold ${m.color || ''}`}>{m.value}</div>
                    </div>
                  ))}
                </div>
                <div className="card p-4">
                  <h3 className="font-semibold text-sm mb-3">Conversion Plan ({cv.years_to_convert} years)</h3>
                  <div className="overflow-x-auto max-h-64">
                    <table className="data-table text-xs w-full">
                      <thead><tr><th>Year</th><th>Convert</th><th>Tax Due</th><th>Remaining Trad.</th></tr></thead>
                      <tbody>
                        {cv.conversion_plan.map(r => (
                          <tr key={r.year}>
                            <td>{r.year}</td>
                            <td>${r.convert_amount.toLocaleString()}</td>
                            <td className="text-red-400">${r.tax_due.toLocaleString()}</td>
                            <td>${r.remaining_traditional.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )
          })()}
        </div>
      </div>
    </div>
  )
}
