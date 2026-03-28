from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.retirement_service import run_retirement_plan

router = APIRouter(prefix="/api/retirement", tags=["retirement"])


class RetirementRequest(BaseModel):
    current_age: int = Field(35, ge=18, le=80)
    retirement_age: int = Field(65, ge=30, le=90)
    life_expectancy: int = Field(90, ge=60, le=110)
    current_savings: float = Field(100_000, ge=0)
    annual_contribution: float = Field(20_000, ge=0)
    contribution_growth: float = Field(2.0, ge=0, le=10)
    expected_return: float = Field(7.0, ge=0, le=30)
    volatility: float = Field(15.0, ge=1, le=50)
    inflation: float = Field(3.0, ge=0, le=15)
    annual_expenses_in_retirement: float = Field(80_000, ge=0)
    social_security: float = Field(0.0, ge=0)
    simulations: int = Field(1000, ge=100, le=10000)


@router.post("/plan")
async def plan_retirement(req: RetirementRequest):
    if req.retirement_age <= req.current_age:
        raise HTTPException(400, "Retirement age must be greater than current age")
    if req.life_expectancy <= req.retirement_age:
        raise HTTPException(400, "Life expectancy must be greater than retirement age")
    try:
        return run_retirement_plan(**req.model_dump())
    except Exception as e:
        raise HTTPException(500, str(e))
