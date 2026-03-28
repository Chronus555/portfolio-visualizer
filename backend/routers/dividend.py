from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.dividend_service import analyze_dividends

router = APIRouter(prefix="/api/dividend", tags=["dividend"])


class DividendHolding(BaseModel):
    ticker: str
    shares: float = 0
    value: float = 0


class DividendRequest(BaseModel):
    holdings: List[DividendHolding]
    years_history: int = 5
    project_years: int = 10
    dividend_growth_assumption: float = 0.05


@router.post("/analyze")
def analyze(req: DividendRequest):
    try:
        holdings = [h.model_dump() for h in req.holdings]
        return analyze_dividends(
            holdings,
            req.years_history,
            req.project_years,
            req.dividend_growth_assumption,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
