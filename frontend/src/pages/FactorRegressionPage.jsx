import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { runFactorRegression } from '../api/client'
import TickerInput from '../components/common/TickerInput'
import PlotlyChart from '../components/common/PlotlyChart'

const FACTOR_DESCRIPTIONS = {
  'Mkt-RF': 'Market Risk Premium',
  SMB: 'Small Minus Big (Size)',
  HML: 'High Minus Low (Value)',
  RMW: 'Robust Minus Weak (Profitability)',
  CMA: 'Conservative Minus Aggressive (Investment)',
  MOM: 'Momentum',
}

const MODEL_FACTORS = {
  ff3: ['Mkt-RF', 'SMB', 'HML'],
  ff5: ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA'],
  carhart4: ['Mkt-RF', 'SMB', 'HML', 'MOM'],
}

export default function FactorRegressionPage() {
  const [assets, setAssets] = useState([])
  const [settings, setSettings] = useState({
    model: 'ff3',
    start_year: 2000,
    end_year: '',
    mode: 'individual', // 'individual' or 'portfolio'
  })
  const [selected, setSelected] = useState(null)

  const { mutate, data: results, isPending } = useMutation({
    mutationFn: runFactorRegression,
    onError: (e) => toast.error(e.message),
    onSuccess: (data) => setSelected(data[0]?.ticker || null),
  })

  const handleRun = () => {
    if (!assets.length) { toast.error('Add at least one asset'); return }
    const totalWeight = assets.reduce((s, a) => s + Number(a.weight), 0)

    mutate({
      tickers: assets.map((a) => a.ticker),
      weights: settings.mode === 'portfolio'
        ? assets.map((a) => a.weight / 100)
        : null,
      model: settings.model,
      start_year: Number(settings.start_year),
      end_year: settings.end_year ? Number(settings.end_year) : null,
    })
  }

  const current = results?.find((r) => r.ticker === selected) || results?.[0]

  const buildContributionChart = (result) => {
    if (!result) return []
    const factors = Object.entries(result.factor_returns_contribution)
    return [{
      x: factors.map(([f]) => f),
      y: factors.map(([, v]) => +(v * 100).toFixed(3)),
      type: 'bar',
      marker: {
        color: factors.map(([, v]) => v >= 0 ? '#3b82f6' : '#ef4444'),
      },
      name: 'Factor Contribution (%/yr)',
    }]
  }

  const sigColor = (p) => p < 0.01 ? 'text-green-700 font-semibold' : p < 0.05 ? 'text-yellow-700' : 'text-gray-400'

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6 items-start">
      {/* Left */}
      <div className="space-y-4">
        <div className="card space-y-3">
          <h2 className="section-title">Assets</h2>
          <TickerInput
            assets={assets}
            onChange={setAssets}
            showWeights={settings.mode === 'portfolio'}
          />
        </div>

        <div className="card space-y-3">
          <h2 className="section-title">Regression Settings</h2>

          <div>
            <label className="label">Mode</label>
            <select className="select" value={settings.mode}
              onChange={(e) => setSettings((s) => ({ ...s, mode: e.target.value }))}>
              <option value="individual">Individual Ticker Regressions</option>
              <option value="portfolio">Portfolio Regression</option>
            </select>
          </div>

          <div>
            <label className="label">Factor Model</label>
            <select className="select" value={settings.model}
              onChange={(e) => setSettings((s) => ({ ...s, model: e.target.value }))}>
              <option value="ff3">Fama-French 3-Factor</option>
              <option value="ff5">Fama-French 5-Factor</option>
              <option value="carhart4">Carhart 4-Factor (FF3 + Momentum)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Start Year</label>
              <input type="number" className="input" value={settings.start_year} min="1926" max="2024"
                onChange={(e) => setSettings((s) => ({ ...s, start_year: e.target.value }))} />
            </div>
            <div>
              <label className="label">End Year</label>
              <input type="number" className="input" placeholder="Current" value={settings.end_year}
                onChange={(e) => setSettings((s) => ({ ...s, end_year: e.target.value }))} />
            </div>
          </div>

          {/* Factor legend */}
          <div className="text-xs text-gray-500 space-y-1 pt-1">
            <div className="font-medium text-gray-700">Factors in {settings.model.toUpperCase()}:</div>
            {MODEL_FACTORS[settings.model]?.map((f) => (
              <div key={f}><span className="font-mono text-blue-700">{f}</span> — {FACTOR_DESCRIPTIONS[f]}</div>
            ))}
          </div>
        </div>

        <button onClick={handleRun} disabled={isPending} className="btn-primary w-full">
          {isPending ? 'Running Regression…' : 'Run Factor Regression'}
        </button>
      </div>

      {/* Right */}
      <div className="space-y-6">
        {isPending && (
          <div className="card flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500">Fetching factors and running OLS regression…</p>
            </div>
          </div>
        )}

        {results && !isPending && (
          <>
            {/* Ticker selector tabs */}
            {results.length > 1 && (
              <div className="flex gap-1 flex-wrap">
                {results.map((r) => (
                  <button key={r.ticker} onClick={() => setSelected(r.ticker)}
                    className={`tab-btn ${selected === r.ticker ? 'active' : ''}`}>
                    {r.ticker}
                  </button>
                ))}
              </div>
            )}

            {current && (
              <>
                {/* Summary stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Alpha (Monthly)', value: `${(current.alpha * 100).toFixed(4)}%` },
                    { label: 'Alpha (Annual)', value: `${(current.alpha_annualized * 100).toFixed(2)}%` },
                    { label: 'R²', value: current.r_squared.toFixed(4) },
                    { label: 'Observations', value: current.observations },
                  ].map(({ label, value }) => (
                    <div key={label} className="metric-card">
                      <div className="metric-label">{label}</div>
                      <div className="metric-value text-xl">{value}</div>
                    </div>
                  ))}
                </div>

                {/* Coefficients table */}
                <div className="card">
                  <h3 className="section-title">Factor Coefficients — {current.ticker}</h3>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 text-gray-500 font-medium">Factor</th>
                        <th className="text-right py-2 text-gray-500 font-medium">Loading (β)</th>
                        <th className="text-right py-2 text-gray-500 font-medium">t-stat</th>
                        <th className="text-right py-2 text-gray-500 font-medium">p-value</th>
                        <th className="text-right py-2 text-gray-500 font-medium">Significant</th>
                      </tr>
                    </thead>
                    <tbody>
                      {current.coefficients.map((c) => (
                        <tr key={c.factor} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-2 font-mono font-semibold text-blue-700">{c.factor}</td>
                          <td className={`text-right py-2 font-medium ${c.coefficient >= 0 ? 'positive' : 'negative'}`}>
                            {c.coefficient.toFixed(4)}
                          </td>
                          <td className="text-right py-2">{c.t_stat.toFixed(3)}</td>
                          <td className={`text-right py-2 ${sigColor(c.p_value)}`}>{c.p_value.toFixed(4)}</td>
                          <td className="text-right py-2">
                            {c.significant ? (
                              <span className="text-green-600 font-semibold">Yes</span>
                            ) : (
                              <span className="text-gray-400">No</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Factor contributions chart */}
                <div className="card">
                  <h3 className="section-title">Annual Factor Return Contributions</h3>
                  <PlotlyChart
                    data={buildContributionChart(current)}
                    layout={{
                      yaxis: { title: 'Contribution (%/yr)', ticksuffix: '%' },
                      xaxis: { title: 'Factor' },
                      showlegend: false,
                    }}
                  />
                </div>

                {/* Interpretation */}
                <div className="card bg-blue-50 border-blue-200">
                  <h3 className="section-title text-blue-800">Interpretation</h3>
                  <div className="text-sm text-blue-900 space-y-1">
                    <p>
                      <strong>Alpha ({(current.alpha_annualized * 100).toFixed(2)}%/yr):</strong>{' '}
                      {current.alpha_annualized > 0
                        ? 'Positive alpha suggests outperformance above what factor exposures explain.'
                        : 'Negative alpha suggests underperformance relative to factor exposures.'}
                    </p>
                    <p>
                      <strong>R² ({current.r_squared.toFixed(4)}):</strong>{' '}
                      {(current.r_squared * 100).toFixed(1)}% of return variance is explained by the {settings.model.toUpperCase()} factors.
                    </p>
                    <p>
                      <strong>Residual Std ({(current.residual_std * 100).toFixed(2)}%/yr):</strong>{' '}
                      Idiosyncratic (unexplained) risk annualised.
                    </p>
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {!results && !isPending && (
          <div className="card flex items-center justify-center h-64 text-gray-400 text-sm">
            Add assets and click "Run Factor Regression".
          </div>
        )}
      </div>
    </div>
  )
}
