"""
FAISS index create/load/search helpers.
"""
import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

class FAISSStore:
    """Helper class for managing FAISS vector stores."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []
        self.dimension = 384  # Default for all-MiniLM-L6-v2
    
    def create_index(self, texts: List[str], documents: List[Dict[str, Any]]):
        """Create a new FAISS index from texts."""
        embeddings = self.model.encode(texts)
        self.dimension = embeddings.shape[1]
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype("float32"))
        self.documents = documents
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.index is None:
            raise ValueError("Index not created. Call create_index first.")
        
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding.astype("float32"), k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append({
                    "document": self.documents[idx],
                    "score": float(distance)
                })
        
        return results
    
    def save(self, index_path: str, documents_path: str):
        """Save index and documents to disk."""
        if self.index is None:
            raise ValueError("No index to save.")
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save documents
        with open(documents_path, "wb") as f:
            pickle.dump(self.documents, f)
    
    def load(self, index_path: str, documents_path: str):
        """Load index and documents from disk."""
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        self.dimension = self.index.d
        
        # Load documents
        with open(documents_path, "rb") as f:
            self.documents = pickle.load(f)

