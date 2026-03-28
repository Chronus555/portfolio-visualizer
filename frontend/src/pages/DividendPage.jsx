import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { CircleDollarSign, Plus, Trash2, TrendingUp } from 'lucide-react'
import { analyzeDividends } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'

const fmt$ = v => `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
const fmtD = (v, d=2) => v != null ? `$${Number(v).toFixed(d)}` : '—'

const GRADE_COLOR = { A:'text-emerald-500', B:'text-blue-500', C:'text-yellow-500', D:'text-orange-500', F:'text-red-500' }

const DEFAULT_HOLDINGS = [
  { ticker: 'VYM',  shares: 200, value: 20000 },
  { ticker: 'SCHD', shares: 150, value: 15000 },
  { ticker: 'O',    shares: 100, value: 6000  },
  { ticker: 'JNJ',  shares: 50,  value: 8000  },
]

export default function DividendPage() {
  const [holdings, setHoldings] = useState(DEFAULT_HOLDINGS)
  const [growthRate, setGrowthRate] = useState(5)
  const [projectYears, setProjectYears] = useState(10)

  const { mutate, data: results, isPending } = useMutation({
    mutationFn: analyzeDividends,
    onError: e => toast.error(e.message),
  })

  const addHolding = () => setHoldings(h => [...h, { ticker: '', shares: 0, value: 0 }])
  const removeHolding = i => setHoldings(h => h.filter((_, idx) => idx !== i))
  const update = (i, field, val) =>
    setHoldings(h => h.map((item, idx) => idx === i ? { ...item, [field]: val } : item))

  const handleRun = () => {
    if (!holdings.length) { toast.error('Add at least one holding'); return }
    mutate({ holdings, dividend_growth_assumption: growthRate / 100, project_years: projectYears })
  }

  // Charts
  const historyTrace = results?.combined_history?.length ? [{
    x: results.combined_history.map(d => d.date),
    y: results.combined_history.map(d => d.income),
    type: 'bar', name: 'Quarterly Income',
    marker: { color: '#3b82f6' },
  }] : []

  const projectionTrace = results?.income_projection?.length ? [
    { x: results.income_projection.map(d => d.year), y: results.income_projection.map(d => d.annual_income),
      type: 'scatter', mode: 'lines+markers', name: `Projected (${growthRate}% growth)`,
      line: { color: '#10b981', width: 2 }, marker: { size: 6 } },
  ] : []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-5 items-start">
      {/* Left */}
      <div className="space-y-3">
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
              <CircleDollarSign size={14} className="text-emerald-500" /> Holdings
            </h2>
            <button onClick={addHolding} className="btn-secondary flex items-center gap-1 text-xs py-1 px-2">
              <Plus size={11} /> Add
            </button>
          </div>
          <div className="p-3 space-y-2">
            {holdings.map((h, i) => (
              <div key={i} className="grid grid-cols-[70px_60px_1fr_24px] gap-1.5 items-center">
                <input className="input font-mono text-xs" placeholder="Ticker"
                  value={h.ticker} onChange={e => update(i, 'ticker', e.target.value.toUpperCase())} />
                <input type="number" className="input text-xs" placeholder="Shares"
                  value={h.shares || ''} onChange={e => update(i, 'shares', +e.target.value)} />
                <div className="relative">
                  <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-[10px] text-gray-400">$</span>
                  <input type="number" className="input text-xs pl-3.5" placeholder="Value"
                    value={h.value || ''} onChange={e => update(i, 'value', +e.target.value)} />
                </div>
                <button onClick={() => removeHolding(i)} className="btn-ghost text-gray-400 hover:text-red-500 !p-1">
                  <Trash2 size={11} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="panel animate-fade-in">
          <div className="panel-header"><h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Projection</h2></div>
          <div className="p-4 space-y-3">
            <div>
              <label className="label">Dividend Growth Rate</label>
              <div className="relative">
                <input type="number" className="input text-sm pr-5" step="0.5" value={growthRate}
                  onChange={e => setGrowthRate(+e.target.value)} min="0" max="20" />
                <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">%</span>
              </div>
            </div>
            <div>
              <label className="label">Project Years</label>
              <input type="number" className="input text-sm" value={projectYears}
                onChange={e => setProjectYears(+e.target.value)} min="1" max="30" />
            </div>
          </div>
        </div>

        <button onClick={handleRun} disabled={isPending || !holdings.length}
          className="btn-primary w-full flex items-center justify-center gap-2 py-2.5">
          {isPending ? <><span className="spinner !w-4 !h-4" /> Analyzing…</> : <><CircleDollarSign size={14} /> Analyze Dividends</>}
        </button>
      </div>

      {/* Right */}
      <div className="space-y-4 min-w-0">
        {results && !isPending && (
          <div className="space-y-4 animate-fade-in">
            {/* Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Annual Income',    val: fmt$(results.summary.annual_income),    color: 'text-emerald-500', sub: `${fmt$(results.summary.monthly_income)}/month` },
                { label: 'Portfolio Yield',  val: `${results.summary.portfolio_yield.toFixed(2)}%`, color: 'text-blue-500', sub: `on ${fmt$(results.summary.total_portfolio_value)}` },
                { label: 'Income Payers',    val: results.summary.income_payers,          color: 'text-violet-500', sub: `${results.summary.non_payers} non-payers` },
                { label: `In ${projectYears}yrs`,  val: fmt$(results.income_projection?.at(-1)?.annual_income ?? 0), color: 'text-orange-500', sub: `at ${growthRate}% growth` },
              ].map(m => (
                <div key={m.label} className="metric-card text-center">
                  <div className={`text-xl font-bold ${m.color}`}>{m.val}</div>
                  <div className="metric-label">{m.label}</div>
                  <div className="text-[10px] text-gray-400 mt-1">{m.sub}</div>
                </div>
              ))}
            </div>

            {/* Holdings breakdown */}
            <div className="card">
              <h3 className="section-title">Holding Breakdown</h3>
              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="data-table w-full">
                  <thead><tr>
                    <th className="text-left">Ticker</th>
                    <th className="text-right">Yield</th>
                    <th className="text-right">TTM Div</th>
                    <th className="text-right">Annual Income</th>
                    <th className="text-right">5yr CAGR</th>
                    <th className="text-right">Payout Ratio</th>
                    <th className="text-center">Quality</th>
                  </tr></thead>
                  <tbody>
                    {results.holdings.map(h => (
                      <tr key={h.ticker}>
                        <td>
                          <span className="font-mono font-bold text-xs">{h.ticker}</span>
                          <div className="text-[10px] text-gray-400 truncate max-w-[100px]">{h.name}</div>
                        </td>
                        <td className="text-right font-semibold text-emerald-600 dark:text-emerald-400">
                          {h.dividend_yield != null ? `${h.dividend_yield.toFixed(2)}%` : '—'}
                        </td>
                        <td className="text-right">{h.ttm_dividend ? `$${h.ttm_dividend.toFixed(4)}` : '—'}</td>
                        <td className="text-right font-semibold text-emerald-500">{fmt$(h.annual_income)}</td>
                        <td className={`text-right font-medium ${h.dividend_cagr_5y > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                          {h.dividend_cagr_5y != null ? `${h.dividend_cagr_5y > 0 ? '+' : ''}${h.dividend_cagr_5y.toFixed(1)}%` : '—'}
                        </td>
                        <td className="text-right">
                          {h.payout_ratio != null
                            ? <span className={h.payout_ratio > 80 ? 'text-red-500' : h.payout_ratio > 60 ? 'text-orange-500' : 'text-emerald-500'}>
                                {h.payout_ratio.toFixed(0)}%
                              </span>
                            : '—'}
                        </td>
                        <td className="text-center">
                          {h.quality_score
                            ? <span className={`text-lg font-bold ${GRADE_COLOR[h.quality_score.grade] || 'text-gray-500'}`}>{h.quality_score.grade}</span>
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {historyTrace.length > 0 && (
                <div className="card">
                  <h3 className="section-title">Dividend Income History</h3>
                  <PlotlyChart data={historyTrace}
                    layout={{ yaxis: { title: 'Income ($)', tickformat: '$,.0f' }, xaxis: { title: '' } }}
                    style={{ minHeight: 260 }} />
                </div>
              )}
              {projectionTrace.length > 0 && (
                <div className="card">
                  <h3 className="section-title">Income Projection ({growthRate}% Growth)</h3>
                  <PlotlyChart data={projectionTrace}
                    layout={{ yaxis: { title: 'Annual Income ($)', tickformat: '$,.0f' }, xaxis: { title: 'Years from Now' } }}
                    style={{ minHeight: 260 }} />
                </div>
              )}
            </div>
          </div>
        )}

        {!results && !isPending && (
          <div className="card">
            <div className="empty-state py-20">
              <div className="empty-state-icon"><CircleDollarSign size={28} className="text-gray-400 dark:text-gray-600" /></div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">No dividend analysis yet</h3>
              <p className="text-xs text-gray-400 max-w-xs">Add your income-generating holdings and analyze yield, growth, payout safety, and projected future income.</p>
            </div>
          </div>
        )}
        {isPending && (
          <div className="card flex flex-col items-center justify-center py-20 gap-4">
            <div className="spinner w-10 h-10" /><p className="text-sm text-gray-500">Fetching dividend data from Yahoo Finance…</p>
          </div>
        )}
      </div>
    </div>
  )
}
