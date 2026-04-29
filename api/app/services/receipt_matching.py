"""
Receipt-to-Invoice matching service.
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Document, Transaction

class ReceiptMatcher:
    """Match receipts to invoices automatically."""
    
    @staticmethod
    def find_matching_invoice(
        receipt_vendor: Optional[str] = None,
        receipt_amount: Optional[float] = None,
        receipt_date: Optional[datetime] = None,
        tolerance_days: int = 30,
        tolerance_amount: float = 0.05  # 5% tolerance
    ) -> List[Dict[str, Any]]:
        """
        Find invoices that match a receipt.
        
        Args:
            receipt_vendor: Vendor name from receipt
            receipt_amount: Amount from receipt
            receipt_date: Date from receipt
            tolerance_days: Days tolerance for date matching
            tolerance_amount: Amount tolerance (0.05 = 5%)
            
        Returns:
            List of matching invoices with confidence scores
        """
        db = SessionLocal()
        try:
            # Get all invoices
            invoices = db.query(Document).filter(
                Document.document_type == "invoice"
            ).all()
            
            matches = []
            
            for invoice in invoices:
                extracted = invoice.extracted_data or {}
                invoice_vendor = extracted.get("vendor")
                invoice_total = extracted.get("total")
                invoice_dates = extracted.get("dates", [])
                invoice_date = None
                if invoice_dates:
                    try:
                        invoice_date = datetime.strptime(invoice_dates[0], "%m/%d/%Y")
                    except:
                        pass
                
                confidence = 0.0
                match_reasons = []
                
                # Vendor matching (fuzzy)
                if receipt_vendor and invoice_vendor:
                    vendor_similarity = _fuzzy_match(receipt_vendor, invoice_vendor)
                    if vendor_similarity > 0.7:
                        confidence += 40 * vendor_similarity
                        match_reasons.append(f"Vendor match ({vendor_similarity:.0%})")
                
                # Amount matching
                if receipt_amount and invoice_total:
                    amount_diff = abs(receipt_amount - invoice_total)
                    amount_tolerance = invoice_total * tolerance_amount
                    if amount_diff <= amount_tolerance:
                        amount_score = 1.0 - (amount_diff / amount_tolerance)
                        confidence += 40 * amount_score
                        match_reasons.append(f"Amount match (diff: ${amount_diff:.2f})")
                    elif amount_diff <= invoice_total * 0.1:  # Within 10%
                        amount_score = 0.5
                        confidence += 20 * amount_score
                        match_reasons.append(f"Amount close (diff: ${amount_diff:.2f})")
                
                # Date matching
                if receipt_date and invoice_date:
                    date_diff = abs((receipt_date - invoice_date).days)
                    if date_diff <= tolerance_days:
                        date_score = 1.0 - (date_diff / tolerance_days)
                        confidence += 20 * date_score
                        match_reasons.append(f"Date match ({date_diff} days)")
                
                if confidence > 30:  # Minimum threshold
                    matches.append({
                        "invoice_id": invoice.id,
                        "invoice_filename": invoice.filename,
                        "invoice_vendor": invoice_vendor,
                        "invoice_total": invoice_total,
                        "invoice_date": invoice_date.strftime("%Y-%m-%d") if invoice_date else None,
                        "confidence": round(confidence, 2),
                        "match_reasons": match_reasons
                    })
            
            # Sort by confidence
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            return matches
            
        finally:
            db.close()
    
    @staticmethod
    def match_receipt_to_invoice(receipt_doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Match a receipt document to an invoice.
        
        Args:
            receipt_doc_id: ID of the receipt document
            
        Returns:
            Best matching invoice or None
        """
        db = SessionLocal()
        try:
            receipt = db.query(Document).filter(Document.id == receipt_doc_id).first()
            if not receipt or receipt.document_type != "receipt":
                return None
            
            extracted = receipt.extracted_data or {}
            receipt_vendor = extracted.get("vendor")
            receipt_amount = extracted.get("total")
            receipt_dates = extracted.get("dates", [])
            receipt_date = None
            if receipt_dates:
                try:
                    receipt_date = datetime.strptime(receipt_dates[0], "%m/%d/%Y")
                except:
                    pass
            
            matches = ReceiptMatcher.find_matching_invoice(
                receipt_vendor=receipt_vendor,
                receipt_amount=receipt_amount,
                receipt_date=receipt_date
            )
            
            if matches and matches[0]["confidence"] > 50:
                return matches[0]
            
            return None
            
        finally:
            db.close()
    
    @staticmethod
    def get_unmatched_receipts() -> List[Dict[str, Any]]:
        """Get all receipts that haven't been matched to invoices."""
        db = SessionLocal()
        try:
            receipts = db.query(Document).filter(
                Document.document_type == "receipt"
            ).all()
            
            unmatched = []
            for receipt in receipts:
                # Check if this receipt has been matched (could add a matched_invoice_id field)
                # For now, just return all receipts
                extracted = receipt.extracted_data or {}
                unmatched.append({
                    "receipt_id": receipt.id,
                    "filename": receipt.filename,
                    "vendor": extracted.get("vendor"),
                    "amount": extracted.get("total"),
                    "date": extracted.get("dates", [None])[0] if extracted.get("dates") else None
                })
            
            return unmatched
            
        finally:
            db.close()

def _fuzzy_match(str1: str, str2: str) -> float:
    """
    Simple fuzzy string matching.
    Returns similarity score between 0 and 1.
    """
    if not str1 or not str2:
        return 0.0
    
    str1_lower = str1.lower().strip()
    str2_lower = str2.lower().strip()
    
    # Exact match
    if str1_lower == str2_lower:
        return 1.0
    
    # Substring match
    if str1_lower in str2_lower or str2_lower in str1_lower:
        return 0.8
    
    # Word overlap
    words1 = set(str1_lower.split())
    words2 = set(str2_lower.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if union:
        return len(intersection) / len(union)
    
    return 0.0

