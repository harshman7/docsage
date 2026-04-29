"""
Document comparison tool - compare similar invoices side-by-side.
"""
from typing import List, Dict, Any, Tuple
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Document, Transaction

class DocumentComparator:
    """Compare documents and find similarities."""
    
    @staticmethod
    def find_similar_documents(document_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Find documents similar to the given one."""
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                return []
            
            extracted = doc.extracted_data or {}
            vendor = extracted.get("vendor")
            total = extracted.get("total")
            
            if not vendor:
                return []
            
            # Find documents with same vendor
            similar = db.query(Document).filter(
                Document.id != document_id,
                Document.document_type == doc.document_type
            ).all()
            
            results = []
            for sim_doc in similar:
                sim_extracted = sim_doc.extracted_data or {}
                sim_vendor = sim_extracted.get("vendor")
                sim_total = sim_extracted.get("total")
                
                # Calculate similarity score
                score = 0
                if sim_vendor and vendor and sim_vendor.lower() == vendor.lower():
                    score += 50
                
                if sim_total and total:
                    # Similar amounts (within 10%)
                    diff = abs(sim_total - total) / max(total, 1)
                    if diff < 0.1:
                        score += 30
                    elif diff < 0.5:
                        score += 15
                
                if score > 0:
                    results.append({
                        "document_id": sim_doc.id,
                        "filename": sim_doc.filename,
                        "vendor": sim_vendor,
                        "total": sim_total,
                        "invoice_number": sim_extracted.get("invoice_number"),
                        "date": sim_extracted.get("dates", [None])[0] if sim_extracted.get("dates") else None,
                        "similarity_score": score
                    })
            
            # Sort by similarity score
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:limit]
            
        finally:
            db.close()
    
    @staticmethod
    def compare_documents(doc1_id: int, doc2_id: int) -> Dict[str, Any]:
        """Compare two documents side-by-side."""
        db = SessionLocal()
        try:
            doc1 = db.query(Document).filter(Document.id == doc1_id).first()
            doc2 = db.query(Document).filter(Document.id == doc2_id).first()
            
            if not doc1 or not doc2:
                return {"error": "One or both documents not found"}
            
            extracted1 = doc1.extracted_data or {}
            extracted2 = doc2.extracted_data or {}
            
            comparison = {
                "document1": {
                    "id": doc1.id,
                    "filename": doc1.filename,
                    "vendor": extracted1.get("vendor"),
                    "total": extracted1.get("total"),
                    "invoice_number": extracted1.get("invoice_number"),
                    "date": extracted1.get("dates", [None])[0] if extracted1.get("dates") else None,
                },
                "document2": {
                    "id": doc2.id,
                    "filename": doc2.filename,
                    "vendor": extracted2.get("vendor"),
                    "total": extracted2.get("total"),
                    "invoice_number": extracted2.get("invoice_number"),
                    "date": extracted2.get("dates", [None])[0] if extracted2.get("dates") else None,
                },
                "differences": []
            }
            
            # Compare fields
            fields_to_compare = ["vendor", "total", "invoice_number"]
            for field in fields_to_compare:
                val1 = extracted1.get(field)
                val2 = extracted2.get(field)
                
                if val1 != val2:
                    if field == "total" and val1 and val2:
                        diff = abs(val1 - val2)
                        pct_diff = (diff / max(val1, 1)) * 100
                        comparison["differences"].append({
                            "field": field,
                            "value1": val1,
                            "value2": val2,
                            "difference": diff,
                            "percent_difference": round(pct_diff, 2)
                        })
                    else:
                        comparison["differences"].append({
                            "field": field,
                            "value1": val1,
                            "value2": val2
                        })
            
            return comparison
            
        finally:
            db.close()
    
    @staticmethod
    def detect_price_changes(vendor: str) -> List[Dict[str, Any]]:
        """Detect price changes for a specific vendor over time."""
        db = SessionLocal()
        try:
            # Get all documents for this vendor
            docs = db.query(Document).join(Transaction).filter(
                Transaction.vendor == vendor
            ).distinct().all()
            
            if len(docs) < 2:
                return []
            
            price_history = []
            for doc in docs:
                extracted = doc.extracted_data or {}
                total = extracted.get("total")
                date = extracted.get("dates", [None])[0] if extracted.get("dates") else None
                
                if total and date:
                    price_history.append({
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "date": date,
                        "amount": total
                    })
            
            # Sort by date
            price_history.sort(key=lambda x: x["date"] if x["date"] else "")
            
            # Calculate changes
            changes = []
            for i in range(1, len(price_history)):
                prev = price_history[i-1]
                curr = price_history[i]
                
                if prev["amount"] and curr["amount"]:
                    change = curr["amount"] - prev["amount"]
                    pct_change = (change / prev["amount"]) * 100 if prev["amount"] > 0 else 0
                    
                    changes.append({
                        "from_date": prev["date"],
                        "to_date": curr["date"],
                        "from_amount": prev["amount"],
                        "to_amount": curr["amount"],
                        "change": change,
                        "percent_change": round(pct_change, 2),
                        "from_document": prev["filename"],
                        "to_document": curr["filename"]
                    })
            
            return changes
            
        finally:
            db.close()

