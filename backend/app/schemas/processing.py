"""
processing.py — Pydantic schemas for the document processing layer.

These schemas define the structured output produced by the document
processor after reading and cleaning a file.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class PageMetadata(BaseModel):
    """Metadata attached to each processed page."""

    filename: str = Field(..., description="Original uploaded filename")
    page_number: int = Field(..., description="1-indexed page number")
    document_type: Literal["pdf", "docx", "txt"] = Field(..., description="File format")
    processing_timestamp: str = Field(..., description="ISO 8601 UTC timestamp of processing")
    processing_duration_ms: float = Field(..., description="Time taken to process this specific page (ms)")


class ProcessedPage(BaseModel):
    """A single page or section of text extracted from a document."""

    page_number: int = Field(..., description="1-indexed page number")
    text: str = Field(..., description="Cleaned and normalized text content")
    character_count: int = Field(..., description="Number of characters in the cleaned text")
    metadata: PageMetadata


class ProcessedDocument(BaseModel):
    """The complete structured output for a successfully processed document."""

    document_id: str = Field(..., description="UUID of the document")
    filename: str = Field(..., description="Original uploaded filename")
    document_type: Literal["pdf", "docx", "txt"] = Field(..., description="File format")
    upload_timestamp: str = Field(..., description="ISO 8601 UTC timestamp from file stat (or upload)")
    total_pages: int = Field(..., description="Total number of non-empty pages extracted")
    pages: List[ProcessedPage]
