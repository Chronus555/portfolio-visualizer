import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { optimizePortfolio } from '../api/client'
import TickerInput from '../components/common/TickerInput'
import PlotlyChart from '../components/common/PlotlyChart'

const GOAL_LABELS = {
  max_sharpe: 'Maximum Sharpe Ratio',
  min_volatility: 'Minimum Volatility',
  efficient_risk: 'Efficient Risk (target volatility)',
  efficient_return: 'Efficient Return (target return)',
  max_quadratic_utility: 'Maximum Quadratic Utility',
  cvar: 'Minimum CVaR',
  risk_parity: 'Risk Parity',
  cdar: 'Minimum CDaR',
}

export default function OptimizationPage() {
  const [assets, setAssets] = useState([])
  const [settings, setSettings] = useState({
    start_year: 2010,
    end_year: '',
    goal: 'max_sharpe',
    risk_free_rate: 2,
    target_return: '',
    target_risk: '',
    risk_aversion: 1,
    n_frontier_points: 50,
  })
  const [activeTab, setActiveTab] = useState('frontier')

  const { mutate, data: results, isPending } = useMutation({
    mutationFn: optimizePortfolio,
    onError: (e) => toast.error(e.message),
  })

  const handleRun = () => {
    if (assets.length < 2) { toast.error('Add at least 2 assets'); return }
    mutate({
      tickers: assets.map((a) => a.ticker),
      start_year: Number(settings.start_year),
      end_year: settings.end_year ? Number(settings.end_year) : null,
      goal: settings.goal,
      risk_free_rate: Number(settings.risk_free_rate) / 100,
      target_return: settings.target_return ? Number(settings.target_return) / 100 : null,
      target_risk: settings.target_risk ? Number(settings.target_risk) / 100 : null,
      risk_aversion: Number(settings.risk_aversion),
      n_frontier_points: Number(settings.n_frontier_points),
      weight_bounds: [0, 1],
    })
  }

  const buildFrontierTraces = () => {
    if (!results) return []
    const traces = []

    // Frontier curve
    traces.push({
      x: results.efficient_frontier.map((p) => p.risk),
      y: results.efficient_frontier.map((p) => p.return),
      mode: 'lines',
      type: 'scatter',
      name: 'Efficient Frontier',
      line: { color: '#3b82f6', width: 2.5 },
      hovertemplate: 'Risk: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>',
    })

    // Individual assets
    traces.push({
      x: results.individual_assets.map((a) => a.expected_volatility),
      y: results.individual_assets.map((a) => a.expected_return),
      mode: 'markers+text',
      type: 'scatter',
      name: 'Individual Assets',
      text: results.individual_assets.map((a) => a.ticker),
      textposition: 'top center',
      marker: { color: '#6b7280', size: 8 },
    })

    // Optimal portfolio
    traces.push({
      x: [results.expected_volatility],
      y: [results.expected_return],
      mode: 'markers',
      type: 'scatter',
      name: `Optimal (${GOAL_LABELS[settings.goal]})`,
      marker: { color: '#ef4444', size: 14, symbol: 'star' },
      hovertemplate: `Risk: ${results.expected_volatility.toFixed(2)}%<br>Return: ${results.expected_return.toFixed(2)}%<br>Sharpe: ${results.sharpe_ratio.toFixed(3)}<extra></extra>`,
    })

    return traces
  }

  const totalOptimalWeight = results
    ? Object.values(results.weights).reduce((s, v) => s + v, 0)
    : 0

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6 items-start">
      {/* Left */}
      <div className="space-y-4">
        <div className="card space-y-3">
          <h2 className="section-title">Assets</h2>
          <TickerInput assets={assets} onChange={setAssets} showWeights={false} />
        </div>

        <div className="card space-y-3">
          <h2 className="section-title">Optimization Settings</h2>

          <div>
            <label className="label">Optimization Goal</label>
            <select className="select" value={settings.goal}
              onChange={(e) => setSettings((s) => ({ ...s, goal: e.target.value }))}>
              {Object.entries(GOAL_LABELS).map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Start Year</label>
              <input type="number" className="input" value={settings.start_year} min="1970" max="2024"
                onChange={(e) => setSettings((s) => ({ ...s, start_year: e.target.value }))} />
            </div>
            <div>
              <label className="label">End Year</label>
              <input type="number" className="input" placeholder="Current" value={settings.end_year}
                onChange={(e) => setSettings((s) => ({ ...s, end_year: e.target.value }))} />
            </div>
            <div>
              <label className="label">Risk-Free Rate (%)</label>
              <input type="number" className="input" value={settings.risk_free_rate} step="0.1"
                onChange={(e) => setSettings((s) => ({ ...s, risk_free_rate: e.target.value }))} />
            </div>
            <div>
              <label className="label">Frontier Points</label>
              <input type="number" className="input" value={settings.n_frontier_points} min="10" max="200"
                onChange={(e) => setSettings((s) => ({ ...s, n_frontier_points: e.target.value }))} />
            </div>
          </div>

          {settings.goal === 'efficient_risk' && (
            <div>
              <label className="label">Target Volatility (%)</label>
              <input type="number" className="input" value={settings.target_risk} step="0.5"
                onChange={(e) => setSettings((s) => ({ ...s, target_risk: e.target.value }))} />
            </div>
          )}
          {settings.goal === 'efficient_return' && (
            <div>
              <label className="label">Target Return (%/yr)</label>
              <input type="number" className="input" value={settings.target_return} step="0.5"
                onChange={(e) => setSettings((s) => ({ ...s, target_return: e.target.value }))} />
            </div>
          )}
          {settings.goal === 'max_quadratic_utility' && (
            <div>
              <label className="label">Risk Aversion (λ)</label>
              <input type="number" className="input" value={settings.risk_aversion} step="0.5" min="0.1"
                onChange={(e) => setSettings((s) => ({ ...s, risk_aversion: e.target.value }))} />
            </div>
          )}
        </div>

        <button onClick={handleRun} disabled={isPending} className="btn-primary w-full">
          {isPending ? 'Optimizing…' : 'Optimize Portfolio'}
        </button>
      </div>

      {/* Right */}
      <div className="space-y-6">
        {isPending && (
          <div className="card flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500">Computing efficient frontier…</p>
            </div>
          </div>
        )}

        {results && !isPending && (
          <>
            {/* Tabs */}
            <div className="flex gap-1">
              {['frontier', 'weights', 'assets'].map((tab) => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`tab-btn ${activeTab === tab ? 'active' : ''}`}>
                  {tab === 'frontier' ? 'Efficient Frontier' : tab === 'weights' ? 'Optimal Weights' : 'Asset Stats'}
                </button>
              ))}
            </div>

            {/* Key metrics */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Expected Return', value: `${results.expected_return.toFixed(2)}%` },
                { label: 'Expected Volatility', value: `${results.expected_volatility.toFixed(2)}%` },
                { label: 'Sharpe Ratio', value: results.sharpe_ratio.toFixed(3) },
              ].map(({ label, value }) => (
                <div key={label} className="metric-card text-center">
                  <div className="metric-value">{value}</div>
                  <div className="metric-label">{label}</div>
                </div>
              ))}
            </div>

            {activeTab === 'frontier' && (
              <div className="card">
                <h3 className="section-title">Efficient Frontier</h3>
                <PlotlyChart
                  data={buildFrontierTraces()}
                  layout={{
                    xaxis: { title: 'Expected Volatility (%)', ticksuffix: '%' },
                    yaxis: { title: 'Expected Return (%)', ticksuffix: '%' },
                    hovermode: 'closest',
                    legend: { orientation: 'v', x: 0.02, y: 0.98, xanchor: 'left', yanchor: 'top' },
                  }}
                />
              </div>
            )}

            {activeTab === 'weights' && (
              <div className="card">
                <h3 className="section-title">Optimal Portfolio Weights</h3>
                <div className="space-y-2 mb-6">
                  {Object.entries(results.weights)
                    .sort(([, a], [, b]) => b - a)
                    .map(([ticker, weight]) => (
                      <div key={ticker} className="flex items-center gap-3">
                        <span className="font-mono font-semibold w-16 text-sm">{ticker}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full transition-all"
                            style={{ width: `${(weight * 100).toFixed(1)}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium w-16 text-right">
                          {(weight * 100).toFixed(2)}%
                        </span>
                      </div>
                    ))}
                </div>
                {/* Pie chart */}
                <PlotlyChart
                  data={[{
                    type: 'pie',
                    labels: Object.keys(results.weights),
                    values: Object.values(results.weights).map((v) => +(v * 100).toFixed(2)),
                    textinfo: 'label+percent',
                    hole: 0.4,
                  }]}
                  layout={{ showlegend: false, margin: { t: 10, b: 10, l: 10, r: 10 } }}
                  style={{ minHeight: 280 }}
                />
              </div>
            )}

            {activeTab === 'assets' && (
              <div className="card">
                <h3 className="section-title">Individual Asset Statistics</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 text-gray-500 font-medium">Ticker</th>
                      <th className="text-right py-2 text-gray-500 font-medium">Exp. Return</th>
                      <th className="text-right py-2 text-gray-500 font-medium">Volatility</th>
                      <th className="text-right py-2 text-gray-500 font-medium">Sharpe</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.individual_assets.map((a) => (
                      <tr key={a.ticker} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-2 font-mono font-semibold">{a.ticker}</td>
                        <td className={`text-right py-2 ${a.expected_return >= 0 ? 'positive' : 'negative'}`}>
                          {a.expected_return >= 0 ? '+' : ''}{a.expected_return.toFixed(2)}%
                        </td>
                        <td className="text-right py-2">{a.expected_volatility.toFixed(2)}%</td>
                        <td className="text-right py-2">{a.sharpe.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {!results && !isPending && (
          <div className="card flex items-center justify-center h-64 text-gray-400 text-sm">
            Add at least 2 assets and click "Optimize Portfolio".
          </div>
        )}
      </div>
    </div>
  )
}
