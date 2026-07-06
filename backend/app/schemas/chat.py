"""
chat.py — Pydantic schemas for the Chat and RAG response layer.
"""

from typing import List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload for submitting a chat message."""

    session_id: str = Field(..., description="Unique identifier for the chat session", min_length=1)
    message: str = Field(..., description="The user's question or message", min_length=1)


class SourceAttribution(BaseModel):
    """Represents a unique source document and page used in a response."""

    filename: str = Field(..., description="The name of the source file")
    page_number: int = Field(..., description="The specific page number within the file")


class ChatResponse(BaseModel):
    """Structured response returned by the RAG generation layer."""

    answer: str = Field(..., description="The generated response or fallback string")
    sources: List[SourceAttribution] = Field(
        default_factory=list,
        description="Unique sources used to generate this answer, deduplicated.",
    )
    response_time_ms: float = Field(
        ..., description="Total time taken by the LLM generation phase in ms"
    )
    fallback_used: bool = Field(
        ...,
        description="True if the response is the 'I don't know.' fallback, False otherwise",
    )
