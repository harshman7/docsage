"""
Anomaly detection for invoices and transactions.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Document, Transaction

class AnomalyDetector:
    """Detect anomalies in documents and transactions."""
    
    @staticmethod
    def detect_duplicates() -> List[Dict[str, Any]]:
        """Detect duplicate invoices/transactions."""
        anomalies = []
        db = SessionLocal()
        try:
            # Find transactions with same vendor, amount, and date
            duplicates = db.query(
                Transaction.vendor,
                Transaction.amount,
                Transaction.date,
                func.count(Transaction.id).label("count")
            ).group_by(
                Transaction.vendor,
                Transaction.amount,
                Transaction.date
            ).having(func.count(Transaction.id) > 1).all()
            
            for dup in duplicates:
                transactions = db.query(Transaction).filter(
                    Transaction.vendor == dup.vendor,
                    Transaction.amount == dup.amount,
                    Transaction.date == dup.date
                ).all()
                
                anomalies.append({
                    "type": "duplicate",
                    "severity": "high",
                    "message": f"Duplicate transaction: {dup.vendor} - ${dup.amount:.2f} on {dup.date}",
                    "count": dup.count,
                    "transaction_ids": [t.id for t in transactions],
                    "document_ids": [t.document_id for t in transactions]
                })
        finally:
            db.close()
        
        return anomalies
    
    @staticmethod
    def detect_unusual_amounts() -> List[Dict[str, Any]]:
        """Detect transactions with unusually high amounts."""
        anomalies = []
        db = SessionLocal()
        try:
            # Calculate vendor averages
            vendor_stats = db.query(
                Transaction.vendor,
                func.avg(Transaction.amount).label("avg_amount"),
                func.stddev(Transaction.amount).label("stddev_amount")
            ).group_by(Transaction.vendor).all()
            
            for vendor, avg_amt, stddev_amt in vendor_stats:
                if stddev_amt is None:
                    continue
                
                # Find transactions > 2 standard deviations above mean
                threshold = avg_amt + (2 * stddev_amt)
                unusual = db.query(Transaction).filter(
                    Transaction.vendor == vendor,
                    Transaction.amount > threshold
                ).all()
                
                for txn in unusual:
                    anomalies.append({
                        "type": "unusual_amount",
                        "severity": "medium",
                        "message": f"Unusually high amount for {vendor}: ${txn.amount:.2f} (avg: ${avg_amt:.2f})",
                        "transaction_id": txn.id,
                        "document_id": txn.document_id,
                        "amount": txn.amount,
                        "vendor_avg": float(avg_amt)
                    })
        finally:
            db.close()
        
        return anomalies
    
    @staticmethod
    def detect_missing_fields() -> List[Dict[str, Any]]:
        """Detect documents with missing critical fields."""
        anomalies = []
        db = SessionLocal()
        try:
            documents = db.query(Document).filter(
                Document.document_type == "invoice"
            ).all()
            
            for doc in documents:
                extracted = doc.extracted_data or {}
                issues = []
                
                if not extracted.get("vendor"):
                    issues.append("Missing vendor")
                if not extracted.get("total") or extracted.get("total") == 0:
                    issues.append("Missing total amount")
                if not extracted.get("invoice_number"):
                    issues.append("Missing invoice number")
                if not extracted.get("dates"):
                    issues.append("Missing date")
                
                if issues:
                    anomalies.append({
                        "type": "missing_fields",
                        "severity": "medium",
                        "message": f"Document {doc.filename} missing: {', '.join(issues)}",
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "missing_fields": issues
                    })
        finally:
            db.close()
        
        return anomalies
    
    @staticmethod
    def detect_date_anomalies() -> List[Dict[str, Any]]:
        """Detect future dates or very old invoices."""
        anomalies = []
        db = SessionLocal()
        try:
            now = datetime.now()
            future_threshold = now + timedelta(days=1)
            old_threshold = now - timedelta(days=365 * 5)  # 5 years old
            
            future_txns = db.query(Transaction).filter(
                Transaction.date > future_threshold
            ).all()
            
            old_txns = db.query(Transaction).filter(
                Transaction.date < old_threshold
            ).all()
            
            for txn in future_txns:
                anomalies.append({
                    "type": "future_date",
                    "severity": "high",
                    "message": f"Future date detected: {txn.date}",
                    "transaction_id": txn.id,
                    "document_id": txn.document_id,
                    "date": txn.date
                })
            
            for txn in old_txns:
                anomalies.append({
                    "type": "old_date",
                    "severity": "low",
                    "message": f"Very old transaction: {txn.date}",
                    "transaction_id": txn.id,
                    "document_id": txn.document_id,
                    "date": txn.date
                })
        finally:
            db.close()
        
        return anomalies
    
    @staticmethod
    def get_all_anomalies() -> List[Dict[str, Any]]:
        """Get all detected anomalies."""
        all_anomalies = []
        all_anomalies.extend(AnomalyDetector.detect_duplicates())
        all_anomalies.extend(AnomalyDetector.detect_unusual_amounts())
        all_anomalies.extend(AnomalyDetector.detect_missing_fields())
        all_anomalies.extend(AnomalyDetector.detect_date_anomalies())
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_anomalies.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))
        
        return all_anomalies

