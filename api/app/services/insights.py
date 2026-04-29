"""
Precomputed metrics: monthly spend, vendor stats, etc.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Transaction

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
    def get_time_series_data(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get time series data for spending trends."""
        with SessionLocal() as db:
            if not start_date:
                # Default to last 12 months
                end_date = end_date or datetime.now()
                start_date = end_date - timedelta(days=365)
            
            transactions = db.query(Transaction).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
            
            if not transactions:
                return {
                    "daily": [],
                    "monthly": [],
                    "vendor_trends": []
                }
            
            # Convert to DataFrame-like structure
            daily_data = {}
            monthly_data = {}
            vendor_monthly = {}
            
            for txn in transactions:
                date = txn.date
                if not date:
                    continue
                
                # Daily aggregation
                day_key = date.strftime("%Y-%m-%d")
                daily_data[day_key] = daily_data.get(day_key, 0) + txn.amount
                
                # Monthly aggregation
                month_key = date.strftime("%Y-%m")
                monthly_data[month_key] = monthly_data.get(month_key, 0) + txn.amount
                
                # Vendor monthly
                if txn.vendor:
                    vendor_key = f"{txn.vendor}|{month_key}"
                    vendor_monthly[vendor_key] = vendor_monthly.get(vendor_key, 0) + txn.amount
            
            # Format for frontend
            daily_list = [{"date": k, "amount": v} for k, v in sorted(daily_data.items())]
            monthly_list = [{"date": k, "amount": v} for k, v in sorted(monthly_data.items())]
            
            # Top vendors over time
            vendor_trends = {}
            for key, amount in vendor_monthly.items():
                vendor, month = key.split("|")
                if vendor not in vendor_trends:
                    vendor_trends[vendor] = []
                vendor_trends[vendor].append({"date": month, "amount": amount})
            
            # Get top 5 vendors
            vendor_totals = {v: sum(item["amount"] for item in items) for v, items in vendor_trends.items()}
            top_vendors = sorted(vendor_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            top_vendor_trends = {v: sorted(vendor_trends[v], key=lambda x: x["date"]) for v, _ in top_vendors}
            
            return {
                "daily": daily_list,
                "monthly": monthly_list,
                "vendor_trends": top_vendor_trends
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

