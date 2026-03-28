import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Layout/Navbar'
import Home from './pages/Home'
import BacktestPage from './pages/BacktestPage'
import MonteCarloPage from './pages/MonteCarloPage'
import OptimizationPage from './pages/OptimizationPage'
import FactorRegressionPage from './pages/FactorRegressionPage'
import CorrelationsPage from './pages/CorrelationsPage'
import StressTestPage from './pages/StressTestPage'
import FeeAnalyzerPage from './pages/FeeAnalyzerPage'
import TaxHarvestPage from './pages/TaxHarvestPage'
import DividendPage from './pages/DividendPage'
import WatchlistPage from './pages/WatchlistPage'
import RetirementPlannerPage from './pages/RetirementPlannerPage'
import SWRPage from './pages/SWRPage'
import BudgetPlannerPage from './pages/BudgetPlannerPage'
import SavingsGoalPage from './pages/SavingsGoalPage'
import LoanCalculatorPage from './pages/LoanCalculatorPage'
import DCASimulatorPage from './pages/DCASimulatorPage'
import RothOptimizerPage from './pages/RothOptimizerPage'
import NetWorthPage from './pages/NetWorthPage'
import BondCalculatorPage from './pages/BondCalculatorPage'
import PortfolioXRayPage from './pages/PortfolioXRayPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-[var(--bg)]">
        <Navbar />
        <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-6">
          <Routes>
            <Route path="/"             element={<Home />} />
            <Route path="/backtest"     element={<BacktestPage />} />
            <Route path="/monte-carlo"  element={<MonteCarloPage />} />
            <Route path="/optimize"     element={<OptimizationPage />} />
            <Route path="/factors"      element={<FactorRegressionPage />} />
            <Route path="/correlations" element={<CorrelationsPage />} />
            <Route path="/stress-test"  element={<StressTestPage />} />
            <Route path="/fee-analyzer" element={<FeeAnalyzerPage />} />
            <Route path="/tax-harvest"  element={<TaxHarvestPage />} />
            <Route path="/dividends"    element={<DividendPage />} />
            <Route path="/watchlist"     element={<WatchlistPage />} />
            <Route path="/retirement"    element={<RetirementPlannerPage />} />
            <Route path="/swr"           element={<SWRPage />} />
            <Route path="/budget"        element={<BudgetPlannerPage />} />
            <Route path="/savings-goals" element={<SavingsGoalPage />} />
            <Route path="/loan"          element={<LoanCalculatorPage />} />
            <Route path="/dca"           element={<DCASimulatorPage />} />
            <Route path="/roth"          element={<RothOptimizerPage />} />
            <Route path="/net-worth"     element={<NetWorthPage />} />
            <Route path="/bond"          element={<BondCalculatorPage />} />
            <Route path="/xray"          element={<PortfolioXRayPage />} />
            <Route path="*"              element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="text-center text-xs py-4 border-t
          text-gray-400 dark:text-gray-600
          border-gray-200 dark:border-gray-800
          bg-white dark:bg-[#161b22]">
          Portfolio Visualizer — Open Source Portfolio Analysis Tool
        </footer>
      </div>
    </BrowserRouter>
  )
}
