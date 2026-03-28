import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Shield, TrendingDown, Clock, DollarSign, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { runStressTest, getScenarios } from '../api/client'
import TickerInput from '../components/common/TickerInput'
import PlotlyChart from '../components/common/PlotlyChart'

const COLORS = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6']

function ScenarioCard({ s, initialAmount }) {
  const [expanded, setExpanded] = useState(false)
  if (!s.available) {
    return (
      <div className="panel opacity-60">
        <div className="panel-header">
          <span className="text-sm font-semibold text-gray-600 dark:text-gray-400">{s.label}</span>
          <span className="badge badge-blue text-[10px]">{s.period}</span>
        </div>
        <div className="p-4 text-xs text-gray-400">Data not available for this period</div>
      </div>
    )
  }
  const isLoss = s.portfolio_return < 0
  const beatMarket = s.portfolio_return > s.spy_return
  const traces = s.path?.length ? [{
    x: s.path.map(p => p.date),
    y: s.path.map(p => p.value),
    type: 'scatter', mode: 'lines',
    line: { color: isLoss ? '#ef4444' : '#10b981', width: 2 },
    name: 'Portfolio',
    fill: 'tozeroy',
    fillcolor: isLoss ? 'rgba(239,68,68,0.08)' : 'rgba(16,185,129,0.08)',
  }] : []

  return (
    <div className={`panel border ${isLoss ? 'dark:border-red-900/50' : 'dark:border-emerald-900/50'}`}>
      <div className="panel-header cursor-pointer" onClick={() => setExpanded(e => !e)}>
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isLoss ? 'bg-red-100 dark:bg-red-900/30' : 'bg-emerald-100 dark:bg-emerald-900/30'}`}>
            <TrendingDown size={15} className={isLoss ? 'text-red-500' : 'text-emerald-500'} />
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate">{s.label}</div>
            <div className="text-xs text-gray-400">{s.period}</div>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right">
            <div className={`text-base font-bold ${isLoss ? 'text-red-500' : 'text-emerald-500'}`}>
              {s.portfolio_return > 0 ? '+' : ''}{s.portfolio_return?.toFixed(1)}%
            </div>
            <div className="text-[10px] text-gray-400">vs SPY {s.spy_return > 0 ? '+' : ''}{s.spy_return}%</div>
          </div>
          {expanded ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
        </div>
      </div>

      {expanded && (
        <div className="p-4 space-y-4 animate-fade-in">
          <p className="text-xs text-gray-500 dark:text-gray-400">{s.description}</p>

          {/* Key stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Total Return',     val: `${s.portfolio_return > 0 ? '+' : ''}${s.portfolio_return?.toFixed(2)}%`, color: isLoss ? 'text-red-500' : 'text-emerald-500' },
              { label: 'Max Drawdown',     val: `${s.max_drawdown?.toFixed(2)}%`,                                           color: 'text-red-500' },
              { label: 'Dollar Change',    val: `$${(s.dollar_change ?? 0).toLocaleString('en-US', {maximumFractionDigits:0})}`, color: isLoss ? 'text-red-500' : 'text-emerald-500' },
              { label: 'Recovery (est.)',  val: s.recovery_months ? `${s.recovery_months} mo` : 'N/A',                     color: 'text-gray-600 dark:text-gray-400' },
            ].map(m => (
              <div key={m.label} className="metric-card text-center">
                <div className={`text-lg font-bold ${m.color}`}>{m.val}</div>
                <div className="metric-label">{m.label}</div>
              </div>
            ))}
          </div>

          {/* vs SPY comparison */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${beatMarket ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400' : 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400'}`}>
            <Shield size={12} />
            {beatMarket
              ? `Outperformed SPY by ${(s.portfolio_return - s.spy_return).toFixed(1)}pp — better diversification helped`
              : `Underperformed SPY by ${(s.spy_return - s.portfolio_return).toFixed(1)}pp during this crisis`}
          </div>

          {traces.length > 0 && (
            <PlotlyChart
              data={traces}
              layout={{ yaxis: { title: 'Portfolio Value ($)', tickformat: '$,.0f' }, xaxis: { title: '' } }}
              style={{ minHeight: 220 }}
            />
          )}
        </div>
      )}
    </div>
  )
}

export default function StressTestPage() {
  const [assets, setAssets] = useState([])
  const [initialAmount, setInitialAmount] = useState(100000)

  const { mutate, data: results, isPending, reset } = useMutation({
    mutationFn: runStressTest,
    onError: e => toast.error(e.message),
  })

  const handleRun = () => {
    if (!assets.length) { toast.error('Add at least one asset'); return }
    const totalWeight = assets.reduce((s, a) => s + Number(a.weight), 0)
    if (Math.abs(totalWeight - 100) > 1) { toast.error('Weights must sum to 100%'); return }
    mutate({
      allocations: assets.map(a => ({ ticker: a.ticker, weight: a.weight })),
      initial_amount: Number(initialAmount),
    })
  }

  const worstScenario = results?.scenarios?.filter(s => s.available && s.portfolio_return != null)
    .sort((a, b) => a.portfolio_return - b.portfolio_return)[0]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5 items-start">
      {/* Left */}
      <div className="space-y-3">
        <div className="panel animate-fade-in">
          <div className="panel-header">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
              <Shield size={14} className="text-blue-500" /> Stress Test Settings
            </h2>
          </div>
          <div className="p-4 space-y-3">
            <div>
              <label className="label">Initial Amount</label>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">$</span>
                <input type="number" className="input text-sm pl-5" value={initialAmount}
                  onChange={e => setInitialAmount(e.target.value)} min="1000" />
              </div>
            </div>
            <div>
              <label className="label">Portfolio Holdings</label>
              <TickerInput assets={assets} onChange={setAssets} />
            </div>
          </div>
        </div>

        <button onClick={handleRun} disabled={isPending || !assets.length}
          className="btn-primary w-full flex items-center justify-center gap-2 py-2.5">
          {isPending ? <><span className="spinner !w-4 !h-4" /> Testing…</> : <><Shield size={14} /> Run Stress Test</>}
        </button>

        <div className="card text-xs text-gray-500 dark:text-gray-400 space-y-1.5">
          <p className="font-semibold text-gray-700 dark:text-gray-300">What is stress testing?</p>
          <p>Tests how your portfolio would have performed during real historical crises — 2008, dot-com crash, COVID, and more. Essential for understanding true downside risk before a crisis occurs.</p>
        </div>
      </div>

      {/* Right */}
      <div className="space-y-4 min-w-0">
        {isPending && (
          <div className="card flex flex-col items-center justify-center py-20 gap-4">
            <div className="spinner w-10 h-10" />
            <p className="text-sm text-gray-500">Fetching historical data for all scenarios…</p>
          </div>
        )}

        {results && !isPending && (
          <div className="space-y-3 animate-fade-in">
            {/* Summary banner */}
            {worstScenario && (
              <div className="card bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950/30 dark:to-orange-950/20 border-red-200 dark:border-red-900/50">
                <div className="flex items-start gap-3">
                  <AlertTriangle size={18} className="text-red-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-red-700 dark:text-red-400">Worst Historical Scenario</p>
                    <p className="text-xs text-red-600 dark:text-red-500 mt-0.5">
                      During the <strong>{worstScenario.label}</strong>, your portfolio would have
                      lost <strong>${Math.abs(worstScenario.dollar_change ?? 0).toLocaleString('en-US', {maximumFractionDigits:0})}</strong> ({worstScenario.portfolio_return?.toFixed(1)}%),
                      reaching a low of <strong>${(worstScenario.dollar_at_bottom ?? 0).toLocaleString('en-US', {maximumFractionDigits:0})}</strong>.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {results.scenarios.map(s => (
              <ScenarioCard key={s.scenario_id} s={s} initialAmount={results.initial_amount} />
            ))}
          </div>
        )}

        {!results && !isPending && (
          <div className="card">
            <div className="empty-state py-20">
              <div className="empty-state-icon">
                <Shield size={28} className="text-gray-400 dark:text-gray-600" />
              </div>
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">No stress test run yet</h3>
              <p className="text-xs text-gray-400 max-w-xs">
                Add your portfolio on the left and click Run Stress Test to see how it holds up against 8 historical market crises.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
