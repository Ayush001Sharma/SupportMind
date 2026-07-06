"""
logging.py — Structured logging configuration for the entire application.

Emits JSON-formatted log records to stdout so they are machine-readable
by log aggregators (e.g. Render's log dashboard, Datadog, CloudWatch).

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("document_uploaded", extra={"filename": "report.pdf", "size_bytes": 204800})
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class _JsonFormatter(logging.Formatter):
    """
    Custom log formatter that serialises each LogRecord to a single JSON line.

    Fields emitted on every record:
      - timestamp  : ISO 8601 UTC
      - level      : log level name
      - logger     : logger name (typically __name__ of the emitting module)
      - message    : the formatted log message
      - **extra    : any key=value pairs passed via the `extra` kwarg

    This matches the observability schema defined in the implementation plan
    (Section 8a) so log queries like `level=WARNING event=fallback_triggered`
    work out of the box without parsing free-text strings.
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        # Build the base payload
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach any extra fields injected via logger.info(..., extra={...})
        # "taskName" was added to LogRecord in Python 3.12; guard it so the
        # reserved set is accurate on Python 3.11 (our minimum target).
        #
        # ⚠️  IMPORTANT for callers using extra={}:
        # The following keys are RESERVED by Python's LogRecord and will raise
        # KeyError("Attempt to overwrite ...") if used in extra={}:
        #   "filename", "funcName", "lineno", "module", "name", "pathname",
        #   "process", "processName", "thread", "threadName", "args", "msg"
        # Use prefixed alternatives instead — e.g. "doc_filename" not "filename".
        _reserved = {
            "args", "created", "exc_info", "exc_text", "filename",
            "funcName", "levelname", "levelno", "lineno", "message",
            "module", "msecs", "msg", "name", "pathname", "process",
            "processName", "relativeCreated", "stack_info", "thread",
            "threadName",
        }
        if sys.version_info >= (3, 12):
            _reserved.add("taskName")
        for key, value in record.__dict__.items():
            if key not in _reserved:
                payload[key] = value

        # Attach exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(log_level: str = "INFO") -> None:
    """
    Call once at application startup (inside main.py lifespan).

    Replaces the default root-logger handlers with a single stderr/stdout
    handler using _JsonFormatter. All third-party loggers (uvicorn, httpx,
    langchain, chromadb) are also captured at WARNING or above to reduce noise.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger — catches everything our app emits
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Remove any handlers added by uvicorn or prior configure calls
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)

    # Silence overly chatty third-party loggers in production
    _noisy = ["httpx", "httpcore", "openai", "chromadb", "urllib3"]
    for name in _noisy:
        logging.getLogger(name).setLevel(logging.WARNING)

    # Uvicorn's access log is useful but keep it at INFO
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Module-level helper — mirrors the interface of logging.getLogger
    so callers never need to import the logging stdlib directly.

    Example:
        logger = get_logger(__name__)
        logger.warning(
            "fallback_triggered",
            extra={
                "session_id": session_id,
                "query_preview": query[:80],
                "max_similarity_score": max_score,
            },
        )
    """
    return logging.getLogger(name)
