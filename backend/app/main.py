"""
main.py — FastAPI application factory and entry point.

Responsibilities:
  - Create and configure the FastAPI application instance
  - Register CORS middleware with settings-driven allow-list
  - Mount the versioned API router at /api/v1
  - Register global exception handlers (domain errors → HTTP responses)
  - Manage application lifespan (startup/shutdown hooks)
  - Expose the ASGI app object for Uvicorn / Gunicorn

Run locally:
  uvicorn app.main:app --reload --port 8000
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    FileTooLargeError,
    LLMError,
    RetrievalError,
    SessionNotFoundError,
    SupportMindError,
    UnsupportedFileTypeError,
)
from app.core.logging import configure_logging, get_logger

# Configure JSON logging immediately at import time with a safe default so
# that any log calls made before lifespan (e.g. module-level errors during
# startup) are already structured. The lifespan will re-configure with the
# env-specified level once Settings is validated.
configure_logging("INFO")
logger = get_logger(__name__)


# ------------------------------------------------------------------ #
# Lifespan — startup and shutdown hooks
# ------------------------------------------------------------------ #


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Async context manager executed around the full server lifetime.

    Startup:
      1. Configure structured JSON logging
      2. Validate settings (pydantic raises on missing required fields)
      3. Log the active configuration summary

    Shutdown:
      1. Log a clean shutdown message
      (ChromaDB client cleanup happens automatically via its own teardown)
    """
    settings = get_settings()

    # ---- Startup ---------------------------------------------------- #
    # Re-configure with the env-specified log level now that Settings is
    # validated. This overrides the safe INFO default set at import time.
    configure_logging(settings.log_level)

    logger.info(
        "application_startup",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "api_prefix": settings.api_v1_prefix,
            "log_level": settings.log_level,
            "chroma_persist_dir": settings.chroma_persist_dir,
            "ollama_chat_model": settings.ollama_chat_model,
            "ollama_embedding_model": settings.ollama_embedding_model,
            "allowed_origins": settings.allowed_origins,
        },
    )

    yield  # ← server is live and handling requests

    # ---- Shutdown --------------------------------------------------- #
    logger.info("application_shutdown", extra={"app_name": settings.app_name})


# ------------------------------------------------------------------ #
# Application factory
# ------------------------------------------------------------------ #


def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application.

    Separating construction into a factory function makes it easy to
    create isolated test instances with overridden settings.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs",          # Swagger UI
        redoc_url="/redoc",        # ReDoc
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # ---- CORS ------------------------------------------------------- #
    # Only the origins listed in settings.allowed_origins are permitted.
    # Never use allow_origins=["*"] in production — it would expose the
    # API to any web page and bypass browser same-origin protections.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # ---- Request timing middleware ----------------------------------- #
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """
        Attach X-Process-Time-Ms to every response so the frontend
        and monitoring tools can track end-to-end latency without
        additional instrumentation.
        """
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        return response

    # ---- API routes ------------------------------------------------- #
    app.include_router(v1_router, prefix=settings.api_v1_prefix)

    # ---- Exception handlers ----------------------------------------- #
    _register_exception_handlers(app)

    return app


# ------------------------------------------------------------------ #
# Global exception handlers
# ------------------------------------------------------------------ #


def _register_exception_handlers(app: FastAPI) -> None:
    """
    Map domain exceptions to HTTP responses.

    Service-layer code raises typed SupportMindError subclasses;
    these handlers translate them into well-formed JSON error responses
    without leaking internal stack traces to clients.
    """

    @app.exception_handler(UnsupportedFileTypeError)
    async def handle_unsupported_file_type(
        request: Request, exc: UnsupportedFileTypeError
    ) -> JSONResponse:
        logger.warning("unsupported_file_type", extra={"detail": str(exc), "path": request.url.path})
        return _error_response(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "unsupported_file_type", exc)

    @app.exception_handler(FileTooLargeError)
    async def handle_file_too_large(
        request: Request, exc: FileTooLargeError
    ) -> JSONResponse:
        logger.warning("file_too_large", extra={"detail": str(exc), "path": request.url.path})
        return _error_response(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file_too_large", exc)

    @app.exception_handler(DocumentProcessingError)
    async def handle_document_processing(
        request: Request, exc: DocumentProcessingError
    ) -> JSONResponse:
        logger.error("document_processing_error", extra={"detail": str(exc), "path": request.url.path})
        return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "document_processing_error", exc)

    @app.exception_handler(DocumentNotFoundError)
    async def handle_document_not_found(
        request: Request, exc: DocumentNotFoundError
    ) -> JSONResponse:
        logger.info("document_not_found", extra={"detail": str(exc)})
        return _error_response(status.HTTP_404_NOT_FOUND, "document_not_found", exc)

    @app.exception_handler(SessionNotFoundError)
    async def handle_session_not_found(
        request: Request, exc: SessionNotFoundError
    ) -> JSONResponse:
        logger.info("session_not_found", extra={"detail": str(exc)})
        return _error_response(status.HTTP_404_NOT_FOUND, "session_not_found", exc)

    @app.exception_handler(RetrievalError)
    async def handle_retrieval_error(
        request: Request, exc: RetrievalError
    ) -> JSONResponse:
        logger.error("retrieval_error", extra={"detail": str(exc)})
        return _error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "retrieval_error", exc)

    @app.exception_handler(LLMError)
    async def handle_llm_error(
        request: Request, exc: LLMError
    ) -> JSONResponse:
        logger.error("llm_error", extra={"detail": str(exc)})
        return _error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "llm_error", exc)

    @app.exception_handler(SupportMindError)
    async def handle_generic_domain_error(
        request: Request, exc: SupportMindError
    ) -> JSONResponse:
        # Catch-all for any SupportMindError subclass not handled above
        logger.error("unhandled_domain_error", extra={"detail": str(exc), "type": type(exc).__name__})
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", exc)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Never expose raw exception details to clients in production
        logger.exception("unexpected_error", extra={"path": str(request.url)})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred. Please try again.",
                    "details": None,
                }
            },
        )


def _error_response(
    http_status: int,
    code: str,
    exc: SupportMindError,
) -> JSONResponse:
    """Build a consistent JSON error envelope from a domain exception."""
    return JSONResponse(
        status_code=http_status,
        content={
            "error": {
                "code": code,
                "message": exc.message,
                "details": exc.details or None,
            }
        },
    )


# ------------------------------------------------------------------ #
# ASGI application instance
# ------------------------------------------------------------------ #

app = create_app()
