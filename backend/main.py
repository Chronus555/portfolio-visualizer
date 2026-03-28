"""
Portfolio Visualizer — FastAPI Backend
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import backtest, monte_carlo, optimization, factor_regression, correlations, fund_data
from routers import stress_test, fee_analyzer, tax_harvest, dividend, report
from routers import retirement, swr, budget, savings_goals
from routers import loan, dca, roth, bond, portfolio_xray

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Portfolio Visualizer API",
    description="Open-source portfolio analysis platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backtest.router)
app.include_router(monte_carlo.router)
app.include_router(optimization.router)
app.include_router(factor_regression.router)
app.include_router(correlations.router)
app.include_router(fund_data.router)
app.include_router(stress_test.router)
app.include_router(fee_analyzer.router)
app.include_router(tax_harvest.router)
app.include_router(dividend.router)
app.include_router(report.router)
app.include_router(retirement.router)
app.include_router(swr.router)
app.include_router(budget.router)
app.include_router(savings_goals.router)
app.include_router(loan.router)
app.include_router(dca.router)
app.include_router(roth.router)
app.include_router(bond.router)
app.include_router(portfolio_xray.router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Portfolio Visualizer API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
