from fastapi import APIRouter, HTTPException
from models.schemas import MonteCarloRequest, MonteCarloResult
from services.monte_carlo_service import run_monte_carlo
import logging

router = APIRouter(prefix="/api/monte-carlo", tags=["Monte Carlo"])
logger = logging.getLogger(__name__)


@router.post("/simulate", response_model=MonteCarloResult)
async def monte_carlo_simulate(request: MonteCarloRequest):
    try:
        return run_monte_carlo(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Monte Carlo error")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
