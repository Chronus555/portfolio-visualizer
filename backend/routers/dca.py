from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from services.dca_service import simulate_dca

router = APIRouter(prefix="/api/dca", tags=["dca"])


class DCARequest(BaseModel):
    ticker: str = "SPY"
    monthly_amount: float = Field(default=500, gt=0)
    start_year: int = Field(default=2010, ge=1970, le=2024)
    end_year: Optional[int] = None


@router.post("/simulate")
def dca_simulate(req: DCARequest):
    return simulate_dca(
        ticker=req.ticker.upper().strip(),
        monthly_amount=req.monthly_amount,
        start_year=req.start_year,
        end_year=req.end_year,
    )
