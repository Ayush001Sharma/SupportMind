"""
dependencies.py — Central FastAPI dependency providers.

All shared, reusable dependencies live here so endpoint modules import
from a single place. This is the canonical pattern for FastAPI projects:
thin routers that inject services, not instantiate them.

Current providers
-----------------
- get_settings()          → Settings singleton (re-exported from core)
- get_ollama_embeddings() → Ollama embeddings client (lazy, cached)
- get_chroma_client()     → ChromaDB persistent client (lazy, cached)
- get_chroma_collection() → Named ChromaDB collection (derived from client)

Design decisions
----------------
1. **Lazy initialization**: Clients are created on first request, not at
   import time. This means a missing OPENAI_API_KEY will raise at the
   first endpoint call, not at module load — keeping startup fast and
   test setup simple (just patch get_settings before the first request).

2. **Module-level cache**: @lru_cache on the factory functions means one
   client instance is shared across all requests in the same process.
   This avoids the overhead of reconnecting to ChromaDB on every call.

3. **No singletons in endpoint signatures**: Endpoint functions receive
   clients via `Depends()`, which makes them unit-testable by overriding
   the dependency in test fixtures:
       app.dependency_overrides[get_chroma_client] = lambda: mock_client

4. **Type annotations**: All providers are annotated with their concrete
   return types so IDEs and type checkers can resolve attribute access on
   the injected objects.
"""

from functools import lru_cache
from typing import Annotated

import chromadb
from chromadb import Collection
from fastapi import Depends
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Re-export get_settings so endpoint modules only need one import
__all__ = [
    "get_settings",
    "get_ollama_embeddings",
    "get_ollama_chat_model",
    "get_chroma_client",
    "get_chroma_collection",
    "SettingsDep",
    "EmbeddingsDep",
    "ChatModelDep",
    "ChromaClientDep",
    "ChromaCollectionDep",
]


# ------------------------------------------------------------------ #
# Ollama Embeddings
# ------------------------------------------------------------------ #


@lru_cache(maxsize=1)
def _create_embeddings(base_url: str, model: str) -> OllamaEmbeddings:
    """
    Internal factory — called once per unique (base_url, model) pair.
    Separated from get_ollama_embeddings so the cache key is explicit.
    """
    logger.info(
        "ollama_embeddings_client_init",
        extra={"model": model, "base_url": base_url},
    )
    return OllamaEmbeddings(base_url=base_url, model=model)


def get_ollama_embeddings(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OllamaEmbeddings:
    """
    FastAPI dependency that returns the shared Ollama embeddings client.

    The underlying client is created lazily on first call and then cached
    for the lifetime of the process. Inject it via:

        embeddings: Annotated[OllamaEmbeddings, Depends(get_ollama_embeddings)]
    """
    return _create_embeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
    )


# ------------------------------------------------------------------ #
# Ollama Chat Model
# ------------------------------------------------------------------ #


@lru_cache(maxsize=1)
def _create_chat_model(base_url: str, model: str) -> ChatOllama:
    """
    Internal factory — called once per unique (base_url, model) pair.
    """
    logger.info(
        "ollama_chat_client_init",
        extra={"model": model, "base_url": base_url},
    )
    # Using temperature 0 for grounded RAG (deterministic)
    return ChatOllama(base_url=base_url, model=model, temperature=0.0)


def get_ollama_chat_model(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatOllama:
    """
    FastAPI dependency that returns the shared Ollama chat client.
    """
    return _create_chat_model(
        base_url=settings.ollama_base_url,
        model=settings.ollama_chat_model,
    )


# ------------------------------------------------------------------ #
# ChromaDB Persistent Client
# ------------------------------------------------------------------ #


@lru_cache(maxsize=1)
def _create_chroma_client(persist_dir: str) -> chromadb.PersistentClient:
    """
    Internal factory — creates the ChromaDB persistent client once.
    The persist_dir argument is the cache key, so changing CHROMA_PERSIST_DIR
    in tests will produce a fresh client.
    """
    logger.info(
        "chromadb_client_init",
        extra={"persist_dir": persist_dir},
    )
    return chromadb.PersistentClient(path=persist_dir)


def get_chroma_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> chromadb.PersistentClient:
    """
    FastAPI dependency that returns the shared ChromaDB persistent client.

    Inject it via:
        client: Annotated[chromadb.PersistentClient, Depends(get_chroma_client)]
    """
    return _create_chroma_client(persist_dir=settings.chroma_persist_dir)


# ------------------------------------------------------------------ #
# ChromaDB Collection
# ------------------------------------------------------------------ #


def get_chroma_collection(
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[chromadb.PersistentClient, Depends(get_chroma_client)],
) -> Collection:
    """
    FastAPI dependency that returns the named ChromaDB collection.

    Uses get_or_create_collection so the collection is created on first
    access without an explicit migration step. Inject it via:

        collection: Annotated[Collection, Depends(get_chroma_collection)]

    The document service (Phase 2) will receive this and call:
        collection.add(...)  for indexing
        collection.query(...)  for retrieval
    """
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},  # cosine similarity matches the plan
    )


# ------------------------------------------------------------------ #
# Annotated type aliases — convenience shorthands for endpoint signatures
# ------------------------------------------------------------------ #

SettingsDep = Annotated[Settings, Depends(get_settings)]
EmbeddingsDep = Annotated[OllamaEmbeddings, Depends(get_ollama_embeddings)]
ChatModelDep = Annotated[ChatOllama, Depends(get_ollama_chat_model)]
ChromaClientDep = Annotated[chromadb.PersistentClient, Depends(get_chroma_client)]
ChromaCollectionDep = Annotated[Collection, Depends(get_chroma_collection)]
