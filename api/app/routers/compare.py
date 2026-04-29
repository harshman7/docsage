"""Document comparison API."""
from fastapi import APIRouter, HTTPException
from app.services.document_comparison import DocumentComparator
from app.schemas import CompareBody

router = APIRouter(tags=["compare"])


@router.get("/documents/{document_id}/similar")
def similar_documents(document_id: int, limit: int = 5):
    return {"similar": DocumentComparator.find_similar_documents(document_id, limit=limit)}


@router.post("/documents/compare")
def compare_two(body: CompareBody):
    result = DocumentComparator.compare_documents(
        body.document_id_1, body.document_id_2
    )
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
