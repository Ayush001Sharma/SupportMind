"""
document_service.py — Document upload service.

This is the ONLY place that contains upload business logic.
The endpoint (documents.py) is a thin router that calls this service
and maps the result to an HTTP response.

Phase 2 scope
-------------
This service validates the uploaded file and persists it to disk.
It does NOT:
  - Parse or extract text
  - Generate embeddings
  - Write to ChromaDB
  - Call OpenAI

Those steps belong to Phase 3 (document_processor.py).

Design
------
- All validation raises typed exceptions from app.core.exceptions.
  The global handlers in main.py translate them to HTTP 4xx responses
  without any error-handling code inside this service.
- File I/O uses asyncio.to_thread() so the async FastAPI event loop
  is never blocked by synchronous disk writes.
- The upload directory is created lazily on first use; no migration step
  or startup hook required.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.core.logging import get_logger
from app.schemas.documents import DocumentUploadResponse
from app.utils.file_utils import (
    human_readable_bytes,
    sanitize_filename,
    validate_file_size,
    validate_mime_type,
)

logger = get_logger(__name__)

# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #

# Maps each allowed file extension to its canonical document_type label.
# Both the extension check and the document_type in the response derive
# from this single source of truth.
_EXTENSION_TO_TYPE: dict[str, Literal["pdf", "docx", "txt"]] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
}

# Allowed extensions as a set for fast membership testing.
_ALLOWED_EXTENSIONS: frozenset[str] = frozenset(_EXTENSION_TO_TYPE.keys())


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #


async def upload_document(
    file: UploadFile,
    settings: Settings,
) -> DocumentUploadResponse:
    """
    Validate, save, and return metadata for an uploaded document.

    Parameters
    ----------
    file:
        The raw UploadFile received from the multipart/form-data request.
    settings:
        The application settings singleton (injected by the endpoint).

    Returns
    -------
    DocumentUploadResponse
        Metadata about the saved file. Status is always "uploaded".

    Raises
    ------
    UnsupportedFileTypeError
        If the MIME type or file extension is not in the allow-list.
    FileTooLargeError
        If the file exceeds settings.max_upload_size_mb.
    """
    original_filename = file.filename or "unnamed_file"

    # ---------------------------------------------------------------- #
    # Step 1: MIME type validation
    # ---------------------------------------------------------------- #
    # Browser-supplied Content-Type is the first gate. We do NOT trust
    # it exclusively (a renamed .exe would still pass), but it catches
    # the common cases and sets clear expectations for the client.
    if not validate_mime_type(file.content_type, settings.allowed_mime_types):
        raise UnsupportedFileTypeError(
            message=(
                f"File type '{file.content_type}' is not supported. "
                f"Accepted types: PDF, DOCX, TXT."
            ),
            details={
                "received_mime_type": file.content_type,
                "allowed_mime_types": settings.allowed_mime_types,
            },
        )

    # ---------------------------------------------------------------- #
    # Step 2: File extension validation
    # ---------------------------------------------------------------- #
    # Extension check is a second independent gate. A file with a correct
    # MIME type but wrong extension (or no extension) is still rejected.
    suffix = Path(original_filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            message=(
                f"File extension '{suffix}' is not supported. "
                f"Accepted extensions: .pdf, .docx, .txt."
            ),
            details={
                "received_extension": suffix,
                "allowed_extensions": sorted(_ALLOWED_EXTENSIONS),
            },
        )

    # ---------------------------------------------------------------- #
    # Step 3: Read file content
    # ---------------------------------------------------------------- #
    # Read the entire file into memory. The 10 MB default limit makes this
    # safe; larger limits should use streaming reads with size accounting.
    content: bytes = await file.read()

    # ---------------------------------------------------------------- #
    # Step 4: File size validation
    # ---------------------------------------------------------------- #
    # Validate AFTER reading so the actual byte count is authoritative,
    # not the browser-supplied Content-Length header (which can be spoofed).
    size_bytes = len(content)
    if not validate_file_size(size_bytes, settings.max_upload_size_bytes):
        raise FileTooLargeError(
            message=(
                f"File size {human_readable_bytes(size_bytes)} exceeds the "
                f"{settings.max_upload_size_mb} MB limit."
            ),
            details={
                "received_bytes": size_bytes,
                "max_bytes": settings.max_upload_size_bytes,
                "max_mb": settings.max_upload_size_mb,
            },
        )

    # ---------------------------------------------------------------- #
    # Step 5: Sanitize filename and resolve document type
    # ---------------------------------------------------------------- #
    safe_filename = sanitize_filename(original_filename)
    document_type = _EXTENSION_TO_TYPE[suffix]

    # ---------------------------------------------------------------- #
    # Step 6: Generate unique document ID
    # ---------------------------------------------------------------- #
    document_id = str(uuid.uuid4())

    # ---------------------------------------------------------------- #
    # Step 7: Persist file to disk
    # ---------------------------------------------------------------- #
    # Storage path: {upload_dir}/{document_id}_{safe_filename}
    # Prefixing with the UUID prevents collisions when two users upload
    # files with the same name.
    upload_dir = Path(settings.upload_dir)
    dest_path = upload_dir / f"{document_id}_{safe_filename}"

    await asyncio.to_thread(_write_file, dest_path, content)

    # ---------------------------------------------------------------- #
    # Step 8: Emit structured log (Section 8a observability schema)
    # ---------------------------------------------------------------- #
    upload_timestamp = datetime.now(tz=timezone.utc).isoformat()

    logger.info(
        "document_uploaded",
        extra={
            "document_id": document_id,
            # NOTE: "filename" is a reserved LogRecord field (module filename).
            # Use "doc_filename" to carry the uploaded file's name safely.
            "doc_filename": safe_filename,
            "original_doc_filename": original_filename,
            "document_type": document_type,
            "size_bytes": size_bytes,
            "dest_path": str(dest_path),
            "timestamp": upload_timestamp,
        },
    )

    # ---------------------------------------------------------------- #
    # Step 9: Return metadata
    # ---------------------------------------------------------------- #
    return DocumentUploadResponse(
        document_id=document_id,
        filename=safe_filename,
        document_type=document_type,
        file_size=size_bytes,
        upload_timestamp=upload_timestamp,
        status="uploaded",
    )


# ------------------------------------------------------------------ #
# Private helpers
# ------------------------------------------------------------------ #


def _write_file(dest_path: Path, content: bytes) -> None:
    """
    Synchronous file write — always called via asyncio.to_thread().

    Creates the parent directory tree if it doesn't exist. Using
    exist_ok=True makes this idempotent and safe under concurrent uploads.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(content)
