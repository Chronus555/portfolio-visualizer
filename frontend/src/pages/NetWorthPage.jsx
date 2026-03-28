import { useState, useEffect } from 'react'
import PlotlyChart from '../components/common/PlotlyChart'
import { Plus, Trash2, TrendingUp } from 'lucide-react'

const ASSET_CATS = ['Cash & Savings', 'Investments', 'Retirement Accounts', 'Real Estate', 'Vehicles', 'Other Assets']
const LIABILITY_CATS = ['Mortgage', 'Student Loans', 'Car Loans', 'Credit Cards', 'Personal Loans', 'Other Debt']

const STORAGE_KEY = 'nw_entries'
const HISTORY_KEY = 'nw_history'

let nextId = Date.now()

const DEFAULT_ASSETS = [
  { id: nextId++, category: 'Cash & Savings', name: 'Checking Account', value: 5000 },
  { id: nextId++, category: 'Investments', name: 'Brokerage Account', value: 50000 },
  { id: nextId++, category: 'Retirement Accounts', name: '401(k)', value: 80000 },
  { id: nextId++, category: 'Real Estate', name: 'Home', value: 450000 },
]

const DEFAULT_LIABILITIES = [
  { id: nextId++, category: 'Mortgage', name: 'Home Mortgage', value: 320000 },
  { id: nextId++, category: 'Car Loans', name: 'Car Loan', value: 12000 },
  { id: nextId++, category: 'Student Loans', name: 'Student Loan', value: 25000 },
]

export default function NetWorthPage() {
  const [assets, setAssets] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY + '_a')) || DEFAULT_ASSETS } catch { return DEFAULT_ASSETS }
  })
  const [liabilities, setLiabilities] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY + '_l')) || DEFAULT_LIABILITIES } catch { return DEFAULT_LIABILITIES }
  })
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [] } catch { return [] }
  })

  useEffect(() => { localStorage.setItem(STORAGE_KEY + '_a', JSON.stringify(assets)) }, [assets])
  useEffect(() => { localStorage.setItem(STORAGE_KEY + '_l', JSON.stringify(liabilities)) }, [liabilities])
  useEffect(() => { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)) }, [history])

  const totalAssets = assets.reduce((s, a) => s + (a.value || 0), 0)
  const totalLiabilities = liabilities.reduce((s, l) => s + (l.value || 0), 0)
  const netWorth = totalAssets - totalLiabilities

  const addItem = (type) => {
    const item = { id: Date.now(), category: type === 'asset' ? ASSET_CATS[0] : LIABILITY_CATS[0], name: '', value: 0 }
    type === 'asset' ? setAssets(p => [...p, item]) : setLiabilities(p => [...p, item])
  }
  const removeItem = (type, id) => type === 'asset' ? setAssets(p => p.filter(x => x.id !== id)) : setLiabilities(p => p.filter(x => x.id !== id))
  const updateItem = (type, id, field, value) => {
    const setter = type === 'asset' ? setAssets : setLiabilities
    setter(p => p.map(x => x.id === id ? { ...x, [field]: value } : x))
  }

  const saveSnapshot = () => {
    const snap = { date: new Date().toISOString().slice(0, 10), net_worth: netWorth, assets: totalAssets, liabilities: totalLiabilities }
    setHistory(p => [...p.filter(h => h.date !== snap.date), snap].sort((a, b) => a.date.localeCompare(b.date)))
  }

  // Charts
  const assetsByCat = ASSET_CATS.map(cat => ({ cat, val: assets.filter(a => a.category === cat).reduce((s, a) => s + a.value, 0) })).filter(x => x.val > 0)
  const liabByCat = LIABILITY_CATS.map(cat => ({ cat, val: liabilities.filter(l => l.category === cat).reduce((s, l) => s + l.value, 0) })).filter(x => x.val > 0)

  const pieChart = {
    data: [
      { labels: assetsByCat.map(x => x.cat), values: assetsByCat.map(x => x.val), type: 'pie', name: 'Assets', domain: { column: 0 }, hole: 0.4, marker: { colors: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#06b6d4', '#ec4899'] } },
    ],
    layout: { title: 'Asset Breakdown', height: 260, showlegend: true },
  }

  const histChart = history.length > 1 ? {
    data: [
      { x: history.map(h => h.date), y: history.map(h => h.assets), type: 'scatter', mode: 'lines+markers', name: 'Total Assets', line: { color: '#10b981' } },
      { x: history.map(h => h.date), y: history.map(h => h.liabilities), type: 'scatter', mode: 'lines+markers', name: 'Total Liabilities', line: { color: '#ef4444' } },
      { x: history.map(h => h.date), y: history.map(h => h.net_worth), type: 'scatter', mode: 'lines+markers', name: 'Net Worth', fill: 'tozeroy', fillcolor: 'rgba(59,130,246,0.1)', line: { color: '#3b82f6', width: 3 } },
    ],
    layout: { title: 'Net Worth Over Time', xaxis: { title: 'Date' }, yaxis: { title: 'Amount ($)', tickformat: '$,.0f' }, height: 300 },
  } : null

  const ItemList = ({ type, items, cats }) => (
    <div className="space-y-2">
      {items.map(item => (
        <div key={item.id} className="flex items-center gap-2">
          <select value={item.category} onChange={e => updateItem(type, item.id, 'category', e.target.value)}
            className="input text-xs py-1 w-32 shrink-0">
            {cats.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <input value={item.name} onChange={e => updateItem(type, item.id, 'name', e.target.value)}
            placeholder="Description" className="input text-xs py-1 flex-1 min-w-0" />
          <div className="relative flex items-center shrink-0 w-32">
            <span className="absolute left-2 text-xs text-[var(--text-muted)]">$</span>
            <input type="number" value={item.value} onChange={e => updateItem(type, item.id, 'value', parseFloat(e.target.value) || 0)}
              className="input text-xs py-1 w-full pl-5" />
          </div>
          <button onClick={() => removeItem(type, item.id)} className="text-[var(--text-muted)] hover:text-red-400 shrink-0">
            <Trash2 size={13} />
          </button>
        </div>
      ))}
      <button onClick={() => addItem(type)} className="flex items-center gap-1 text-xs text-[var(--accent)] hover:opacity-80 mt-1">
        <Plus size={12} /> Add {type === 'asset' ? 'Asset' : 'Liability'}
      </button>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Net Worth Tracker</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">Track all your assets and liabilities. Saved locally in your browser.</p>
        </div>
        <button onClick={saveSnapshot} className="btn-primary text-sm px-4 py-2">Save Snapshot</button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center border-l-4 border-green-500">
          <div className="text-xs text-[var(--text-muted)] mb-1">Total Assets</div>
          <div className="text-2xl font-bold text-green-400">${totalAssets.toLocaleString()}</div>
        </div>
        <div className="card p-4 text-center border-l-4 border-red-500">
          <div className="text-xs text-[var(--text-muted)] mb-1">Total Liabilities</div>
          <div className="text-2xl font-bold text-red-400">${totalLiabilities.toLocaleString()}</div>
        </div>
        <div className={`card p-4 text-center border-l-4 ${netWorth >= 0 ? 'border-blue-500' : 'border-orange-500'}`}>
          <div className="text-xs text-[var(--text-muted)] mb-1">Net Worth</div>
          <div className={`text-2xl font-bold ${netWorth >= 0 ? 'text-blue-400' : 'text-orange-400'}`}>${netWorth.toLocaleString()}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Assets */}
        <div className="card p-4 space-y-3">
          <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2 flex justify-between">
            <span>Assets</span>
            <span className="text-green-400">${totalAssets.toLocaleString()}</span>
          </h2>
          <ItemList type="asset" items={assets} cats={ASSET_CATS} />
        </div>

        {/* Liabilities */}
        <div className="card p-4 space-y-3">
          <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2 flex justify-between">
            <span>Liabilities</span>
            <span className="text-red-400">${totalLiabilities.toLocaleString()}</span>
          </h2>
          <ItemList type="liability" items={liabilities} cats={LIABILITY_CATS} />
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {assetsByCat.length > 0 && <div className="card p-4"><PlotlyChart data={pieChart.data} layout={pieChart.layout} /></div>}
        {histChart && <div className="card p-4"><PlotlyChart data={histChart.data} layout={histChart.layout} /></div>}
        {history.length <= 1 && (
          <div className="card p-4 flex items-center justify-center text-center text-[var(--text-muted)]">
            <div>
              <TrendingUp size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Click "Save Snapshot" periodically to build your net worth history chart</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
