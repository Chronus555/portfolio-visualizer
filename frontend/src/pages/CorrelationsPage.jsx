import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { analyzeCorrelations } from '../api/client'
import TickerInput from '../components/common/TickerInput'
import PlotlyChart from '../components/common/PlotlyChart'

function corrColor(v) {
  if (v >= 0.8) return '#1e3a8a'
  if (v >= 0.6) return '#2563eb'
  if (v >= 0.4) return '#60a5fa'
  if (v >= 0.2) return '#bfdbfe'
  if (v >= 0) return '#f0f9ff'
  if (v >= -0.2) return '#fef9c3'
  if (v >= -0.4) return '#fde047'
  if (v >= -0.6) return '#f97316'
  return '#b91c1c'
}

function corrTextColor(v) {
  return Math.abs(v) >= 0.6 ? 'text-white' : 'text-gray-800'
}

export default function CorrelationsPage() {
  const [assets, setAssets] = useState([])
  const [settings, setSettings] = useState({
    start_year: 2000,
    end_year: '',
    method: 'pearson',
    rolling_window: '',
  })
  const [activeTab, setActiveTab] = useState('matrix')

  const { mutate, data: results, isPending } = useMutation({
    mutationFn: analyzeCorrelations,
    onError: (e) => toast.error(e.message),
  })

  const handleRun = () => {
    if (assets.length < 2) { toast.error('Add at least 2 assets'); return }
    mutate({
      tickers: assets.map((a) => a.ticker),
      start_year: Number(settings.start_year),
      end_year: settings.end_year ? Number(settings.end_year) : null,
      method: settings.method,
      rolling_window: settings.rolling_window ? Number(settings.rolling_window) : null,
    })
  }

  // Build heatmap trace
  const buildHeatmap = () => {
    if (!results) return []
    const { tickers, matrix } = results
    return [{
      type: 'heatmap',
      x: tickers,
      y: tickers,
      z: matrix,
      colorscale: [
        [0, '#b91c1c'], [0.25, '#f97316'], [0.5, '#f0f9ff'],
        [0.75, '#60a5fa'], [1, '#1e3a8a'],
      ],
      zmin: -1, zmax: 1,
      text: matrix.map((row) => row.map((v) => v.toFixed(3))),
      texttemplate: '%{text}',
      showscale: true,
      colorbar: { title: 'Correlation', len: 0.8 },
    }]
  }

  // Build rolling correlation traces
  const buildRollingTraces = () => {
    if (!results?.rolling_data?.length) return []
    const keys = Object.keys(results.rolling_data[0]).filter((k) => k !== 'date')
    const colors = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6','#ec4899']
    return keys.map((key, i) => ({
      x: results.rolling_data.map((d) => d.date),
      y: results.rolling_data.map((d) => d[key]),
      name: key.replace('_vs_', ' vs '),
      type: 'scatter',
      mode: 'lines',
      line: { color: colors[i % colors.length], width: 1.5 },
    }))
  }

  // Build PCA bar chart
  const buildPCAChart = () => {
    if (!results?.pca_variance_explained) return []
    const cumulative = results.pca_variance_explained.reduce((acc, v, i) => {
      acc.push((acc[i - 1] || 0) + v)
      return acc
    }, [])
    return [
      {
        x: results.pca_variance_explained.map((_, i) => `PC${i + 1}`),
        y: results.pca_variance_explained,
        type: 'bar',
        name: 'Variance Explained',
        marker: { color: '#3b82f6' },
      },
      {
        x: results.pca_variance_explained.map((_, i) => `PC${i + 1}`),
        y: cumulative,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Cumulative',
        yaxis: 'y2',
        line: { color: '#ef4444', width: 2 },
        marker: { size: 6 },
      },
    ]
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6 items-start">
      {/* Left */}
      <div className="space-y-4">
        <div className="card space-y-3">
          <h2 className="section-title">Assets</h2>
          <TickerInput assets={assets} onChange={setAssets} showWeights={false} />
        </div>

        <div className="card space-y-3">
          <h2 className="section-title">Settings</h2>

          <div>
            <label className="label">Correlation Method</label>
            <select className="select" value={settings.method}
              onChange={(e) => setSettings((s) => ({ ...s, method: e.target.value }))}>
              <option value="pearson">Pearson (Linear)</option>
              <option value="spearman">Spearman (Rank)</option>
              <option value="kendall">Kendall (Rank)</option>
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
          </div>

          <div>
            <label className="label">Rolling Window (months, optional)</label>
            <input type="number" className="input" placeholder="e.g. 36" value={settings.rolling_window}
              onChange={(e) => setSettings((s) => ({ ...s, rolling_window: e.target.value }))} min="6" max="120" />
          </div>
        </div>

        <button onClick={handleRun} disabled={isPending} className="btn-primary w-full">
          {isPending ? 'Analyzing…' : 'Analyze Correlations'}
        </button>
      </div>

      {/* Right */}
      <div className="space-y-6">
        {isPending && (
          <div className="card flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500">Computing correlations…</p>
            </div>
          </div>
        )}

        {results && !isPending && (
          <>
            {/* Tabs */}
            <div className="flex gap-1 flex-wrap">
              {[
                ['matrix', 'Correlation Matrix'],
                ...(results.rolling_data ? [['rolling', 'Rolling Correlations']] : []),
                ['pca', 'PCA'],
              ].map(([tab, label]) => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`tab-btn ${activeTab === tab ? 'active' : ''}`}>
                  {label}
                </button>
              ))}
            </div>

            {activeTab === 'matrix' && (
              <>
                {/* Plotly heatmap */}
                <div className="card">
                  <h3 className="section-title">Correlation Heatmap</h3>
                  <PlotlyChart
                    data={buildHeatmap()}
                    layout={{
                      xaxis: { side: 'bottom' },
                      yaxis: { autorange: 'reversed' },
                      margin: { t: 20, r: 80, b: 60, l: 60 },
                    }}
                    style={{ minHeight: 420 }}
                  />
                </div>

                {/* Manual table for readability */}
                <div className="card">
                  <h3 className="section-title">Correlation Table</h3>
                  <div className="overflow-x-auto">
                    <table className="text-sm w-full">
                      <thead>
                        <tr>
                          <th className="text-left py-1.5 pr-3 font-medium text-gray-500"></th>
                          {results.tickers.map((t) => (
                            <th key={t} className="text-center py-1.5 px-2 font-mono font-semibold text-gray-700">{t}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {results.tickers.map((row, i) => (
                          <tr key={row}>
                            <td className="py-1.5 pr-3 font-mono font-semibold text-gray-700">{row}</td>
                            {results.matrix[i].map((v, j) => (
                              <td key={j}
                                className={`text-center py-1.5 px-2 text-xs font-medium rounded ${corrTextColor(v)}`}
                                style={{ backgroundColor: corrColor(v) }}>
                                {v.toFixed(3)}
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

            {activeTab === 'rolling' && results.rolling_data && (
              <div className="card">
                <h3 className="section-title">Rolling Correlations ({settings.rolling_window}-Month Window)</h3>
                <PlotlyChart
                  data={buildRollingTraces()}
                  layout={{
                    yaxis: { title: 'Correlation', range: [-1.05, 1.05] },
                    xaxis: { title: 'Date' },
                    shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 0, y1: 0, line: { color: '#9ca3af', dash: 'dash', width: 1 } }],
                  }}
                />
              </div>
            )}

            {activeTab === 'pca' && results.pca_variance_explained && (
              <>
                <div className="card">
                  <h3 className="section-title">PCA — Variance Explained</h3>
                  <PlotlyChart
                    data={buildPCAChart()}
                    layout={{
                      yaxis: { title: 'Variance Explained (%)', ticksuffix: '%' },
                      yaxis2: { title: 'Cumulative (%)', overlaying: 'y', side: 'right', ticksuffix: '%', range: [0, 105] },
                      xaxis: { title: 'Principal Component' },
                      legend: { orientation: 'h', y: -0.2 },
                    }}
                  />
                </div>

                <div className="card">
                  <h3 className="section-title">PCA Component Loadings</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-2 font-medium text-gray-500">Component</th>
                          <th className="text-right py-2 font-medium text-gray-500">Var. Explained</th>
                          {results.tickers.map((t) => (
                            <th key={t} className="text-right py-2 font-mono font-medium text-gray-500">{t}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {results.pca_components?.map((comp) => (
                          <tr key={comp.component} className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="py-1.5 font-semibold">{comp.component}</td>
                            <td className="text-right py-1.5">{comp.variance_explained?.toFixed(2)}%</td>
                            {results.tickers.map((t) => {
                              const v = comp[t] || 0
                              return (
                                <td key={t} className={`text-right py-1.5 font-medium ${v >= 0 ? 'positive' : 'negative'}`}>
                                  {v.toFixed(4)}
                                </td>
                              )
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {!results && !isPending && (
          <div className="card flex items-center justify-center h-64 text-gray-400 text-sm">
            Add at least 2 assets and click "Analyze Correlations".
          </div>
        )}
      </div>
    </div>
  )
}
