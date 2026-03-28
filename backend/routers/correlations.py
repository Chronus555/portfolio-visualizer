from fastapi import APIRouter, HTTPException
from models.schemas import CorrelationRequest, CorrelationResult
from services.correlation_service import run_correlation_analysis
import logging

router = APIRouter(prefix="/api/correlations", tags=["Correlations"])
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=CorrelationResult)
async def analyze_correlations(request: CorrelationRequest):
    try:
        return run_correlation_analysis(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Correlation analysis error")
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")
