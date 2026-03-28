"""
Portfolio backtesting engine.

Supports:
  - Multiple portfolios compared side-by-side
  - Annual / quarterly / monthly / semi-annual rebalancing (or buy-and-hold)
  - Optional annual contributions or withdrawals
  - Inflation adjustment
  - Full set of risk/return metrics
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from services.data_service import (
    fetch_price_data,
    fetch_benchmark_returns,
    current_year,
)
from models.schemas import (
    BacktestRequest,
    BacktestMetrics,
    BacktestResult,
    RebalanceFrequency,
)

logger = logging.getLogger(__name__)

REBALANCE_MONTHS = {
    RebalanceFrequency.monthly: 1,
    RebalanceFrequency.quarterly: 3,
    RebalanceFrequency.semiannual: 6,
    RebalanceFrequency.annual: 12,
    RebalanceFrequency.none: 0,
}


# ── Core simulation ────────────────────────────────────────────────────────────

def simulate_portfolio(
    prices: pd.DataFrame,
    allocations: Dict[str, float],   # ticker -> weight (must sum to ~1)
    initial_amount: float,
    annual_contribution: float,
    rebalance_freq: RebalanceFrequency,
) -> pd.Series:
    """
    Simulate portfolio value month-by-month.
    Returns a Series indexed by date with portfolio dollar value.
    """
    tickers = [t for t in allocations if t in prices.columns]
    if not tickers:
        return pd.Series(dtype=float)

    weights = np.array([allocations[t] for t in tickers])
    weights = weights / weights.sum()  # normalise

    price_slice = prices[tickers].dropna(how="all").ffill()
    monthly_returns = price_slice.pct_change().dropna()

    rebalance_n = REBALANCE_MONTHS[rebalance_freq]
    monthly_contribution = annual_contribution / 12.0

    # Initialise holdings in shares
    first_prices = price_slice.iloc[0]
    dollar_alloc = weights * initial_amount
    shares = dollar_alloc / first_prices

    values = []
    dates = []
    months_since_rebalance = 0

    for i, (date, row) in enumerate(price_slice.iterrows()):
        # current portfolio value
        port_value = float((shares * row).sum())

        # contributions (add at beginning of each month)
        if i > 0 and monthly_contribution != 0:
            # buy shares proportionally
            extra = monthly_contribution * weights
            shares = shares + extra / row

        # recalculate value after contribution
        port_value = float((shares * row).sum())
        values.append(port_value)
        dates.append(date)

        months_since_rebalance += 1

        # rebalance
        if rebalance_n > 0 and months_since_rebalance >= rebalance_n:
            port_value = float((shares * row).sum())
            dollar_alloc = weights * port_value
            shares = dollar_alloc / row
            months_since_rebalance = 0

    return pd.Series(values, index=pd.DatetimeIndex(dates))


# ── Metric calculations ────────────────────────────────────────────────────────

def compute_cagr(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0
    years = (series.index[-1] - series.index[0]).days / 365.25
    if years <= 0 or series.iloc[0] <= 0:
        return 0.0
    return float((series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1)


def compute_max_drawdown(series: pd.Series) -> float:
    cummax = series.cummax()
    drawdown = (series - cummax) / cummax
    return float(drawdown.min())


def compute_sharpe(returns: pd.Series, rf_annual: float = 0.02) -> float:
    rf_monthly = (1 + rf_annual) ** (1 / 12) - 1
    excess = returns - rf_monthly
    if excess.std() == 0:
        return 0.0
    return float(excess.mean() / excess.std() * np.sqrt(12))


def compute_sortino(returns: pd.Series, rf_annual: float = 0.02) -> float:
    rf_monthly = (1 + rf_annual) ** (1 / 12) - 1
    excess = returns - rf_monthly
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std() * np.sqrt(12))


def compute_annual_returns(series: pd.Series) -> Dict[int, float]:
    yearly = series.resample("YE").last()
    returns = yearly.pct_change().dropna()
    return {int(d.year): float(r) for d, r in returns.items()}


def compute_rolling_returns(series: pd.Series, window_months: int) -> pd.Series:
    monthly = series.pct_change().dropna()
    rolling = (1 + monthly).rolling(window_months).apply(
        lambda x: np.prod(x) - 1, raw=True
    )
    return rolling.dropna()


def compute_market_correlation(
    portfolio_returns: pd.Series, benchmark_returns: pd.Series
) -> float:
    aligned = pd.concat(
        [portfolio_returns, benchmark_returns], axis=1
    ).dropna()
    if len(aligned) < 3:
        return 0.0
    return float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))


# ── Main entry point ───────────────────────────────────────────────────────────

def run_backtest(request: BacktestRequest) -> BacktestResult:
    end_y = request.end_year or current_year()

    # Collect all unique tickers
    all_tickers = list(
        {a.ticker for p in request.portfolios for a in p.allocations}
    )
    if request.benchmark and request.benchmark.lower() != "none":
        all_tickers.append(request.benchmark)

    prices = fetch_price_data(all_tickers, request.start_year, end_y)

    benchmark_returns = fetch_benchmark_returns(
        request.benchmark, request.start_year, end_y
    )

    # ── Simulate each portfolio ──────────────────────────────────────────────
    portfolio_series: Dict[str, pd.Series] = {}
    portfolio_returns: Dict[str, pd.Series] = {}

    for port in request.portfolios:
        alloc = {a.ticker: a.weight / 100.0 for a in port.allocations}
        series = simulate_portfolio(
            prices,
            alloc,
            request.initial_amount,
            request.annual_contribution,
            request.rebalance,
        )
        if series.empty:
            continue
        portfolio_series[port.name] = series
        portfolio_returns[port.name] = series.pct_change().dropna()

    if not portfolio_series:
        raise ValueError("No valid portfolio data could be computed.")

    # ── Metrics ──────────────────────────────────────────────────────────────
    metrics_list: List[BacktestMetrics] = []
    for name, series in portfolio_series.items():
        rets = portfolio_returns[name]
        annual_rets = compute_annual_returns(series)

        mkt_corr = compute_market_correlation(rets, benchmark_returns)

        metrics_list.append(
            BacktestMetrics(
                portfolio_name=name,
                cagr=compute_cagr(series),
                stdev=float(rets.std() * np.sqrt(12)),
                best_year=max(annual_rets.values()) if annual_rets else 0.0,
                worst_year=min(annual_rets.values()) if annual_rets else 0.0,
                max_drawdown=compute_max_drawdown(series),
                sharpe_ratio=compute_sharpe(rets),
                sortino_ratio=compute_sortino(rets),
                market_correlation=mkt_corr,
                final_balance=float(series.iloc[-1]),
                start_balance=request.initial_amount,
            )
        )

    # ── Growth data (for the main chart) ────────────────────────────────────
    # Align all series to common dates
    all_series = pd.DataFrame(portfolio_series)
    if not benchmark_returns.empty:
        bench_val = (1 + benchmark_returns).cumprod() * request.initial_amount
        bench_val.name = request.benchmark
        all_series = all_series.join(bench_val, how="left")

    growth_data = []
    for date, row in all_series.iterrows():
        entry = {"date": date.strftime("%Y-%m-%d")}
        for col in all_series.columns:
            if not np.isnan(row[col]):
                entry[col] = round(float(row[col]), 2)
        growth_data.append(entry)

    # ── Annual returns table ─────────────────────────────────────────────────
    annual_data = {}
    for name, series in portfolio_series.items():
        annual_data[name] = compute_annual_returns(series)

    all_years = sorted(
        {yr for d in annual_data.values() for yr in d.keys()}
    )
    annual_returns = [
        {
            "year": yr,
            "returns": {
                name: round(annual_data[name].get(yr, 0) * 100, 2)
                for name in portfolio_series
            },
        }
        for yr in all_years
    ]

    # ── Drawdown data ────────────────────────────────────────────────────────
    drawdown_df = pd.DataFrame(
        {
            name: (s - s.cummax()) / s.cummax() * 100
            for name, s in portfolio_series.items()
        }
    )
    drawdown_data = []
    for date, row in drawdown_df.iterrows():
        values = {col: round(float(row[col]), 2) for col in drawdown_df.columns}
        drawdown_data.append({"date": date.strftime("%Y-%m-%d"), "values": values})

    # ── Rolling returns ──────────────────────────────────────────────────────
    def rolling_dict(window: int) -> List[Dict[str, Any]]:
        result = {}
        for name, series in portfolio_series.items():
            r = compute_rolling_returns(series, window)
            result[name] = r * 100
        df = pd.DataFrame(result).dropna(how="all")
        out = []
        for date, row in df.iterrows():
            entry = {"date": date.strftime("%Y-%m-%d")}
            for col in df.columns:
                if not np.isnan(row[col]):
                    entry[col] = round(float(row[col]), 2)
            out.append(entry)
        return out

    # ── Monthly returns heat-map data ────────────────────────────────────────
    monthly_returns_data: Dict[str, List[Dict[str, Any]]] = {}
    for name, series in portfolio_series.items():
        rets = series.pct_change().dropna()
        rows = []
        for date, val in rets.items():
            rows.append(
                {
                    "year": date.year,
                    "month": date.month,
                    "return": round(float(val) * 100, 2),
                }
            )
        monthly_returns_data[name] = rows

    return BacktestResult(
        metrics=metrics_list,
        growth_data=growth_data,
        annual_returns=annual_returns,
        drawdown_data=drawdown_data,
        rolling_returns_1yr=rolling_dict(12),
        rolling_returns_3yr=rolling_dict(36),
        rolling_returns_5yr=rolling_dict(60),
        monthly_returns=monthly_returns_data,
    )
