"""
Natural language insights generator using LLM.
"""
import json
from app.services.llm_service import call_llm
from app.services.insights import InsightsService
from app.services.anomaly_detection import AnomalyDetector
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Transaction

def generate_insights_report() -> str:
    """Generate a natural language insights report."""
    
    # Gather data
    vendor_stats = InsightsService.get_vendor_stats(limit=5)
    category_breakdown = InsightsService.get_category_breakdown()
    anomalies = AnomalyDetector.get_all_anomalies()
    forecast = InsightsService.get_spending_forecast()
    
    # Get transaction summary
    db = SessionLocal()
    try:
        total_txns = db.query(Transaction).count()
        total_spend = db.query(func.sum(Transaction.amount)).scalar() or 0
    finally:
        db.close()
    
    # Build context for LLM
    context = f"""Analyze this business expense data and generate insights:

SUMMARY:
- Total Transactions: {total_txns}
- Total Spending: ${total_spend:,.2f}

TOP VENDORS:
{json.dumps(vendor_stats, indent=2)}

CATEGORY BREAKDOWN:
{json.dumps(category_breakdown[:5], indent=2)}

ANOMALIES DETECTED:
- {len(anomalies)} issues found
- High priority: {len([a for a in anomalies if a.get('severity') == 'high'])}
- Medium priority: {len([a for a in anomalies if a.get('severity') == 'medium'])}

SPENDING TREND:
- Trend: {forecast.get('trend', 'unknown')}
- Monthly change: ${forecast.get('monthly_change', 0):,.2f}

Generate a concise business insights report (3-4 paragraphs) covering:
1. Key spending patterns and trends
2. Top categories and vendors
3. Important anomalies or concerns
4. Recommendations for cost optimization

Format as markdown with clear sections."""

    try:
        # Call LLM (supports Ollama, Groq, Hugging Face)
        report = call_llm(context, timeout=30).strip()
        return report
        
    except Exception:
        # Fallback report
        return f"""# Business Expense Insights Report

## Summary
- **Total Transactions**: {total_txns}
- **Total Spending**: ${total_spend:,.2f}

## Top Spending Categories
{chr(10).join([f"- {cat['category']}: ${cat['total_spend']:,.2f}" for cat in category_breakdown[:5]])}

## Top Vendors
{chr(10).join([f"- {v['vendor']}: ${v['total_spend']:,.2f} ({v['transaction_count']} transactions)" for v in vendor_stats[:5]])}

## Anomalies
- {len(anomalies)} issues detected requiring attention
- Review duplicate transactions and unusual amounts

## Recommendations
- Monitor spending trends monthly
- Review top vendors for contract optimization
- Address detected anomalies promptly
"""

