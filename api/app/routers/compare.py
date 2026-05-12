"""Document comparison API."""
from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from app.models import User
from app.services.document_comparison import DocumentComparator
from app.schemas import CompareBody

router = APIRouter(tags=["compare"])


@router.get("/documents/{document_id}/similar")
def similar_documents(document_id: int, limit: int = 5, current_user: User = Depends(get_current_user)):
    return {"similar": DocumentComparator.find_similar_documents(document_id, limit=limit, user_id=current_user.id)}


@router.post("/documents/compare")
def compare_two(body: CompareBody, current_user: User = Depends(get_current_user)):
    result = DocumentComparator.compare_documents(
        body.document_id_1, body.document_id_2, user_id=current_user.id
    )
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
