from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from services.loan_service import analyze_loan

router = APIRouter(prefix="/api/loan", tags=["loan"])


class LoanRequest(BaseModel):
    principal: float = Field(gt=0)
    annual_rate: float = Field(ge=0)
    years: int = Field(ge=1, le=50)
    extra_monthly: float = Field(default=0, ge=0)
    property_value: Optional[float] = None
    monthly_rent: Optional[float] = None
    home_appreciation: float = Field(default=3.0)
    new_rate: Optional[float] = None
    closing_costs: float = Field(default=0, ge=0)


@router.post("/analyze")
def loan_analyze(req: LoanRequest):
    return analyze_loan(
        principal=req.principal,
        annual_rate=req.annual_rate,
        years=req.years,
        extra_monthly=req.extra_monthly,
        property_value=req.property_value,
        monthly_rent=req.monthly_rent,
        home_appreciation=req.home_appreciation,
        new_rate=req.new_rate,
        closing_costs=req.closing_costs,
    )
