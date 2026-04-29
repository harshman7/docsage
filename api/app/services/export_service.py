"""
Export service for generating Excel and PDF reports.
"""
import pandas as pd
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Transaction, Document
from app.services.insights import InsightsService
from app.services.anomaly_detection import AnomalyDetector

def export_to_excel(output_path: Optional[str] = None) -> BytesIO:
    """
    Export all data to Excel with multiple sheets.
    
    Returns:
        BytesIO object with Excel file
    """
    db = SessionLocal()
    try:
        # Create Excel writer
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: All Transactions
            transactions = db.query(Transaction).all()
            txn_data = [{
                "ID": t.id,
                "Date": t.date,
                "Vendor": t.vendor,
                "Amount": t.amount,
                "Category": t.category,
                "Description": t.description,
                "Document ID": t.document_id
            } for t in transactions]
            
            if txn_data:
                df_txns = pd.DataFrame(txn_data)
                df_txns.to_excel(writer, sheet_name="Transactions", index=False)
            
            # Sheet 2: Vendor Statistics
            vendor_stats = InsightsService.get_vendor_stats(limit=50)
            if vendor_stats:
                df_vendors = pd.DataFrame(vendor_stats)
                df_vendors.to_excel(writer, sheet_name="Vendor Stats", index=False)
            
            # Sheet 3: Category Breakdown
            category_breakdown = InsightsService.get_category_breakdown()
            if category_breakdown:
                df_categories = pd.DataFrame(category_breakdown)
                df_categories.to_excel(writer, sheet_name="Category Breakdown", index=False)
            
            # Sheet 4: Anomalies
            anomalies = AnomalyDetector.get_all_anomalies()
            if anomalies:
                # Flatten anomaly data
                anomaly_data = []
                for anom in anomalies:
                    row = {
                        "Type": anom.get("type"),
                        "Severity": anom.get("severity"),
                        "Message": anom.get("message")
                    }
                    if "transaction_id" in anom:
                        row["Transaction ID"] = anom["transaction_id"]
                    if "document_id" in anom:
                        row["Document ID"] = anom["document_id"]
                    anomaly_data.append(row)
                
                df_anomalies = pd.DataFrame(anomaly_data)
                df_anomalies.to_excel(writer, sheet_name="Anomalies", index=False)
            
            # Sheet 5: Documents Summary
            documents = db.query(Document).all()
            doc_data = [{
                "ID": d.id,
                "Filename": d.filename,
                "Type": d.document_type,
                "Vendor": (d.extracted_data or {}).get("vendor"),
                "Total": (d.extracted_data or {}).get("total"),
                "Invoice #": (d.extracted_data or {}).get("invoice_number"),
                "Created": d.created_at
            } for d in documents]
            
            if doc_data:
                df_docs = pd.DataFrame(doc_data)
                df_docs.to_excel(writer, sheet_name="Documents", index=False)
        
        output.seek(0)
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(output.read())
            output.seek(0)
        
        return output
        
    finally:
        db.close()

def export_summary_report() -> str:
    """
    Generate a text summary report.
    
    Returns:
        Markdown formatted report string
    """
    db = SessionLocal()
    try:
        total_txns = db.query(Transaction).count()
        total_spend = db.query(func.sum(Transaction.amount)).scalar() or 0
        
        vendor_stats = InsightsService.get_vendor_stats(limit=10)
        category_breakdown = InsightsService.get_category_breakdown()
        anomalies = AnomalyDetector.get_all_anomalies()
        
        report = f"""# Expense Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- **Total Transactions**: {total_txns}
- **Total Spending**: ${total_spend:,.2f}

## Top Vendors
"""
        for i, vendor in enumerate(vendor_stats[:10], 1):
            report += f"{i}. {vendor['vendor']}: ${vendor['total_spend']:,.2f} ({vendor['transaction_count']} transactions)\n"
        
        report += "\n## Category Breakdown\n"
        for cat in category_breakdown[:10]:
            report += f"- {cat['category']}: ${cat['total_spend']:,.2f}\n"
        
        report += f"\n## Anomalies Detected\n"
        report += f"- Total Issues: {len(anomalies)}\n"
        report += f"- High Priority: {len([a for a in anomalies if a.get('severity') == 'high'])}\n"
        report += f"- Medium Priority: {len([a for a in anomalies if a.get('severity') == 'medium'])}\n"
        
        return report
        
    finally:
        db.close()

