"""
config.py — Application configuration loaded from environment variables.

Uses pydantic-settings so every field is type-validated at startup.
Missing required variables (e.g. OPENAI_API_KEY) will raise a clear
ValidationError before the server accepts traffic.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object — instantiated once and cached."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # silently drop unknown env vars
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_name: str = Field(default="SupportMind API", description="Human-readable application name")
    app_version: str = Field(default="0.1.0", description="API version string surfaced in /health")
    app_description: str = Field(
        default=(
            "SupportMind — an Intelligent Customer Support AI Assistant. "
            "Answers questions exclusively from uploaded documents using a "
            "Retrieval-Augmented Generation (RAG) pipeline."
        ),
        description="OpenAPI description shown in /docs and /redoc",
    )
    debug: bool = Field(default=False, description="Enable debug mode (verbose errors, auto-reload)")

    # ------------------------------------------------------------------ #
    # API
    # ------------------------------------------------------------------ #
    api_v1_prefix: str = Field(default="/api/v1", description="Prefix for all v1 routes")

    # ------------------------------------------------------------------ #
    # Ollama
    # ------------------------------------------------------------------ #
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the local Ollama instance",
    )
    ollama_embedding_model: str = Field(
        default="nomic-embed-text",
        description="Ollama embedding model used during document ingestion",
    )
    ollama_chat_model: str = Field(
        default="llama3.2:3b",
        description="Ollama chat model used for answer generation",
    )

    # ------------------------------------------------------------------ #
    # ChromaDB
    # ------------------------------------------------------------------ #
    chroma_persist_dir: str = Field(
        default="./chromadb_data",
        description="Path where ChromaDB writes its persistent collection files",
    )
    chroma_collection_name: str = Field(
        default="kb_documents",
        description="Name of the ChromaDB collection that stores document chunks",
    )

    # ------------------------------------------------------------------ #
    # RAG / Retrieval
    # ------------------------------------------------------------------ #
    chunk_size: int = Field(default=800, description="Target token size for each text chunk")
    chunk_overlap: int = Field(default=150, description="Overlap between consecutive chunks (tokens)")
    retrieval_top_k: int = Field(default=5, description="Number of chunks fetched from ChromaDB per query")
    similarity_threshold: float = Field(
        default=0.35,
        description="Minimum cosine similarity score for a chunk to be included in the LLM context",
    )
    max_history_messages: int = Field(
        default=12,
        description="Maximum number of messages kept in session history",
    )

    # ------------------------------------------------------------------ #
    # File upload
    # ------------------------------------------------------------------ #
    max_upload_size_mb: int = Field(
        default=10,
        description="Maximum allowed file upload size in megabytes",
    )
    upload_dir: str = Field(
        default="./storage/uploaded_files",
        description="Directory where uploaded files are persisted on disk",
    )
    allowed_mime_types: List[str] = Field(
        default=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ],
        description="MIME types accepted by the document upload endpoint",
    )

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173"],
        description=(
            "Comma-separated list of allowed CORS origins. "
            "In production, set this to your Vercel deployment URL."
        ),
    )

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    log_level: str = Field(
        default="INFO",
        description="Python logging level: DEBUG | INFO | WARNING | ERROR | CRITICAL",
    )

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return upper

    @field_validator("similarity_threshold")
    @classmethod
    def validate_similarity_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        """Convenience property — converts MB limit to bytes for FastAPI validators."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.

    Using @lru_cache means the .env file is read exactly once per process
    lifetime. In tests, call get_settings.cache_clear() to reset.
    """
    return Settings()
