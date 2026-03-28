"""
Portfolio Visualizer — FastAPI Backend
"""

# ── Matplotlib compatibility patch ──────────────────────────────────────────
# PyPortfolioOpt's plotting.py calls plt.style.use("seaborn-deep") at import
# time.  matplotlib ≥ 3.6 renamed these styles to "seaborn-v0_8-deep"; the
# old aliases were fully removed in 3.9.  Register the alias before anything
# triggers a pypfopt import so the server starts cleanly on any mpl version.
try:
    import matplotlib
    import matplotlib.style.core as _mpl_style_core
    _mpl_style_core.reload_library()          # ensure library is populated
    _lib = matplotlib.style.library
    for _old, _new in [
        ("seaborn-deep",       "seaborn-v0_8-deep"),
        ("seaborn-whitegrid",  "seaborn-v0_8-whitegrid"),
        ("seaborn-darkgrid",   "seaborn-v0_8-darkgrid"),
        ("seaborn-muted",      "seaborn-v0_8-muted"),
        ("seaborn-pastel",     "seaborn-v0_8-pastel"),
        ("seaborn-bright",     "seaborn-v0_8-bright"),
        ("seaborn-dark",       "seaborn-v0_8-dark"),
        ("seaborn-colorblind", "seaborn-v0_8-colorblind"),
        ("seaborn-notebook",   "seaborn-v0_8-notebook"),
        ("seaborn-paper",      "seaborn-v0_8-paper"),
        ("seaborn-poster",     "seaborn-v0_8-poster"),
        ("seaborn-talk",       "seaborn-v0_8-talk"),
        ("seaborn-ticks",      "seaborn-v0_8-ticks"),
        ("seaborn",            "seaborn-v0_8"),
    ]:
        if _old not in _lib and _new in _lib:
            _lib[_old] = _lib[_new]
except Exception:
    pass  # best-effort — never block startup
# ── End patch ────────────────────────────────────────────────────────────────

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
