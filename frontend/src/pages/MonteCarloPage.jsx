import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { runMonteCarlo } from '../api/client'
import TickerInput from '../components/common/TickerInput'
import PlotlyChart from '../components/common/PlotlyChart'

const BAND_COLORS = {
  '90': 'rgba(59,130,246,0.15)',
  '75': 'rgba(59,130,246,0.25)',
  '50': 'rgba(59,130,246,1)',
  '25': 'rgba(59,130,246,0.25)',
  '10': 'rgba(59,130,246,0.15)',
}

export default function MonteCarloPage() {
  const [assets, setAssets] = useState([])
  const [settings, setSettings] = useState({
    initial_amount: 100000,
    years: 30,
    simulations: 1000,
    annual_withdrawal: 4000,
    annual_contribution: 0,
    model: 'historical',
    start_year: 2000,
    end_year: '',
    inflation_rate: 0,
    management_fee: 0,
    mean_return: '',
    std_dev: '',
  })

  const { mutate, data: results, isPending } = useMutation({
    mutationFn: runMonteCarlo,
    onError: (e) => toast.error(e.message),
  })

  const handleRun = () => {
    if (!assets.length) { toast.error('Add at least one asset'); return }
    const totalWeight = assets.reduce((s, a) => s + Number(a.weight), 0)
    if (Math.abs(totalWeight - 100) > 1) { toast.error('Weights must sum to 100%'); return }

    mutate({
      tickers: assets.map((a) => a.ticker),
      weights: assets.map((a) => a.weight / 100),
      initial_amount: Number(settings.initial_amount),
      years: Number(settings.years),
      simulations: Number(settings.simulations),
      annual_withdrawal: Number(settings.annual_withdrawal),
      annual_contribution: Number(settings.annual_contribution),
      model: settings.model,
      start_year: Number(settings.start_year),
      end_year: settings.end_year ? Number(settings.end_year) : null,
      inflation_rate: Number(settings.inflation_rate) / 100,
      management_fee: Number(settings.management_fee) / 100,
      mean_return: settings.mean_return ? Number(settings.mean_return) / 100 : null,
      std_dev: settings.std_dev ? Number(settings.std_dev) / 100 : null,
    })
  }

  // Build fan chart traces
  const buildTraces = () => {
    if (!results) return []
    const { percentiles, years } = results

    const traces = []
    // 10-90 band
    traces.push({
      x: [...years, ...years.slice().reverse()],
      y: [...percentiles['90'], ...percentiles['10'].slice().reverse()],
      fill: 'toself', fillcolor: 'rgba(59,130,246,0.1)',
      line: { color: 'transparent' }, name: '10th–90th %ile',
      showlegend: true, type: 'scatter',
    })
    // 25-75 band
    traces.push({
      x: [...years, ...years.slice().reverse()],
      y: [...percentiles['75'], ...percentiles['25'].slice().reverse()],
      fill: 'toself', fillcolor: 'rgba(59,130,246,0.2)',
      line: { color: 'transparent' }, name: '25th–75th %ile',
      showlegend: true, type: 'scatter',
    })
    // Median line
    traces.push({
      x: years, y: percentiles['50'],
      type: 'scatter', mode: 'lines',
      name: 'Median (50th)',
      line: { color: '#3b82f6', width: 2.5 },
    })
    // 10th / 90th lines
    traces.push({
      x: years, y: percentiles['10'],
      type: 'scatter', mode: 'lines', name: '10th %ile',
      line: { color: '#ef4444', width: 1.5, dash: 'dot' },
    })
    traces.push({
      x: years, y: percentiles['90'],
      type: 'scatter', mode: 'lines', name: '90th %ile',
      line: { color: '#10b981', width: 1.5, dash: 'dot' },
    })
    return traces
  }

  const fmt$ = (v) => v == null ? '—' : `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6 items-start">
      {/* Left */}
      <div className="space-y-4">
        <div className="card space-y-3">
          <h2 className="section-title">Portfolio Assets</h2>
          <TickerInput assets={assets} onChange={setAssets} />
        </div>

        <div className="card space-y-3">
          <h2 className="section-title">Simulation Settings</h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Initial Amount ($)</label>
              <input type="number" className="input" value={settings.initial_amount}
                onChange={(e) => setSettings((s) => ({ ...s, initial_amount: e.target.value }))} />
            </div>
            <div>
              <label className="label">Years</label>
              <input type="number" className="input" value={settings.years} min="1" max="100"
                onChange={(e) => setSettings((s) => ({ ...s, years: e.target.value }))} />
            </div>
            <div>
              <label className="label">Annual Withdrawal ($)</label>
              <input type="number" className="input" value={settings.annual_withdrawal}
                onChange={(e) => setSettings((s) => ({ ...s, annual_withdrawal: e.target.value }))} />
            </div>
            <div>
              <label className="label">Annual Contribution ($)</label>
              <input type="number" className="input" value={settings.annual_contribution}
                onChange={(e) => setSettings((s) => ({ ...s, annual_contribution: e.target.value }))} />
            </div>
            <div>
              <label className="label">Simulations</label>
              <select className="select" value={settings.simulations}
                onChange={(e) => setSettings((s) => ({ ...s, simulations: e.target.value }))}>
                <option value="500">500</option>
                <option value="1000">1,000</option>
                <option value="5000">5,000</option>
                <option value="10000">10,000</option>
              </select>
            </div>
            <div>
              <label className="label">Return Model</label>
              <select className="select" value={settings.model}
                onChange={(e) => setSettings((s) => ({ ...s, model: e.target.value }))}>
                <option value="historical">Historical</option>
                <option value="statistical">Statistical</option>
                <option value="forecasted">Forecasted</option>
                <option value="parameterized">Parameterized</option>
              </select>
            </div>
          </div>

          {(settings.model === 'forecasted' || settings.model === 'parameterized') && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Mean Return (%/yr)</label>
                <input type="number" className="input" value={settings.mean_return} step="0.1"
                  onChange={(e) => setSettings((s) => ({ ...s, mean_return: e.target.value }))} />
              </div>
              <div>
                <label className="label">Std Dev (%/yr)</label>
                <input type="number" className="input" value={settings.std_dev} step="0.1"
                  onChange={(e) => setSettings((s) => ({ ...s, std_dev: e.target.value }))} />
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Historical Start Year</label>
              <input type="number" className="input" value={settings.start_year} min="1970" max="2023"
                onChange={(e) => setSettings((s) => ({ ...s, start_year: e.target.value }))} />
            </div>
            <div>
              <label className="label">Historical End Year</label>
              <input type="number" className="input" placeholder="Current" value={settings.end_year}
                onChange={(e) => setSettings((s) => ({ ...s, end_year: e.target.value }))} />
            </div>
            <div>
              <label className="label">Inflation Rate (%)</label>
              <input type="number" className="input" value={settings.inflation_rate} step="0.1"
                onChange={(e) => setSettings((s) => ({ ...s, inflation_rate: e.target.value }))} />
            </div>
            <div>
              <label className="label">Management Fee (%)</label>
              <input type="number" className="input" value={settings.management_fee} step="0.05"
                onChange={(e) => setSettings((s) => ({ ...s, management_fee: e.target.value }))} />
            </div>
          </div>
        </div>

        <button onClick={handleRun} disabled={isPending} className="btn-primary w-full">
          {isPending ? 'Simulating…' : 'Run Simulation'}
        </button>
      </div>

      {/* Right */}
      <div className="space-y-6">
        {isPending && (
          <div className="card flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500">Running {Number(settings.simulations).toLocaleString()} simulations…</p>
            </div>
          </div>
        )}

        {results && !isPending && (
          <>
            {/* Summary stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: 'Success Rate', value: `${results.success_rate}%`, sub: 'portfolio survives' },
                { label: 'Median Outcome', value: fmt$(results.median_final), sub: '50th percentile' },
                { label: '10th Percentile', value: fmt$(results.p10_final), sub: 'pessimistic' },
                { label: '90th Percentile', value: fmt$(results.p90_final), sub: 'optimistic' },
              ].map(({ label, value, sub }) => (
                <div key={label} className="metric-card">
                  <div className="metric-label">{label}</div>
                  <div className="metric-value text-xl">{value}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{sub}</div>
                </div>
              ))}
            </div>

            <div className="card">
              <h3 className="section-title">Projected Portfolio Value</h3>
              <PlotlyChart
                data={buildTraces()}
                layout={{
                  xaxis: { title: 'Year', dtick: 5 },
                  yaxis: { title: 'Portfolio Value ($)', tickformat: '$,.0f' },
                  hovermode: 'x',
                }}
              />
            </div>

            {/* Percentile table */}
            <div className="card">
              <h3 className="section-title">Percentile Outcomes by Year</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 pr-4 text-gray-500 font-medium">Year</th>
                      {['10th', '25th', '50th', '75th', '90th'].map((p) => (
                        <th key={p} className="text-right py-2 px-3 font-semibold text-gray-800">{p}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {results.years.filter((y) => y % 5 === 0 || y === results.years[results.years.length - 1]).map((yr) => (
                      <tr key={yr} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-1.5 pr-4 text-gray-600">{yr}</td>
                        {['10','25','50','75','90'].map((p) => (
                          <td key={p} className="text-right py-1.5 px-3">
                            {fmt$(results.percentiles[p]?.[yr])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {!results && !isPending && (
          <div className="card flex items-center justify-center h-64 text-gray-400 text-sm">
            Add assets, configure settings, and click "Run Simulation".
          </div>
        )}
      </div>
    </div>
  )
}
