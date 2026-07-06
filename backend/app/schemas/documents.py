"""
documents.py — Pydantic schemas for the document management feature.

Each endpoint response has an explicit schema so:
  1. FastAPI generates accurate OpenAPI documentation automatically.
  2. Callers get type-safe, validated response objects.
  3. The contract between service and router is enforced by the type system.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """
    Returned by POST /api/v1/documents/upload on success.

    Matches the metadata contract defined in the implementation plan
    (Section 4 — APIs Required).
    """

    document_id: str = Field(
        ...,
        description="UUID assigned to this document at upload time",
        examples=["3f8a2b1c-4d5e-6f7a-8b9c-0d1e2f3a4b5c"],
    )
    filename: str = Field(
        ...,
        description="Sanitized filename as stored on disk",
        examples=["annual_report_2024.pdf"],
    )
    document_type: Literal["pdf", "docx", "txt"] = Field(
        ...,
        description="Detected document type derived from the file extension",
    )
    file_size: int = Field(
        ...,
        description="File size in bytes",
        examples=[204800],
    )
    upload_timestamp: str = Field(
        ...,
        description="ISO 8601 UTC timestamp of when the file was received",
        examples=["2026-07-05T16:00:00+00:00"],
    )
    status: Literal["uploaded", "indexed"] = Field(
        default="uploaded",
        description=(
            "Processing status. 'uploaded' means the file has been saved "
            "and is ready for Phase 3 text extraction and indexing. 'indexed' means "
            "it is fully available in ChromaDB."
        ),
    )
    chunk_count: Optional[int] = Field(
        default=None,
        description="Number of text chunks indexed in ChromaDB",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "document_id": "3f8a2b1c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
                "filename": "annual_report_2024.pdf",
                "document_type": "pdf",
                "file_size": 204800,
                "upload_timestamp": "2026-07-05T16:00:00+00:00",
                "status": "indexed",
                "chunk_count": 15,
            }
        }
    }


class DocumentListItem(BaseModel):
    """
    Single item returned by GET /api/v1/documents/ (Phase 3+).
    Defined now so the schema is available when the list endpoint is implemented.
    """

    document_id: str
    filename: str
    document_type: Literal["pdf", "docx", "txt"]
    file_size: int
    upload_timestamp: str
    status: str = Field(
        ...,
        description="'uploaded' | 'indexed' | 'failed'",
    )
    chunk_count: Optional[int] = Field(
        default=None,
        description="Number of text chunks indexed in ChromaDB (set after Phase 3 processing)",
    )
