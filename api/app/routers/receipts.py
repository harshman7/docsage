"""Receipt matching API."""
from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from app.models import User
from app.services.receipt_matching import ReceiptMatcher

router = APIRouter(prefix="/receipt-matching", tags=["receipt-matching"])


@router.get("/unmatched")
def unmatched(current_user: User = Depends(get_current_user)):
    return {"receipts": ReceiptMatcher.get_unmatched_receipts(user_id=current_user.id)}


@router.post("/{receipt_doc_id}/match")
def match_receipt(receipt_doc_id: int, current_user: User = Depends(get_current_user)):
    result = ReceiptMatcher.match_receipt_to_invoice(receipt_doc_id, user_id=current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="No strong match for this receipt")
    return {"match": result}
