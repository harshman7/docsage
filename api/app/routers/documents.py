"""Document CRUD, upload, and preview."""
import io
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models import Document, DocumentCorrection, Transaction, User
from app.schemas import DocumentResponse, DocumentUpdateBody
from app.services.document_visualization import (
    create_annotated_document,
    get_extraction_confidence,
)
from app.services.idp_pipeline import (
    extract_amounts,
    extract_dates,
    extract_vendor,
    parse_document,
)
from scripts.ingest_docs import extract_transactions_from_document

router = APIRouter(prefix="/documents", tags=["documents"])

_RAW_PREVIEW_LEN = 2000
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


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
    current_user: User = Depends(get_current_user),
):
    q = db.query(Document).filter(Document.user_id == current_user.id)
    if doc_type and doc_type != "all":
        q = q.filter(Document.document_type == doc_type)
    rows = q.order_by(Document.id.desc()).offset(skip).limit(limit).all()
    return [_doc_to_response(d) for d in rows]


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(400, "Missing filename")
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    body = await file.read()
    if len(body) > max_bytes:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_MB} MB")

    upload_dir = Path(settings.RAW_DOCS_PATH) / f"user_{current_user.id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(body)

    result = parse_document(str(file_path))
    doc = Document(
        user_id=current_user.id,
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
        txn_data["user_id"] = current_user.id
        db.add(Transaction(**txn_data))
    db.commit()
    db.refresh(doc)
    return _doc_to_response(doc)


def _get_user_doc(document_id: int, user: User, db: Session) -> Document:
    doc = db.query(Document).filter(
        Document.id == document_id, Document.user_id == user.id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _doc_to_response(_get_user_doc(document_id, current_user, db))


@router.get("/{document_id}/extraction-debug")
def get_extraction_debug(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Heuristic extraction from stored raw_text vs saved extracted_data (read-only)."""
    doc = _get_user_doc(document_id, current_user, db)
    if not doc:
        raise HTTPException(404, "Document not found")

    raw = doc.raw_text or ""
    path_str = doc.file_path or ""
    fp = Path(path_str) if path_str else None
    file_exists = bool(fp and fp.is_file())
    synthetic = path_str.startswith("kaggle://")

    suffix = fp.suffix.lower() if fp else ""
    preview_available = file_exists and suffix in _IMAGE_SUFFIXES and not synthetic
    preview_note: Optional[str] = None
    if synthetic:
        preview_note = "Synthetic seed row — no file on disk; annotated preview unavailable."
    elif not path_str:
        preview_note = "No file path on document record."
    elif not file_exists:
        preview_note = "File not found on disk (moved or deleted)."
    elif suffix == ".pdf":
        preview_note = "Annotated preview is for raster images only; PDF preview may fail on the preview endpoint."
    elif not preview_available:
        preview_note = "Preview expects PNG, JPEG, or similar raster formats."

    extracted = doc.extracted_data or {}
    confidence = get_extraction_confidence(extracted)

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "document_type": doc.document_type,
        "file_path": doc.file_path,
        "raw_text_length": len(raw),
        "raw_text_preview": raw[:_RAW_PREVIEW_LEN],
        "file_exists": file_exists,
        "synthetic_source": synthetic,
        "preview_available": preview_available,
        "preview_note": preview_note,
        "confidence": confidence,
        "heuristics_from_raw_text": {
            "amounts": extract_amounts(raw),
            "dates": extract_dates(raw),
            "vendor_guess": extract_vendor(raw),
        },
        "stored_extracted_data": extracted,
    }


@router.post("/{document_id}/reparse")
def reparse_document(
    document_id: int,
    replace_transactions: bool = Query(
        True,
        description="Delete existing transactions for this document and insert new ones from re-extraction to avoid duplicates while debugging.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-run parse_document on the stored file and update DB (local files only)."""
    doc = _get_user_doc(document_id, current_user, db)
    if not doc:
        raise HTTPException(404, "Document not found")
    path_str = doc.file_path or ""
    if path_str.startswith("kaggle://"):
        raise HTTPException(
            400,
            "Cannot reparse synthetic seed documents (no source file on disk).",
        )
    fp = Path(path_str)
    if not path_str or not fp.is_file():
        raise HTTPException(
            400,
            "Cannot reparse: file path missing or file not on disk.",
        )

    result = parse_document(str(fp))
    doc.document_type = result.get("document_type", "unknown")
    doc.raw_text = result.get("raw_text", "")
    doc.extracted_data = result.get("extracted_data") or {}

    new_txn_count = 0
    if replace_transactions:
        db.query(Transaction).filter(Transaction.document_id == document_id).delete(
            synchronize_session=False
        )
        db.flush()
        extr = result.get("extracted_data") or {}
        for txn_data in extract_transactions_from_document(doc, extr):
            db.add(Transaction(**txn_data))
            new_txn_count += 1

    db.commit()
    db.refresh(doc)

    return {
        "ok": True,
        "document_id": doc.id,
        "document_type": doc.document_type,
        "transactions_replaced": replace_transactions,
        "transactions_inserted": new_txn_count if replace_transactions else None,
    }


@router.get("/{document_id}/detail")
def get_document_detail(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = _get_user_doc(document_id, current_user, db)
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
def doc_confidence(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = _get_user_doc(document_id, current_user, db)
    if not doc:
        raise HTTPException(404, "Document not found")
    ed = doc.extracted_data or {}
    return {"confidence": get_extraction_confidence(ed)}


@router.get("/{document_id}/preview")
def doc_preview(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = _get_user_doc(document_id, current_user, db)
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
    current_user: User = Depends(get_current_user),
):
    doc = _get_user_doc(document_id, current_user, db)
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
