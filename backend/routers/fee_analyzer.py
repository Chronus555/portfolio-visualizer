from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.fee_service import analyze_fees, lookup_expense_ratios

router = APIRouter(prefix="/api/fees", tags=["fees"])


class HoldingInput(BaseModel):
    ticker: str
    name: Optional[str] = None
    expense_ratio: Optional[float] = None   # decimal, e.g. 0.0003 for 0.03%
    value: float = 0


class FeeAnalysisRequest(BaseModel):
    holdings: List[HoldingInput]
    initial_amount: float = 100000
    years: int = 30
    annual_return: float = 0.07
    annual_contribution: float = 0
    advisor_fee: float = 0   # decimal AUM fee


@router.post("/analyze")
def fee_analysis(req: FeeAnalysisRequest):
    try:
        holdings = [h.model_dump() for h in req.holdings]
        return analyze_fees(
            holdings,
            req.initial_amount,
            req.years,
            req.annual_return,
            req.annual_contribution,
            req.advisor_fee,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lookup")
def lookup_ers(tickers: List[str]):
    try:
        return lookup_expense_ratios(tickers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
