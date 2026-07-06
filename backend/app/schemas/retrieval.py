"""
retrieval.py — Pydantic schemas for the retrieval layer.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Represents a single chunk of text retrieved from the knowledge base."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    text: str = Field(..., description="The raw text of the chunk")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    filename: str = Field(..., description="Source document filename")
    page_number: int = Field(..., description="Source page number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Full metadata dictionary")


class RetrievalResult(BaseModel):
    """The complete result of a retrieval operation against the knowledge base."""

    query: str = Field(..., description="The original search query")
    retrieved_chunks: List[RetrievedChunk] = Field(
        ..., description="List of chunks that passed the similarity threshold, deduplicated by page"
    )
    total_chunks: int = Field(..., description="Total number of chunks returned in this result")
    max_similarity_score: float = Field(
        default=0.0, description="The highest similarity score before filtering was applied"
    )
    retrieval_duration_ms: float = Field(..., description="Time taken to execute the retrieval (ms)")
