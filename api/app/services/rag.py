"""
RAG utilities: embed docs, search FAISS.
"""
from typing import List, Dict, Any
from pathlib import Path
from app.vectorstore.faiss_store import FAISSStore
from app.config import settings

class RAGService:
    """Service for RAG operations using FAISS vector store."""
    
    def __init__(self, model_name: str = None):
        model_name = model_name or settings.EMBEDDING_MODEL
        self.store = FAISSStore(model_name=model_name)
        self._load_index_if_exists()
    
    def _load_index_if_exists(self):
        """Load existing index if it exists."""
        index_path = Path(settings.FAISS_INDEX_PATH)
        documents_path = Path(settings.FAISS_DOCUMENTS_PATH)
        
        if index_path.exists() and documents_path.exists():
            try:
                self.store.load(str(index_path), str(documents_path))
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")
    
    def embed_documents(self, texts: List[str]):
        """Generate embeddings for a list of texts."""
        return self.store.model.encode(texts)
    
    def build_index(self, texts: List[str], documents: List[Dict[str, Any]]):
        """Build FAISS index from texts and store document metadata."""
        self.store.create_index(texts, documents)
        self._save_index()
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.store.index is None:
            return []
        
        return self.store.search(query, k=k)
    
    def _save_index(self):
        """Save FAISS index and documents to disk."""
        index_path = Path(settings.FAISS_INDEX_PATH)
        documents_path = Path(settings.FAISS_DOCUMENTS_PATH)
        
        # Create directories if they don't exist
        index_path.parent.mkdir(parents=True, exist_ok=True)
        documents_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.store.save(str(index_path), str(documents_path))
    
    def add_documents(self, texts: List[str], documents: List[Dict[str, Any]]):
        """Add new documents to existing index."""
        if self.store.index is None:
            self.build_index(texts, documents)
        else:
            # For simplicity, rebuild the entire index
            # In production, you'd want incremental updates
            existing_docs = self.store.documents
            existing_texts = [doc.get("text", "") for doc in existing_docs]
            
            all_texts = existing_texts + texts
            all_docs = existing_docs + documents
            
            self.build_index(all_texts, all_docs)

