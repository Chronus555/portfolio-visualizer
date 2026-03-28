import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import PlotlyChart from '../components/common/PlotlyChart'
import { TrendingUp, ShieldCheck, AlertTriangle, Info } from 'lucide-react'

const DEFAULT_INPUTS = {
  current_age: 35,
  retirement_age: 65,
  life_expectancy: 90,
  current_savings: 150000,
  annual_contribution: 24000,
  contribution_growth: 2,
  expected_return: 7,
  volatility: 15,
  inflation: 3,
  annual_expenses_in_retirement: 80000,
  social_security: 18000,
  simulations: 1000,
}

function InputField({ label, name, value, onChange, prefix, suffix, min, max, step = 1, tip }) {
  return (
    <div>
      <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
        {label}
        {tip && <span className="ml-1 text-[var(--text-muted)] cursor-help" title={tip}>ⓘ</span>}
      </label>
      <div className="relative flex items-center">
        {prefix && <span className="absolute left-3 text-sm text-[var(--text-muted)]">{prefix}</span>}
        <input
          type="number"
          name={name}
          value={value}
          onChange={onChange}
          min={min} max={max} step={step}
          className={`input w-full text-sm ${prefix ? 'pl-7' : ''} ${suffix ? 'pr-10' : ''}`}
        />
        {suffix && <span className="absolute right-3 text-sm text-[var(--text-muted)]">{suffix}</span>}
      </div>
    </div>
  )
}

function MetricCard({ label, value, sub, color = 'blue', icon: Icon }) {
  const colors = {
    blue:   'border-blue-500/30 bg-blue-500/5 text-blue-400',
    green:  'border-green-500/30 bg-green-500/5 text-green-400',
    yellow: 'border-yellow-500/30 bg-yellow-500/5 text-yellow-400',
    red:    'border-red-500/30 bg-red-500/5 text-red-400',
  }
  return (
    <div className={`card border-l-4 ${colors[color]} p-4`}>
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={16} className="opacity-60" />}
        <span className="text-xs text-[var(--text-muted)]">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {sub && <div className="text-xs text-[var(--text-muted)] mt-0.5">{sub}</div>}
    </div>
  )
}

export default function RetirementPlannerPage() {
  const [inputs, setInputs] = useState(DEFAULT_INPUTS)

  const mutation = useMutation({
    mutationFn: () => api.post('/retirement/plan', inputs).then(r => r.data),
    mutationKey: ['retirement'],
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setInputs(p => ({ ...p, [name]: parseFloat(value) || 0 }))
  }

  const data = mutation.data
  const summary = data?.summary
  const probColor = !summary ? 'blue'
    : summary.probability_of_success >= 80 ? 'green'
    : summary.probability_of_success >= 60 ? 'yellow'
    : 'red'

  // ── Charts ──────────────────────────────────────────────────────────────
  const accumChart = data ? {
    data: [{
      x: data.accumulation_path.map(p => p.age),
      y: data.accumulation_path.map(p => p.balance),
      type: 'scatter', mode: 'lines', fill: 'tozeroy',
      fillcolor: 'rgba(59,130,246,0.15)',
      line: { color: '#3b82f6', width: 2 },
      name: 'Projected Balance',
      hovertemplate: 'Age %{x}: $%{y:,.0f}<extra></extra>',
    }],
    layout: {
      title: 'Accumulation Phase',
      xaxis: { title: 'Age' },
      yaxis: { title: 'Portfolio Value ($)', tickformat: '$,.0f' },
      height: 260,
    },
  } : null

  const wdChart = data ? (() => {
    const wc = data.withdrawal_chart
    return {
      data: [
        { x: wc.ages, y: wc.p90, type: 'scatter', mode: 'lines', line: { color: 'transparent' }, showlegend: false, hoverinfo: 'skip' },
        { x: wc.ages, y: wc.p10, type: 'scatter', mode: 'lines', fill: 'tonexty', fillcolor: 'rgba(59,130,246,0.1)', line: { color: 'transparent' }, name: '10th–90th %ile', showlegend: true },
        { x: wc.ages, y: wc.p25, type: 'scatter', mode: 'lines', line: { color: 'transparent' }, showlegend: false, hoverinfo: 'skip' },
        { x: wc.ages, y: wc.p75, type: 'scatter', mode: 'lines', fill: 'tonexty', fillcolor: 'rgba(59,130,246,0.15)', line: { color: 'transparent' }, name: '25th–75th %ile', showlegend: true },
        { x: wc.ages, y: wc.p50, type: 'scatter', mode: 'lines', line: { color: '#3b82f6', width: 2 }, name: 'Median', hovertemplate: 'Age %{x}: $%{y:,.0f}<extra></extra>' },
      ],
      layout: {
        title: 'Withdrawal Phase — Monte Carlo Bands',
        xaxis: { title: 'Age' },
        yaxis: { title: 'Portfolio Value ($)', tickformat: '$,.0f' },
        height: 280,
      },
    }
  })() : null

  const sorChart = data ? {
    data: [
      { x: data.sequence_of_returns.ages, y: data.sequence_of_returns.median,    type: 'scatter', mode: 'lines', name: 'Median Returns', line: { color: '#3b82f6', width: 2, dash: 'dash' } },
      { x: data.sequence_of_returns.ages, y: data.sequence_of_returns.bad_early,  type: 'scatter', mode: 'lines', name: 'Bad Returns Early', line: { color: '#ef4444', width: 2 } },
      { x: data.sequence_of_returns.ages, y: data.sequence_of_returns.bad_late,   type: 'scatter', mode: 'lines', name: 'Bad Returns Late',  line: { color: '#f59e0b', width: 2 } },
    ],
    layout: {
      title: 'Sequence of Returns Risk',
      xaxis: { title: 'Age' },
      yaxis: { title: 'Portfolio Value ($)', tickformat: '$,.0f' },
      height: 260,
    },
  } : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Retirement Planner</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          Monte Carlo simulation across {inputs.simulations.toLocaleString()} market scenarios — know your real probability of success.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Left: Inputs ─────────────────────────────────────────────── */}
        <div className="space-y-4">
          <div className="card p-4 space-y-4">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Your Profile</h2>
            <div className="grid grid-cols-2 gap-3">
              <InputField label="Current Age"    name="current_age"    value={inputs.current_age}    onChange={handleChange} min={18} max={80} />
              <InputField label="Retirement Age" name="retirement_age" value={inputs.retirement_age} onChange={handleChange} min={30} max={90} />
              <InputField label="Life Expectancy" name="life_expectancy" value={inputs.life_expectancy} onChange={handleChange} min={60} max={110} />
              <InputField label="Simulations"    name="simulations"    value={inputs.simulations}    onChange={handleChange} min={100} max={10000} step={100} tip="More = more accurate but slower" />
            </div>
          </div>

          <div className="card p-4 space-y-4">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Savings & Contributions</h2>
            <div className="grid grid-cols-1 gap-3">
              <InputField label="Current Savings"       name="current_savings"       value={inputs.current_savings}       onChange={handleChange} prefix="$" min={0} />
              <InputField label="Annual Contribution"   name="annual_contribution"   value={inputs.annual_contribution}   onChange={handleChange} prefix="$" min={0} />
              <InputField label="Contribution Growth/yr" name="contribution_growth"  value={inputs.contribution_growth}   onChange={handleChange} suffix="%" min={0} max={10} step={0.5} tip="How much your contributions grow each year (annual raise)" />
            </div>
          </div>

          <div className="card p-4 space-y-4">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Retirement Spending</h2>
            <div className="grid grid-cols-1 gap-3">
              <InputField label="Annual Expenses in Retirement" name="annual_expenses_in_retirement" value={inputs.annual_expenses_in_retirement} onChange={handleChange} prefix="$" min={0} />
              <InputField label="Social Security (annual)"      name="social_security"               value={inputs.social_security}               onChange={handleChange} prefix="$" min={0} tip="Annual SS benefit at retirement (in today's dollars)" />
            </div>
          </div>

          <div className="card p-4 space-y-4">
            <h2 className="font-semibold text-sm border-b border-[var(--border)] pb-2">Market Assumptions</h2>
            <div className="grid grid-cols-2 gap-3">
              <InputField label="Expected Return"  name="expected_return" value={inputs.expected_return} onChange={handleChange} suffix="%" min={0} max={30} step={0.5} />
              <InputField label="Volatility (σ)"   name="volatility"      value={inputs.volatility}      onChange={handleChange} suffix="%" min={1} max={50} step={0.5} />
              <InputField label="Inflation"        name="inflation"       value={inputs.inflation}       onChange={handleChange} suffix="%" min={0} max={15} step={0.1} />
            </div>
          </div>

          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="btn-primary w-full py-3 font-semibold"
          >
            {mutation.isPending ? 'Running Monte Carlo…' : 'Run Retirement Plan'}
          </button>
          {mutation.isError && (
            <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-3">
              {String(mutation.error)}
            </div>
          )}
        </div>

        {/* ── Right: Results ───────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          {!data && !mutation.isPending && (
            <div className="empty-state">
              <TrendingUp size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Configure your retirement plan</p>
              <p className="text-sm mt-1">Set your details on the left and click Run Retirement Plan</p>
            </div>
          )}
          {mutation.isPending && (
            <div className="empty-state">
              <div className="spinner mx-auto mb-3" />
              <p>Running {inputs.simulations.toLocaleString()} Monte Carlo simulations…</p>
            </div>
          )}

          {data && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <MetricCard
                  label="Probability of Success"
                  value={`${summary.probability_of_success}%`}
                  sub={summary.probability_of_success >= 80 ? 'Excellent' : summary.probability_of_success >= 60 ? 'Fair' : 'At Risk'}
                  color={probColor}
                  icon={ShieldCheck}
                />
                <MetricCard
                  label="Median Nest Egg"
                  value={`$${(summary.median_retirement_balance / 1e6).toFixed(2)}M`}
                  sub={`Target: $${(summary.target_nest_egg / 1e6).toFixed(2)}M`}
                  color="blue"
                  icon={TrendingUp}
                />
                <MetricCard
                  label="On-Track"
                  value={`${summary.on_track_pct}%`}
                  sub="of target nest egg"
                  color={summary.on_track_pct >= 100 ? 'green' : summary.on_track_pct >= 75 ? 'yellow' : 'red'}
                />
                <MetricCard
                  label="Years to Retire"
                  value={summary.years_to_retirement}
                  sub={`${summary.withdrawal_years} years in retirement`}
                  color="blue"
                />
              </div>

              {/* Percentile bands */}
              <div className="card p-4">
                <h3 className="font-semibold text-sm mb-3">Retirement Balance Range ({data.inputs.simulations.toLocaleString()} simulations)</h3>
                <div className="grid grid-cols-5 gap-2 text-center">
                  {Object.entries(data.retirement_balance_percentiles).map(([k, v]) => (
                    <div key={k} className="panel p-2">
                      <div className="text-xs text-[var(--text-muted)] mb-1">{k.toUpperCase()}</div>
                      <div className="font-bold text-sm">${(v/1e6).toFixed(2)}M</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Charts */}
              {accumChart  && <div className="card p-4"><PlotlyChart data={accumChart.data}  layout={accumChart.layout}  /></div>}
              {wdChart     && <div className="card p-4"><PlotlyChart data={wdChart.data}     layout={wdChart.layout}     /></div>}
              {sorChart    && (
                <div className="card p-4">
                  <PlotlyChart data={sorChart.data} layout={sorChart.layout} />
                  <p className="text-xs text-[var(--text-muted)] mt-2 flex items-start gap-1.5">
                    <Info size={12} className="mt-0.5 shrink-0" />
                    Sequence of returns risk: two portfolios with identical average returns but different timing — crashes early in retirement are far more damaging than late-retirement crashes.
                  </p>
                </div>
              )}

              {/* Contribution summary */}
              <div className="card p-4">
                <h3 className="font-semibold text-sm mb-3">Where Does the Money Come From?</h3>
                <div className="space-y-2">
                  {[
                    { label: 'Starting Savings', value: data.inputs.current_savings, color: '#3b82f6' },
                    { label: 'Your Contributions', value: summary.total_contributions_est, color: '#10b981' },
                    { label: 'Investment Growth', value: summary.investment_growth_est, color: '#f59e0b' },
                  ].map(item => {
                    const total = data.inputs.current_savings + summary.total_contributions_est + summary.investment_growth_est
                    const pct = total > 0 ? item.value / total * 100 : 0
                    return (
                      <div key={item.label}>
                        <div className="flex justify-between text-xs mb-1">
                          <span>{item.label}</span>
                          <span className="font-medium">${item.value.toLocaleString(undefined, {maximumFractionDigits: 0})} ({pct.toFixed(0)}%)</span>
                        </div>
                        <div className="h-2 bg-[var(--bg)] rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700"
                               style={{ width: `${pct}%`, background: item.color }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
