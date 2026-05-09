"""
Precomputed metrics: monthly spend, vendor stats, etc.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Transaction

# Presets aligned with dashboard query params
TIME_SERIES_PRESETS = frozenset(
    {"all", "last_12_months", "last_3_years", "last_5_years"}
)
GRANULARITIES = frozenset({"auto", "month", "year"})

class InsightsService:
    """Service for computing insights from transaction data."""
    
    @staticmethod
    def get_monthly_spend(year: int, month: int) -> Dict[str, Any]:
        """Calculate total spend for a specific month."""
        with SessionLocal() as db:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            result = db.query(
                func.sum(Transaction.amount).label("total_spend"),
                func.count(Transaction.id).label("transaction_count")
            ).filter(
                Transaction.date >= start_date,
                Transaction.date < end_date
            ).first()
            
            return {
                "year": year,
                "month": month,
                "total_spend": float(result.total_spend or 0),
                "transaction_count": result.transaction_count
            }
    
    @staticmethod
    def get_vendor_stats(limit: int = 10) -> List[Dict[str, Any]]:
        """Get statistics by vendor."""
        with SessionLocal() as db:
            results = db.query(
                Transaction.vendor,
                func.sum(Transaction.amount).label("total_spend"),
                func.count(Transaction.id).label("transaction_count"),
                func.avg(Transaction.amount).label("avg_amount")
            ).group_by(Transaction.vendor).order_by(
                func.sum(Transaction.amount).desc()
            ).limit(limit).all()
            
            return [
                {
                    "vendor": row.vendor,
                    "total_spend": float(row.total_spend),
                    "transaction_count": row.transaction_count,
                    "avg_amount": float(row.avg_amount)
                }
                for row in results
            ]
    
    @staticmethod
    def get_category_breakdown() -> List[Dict[str, Any]]:
        """Get spending breakdown by category."""
        with SessionLocal() as db:
            results = db.query(
                Transaction.category,
                func.sum(Transaction.amount).label("total_spend"),
                func.count(Transaction.id).label("transaction_count")
            ).group_by(Transaction.category).order_by(
                func.sum(Transaction.amount).desc()
            ).all()
            
            return [
                {
                    "category": row.category or "Uncategorized",
                    "total_spend": float(row.total_spend),
                    "transaction_count": row.transaction_count
                }
                for row in results
            ]
    
    @staticmethod
    def _resolve_time_window(
        db,
        preset: str,
        start_override: Optional[datetime],
        end_override: Optional[datetime],
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Return inclusive [start, end] for Transaction.date filtering."""
        now = datetime.now()

        if start_override is not None and end_override is not None:
            return start_override, end_override

        if preset == "all":
            row = (
                db.query(
                    func.min(Transaction.date).label("dmin"),
                    func.max(Transaction.date).label("dmax"),
                )
                .filter(Transaction.date.isnot(None))
                .first()
            )
            if row is None or row.dmin is None:
                return None, None
            return row.dmin, row.dmax

        if preset == "last_12_months":
            return now - timedelta(days=365), now
        if preset == "last_3_years":
            return now - timedelta(days=365 * 3), now
        if preset == "last_5_years":
            return now - timedelta(days=365 * 5), now

        row = (
            db.query(
                func.min(Transaction.date).label("dmin"),
                func.max(Transaction.date).label("dmax"),
            )
            .filter(Transaction.date.isnot(None))
            .first()
        )
        if row is None or row.dmin is None:
            return None, None
        return row.dmin, row.dmax

    @staticmethod
    def get_time_series_data(
        preset: str = "all",
        granularity: str = "auto",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Spending time series with presets, optional custom range, and month/year granularity.

        preset: all | last_12_months | last_3_years | last_5_years
        granularity: auto (year if span > 3y else month) | month | year
        start/end: optional inclusive bounds (override preset when both set)
        """
        preset = preset if preset in TIME_SERIES_PRESETS else "all"
        granularity = granularity if granularity in GRANULARITIES else "auto"

        with SessionLocal() as db:
            without_date = (
                db.query(func.count(Transaction.id))
                .filter(Transaction.date.is_(None))
                .scalar()
                or 0
            )

            start_date, end_date = InsightsService._resolve_time_window(
                db, preset, start, end
            )
            if start_date is None or end_date is None:
                return {
                    "daily": [],
                    "monthly": [],
                    "yearly": [],
                    "granularity": "month",
                    "range": {"start": None, "end": None},
                    "transactions_in_range": 0,
                    "transactions_without_date": int(without_date),
                    "vendor_trends": {},
                }

            transactions = (
                db.query(Transaction)
                .filter(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                )
                .all()
            )

            span_days = (end_date - start_date).days + 1
            if granularity == "auto":
                resolved = "year" if span_days > 3 * 365 else "month"
            elif granularity == "year":
                resolved = "year"
            else:
                resolved = "month"

            daily_data: Dict[str, float] = {}
            monthly_data: Dict[str, float] = {}
            yearly_data: Dict[str, float] = {}
            vendor_monthly: Dict[str, float] = {}

            for txn in transactions:
                d = txn.date
                if not d:
                    continue

                day_key = d.strftime("%Y-%m-%d")
                daily_data[day_key] = daily_data.get(day_key, 0) + txn.amount
                month_key = d.strftime("%Y-%m")
                monthly_data[month_key] = monthly_data.get(month_key, 0) + txn.amount
                year_key = d.strftime("%Y")
                yearly_data[year_key] = yearly_data.get(year_key, 0) + txn.amount

                if txn.vendor:
                    vk = f"{txn.vendor}|{month_key}"
                    vendor_monthly[vk] = vendor_monthly.get(vk, 0) + txn.amount

            daily_list: List[Dict[str, Any]] = []
            if span_days <= 366:
                daily_list = [
                    {"date": k, "amount": v} for k, v in sorted(daily_data.items())
                ]

            monthly_list = [
                {"date": k, "amount": v} for k, v in sorted(monthly_data.items())
            ]
            yearly_list = [
                {"date": k, "amount": v} for k, v in sorted(yearly_data.items())
            ]

            vendor_trends: Dict[str, List[Dict[str, Any]]] = {}
            for key, amount in vendor_monthly.items():
                vendor_name, month = key.rsplit("|", 1)
                if vendor_name not in vendor_trends:
                    vendor_trends[vendor_name] = []
                vendor_trends[vendor_name].append({"date": month, "amount": amount})

            vendor_totals = {
                v: sum(item["amount"] for item in items)
                for v, items in vendor_trends.items()
            }
            top_vendors = sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            top_vendor_trends = {
                v: sorted(vendor_trends[v], key=lambda x: x["date"]) for v, _ in top_vendors
            }

            return {
                "daily": daily_list,
                "monthly": monthly_list,
                "yearly": yearly_list,
                "granularity": resolved,
                "range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "transactions_in_range": len(transactions),
                "transactions_without_date": int(without_date),
                "vendor_trends": top_vendor_trends,
            }
    
    @staticmethod
    def get_spending_forecast(months: int = 3) -> Dict[str, Any]:
        """Simple linear regression forecast for future spending."""
        with SessionLocal() as db:
            # Get last 6 months of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            transactions = db.query(Transaction).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
            
            if len(transactions) < 2:
                return {"forecast": [], "trend": "insufficient_data"}
            
            # Group by month
            monthly_totals = {}
            for txn in transactions:
                if txn.date:
                    month_key = txn.date.strftime("%Y-%m")
                    monthly_totals[month_key] = monthly_totals.get(month_key, 0) + txn.amount
            
            if len(monthly_totals) < 2:
                return {"forecast": [], "trend": "insufficient_data"}
            
            # Simple linear trend
            sorted_months = sorted(monthly_totals.keys())
            amounts = [monthly_totals[m] for m in sorted_months]
            
            # Calculate trend
            n = len(amounts)
            if n > 1:
                avg_change = (amounts[-1] - amounts[0]) / (n - 1) if n > 1 else 0
                last_amount = amounts[-1]
                
                forecast = []
                for i in range(1, months + 1):
                    predicted = last_amount + (avg_change * i)
                    forecast.append({
                        "month": i,
                        "predicted_amount": max(0, predicted)  # Don't predict negative
                    })
                
                trend = "increasing" if avg_change > 0 else "decreasing" if avg_change < 0 else "stable"
                
                return {
                    "forecast": forecast,
                    "trend": trend,
                    "monthly_change": float(avg_change)
                }
            
            return {"forecast": [], "trend": "insufficient_data"}

