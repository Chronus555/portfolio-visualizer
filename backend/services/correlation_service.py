"""
Asset correlation, rolling correlation, and PCA engine.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from services.data_service import fetch_returns, current_year
from models.schemas import CorrelationRequest, CorrelationResult

logger = logging.getLogger(__name__)


def run_correlation_analysis(request: CorrelationRequest) -> CorrelationResult:
    end_y = request.end_year or current_year()

    rets = fetch_returns(request.tickers, request.start_year, end_y, "M")
    available = [t for t in request.tickers if t in rets.columns]

    if len(available) < 2:
        raise ValueError("Need at least 2 assets with available data.")

    rets = rets[available].dropna()

    # ── Correlation matrix ────────────────────────────────────────────────────
    corr_matrix = rets.corr(method=request.method.value)
    matrix_list = corr_matrix.values.round(4).tolist()

    # ── Rolling correlations ──────────────────────────────────────────────────
    rolling_data: Optional[List[Dict[str, Any]]] = None
    if request.rolling_window and len(available) >= 2:
        window = request.rolling_window
        roll_records = []
        for i in range(window, len(rets) + 1):
            slice_df = rets.iloc[i - window : i]
            date = rets.index[i - 1]
            corr_slice = slice_df.corr(method=request.method.value)
            record = {"date": date.strftime("%Y-%m-%d")}
            for j, t1 in enumerate(available):
                for k, t2 in enumerate(available):
                    if k > j:
                        key = f"{t1}_vs_{t2}"
                        record[key] = round(float(corr_slice.loc[t1, t2]), 4)
            roll_records.append(record)
        rolling_data = roll_records

    # ── PCA ──────────────────────────────────────────────────────────────────
    scaler = StandardScaler()
    scaled = scaler.fit_transform(rets.values)
    n_components = min(len(available), len(rets))
    pca = PCA(n_components=n_components)
    pca.fit(scaled)

    variance_explained = [round(float(v) * 100, 2) for v in pca.explained_variance_ratio_]
    pca_components = []
    for i, component in enumerate(pca.components_):
        comp_dict = {available[j]: round(float(component[j]), 4) for j in range(len(available))}
        comp_dict["component"] = f"PC{i+1}"
        comp_dict["variance_explained"] = variance_explained[i]
        pca_components.append(comp_dict)

    return CorrelationResult(
        tickers=available,
        matrix=matrix_list,
        rolling_data=rolling_data,
        pca_variance_explained=variance_explained,
        pca_components=pca_components,
    )
