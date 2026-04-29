"""Document CRUD, upload, and preview."""
import io
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Document, DocumentCorrection, Transaction
from app.schemas import DocumentResponse, DocumentUpdateBody
from app.services.document_visualization import (
    create_annotated_document,
    get_extraction_confidence,
)
from app.services.idp_pipeline import parse_document
from scripts.ingest_docs import extract_transactions_from_document

router = APIRouter(prefix="/documents", tags=["documents"])


def _doc_to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_path=doc.file_path,
        document_type=doc.document_type,
        created_at=doc.created_at,
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 200,
    doc_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Document)
    if doc_type and doc_type != "all":
        q = q.filter(Document.document_type == doc_type)
    rows = q.order_by(Document.id.desc()).offset(skip).limit(limit).all()
    return [_doc_to_response(d) for d in rows]


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, "Missing filename")
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    body = await file.read()
    if len(body) > max_bytes:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_MB} MB")

    upload_dir = Path(settings.RAW_DOCS_PATH)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(body)

    result = parse_document(str(file_path))
    doc = Document(
        filename=file.filename,
        file_path=str(file_path),
        document_type=result.get("document_type", "unknown"),
        raw_text=result.get("raw_text", ""),
        extracted_data=result.get("extracted_data", {}) or {},
    )
    db.add(doc)
    db.flush()

    extr = result.get("extracted_data", {}) or {}
    for txn_data in extract_transactions_from_document(doc, extr):
        db.add(Transaction(**txn_data))
    db.commit()
    db.refresh(doc)
    return _doc_to_response(doc)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return _doc_to_response(doc)


@router.get("/{document_id}/detail")
def get_document_detail(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_path": doc.file_path,
        "document_type": doc.document_type,
        "raw_text": doc.raw_text,
        "extracted_data": doc.extracted_data or {},
        "created_at": doc.created_at,
    }


@router.get("/{document_id}/confidence")
def doc_confidence(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    ed = doc.extracted_data or {}
    return {"confidence": get_extraction_confidence(ed)}


@router.get("/{document_id}/preview")
def doc_preview(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if not doc.file_path or not Path(doc.file_path).exists():
        raise HTTPException(404, "File not on disk")
    ed = doc.extracted_data or {}
    try:
        img = create_annotated_document(doc.file_path, ed)
    except Exception as e:
        raise HTTPException(500, f"Could not render preview: {e}") from e
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.patch("/{document_id}")
def patch_document(
    document_id: int,
    body: DocumentUpdateBody,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    old = dict(doc.extracted_data or {})
    merged = {**old, **body.extracted_data}
    for field, val in body.extracted_data.items():
        if field in old and str(old[field]) != str(val):
            db.add(
                DocumentCorrection(
                    document_id=document_id,
                    field_name=field,
                    original_value=str(old.get(field, "")),
                    corrected_value=str(val),
                )
            )
    doc.extracted_data = merged
    db.commit()
    db.refresh(doc)
    return {"ok": True, "extracted_data": merged}
