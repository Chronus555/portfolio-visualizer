import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Trash2, ChevronDown, ChevronUp, TrendingUp, Play, Download } from 'lucide-react'
import { backtestPortfolio, downloadBacktestPDF } from '../api/client'
import TickerInput from '../components/common/TickerInput'
import MetricsTable from '../components/common/MetricsTable'
import PlotlyChart from '../components/common/PlotlyChart'

const COLORS = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6','#ec4899']

const emptyPortfolio = (n) => ({ name: `Portfolio ${n}`, assets: [] })

const TABS = [
  { id: 'growth',   label: 'Growth' },
  { id: 'drawdown', label: 'Drawdown' },
  { id: 'annual',   label: 'Annual Returns' },
  { id: 'rolling',  label: 'Rolling Returns' },
  { id: 'metrics',  label: 'Metrics' },
]

function AnnualReturnsTable({ data, names }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm data-table">
        <thead>
          <tr>
            <th className="text-left">Year</th>
            {names.map((n) => <th key={n} className="text-right">{n}</th>)}
          </tr>
        </thead>
        <tbody>
          {[...data].reverse().map((row) => (
            <tr key={row.year}>
              <td className="font-medium text-gray-700 dark:text-gray-300">{row.year}</td>
              {names.map((n) => {
                const v = row.returns?.[n]
                return (
                  <td key={n} className={`text-right font-semibold ${
                    v == null ? 'text-gray-400' :
                    v >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'
                  }`}>
                    {v != null ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}%` : '—'}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function BacktestPage() {
  const [portfolios, setPortfolios] = useState([emptyPortfolio(1)])
  const [settings, setSettings] = useState({
    start_year: 2000,
    end_year: '',
    initial_amount: 10000,
    annual_contribution: 0,
    rebalance: 'annual',
    benchmark: 'SPY',
    inflation_adjusted: false,
  })
  const [activeTab, setActiveTab] = useState('growth')
  const [expandedPortfolio, setExpandedPortfolio] = useState(0)

  const { mutate, data: results, isPending, reset } = useMutation({
    mutationFn: backtestPortfolio,
    onError: (e) => toast.error(e.message),
  })

  const addPortfolio = () => {
    if (portfolios.length >= 6) { toast.error('Max 6 portfolios'); return }
    setPortfolios((p) => [...p, emptyPortfolio(p.length + 1)])
    setExpandedPortfolio(portfolios.length)
  }

  const removePortfolio = (i) => {
    setPortfolios((p) => p.filter((_, idx) => idx !== i))
    reset()
  }

  const updatePortfolioName = (i, name) =>
    setPortfolios((p) => p.map((port, idx) => idx === i ? { ...port, name } : port))

  const updatePortfolioAssets = (i, assets) =>
    setPortfolios((p) => p.map((port, idx) => idx === i ? { ...port, assets } : port))

  const handleRun = () => {
    const valid = portfolios.filter((p) => p.assets.length > 0)
    if (!valid.length) { toast.error('Add at least one asset to a portfolio'); return }

    mutate({
      portfolios: valid.map((p) => ({
        name: p.name,
        allocations: p.assets.map((a) => ({ ticker: a.ticker, weight: a.weight })),
      })),
      start_year: Number(settings.start_year),
      end_year: settings.end_year ? Number(settings.end_year) : null,
      initial_amount: Number(settings.initial_amount),
      annual_contribution: Number(settings.annual_contribution),
      rebalance: settings.rebalance,
      benchmark: settings.benchmark || 'SPY',
      inflation_adjusted: settings.inflation_adjusted,
    })
  }

  // Build Plotly traces
  const growthTraces = results
    ? Object.keys(results.growth_data[0] || {})
        .filter((k) => k !== 'date')
        .map((name, i) => ({
          x: results.growth_data.map((d) => d.date),
          y: results.growth_data.map((d) => d[name]),
          name, type: 'scatter', mode: 'lines',
          line: { color: COLORS[i % COLORS.length], width: 2 },
        }))
    : []

  const drawdownTraces = results
    ? Object.keys(results.drawdown_data[0]?.values || {})
        .map((name, i) => ({
          x: results.drawdown_data.map((d) => d.date),
          y: results.drawdown_data.map((d) => d.values[name]),
          name, type: 'scatter', mode: 'lines', fill: 'tozeroy',
          line: { color: COLORS[i % COLORS.length], width: 1.5 },
        }))
    : []

  const rollingData = {
    '1 Year': results?.rolling_returns_1yr,
    '3 Year': results?.rolling_returns_3yr,
    '5 Year': results?.rolling_returns_5yr,
  }

  const portfolioNames = results?.metrics.map((m) => m.portfolio_name) || []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-5 items-start">

      {/* ── Left panel ── */}
      <div className="space-y-3">

        {/* Settings card */}
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Settings</h2>
          </div>
          <div className="p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Start Year</label>
                <input type="number" className="input text-sm" value={settings.start_year}
                  onChange={(e) => setSettings((s) => ({ ...s, start_year: e.target.value }))} min="1970" max="2024" />
              </div>
              <div>
                <label className="label">End Year</label>
                <input type="number" className="input text-sm" placeholder="Current"
                  value={settings.end_year}
                  onChange={(e) => setSettings((s) => ({ ...s, end_year: e.target.value }))} min="1971" max="2025" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Initial Amount</label>
                <div className="relative">
                  <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">$</span>
                  <input type="number" className="input text-sm pl-5" value={settings.initial_amount}
                    onChange={(e) => setSettings((s) => ({ ...s, initial_amount: e.target.value }))} min="1" />
                </div>
              </div>
              <div>
                <label className="label">Ann. Contribution</label>
                <div className="relative">
                  <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">$</span>
                  <input type="number" className="input text-sm pl-5" value={settings.annual_contribution}
                    onChange={(e) => setSettings((s) => ({ ...s, annual_contribution: e.target.value }))} />
                </div>
              </div>
            </div>

            <div>
              <label className="label">Rebalancing</label>
              <select className="select text-sm" value={settings.rebalance}
                onChange={(e) => setSettings((s) => ({ ...s, rebalance: e.target.value }))}>
                <option value="none">Buy and Hold</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="semiannual">Semi-Annual</option>
                <option value="annual">Annual</option>
              </select>
            </div>

            <div>
              <label className="label">Benchmark</label>
              <input type="text" className="input text-sm font-mono" value={settings.benchmark}
                onChange={(e) => setSettings((s) => ({ ...s, benchmark: e.target.value.toUpperCase() }))}
                placeholder="e.g. SPY" />
            </div>

            <label className="flex items-center gap-2.5 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={settings.inflation_adjusted}
                  onChange={(e) => setSettings((s) => ({ ...s, inflation_adjusted: e.target.checked }))}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 rounded-full bg-gray-200 dark:bg-gray-700 peer-checked:bg-blue-500
                  transition-colors duration-200" />
                <div className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow
                  peer-checked:translate-x-4 transition-transform duration-200" />
              </div>
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200">
                Inflation Adjusted
              </span>
            </label>
          </div>
        </div>

        {/* Portfolio cards */}
        {portfolios.map((port, i) => (
          <div key={i} className="panel animate-fade-in">
            <div className="panel-header">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                <input
                  className="flex-1 font-semibold text-xs bg-transparent border-0 outline-none
                    text-gray-800 dark:text-gray-200 min-w-0"
                  value={port.name}
                  onChange={(e) => updatePortfolioName(i, e.target.value)}
                />
              </div>
              <div className="flex items-center gap-1">
                {port.assets.length > 0 && (
                  <span className="badge badge-blue text-[10px]">{port.assets.length} assets</span>
                )}
                <button onClick={() => setExpandedPortfolio(expandedPortfolio === i ? -1 : i)}
                  className="btn-ghost">
                  {expandedPortfolio === i ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {portfolios.length > 1 && (
                  <button onClick={() => removePortfolio(i)} className="btn-ghost text-gray-400 hover:text-red-500">
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            </div>

            <div className="p-3">
              {expandedPortfolio === i ? (
                <TickerInput assets={port.assets} onChange={(assets) => updatePortfolioAssets(i, assets)} />
              ) : (
                port.assets.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {port.assets.map((a) => (
                      <span key={a.ticker} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full
                        bg-gray-100 dark:bg-gray-800 text-xs font-mono font-semibold text-gray-700 dark:text-gray-300">
                        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: a.color }} />
                        {a.ticker} <span className="text-gray-400">{a.weight}%</span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 dark:text-gray-600 italic">No assets added yet</p>
                )
              )}
            </div>
          </div>
        ))}

        {/* Action buttons */}
        <div className="flex gap-2">
          <button onClick={addPortfolio}
            className="btn-secondary flex items-center gap-1.5 flex-1 justify-center text-sm py-2">
            <Plus size={14} /> Add Portfolio
          </button>
          <button onClick={handleRun} disabled={isPending}
            className="btn-primary flex items-center gap-1.5 flex-1 justify-center text-sm py-2">
            {isPending ? (
              <><span className="spinner !w-4 !h-4" /> Running…</>
            ) : (
              <><Play size={13} /> Run Backtest</>
            )}
          </button>
        </div>
      </div>

      {/* ── Right panel ── */}
      <div className="space-y-4 min-w-0">

        {/* Loading */}
        {isPending && (
          <div className="card flex flex-col items-center justify-center py-20 gap-4">
            <div className="spinner w-10 h-10" />
            <div className="text-center">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Fetching data & computing…</p>
              <p className="text-xs text-gray-400 mt-1">This may take a few seconds</p>
            </div>
          </div>
        )}

        {/* Results */}
        {results && !isPending && (
          <div className="space-y-4 animate-fade-in">
            {/* Tab bar + PDF download */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => downloadBacktestPDF(results)}
                className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3 shrink-0"
                title="Download PDF Report"
              >
                <Download size={13} /> PDF
              </button>
            </div>
            <div className="tab-bar">
              {TABS.map(({ id, label }) => (
                <button key={id} onClick={() => setActiveTab(id)}
                  className={`tab-btn ${activeTab === id ? 'active' : ''}`}>
                  {label}
                </button>
              ))}
            </div>

            {activeTab === 'growth' && (
              <div className="card">
                <h3 className="section-title">Portfolio Growth</h3>
                <PlotlyChart
                  data={growthTraces}
                  layout={{ yaxis: { title: 'Value ($)', tickformat: '$,.0f' }, xaxis: { title: 'Date' } }}
                />
              </div>
            )}

            {activeTab === 'drawdown' && (
              <div className="card">
                <h3 className="section-title">Drawdown</h3>
                <PlotlyChart
                  data={drawdownTraces}
                  layout={{ yaxis: { title: 'Drawdown (%)', ticksuffix: '%' }, xaxis: { title: 'Date' } }}
                />
              </div>
            )}

            {activeTab === 'annual' && (
              <div className="card">
                <h3 className="section-title">Annual Returns</h3>
                <AnnualReturnsTable data={results.annual_returns} names={portfolioNames} />
              </div>
            )}

            {activeTab === 'rolling' && (
              <div className="space-y-4">
                {Object.entries(rollingData).map(([label, data]) =>
                  data?.length > 0 && (
                    <div key={label} className="card">
                      <h3 className="section-title">{label} Rolling Returns</h3>
                      <PlotlyChart
                        data={Object.keys(data[0] || {}).filter((k) => k !== 'date').map((name, i) => ({
                          x: data.map((d) => d.date),
                          y: data.map((d) => d[name]),
                          name, type: 'scatter', mode: 'lines',
                          line: { color: COLORS[i % COLORS.length], width: 2 },
                        }))}
                        layout={{ yaxis: { title: 'Return (%)', ticksuffix: '%' }, xaxis: { title: 'Date' } }}
                      />
                    </div>
                  )
                )}
              </div>
            )}

            {activeTab === 'metrics' && (
              <div className="card">
                <h3 className="section-title">Performance Metrics</h3>
                <MetricsTable metrics={results.metrics} />
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!results && !isPending && (
          <div className="card animate-fade-in">
            <div className="empty-state py-20">
              <div className="empty-state-icon">
                <TrendingUp size={28} className="text-gray-400 dark:text-gray-600" />
              </div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">No results yet</h3>
              <p className="text-xs text-gray-400 dark:text-gray-600 max-w-xs">
                Add assets to a portfolio on the left, configure your settings, then click <strong>Run Backtest</strong>.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
