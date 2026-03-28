from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Any, Dict
from services.report_service import generate_backtest_report, generate_portfolio_report

router = APIRouter(prefix="/api/report", tags=["report"])


class BacktestReportRequest(BaseModel):
    data: Dict[str, Any]
    title: str = "Portfolio Backtest Report"


class GenericReportRequest(BaseModel):
    report_type: str
    title: str
    data: Dict[str, Any]


@router.post("/backtest")
def backtest_pdf(req: BacktestReportRequest):
    try:
        pdf_bytes = generate_backtest_report(req.data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="backtest_report.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
def generic_pdf(req: GenericReportRequest):
    try:
        pdf_bytes = generate_portfolio_report(req.report_type, req.title, req.data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
