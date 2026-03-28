from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.stress_test_service import run_stress_test, SCENARIOS

router = APIRouter(prefix="/api/stress-test", tags=["stress-test"])


class Allocation(BaseModel):
    ticker: str
    weight: float


class StressTestRequest(BaseModel):
    allocations: List[Allocation]
    initial_amount: float = 100000
    scenario_ids: Optional[List[str]] = None


@router.get("/scenarios")
def list_scenarios():
    return [{"id": s["id"], "label": s["label"], "description": s["description"],
             "period": f"{s['start'][:7]} → {s['end'][:7]}"} for s in SCENARIOS]


@router.post("/run")
def run(req: StressTestRequest):
    try:
        allocs = [{"ticker": a.ticker, "weight": a.weight} for a in req.allocations]
        return run_stress_test(allocs, req.initial_amount, req.scenario_ids)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
