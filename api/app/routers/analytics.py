"""Dashboard analytics endpoints."""
from fastapi import APIRouter
from sqlalchemy import func
from app.services.insights import InsightsService
from app.db import SessionLocal
from app.models import Transaction, Document
from app.schemas import DashboardSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=DashboardSummary)
def summary():
    db = SessionLocal()
    try:
        total_txns = db.query(Transaction).count()
        total_spend = db.query(func.sum(Transaction.amount)).scalar() or 0.0
        avg_transaction = (
            float(total_spend) / total_txns if total_txns > 0 else 0.0
        )
        doc_count = db.query(Document).count()
        return DashboardSummary(
            total_transactions=total_txns,
            total_spend=float(total_spend),
            avg_transaction=avg_transaction,
            document_count=doc_count,
        )
    finally:
        db.close()


@router.get("/time-series")
def time_series():
    return InsightsService.get_time_series_data()


@router.get("/vendor-stats")
def vendor_stats(limit: int = 10):
    return InsightsService.get_vendor_stats(limit=limit)


@router.get("/category-breakdown")
def category_breakdown():
    return InsightsService.get_category_breakdown()


@router.get("/spending-forecast")
def forecast(months: int = 3):
    return InsightsService.get_spending_forecast(months=months)


@router.get("/monthly-spend")
def monthly_spend(year: int, month: int):
    return InsightsService.get_monthly_spend(year, month)
