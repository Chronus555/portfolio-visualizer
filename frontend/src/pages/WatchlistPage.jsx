import { useState, useEffect } from 'react'
import { useQueries } from '@tanstack/react-query'
import { Eye, Plus, Trash2, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { validateTicker } from '../api/client'
import toast from 'react-hot-toast'

const STORAGE_KEY = 'pv_watchlist'

const loadWatchlist = () => {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') }
  catch { return [] }
}

const saveWatchlist = (list) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

function TickerCard({ ticker, onRemove }) {
  // We use validateTicker which gives us name + valid status — for a real-time price
  // we'd need a different endpoint; here we show a "live-ish" card with yfinance data
  const [price, setPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [info, setInfo] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetch(`/api/funds/validate?ticker=${ticker}`)
      .then(r => r.json())
      .then(d => {
        if (!cancelled) { setInfo(d); setLoading(false) }
      })
      .catch(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [ticker])

  return (
    <div className="panel group hover:border-blue-400/60 dark:hover:border-blue-500/40 transition-all">
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-base text-gray-900 dark:text-gray-100">{ticker}</span>
              {loading && <span className="w-3 h-3 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />}
            </div>
            {info?.name && (
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{info.name}</div>
            )}
          </div>
          <button onClick={() => onRemove(ticker)}
            className="btn-ghost opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 !p-1 shrink-0">
            <Trash2 size={13} />
          </button>
        </div>

        {info && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {info.asset_class && (
              <div className="text-[10px]">
                <span className="text-gray-400 block">Type</span>
                <span className="font-medium text-gray-700 dark:text-gray-300">{info.asset_class}</span>
              </div>
            )}
            {info.expense_ratio != null && (
              <div className="text-[10px]">
                <span className="text-gray-400 block">Expense Ratio</span>
                <span className={`font-semibold ${info.expense_ratio > 0.005 ? 'text-orange-500' : 'text-emerald-500'}`}>
                  {(info.expense_ratio * 100).toFixed(4)}%
                </span>
              </div>
            )}
            {info.category && (
              <div className="text-[10px] col-span-2">
                <span className="text-gray-400 block">Category</span>
                <span className="font-medium text-gray-700 dark:text-gray-300">{info.category}</span>
              </div>
            )}
            {info.fund_family && (
              <div className="text-[10px]">
                <span className="text-gray-400 block">Fund Family</span>
                <span className="font-medium text-gray-700 dark:text-gray-300">{info.fund_family}</span>
              </div>
            )}
          </div>
        )}

        {/* Quick action links */}
        <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-800 flex gap-2 flex-wrap">
          {[
            { label: 'Backtest', href: `/backtest?ticker=${ticker}` },
            { label: 'Dividend', href: `/dividend` },
            { label: 'Stress Test', href: `/stress-test` },
          ].map(link => (
            <a key={link.label} href={link.href}
              className="text-[10px] font-semibold text-blue-500 dark:text-blue-400 hover:underline">
              {link.label} →
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState(loadWatchlist)
  const [input, setInput] = useState('')
  const [adding, setAdding] = useState(false)

  useEffect(() => { saveWatchlist(watchlist) }, [watchlist])

  const addTicker = async () => {
    const t = input.trim().toUpperCase()
    if (!t) return
    if (watchlist.includes(t)) { toast.error(`${t} already in watchlist`); return }
    setAdding(true)
    try {
      const res = await validateTicker(t)
      if (!res.valid) { toast.error(`"${t}" not found`); return }
      setWatchlist(w => [...w, t])
      setInput('')
      toast.success(`Added ${t}`)
    } catch { toast.error('Could not validate ticker') }
    finally { setAdding(false) }
  }

  const removeTicker = (t) => {
    setWatchlist(w => w.filter(x => x !== t))
    toast.success(`Removed ${t}`)
  }

  const clearAll = () => { setWatchlist([]); toast.success('Watchlist cleared') }

  // Popular starters
  const SUGGESTIONS = ['SPY','QQQ','VTI','VXUS','BND','GLD','VNQ','TLT','BTC-USD','AAPL','MSFT','NVDA']

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Eye size={20} className="text-blue-500" /> Watchlist
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Track tickers and quickly access analysis tools. Saved locally in your browser.
          </p>
        </div>
        {watchlist.length > 0 && (
          <button onClick={clearAll} className="btn-secondary text-xs py-1.5 px-3 text-red-500 border-red-200 hover:bg-red-50">
            Clear All
          </button>
        )}
      </div>

      {/* Add ticker */}
      <div className="card">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Add ticker (e.g. AAPL, SPY, BTC-USD)"
            value={input}
            onChange={e => setInput(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && addTicker()}
            className="input flex-1 font-mono"
          />
          <button onClick={addTicker} disabled={adding || !input}
            className="btn-primary flex items-center gap-1.5 px-4">
            {adding ? <span className="spinner !w-4 !h-4" /> : <Plus size={16} />} Add
          </button>
        </div>

        {/* Quick-add suggestions */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className="text-xs text-gray-400 mr-1">Quick add:</span>
          {SUGGESTIONS.filter(s => !watchlist.includes(s)).slice(0, 8).map(s => (
            <button key={s} onClick={() => { setInput(s); }}
              className="px-2 py-0.5 rounded-full text-xs font-mono font-semibold
                bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400
                hover:bg-blue-100 dark:hover:bg-blue-950/40 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Watchlist grid */}
      {watchlist.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {watchlist.map(ticker => (
            <TickerCard key={ticker} ticker={ticker} onRemove={removeTicker} />
          ))}
        </div>
      ) : (
        <div className="card">
          <div className="empty-state py-16">
            <div className="empty-state-icon"><Eye size={28} className="text-gray-400 dark:text-gray-600" /></div>
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">Your watchlist is empty</h3>
            <p className="text-xs text-gray-400 max-w-xs">Add tickers above to track them. Click any watchlist card to quickly jump to backtest, dividend, or stress test analysis.</p>
          </div>
        </div>
      )}
    </div>
  )
}
