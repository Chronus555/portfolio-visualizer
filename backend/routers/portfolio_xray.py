from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List
from services.portfolio_xray_service import xray_portfolio

router = APIRouter(prefix="/api/xray", tags=["xray"])


class Holding(BaseModel):
    ticker: str
    weight: float = Field(gt=0)


class XRayRequest(BaseModel):
    holdings: List[Holding]


@router.post("/analyze")
def xray_analyze(req: XRayRequest):
    return xray_portfolio([{"ticker": h.ticker, "weight": h.weight} for h in req.holdings])
