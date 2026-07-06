"""
document_processor.py — Document processing layer.

This service handles the text extraction and preprocessing for uploaded documents.
It operates purely on files on disk and returns structured text.

It is completely decoupled from FastAPI, ChromaDB, and OpenAI for testability.
"""

import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from pypdf.errors import PdfReadError

from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    UnsupportedFileTypeError,
)
from app.core.logging import get_logger
from app.schemas.processing import PageMetadata, ProcessedDocument, ProcessedPage
from app.utils.text_utils import is_empty_page, preprocess_text

logger = get_logger(__name__)


def process_document(file_path: Path) -> ProcessedDocument:
    """
    Read a document from disk, extract text per page/section, apply
    preprocessing, and return a structured ProcessedDocument.

    Parameters
    ----------
    file_path : Path
        Absolute or relative path to the uploaded document on disk.
        The filename is assumed to be in the format: {document_id}_{filename}

    Returns
    -------
    ProcessedDocument
        The cleaned and structured text, split into pages.

    Raises
    ------
    DocumentNotFoundError
        If the file does not exist on disk.
    UnsupportedFileTypeError
        If the file extension is not recognized.
    DocumentProcessingError
        If extraction fails (e.g. corrupted PDF, unreadable DOCX, encoding error)
        or if the document yields no readable text.
    """
    if not file_path.exists():
        raise DocumentNotFoundError(message=f"Missing file: {file_path.name}")

    start_time = time.perf_counter()

    # Parse metadata from the standardized filename (uuid_filename.ext)
    parts = file_path.name.split("_", 1)
    if len(parts) == 2:
        document_id, original_filename = parts
    else:
        document_id = "unknown"
        original_filename = file_path.name

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        document_type = "pdf"
        loader = PyPDFLoader(str(file_path))
    elif suffix == ".docx":
        document_type = "docx"
        loader = Docx2txtLoader(str(file_path))
    elif suffix == ".txt":
        document_type = "txt"
        # Force UTF-8 for plain text to ensure consistency
        loader = TextLoader(str(file_path), encoding="utf-8")
    else:
        raise UnsupportedFileTypeError(
            message=f"Unsupported document type for processing: {suffix}"
        )

    # Use the file's modification time as the upload timestamp
    upload_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()

    logger.info(
        "processing_started",
        extra={
            "document_id": document_id,
            "doc_filename": original_filename,  # Avoids logging's reserved 'filename' key
            "document_type": document_type,
        },
    )

    # Extract text from the document
    try:
        raw_documents = loader.load()
    except PdfReadError as e:
        _log_processing_failure(document_id, original_filename, document_type, start_time, str(e))
        raise DocumentProcessingError(message="Corrupted PDF: unable to extract text.") from e
    except zipfile.BadZipFile as e:
        # DOCX files are essentially zip archives
        _log_processing_failure(document_id, original_filename, document_type, start_time, str(e))
        raise DocumentProcessingError(message="Unreadable DOCX: corrupted archive structure.") from e
    except UnicodeDecodeError as e:
        _log_processing_failure(document_id, original_filename, document_type, start_time, str(e))
        raise DocumentProcessingError(message="Encoding error: TXT file must be valid UTF-8.") from e
    except Exception as e:
        _log_processing_failure(document_id, original_filename, document_type, start_time, str(e))
        raise DocumentProcessingError(message=f"Failed to process document: {e}") from e

    if not raw_documents:
        _log_processing_failure(
            document_id, original_filename, document_type, start_time, "Empty document"
        )
        raise DocumentProcessingError(message="Empty document: no text could be extracted.")

    # Process and clean each page
    processed_pages = []
    
    for i, doc in enumerate(raw_documents):
        page_start = time.perf_counter()

        # PyPDFLoader injects 'page' metadata (0-indexed).
        # Fall back to iteration index + 1 for DOCX/TXT which load as a single document.
        page_num = doc.metadata.get("page", i) + 1

        # Apply preprocessing pipeline (encoding cleanup, whitespace normalization)
        cleaned_text = preprocess_text(doc.page_content)

        # Drop empty pages after cleaning
        if is_empty_page(cleaned_text):
            continue

        page_duration_ms = (time.perf_counter() - page_start) * 1000
        processing_timestamp = datetime.now(tz=timezone.utc).isoformat()

        processed_pages.append(
            ProcessedPage(
                page_number=page_num,
                text=cleaned_text,
                character_count=len(cleaned_text),
                metadata=PageMetadata(
                    filename=original_filename,
                    page_number=page_num,
                    document_type=document_type,
                    processing_timestamp=processing_timestamp,
                    processing_duration_ms=page_duration_ms,
                ),
            )
        )

    processing_time_ms = (time.perf_counter() - start_time) * 1000
    total_pages = len(processed_pages)

    # Edge case: text was extracted, but preprocessing left nothing (e.g. just spaces)
    if total_pages == 0:
        _log_processing_failure(
            document_id, original_filename, document_type, start_time, "Document empty after preprocessing"
        )
        raise DocumentProcessingError(message="Empty document: no readable text after preprocessing.")

    logger.info(
        "processing_completed",
        extra={
            "document_id": document_id,
            "doc_filename": original_filename,
            "document_type": document_type,
            "processing_time_ms": processing_time_ms,
            "total_pages": total_pages,
        },
    )

    return ProcessedDocument(
        document_id=document_id,
        filename=original_filename,
        document_type=document_type,
        upload_timestamp=upload_timestamp,
        total_pages=total_pages,
        pages=processed_pages,
    )


def _log_processing_failure(
    document_id: str,
    original_filename: str,
    document_type: str,
    start_time: float,
    error_msg: str,
) -> None:
    """Helper to emit consistent failure logs with processing time."""
    processing_time_ms = (time.perf_counter() - start_time) * 1000
    logger.error(
        "processing_failed",
        extra={
            "document_id": document_id,
            "doc_filename": original_filename,
            "document_type": document_type,
            "processing_time_ms": processing_time_ms,
            "error": error_msg,
        },
    )
