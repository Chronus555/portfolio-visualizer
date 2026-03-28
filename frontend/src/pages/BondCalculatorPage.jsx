import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { BarChart2 } from 'lucide-react'

const DEFAULTS = {
  face: 1000,
  coupon_rate: 0.05,
  years: 10,
  price: null,
  ytm: 0.06,
  freq: 2,
  inflation: 2.5,
  solve_for: 'price',
}

export default function BondCalculatorPage() {
  const [form, setForm] = useState(DEFAULTS)
  const num = (k, e) => setForm(p => ({ ...p, [k]: parseFloat(e.target.value) || 0 }))

  const mutation = useMutation({
    mutationFn: () => {
      const payload = {
        face: form.face,
        coupon_rate: form.coupon_rate,
        years: form.years,
        freq: form.freq,
        inflation: form.inflation,
        price: form.solve_for === 'ytm' ? form.price : null,
        ytm: form.solve_for === 'price' ? form.ytm : null,
      }
      return api.post('/bond/analyze', payload).then(r => r.data)
    },
  })

  const d = mutation.data

  // Cash flow chart
  const cfChart = d ? {
    data: [
      { x: d.schedule.map(r => r.year), y: d.schedule.map(r => r.pv), type: 'bar', name: 'Present Value of Cash Flow', marker: { color: '#3b82f6' }, hovertemplate: 'Year %{x}: $%{y:,.2f}<extra></extra>' },
      { x: d.schedule.map(r => r.year), y: d.schedule.map(r => r.cash_flow), type: 'scatter', mode: 'markers', name: 'Nominal Cash Flow', marker: { color: '#10b981', size: 8 }, hovertemplate: 'Year %{x}: $%{y:,.2f}<extra></extra>' },
    ],
    layout: { title: 'Cash Flow Schedule — Nominal vs Present Value', xaxis: { title: 'Year' }, yaxis: { title: 'Cash Flow ($)', tickformat: '$,.0f' }, height: 300 },
  } : null

  // Price sensitivity
  const sensChart = d ? {
    data: [{
      x: [-3, -2, -1, 0, 1, 2, 3],
      y: [-3, -2, -1, 0, 1, 2, 3].map(delta => {
        const newYtm = Math.max(0.001, d.ytm_pct / 100 + delta / 100)
        const r = newYtm / form.freq
        const n = form.years * form.freq
        const c = form.face * form.coupon_rate / form.freq
        const p = r > 0 ? c * (1 - (1 + r) ** -n) / r + form.face / (1 + r) ** n : c * n + form.face
        return round2(p)
      }),
      type: 'scatter', mode: 'lines+markers',
      line: { color: '#3b82f6', width: 2 },
      hovertemplate: 'Rate \u0394 %{x}%: Price $%{y:,.2f}<extra></extra>',
    }],
    layout: { title: 'Price Sensitivity to Rate Changes', xaxis: { title: 'Interest Rate Change (%)' }, yaxis: { title: 'Bond Price ($)', tickformat: '$,.2f' }, height: 260 },
  } : null

  function round2(n) { return Math.round(n * 100) / 100 }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Bond Calculator</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Calculate bond price, yield to maturity, Macaulay/modified duration, convexity, and cash flow schedule.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Bond Parameters</h2>
            {[
              { label: 'Face Value', key: 'face', prefix: '$' },
              { label: 'Annual Coupon Rate', key: 'coupon_rate', suffix: '(e.g. 0.05 = 5%)', step: 0.005 },
              { label: 'Years to Maturity', key: 'years', suffix: 'yr' },
              { label: 'Inflation Rate', key: 'inflation', suffix: '%', step: 0.1 },
            ].map(f => (
              <div key={f.key}>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">{f.label} {f.suffix && <span className="font-normal">({f.suffix})</span>}</label>
                <div className="relative flex items-center">
                  {f.prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{f.prefix}</span>}
                  <input type="number" value={form[f.key]} onChange={e => num(f.key, e)}
                    step={f.step || 1} className={`input w-full text-sm ${f.prefix ? 'pl-7' : ''}`} />
                </div>
              </div>
            ))}
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">Coupon Frequency</label>
              <select value={form.freq} onChange={e => setForm(p => ({ ...p, freq: parseInt(e.target.value) }))} className="input w-full text-sm">
                <option value={1}>Annual</option>
                <option value={2}>Semi-Annual</option>
                <option value={4}>Quarterly</option>
              </select>
            </div>
          </div>

          <div className="card p-4 space-y-3">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Solve For</h2>
            <div className="flex gap-2">
              {[{ id: 'price', label: 'Price (given YTM)' }, { id: 'ytm', label: 'YTM (given Price)' }].map(opt => (
                <button key={opt.id} onClick={() => setForm(p => ({ ...p, solve_for: opt.id }))}
                  className={`flex-1 text-xs py-2 rounded-md font-medium transition-colors ${form.solve_for === opt.id ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-muted)] border border-[var(--border)]'}`}>
                  {opt.label}
                </button>
              ))}
            </div>
            {form.solve_for === 'price' ? (
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">YTM (e.g. 0.06 = 6%)</label>
                <input type="number" value={form.ytm} onChange={e => num('ytm', e)} step={0.005} className="input w-full text-sm" />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">Market Price ($)</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[var(--text-muted)]">$</span>
                  <input type="number" value={form.price || ''} onChange={e => setForm(p => ({ ...p, price: parseFloat(e.target.value) || null }))} step={0.01} className="input w-full text-sm pl-7" />
                </div>
              </div>
            )}
          </div>

          <button onClick={() => mutation.mutate()} disabled={mutation.isPending}
            className="btn-primary w-full py-3 font-semibold">
            {mutation.isPending ? 'Calculating…' : 'Calculate Bond'}
          </button>
          {mutation.isError && <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3">{String(mutation.error)}</div>}
        </div>

        <div className="lg:col-span-2 space-y-5">
          {!d && !mutation.isPending && (
            <div className="empty-state">
              <BarChart2 size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Enter bond parameters to calculate price, yield, and duration</p>
            </div>
          )}
          {mutation.isPending && <div className="empty-state"><div className="spinner mx-auto mb-3" /><p>Calculating…</p></div>}

          {d && (
            <>
              <div className={`card p-3 text-center ${d.status === 'Premium' ? 'border-l-4 border-orange-500' : d.status === 'Discount' ? 'border-l-4 border-green-500' : 'border-l-4 border-blue-500'}`}>
                <span className="text-xs text-[var(--text-muted)]">Trading at </span>
                <span className={`font-bold ${d.status === 'Premium' ? 'text-orange-400' : d.status === 'Discount' ? 'text-green-400' : 'text-blue-400'}`}>{d.status}</span>
                <span className="text-xs text-[var(--text-muted)] ml-2">(${d.premium_discount > 0 ? '+' : ''}{d.premium_discount.toFixed(2)} vs par)</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Price', value: `$${d.price.toFixed(2)}` },
                  { label: 'YTM', value: `${d.ytm_pct.toFixed(3)}%`, color: 'text-blue-400' },
                  { label: 'Current Yield', value: `${d.current_yield_pct.toFixed(3)}%` },
                  { label: 'Real Yield', value: `${d.real_yield_pct.toFixed(3)}%`, color: d.real_yield_pct > 0 ? 'text-green-400' : 'text-red-400' },
                  { label: 'Macaulay Duration', value: `${d.macaulay_duration.toFixed(3)}yr` },
                  { label: 'Modified Duration', value: `${d.modified_duration.toFixed(3)}` },
                  { label: 'Price +1%', value: `$${d.price_if_rates_rise_1pct.toFixed(2)}`, color: 'text-red-400' },
                  { label: 'Price -1%', value: `$${d.price_if_rates_fall_1pct.toFixed(2)}`, color: 'text-green-400' },
                ].map(m => (
                  <div key={m.label} className="card p-3 text-center">
                    <div className="text-xs text-[var(--text-muted)] mb-1">{m.label}</div>
                    <div className={`font-bold text-sm ${m.color || ''}`}>{m.value}</div>
                  </div>
                ))}
              </div>

              {cfChart && <div className="card p-4"><PlotlyChart data={cfChart.data} layout={cfChart.layout} /></div>}
              {sensChart && <div className="card p-4"><PlotlyChart data={sensChart.data} layout={sensChart.layout} /></div>}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
