"""
CLI script: embed docs and build FAISS index.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db import SessionLocal
from app.models import Document
from app.services.rag import RAGService
from app.config import settings

def build_embeddings(chunk_size: int = 500, chunk_overlap: int = 50):
    """Build FAISS index from documents in database."""
    db = SessionLocal()
    try:
        # Get all documents
        documents = db.query(Document).all()
        
        if not documents:
            print("No documents found in database. Run ingest_docs.py first.")
            return
        
        print(f"Building embeddings for {len(documents)} documents...")
        
        # Initialize RAG service
        rag_service = RAGService()
        
        # Prepare texts and metadata
        texts = []
        doc_metadata = []
        
        for doc in documents:
            if not doc.raw_text:
                continue
            
            # Split long documents into chunks
            text = doc.raw_text
            if len(text) > chunk_size:
                # Simple chunking (in production, use a proper text splitter)
                chunks = []
                start = 0
                while start < len(text):
                    end = start + chunk_size
                    chunk = text[start:end]
                    chunks.append(chunk)
                    start = end - chunk_overlap
                
                for i, chunk in enumerate(chunks):
                    texts.append(chunk)
                    doc_metadata.append({
                        "id": doc.id,
                        "filename": doc.filename,
                        "document_type": doc.document_type,
                        "file_path": doc.file_path,
                        "text": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    })
            else:
                texts.append(text)
                doc_metadata.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "document_type": doc.document_type,
                    "file_path": doc.file_path,
                    "text": text
                })
        
        if not texts:
            print("No text content found in documents.")
            return
        
        print(f"  → Created {len(texts)} text chunks")
        print(f"  → Generating embeddings...")
        
        # Build index
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
    chunk_size = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 500
    build_embeddings(chunk_size=chunk_size)

