import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { DollarSign, TrendingDown, Plus, Trash2, Calculator } from 'lucide-react'
import { analyzeFees } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'

const DEFAULT_HOLDINGS = [
  { ticker: 'VTI',  name: 'Vanguard Total Stock Market', expense_ratio: 0.0003, value: 60000 },
  { ticker: 'VXUS', name: 'Vanguard Total Intl Stock',   expense_ratio: 0.0007, value: 30000 },
  { ticker: 'BND',  name: 'Vanguard Total Bond Market',  expense_ratio: 0.0003, value: 10000 },
]

const fmt$ = v => `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
const fmtPct = (v, d=4) => `${(v*100).toFixed(d)}%`

export default function FeeAnalyzerPage() {
  const [holdings, setHoldings]   = useState(DEFAULT_HOLDINGS)
  const [settings, setSettings]   = useState({
    initial_amount: 100000,
    years: 30,
    annual_return: 0.07,
    annual_contribution: 6000,
    advisor_fee: 0.0,
  })

  const { mutate, data: results, isPending } = useMutation({
    mutationFn: analyzeFees,
    onError: e => toast.error(e.message),
  })

  const addHolding = () => setHoldings(h => [...h, { ticker: '', name: '', expense_ratio: 0, value: 0 }])
  const removeHolding = i => setHoldings(h => h.filter((_, idx) => idx !== i))
  const updateHolding = (i, field, val) =>
    setHoldings(h => h.map((item, idx) => idx === i ? { ...item, [field]: val } : item))

  const handleRun = () => {
    if (!holdings.length) { toast.error('Add at least one holding'); return }
    mutate({ holdings, ...settings })
  }

  const totalValue = holdings.reduce((s, h) => s + Number(h.value || 0), 0)

  // Plotly traces
  const chartTraces = results ? [
    { x: results.chart_data.years, y: results.chart_data.gross,    name: 'No Fees (Gross)', mode:'lines', line:{color:'#10b981',width:2} },
    { x: results.chart_data.years, y: results.chart_data.low_cost, name: 'Low-Cost (0.03%)', mode:'lines', line:{color:'#3b82f6',width:2,dash:'dot'} },
    { x: results.chart_data.years, y: results.chart_data.net,      name: 'Your Portfolio',  mode:'lines', line:{color:'#ef4444',width:2.5} },
  ] : []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-5 items-start">
      {/* Left Panel */}
      <div className="space-y-3">
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
              <Calculator size={14} className="text-blue-500" /> Assumptions
            </h2>
          </div>
          <div className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Initial Amount</label>
                <div className="relative"><span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">$</span>
                  <input type="number" className="input text-sm pl-5" value={settings.initial_amount}
                    onChange={e => setSettings(s => ({...s, initial_amount: +e.target.value}))} /></div>
              </div>
              <div>
                <label className="label">Ann. Contribution</label>
                <div className="relative"><span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">$</span>
                  <input type="number" className="input text-sm pl-5" value={settings.annual_contribution}
                    onChange={e => setSettings(s => ({...s, annual_contribution: +e.target.value}))} /></div>
              </div>
              <div>
                <label className="label">Time Horizon (yrs)</label>
                <input type="number" className="input text-sm" value={settings.years} min="1" max="50"
                  onChange={e => setSettings(s => ({...s, years: +e.target.value}))} />
              </div>
              <div>
                <label className="label">Expected Return</label>
                <div className="relative">
                  <input type="number" className="input text-sm pr-5" value={(settings.annual_return*100).toFixed(1)} step="0.1"
                    onChange={e => setSettings(s => ({...s, annual_return: +e.target.value/100}))} />
                  <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">%</span>
                </div>
              </div>
            </div>
            <div>
              <label className="label">Advisor Fee (AUM %)</label>
              <div className="relative">
                <input type="number" className="input text-sm pr-5" value={(settings.advisor_fee*100).toFixed(2)} step="0.01"
                  onChange={e => setSettings(s => ({...s, advisor_fee: +e.target.value/100}))} placeholder="e.g. 1 for 1%" />
                <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Holdings */}
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Holdings</h2>
            <span className="text-xs text-gray-400">{fmt$(totalValue)} total</span>
          </div>
          <div className="p-3 space-y-2">
            {holdings.map((h, i) => (
              <div key={i} className="grid grid-cols-[80px_1fr_80px_28px] gap-1.5 items-center">
                <input className="input font-mono text-xs" placeholder="Ticker"
                  value={h.ticker} onChange={e => updateHolding(i, 'ticker', e.target.value.toUpperCase())} />
                <div className="relative">
                  <input type="number" className="input text-xs pr-4" placeholder="Exp ratio %" step="0.01"
                    value={h.expense_ratio ? (h.expense_ratio*100).toFixed(4) : ''}
                    onChange={e => updateHolding(i, 'expense_ratio', +e.target.value/100)} />
                  <span className="absolute right-1.5 top-1/2 -translate-y-1/2 text-[10px] text-gray-400">%</span>
                </div>
                <div className="relative">
                  <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-[10px] text-gray-400">$</span>
                  <input type="number" className="input text-xs pl-3.5" placeholder="Value"
                    value={h.value || ''} onChange={e => updateHolding(i, 'value', +e.target.value)} />
                </div>
                <button onClick={() => removeHolding(i)} className="btn-ghost text-gray-400 hover:text-red-500 !p-1">
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
            <button onClick={addHolding} className="btn-secondary w-full flex items-center justify-center gap-1 text-xs py-1.5 mt-1">
              <Plus size={12} /> Add Holding
            </button>
          </div>
        </div>

        <button onClick={handleRun} disabled={isPending}
          className="btn-primary w-full flex items-center justify-center gap-2 py-2.5">
          {isPending ? <><span className="spinner !w-4 !h-4" /> Calculating…</> : <><TrendingDown size={14} /> Analyze Fee Drag</>}
        </button>
      </div>

      {/* Right Panel */}
      <div className="space-y-4 min-w-0">
        {results && !isPending && (
          <div className="space-y-4 animate-fade-in">
            {/* Top summary cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Total Fee Rate',     val: `${results.summary.total_fee_rate.toFixed(4)}%`,  color:'text-orange-500', sub: `${results.summary.weighted_expense_ratio.toFixed(4)}% ER + ${results.summary.advisor_fee.toFixed(2)}% advisor` },
                { label: '30-Year Fee Drag',   val: fmt$(results.summary.total_fee_drag),             color:'text-red-500',    sub: `${results.summary.fee_drag_pct.toFixed(1)}% of gross value lost` },
                { label: 'Your Final Balance', val: fmt$(results.summary.net_final_value),            color:'text-blue-500',   sub: `After ${results.summary.years} yrs with fees` },
                { label: 'Low-Cost Alternative',val: fmt$(results.summary.low_cost_final),            color:'text-emerald-500',sub: `+${fmt$(results.summary.vs_low_cost_drag)} more at 0.03% ER` },
              ].map(m => (
                <div key={m.label} className="metric-card text-center">
                  <div className={`text-xl font-bold ${m.color}`}>{m.val}</div>
                  <div className="metric-label">{m.label}</div>
                  <div className="text-[10px] text-gray-400 mt-1">{m.sub}</div>
                </div>
              ))}
            </div>

            {/* Growth chart */}
            <div className="card">
              <h3 className="section-title">Portfolio Growth: With vs. Without Fees</h3>
              <PlotlyChart data={chartTraces}
                layout={{ yaxis: { title: 'Portfolio Value ($)', tickformat: '$,.0f' }, xaxis: { title: 'Years' } }} />
            </div>

            {/* Holding breakdown */}
            <div className="card">
              <h3 className="section-title">Holding-Level Fee Analysis</h3>
              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="data-table w-full">
                  <thead>
                    <tr>
                      <th className="text-left">Ticker</th>
                      <th className="text-right">Value</th>
                      <th className="text-right">Weight</th>
                      <th className="text-right">Expense Ratio</th>
                      <th className="text-right">Annual Cost</th>
                      <th className="text-right">{results.summary.years}yr Drag</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.holdings.map(h => (
                      <tr key={h.ticker}>
                        <td><span className="font-mono font-semibold text-xs">{h.ticker || '—'}</span>
                          <div className="text-[10px] text-gray-400 truncate max-w-[120px]">{h.name}</div></td>
                        <td className="text-right">{fmt$(h.value)}</td>
                        <td className="text-right">{h.weight_pct.toFixed(1)}%</td>
                        <td className="text-right">
                          <span className={`font-semibold ${h.expense_ratio > 0.5 ? 'text-red-500' : h.expense_ratio > 0.2 ? 'text-orange-500' : 'text-emerald-500'}`}>
                            {h.expense_ratio.toFixed(4)}%
                          </span>
                        </td>
                        <td className="text-right text-orange-500 font-medium">{fmt$(h.annual_cost)}/yr</td>
                        <td className="text-right text-red-500 font-semibold">{fmt$(h.projected_drag)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Year-by-year */}
            <div className="card">
              <h3 className="section-title">Cumulative Fee Impact Over Time</h3>
              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="data-table w-full">
                  <thead><tr>
                    <th className="text-left">Year</th>
                    <th className="text-right">Balance</th>
                    <th className="text-right">Fees This Year</th>
                    <th className="text-right">Cumulative Drag</th>
                  </tr></thead>
                  <tbody>
                    {results.breakdown.map(r => (
                      <tr key={r.year}>
                        <td>Year {r.year}</td>
                        <td className="text-right font-medium">{fmt$(r.balance)}</td>
                        <td className="text-right text-orange-500">{fmt$(r.fees_paid_this_year)}</td>
                        <td className="text-right text-red-500 font-semibold">{fmt$(r.cumulative_opportunity_cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {!results && !isPending && (
          <div className="card">
            <div className="empty-state py-20">
              <div className="empty-state-icon"><DollarSign size={28} className="text-gray-400 dark:text-gray-600" /></div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">See the real cost of your fees</h3>
              <p className="text-xs text-gray-400 max-w-xs">Enter your holdings and expense ratios to see exactly how much fees will cost you in dollar terms over your investment horizon.</p>
            </div>
          </div>
        )}

        {isPending && (
          <div className="card flex flex-col items-center justify-center py-20 gap-4">
            <div className="spinner w-10 h-10" />
            <p className="text-sm text-gray-500">Projecting fee drag over {settings.years} years…</p>
          </div>
        )}
      </div>
    </div>
  )
}
