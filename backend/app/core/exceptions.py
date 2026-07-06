"""
exceptions.py — Domain-specific exception hierarchy for SupportMind.

Raising typed exceptions instead of bare HTTPException in service layer
keeps business logic decoupled from HTTP transport. The global exception
handlers in main.py translate these into well-formed API error responses.
"""

from typing import Any, Dict, Optional


class SupportMindError(Exception):
    """Base class for all application-level errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ------------------------------------------------------------------ #
# Document errors
# ------------------------------------------------------------------ #


class UnsupportedFileTypeError(SupportMindError):
    """Raised when an uploaded file has a MIME type not in the allow-list."""


class FileTooLargeError(SupportMindError):
    """Raised when an uploaded file exceeds the configured size limit."""


class DocumentProcessingError(SupportMindError):
    """Raised when text extraction or chunking fails for a document."""


class DocumentNotFoundError(SupportMindError):
    """Raised when a requested document ID does not exist in ChromaDB."""


# ------------------------------------------------------------------ #
# Retrieval / LLM errors
# ------------------------------------------------------------------ #


class RetrievalError(SupportMindError):
    """Raised when the ChromaDB similarity search fails unexpectedly."""


class LLMError(SupportMindError):
    """Raised when the LLM provider returns an error or times out."""


# ------------------------------------------------------------------ #
# Session errors
# ------------------------------------------------------------------ #


class SessionNotFoundError(SupportMindError):
    """Raised when a chat session ID is not found in the in-process store."""
