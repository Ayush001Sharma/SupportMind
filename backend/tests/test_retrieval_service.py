"""
test_retrieval_service.py — Unit tests for retrieval filtering and thresholds.

ChromaDB and embeddings are fully mocked so no real search occurs.
Tests verify: empty results, threshold filtering, page-level deduplication,
sorting by score, and proper error handling.
"""

import pytest
from unittest.mock import MagicMock

from app.core.exceptions import RetrievalError


def _build_chroma_response(
    ids: list[str],
    distances: list[float],
    texts: list[str],
    metas: list[dict],
) -> dict:
    return {
        "ids": [ids],
        "distances": [distances],
        "documents": [texts],
        "metadatas": [metas],
    }


class TestRetrievalService:
    """Unit tests for retrieval_service.retrieve()."""

    def test_empty_query_raises_retrieval_error(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.retrieval_service import retrieve

        with pytest.raises(RetrievalError, match="empty"):
            retrieve(
                query="   ",
                collection=mock_collection,
                embeddings_client=mock_embeddings,
                settings=settings,
            )

    def test_empty_chroma_result_returns_zero_chunks(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.retrieval_service import retrieve

        # Mock: ChromaDB returns no results
        mock_collection.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "documents": [[]],
            "metadatas": [[]],
        }
        mock_embeddings.embed_query.return_value = [0.1] * 384

        result = retrieve(
            query="What is the return policy?",
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
        )

        assert result.total_chunks == 0
        assert result.retrieved_chunks == []

    def test_chunks_below_threshold_are_filtered(
        self, mock_embeddings, mock_collection, settings
    ):
        """Chunks with similarity < threshold must not appear in results."""
        from app.services.retrieval_service import retrieve

        # distance=0.9 → similarity=0.1, well below the default 0.35 threshold
        mock_collection.query.return_value = _build_chroma_response(
            ids=["chunk-1"],
            distances=[0.9],
            texts=["Some irrelevant text."],
            metas=[{"filename": "doc.pdf", "page_number": 1}],
        )
        mock_embeddings.embed_query.return_value = [0.1] * 384

        result = retrieve(
            query="return policy",
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
        )

        assert result.total_chunks == 0

    def test_chunks_above_threshold_are_returned(
        self, mock_embeddings, mock_collection, settings
    ):
        """Chunks with similarity >= threshold must be included."""
        from app.services.retrieval_service import retrieve

        # distance=0.2 → similarity=0.8, above 0.35 threshold
        mock_collection.query.return_value = _build_chroma_response(
            ids=["chunk-1"],
            distances=[0.2],
            texts=["Returns are accepted within 30 days."],
            metas=[{"filename": "policy.pdf", "page_number": 2}],
        )
        mock_embeddings.embed_query.return_value = [0.1] * 384

        result = retrieve(
            query="return policy",
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
        )

        assert result.total_chunks == 1
        assert result.retrieved_chunks[0].similarity_score == pytest.approx(0.8)

    def test_duplicate_pages_are_deduplicated(
        self, mock_embeddings, mock_collection, settings
    ):
        """Two chunks from the same (filename, page_number) must produce only one result."""
        from app.services.retrieval_service import retrieve

        mock_collection.query.return_value = _build_chroma_response(
            ids=["chunk-1", "chunk-2"],
            distances=[0.1, 0.15],
            texts=["First chunk on page 1.", "Second chunk on page 1."],
            metas=[
                {"filename": "policy.pdf", "page_number": 1},
                {"filename": "policy.pdf", "page_number": 1},
            ],
        )
        mock_embeddings.embed_query.return_value = [0.1] * 384

        result = retrieve(
            query="some query",
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
        )

        assert result.total_chunks == 1

    def test_results_sorted_by_similarity_descending(
        self, mock_embeddings, mock_collection, settings
    ):
        """Results must be sorted from highest to lowest similarity score."""
        from app.services.retrieval_service import retrieve

        mock_collection.query.return_value = _build_chroma_response(
            ids=["chunk-low", "chunk-high"],
            distances=[0.4, 0.1],        # similarities: 0.6 and 0.9
            texts=["Lower relevance.", "Higher relevance."],
            metas=[
                {"filename": "doc.pdf", "page_number": 1},
                {"filename": "doc.pdf", "page_number": 2},
            ],
        )
        mock_embeddings.embed_query.return_value = [0.1] * 384

        result = retrieve(
            query="some question",
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
        )

        scores = [c.similarity_score for c in result.retrieved_chunks]
        assert scores == sorted(scores, reverse=True)

    def test_embedding_failure_raises_retrieval_error(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.retrieval_service import retrieve

        mock_embeddings.embed_query.side_effect = RuntimeError("Ollama connection refused")

        with pytest.raises(RetrievalError, match="embedding"):
            retrieve(
                query="valid query",
                collection=mock_collection,
                embeddings_client=mock_embeddings,
                settings=settings,
            )

    def test_chroma_query_failure_raises_retrieval_error(
        self, mock_embeddings, mock_collection, settings
    ):
        from app.services.retrieval_service import retrieve

        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_collection.query.side_effect = Exception("ChromaDB timeout")

        with pytest.raises(RetrievalError, match="ChromaDB"):
            retrieve(
                query="valid query",
                collection=mock_collection,
                embeddings_client=mock_embeddings,
                settings=settings,
            )

    def test_max_similarity_score_tracked(
        self, mock_embeddings, mock_collection, settings
    ):
        """max_similarity_score must reflect the highest score before threshold filtering."""
        from app.services.retrieval_service import retrieve

        # Two chunks: one passes (dist=0.1), one fails (dist=0.9)
        mock_collection.query.return_value = _build_chroma_response(
            ids=["c1", "c2"],
            distances=[0.1, 0.9],
            texts=["Relevant text.", "Irrelevant text."],
            metas=[
                {"filename": "a.pdf", "page_number": 1},
                {"filename": "a.pdf", "page_number": 2},
            ],
        )
        mock_embeddings.embed_query.return_value = [0.1] * 384

        result = retrieve(
            query="some query",
            collection=mock_collection,
            embeddings_client=mock_embeddings,
            settings=settings,
        )

        # max score should be the best one (1-0.1=0.9), not just the filtered ones
        assert result.max_similarity_score == pytest.approx(0.9)
        assert result.total_chunks == 1
