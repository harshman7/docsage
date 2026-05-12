"""
RAG utilities: embed docs, search FAISS.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.vectorstore.faiss_store import FAISSStore
from app.config import settings


def _user_paths(user_id: Optional[int] = None):
    """Return (index_path, documents_path) scoped to user when provided."""
    if user_id is not None:
        base = Path(settings.FAISS_INDEX_PATH).parent / f"user_{user_id}"
        return base / "faiss.index", base / "documents.pkl"
    return Path(settings.FAISS_INDEX_PATH), Path(settings.FAISS_DOCUMENTS_PATH)


class RAGService:
    """Service for RAG operations using FAISS vector store."""

    def __init__(self, model_name: str = None, user_id: Optional[int] = None):
        model_name = model_name or settings.EMBEDDING_MODEL
        self.user_id = user_id
        self.store = FAISSStore(model_name=model_name)
        self._load_index_if_exists()

    def _load_index_if_exists(self):
        index_path, documents_path = _user_paths(self.user_id)
        if index_path.exists() and documents_path.exists():
            try:
                self.store.load(str(index_path), str(documents_path))
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")

    def embed_documents(self, texts: List[str]):
        return self.store.model.encode(texts)

    def build_index(self, texts: List[str], documents: List[Dict[str, Any]]):
        self.store.create_index(texts, documents)
        self._save_index()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if self.store.index is None:
            return []
        return self.store.search(query, k=k)

    def _save_index(self):
        index_path, documents_path = _user_paths(self.user_id)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        self.store.save(str(index_path), str(documents_path))

    def add_documents(self, texts: List[str], documents: List[Dict[str, Any]]):
        if self.store.index is None:
            self.build_index(texts, documents)
        else:
            existing_docs = self.store.documents
            existing_texts = [doc.get("text", "") for doc in existing_docs]
            all_texts = existing_texts + texts
            all_docs = existing_docs + documents
            self.build_index(all_texts, all_docs)

