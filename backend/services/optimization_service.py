"""
Portfolio optimization engine.

Uses PyPortfolioOpt for mean-variance and CVaR optimization.
Falls back to scipy for risk parity.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pypfopt import (
    EfficientFrontier,
    EfficientCVaR,
    EfficientCDaR,
    risk_models,
    expected_returns,
    plotting,
)
from pypfopt.exceptions import OptimizationError
from scipy.optimize import minimize

from services.data_service import fetch_returns, current_year
from models.schemas import OptimizationGoal, OptimizationRequest, OptimizationResult

logger = logging.getLogger(__name__)


# ── Risk Parity ────────────────────────────────────────────────────────────────

def _risk_parity_weights(cov_matrix: np.ndarray) -> np.ndarray:
    """Equal risk contribution weights via scipy."""
    n = cov_matrix.shape[0]

    def portfolio_vol(w):
        return np.sqrt(w @ cov_matrix @ w)

    def risk_contribution(w):
        vol = portfolio_vol(w)
        mrc = cov_matrix @ w / vol   # marginal risk contribution
        return w * mrc               # risk contribution per asset

    def objective(w):
        rc = risk_contribution(w)
        avg_rc = np.mean(rc)
        return np.sum((rc - avg_rc) ** 2)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0.01, 1.0)] * n
    x0 = np.ones(n) / n

    result = minimize(objective, x0, bounds=bounds, constraints=constraints, method="SLSQP")
    return result.x / result.x.sum()


# ── Efficient Frontier points ──────────────────────────────────────────────────

def _compute_frontier_points(
    mu: pd.Series,
    S: pd.DataFrame,
    n_points: int,
    risk_free_rate: float,
    weight_bounds: Tuple[float, float],
) -> List[Dict[str, Any]]:
    """Sample n_points along the efficient frontier."""
    points = []
    min_ret = float(mu.min())
    max_ret = float(mu.max())
    target_returns = np.linspace(min_ret * 1.05, max_ret * 0.95, n_points)

    for target in target_returns:
        try:
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
            ef.efficient_return(target_return=float(target))
            w = ef.clean_weights()
            perf = ef.portfolio_performance(risk_free_rate=risk_free_rate)
            points.append(
                {
                    "risk": round(perf[1] * 100, 3),
                    "return": round(perf[0] * 100, 3),
                    "sharpe": round(perf[2], 3),
                    "weights": {k: round(v, 4) for k, v in w.items() if v > 0.001},
                }
            )
        except (OptimizationError, Exception):
            continue

    return points


# ── Main entry point ───────────────────────────────────────────────────────────

def run_optimization(request: OptimizationRequest) -> OptimizationResult:
    end_y = request.end_year or current_year()

    rets_df = fetch_returns(request.tickers, request.start_year, end_y, "M")
    available = [t for t in request.tickers if t in rets_df.columns]
    if len(available) < 2:
        raise ValueError("Need at least 2 assets with available return data.")

    rets_df = rets_df[available]

    # Annualised expected returns and covariance
    mu = expected_returns.mean_historical_return(
        rets_df, returns_data=True, frequency=12
    )
    S = risk_models.sample_cov(rets_df, returns_data=True, frequency=12)

    weight_bounds = tuple(request.weight_bounds)
    rf = request.risk_free_rate

    # ── Optimise ──────────────────────────────────────────────────────────────
    opt_weights: Dict[str, float] = {}
    exp_ret = exp_vol = sharpe = cvar_val = 0.0

    if request.goal == OptimizationGoal.max_sharpe:
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
        ef.max_sharpe(risk_free_rate=rf)
        opt_weights = dict(ef.clean_weights())
        exp_ret, exp_vol, sharpe = ef.portfolio_performance(risk_free_rate=rf)

    elif request.goal == OptimizationGoal.min_volatility:
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
        ef.min_volatility()
        opt_weights = dict(ef.clean_weights())
        exp_ret, exp_vol, sharpe = ef.portfolio_performance(risk_free_rate=rf)

    elif request.goal == OptimizationGoal.efficient_risk:
        target = request.target_risk or 0.15
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
        ef.efficient_risk(target_volatility=target)
        opt_weights = dict(ef.clean_weights())
        exp_ret, exp_vol, sharpe = ef.portfolio_performance(risk_free_rate=rf)

    elif request.goal == OptimizationGoal.efficient_return:
        target = request.target_return or float(mu.mean())
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
        ef.efficient_return(target_return=target)
        opt_weights = dict(ef.clean_weights())
        exp_ret, exp_vol, sharpe = ef.portfolio_performance(risk_free_rate=rf)

    elif request.goal == OptimizationGoal.max_quadratic_utility:
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
        ef.max_quadratic_utility(risk_aversion=request.risk_aversion)
        opt_weights = dict(ef.clean_weights())
        exp_ret, exp_vol, sharpe = ef.portfolio_performance(risk_free_rate=rf)

    elif request.goal == OptimizationGoal.cvar:
        ef_cvar = EfficientCVaR(mu, rets_df)
        ef_cvar.min_cvar()
        opt_weights = dict(ef_cvar.clean_weights())
        exp_ret = float(mu @ pd.Series(opt_weights).reindex(mu.index).fillna(0))
        w_arr = np.array([opt_weights.get(t, 0) for t in available])
        exp_vol = float(np.sqrt(w_arr @ S.values @ w_arr))
        sharpe = (exp_ret - rf) / exp_vol if exp_vol > 0 else 0
        cvar_val = float(ef_cvar.portfolio_performance()[1])

    elif request.goal == OptimizationGoal.cdar:
        ef_cdar = EfficientCDaR(mu, rets_df)
        ef_cdar.min_cdar()
        opt_weights = dict(ef_cdar.clean_weights())
        exp_ret = float(mu @ pd.Series(opt_weights).reindex(mu.index).fillna(0))
        w_arr = np.array([opt_weights.get(t, 0) for t in available])
        exp_vol = float(np.sqrt(w_arr @ S.values @ w_arr))
        sharpe = (exp_ret - rf) / exp_vol if exp_vol > 0 else 0

    elif request.goal == OptimizationGoal.risk_parity:
        rp_w = _risk_parity_weights(S.values)
        opt_weights = {t: float(w) for t, w in zip(available, rp_w)}
        w_arr = rp_w
        exp_ret = float(w_arr @ mu.values)
        exp_vol = float(np.sqrt(w_arr @ S.values @ w_arr))
        sharpe = (exp_ret - rf) / exp_vol if exp_vol > 0 else 0

    # ── Efficient frontier curve ──────────────────────────────────────────────
    frontier_points = _compute_frontier_points(
        mu, S, request.n_frontier_points, rf, weight_bounds
    )

    # ── Individual asset stats ────────────────────────────────────────────────
    individual_assets = []
    for t in available:
        asset_vol = float(np.sqrt(S.loc[t, t]))
        asset_ret = float(mu[t])
        individual_assets.append(
            {
                "ticker": t,
                "expected_return": round(asset_ret * 100, 2),
                "expected_volatility": round(asset_vol * 100, 2),
                "sharpe": round((asset_ret - rf) / asset_vol if asset_vol > 0 else 0, 3),
            }
        )

    return OptimizationResult(
        weights={k: round(v, 4) for k, v in opt_weights.items() if v > 0.0001},
        expected_return=round(float(exp_ret) * 100, 2),
        expected_volatility=round(float(exp_vol) * 100, 2),
        sharpe_ratio=round(float(sharpe), 3),
        efficient_frontier=frontier_points,
        individual_assets=individual_assets,
        cvar=round(cvar_val * 100, 2) if cvar_val else None,
    )
