"""
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "docsage"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    USE_SQLITE: bool = False  # Set to True to use SQLite instead of PostgreSQL
    
    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return "sqlite:///./docsage.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # LLM Provider Selection
    LLM_PROVIDER: str = "ollama"  # Options: "ollama", "groq", "huggingface"
    
    # Ollama (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"  # or mistral, codellama, etc.
    
    # Groq API (free tier available)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Fast and free
    
    # Hugging Face Inference API (free tier available)
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    
    # Vector Store
    FAISS_INDEX_PATH: str = "data/embeddings/faiss.index"
    FAISS_DOCUMENTS_PATH: str = "data/embeddings/documents.pkl"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Data paths
    RAW_DOCS_PATH: str = "data/raw_docs"
    PROCESSED_PATH: str = "data/processed"
    
    # HTTP / upload
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    MAX_UPLOAD_MB: int = 32

    # Application
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> List[str]:
        raw = self.CORS_ORIGINS.strip()
        if raw == "*":
            return ["*"]
        return [x.strip() for x in raw.split(",") if x.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

