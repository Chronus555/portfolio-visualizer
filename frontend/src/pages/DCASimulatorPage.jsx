import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { TrendingUp, Calendar } from 'lucide-react'

const DEFAULTS = { ticker: 'SPY', monthly_amount: 500, start_year: 2010, end_year: 2024 }

export default function DCASimulatorPage() {
  const [form, setForm] = useState(DEFAULTS)
  const mutation = useMutation({
    mutationFn: () => api.post('/dca/simulate', form).then(r => r.data),
  })
  const num = (k, e) => setForm(p => ({ ...p, [k]: parseFloat(e.target.value) || 0 }))
  const d = mutation.data

  const chart = d ? {
    data: [
      { x: d.dca.history.map(h => h.date), y: d.dca.history.map(h => h.value), type: 'scatter', mode: 'lines', name: 'DCA Value', line: { color: '#3b82f6', width: 2 }, hovertemplate: '%{x}: $%{y:,.0f}<extra>DCA</extra>' },
      { x: d.lump_sum.history.map(h => h.date), y: d.lump_sum.history.map(h => h.value), type: 'scatter', mode: 'lines', name: 'Lump Sum Value', line: { color: '#8b5cf6', width: 2, dash: 'dash' }, hovertemplate: '%{x}: $%{y:,.0f}<extra>Lump Sum</extra>' },
      { x: d.dca.history.map(h => h.date), y: d.dca.history.map(h => h.invested), type: 'scatter', mode: 'lines', name: 'Total Invested', line: { color: '#6b7280', width: 1, dash: 'dot' }, hovertemplate: '%{x}: $%{y:,.0f}<extra>Invested</extra>' },
    ],
    layout: { title: `DCA vs Lump Sum — ${d?.ticker || ''}`, xaxis: { title: 'Date' }, yaxis: { title: 'Portfolio Value ($)', tickformat: '$,.0f' }, height: 350 },
  } : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">DCA vs Lump Sum Simulator</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Compare dollar-cost averaging (investing monthly) against investing a lump sum upfront — using real historical prices.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Settings</h2>
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">Ticker</label>
              <input value={form.ticker} onChange={e => setForm(p => ({ ...p, ticker: e.target.value.toUpperCase() }))}
                className="input w-full text-sm uppercase" placeholder="SPY" />
            </div>
            {[
              { label: 'Monthly DCA Amount', key: 'monthly_amount', prefix: '$' },
              { label: 'Start Year', key: 'start_year' },
              { label: 'End Year', key: 'end_year' },
            ].map(f => (
              <div key={f.key}>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">{f.label}</label>
                <div className="relative flex items-center">
                  {f.prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{f.prefix}</span>}
                  <input type="number" value={form[f.key]} onChange={e => num(f.key, e)}
                    className={`input w-full text-sm ${f.prefix ? 'pl-7' : ''}`} />
                </div>
              </div>
            ))}
          </div>
          <button onClick={() => mutation.mutate()} disabled={mutation.isPending}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Simulating…' : 'Run Simulation'}
          </button>
          {mutation.isError && <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3">{String(mutation.error)}</div>}
        </div>

        <div className="lg:col-span-2 space-y-5">
          {!d && !mutation.isPending && (
            <div className="empty-state">
              <Calendar size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Set your parameters and run the simulation</p>
            </div>
          )}
          {mutation.isPending && <div className="empty-state"><div className="spinner mx-auto mb-3" /><p>Fetching historical data…</p></div>}

          {d && (
            <>
              <div className={`card p-4 flex items-center gap-4 border-l-4 ${d.dca_wins ? 'border-blue-500' : 'border-purple-500'}`}>
                <TrendingUp size={24} className={d.dca_wins ? 'text-blue-400 shrink-0' : 'text-purple-400 shrink-0'} />
                <div>
                  <div className="font-semibold">{d.dca_wins ? 'DCA outperformed Lump Sum' : 'Lump Sum outperformed DCA'}</div>
                  <div className="text-xs text-[var(--text-muted)] mt-0.5">
                    {d.months} months · ${d.monthly_amount}/mo · Total invested: ${d.total_invested.toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: 'DCA', res: d.dca, color: '#3b82f6', winner: d.dca_wins },
                  { label: 'Lump Sum', res: d.lump_sum, color: '#8b5cf6', winner: !d.dca_wins },
                ].map(({ label, res, color, winner }) => (
                  <div key={label} className="card p-4" style={{ borderLeftColor: color, borderLeftWidth: 3 }}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-sm">{label}</span>
                      {winner && <span className="text-xs bg-green-500/10 text-green-400 px-2 py-0.5 rounded-full">Winner</span>}
                    </div>
                    <div className="text-2xl font-bold mb-1">${res.final_value.toLocaleString()}</div>
                    <div className="text-sm" style={{ color }}>+{res.total_return_pct.toFixed(1)}% total return</div>
                  </div>
                ))}
              </div>

              {chart && <div className="card p-4"><PlotlyChart data={chart.data} layout={chart.layout} /></div>}

              <div className="card p-4">
                <h3 className="font-semibold text-sm mb-2">Asset Statistics — {d.ticker}</h3>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Annualized Return</div><div className="font-bold text-green-400">{d.asset_stats.annual_return_pct}%</div></div>
                  <div className="panel p-2 text-center"><div className="text-[var(--text-muted)]">Annual Volatility</div><div className="font-bold text-yellow-400">{d.asset_stats.annual_volatility_pct}%</div></div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
