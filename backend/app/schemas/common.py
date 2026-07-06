"""
common.py — Shared Pydantic schemas used across multiple endpoints.

Domain-specific schemas (DocumentUploadResponse, ChatMessageRequest, etc.)
live in their own modules (documents.py, chat.py) and will be added as
each feature is implemented.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Base
# ------------------------------------------------------------------ #


class APIResponse(BaseModel):
    """
    Generic envelope for simple success/failure responses.
    Not used for rich typed responses — those have their own models.
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable result description")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional payload for simple responses",
    )


class ErrorDetail(BaseModel):
    """Standard error payload embedded inside all 4xx / 5xx responses."""

    code: str = Field(
        ...,
        description="Machine-readable error code (e.g. 'unsupported_file_type')",
    )
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (field name, allowed values, etc.)",
    )


class ErrorResponse(BaseModel):
    """Top-level wrapper returned on all error responses."""

    error: ErrorDetail


# ------------------------------------------------------------------ #
# Health
# ------------------------------------------------------------------ #


class HealthResponse(BaseModel):
    """Response for GET /api/v1/health (liveness)."""

    status: Literal["ok"] = Field(default="ok")
    app_name: str
    version: str


class DependencyStatus(BaseModel):
    """Status of a single downstream dependency checked during readiness."""

    name: str = Field(..., description="Dependency identifier (e.g. 'openai_api_key')")
    status: Literal["ok", "error"] = Field(..., description="'ok' or 'error'")
    detail: Optional[str] = Field(
        default=None,
        description="Human-readable error message when status is 'error'",
    )


class ReadinessResponse(BaseModel):
    """Response for GET /api/v1/health/ready (readiness)."""

    status: Literal["ok", "degraded"]
    dependencies: List[DependencyStatus]
    elapsed_ms: float = Field(..., description="Time taken to run all dependency checks (ms)")


# ------------------------------------------------------------------ #
# Source attribution (shared by chat responses)
# ------------------------------------------------------------------ #


class SourceReference(BaseModel):
    """
    A single source chunk cited in a chat reply.
    Matches the ChromaDB metadata schema from Section 5 of the plan.
    """

    filename: str = Field(..., description="Original uploaded filename")
    page: int = Field(..., description="Page number within the source document")

    model_config = {"json_schema_extra": {"example": {"filename": "returns_policy.pdf", "page": 4}}}
