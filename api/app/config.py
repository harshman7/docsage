"""
Application configuration loaded from environment variables.
"""
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

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
    
    # Google AI Studio / Gemini (https://aistudio.google.com/apikey)
    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    )
    GOOGLE_AI_MODEL: str = "gemini-3.1-flash-lite-preview"  # Gemini 3.1 Flash-Lite (preview)

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

settings = Settings()

