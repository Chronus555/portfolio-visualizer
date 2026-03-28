from fastapi import APIRouter, HTTPException
from models.schemas import BacktestRequest, BacktestResult
from services.backtest_service import run_backtest
import logging

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])
logger = logging.getLogger(__name__)


@router.post("/portfolio", response_model=BacktestResult)
async def backtest_portfolio(request: BacktestRequest):
    try:
        return run_backtest(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Backtest error")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")
