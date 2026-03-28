from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from services.bond_service import analyze_bond

router = APIRouter(prefix="/api/bond", tags=["bond"])


class BondRequest(BaseModel):
    face: float = Field(default=1000, gt=0)
    coupon_rate: float = Field(gt=0, le=1, description="Annual coupon rate as decimal, e.g. 0.05 = 5%")
    years: int = Field(ge=1, le=100)
    price: Optional[float] = Field(default=None, gt=0)
    ytm: Optional[float] = Field(default=None, gt=0, le=2, description="YTM as decimal")
    freq: int = Field(default=2, description="Coupon payments per year: 1=annual, 2=semiannual, 4=quarterly")
    inflation: float = Field(default=2.5, ge=0, le=20)


@router.post("/analyze")
def bond_analyze(req: BondRequest):
    return analyze_bond(
        face=req.face,
        coupon_rate=req.coupon_rate,
        years=req.years,
        price=req.price,
        ytm=req.ytm,
        freq=req.freq,
        inflation=req.inflation,
    )
