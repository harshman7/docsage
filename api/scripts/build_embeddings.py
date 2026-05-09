"""
CLI script: embed docs and build FAISS index.

Indexes (per document when available):
 1. A compact extraction_summary chunk from extracted_data (field-level retrieval).
 2. Chunked raw_text (OCR/PDF text).

Re-run after changing extraction or IDP; paths from settings (FAISS_*).
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db import SessionLocal
from app.models import Document
from app.services.rag import RAGService
from app.services.extraction_summary import extraction_to_index_text
from app.config import settings


def build_embeddings(chunk_size: int = 500, chunk_overlap: int = 50):
    """Build FAISS index from documents in database."""
    db = SessionLocal()
    try:
        documents = db.query(Document).all()

        if not documents:
            print("No documents found in database. Run ingest_docs.py first.")
            return

        print(f"Building embeddings for {len(documents)} documents...")

        rag_service = RAGService()

        texts = []
        doc_metadata = []

        for doc in documents:
            ed = doc.extracted_data if isinstance(doc.extracted_data, dict) else {}
            summary = extraction_to_index_text(
                ed or None,
                filename=doc.filename or "",
                document_id=doc.id,
            )
            has_summary = bool(summary)

            if has_summary:
                texts.append(summary)
                doc_metadata.append(
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "document_type": doc.document_type,
                        "file_path": doc.file_path,
                        "text": summary,
                        "chunk_index": 0,
                        "chunk_type": "extraction_summary",
                    }
                )

            raw = doc.raw_text or ""
            if not raw:
                continue

            if len(raw) > chunk_size:
                chunks = []
                start = 0
                while start < len(raw):
                    end = start + chunk_size
                    chunks.append(raw[start:end])
                    start = end - chunk_overlap
                total_raw = len(chunks)
                for i, chunk in enumerate(chunks):
                    texts.append(chunk)
                    doc_metadata.append(
                        {
                            "id": doc.id,
                            "filename": doc.filename,
                            "document_type": doc.document_type,
                            "file_path": doc.file_path,
                            "text": chunk,
                            "chunk_index": (i + 1) if has_summary else i,
                            "chunk_type": "raw_text",
                            "total_chunks": (1 if has_summary else 0) + total_raw,
                        }
                    )
            else:
                texts.append(raw)
                doc_metadata.append(
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "document_type": doc.document_type,
                        "file_path": doc.file_path,
                        "text": raw,
                        "chunk_index": 1 if has_summary else 0,
                        "chunk_type": "raw_text",
                        "total_chunks": (1 if has_summary else 0) + 1,
                    }
                )

        if not texts:
            print("No text content found in documents (need raw_text and/or extracted_data).")
            return

        print(f"  → Created {len(texts)} text chunks")
        print(f"  → Generating embeddings...")

        rag_service.build_index(texts, doc_metadata)

        print(f"✓ Index built successfully!")
        print(f"  → {len(texts)} embeddings created")
        print(f"  → Saved to {settings.FAISS_INDEX_PATH}")

    except Exception as e:
        print(f"Error building embeddings: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    chunk_size = (
        int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 500
    )
    build_embeddings(chunk_size=chunk_size)
