from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from services.swr_service import analyze_swr, STRATEGY_META

router = APIRouter(prefix="/api/swr", tags=["swr"])

ALL_STRATEGIES = list(STRATEGY_META.keys())


class SWRRequest(BaseModel):
    portfolio_value: float = Field(1_000_000, gt=0)
    annual_expenses: float = Field(40_000, gt=0)
    retirement_years: int = Field(30, ge=5, le=60)
    stock_allocation: float = Field(60.0, ge=0, le=100)
    inflation: float = Field(3.0, ge=0, le=15)
    strategies: List[str] = Field(default_factory=lambda: ALL_STRATEGIES)
    simulations: int = Field(5000, ge=500, le=20000)


@router.get("/strategies")
async def list_strategies():
    return {"strategies": STRATEGY_META}


@router.post("/analyze")
async def swr_analyze(req: SWRRequest):
    valid = [s for s in req.strategies if s in STRATEGY_META]
    if not valid:
        raise HTTPException(400, "No valid strategies provided")
    try:
        return analyze_swr(
            portfolio_value=req.portfolio_value,
            annual_expenses=req.annual_expenses,
            retirement_years=req.retirement_years,
            stock_allocation=req.stock_allocation,
            inflation=req.inflation,
            strategies=valid,
            simulations=req.simulations,
        )
    except Exception as e:
        raise HTTPException(500, str(e))
