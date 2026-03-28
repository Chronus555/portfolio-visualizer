from fastapi import APIRouter, HTTPException
from models.schemas import OptimizationRequest, OptimizationResult
from services.optimization_service import run_optimization
import logging

router = APIRouter(prefix="/api/optimize", tags=["Optimization"])
logger = logging.getLogger(__name__)


@router.post("/portfolio", response_model=OptimizationResult)
async def optimize_portfolio(request: OptimizationRequest):
    try:
        return run_optimization(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Optimization error")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
