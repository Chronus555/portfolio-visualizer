import clsx from 'clsx'

const fmt = (v, decimals = 2) =>
  v == null ? '—' : Number(v).toFixed(decimals)

const fmtPct = (v) => {
  if (v == null) return { text: '—', positive: null }
  const n = Number(v)
  return { text: `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`, positive: n >= 0 }
}

const fmtDollar = (v) =>
  v == null ? '—' : `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`

const ROWS = [
  { key: 'cagr',               label: 'CAGR',               pct: true,  group: 'Returns' },
  { key: 'stdev',              label: 'Std Dev (Ann.)',      pct: true,  group: 'Returns' },
  { key: 'best_year',          label: 'Best Year',          pct: true,  group: 'Returns' },
  { key: 'worst_year',         label: 'Worst Year',         pct: true,  group: 'Returns' },
  { key: 'sharpe_ratio',       label: 'Sharpe Ratio',       pct: false, group: 'Risk' },
  { key: 'sortino_ratio',      label: 'Sortino Ratio',      pct: false, group: 'Risk' },
  { key: 'max_drawdown',       label: 'Max Drawdown',       pct: true,  group: 'Risk' },
  { key: 'market_correlation', label: 'Market Corr.',       pct: false, group: 'Risk' },
  { key: 'final_balance',      label: 'Final Balance',      dollar: true, group: 'Result' },
]

const PORTFOLIO_COLORS = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6','#ec4899']

export default function MetricsTable({ metrics = [] }) {
  if (!metrics.length) return null

  const groups = [...new Set(ROWS.map(r => r.group))]

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 dark:bg-gray-800/60">
            <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 w-40">
              Metric
            </th>
            {metrics.map((m, i) => (
              <th key={m.portfolio_name} className="text-right py-3 px-4 font-semibold text-gray-800 dark:text-gray-200">
                <div className="flex items-center justify-end gap-2">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: PORTFOLIO_COLORS[i % PORTFOLIO_COLORS.length] }} />
                  <span className="text-xs">{m.portfolio_name}</span>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <>
              {/* Group header */}
              <tr key={`group-${group}`} className="bg-gray-50/50 dark:bg-gray-800/30">
                <td
                  colSpan={metrics.length + 1}
                  className="px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-gray-600"
                >
                  {group}
                </td>
              </tr>

              {ROWS.filter(r => r.group === group).map(({ key, label, pct, dollar }, rowIdx) => (
                <tr
                  key={key}
                  className="border-t border-gray-100 dark:border-gray-800 hover:bg-blue-50/30 dark:hover:bg-blue-950/20 transition-colors"
                >
                  <td className="py-2.5 px-4 text-gray-600 dark:text-gray-400 font-medium text-xs">
                    {label}
                  </td>
                  {metrics.map((m, i) => {
                    const raw = m[key]
                    if (dollar) {
                      return (
                        <td key={m.portfolio_name} className="text-right py-2.5 px-4 font-semibold text-gray-900 dark:text-gray-100">
                          {fmtDollar(raw)}
                        </td>
                      )
                    }
                    if (pct) {
                      const { text, positive } = fmtPct(Number(raw) * 100)
                      return (
                        <td key={m.portfolio_name} className={clsx(
                          'text-right py-2.5 px-4 font-semibold',
                          positive === true ? 'text-emerald-600 dark:text-emerald-400' :
                          positive === false ? 'text-red-500 dark:text-red-400' :
                          'text-gray-500'
                        )}>
                          {text}
                        </td>
                      )
                    }
                    return (
                      <td key={m.portfolio_name} className="text-right py-2.5 px-4 font-medium text-gray-700 dark:text-gray-300">
                        {fmt(raw, 3)}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </>
          ))}
        </tbody>
      </table>
    </div>
  )
}
