from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from services.roth_service import compare_roth_vs_traditional, optimize_roth_conversion

router = APIRouter(prefix="/api/roth", tags=["roth"])


class RothCompareRequest(BaseModel):
    current_income: float = Field(gt=0)
    retirement_income: float = Field(gt=0)
    annual_contribution: float = Field(gt=0)
    years_to_retirement: int = Field(ge=1, le=60)
    years_in_retirement: int = Field(default=25, ge=1, le=50)
    expected_return: float = Field(default=7.0, ge=0, le=30)


class RothConversionRequest(BaseModel):
    trad_balance: float = Field(gt=0)
    current_income: float = Field(gt=0)
    top_bracket_ceiling: float = Field(gt=0)
    expected_return: float = Field(default=7.0, ge=0, le=30)
    years_to_retirement: int = Field(ge=1, le=60)
    retirement_rate: float = Field(default=22.0, ge=0, le=50)


@router.post("/compare")
def roth_compare(req: RothCompareRequest):
    return compare_roth_vs_traditional(
        current_income=req.current_income,
        retirement_income=req.retirement_income,
        annual_contribution=req.annual_contribution,
        years_to_retirement=req.years_to_retirement,
        years_in_retirement=req.years_in_retirement,
        expected_return=req.expected_return,
    )


@router.post("/conversion")
def roth_conversion(req: RothConversionRequest):
    return optimize_roth_conversion(
        trad_balance=req.trad_balance,
        current_income=req.current_income,
        top_bracket_ceiling=req.top_bracket_ceiling,
        expected_return=req.expected_return,
        years_to_retirement=req.years_to_retirement,
        retirement_rate=req.retirement_rate,
    )
