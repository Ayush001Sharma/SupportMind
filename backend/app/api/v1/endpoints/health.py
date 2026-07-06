"""
health.py — Liveness and readiness endpoints.

GET /api/v1/health          → basic liveness check (always 200 if the server is up)
GET /api/v1/health/ready    → readiness check (verifies critical dependencies)

The readiness endpoint is intentionally lightweight for this assignment:
it validates the Ollama Base URL is set and the ChromaDB persist directory
is accessible. A load balancer or Render health check can poll /ready.
"""

import os
import time

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.schemas.common import HealthResponse, ReadinessResponse, DependencyStatus

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns 200 as long as the FastAPI process is running.",
)
async def liveness(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Minimal liveness probe.
    Render / Vercel uses this to decide if the container is alive.
    """
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description=(
        "Verifies that required dependencies are reachable before the "
        "instance starts receiving production traffic."
    ),
)
async def readiness(settings: Settings = Depends(get_settings)) -> ReadinessResponse:
    """
    Readiness probe — checks:
    - OLLAMA_BASE_URL is set (non-empty)
    - ChromaDB persist directory exists or can be created
    """
    start = time.perf_counter()
    dependencies: list[DependencyStatus] = []
    overall_ok = True

    # ---- Check 1: Ollama Base URL ----------------------------------- #
    ollama_ok = bool(settings.ollama_base_url)
    dependencies.append(
        DependencyStatus(
            name="ollama_base_url",
            status="ok" if ollama_ok else "error",
            detail=None if ollama_ok else "OLLAMA_BASE_URL is not set or empty",
        )
    )
    if not ollama_ok:
        overall_ok = False

    # ---- Check 2: ChromaDB persist directory ------------------------- #
    chroma_dir = settings.chroma_persist_dir
    try:
        os.makedirs(chroma_dir, exist_ok=True)
        chroma_ok = True
        chroma_detail = None
    except OSError as exc:
        chroma_ok = False
        chroma_detail = f"Cannot create ChromaDB directory '{chroma_dir}': {exc}"

    dependencies.append(
        DependencyStatus(
            name="chromadb_persist_dir",
            status="ok" if chroma_ok else "error",
            detail=chroma_detail,
        )
    )
    if not chroma_ok:
        overall_ok = False

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    logger.info(
        "readiness_check",
        extra={
            "overall": "ok" if overall_ok else "degraded",
            "elapsed_ms": elapsed_ms,
        },
    )

    return ReadinessResponse(
        status="ok" if overall_ok else "degraded",
        dependencies=dependencies,
        elapsed_ms=elapsed_ms,
    )
