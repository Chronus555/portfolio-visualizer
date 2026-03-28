from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.tax_service import scan_tax_harvest

router = APIRouter(prefix="/api/tax", tags=["tax"])


class PositionInput(BaseModel):
    ticker: str
    name: Optional[str] = None
    shares: float
    cost_basis: float          # per-share cost basis
    purchase_date: Optional[str] = None   # YYYY-MM-DD


class TaxHarvestRequest(BaseModel):
    positions: List[PositionInput]
    tax_rate_st: float = 0.37   # short-term ordinary income rate
    tax_rate_lt: float = 0.20   # long-term capital gains rate
    state_tax_rate: float = 0.0


@router.post("/harvest-scan")
def harvest_scan(req: TaxHarvestRequest):
    try:
        positions = [p.model_dump() for p in req.positions]
        return scan_tax_harvest(
            positions,
            req.tax_rate_st,
            req.tax_rate_lt,
            req.state_tax_rate,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
