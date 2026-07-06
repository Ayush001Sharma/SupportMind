"""
test_vector_store.py — Unit tests for the vector indexing layer.

ChromaDB collection and embeddings are fully mocked.
No real Ollama calls or disk writes occur.
"""

import pytest
from langchain_core.documents import Document
from unittest.mock import MagicMock


def _make_chunks(n: int) -> list[Document]:
    return [
        Document(
            page_content=f"Chunk number {i} text content.",
            metadata={
                "filename": "policy.pdf",
                "page_number": i,
                "chunk_id": i,
                "upload_timestamp": "2026-07-06T00:00:00Z",
                "doc_type": "pdf",
            },
            id=f"chunk-{i:04d}",
        )
        for i in range(n)
    ]


class TestIndexChunks:
    """Tests for vector_store.index_chunks() with mocked dependencies."""

    def test_returns_correct_chunk_count(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.vector_store import index_chunks

        mock_embeddings.embed_documents.return_value = [[0.1] * 384, [0.2] * 384]
        chunks = _make_chunks(2)

        count = index_chunks(
            chunks=chunks,
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
            document_id="doc-001",
            filename="policy.pdf",
            document_type="pdf",
        )

        assert count == 2

    def test_calls_embed_documents_once(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.vector_store import index_chunks

        mock_embeddings.embed_documents.return_value = [[0.1] * 384]
        chunks = _make_chunks(1)

        index_chunks(
            chunks=chunks,
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
            document_id="doc-002",
            filename="guide.txt",
            document_type="txt",
        )

        mock_embeddings.embed_documents.assert_called_once()

    def test_calls_collection_add(self, mock_embeddings, mock_collection, settings):
        from app.services.vector_store import index_chunks

        mock_embeddings.embed_documents.return_value = [[0.3] * 384, [0.4] * 384]
        chunks = _make_chunks(2)

        index_chunks(
            chunks=chunks,
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
            document_id="doc-003",
            filename="manual.docx",
            document_type="docx",
        )

        mock_collection.add.assert_called_once()
        call_kwargs = mock_collection.add.call_args.kwargs
        assert len(call_kwargs["ids"]) == 2

    def test_empty_chunks_returns_zero_and_skips_add(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.vector_store import index_chunks

        count = index_chunks(
            chunks=[],
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
            document_id="doc-empty",
            filename="empty.txt",
            document_type="txt",
        )

        assert count == 0
        mock_collection.add.assert_not_called()
        mock_embeddings.embed_documents.assert_not_called()

    def test_ids_passed_to_collection_match_chunk_ids(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.vector_store import index_chunks

        chunks = _make_chunks(3)
        mock_embeddings.embed_documents.return_value = [[0.1] * 384] * 3
        expected_ids = [c.id for c in chunks]

        index_chunks(
            chunks=chunks,
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
            document_id="doc-004",
            filename="faq.pdf",
            document_type="pdf",
        )

        actual_ids = mock_collection.add.call_args.kwargs["ids"]
        assert actual_ids == expected_ids
