from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class RebalanceFrequency(str, Enum):
    none = "none"
    monthly = "monthly"
    quarterly = "quarterly"
    semiannual = "semiannual"
    annual = "annual"

class BenchmarkType(str, Enum):
    none = "none"
    spy = "SPY"
    qqq = "QQQ"
    agg = "AGG"
    custom = "custom"

class MCModel(str, Enum):
    historical = "historical"
    statistical = "statistical"
    forecasted = "forecasted"
    parameterized = "parameterized"

class OptimizationGoal(str, Enum):
    max_sharpe = "max_sharpe"
    min_volatility = "min_volatility"
    efficient_risk = "efficient_risk"
    efficient_return = "efficient_return"
    max_quadratic_utility = "max_quadratic_utility"
    cvar = "cvar"
    risk_parity = "risk_parity"
    cdar = "cdar"

class FactorModel(str, Enum):
    ff3 = "ff3"
    ff5 = "ff5"
    carhart4 = "carhart4"
    ff3_momentum = "ff3_momentum"

class CorrelationMethod(str, Enum):
    pearson = "pearson"
    spearman = "spearman"
    kendall = "kendall"


# ── Shared sub-models ──────────────────────────────────────────────────────────

class AssetAllocation(BaseModel):
    ticker: str
    weight: float = Field(ge=0, le=100)
    name: Optional[str] = None

class PortfolioDefinition(BaseModel):
    name: str = "Portfolio"
    allocations: List[AssetAllocation]


# ── Backtest ───────────────────────────────────────────────────────────────────

class BacktestRequest(BaseModel):
    portfolios: List[PortfolioDefinition]
    start_year: int = Field(default=2000, ge=1970, le=2100)
    end_year: Optional[int] = None
    initial_amount: float = Field(default=10000, ge=1)
    annual_contribution: float = 0
    rebalance: RebalanceFrequency = RebalanceFrequency.annual
    benchmark: str = "SPY"
    inflation_adjusted: bool = False

class RollingReturn(BaseModel):
    date: str
    value: float

class YearlyReturn(BaseModel):
    year: int
    returns: Dict[str, float]  # portfolio name -> return %

class DrawdownPoint(BaseModel):
    date: str
    values: Dict[str, float]

class BacktestMetrics(BaseModel):
    portfolio_name: str
    cagr: float
    stdev: float
    best_year: float
    worst_year: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    market_correlation: float
    final_balance: float
    start_balance: float

class BacktestResult(BaseModel):
    metrics: List[BacktestMetrics]
    growth_data: List[Dict[str, Any]]          # date + portfolio values
    annual_returns: List[YearlyReturn]
    drawdown_data: List[DrawdownPoint]
    rolling_returns_1yr: List[Dict[str, Any]]
    rolling_returns_3yr: List[Dict[str, Any]]
    rolling_returns_5yr: List[Dict[str, Any]]
    monthly_returns: Dict[str, List[Dict[str, Any]]]


# ── Monte Carlo ────────────────────────────────────────────────────────────────

class MonteCarloRequest(BaseModel):
    tickers: List[str]
    weights: List[float]
    initial_amount: float = Field(default=100000, ge=1)
    years: int = Field(default=30, ge=1, le=100)
    simulations: int = Field(default=1000, ge=100, le=10000)
    annual_withdrawal: float = 0
    annual_contribution: float = 0
    model: MCModel = MCModel.historical
    # for forecasted / parameterized
    mean_return: Optional[float] = None
    std_dev: Optional[float] = None
    start_year: int = Field(default=2000, ge=1970)
    end_year: Optional[int] = None
    inflation_rate: float = 0
    management_fee: float = 0

class MonteCarloResult(BaseModel):
    percentiles: Dict[str, List[float]]   # "10","25","50","75","90" -> list per year
    years: List[int]
    success_rate: float
    median_final: float
    p10_final: float
    p90_final: float
    initial_amount: float


# ── Optimization ───────────────────────────────────────────────────────────────

class OptimizationRequest(BaseModel):
    tickers: List[str]
    start_year: int = Field(default=2010, ge=1970)
    end_year: Optional[int] = None
    goal: OptimizationGoal = OptimizationGoal.max_sharpe
    risk_free_rate: float = 0.02
    target_return: Optional[float] = None
    target_risk: Optional[float] = None
    weight_bounds: tuple = (0.0, 1.0)
    risk_aversion: float = 1.0
    n_frontier_points: int = Field(default=50, ge=10, le=200)

class OptimizationResult(BaseModel):
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    efficient_frontier: List[Dict[str, Any]]  # [{risk, return, sharpe, weights}]
    individual_assets: List[Dict[str, Any]]      # each ticker's risk/return
    cvar: Optional[float] = None


# ── Factor Regression ─────────────────────────────────────────────────────────

class FactorRegressionRequest(BaseModel):
    tickers: List[str]
    weights: Optional[List[float]] = None   # if None, equal weight
    model: FactorModel = FactorModel.ff3
    start_year: int = Field(default=2000, ge=1926)
    end_year: Optional[int] = None

class FactorCoefficient(BaseModel):
    factor: str
    coefficient: float
    t_stat: float
    p_value: float
    significant: bool

class FactorRegressionResult(BaseModel):
    ticker: str
    alpha: float
    alpha_annualized: float
    r_squared: float
    coefficients: List[FactorCoefficient]
    factor_returns_contribution: Dict[str, float]
    residual_std: float
    observations: int


# ── Correlations ──────────────────────────────────────────────────────────────

class CorrelationRequest(BaseModel):
    tickers: List[str]
    start_year: int = Field(default=2000, ge=1970)
    end_year: Optional[int] = None
    method: CorrelationMethod = CorrelationMethod.pearson
    rolling_window: Optional[int] = None   # months

class CorrelationResult(BaseModel):
    tickers: List[str]
    matrix: List[List[float]]
    rolling_data: Optional[List[Dict[str, Any]]] = None
    pca_variance_explained: Optional[List[float]] = None
    pca_components: Optional[List[Dict[str, Any]]] = None


# ── Fund Screener ─────────────────────────────────────────────────────────────

class FundScreenerRequest(BaseModel):
    tickers: List[str]
    start_year: int = Field(default=2010, ge=1970)
    end_year: Optional[int] = None

class FundMetrics(BaseModel):
    ticker: str
    name: str
    cagr_1yr: Optional[float]
    cagr_3yr: Optional[float]
    cagr_5yr: Optional[float]
    cagr_10yr: Optional[float]
    stdev: float
    sharpe: float
    sortino: float
    max_drawdown: float
    beta: float
    alpha: float
    expense_ratio: Optional[float]


# ── Export ────────────────────────────────────────────────────────────────────

class ExportFormat(str, Enum):
    csv = "csv"
    excel = "excel"
    pdf = "pdf"
