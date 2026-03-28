from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.budget_service import analyze_budget

router = APIRouter(prefix="/api/budget", tags=["budget"])


class Expense(BaseModel):
    category: str
    amount: float = Field(..., ge=0)
    type: Optional[str] = None   # "needs" | "wants" | "savings"


class BudgetRequest(BaseModel):
    monthly_income: float = Field(..., gt=0)
    expenses: List[Expense]
    existing_savings: float = Field(0.0, ge=0)
    emergency_fund: float = Field(0.0, ge=0)
    projection_years: int = Field(30, ge=1, le=50)
    expected_return: float = Field(7.0, ge=0, le=30)


@router.post("/analyze")
async def budget_analyze(req: BudgetRequest):
    try:
        return analyze_budget(
            monthly_income=req.monthly_income,
            expenses=[e.model_dump() for e in req.expenses],
            existing_savings=req.existing_savings,
            emergency_fund=req.emergency_fund,
            projection_years=req.projection_years,
            expected_return=req.expected_return,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
