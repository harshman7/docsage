"""LLM-generated insights report."""
from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models import User
from app.services.insights_generator import generate_insights_report

router = APIRouter(prefix="/insights", tags=["insights-report"])


@router.post("/generate-report")
def generate_report(current_user: User = Depends(get_current_user)):
    return {"report_markdown": generate_insights_report(user_id=current_user.id)}
