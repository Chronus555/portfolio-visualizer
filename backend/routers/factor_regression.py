from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import FactorRegressionRequest, FactorRegressionResult
from services.factor_service import run_factor_regression
import logging

router = APIRouter(prefix="/api/factors", tags=["Factor Regression"])
logger = logging.getLogger(__name__)


@router.post("/regression", response_model=List[FactorRegressionResult])
async def factor_regression(request: FactorRegressionRequest):
    try:
        return run_factor_regression(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Factor regression error")
        raise HTTPException(status_code=500, detail=f"Factor regression failed: {str(e)}")
