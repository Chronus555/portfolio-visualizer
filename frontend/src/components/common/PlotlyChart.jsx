import Plot from 'react-plotly.js'
import { useEffect, useState } from 'react'

const CONFIG = {
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
  toImageButtonOptions: { format: 'png', filename: 'chart', scale: 2 },
  responsive: true,
}

function getLayout(dark) {
  const gridColor  = dark ? '#30363d' : '#f0f0f0'
  const tickColor  = dark ? '#8b949e' : '#6b7280'
  const titleColor = dark ? '#8b949e' : '#6b7280'
  const bgColor    = 'rgba(0,0,0,0)'

  return {
    font: { family: 'Inter, system-ui, sans-serif', size: 12, color: tickColor },
    paper_bgcolor: bgColor,
    plot_bgcolor:  bgColor,
    margin: { t: 20, r: 20, b: 50, l: 65 },
    xaxis: {
      gridcolor: gridColor,
      linecolor: gridColor,
      tickcolor: tickColor,
      zeroline: false,
      automargin: true,
    },
    yaxis: {
      gridcolor: gridColor,
      linecolor: gridColor,
      tickcolor: tickColor,
      zeroline: false,
      automargin: true,
    },
    legend: {
      orientation: 'h',
      y: -0.18,
      x: 0.5,
      xanchor: 'center',
      bgcolor: 'rgba(0,0,0,0)',
      font: { size: 11, color: tickColor },
    },
    hovermode: 'x unified',
    hoverlabel: {
      bgcolor: dark ? '#21262d' : '#ffffff',
      bordercolor: dark ? '#30363d' : '#e2e8f0',
      font: { color: dark ? '#e6edf3' : '#0f172a', size: 12 },
    },
    modebar: {
      bgcolor: 'rgba(0,0,0,0)',
      color: tickColor,
      activecolor: dark ? '#58a6ff' : '#3b82f6',
    },
  }
}

export default function PlotlyChart({ data, layout = {}, style = {}, config = {} }) {
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const check = () => setDark(document.documentElement.classList.contains('dark'))
    check()
    const obs = new MutationObserver(check)
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => obs.disconnect()
  }, [])

  const baseLayout = getLayout(dark)

  return (
    <Plot
      data={data}
      layout={{
        ...baseLayout,
        ...layout,
        xaxis: { ...baseLayout.xaxis, ...(layout.xaxis || {}) },
        yaxis: { ...baseLayout.yaxis, ...(layout.yaxis || {}) },
      }}
      config={{ ...CONFIG, ...config }}
      style={{ width: '100%', minHeight: 380, ...style }}
      useResizeHandler
    />
  )
}
