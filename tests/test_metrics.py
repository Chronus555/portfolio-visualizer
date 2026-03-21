"""Comprehensive tests for utils/metrics.py."""

import numpy as np
import pandas as pd
import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.metrics import (
    compute_portfolio_returns,
    compute_growth,
    cagr,
    annual_volatility,
    sharpe_ratio,
    sortino_ratio,
    max_drawdown,
    drawdown_series,
    calmar_ratio,
    annual_returns,
    monthly_returns_table,
    rolling_returns,
    beta,
    alpha,
    information_ratio,
    tail_ratio,
    var_historic,
    cvar_historic,
    compute_all_metrics,
    monte_carlo_simulation,
    monte_carlo_percentiles,
    efficient_frontier,
    tangency_portfolio,
    min_variance_portfolio,
    asset_correlation,
    rolling_correlation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_returns(n=504, seed=42, mu=0.0003, sigma=0.01):
    """Generate reproducible daily returns."""
    rng = np.random.default_rng(seed)
    vals = rng.normal(mu, sigma, n)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.Series(vals, index=dates)


def make_prices(tickers=("A", "B"), n=504, seed=42):
    """Generate reproducible price DataFrame."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    data = {}
    for i, t in enumerate(tickers):
        r = rng.normal(0.0003, 0.01, n)
        data[t] = 100 * np.cumprod(1 + r)
    return pd.DataFrame(data, index=dates)


EMPTY = pd.Series([], dtype=float)


# ---------------------------------------------------------------------------
# compute_growth
# ---------------------------------------------------------------------------

class TestComputeGrowth:
    def test_normal(self):
        r = make_returns(10)
        g = compute_growth(r, 10_000)
        assert len(g) == 10
        assert g.iloc[0] == pytest.approx(10_000 * (1 + r.iloc[0]))

    def test_empty_returns_not_empty(self):
        """Empty returns must not produce empty Series (guards .iloc[-1])."""
        g = compute_growth(EMPTY, 10_000)
        assert len(g) >= 1

    def test_empty_returns_initial_value(self):
        g = compute_growth(EMPTY, 5_000)
        assert g.iloc[-1] == pytest.approx(5_000)

    def test_normal_returns_have_datetimeindex(self):
        """Growth from dated returns must keep the DatetimeIndex so that
        date.year works in the annual-contributions loop."""
        r = make_returns(252)
        g = compute_growth(r, 10_000)
        assert isinstance(g.index, pd.DatetimeIndex)

    def test_all_zero_returns(self):
        r = pd.Series([0.0] * 5)
        g = compute_growth(r, 1_000)
        pd.testing.assert_series_equal(g, pd.Series([1_000.0] * 5))


# ---------------------------------------------------------------------------
# compute_portfolio_returns
# ---------------------------------------------------------------------------

class TestComputePortfolioReturns:
    def setup_method(self):
        self.prices = make_prices(("SPY", "AGG"), n=504)
        self.weights = {"SPY": 0.6, "AGG": 0.4}

    def _run(self, rebalance):
        ret = compute_portfolio_returns(self.prices, self.weights, rebalance)
        assert isinstance(ret, pd.Series)
        assert len(ret) == len(self.prices) - 1  # pct_change drops first row
        assert not ret.isna().any()
        return ret

    def test_monthly(self):   self._run("monthly")
    def test_quarterly(self): self._run("quarterly")
    def test_annually(self):  self._run("annually")
    def test_daily(self):     self._run("daily")
    def test_none(self):      self._run("none")

    def test_daily_equals_weighted_sum(self):
        """For daily rebalancing, returns == dot(w, asset_returns) exactly."""
        dr = self.prices.pct_change().dropna()
        expected = dr["SPY"] * 0.6 + dr["AGG"] * 0.4
        result = compute_portfolio_returns(self.prices, self.weights, "daily")
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_none_weights_drift(self):
        """Buy-and-hold: first-day return == weighted sum; after that weights drift."""
        dr = self.prices.pct_change().dropna()
        result = compute_portfolio_returns(self.prices, self.weights, "none")
        expected_day0 = dr["SPY"].iloc[0] * 0.6 + dr["AGG"].iloc[0] * 0.4
        assert result.iloc[0] == pytest.approx(expected_day0)

    def test_single_asset(self):
        """Single-asset portfolio return must equal asset return."""
        prices = self.prices[["SPY"]]
        ret = compute_portfolio_returns(prices, {"SPY": 1.0}, "monthly")
        expected = prices["SPY"].pct_change().dropna()
        pd.testing.assert_series_equal(ret, expected, check_names=False)

    def test_short_series_none(self):
        """none rebalancing on a series shorter than 22 days must still work."""
        short_prices = make_prices(("SPY", "AGG"), n=10)
        ret = compute_portfolio_returns(short_prices, self.weights, "none")
        assert len(ret) == 9
        assert not ret.isna().any()


# ---------------------------------------------------------------------------
# cagr
# ---------------------------------------------------------------------------

class TestCagr:
    def test_positive_returns(self):
        # Use a very large mu so the sum is overwhelmingly positive
        r = pd.Series([0.005] * 252)
        assert cagr(r) > 0

    def test_empty(self):
        assert cagr(EMPTY) == 0.0

    def test_known_value(self):
        """10% per year for exactly 1 year → cagr ≈ 0.10."""
        daily = (1.10) ** (1 / 252) - 1
        r = pd.Series([daily] * 252)
        assert cagr(r) == pytest.approx(0.10, rel=1e-3)

    def test_zero_years(self):
        assert cagr(pd.Series([])) == 0.0


# ---------------------------------------------------------------------------
# annual_volatility
# ---------------------------------------------------------------------------

class TestAnnualVolatility:
    def test_normal(self):
        r = make_returns(252, sigma=0.01)
        vol = annual_volatility(r)
        assert 0.10 < vol < 0.25  # daily 1% sigma → ~16% annualised

    def test_single_element(self):
        assert annual_volatility(pd.Series([0.01])) == 0.0

    def test_empty(self):
        assert annual_volatility(EMPTY) == 0.0

    def test_constant_returns(self):
        r = pd.Series([0.005] * 100)
        assert annual_volatility(r) == pytest.approx(0.0, abs=1e-10)


# ---------------------------------------------------------------------------
# sharpe_ratio
# ---------------------------------------------------------------------------

class TestSharpeRatio:
    def test_positive(self):
        r = make_returns(252, mu=0.001, sigma=0.01)
        assert sharpe_ratio(r) > 0

    def test_zero_vol(self):
        r = pd.Series([0.0] * 252)
        assert sharpe_ratio(r) == 0.0

    def test_empty(self):
        assert sharpe_ratio(EMPTY) == 0.0


# ---------------------------------------------------------------------------
# sortino_ratio
# ---------------------------------------------------------------------------

class TestSortinoRatio:
    def test_positive_for_good_returns(self):
        r = make_returns(252, mu=0.001, sigma=0.01)
        assert sortino_ratio(r) > 0

    def test_empty(self):
        assert sortino_ratio(EMPTY) == 0.0

    def test_no_negative_returns(self):
        r = pd.Series([0.01] * 252)  # all positive
        assert sortino_ratio(r) == 0.0


# ---------------------------------------------------------------------------
# max_drawdown / drawdown_series
# ---------------------------------------------------------------------------

class TestDrawdown:
    def test_max_drawdown_negative(self):
        r = make_returns(504)
        mdd = max_drawdown(r)
        assert mdd <= 0

    def test_max_drawdown_empty(self):
        assert max_drawdown(EMPTY) == 0.0

    def test_max_drawdown_all_positive(self):
        r = pd.Series([0.01] * 252)
        assert max_drawdown(r) == pytest.approx(0.0, abs=1e-10)

    def test_drawdown_series_empty_returns_empty(self):
        """drawdown_series on empty returns must produce empty Series — not crash.
        Guards the idxmin().strftime() call in the Drawdown tab."""
        dd = drawdown_series(EMPTY)
        assert len(dd) == 0

    def test_drawdown_series_shape(self):
        r = make_returns(100)
        dd = drawdown_series(r)
        assert len(dd) == 100
        assert (dd <= 0).all()

    def test_known_drawdown(self):
        """Drops 50% then recovers: max drawdown == -0.5."""
        r = pd.Series([0.0, -0.5, 1.0])   # 1.0 → 0.5 → 1.0; DD = -0.5
        assert max_drawdown(r) == pytest.approx(-0.5, rel=1e-6)


# ---------------------------------------------------------------------------
# calmar_ratio
# ---------------------------------------------------------------------------

class TestCalmarRatio:
    def test_normal(self):
        r = make_returns(504, mu=0.0003)
        c = calmar_ratio(r)
        assert isinstance(c, float)

    def test_zero_drawdown(self):
        r = pd.Series([0.01] * 252)
        assert calmar_ratio(r) == 0.0


# ---------------------------------------------------------------------------
# annual_returns
# ---------------------------------------------------------------------------

class TestAnnualReturns:
    def test_shape(self):
        r = make_returns(504)  # ~2 years
        yr = annual_returns(r)
        assert len(yr) >= 2

    def test_single_year(self):
        r = make_returns(252)
        yr = annual_returns(r)
        assert len(yr) == 1

    def test_values_reasonable(self):
        r = make_returns(504, mu=0.0003, sigma=0.01)
        yr = annual_returns(r)
        assert (yr > -0.9).all() and (yr < 5.0).all()


# ---------------------------------------------------------------------------
# monthly_returns_table
# ---------------------------------------------------------------------------

class TestMonthlyReturnsTable:
    def test_full_year_column_names(self):
        """All 12 months present → column names Jan … Dec."""
        dates = pd.date_range("2021-01-01", "2021-12-31", freq="B")
        r = pd.Series(np.random.default_rng(0).normal(0, 0.01, len(dates)), index=dates)
        t = monthly_returns_table(r)
        assert list(t.columns) == ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def test_partial_year_column_names(self):
        """Data starting March: columns must be Mar … Dec, NOT Jan … Oct."""
        dates = pd.date_range("2021-03-01", "2021-12-31", freq="B")
        r = pd.Series(np.random.default_rng(1).normal(0, 0.01, len(dates)), index=dates)
        t = monthly_returns_table(r)
        assert "Mar" in t.columns
        assert "Dec" in t.columns
        assert "Jan" not in t.columns
        assert "Feb" not in t.columns

    def test_multi_year_shape(self):
        r = make_returns(756)  # ~3 years
        t = monthly_returns_table(r)
        assert t.shape[0] >= 3

    def test_ytd_computable(self):
        """Confirm the YTD logic used in the page doesn't crash."""
        r = make_returns(504)
        t = monthly_returns_table(r)
        ytd = (1 + t.fillna(0)).prod(axis=1) - 1
        assert len(ytd) == len(t)


# ---------------------------------------------------------------------------
# rolling_returns
# ---------------------------------------------------------------------------

class TestRollingReturns:
    def test_length(self):
        r = make_returns(504)
        roll = rolling_returns(r, 252)
        assert len(roll) == 504 - 252

    def test_values_finite(self):
        r = make_returns(504)
        roll = rolling_returns(r, 252)
        assert np.isfinite(roll.values).all()


# ---------------------------------------------------------------------------
# beta / alpha / information_ratio
# ---------------------------------------------------------------------------

class TestBenchmarkMetrics:
    def setup_method(self):
        self.r = make_returns(504, seed=1)
        self.bm = make_returns(504, seed=2)

    def test_beta_range(self):
        b = beta(self.r, self.bm)
        assert -5.0 < b < 5.0

    def test_beta_perfect_correlation(self):
        b = beta(self.r, self.r)
        assert b == pytest.approx(1.0, rel=1e-6)

    def test_beta_misaligned_index(self):
        """beta should align on index, not crash with different lengths."""
        bm_short = self.bm.iloc[:200]
        b = beta(self.r, bm_short)
        assert np.isfinite(b)

    def test_alpha_returns_float(self):
        a = alpha(self.r, self.bm)
        assert isinstance(a, float)

    def test_information_ratio_returns_float(self):
        ir = information_ratio(self.r, self.bm)
        assert isinstance(ir, float)

    def test_empty_benchmark(self):
        assert beta(self.r, EMPTY) == 0.0

    def test_short_benchmark(self):
        assert beta(self.r, pd.Series([0.01])) == 0.0


# ---------------------------------------------------------------------------
# tail_ratio / VaR / CVaR
# ---------------------------------------------------------------------------

class TestRiskMetrics:
    def setup_method(self):
        self.r = make_returns(504)

    def test_var_negative(self):
        """VaR at 5% should be negative for realistic returns."""
        v = var_historic(self.r, 0.05)
        assert v < 0

    def test_cvar_le_var(self):
        v = var_historic(self.r, 0.05)
        cv = cvar_historic(self.r, 0.05)
        assert cv <= v

    def test_tail_ratio_positive(self):
        assert tail_ratio(self.r) > 0

    def test_var_empty(self):
        assert var_historic(EMPTY) == 0.0

    def test_cvar_empty(self):
        assert cvar_historic(EMPTY) == 0.0

    def test_tail_ratio_empty(self):
        assert tail_ratio(EMPTY) == 0.0


# ---------------------------------------------------------------------------
# compute_all_metrics
# ---------------------------------------------------------------------------

class TestComputeAllMetrics:
    def setup_method(self):
        self.r = make_returns(504)
        self.bm = make_returns(504, seed=2)

    def test_returns_dict(self):
        m = compute_all_metrics(self.r)
        assert isinstance(m, dict)
        assert "CAGR" in m
        assert "Max Drawdown" in m

    def test_with_benchmark_adds_keys(self):
        m = compute_all_metrics(self.r, self.bm)
        assert "Beta" in m
        assert "Alpha" in m
        assert "Information Ratio" in m

    def test_empty_returns(self):
        m = compute_all_metrics(EMPTY)
        assert m["CAGR"] == 0

    def test_all_values_finite(self):
        m = compute_all_metrics(self.r, self.bm)
        for k, v in m.items():
            assert np.isfinite(v), f"{k} is not finite: {v}"


# ---------------------------------------------------------------------------
# monte_carlo_simulation / monte_carlo_percentiles
# ---------------------------------------------------------------------------

class TestMonteCarlo:
    def setup_method(self):
        self.r = make_returns(504)

    def test_shape(self):
        results = monte_carlo_simulation(self.r, years=5, simulations=100, initial=10_000)
        assert results.shape == (100, 5 * 252)

    def test_initial_value(self):
        results = monte_carlo_simulation(self.r, years=1, simulations=50, initial=10_000)
        # all paths start from reinvested returns, values should be near 10k range
        assert results[:, 0].mean() > 0

    def test_percentiles_keys(self):
        results = monte_carlo_simulation(self.r, years=2, simulations=100)
        pcts = monte_carlo_percentiles(results)
        assert set(pcts.keys()) == {5, 10, 25, 50, 75, 90, 95}

    def test_percentiles_ordered(self):
        results = monte_carlo_simulation(self.r, years=2, simulations=200)
        pcts = monte_carlo_percentiles(results)
        # at every time step p5 <= p50 <= p95
        assert (pcts[5] <= pcts[50]).all()
        assert (pcts[50] <= pcts[95]).all()


# ---------------------------------------------------------------------------
# efficient_frontier / tangency / min_variance
# ---------------------------------------------------------------------------

class TestOptimization:
    def setup_method(self):
        prices = make_prices(("A", "B", "C"), n=504)
        self.ret_df = prices.pct_change().dropna()

    def test_efficient_frontier_shape(self):
        risks, rets, weights = efficient_frontier(self.ret_df, n_points=10)
        assert len(risks) > 0
        assert len(risks) == len(rets) == len(weights)

    def test_efficient_frontier_risks_positive(self):
        risks, _, _ = efficient_frontier(self.ret_df, n_points=10)
        assert (risks >= 0).all()

    def test_tangency_weights_sum_to_one(self):
        w, pr, pv = tangency_portfolio(self.ret_df)
        assert w.sum() == pytest.approx(1.0, abs=1e-6)
        assert pv >= 0

    def test_tangency_no_short_selling(self):
        w, _, _ = tangency_portfolio(self.ret_df, short_selling=False)
        assert (w >= -1e-6).all()

    def test_min_variance_weights_sum_to_one(self):
        w, pr, pv = min_variance_portfolio(self.ret_df)
        assert w.sum() == pytest.approx(1.0, abs=1e-6)

    def test_min_variance_lower_risk_than_equal_weight(self):
        w_mv, _, pv_mv = min_variance_portfolio(self.ret_df)
        ew = np.ones(3) / 3
        cov = self.ret_df.cov().values * 252
        pv_ew = np.sqrt(ew @ cov @ ew)
        assert pv_mv <= pv_ew + 1e-6


# ---------------------------------------------------------------------------
# asset_correlation / rolling_correlation
# ---------------------------------------------------------------------------

class TestCorrelation:
    def setup_method(self):
        self.prices = make_prices(("A", "B"), n=504)

    def test_asset_correlation_shape(self):
        corr = asset_correlation(self.prices)
        assert corr.shape == (2, 2)

    def test_asset_correlation_diagonal_ones(self):
        corr = asset_correlation(self.prices)
        assert corr.loc["A", "A"] == pytest.approx(1.0)
        assert corr.loc["B", "B"] == pytest.approx(1.0)

    def test_asset_correlation_symmetric(self):
        corr = asset_correlation(self.prices)
        assert corr.loc["A", "B"] == pytest.approx(corr.loc["B", "A"])

    def test_asset_correlation_range(self):
        corr = asset_correlation(self.prices)
        assert (-1.0 <= corr.values).all() and (corr.values <= 1.0).all()

    def test_rolling_correlation_length(self):
        # rolling_correlation calls pct_change().dropna() internally,
        # so the result has len(prices) - 1 rows.
        rc = rolling_correlation(self.prices, "A", "B", window=63)
        assert len(rc) == len(self.prices) - 1

    def test_rolling_correlation_range(self):
        rc = rolling_correlation(self.prices, "A", "B", window=63).dropna()
        assert (rc >= -1.0).all() and (rc <= 1.0).all()
