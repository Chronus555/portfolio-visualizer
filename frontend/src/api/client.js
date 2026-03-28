import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(msg))
  }
)

// ── Core ───────────────────────────────────────────────────────────────────────
export const backtestPortfolio  = (p) => api.post('/backtest/portfolio', p).then(r => r.data)
export const runMonteCarlo      = (p) => api.post('/monte-carlo/simulate', p).then(r => r.data)
export const optimizePortfolio  = (p) => api.post('/optimize/portfolio', p).then(r => r.data)
export const runFactorRegression= (p) => api.post('/factors/regression', p).then(r => r.data)
export const analyzeCorrelations= (p) => api.post('/correlations/analyze', p).then(r => r.data)
export const validateTicker     = (t) => api.get(`/funds/validate?ticker=${t}`).then(r => r.data)
export const searchTicker       = (q) => api.get(`/funds/search?q=${q}`).then(r => r.data)
export const screenFunds        = (p) => api.post('/funds/screener', p).then(r => r.data)

// ── Stress Test ────────────────────────────────────────────────────────────────
export const getScenarios  = ()  => api.get('/stress-test/scenarios').then(r => r.data)
export const runStressTest = (p) => api.post('/stress-test/run', p).then(r => r.data)

// ── Fee Analyzer ───────────────────────────────────────────────────────────────
export const analyzeFees           = (p) => api.post('/fees/analyze', p).then(r => r.data)
export const lookupExpenseRatios   = (t) => api.post('/fees/lookup', t).then(r => r.data)

// ── Tax Harvest ────────────────────────────────────────────────────────────────
export const scanTaxHarvest = (p) => api.post('/tax/harvest-scan', p).then(r => r.data)

// ── Dividend ───────────────────────────────────────────────────────────────────
export const analyzeDividends = (p) => api.post('/dividend/analyze', p).then(r => r.data)

// ── Retirement Planner ─────────────────────────────────────────────────────────
export const planRetirement   = (p) => api.post('/retirement/plan', p).then(r => r.data)

// ── Safe Withdrawal Rate ───────────────────────────────────────────────────────
export const getSWRStrategies = ()  => api.get('/swr/strategies').then(r => r.data)
export const analyzeSWR       = (p) => api.post('/swr/analyze', p).then(r => r.data)

// ── Budget Planner ─────────────────────────────────────────────────────────────
export const analyzeBudget = (p) => api.post('/budget/analyze', p).then(r => r.data)

// ── Savings Goals ──────────────────────────────────────────────────────────────
export const projectGoals = (p) => api.post('/savings/goals', p).then(r => r.data)

// ── PDF Reports ────────────────────────────────────────────────────────────────
export const downloadBacktestPDF = async (data) => {
  const res = await api.post('/report/backtest', { data }, { responseType: 'blob' })
  const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
  const a = document.createElement('a')
  a.href = url; a.download = 'backtest_report.pdf'; a.click()
  URL.revokeObjectURL(url)
}
