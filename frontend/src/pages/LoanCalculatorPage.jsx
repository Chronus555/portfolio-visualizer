import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { Home, DollarSign, TrendingDown, RefreshCw } from 'lucide-react'

const DEFAULTS = {
  principal: 400000,
  annual_rate: 6.5,
  years: 30,
  extra_monthly: 0,
  property_value: 500000,
  monthly_rent: 2500,
  home_appreciation: 3.0,
  new_rate: 5.5,
  closing_costs: 8000,
}

export default function LoanCalculatorPage() {
  const [form, setForm] = useState(DEFAULTS)
  const [showRefi, setShowRefi] = useState(false)
  const [showRentBuy, setShowRentBuy] = useState(false)

  const mutation = useMutation({
    mutationFn: () => api.post('/loan/analyze', {
      ...form,
      new_rate: showRefi ? form.new_rate : null,
      property_value: showRentBuy ? form.property_value : null,
      monthly_rent: showRentBuy ? form.monthly_rent : null,
    }).then(r => r.data),
  })

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))
  const num = (k, e) => set(k, parseFloat(e.target.value) || 0)

  const d = mutation.data

  // Amortization chart
  const amorChart = d ? {
    data: [
      { x: d.yearly.map(r => r.year), y: d.yearly.map(r => r.balance), type: 'scatter', mode: 'lines', name: 'Remaining Balance', line: { color: '#3b82f6', width: 2 }, fill: 'tozeroy', fillcolor: 'rgba(59,130,246,0.1)', hovertemplate: 'Year %{x}: $%{y:,.0f}<extra></extra>' },
      { x: d.yearly.map(r => r.year), y: d.yearly.map(r => r.cum_interest), type: 'scatter', mode: 'lines', name: 'Cumulative Interest', line: { color: '#ef4444', width: 2 }, hovertemplate: 'Year %{x}: $%{y:,.0f}<extra></extra>' },
    ],
    layout: { title: 'Loan Balance & Interest Over Time', xaxis: { title: 'Year' }, yaxis: { title: 'Amount ($)', tickformat: '$,.0f' }, height: 300 },
  } : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Loan & Mortgage Calculator</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Amortization schedule, extra payments, refinancing break-even, and rent vs buy analysis.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Inputs */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Loan Details</h2>
            {[
              { label: 'Loan Amount', key: 'principal', prefix: '$' },
              { label: 'Annual Interest Rate', key: 'annual_rate', suffix: '%', step: 0.1 },
              { label: 'Loan Term', key: 'years', suffix: 'yr' },
              { label: 'Extra Monthly Payment', key: 'extra_monthly', prefix: '$' },
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

          {/* Rent vs Buy toggle */}
          <div className="card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-sm">Rent vs Buy</h2>
              <button onClick={() => setShowRentBuy(v => !v)} className={`text-xs px-2 py-0.5 rounded ${showRentBuy ? 'bg-green-500/10 text-green-400' : 'text-[var(--text-muted)]'}`}>
                {showRentBuy ? 'On' : 'Off'}
              </button>
            </div>
            {showRentBuy && (
              <div className="space-y-2">
                {[
                  { label: 'Property Value', key: 'property_value', prefix: '$' },
                  { label: 'Comparable Monthly Rent', key: 'monthly_rent', prefix: '$' },
                  { label: 'Home Appreciation Rate', key: 'home_appreciation', suffix: '%', step: 0.5 },
                ].map(f => (
                  <div key={f.key}>
                    <label className="block text-xs text-[var(--text-muted)] mb-1">{f.label}</label>
                    <div className="relative flex items-center">
                      {f.prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{f.prefix}</span>}
                      <input type="number" value={form[f.key]} onChange={e => num(f.key, e)}
                        step={f.step || 1} className={`input w-full text-xs ${f.prefix ? 'pl-7' : ''} ${f.suffix ? 'pr-8' : ''}`} />
                      {f.suffix && <span className="absolute right-2 text-xs text-[var(--text-muted)]">{f.suffix}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Refi toggle */}
          <div className="card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-sm">Refinancing Analysis</h2>
              <button onClick={() => setShowRefi(v => !v)} className={`text-xs px-2 py-0.5 rounded ${showRefi ? 'bg-blue-500/10 text-blue-400' : 'text-[var(--text-muted)]'}`}>
                {showRefi ? 'On' : 'Off'}
              </button>
            </div>
            {showRefi && (
              <div className="space-y-2">
                {[
                  { label: 'New Interest Rate', key: 'new_rate', suffix: '%', step: 0.1 },
                  { label: 'Closing Costs', key: 'closing_costs', prefix: '$' },
                ].map(f => (
                  <div key={f.key}>
                    <label className="block text-xs text-[var(--text-muted)] mb-1">{f.label}</label>
                    <div className="relative flex items-center">
                      {f.prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{f.prefix}</span>}
                      <input type="number" value={form[f.key]} onChange={e => num(f.key, e)}
                        step={f.step || 1} className={`input w-full text-xs ${f.prefix ? 'pl-7' : ''} ${f.suffix ? 'pr-8' : ''}`} />
                      {f.suffix && <span className="absolute right-2 text-xs text-[var(--text-muted)]">{f.suffix}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Calculating…' : 'Calculate'}
          </button>
          {mutation.isError && <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3">{String(mutation.error)}</div>}
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-5">
          {!d && !mutation.isPending && (
            <div className="empty-state">
              <Home size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Enter your loan details to see the full breakdown</p>
            </div>
          )}
          {mutation.isPending && <div className="empty-state"><div className="spinner mx-auto mb-3" /><p>Calculating…</p></div>}

          {d && (
            <>
              {/* Key metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Monthly Payment', value: `$${d.monthly_payment.toLocaleString()}`, color: 'text-blue-400' },
                  { label: 'Total Interest', value: `$${d.total_interest.toLocaleString()}`, color: 'text-red-400' },
                  { label: 'Payoff Time', value: `${d.payoff_years}yr`, color: 'text-green-400' },
                  { label: 'Interest Saved', value: `$${d.interest_saved.toLocaleString()}`, color: d.interest_saved > 0 ? 'text-green-400' : 'text-[var(--text-muted)]' },
                ].map(m => (
                  <div key={m.label} className="card p-3 text-center">
                    <div className="text-xs text-[var(--text-muted)] mb-1">{m.label}</div>
                    <div className={`text-lg font-bold ${m.color}`}>{m.value}</div>
                  </div>
                ))}
              </div>

              {amorChart && <div className="card p-4"><PlotlyChart data={amorChart.data} layout={amorChart.layout} /></div>}

              {/* Refinancing */}
              {d.refinance && (
                <div className={`card p-4 border-l-4 ${d.refinance.worthwhile ? 'border-green-500' : 'border-yellow-500'}`}>
                  <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                    <RefreshCw size={14} /> Refinancing Analysis
                    <span className={`text-xs px-2 py-0.5 rounded-full ${d.refinance.worthwhile ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
                      {d.refinance.worthwhile ? 'Worth It' : 'Not Worth It'}
                    </span>
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">New Payment</div><div className="font-bold">${d.refinance.new_monthly.toLocaleString()}/mo</div></div>
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Monthly Savings</div><div className="font-bold text-green-400">${d.refinance.monthly_savings.toLocaleString()}/mo</div></div>
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Closing Costs</div><div className="font-bold">${d.refinance.closing_costs.toLocaleString()}</div></div>
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Break-Even</div><div className="font-bold">{d.refinance.breakeven_months ? `${d.refinance.breakeven_years}yr` : 'Never'}</div></div>
                  </div>
                </div>
              )}

              {/* Rent vs Buy */}
              {d.rent_vs_buy && (
                <div className={`card p-4 border-l-4 ${d.rent_vs_buy.advantage > 0 ? 'border-green-500' : 'border-red-500'}`}>
                  <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                    <Home size={14} /> Rent vs Buy
                    <span className={`text-xs px-2 py-0.5 rounded-full ${d.rent_vs_buy.advantage > 0 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                      {d.rent_vs_buy.advantage > 0 ? 'Buying Wins' : 'Renting Wins'}
                    </span>
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Home Value at End</div><div className="font-bold">${(d.rent_vs_buy.home_value_end/1e6).toFixed(2)}M</div></div>
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Equity Built</div><div className="font-bold text-green-400">${(d.rent_vs_buy.equity_built/1e6).toFixed(2)}M</div></div>
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Net Cost: Buy</div><div className="font-bold">${d.rent_vs_buy.net_cost_buy.toLocaleString()}</div></div>
                    <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Net Cost: Rent</div><div className="font-bold">${d.rent_vs_buy.net_cost_rent.toLocaleString()}</div></div>
                    <div className="panel p-2 text-center col-span-2"><div className="text-[var(--text-muted)]">Buying Advantage</div><div className={`font-bold text-lg ${d.rent_vs_buy.advantage > 0 ? 'text-green-400' : 'text-red-400'}`}>${Math.abs(d.rent_vs_buy.advantage).toLocaleString()}</div></div>
                  </div>
                </div>
              )}

              {/* Amortization table */}
              <div className="card p-4">
                <h3 className="font-semibold text-sm mb-3">Amortization Schedule (Yearly)</h3>
                <div className="overflow-x-auto max-h-64">
                  <table className="data-table text-xs w-full">
                    <thead><tr><th>Year</th><th>Balance</th><th>Interest Paid</th><th>Cumulative Interest</th></tr></thead>
                    <tbody>
                      {d.yearly.map(r => (
                        <tr key={r.year}>
                          <td>{r.year}</td>
                          <td>${r.balance.toLocaleString()}</td>
                          <td>${(d.schedule.filter(s => s.year === r.year).reduce((a, s) => a + s.interest_paid, 0)).toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                          <td>${r.cum_interest.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
