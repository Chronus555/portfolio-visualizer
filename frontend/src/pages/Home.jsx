import { Link } from 'react-router-dom'
import {
  TrendingUp, Activity, PieChart, GitBranch, Layers,
  Shield, DollarSign, Leaf, CircleDollarSign, Eye,
  ArrowRight, Zap, Globe, Lock, Infinity,
  BarChart3, Wallet, Calculator, Target,
  Home as HomeIcon, Calendar, ArrowRightLeft, BarChart2, Search, TrendingDown
} from 'lucide-react'

const CORE_TOOLS = [
  { to: '/backtest',     icon: TrendingUp,        title: 'Backtest Portfolio',       desc: 'Compare historical performance with full metrics: CAGR, Sharpe, Sortino, Max Drawdown.', color:'text-blue-500',    bg:'bg-blue-500/10', delay:'stagger-1' },
  { to: '/monte-carlo',  icon: Activity,           title: 'Monte Carlo Simulation',   desc: 'Project long-term growth and survival probability for retirement planning.',              color:'text-violet-500',  bg:'bg-violet-500/10', delay:'stagger-2' },
  { to: '/optimize',     icon: PieChart,           title: 'Portfolio Optimization',   desc: 'Find optimal weights using Mean-Variance, CVaR, Risk Parity, or CDaR. Efficient frontier.', color:'text-emerald-500', bg:'bg-emerald-500/10', delay:'stagger-3' },
  { to: '/factors',      icon: GitBranch,          title: 'Factor Regression',        desc: 'Decompose returns using Fama-French 3/5-factor and Carhart 4-factor models.',            color:'text-orange-500',  bg:'bg-orange-500/10', delay:'stagger-4' },
  { to: '/correlations', icon: Layers,             title: 'Asset Correlations',       desc: 'Analyse correlation matrices, rolling correlations, and principal components.',           color:'text-pink-500',    bg:'bg-pink-500/10', delay:'stagger-5' },
]

const PREMIUM_TOOLS = [
  { to: '/stress-test',  icon: Shield,             title: 'Stress Test',              desc: '8 historical crises: 2008 GFC, dot-com crash, COVID, 1987 Black Monday, and more.', color:'text-red-500',     bg:'bg-red-500/10',    badge:'High Value' },
  { to: '/fee-analyzer', icon: DollarSign,         title: 'Fee Analyzer',             desc: 'See expense ratios in dollar terms. A 1% fee on $500k costs $800k+ over 30 years.', color:'text-amber-500',  bg:'bg-amber-500/10',  badge:'High Value' },
  { to: '/tax-harvest',  icon: Leaf,               title: 'Tax-Loss Harvesting',      desc: 'Scan positions for harvest candidates. Get replacement ETFs to avoid wash-sales.',    color:'text-emerald-500',bg:'bg-emerald-500/10',badge:'High Value' },
  { to: '/dividends',    icon: CircleDollarSign,   title: 'Dividend Analyzer',        desc: 'Yield, growth rate, payout safety score, income history, and 10-year projection.',   color:'text-green-500',  bg:'bg-green-500/10',  badge: null },
  { to: '/watchlist',    icon: Eye,                title: 'Watchlist',                desc: 'Track tickers and jump to any analysis tool instantly. Saved in your browser.',      color:'text-blue-500',   bg:'bg-blue-500/10',   badge: null },
]

const PLANNING_TOOLS = [
  { to: '/retirement',    icon: BarChart3,         title: 'Retirement Planner',   desc: 'Monte Carlo retirement simulation across 1,000 scenarios. Probability of success, percentile bands, sequence-of-returns risk.', color:'text-blue-500',    bg:'bg-blue-500/10',   badge: null },
  { to: '/swr',           icon: Shield,            title: 'Safe Withdrawal Rate', desc: '7 withdrawal strategies: 4% rule, Guyton-Klinger guardrails, floor-ceiling, bucket strategy, RMD-based, and more.', color:'text-purple-500',  bg:'bg-purple-500/10', badge: null },
  { to: '/budget',        icon: Wallet,            title: 'Budget Planner',       desc: '50/30/20 analysis, financial health score (0–100), recommendations, and 30-year wealth projection from your habits.', color:'text-green-500',   bg:'bg-green-500/10',  badge: null },
  { to: '/savings-goals', icon: Target,            title: 'Savings Goals',        desc: 'Track retirement, house, college, emergency fund, and custom goals simultaneously. Contribution sensitivity analysis.', color:'text-orange-500',  bg:'bg-orange-500/10', badge: null },
  { to: '/roth',          icon: ArrowRightLeft,    title: 'Roth Optimizer',       desc: 'Compare Roth vs Traditional IRA after-tax outcomes. Optimize your annual Roth conversion amount using 2024 tax brackets.', color:'text-yellow-500',  bg:'bg-yellow-500/10', badge:'New' },
  { to: '/net-worth',     icon: TrendingDown,      title: 'Net Worth Tracker',    desc: 'Track all assets and liabilities. Categorized breakdown, snapshot history chart, and asset allocation pie. Saved locally.', color:'text-teal-500',    bg:'bg-teal-500/10',   badge:'New' },
]

const CALCULATOR_TOOLS = [
  { to: '/loan',          icon: HomeIcon,          title: 'Loan & Mortgage',      desc: 'Full amortization schedule with extra payments, refinancing break-even, and rent vs buy comparison.', color:'text-rose-500',    bg:'bg-rose-500/10',   badge:'New' },
  { to: '/dca',           icon: Calendar,          title: 'DCA Simulator',        desc: 'Compare dollar-cost averaging against lump sum investing using real historical price data.', color:'text-indigo-500',  bg:'bg-indigo-500/10', badge:'New' },
  { to: '/bond',          icon: BarChart2,         title: 'Bond Calculator',      desc: 'Bond price, YTM, Macaulay/modified duration, convexity, cash flow schedule, and price sensitivity.', color:'text-cyan-500',    bg:'bg-cyan-500/10',   badge:'New' },
  { to: '/xray',          icon: Search,            title: 'Portfolio X-Ray',      desc: 'Deep-dive into your portfolio\'s sector, asset class, and geographic exposure. Powered by live Yahoo Finance data.', color:'text-violet-500',  bg:'bg-violet-500/10', badge:'New' },
]

const FEATURES = [
  { icon: Infinity, label: 'Unlimited Assets',  sub: 'No 15-asset cap',       color: 'text-blue-500' },
  { icon: Globe,    label: 'Full History',       sub: 'Data since 1970s',      color: 'text-emerald-500' },
  { icon: Zap,      label: 'No Paywall',         sub: 'All features free',     color: 'text-violet-500' },
  { icon: Lock,     label: 'Self-Hosted',        sub: 'Your data, your server',color: 'text-orange-500' },
]

function ToolCard({ to, icon: Icon, title, desc, color, bg, delay = '', badge }) {
  return (
    <Link to={to} className={`card-interactive animate-fade-in ${delay} group`}>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${bg}`}>
        <Icon size={21} className={color} />
      </div>
      <div className="flex items-start gap-2 mb-1.5">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex-1
          group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
          {title}
        </h2>
        {badge && (
          <span className="badge badge-blue text-[9px] shrink-0 mt-0.5">{badge}</span>
        )}
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">{desc}</p>
      <div className="mt-4 flex items-center gap-1 text-xs font-semibold
        text-blue-500 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
        Open tool <ArrowRight size={11} />
      </div>
    </Link>
  )
}

export default function Home() {
  return (
    <div className="max-w-5xl mx-auto px-4 pb-16">

      {/* Hero */}
      <div className="text-center pt-12 pb-10 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-6
          bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400
          border border-blue-200 dark:border-blue-800">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          20 Tools · Open Source · Self-Hosted · Unlimited
        </div>
        <h1 className="text-5xl font-extrabold tracking-tight mb-4 leading-tight text-gray-900 dark:text-white">
          Portfolio{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-blue-600 to-violet-600">
            Visualizer
          </span>
        </h1>
        <p className="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed mb-8">
          Institutional-grade portfolio analysis and financial planning — backtest, simulate, optimise,
          stress-test, plan retirement, budget, and track goals. No limits, no paywalls.
        </p>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link to="/backtest"    className="btn-primary flex items-center gap-2 px-6 py-2.5 text-sm">Start Backtesting <ArrowRight size={15} /></Link>
          <Link to="/stress-test" className="btn-secondary flex items-center gap-2 px-5 py-2.5 text-sm"><Shield size={14} /> Stress Test</Link>
          <Link to="/fee-analyzer"className="btn-secondary flex items-center gap-2 px-5 py-2.5 text-sm"><DollarSign size={14} /> Fee Analyzer</Link>
        </div>
      </div>

      {/* Core Tools */}
      <div className="mb-6">
        <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-gray-600 mb-3">Core Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {CORE_TOOLS.map(t => <ToolCard key={t.to} {...t} />)}
        </div>
      </div>

      {/* Premium Tools */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-gray-600">Advanced Tools</h2>
          <span className="badge badge-blue text-[9px]">Rivals charge $300–$500/mo for these</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {PREMIUM_TOOLS.map(t => <ToolCard key={t.to} {...t} />)}
        </div>
      </div>

      {/* Financial Planning Suite */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-gray-600">Financial Planning Suite</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {PLANNING_TOOLS.map(t => <ToolCard key={t.to} {...t} />)}
        </div>
      </div>

      {/* Calculators */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-gray-600">Calculators</h2>
          <span className="badge badge-green text-[9px]">New</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-3">
          {CALCULATOR_TOOLS.map(t => <ToolCard key={t.to} {...t} />)}
        </div>
      </div>

      {/* Feature strip */}
      <div className="border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden
        bg-white dark:bg-gray-900/50 animate-fade-in">
        <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-gray-200 dark:divide-gray-800">
          {FEATURES.map(({ icon: Icon, label, sub, color }) => (
            <div key={label} className="flex items-center gap-3 px-6 py-5
              hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
              <div className={`shrink-0 ${color}`}><Icon size={20} /></div>
              <div>
                <div className="font-semibold text-sm text-gray-900 dark:text-gray-100">{label}</div>
                <div className="text-xs text-gray-500 dark:text-gray-500 mt-0.5">{sub}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
