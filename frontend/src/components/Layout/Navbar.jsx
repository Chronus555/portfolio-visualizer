import { NavLink } from 'react-router-dom'
import { TrendingUp, Sun, Moon, ChevronDown } from 'lucide-react'
import clsx from 'clsx'
import { useEffect, useState, useRef } from 'react'

const NAV_LINKS = [
  { to: '/backtest',     label: 'Backtest' },
  { to: '/monte-carlo',  label: 'Monte Carlo' },
  { to: '/optimize',     label: 'Optimization' },
  { to: '/factors',      label: 'Factor Regression' },
  { to: '/correlations', label: 'Correlations' },
]

const TOOLS_DROPDOWN = [
  { to: '/stress-test',   label: 'Stress Test',         desc: 'Historical crisis scenarios',   badge: null },
  { to: '/fee-analyzer',  label: 'Fee Analyzer',         desc: 'True cost of expense ratios',   badge: null },
  { to: '/tax-harvest',   label: 'Tax-Loss Harvesting',  desc: 'Find harvest opportunities',    badge: null },
  { to: '/dividends',     label: 'Dividend Analyzer',    desc: 'Income & yield analysis',        badge: null },
  { to: '/watchlist',     label: 'Watchlist',            desc: 'Track your tickers',             badge: null },
  { to: '/dca',           label: 'DCA Simulator',        desc: 'DCA vs lump sum backtest',       badge: 'New' },
  { to: '/xray',          label: 'Portfolio X-Ray',      desc: 'Sector & asset breakdown',       badge: 'New' },
]

const PLANNING_DROPDOWN = [
  { to: '/retirement',    label: 'Retirement Planner',   desc: 'Monte Carlo retirement sim',    badge: null },
  { to: '/swr',           label: 'Safe Withdrawal Rate', desc: '7 withdrawal strategies',        badge: null },
  { to: '/budget',        label: 'Budget Planner',       desc: '50/30/20 + health score',        badge: null },
  { to: '/savings-goals', label: 'Savings Goals',        desc: 'Multi-goal projection',          badge: null },
  { to: '/roth',          label: 'Roth Optimizer',       desc: 'Roth vs Traditional + convert',  badge: 'New' },
  { to: '/net-worth',     label: 'Net Worth Tracker',    desc: 'Assets & liabilities tracker',   badge: 'New' },
]

const CALCULATORS_DROPDOWN = [
  { to: '/loan',          label: 'Loan & Mortgage',      desc: 'Amortization + rent vs buy',    badge: 'New' },
  { to: '/bond',          label: 'Bond Calculator',      desc: 'Price, YTM, duration, convexity',badge: 'New' },
]

function Dropdown({ label, badge, items, isOpen, onToggle, onClose, dropRef }) {
  return (
    <div className="relative" ref={dropRef}>
      <button
        onClick={onToggle}
        className={clsx(
          'flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[13px] whitespace-nowrap transition-all duration-150 font-medium',
          isOpen
            ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50'
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800'
        )}>
        {label}
        {badge && <span className="badge badge-green text-[9px] px-1 py-0">{badge}</span>}
        <ChevronDown size={12} className={clsx('transition-transform', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 rounded-xl border shadow-lg overflow-hidden z-50
          bg-white dark:bg-[#161b22] border-gray-200 dark:border-gray-700 animate-fade-scale">
          {items.map(({ to, label: itemLabel, desc, badge: itemBadge }) => (
            <NavLink key={to} to={to}
              onClick={onClose}
              className={({ isActive }) => clsx(
                'flex items-start gap-3 px-4 py-3 transition-colors group',
                isActive ? 'bg-blue-50 dark:bg-blue-950/40' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
              )}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-800 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {itemLabel}
                  </span>
                  {itemBadge && <span className="badge badge-blue text-[9px] px-1.5 py-0.5">{itemBadge}</span>}
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">{desc}</span>
              </div>
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Navbar() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' ||
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    }
    return false
  })
  const [scrolled, setScrolled] = useState(false)
  const [openMenu, setOpenMenu] = useState(null) // 'tools' | 'planning' | 'calculators' | null
  const toolsRef = useRef(null)
  const planRef = useRef(null)
  const calcRef = useRef(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const handler = (e) => {
      if (
        toolsRef.current && !toolsRef.current.contains(e.target) &&
        planRef.current && !planRef.current.contains(e.target) &&
        calcRef.current && !calcRef.current.contains(e.target)
      ) setOpenMenu(null)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <header className={clsx(
      'sticky top-0 z-50 transition-all duration-300',
      scrolled
        ? 'shadow-md backdrop-blur-md bg-white/90 dark:bg-[#161b22]/90 border-b border-gray-200 dark:border-gray-700'
        : 'bg-white dark:bg-[#161b22] border-b border-gray-200 dark:border-gray-800'
    )}>
      <div className="max-w-screen-xl mx-auto px-4 flex items-center h-14 gap-4">

        {/* Logo */}
        <NavLink to="/" className="flex items-center gap-2 shrink-0 group">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm group-hover:bg-blue-500 transition-colors">
            <TrendingUp size={14} className="text-white" />
          </div>
          <span className="font-bold text-[14px] text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            Portfolio Visualizer
          </span>
        </NavLink>

        <div className="h-5 w-px bg-gray-200 dark:bg-gray-700 shrink-0" />

        {/* Nav */}
        <nav className="flex items-center gap-0.5 overflow-x-auto flex-1 hide-scrollbar">
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) => clsx(
                'px-2.5 py-1.5 rounded-md text-[13px] whitespace-nowrap transition-all duration-150 relative',
                isActive
                  ? 'font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50'
                  : 'font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800'
              )}>
              {({ isActive }) => (
                <>
                  {label}
                  {isActive && <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-blue-500 rounded-full" />}
                </>
              )}
            </NavLink>
          ))}

          <Dropdown label="Tools" items={TOOLS_DROPDOWN} isOpen={openMenu === 'tools'}
            onToggle={() => setOpenMenu(o => o === 'tools' ? null : 'tools')}
            onClose={() => setOpenMenu(null)} dropRef={toolsRef} />

          <Dropdown label="Planning" items={PLANNING_DROPDOWN} isOpen={openMenu === 'planning'}
            onToggle={() => setOpenMenu(o => o === 'planning' ? null : 'planning')}
            onClose={() => setOpenMenu(null)} dropRef={planRef} />

          <Dropdown label="Calculators" badge="New" items={CALCULATORS_DROPDOWN} isOpen={openMenu === 'calculators'}
            onToggle={() => setOpenMenu(o => o === 'calculators' ? null : 'calculators')}
            onClose={() => setOpenMenu(null)} dropRef={calcRef} />
        </nav>

        {/* Dark mode toggle */}
        <button
          onClick={() => setDark(d => !d)}
          className="w-8 h-8 rounded-md flex items-center justify-center transition-all duration-150
            text-gray-500 dark:text-gray-400
            hover:bg-gray-100 dark:hover:bg-gray-800
            hover:text-gray-900 dark:hover:text-gray-100 shrink-0"
          aria-label="Toggle dark mode">
          {dark ? <Sun size={15} /> : <Moon size={15} />}
        </button>
      </div>
    </header>
  )
}
