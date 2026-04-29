"""LLM-generated insights report."""
from fastapi import APIRouter
from app.services.insights_generator import generate_insights_report

router = APIRouter(prefix="/insights", tags=["insights-report"])


@router.post("/generate-report")
def generate_report():
    return {"report_markdown": generate_insights_report()}
