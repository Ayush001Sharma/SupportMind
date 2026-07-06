"""
ingestion_service.py — Document ingestion orchestrator.

Coordinates the end-to-end pipeline:
1. Validates and saves the uploaded file (document_service)
2. Extracts and cleans text (document_processor)
3. Splits text into semantic chunks (chunking_service)
4. Generates embeddings and indexes into ChromaDB (vector_store)

Ensures system consistency by cleaning up disk artifacts if the pipeline fails.
"""

import asyncio
from pathlib import Path

from chromadb import Collection
from fastapi import UploadFile
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.documents import DocumentUploadResponse
from app.services import chunking_service, document_processor, document_service, vector_store

logger = get_logger(__name__)


async def ingest_document(
    file: UploadFile,
    settings: Settings,
    collection: Collection,
    embeddings_client: Embeddings,
) -> DocumentUploadResponse:
    """
    Orchestrate the complete document ingestion pipeline.

    If any step after the initial upload fails, the uploaded file is cleanly
    removed from disk so the system is not left in an inconsistent state with
    unindexed files.
    """
    # 1. Upload and Validate
    # This step will raise HTTP 4xx validation errors before persisting anything.
    metadata = await document_service.upload_document(file=file, settings=settings)
    dest_path = Path(settings.upload_dir) / f"{metadata.document_id}_{metadata.filename}"

    try:
        # 2. Extract and Process Text (CPU bound)
        processed_doc = await asyncio.to_thread(
            document_processor.process_document, dest_path
        )

        # 3. Chunking (CPU bound)
        chunks = await asyncio.to_thread(
            chunking_service.chunk_document, processed_doc, settings
        )

        # 4. Vector Storage (Network & Disk I/O bound)
        chunk_count = await asyncio.to_thread(
            vector_store.index_chunks,
            chunks=chunks,
            collection=collection,
            embeddings_client=embeddings_client,
            settings=settings,
            document_id=metadata.document_id,
            filename=metadata.filename,
            document_type=metadata.document_type,
        )

        # Update metadata to reflect success
        metadata.status = "indexed"
        metadata.chunk_count = chunk_count
        
        return metadata

    except Exception as e:
        logger.error(
            "ingestion_failed",
            extra={
                "document_id": metadata.document_id,
                "doc_filename": metadata.filename,
                "error": str(e),
                "action": "cleaning up temporary file",
            },
        )
        # Clean up temporary state to maintain consistency
        if dest_path.exists():
            await asyncio.to_thread(dest_path.unlink)
            
        raise
