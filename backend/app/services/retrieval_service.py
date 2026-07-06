"""
retrieval_service.py — Retrieval layer for Phase 4.

This service queries ChromaDB to find relevant chunks for a user query.
It handles query embedding, similarity search, threshold filtering, and
page-level deduplication.

It is completely decoupled from FastAPI endpoints and LangChain LLM generation.
"""

import time
from typing import Set, Tuple

from chromadb import Collection
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.core.exceptions import RetrievalError
from app.core.logging import get_logger
from app.schemas.retrieval import RetrievalResult, RetrievedChunk

logger = get_logger(__name__)


def retrieve(
    query: str,
    collection: Collection,
    embeddings_client: Embeddings,
    settings: Settings,
) -> RetrievalResult:
    """
    Retrieve and filter relevant document chunks from ChromaDB for a given query.

    Parameters
    ----------
    query : str
        The raw user search query.
    collection : chromadb.Collection
        The persistent ChromaDB collection.
    embeddings_client : Embeddings
        The LangChain embeddings client (e.g., OllamaEmbeddings).
    settings : Settings
        Global configuration containing retrieval_top_k and similarity_threshold.

    Returns
    -------
    RetrievalResult
        The filtered, sorted, and deduplicated chunks alongside retrieval metadata.
        If no chunks pass the threshold, the retrieved_chunks list is empty.

    Raises
    ------
    RetrievalError
        If the query is empty, or if embedding/search fails unexpectedly.
    """
    start_time = time.perf_counter()

    # 1. Validate query
    if not query or not query.strip():
        raise RetrievalError(message="Query cannot be empty.")

    logger.info("retrieval_started", extra={"query_length": len(query)})

    # 2. Generate query embedding
    try:
        query_embedding = embeddings_client.embed_query(query)
    except Exception as e:
        logger.error("retrieval_failed", extra={"error": str(e)})
        raise RetrievalError(message="Failed to generate query embedding.") from e

    # 3. Perform similarity search against ChromaDB
    try:
        # 4. Retrieve top_k documents
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=settings.retrieval_top_k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.error("retrieval_failed", extra={"error": str(e)})
        raise RetrievalError(message="Failed to execute ChromaDB similarity search.") from e

    # Handle empty knowledge base or empty search results
    if not results or not results.get("ids") or not results["ids"][0]:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.warning(
            "retrieval_completed",
            extra={
                "retrieved_chunks": 0,
                "filtered_chunks": 0,
                "max_similarity_score": 0.0,
                "retrieval_duration_ms": duration_ms,
            },
        )
        return RetrievalResult(
            query=query,
            retrieved_chunks=[],
            total_chunks=0,
            max_similarity_score=0.0,
            retrieval_duration_ms=duration_ms,
        )

    # Extract parallel lists from the first (and only) query result
    ids = results["ids"][0]
    distances = results["distances"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    max_score = 0.0
    passed_chunks = []
    seen_pages: Set[Tuple[str, int]] = set()

    for chunk_id, distance, text, meta in zip(ids, distances, documents, metadatas):
        # ChromaDB with hnsw:space='cosine' returns cosine distance.
        # Cosine similarity = 1 - Cosine distance.
        similarity = 1.0 - distance
        max_score = max(max_score, similarity)

        # 5. Apply similarity threshold filtering
        if similarity < settings.similarity_threshold:
            continue

        filename = meta.get("filename", "unknown")
        page_num = meta.get("page_number", 1)

        # 6. Remove duplicate chunks from the same page
        # This keeps only the highest scoring chunk per unique (filename, page_number)
        page_identifier = (filename, page_num)
        if page_identifier in seen_pages:
            continue

        seen_pages.add(page_identifier)

        passed_chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=text,
                similarity_score=similarity,
                filename=filename,
                page_number=page_num,
                metadata=meta,
            )
        )

    # 7. Sort by similarity score (descending)
    passed_chunks.sort(key=lambda x: x.similarity_score, reverse=True)

    duration_ms = (time.perf_counter() - start_time) * 1000

    # 8. Return structured retrieval results
    logger.info(
        "retrieval_completed",
        extra={
            "retrieved_chunks": len(ids),
            "filtered_chunks": len(passed_chunks),
            "max_similarity_score": max_score,
            "retrieval_duration_ms": duration_ms,
        },
    )

    return RetrievalResult(
        query=query,
        retrieved_chunks=passed_chunks,
        total_chunks=len(passed_chunks),
        max_similarity_score=max_score,
        retrieval_duration_ms=duration_ms,
    )
