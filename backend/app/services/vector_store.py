"""
vector_store.py — ChromaDB ingestion and indexing layer (Phase 3).

This service converts a ProcessedDocument into semantic chunks using
a token-aware text splitter, generates embeddings using the configured
provider (e.g., Ollama), and persists everything to the local ChromaDB collection.
"""

import hashlib
import time
from typing import List

from chromadb import Collection
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.processing import ProcessedDocument

logger = get_logger(__name__)


from langchain_core.documents import Document

def index_chunks(
    chunks: List[Document],
    collection: Collection,
    embeddings_client: Embeddings,
    settings: Settings,
    document_id: str,
    filename: str,
    document_type: str,
) -> int:
    """
    Generate embeddings for LangChain Document chunks and index them into ChromaDB.

    This function is synchronous and performs network I/O to the embeddings API
    and disk I/O to ChromaDB. It should be called via asyncio.to_thread() from an endpoint.
    """
    if not chunks:
        logger.warning(
            "indexing_skipped_empty",
            extra={
                "document_id": document_id,
                "doc_filename": filename,
            },
        )
        return 0

    start_time = time.perf_counter()

    ids: List[str] = [chunk.id for chunk in chunks]
    documents: List[str] = [chunk.page_content for chunk in chunks]
    metadatas: List[dict] = [chunk.metadata for chunk in chunks]

    # 1. Embedding Generation
    # We call embed_documents explicitly before inserting into ChromaDB.
    embeddings_list = embeddings_client.embed_documents(documents)

    # 2. Vector Database Insertion
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings_list,
        metadatas=metadatas,
    )

    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "embedding_generation_complete",
        extra={
            "document_id": document_id,
            "doc_filename": filename,
            "document_type": document_type,
            "chunk_count": len(ids),
            "model": settings.ollama_embedding_model,
            "duration_ms": duration_ms,
        },
    )

    return len(ids)
