import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { Plus, Trash2, Search } from 'lucide-react'

const DEFAULT_HOLDINGS = [
  { id: 1, ticker: 'VTI', weight: 40 },
  { id: 2, ticker: 'VXUS', weight: 20 },
  { id: 3, ticker: 'BND', weight: 30 },
  { id: 4, ticker: 'VNQ', weight: 10 },
]

let nextId = 5

const PIE_COLORS = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#ec4899','#f97316','#6b7280','#14b8a6']

export default function PortfolioXRayPage() {
  const [holdings, setHoldings] = useState(DEFAULT_HOLDINGS)

  const mutation = useMutation({
    mutationFn: () => api.post('/xray/analyze', {
      holdings: holdings.map(h => ({ ticker: h.ticker, weight: h.weight }))
    }).then(r => r.data),
  })

  const add = () => setHoldings(p => [...p, { id: nextId++, ticker: '', weight: 0 }])
  const remove = (id) => setHoldings(p => p.filter(h => h.id !== id))
  const update = (id, field, value) => setHoldings(p => p.map(h => h.id === id ? { ...h, [field]: value } : h))

  const totalWeight = holdings.reduce((s, h) => s + (parseFloat(h.weight) || 0), 0)

  const d = mutation.data

  const makePie = (alloc, title) => ({
    data: [{ labels: alloc.map(a => a.label), values: alloc.map(a => a.pct), type: 'pie', hole: 0.4,
      marker: { colors: PIE_COLORS }, hovertemplate: '%{label}: %{value:.1f}%<extra></extra>' }],
    layout: { title, height: 260, showlegend: true },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Portfolio X-Ray</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Deep-dive into your portfolio's true composition — asset class, sector, and geographic exposure.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <div className="flex justify-between items-center border-b border-[var(--border)] pb-2">
              <h2 className="font-semibold text-sm">Holdings</h2>
              <div className="flex items-center gap-3">
                <span className={`text-xs ${Math.abs(totalWeight - 100) < 0.5 ? 'text-green-400' : 'text-yellow-400'}`}>{totalWeight.toFixed(1)}%</span>
                <button onClick={add} className="flex items-center gap-1 text-xs text-[var(--accent)] hover:opacity-80">
                  <Plus size={12} /> Add
                </button>
              </div>
            </div>
            <div className="space-y-2">
              {holdings.map(h => (
                <div key={h.id} className="flex items-center gap-2">
                  <input value={h.ticker} onChange={e => update(h.id, 'ticker', e.target.value.toUpperCase())}
                    placeholder="TICK" className="input text-xs py-1 w-20 uppercase" />
                  <div className="relative flex-1">
                    <input type="number" value={h.weight} onChange={e => update(h.id, 'weight', parseFloat(e.target.value) || 0)}
                      step={1} min={0} max={100} className="input text-xs py-1 w-full pr-6" />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-[var(--text-muted)]">%</span>
                  </div>
                  <button onClick={() => remove(h.id)} className="text-[var(--text-muted)] hover:text-red-400">
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending || holdings.length === 0}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Analyzing…' : 'Analyze Portfolio'}
          </button>
          {mutation.isError && <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3">{String(mutation.error)}</div>}
        </div>

        <div className="lg:col-span-2 space-y-5">
          {!d && !mutation.isPending && (
            <div className="empty-state">
              <Search size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Add your holdings and run the X-Ray analysis</p>
              <p className="text-sm mt-1 text-[var(--text-muted)]">Fetches live data from Yahoo Finance</p>
            </div>
          )}
          {mutation.isPending && <div className="empty-state"><div className="spinner mx-auto mb-3" /><p>Fetching portfolio data from Yahoo Finance…</p></div>}

          {d && (
            <>
              {/* Holdings table */}
              <div className="card p-4">
                <h3 className="font-semibold text-sm mb-3">Holdings Detail</h3>
                <div className="overflow-x-auto">
                  <table className="data-table text-xs w-full">
                    <thead><tr><th>Ticker</th><th>Name</th><th>Weight</th><th>Asset Class</th><th>Sector</th><th>P/E</th><th>Div Yield</th><th>Beta</th></tr></thead>
                    <tbody>
                      {d.holdings.map(h => (
                        <tr key={h.ticker}>
                          <td className="font-bold">{h.ticker}</td>
                          <td className="max-w-[120px] truncate" title={h.name}>{h.name}</td>
                          <td>{h.weight.toFixed(1)}%</td>
                          <td>{h.asset_class}</td>
                          <td>{h.sector}</td>
                          <td>{h.pe_ratio ?? '—'}</td>
                          <td>{h.dividend_yield_pct != null ? `${h.dividend_yield_pct}%` : '—'}</td>
                          <td>{h.beta ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Allocation pies */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { key: 'asset_class_allocation', title: 'Asset Class' },
                  { key: 'sector_allocation', title: 'Sector' },
                  { key: 'geographic_allocation', title: 'Geography' },
                ].map(({ key, title }) => d[key]?.length > 0 && (
                  <div key={key} className="card p-4">
                    <PlotlyChart data={makePie(d[key], title).data} layout={makePie(d[key], title).layout} />
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
