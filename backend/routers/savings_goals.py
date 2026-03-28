from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.savings_service import analyze_savings_goals

router = APIRouter(prefix="/api/savings", tags=["savings"])


class SavingsGoal(BaseModel):
    type: str = "custom"
    name: str
    target_amount: float = Field(..., gt=0)
    deadline_years: float = Field(..., gt=0)
    current_savings: float = Field(0.0, ge=0)
    monthly_contribution: float = Field(0.0, ge=0)
    expected_return: float = Field(6.0, ge=0, le=30)
    priority: Optional[str] = "medium"


class SavingsRequest(BaseModel):
    goals: List[SavingsGoal]


@router.post("/goals")
async def project_goals(req: SavingsRequest):
    if not req.goals:
        raise HTTPException(400, "At least one goal is required")
    try:
        return analyze_savings_goals([g.model_dump() for g in req.goals])
    except Exception as e:
        raise HTTPException(500, str(e))
