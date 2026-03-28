"""
Fama-French / Carhart factor regression engine.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm

from services.data_service import (
    fetch_returns,
    fetch_fama_french_factors,
    current_year,
)
from models.schemas import FactorModel, FactorRegressionRequest, FactorRegressionResult, FactorCoefficient

logger = logging.getLogger(__name__)

FACTOR_COLUMNS = {
    FactorModel.ff3: ["Mkt-RF", "SMB", "HML"],
    FactorModel.ff5: ["Mkt-RF", "SMB", "HML", "RMW", "CMA"],
    FactorModel.carhart4: ["Mkt-RF", "SMB", "HML", "MOM"],
    FactorModel.ff3_momentum: ["Mkt-RF", "SMB", "HML", "MOM"],
}

FF_DATASET = {
    FactorModel.ff3: "ff3",
    FactorModel.ff5: "ff5",
    FactorModel.carhart4: "carhart4",
    FactorModel.ff3_momentum: "carhart4",
}


def _regress(excess_returns: pd.Series, factors: pd.DataFrame) -> Dict:
    """Run OLS regression and return results dict."""
    X = sm.add_constant(factors)
    model = sm.OLS(excess_returns, X).fit()

    coefficients = []
    for factor in factors.columns:
        coefficients.append(
            FactorCoefficient(
                factor=factor,
                coefficient=round(float(model.params[factor]), 4),
                t_stat=round(float(model.tvalues[factor]), 3),
                p_value=round(float(model.pvalues[factor]), 4),
                significant=bool(model.pvalues[factor] < 0.05),
            )
        )

    alpha_monthly = float(model.params["const"])
    alpha_annual = (1 + alpha_monthly) ** 12 - 1

    # Factor return contributions (factor coeff * factor mean, annualised)
    factor_contributions = {}
    for factor in factors.columns:
        monthly_contrib = float(model.params[factor]) * float(factors[factor].mean())
        factor_contributions[factor] = round(monthly_contrib * 12, 4)

    return {
        "alpha": round(alpha_monthly, 6),
        "alpha_annualized": round(alpha_annual, 4),
        "r_squared": round(float(model.rsquared), 4),
        "coefficients": coefficients,
        "factor_contributions": factor_contributions,
        "residual_std": round(float(model.resid.std() * np.sqrt(12)), 4),
        "observations": int(model.nobs),
    }


def run_factor_regression(request: FactorRegressionRequest) -> List[FactorRegressionResult]:
    end_y = request.end_year or current_year()

    # Fetch asset returns
    rets_df = fetch_returns(request.tickers, request.start_year, end_y, "M")
    available = [t for t in request.tickers if t in rets_df.columns]

    # Fetch factor data
    ff_dataset = FF_DATASET[request.model]
    factors_raw = fetch_fama_french_factors(ff_dataset, request.start_year, end_y)

    if factors_raw.empty:
        raise ValueError("Could not retrieve Fama-French factor data.")

    factor_cols = FACTOR_COLUMNS[request.model]
    available_factors = [c for c in factor_cols if c in factors_raw.columns]
    rf = factors_raw["RF"] if "RF" in factors_raw.columns else pd.Series(0, index=factors_raw.index)

    # Align dates
    combined = rets_df[available].join(factors_raw[available_factors + ["RF"] if "RF" in factors_raw.columns else available_factors], how="inner").dropna()

    if len(combined) < 12:
        raise ValueError("Insufficient overlapping data between assets and factors.")

    rf_aligned = combined["RF"] if "RF" in combined.columns else pd.Series(0, index=combined.index)
    factor_data = combined[available_factors]

    results = []

    if request.weights and len(request.weights) == len(available):
        # Portfolio regression
        weights = np.array(request.weights[:len(available)])
        weights = weights / weights.sum()
        port_returns = combined[available].values @ weights
        port_series = pd.Series(port_returns, index=combined.index)
        excess = port_series - rf_aligned

        reg = _regress(excess, factor_data)
        results.append(
            FactorRegressionResult(
                ticker="Portfolio",
                alpha=reg["alpha"],
                alpha_annualized=reg["alpha_annualized"],
                r_squared=reg["r_squared"],
                coefficients=reg["coefficients"],
                factor_returns_contribution=reg["factor_contributions"],
                residual_std=reg["residual_std"],
                observations=reg["observations"],
            )
        )
    else:
        # Individual ticker regressions
        for ticker in available:
            excess = combined[ticker] - rf_aligned
            reg = _regress(excess, factor_data)
            results.append(
                FactorRegressionResult(
                    ticker=ticker,
                    alpha=reg["alpha"],
                    alpha_annualized=reg["alpha_annualized"],
                    r_squared=reg["r_squared"],
                    coefficients=reg["coefficients"],
                    factor_returns_contribution=reg["factor_contributions"],
                    residual_std=reg["residual_std"],
                    observations=reg["observations"],
                )
            )

    return results
