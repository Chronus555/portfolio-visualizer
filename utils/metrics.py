"""Financial metrics and calculation utilities."""

import numpy as np
import pandas as pd
from scipy import optimize


# ---------------------------------------------------------------------------
# Core return calculations
# ---------------------------------------------------------------------------

def compute_portfolio_returns(
    prices: pd.DataFrame,
    weights: dict[str, float],
    rebalance: str = "monthly",
) -> pd.Series:
    """Compute weighted portfolio daily returns with periodic rebalancing.

    Args:
        prices: DataFrame of adjusted close prices (dates x tickers).
        weights: {ticker: weight} mapping. Weights should sum to 1.
        rebalance: 'daily', 'monthly', 'quarterly', 'annually', or 'none'.

    Returns:
        Series of daily portfolio returns.
    """
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])
    daily_returns = prices[tickers].pct_change().dropna()

    if rebalance == "daily":
        port_returns = daily_returns.dot(w)
        return port_returns

    # Build rebalancing group labels as a Series
    if rebalance == "monthly":
        groups = daily_returns.index.to_period("M").astype(str)
    elif rebalance == "quarterly":
        groups = daily_returns.index.to_period("Q").astype(str)
    elif rebalance == "annually":
        groups = daily_returns.index.to_period("Y").astype(str)
    else:
        groups = ["0"] * len(daily_returns)

    ret_array = daily_returns.values  # (n_days, n_assets)
    port_rets = np.empty(len(daily_returns))

    # Find period boundaries
    period_idx = np.array([hash(g) for g in groups])
    changes = np.where(np.diff(period_idx) != 0)[0] + 1
    starts = np.concatenate([[0], changes])
    ends = np.concatenate([changes, [len(daily_returns)]])

    for start, end in zip(starts, ends):
        pr = ret_array[start:end]            # (period_days, n_assets)
        port_cum = np.cumprod(1 + pr, axis=0) @ w  # weighted cum product
        port_rets[start] = pr[0] @ w
        if end - start > 1:
            port_rets[start + 1:end] = port_cum[1:] / port_cum[:-1] - 1

    return pd.Series(port_rets, index=daily_returns.index)


def compute_growth(returns: pd.Series, initial: float = 10000) -> pd.Series:
    """Compute growth of $initial investment from daily returns."""
    if len(returns) == 0:
        return pd.Series([initial], dtype=float)
    return initial * (1 + returns).cumprod()


# ---------------------------------------------------------------------------
# Performance metrics
# ---------------------------------------------------------------------------

def cagr(returns: pd.Series) -> float:
    """Compound Annual Growth Rate."""
    if len(returns) == 0:
        return 0.0
    total = (1 + returns).prod()
    years = len(returns) / 252
    if years <= 0:
        return 0.0
    return float(total ** (1 / years) - 1)


def annual_volatility(returns: pd.Series) -> float:
    """Annualized standard deviation."""
    if len(returns) < 2:
        return 0.0
    return float(returns.std() * np.sqrt(252))


def sharpe_ratio(returns: pd.Series, rf_annual: float = 0.0) -> float:
    """Annualized Sharpe Ratio."""
    vol = annual_volatility(returns)
    if vol == 0:
        return 0.0
    return (cagr(returns) - rf_annual) / vol


def sortino_ratio(returns: pd.Series, rf_annual: float = 0.0) -> float:
    """Annualized Sortino Ratio."""
    if len(returns) == 0:
        return 0.0
    neg = returns[returns < 0]
    if len(neg) < 2:
        return 0.0
    downside = neg.std() * np.sqrt(252)
    if downside == 0 or np.isnan(downside):
        return 0.0
    return (cagr(returns) - rf_annual) / float(downside)


def max_drawdown(returns: pd.Series) -> float:
    """Maximum drawdown (as a negative number)."""
    if len(returns) == 0:
        return 0.0
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    dd = (cum - running_max) / running_max
    return float(dd.min())


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Full drawdown time series."""
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    return (cum - running_max) / running_max


def calmar_ratio(returns: pd.Series) -> float:
    """Calmar Ratio = CAGR / |Max Drawdown|."""
    mdd = abs(max_drawdown(returns))
    if mdd == 0:
        return 0.0
    return cagr(returns) / mdd


def annual_returns(returns: pd.Series) -> pd.Series:
    """Yearly total returns."""
    yearly = (1 + returns).groupby(returns.index.year).prod() - 1
    return yearly


def monthly_returns_table(returns: pd.Series) -> pd.DataFrame:
    """Monthly returns pivot table (Year x Month)."""
    monthly = (1 + returns).groupby([returns.index.year, returns.index.month]).prod() - 1
    monthly.index.names = ["Year", "Month"]
    table = monthly.unstack(level="Month")
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    table.columns = [month_names[m - 1] for m in table.columns]
    return table


def rolling_returns(returns: pd.Series, window: int = 252) -> pd.Series:
    """Rolling annualized returns."""
    cum = (1 + returns).cumprod()
    rolling = cum / cum.shift(window)
    rolling = rolling.dropna()
    return rolling ** (252 / window) - 1


def beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Portfolio beta relative to benchmark."""
    aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 2:
        return 0.0
    cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
    if cov[1, 1] == 0:
        return 0.0
    return float(cov[0, 1] / cov[1, 1])


def alpha(returns: pd.Series, benchmark_returns: pd.Series, rf_annual: float = 0.0) -> float:
    """Jensen's Alpha (annualized)."""
    b = beta(returns, benchmark_returns)
    return cagr(returns) - (rf_annual + b * (cagr(benchmark_returns) - rf_annual))


def information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Information Ratio."""
    aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
    excess = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    te = excess.std() * np.sqrt(252)
    if te == 0:
        return 0.0
    return float((cagr(returns) - cagr(benchmark_returns)) / te)


def tail_ratio(returns: pd.Series) -> float:
    """Ratio of 95th percentile to absolute 5th percentile."""
    if len(returns) == 0:
        return 0.0
    p95 = np.percentile(returns, 95)
    p5 = abs(np.percentile(returns, 5))
    if p5 == 0:
        return 0.0
    return float(p95 / p5)


def var_historic(returns: pd.Series, confidence: float = 0.05) -> float:
    """Historical Value at Risk at given confidence level."""
    if len(returns) == 0:
        return 0.0
    return float(np.percentile(returns.dropna(), confidence * 100))


def cvar_historic(returns: pd.Series, confidence: float = 0.05) -> float:
    """Conditional VaR (Expected Shortfall)."""
    if len(returns) == 0:
        return 0.0
    var = var_historic(returns, confidence)
    tail = returns[returns <= var]
    return float(tail.mean()) if len(tail) > 0 else var


def compute_all_metrics(returns: pd.Series, benchmark_returns: pd.Series = None, rf_annual: float = 0.0) -> dict:
    """Compute a comprehensive set of metrics."""
    returns = returns.dropna()
    if len(returns) == 0:
        return {"CAGR": 0, "Annual Volatility": 0, "Sharpe Ratio": 0, "Sortino Ratio": 0,
                "Max Drawdown": 0, "Calmar Ratio": 0, "Best Year": 0, "Worst Year": 0,
                "VaR (5%)": 0, "CVaR (5%)": 0, "Tail Ratio": 0, "Skewness": 0, "Kurtosis": 0}
    _yr = annual_returns(returns)
    metrics = {
        "CAGR": cagr(returns),
        "Annual Volatility": annual_volatility(returns),
        "Sharpe Ratio": sharpe_ratio(returns, rf_annual),
        "Sortino Ratio": sortino_ratio(returns, rf_annual),
        "Max Drawdown": max_drawdown(returns),
        "Calmar Ratio": calmar_ratio(returns),
        "Best Year": float(_yr.max()) if len(returns) > 20 else 0.0,
        "Worst Year": float(_yr.min()) if len(returns) > 20 else 0.0,
        "VaR (5%)": var_historic(returns),
        "CVaR (5%)": cvar_historic(returns),
        "Tail Ratio": tail_ratio(returns),
        "Skewness": float(returns.skew()),
        "Kurtosis": float(returns.kurtosis()),
    }

    if benchmark_returns is not None and len(benchmark_returns) > 0:
        metrics["Beta"] = beta(returns, benchmark_returns)
        metrics["Alpha"] = alpha(returns, benchmark_returns, rf_annual)
        metrics["Information Ratio"] = information_ratio(returns, benchmark_returns)

    return metrics


# ---------------------------------------------------------------------------
# Monte Carlo Simulation
# ---------------------------------------------------------------------------

def monte_carlo_simulation(
    returns: pd.Series,
    years: int = 10,
    simulations: int = 1000,
    initial: float = 10000,
) -> np.ndarray:
    """Run Monte Carlo simulation using bootstrap resampling.

    Returns an array of shape (simulations, trading_days).
    """
    trading_days = years * 252
    returns_array = returns.values

    results = np.zeros((simulations, trading_days))
    for i in range(simulations):
        sampled = np.random.choice(returns_array, size=trading_days, replace=True)
        results[i] = initial * np.cumprod(1 + sampled)

    return results


def monte_carlo_percentiles(results: np.ndarray, percentiles: list[int] = None) -> dict[int, np.ndarray]:
    """Compute percentile paths from Monte Carlo results."""
    if percentiles is None:
        percentiles = [5, 10, 25, 50, 75, 90, 95]
    return {p: np.percentile(results, p, axis=0) for p in percentiles}


# ---------------------------------------------------------------------------
# Efficient Frontier / Mean-Variance Optimization
# ---------------------------------------------------------------------------

def efficient_frontier(
    returns: pd.DataFrame,
    n_points: int = 50,
    rf_annual: float = 0.0,
    short_selling: bool = False,
) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    """Compute the efficient frontier.

    Args:
        returns: DataFrame of daily returns for each asset.
        n_points: Number of points on the frontier.
        rf_annual: Risk-free rate for tangency portfolio.
        short_selling: Whether to allow negative weights.

    Returns:
        (risks, returns_arr, weights_list)
    """
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    n_assets = len(mean_returns)

    def portfolio_stats(w):
        port_return = np.dot(w, mean_returns)
        port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
        return port_return, port_vol

    def neg_sharpe(w):
        pr, pv = portfolio_stats(w)
        return -(pr - rf_annual) / pv if pv > 0 else 0

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    if short_selling:
        bounds = tuple((-1, 1) for _ in range(n_assets))
    else:
        bounds = tuple((0, 1) for _ in range(n_assets))

    w0 = np.ones(n_assets) / n_assets

    # Find min and max return portfolios
    min_ret_result = optimize.minimize(
        lambda w: np.dot(w, mean_returns),
        w0, method="SLSQP", bounds=bounds, constraints=constraints,
    )
    max_ret_result = optimize.minimize(
        lambda w: -np.dot(w, mean_returns),
        w0, method="SLSQP", bounds=bounds, constraints=constraints,
    )

    min_ret = np.dot(min_ret_result.x, mean_returns)
    max_ret = np.dot(max_ret_result.x, mean_returns)

    target_returns = np.linspace(min_ret, max_ret, n_points)
    risks = []
    rets = []
    weights_list = []

    for target in target_returns:
        cons = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, t=target: np.dot(w, mean_returns) - t},
        ]
        result = optimize.minimize(
            lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))),
            w0, method="SLSQP", bounds=bounds, constraints=cons,
        )
        if result.success:
            pr, pv = portfolio_stats(result.x)
            risks.append(pv)
            rets.append(pr)
            weights_list.append(result.x)

    return np.array(risks), np.array(rets), weights_list


def tangency_portfolio(
    returns: pd.DataFrame,
    rf_annual: float = 0.0,
    short_selling: bool = False,
) -> tuple[np.ndarray, float, float]:
    """Find the maximum Sharpe ratio (tangency) portfolio.

    Returns (weights, expected_return, volatility).
    """
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    n_assets = len(mean_returns)

    def neg_sharpe(w):
        pr = np.dot(w, mean_returns)
        pv = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
        return -(pr - rf_annual) / pv if pv > 0 else 0

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    if short_selling:
        bounds = tuple((-1, 1) for _ in range(n_assets))
    else:
        bounds = tuple((0, 1) for _ in range(n_assets))

    w0 = np.ones(n_assets) / n_assets
    result = optimize.minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=constraints)

    pr = np.dot(result.x, mean_returns)
    pv = np.sqrt(np.dot(result.x.T, np.dot(cov_matrix, result.x)))
    return result.x, pr, pv


def min_variance_portfolio(
    returns: pd.DataFrame,
    short_selling: bool = False,
) -> tuple[np.ndarray, float, float]:
    """Find the minimum variance portfolio."""
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    n_assets = len(mean_returns)

    def portfolio_vol(w):
        return np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    if short_selling:
        bounds = tuple((-1, 1) for _ in range(n_assets))
    else:
        bounds = tuple((0, 1) for _ in range(n_assets))

    w0 = np.ones(n_assets) / n_assets
    result = optimize.minimize(portfolio_vol, w0, method="SLSQP", bounds=bounds, constraints=constraints)

    pr = np.dot(result.x, mean_returns)
    pv = portfolio_vol(result.x)
    return result.x, pr, pv


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------

def asset_correlation(prices: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Compute correlation matrix from prices."""
    returns = prices.pct_change().dropna()
    return returns.corr(method=method)


def rolling_correlation(
    prices: pd.DataFrame,
    ticker1: str,
    ticker2: str,
    window: int = 63,
) -> pd.Series:
    """Rolling correlation between two assets."""
    returns = prices[[ticker1, ticker2]].pct_change().dropna()
    return returns[ticker1].rolling(window).corr(returns[ticker2])
