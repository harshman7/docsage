"""
Anomaly detection for invoices and transactions.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Document, Transaction


class AnomalyDetector:
    """Detect anomalies in documents and transactions."""

    @staticmethod
    def _is_kaggle_synthetic(db, document_id: Optional[int]) -> bool:
        if document_id is None:
            return False
        row = (
            db.query(Document.file_path)
            .filter(Document.id == document_id)
            .first()
        )
        fp = row[0] if row else None
        return bool(fp and fp.startswith("kaggle://"))

    @staticmethod
    def detect_duplicates(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        anomalies = []
        db = SessionLocal()
        try:
            q = db.query(
                Transaction.vendor,
                Transaction.amount,
                Transaction.date,
                func.count(Transaction.id).label("count")
            )
            if user_id is not None:
                q = q.filter(Transaction.user_id == user_id)
            duplicates = q.group_by(
                Transaction.vendor, Transaction.amount, Transaction.date
            ).having(func.count(Transaction.id) > 1).all()

            for dup in duplicates:
                tq = db.query(Transaction).filter(
                    Transaction.vendor == dup.vendor,
                    Transaction.amount == dup.amount,
                    Transaction.date == dup.date
                )
                if user_id is not None:
                    tq = tq.filter(Transaction.user_id == user_id)
                transactions = tq.all()
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
    def detect_unusual_amounts(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        anomalies = []
        db = SessionLocal()
        try:
            q = db.query(
                Transaction.vendor,
                func.avg(Transaction.amount).label("avg_amount"),
                func.stddev(Transaction.amount).label("stddev_amount")
            )
            if user_id is not None:
                q = q.filter(Transaction.user_id == user_id)
            vendor_stats = q.group_by(Transaction.vendor).all()

            for vendor, avg_amt, stddev_amt in vendor_stats:
                if stddev_amt is None:
                    continue
                threshold = avg_amt + (2 * stddev_amt)
                uq = db.query(Transaction).filter(
                    Transaction.vendor == vendor,
                    Transaction.amount > threshold
                )
                if user_id is not None:
                    uq = uq.filter(Transaction.user_id == user_id)
                for txn in uq.all():
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
    def detect_missing_fields(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        anomalies = []
        db = SessionLocal()
        try:
            q = db.query(Document).filter(Document.document_type == "invoice")
            if user_id is not None:
                q = q.filter(Document.user_id == user_id)
            documents = q.all()

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
    def detect_date_anomalies(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        anomalies = []
        db = SessionLocal()
        try:
            now = datetime.now()
            future_threshold = now + timedelta(days=1)
            old_threshold = now - timedelta(days=365 * 5)

            fq = db.query(Transaction).filter(Transaction.date > future_threshold)
            oq = db.query(Transaction).filter(Transaction.date < old_threshold)
            if user_id is not None:
                fq = fq.filter(Transaction.user_id == user_id)
                oq = oq.filter(Transaction.user_id == user_id)

            for txn in fq.all():
                if AnomalyDetector._is_kaggle_synthetic(db, txn.document_id):
                    continue
                anomalies.append({
                    "type": "future_date",
                    "severity": "high",
                    "message": f"Future date detected: {txn.date}",
                    "transaction_id": txn.id,
                    "document_id": txn.document_id,
                    "date": txn.date
                })

            for txn in oq.all():
                if AnomalyDetector._is_kaggle_synthetic(db, txn.document_id):
                    continue
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
    def get_all_anomalies(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        all_anomalies = []
        all_anomalies.extend(AnomalyDetector.detect_duplicates(user_id=user_id))
        all_anomalies.extend(AnomalyDetector.detect_unusual_amounts(user_id=user_id))
        all_anomalies.extend(AnomalyDetector.detect_missing_fields(user_id=user_id))
        all_anomalies.extend(AnomalyDetector.detect_date_anomalies(user_id=user_id))
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_anomalies.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))
        return all_anomalies

