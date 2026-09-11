"""Core configuration module using Pydantic Settings."""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path
_ROOT_DIR = Path(__file__).resolve().parents[3]
_DEFAULT_DB = (_ROOT_DIR / "enterprise_local_dev.db").as_posix()
_DEFAULT_CHROMA = (_ROOT_DIR / "chroma_data").as_posix()
_DEFAULT_UPLOADS = (_ROOT_DIR / "uploads").as_posix()

class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "Local AI Nội bộ doanh nghiệp"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Database (defaults to canonical SQLite file in project root)
    DATABASE_URL: str = f"sqlite:///{_DEFAULT_DB}"

    # Security & JWT
    JWT_SECRET_KEY: str = "default_insecure_development_secret_key_change_me_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Vector Database
    CHROMA_PERSIST_DIRECTORY: str = _DEFAULT_CHROMA
    CHROMA_COLLECTION_NAME: str = "enterprise_knowledge_base"

    # Local AI Runtime (Ollama)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_LLM_MODEL: str = "qwen2.5:3b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_TEMPERATURE: float = 0.1
    OLLAMA_TOP_P: float = 0.9
    OLLAMA_CONTEXT_WINDOW: int = 2048

    # RAG Settings
    RAG_TOP_K: int = 3
    RAG_SIMILARITY_THRESHOLD: float = 0.42
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 120

    # File Storage
    UPLOAD_DIRECTORY: str = _DEFAULT_UPLOADS
    MAX_UPLOAD_SIZE_MB: int = 100
    AUTO_IMPORT_DIRECTORY: str = str(_ROOT_DIR / "auto_import_documents")

    model_config = SettingsConfigDict(
        env_file=[
            str(_ROOT_DIR / ".env"),
            str(_ROOT_DIR / "backend" / ".env"),
            ".env",
        ],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
