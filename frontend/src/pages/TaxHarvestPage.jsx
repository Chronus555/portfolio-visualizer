import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Leaf, Plus, Trash2, AlertCircle, CheckCircle2, ArrowRight, Info } from 'lucide-react'
import { scanTaxHarvest } from '../api/client'

const fmt$ = v => `$${Math.abs(Number(v)).toLocaleString('en-US', { maximumFractionDigits: 0 })}`

const DEFAULT_POSITIONS = [
  { ticker: 'VTI',  name: 'Vanguard Total Stock Market', shares: 100,  cost_basis: 220.00, purchase_date: '2022-03-15' },
  { ticker: 'QQQ',  name: 'Invesco QQQ',                 shares: 50,   cost_basis: 380.00, purchase_date: '2021-11-10' },
  { ticker: 'BND',  name: 'Vanguard Total Bond Market',  shares: 200,  cost_basis: 76.00,  purchase_date: '2023-01-05' },
]

export default function TaxHarvestPage() {
  const [positions, setPositions] = useState(DEFAULT_POSITIONS)
  const [taxRates, setTaxRates] = useState({ tax_rate_st: 0.37, tax_rate_lt: 0.20, state_tax_rate: 0.0 })

  const { mutate, data: results, isPending } = useMutation({
    mutationFn: scanTaxHarvest,
    onError: e => toast.error(e.message),
  })

  const addPosition = () => setPositions(p => [...p, { ticker: '', name: '', shares: 0, cost_basis: 0, purchase_date: '' }])
  const removePosition = i => setPositions(p => p.filter((_, idx) => idx !== i))
  const updatePosition = (i, field, val) =>
    setPositions(p => p.map((item, idx) => idx === i ? { ...item, [field]: val } : item))

  const handleScan = () => {
    if (!positions.length) { toast.error('Add at least one position'); return }
    mutate({ positions, ...taxRates })
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-5 items-start">
      {/* Left */}
      <div className="space-y-3">
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
              <Leaf size={14} className="text-emerald-500" /> Tax Rates
            </h2>
          </div>
          <div className="p-4 space-y-3">
            {[
              { label: 'Short-Term Rate', key: 'tax_rate_st', hint: 'Ordinary income (< 1 year)' },
              { label: 'Long-Term Rate',  key: 'tax_rate_lt', hint: 'Capital gains (≥ 1 year)' },
              { label: 'State Tax Rate',  key: 'state_tax_rate', hint: 'Added to federal rate' },
            ].map(({ label, key, hint }) => (
              <div key={key}>
                <label className="label">{label}</label>
                <div className="relative">
                  <input type="number" className="input text-sm pr-5" step="0.1"
                    value={(taxRates[key] * 100).toFixed(1)}
                    onChange={e => setTaxRates(r => ({ ...r, [key]: +e.target.value / 100 }))} />
                  <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">%</span>
                </div>
                <p className="text-[10px] text-gray-400 mt-1">{hint}</p>
              </div>
            ))}
          </div>
        </div>

        <button onClick={handleScan} disabled={isPending || !positions.length}
          className="btn-primary w-full flex items-center justify-center gap-2 py-2.5">
          {isPending ? <><span className="spinner !w-4 !h-4" /> Scanning…</> : <><Leaf size={14} /> Scan for Opportunities</>}
        </button>

        {/* Info box */}
        <div className="card text-xs text-gray-500 dark:text-gray-400 space-y-2">
          <p className="font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1"><Info size={11} /> How it works</p>
          <p>Enter positions with their cost basis. The scanner identifies unrealized losses and estimates the tax savings from harvesting, along with replacement ETFs to maintain market exposure while avoiding wash-sale violations.</p>
          <p className="text-orange-500 dark:text-orange-400 font-medium">⚠ Always consult a tax professional before harvesting.</p>
        </div>
      </div>

      {/* Right - positions table */}
      <div className="space-y-4 min-w-0">
        {/* Positions input */}
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Positions</h2>
            <button onClick={addPosition} className="btn-secondary flex items-center gap-1 text-xs py-1 px-2">
              <Plus size={11} /> Add
            </button>
          </div>
          <div className="p-3 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  {['Ticker','Shares','Cost Basis/sh','Purchase Date',''].map(h => (
                    <th key={h} className="text-left py-2 px-2 text-xs font-semibold uppercase tracking-wide text-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {positions.map((p, i) => (
                  <tr key={i} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="py-1.5 px-1">
                      <input className="input font-mono text-xs w-20" placeholder="SPY"
                        value={p.ticker} onChange={e => updatePosition(i, 'ticker', e.target.value.toUpperCase())} />
                    </td>
                    <td className="py-1.5 px-1">
                      <input type="number" className="input text-xs w-20" placeholder="100"
                        value={p.shares || ''} onChange={e => updatePosition(i, 'shares', +e.target.value)} />
                    </td>
                    <td className="py-1.5 px-1">
                      <div className="relative w-24">
                        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 text-[10px]">$</span>
                        <input type="number" className="input text-xs pl-4 w-24" placeholder="250.00"
                          value={p.cost_basis || ''} onChange={e => updatePosition(i, 'cost_basis', +e.target.value)} />
                      </div>
                    </td>
                    <td className="py-1.5 px-1">
                      <input type="date" className="input text-xs w-32"
                        value={p.purchase_date || ''} onChange={e => updatePosition(i, 'purchase_date', e.target.value)} />
                    </td>
                    <td className="py-1.5 px-1">
                      <button onClick={() => removePosition(i)} className="btn-ghost text-gray-400 hover:text-red-500 !p-1">
                        <Trash2 size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Results */}
        {results && !isPending && (
          <div className="space-y-4 animate-fade-in">
            {/* Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="metric-card text-center">
                <div className="text-2xl font-bold text-emerald-500">{fmt$(results.summary.estimated_tax_savings)}</div>
                <div className="metric-label">Estimated Tax Savings</div>
              </div>
              <div className="metric-card text-center">
                <div className="text-2xl font-bold text-red-500">{fmt$(results.summary.total_harvestable_loss)}</div>
                <div className="metric-label">Harvestable Losses</div>
              </div>
              <div className="metric-card text-center col-span-2 sm:col-span-1">
                <div className="text-2xl font-bold text-blue-500">{results.summary.candidates_count}</div>
                <div className="metric-label">of {results.summary.total_positions} positions are candidates</div>
              </div>
            </div>

            {/* Candidates */}
            {results.candidates.length > 0 && (
              <div className="panel">
                <div className="panel-header">
                  <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                    <CheckCircle2 size={14} className="text-emerald-500" /> Harvest Candidates
                  </h3>
                </div>
                <div className="p-3 space-y-3">
                  {results.candidates.map(c => (
                    <div key={c.ticker} className="rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-950/20 p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-sm text-gray-900 dark:text-gray-100">{c.ticker}</span>
                            <span className={`badge ${c.is_long_term ? 'badge-blue' : 'badge-red'} text-[10px]`}>
                              {c.is_long_term ? 'Long-Term' : 'Short-Term'}
                            </span>
                            {c.holding_days && <span className="text-[10px] text-gray-400">{c.holding_days}d held</span>}
                          </div>
                          <div className="text-xs text-gray-500 mt-0.5">{c.name}</div>
                          <div className="text-xs text-gray-500 mt-1">{c.harvest_note}</div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-red-500 font-bold">{fmt$(c.unrealized_pnl)} loss</div>
                          <div className="text-emerald-600 dark:text-emerald-400 font-semibold text-sm">{fmt$(c.tax_savings)} savings</div>
                          <div className="text-[10px] text-gray-400">at {c.tax_rate_used}% rate</div>
                        </div>
                      </div>
                      {/* Position details */}
                      <div className="grid grid-cols-4 gap-2 mt-2 text-[10px] text-gray-500">
                        <div><span className="font-semibold block">Shares</span>{c.shares}</div>
                        <div><span className="font-semibold block">Cost Basis</span>${c.cost_basis.toFixed(2)}</div>
                        <div><span className="font-semibold block">Current</span>${c.current_price.toFixed(2)}</div>
                        <div><span className="font-semibold block">P&L %</span>
                          <span className="text-red-500">{c.unrealized_pct.toFixed(2)}%</span>
                        </div>
                      </div>
                      {/* Replacement ETFs */}
                      {c.similar_etfs?.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-emerald-200 dark:border-emerald-900/30">
                          <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Replacement ETFs (avoid wash sale):</span>
                          <div className="flex gap-2 mt-1">
                            {c.similar_etfs.map(etf => (
                              <div key={etf.ticker} className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px]">
                                <span className="font-mono font-semibold text-blue-500">{etf.ticker}</span>
                                <ArrowRight size={8} className="text-gray-400" />
                                <span className="text-gray-500 hidden sm:inline">{etf.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* All positions summary */}
            <div className="card">
              <h3 className="section-title">All Positions</h3>
              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="data-table w-full">
                  <thead><tr>
                    <th className="text-left">Ticker</th>
                    <th className="text-right">Shares</th>
                    <th className="text-right">Cost/sh</th>
                    <th className="text-right">Current</th>
                    <th className="text-right">Unrealized P&L</th>
                    <th className="text-right">Tax Savings</th>
                    <th className="text-center">Status</th>
                  </tr></thead>
                  <tbody>
                    {results.all_positions.map(p => (
                      <tr key={p.ticker}>
                        <td><span className="font-mono font-bold text-xs">{p.ticker}</span>
                          <div className="text-[10px] text-gray-400">{p.is_long_term ? 'LT' : p.holding_days ? 'ST' : '—'}</div>
                        </td>
                        <td className="text-right">{p.shares}</td>
                        <td className="text-right">${p.cost_basis?.toFixed(2)}</td>
                        <td className="text-right">${p.current_price?.toFixed(2) ?? '—'}</td>
                        <td className={`text-right font-semibold ${p.unrealized_pnl < 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                          {p.unrealized_pnl != null ? `${p.unrealized_pnl >= 0 ? '+' : ''}$${Math.abs(p.unrealized_pnl).toLocaleString('en-US',{maximumFractionDigits:0})}` : '—'}
                        </td>
                        <td className="text-right text-emerald-500 font-semibold">
                          {p.tax_savings > 0 ? fmt$(p.tax_savings) : '—'}
                        </td>
                        <td className="text-center">
                          {p.is_candidate
                            ? <span className="badge badge-green text-[10px]">Harvest</span>
                            : <span className="badge text-[10px] bg-gray-100 dark:bg-gray-800 text-gray-500">Hold</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/50">
              <p className="text-xs text-amber-700 dark:text-amber-400 flex items-start gap-2">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                {results.disclaimer}
              </p>
            </div>
          </div>
        )}

        {!results && !isPending && (
          <div className="card">
            <div className="empty-state py-16">
              <div className="empty-state-icon"><Leaf size={28} className="text-gray-400 dark:text-gray-600" /></div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">No scan run yet</h3>
              <p className="text-xs text-gray-400 max-w-xs">Enter your positions with cost basis and scan to find tax-loss harvesting opportunities. The scanner shows potential tax savings and replacement ETFs.</p>
            </div>
          </div>
        )}
        {isPending && (
          <div className="card flex flex-col items-center justify-center py-20 gap-4">
            <div className="spinner w-10 h-10" /><p className="text-sm text-gray-500">Fetching current prices…</p>
          </div>
        )}
      </div>
    </div>
  )
}
