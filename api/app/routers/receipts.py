"""Receipt matching API."""
from fastapi import APIRouter, HTTPException
from app.services.receipt_matching import ReceiptMatcher

router = APIRouter(prefix="/receipt-matching", tags=["receipt-matching"])


@router.get("/unmatched")
def unmatched():
    return {"receipts": ReceiptMatcher.get_unmatched_receipts()}


@router.post("/{receipt_doc_id}/match")
def match_receipt(receipt_doc_id: int):
    result = ReceiptMatcher.match_receipt_to_invoice(receipt_doc_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No strong match for this receipt")
    return {"match": result}
