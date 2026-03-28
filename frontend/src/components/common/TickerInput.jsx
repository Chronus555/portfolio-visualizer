import { useState, useCallback } from 'react'
import { X, Plus, SlidersHorizontal } from 'lucide-react'
import { validateTicker } from '../../api/client'
import toast from 'react-hot-toast'

const COLORS = [
  '#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6',
  '#ec4899','#14b8a6','#f97316','#6366f1','#84cc16',
]

export default function TickerInput({ assets, onChange, maxAssets = 50, showWeights = true }) {
  const [inputTicker, setInputTicker] = useState('')
  const [inputWeight, setInputWeight] = useState('')
  const [validating, setValidating] = useState(false)

  const totalWeight = assets.reduce((s, a) => s + Number(a.weight || 0), 0)
  const weightOk = Math.abs(totalWeight - 100) <= 0.5

  const addAsset = useCallback(async () => {
    const ticker = inputTicker.trim().toUpperCase()
    if (!ticker) return
    if (assets.find((a) => a.ticker === ticker)) {
      toast.error(`${ticker} already in portfolio`)
      return
    }
    if (assets.length >= maxAssets) {
      toast.error(`Maximum ${maxAssets} assets`)
      return
    }

    setValidating(true)
    try {
      const result = await validateTicker(ticker)
      if (!result.valid) {
        toast.error(`"${ticker}" not found`)
        setValidating(false)
        return
      }
      const weight = Number(inputWeight) || Math.max(0, Math.round((100 - totalWeight) * 10) / 10)
      onChange([...assets, { ticker, weight, name: result.name, color: COLORS[assets.length % COLORS.length] }])
      setInputTicker('')
      setInputWeight('')
    } catch {
      toast.error('Could not validate ticker')
    } finally {
      setValidating(false)
    }
  }, [inputTicker, inputWeight, assets, onChange, totalWeight, maxAssets])

  const removeAsset = (ticker) => onChange(assets.filter((a) => a.ticker !== ticker))

  const updateWeight = (ticker, weight) =>
    onChange(assets.map((a) => (a.ticker === ticker ? { ...a, weight: Number(weight) } : a)))

  const equaliseWeights = () => {
    const w = +(100 / assets.length).toFixed(2)
    onChange(assets.map((a) => ({ ...a, weight: w })))
  }

  return (
    <div className="space-y-2">

      {/* Asset list */}
      {assets.length > 0 && (
        <div className="space-y-1.5">
          {assets.map((asset) => (
            <div key={asset.ticker}
              className="group flex items-center gap-2 px-2.5 py-2 rounded-lg
                bg-gray-50 dark:bg-gray-800/60
                border border-transparent hover:border-gray-200 dark:hover:border-gray-700
                transition-all duration-150">

              {/* Color dot */}
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: asset.color }} />

              {/* Ticker */}
              <span className="font-mono font-bold text-xs w-14 shrink-0 text-gray-800 dark:text-gray-200">
                {asset.ticker}
              </span>

              {/* Name */}
              <span className="text-xs text-gray-400 dark:text-gray-500 flex-1 truncate hidden sm:block">
                {asset.name}
              </span>

              {/* Weight input + bar */}
              {showWeights && (
                <div className="shrink-0 flex items-center gap-1.5">
                  <div className="relative">
                    <input
                      type="number"
                      min="0" max="100" step="0.5"
                      value={asset.weight}
                      onChange={(e) => updateWeight(asset.ticker, e.target.value)}
                      className="input w-16 text-right text-xs py-1 pr-6 font-semibold"
                    />
                    <span className="absolute right-1.5 top-1/2 -translate-y-1/2 text-xs text-gray-400 pointer-events-none">%</span>
                  </div>
                </div>
              )}

              {/* Remove */}
              <button
                onClick={() => removeAsset(asset.ticker)}
                className="btn-ghost opacity-0 group-hover:opacity-100 !p-1 text-gray-400 hover:text-red-500"
              >
                <X size={13} />
              </button>
            </div>
          ))}

          {/* Weight bar */}
          {showWeights && assets.length > 0 && (
            <div className="px-1">
              <div className="weight-bar">
                <div className="flex h-full">
                  {assets.map((a) => (
                    <div
                      key={a.ticker}
                      className="weight-bar-fill transition-all duration-300"
                      style={{
                        width: `${Math.min((a.weight / 100) * 100, 100)}%`,
                        backgroundColor: a.color,
                      }}
                    />
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between mt-2">
                <span className={`text-xs font-semibold flex items-center gap-1.5 ${weightOk ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${weightOk ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  {totalWeight.toFixed(1)}%
                  {!weightOk && <span className="font-normal text-gray-400">(must = 100%)</span>}
                </span>
                <button
                  onClick={equaliseWeights}
                  className="flex items-center gap-1 text-xs text-blue-500 dark:text-blue-400 hover:underline font-medium"
                >
                  <SlidersHorizontal size={10} /> Equal weights
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add asset input */}
      <div className="flex gap-1.5 pt-1">
        <input
          type="text"
          placeholder="Ticker (e.g. AAPL)"
          value={inputTicker}
          onChange={(e) => setInputTicker(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && addAsset()}
          className="input flex-1 font-mono text-xs"
        />
        {showWeights && (
          <input
            type="number"
            placeholder="Wt %"
            value={inputWeight}
            onChange={(e) => setInputWeight(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addAsset()}
            className="input w-16 text-xs"
            min="0" max="100"
          />
        )}
        <button
          onClick={addAsset}
          disabled={validating || !inputTicker}
          className="btn-primary flex items-center gap-1 px-3 py-1.5 text-xs shrink-0"
        >
          {validating ? (
            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Plus size={14} />
          )}
          Add
        </button>
      </div>
    </div>
  )
}
