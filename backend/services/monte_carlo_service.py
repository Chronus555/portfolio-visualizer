"""
Monte Carlo simulation engine.

Supported models:
  - historical  : bootstrap from historical monthly returns
  - statistical : multivariate normal using historical mean / cov
  - forecasted  : user-supplied mean and std, normal distribution
  - parameterized: user-supplied mean and std (same as forecasted for now)
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from services.data_service import fetch_returns, current_year
from models.schemas import MonteCarloRequest, MonteCarloResult, MCModel

logger = logging.getLogger(__name__)

RNG = np.random.default_rng(42)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _portfolio_monthly_returns(
    returns_df: pd.DataFrame, weights: np.ndarray
) -> np.ndarray:
    """Compute weighted portfolio monthly return array."""
    port = returns_df.values @ weights
    return port


def _simulate_paths(
    monthly_samples: np.ndarray,   # shape (n_simulations, years*12)
    initial: float,
    annual_withdrawal: float,
    annual_contribution: float,
    inflation_rate: float,
    management_fee: float,
    years: int,
    n_sim: int,
) -> np.ndarray:
    """
    Simulate n_sim portfolio paths.
    Returns array of shape (n_sim, years+1) with year-end values.
    """
    monthly_withdrawal = annual_withdrawal / 12.0
    monthly_contribution = annual_contribution / 12.0
    monthly_inflation = (1 + inflation_rate) ** (1 / 12) - 1
    monthly_fee = (1 + management_fee) ** (1 / 12) - 1

    paths = np.zeros((n_sim, years + 1))
    paths[:, 0] = initial

    for sim_i in range(n_sim):
        value = initial
        for yr in range(years):
            for mo in range(12):
                t = yr * 12 + mo
                r = monthly_samples[sim_i, t]
                value = value * (1 + r - monthly_fee)
                value += monthly_contribution
                value -= monthly_withdrawal
                # Adjust withdrawal/contribution for inflation
                monthly_withdrawal *= 1 + monthly_inflation
                monthly_contribution *= 1 + monthly_inflation
                value = max(value, 0.0)

            paths[sim_i, yr + 1] = value
            # Reset for next year
            monthly_withdrawal = annual_withdrawal / 12.0 * (1 + inflation_rate) ** (yr + 1)
            monthly_contribution = annual_contribution / 12.0 * (1 + inflation_rate) ** (yr + 1)

    return paths


# ── Model implementations ──────────────────────────────────────────────────────

def _historical_samples(
    hist_returns: np.ndarray, n_sim: int, total_months: int
) -> np.ndarray:
    """Bootstrap from historical monthly returns."""
    idx = RNG.integers(0, len(hist_returns), size=(n_sim, total_months))
    return hist_returns[idx]


def _statistical_samples(
    mean: float, std: float, n_sim: int, total_months: int, corr: Optional[np.ndarray] = None
) -> np.ndarray:
    """Sample from normal distribution with given mean/std."""
    return RNG.normal(loc=mean, scale=std, size=(n_sim, total_months))


# ── Main entry point ───────────────────────────────────────────────────────────

def run_monte_carlo(request: MonteCarloRequest) -> MonteCarloResult:
    n_sim = request.simulations
    years = request.years
    total_months = years * 12

    weights = np.array(request.weights)
    weights = weights / weights.sum()

    # ── Get historical returns ───────────────────────────────────────────────
    end_y = request.end_year or current_year()
    rets_df = fetch_returns(request.tickers, request.start_year, end_y, "M")

    # Keep only tickers present in data
    available = [t for t in request.tickers if t in rets_df.columns]
    if not available:
        raise ValueError("No return data available for the specified tickers.")

    weights_aligned = np.array(
        [request.weights[request.tickers.index(t)] for t in available]
    )
    weights_aligned = weights_aligned / weights_aligned.sum()

    port_returns = _portfolio_monthly_returns(rets_df[available], weights_aligned)

    hist_mean = float(port_returns.mean())
    hist_std = float(port_returns.std())

    # ── Generate samples ─────────────────────────────────────────────────────
    if request.model == MCModel.historical:
        samples = _historical_samples(port_returns, n_sim, total_months)

    elif request.model == MCModel.statistical:
        samples = _statistical_samples(hist_mean, hist_std, n_sim, total_months)

    elif request.model in (MCModel.forecasted, MCModel.parameterized):
        mean = request.mean_return if request.mean_return is not None else hist_mean
        std = request.std_dev if request.std_dev is not None else hist_std
        samples = _statistical_samples(mean, std, n_sim, total_months)

    else:
        samples = _historical_samples(port_returns, n_sim, total_months)

    # ── Simulate paths ───────────────────────────────────────────────────────
    paths = _simulate_paths(
        samples,
        request.initial_amount,
        request.annual_withdrawal,
        request.annual_contribution,
        request.inflation_rate,
        request.management_fee,
        years,
        n_sim,
    )

    # ── Compute percentiles ──────────────────────────────────────────────────
    pct_labels = [10, 25, 50, 75, 90]
    percentiles: Dict[str, List[float]] = {}
    for p in pct_labels:
        percentiles[str(p)] = [
            round(float(np.percentile(paths[:, yr], p)), 2)
            for yr in range(years + 1)
        ]

    # ── Success rate (portfolio survives) ────────────────────────────────────
    final_values = paths[:, -1]
    success_rate = float(np.mean(final_values > 0) * 100)

    year_list = list(range(years + 1))

    return MonteCarloResult(
        percentiles=percentiles,
        years=year_list,
        success_rate=round(success_rate, 1),
        median_final=round(float(np.percentile(final_values, 50)), 2),
        p10_final=round(float(np.percentile(final_values, 10)), 2),
        p90_final=round(float(np.percentile(final_values, 90)), 2),
        initial_amount=request.initial_amount,
    )
