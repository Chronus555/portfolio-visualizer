# Portfolio Visualizer — Open Source

Self-hosted, unlimited portfolio analysis platform. Replicates and extends the functionality of Portfolio Visualizer with no asset limits, full history, and no paywall.

## Features

| Tool | Description |
|---|---|
| **Backtest Portfolio** | Compare multiple portfolios with real ETF/stock data. Full metrics: CAGR, Sharpe, Sortino, Max Drawdown, rolling returns, annual returns heatmap |
| **Monte Carlo Simulation** | Project long-term growth with historical, statistical, or parameterized return models. Fan charts, percentile bands, survival rates |
| **Portfolio Optimization** | Efficient frontier, Max Sharpe, Min Volatility, CVaR, CDaR, Risk Parity, Black-Litterman |
| **Factor Regression** | Fama-French 3-factor, 5-factor, Carhart 4-factor. Alpha, beta, t-stats, R², factor contributions |
| **Asset Correlations** | Pearson/Spearman/Kendall correlation matrices, rolling correlations, PCA |

## Quick Start (Docker)

```bash
git clone <your-repo>
cd portfolio-visualizer
docker-compose up --build
```

- Frontend: http://localhost
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
# API proxied to http://localhost:8000
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, yfinance, pandas, numpy, scipy, PyPortfolioOpt, statsmodels, scikit-learn
- **Frontend**: React 18, Vite, Tailwind CSS, Plotly.js, TanStack Query
- **Data**: Yahoo Finance (prices), Ken French Data Library (factors)
- **Hosting**: Docker + nginx
