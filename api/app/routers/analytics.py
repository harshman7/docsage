"""Dashboard analytics endpoints."""
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Query
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
def time_series(
    preset: str = Query(
        "all",
        description="Time window: all, last_12_months, last_3_years, last_5_years",
    ),
    granularity: str = Query(
        "auto",
        description="Bucket size: auto, month, year (auto uses year if span > 3 years)",
    ),
    start: Optional[date] = Query(
        None, description="Inclusive range start (override preset when both start and end set)"
    ),
    end: Optional[date] = Query(
        None, description="Inclusive range end (override preset when both start and end set)"
    ),
):
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    if start is not None and end is not None:
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
    return InsightsService.get_time_series_data(
        preset=preset,
        granularity=granularity,
        start=start_dt,
        end=end_dt,
    )


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
