"""
test_chat_endpoint.py — Integration tests for POST /api/v1/chat/message.

All AI services (Ollama, ChromaDB) are mocked via the TestClient fixture
defined in conftest.py. No real inference occurs.
"""

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch


class TestChatEndpoint:
    """Integration tests for the /api/v1/chat/message endpoint."""

    # ------------------------------------------------------------------ #
    # Validation tests
    # ------------------------------------------------------------------ #

    def test_missing_session_id_returns_422(self, test_client):
        response = test_client.post(
            "/api/v1/chat/message",
            json={"message": "What is the return policy?"},
        )
        assert response.status_code == 422

    def test_missing_message_returns_422(self, test_client):
        response = test_client.post(
            "/api/v1/chat/message",
            json={"session_id": str(uuid.uuid4())},
        )
        assert response.status_code == 422

    def test_empty_message_returns_422(self, test_client):
        response = test_client.post(
            "/api/v1/chat/message",
            json={"session_id": str(uuid.uuid4()), "message": ""},
        )
        assert response.status_code == 422

    def test_empty_session_id_returns_422(self, test_client):
        response = test_client.post(
            "/api/v1/chat/message",
            json={"session_id": "", "message": "Hello?"},
        )
        assert response.status_code == 422

    # ------------------------------------------------------------------ #
    # Happy path: fallback (no retrieval results)
    # ------------------------------------------------------------------ #

    def test_no_retrieval_returns_fallback_answer(self, test_client):
        """When ChromaDB returns nothing, the endpoint should return the fallback."""
        from app.services.rag_service import FALLBACK_RESPONSE

        # mock_collection already returns empty results by default (from conftest)
        with patch("app.api.v1.endpoints.chat.retrieval_service") as mock_ret, \
             patch("app.api.v1.endpoints.chat.rag_service") as mock_rag:

            from app.schemas.retrieval import RetrievalResult
            from app.schemas.chat import ChatResponse

            mock_ret.retrieve.return_value = RetrievalResult(
                query="unknown topic",
                retrieved_chunks=[],
                total_chunks=0,
                max_similarity_score=0.0,
                retrieval_duration_ms=10.0,
            )
            mock_rag.generate_answer.return_value = ChatResponse(
                answer=FALLBACK_RESPONSE,
                sources=[],
                response_time_ms=5.0,
                fallback_used=True,
            )

            response = test_client.post(
                "/api/v1/chat/message",
                json={"session_id": str(uuid.uuid4()), "message": "What is 2+2?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == FALLBACK_RESPONSE
        assert data["fallback_used"] is True
        assert data["sources"] == []

    # ------------------------------------------------------------------ #
    # Happy path: successful RAG answer with sources
    # ------------------------------------------------------------------ #

    def test_successful_answer_with_sources(self, test_client):
        """When retrieval finds chunks, the answer should include source attributions."""
        with patch("app.api.v1.endpoints.chat.retrieval_service") as mock_ret, \
             patch("app.api.v1.endpoints.chat.rag_service") as mock_rag:

            from app.schemas.retrieval import RetrievalResult, RetrievedChunk
            from app.schemas.chat import ChatResponse
            from app.schemas.chat import SourceAttribution

            mock_ret.retrieve.return_value = RetrievalResult(
                query="return policy",
                retrieved_chunks=[
                    RetrievedChunk(
                        chunk_id="abc",
                        text="Returns within 30 days.",
                        similarity_score=0.9,
                        filename="policy.pdf",
                        page_number=3,
                        metadata={},
                    )
                ],
                total_chunks=1,
                max_similarity_score=0.9,
                retrieval_duration_ms=25.0,
            )
            mock_rag.generate_answer.return_value = ChatResponse(
                answer="Returns are accepted within 30 days of purchase.",
                sources=[SourceAttribution(filename="policy.pdf", page_number=3)],
                response_time_ms=200.0,
                fallback_used=False,
            )

            response = test_client.post(
                "/api/v1/chat/message",
                json={"session_id": str(uuid.uuid4()), "message": "What is the return policy?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["fallback_used"] is False
        assert len(data["sources"]) == 1
        assert data["sources"][0]["filename"] == "policy.pdf"
        assert data["sources"][0]["page_number"] == 3

    # ------------------------------------------------------------------ #
    # Error handling
    # ------------------------------------------------------------------ #

    def test_retrieval_error_returns_503(self, test_client):
        from app.core.exceptions import RetrievalError

        with patch("app.api.v1.endpoints.chat.retrieval_service") as mock_ret:
            mock_ret.retrieve.side_effect = RetrievalError(message="ChromaDB unavailable")

            response = test_client.post(
                "/api/v1/chat/message",
                json={"session_id": str(uuid.uuid4()), "message": "What are your hours?"},
            )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "retrieval_error"

    def test_llm_error_returns_503(self, test_client):
        from app.core.exceptions import LLMError
        from app.schemas.retrieval import RetrievalResult

        with patch("app.api.v1.endpoints.chat.retrieval_service") as mock_ret, \
             patch("app.api.v1.endpoints.chat.rag_service") as mock_rag:

            mock_ret.retrieve.return_value = RetrievalResult(
                query="some query",
                retrieved_chunks=[],
                total_chunks=0,
                max_similarity_score=0.0,
                retrieval_duration_ms=5.0,
            )
            mock_rag.generate_answer.side_effect = LLMError(message="Ollama offline")

            response = test_client.post(
                "/api/v1/chat/message",
                json={"session_id": str(uuid.uuid4()), "message": "Help me."},
            )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "llm_error"

    # ------------------------------------------------------------------ #
    # Response schema
    # ------------------------------------------------------------------ #

    def test_response_schema_has_all_required_fields(self, test_client):
        with patch("app.api.v1.endpoints.chat.retrieval_service") as mock_ret, \
             patch("app.api.v1.endpoints.chat.rag_service") as mock_rag:

            from app.schemas.retrieval import RetrievalResult
            from app.schemas.chat import ChatResponse
            from app.services.rag_service import FALLBACK_RESPONSE

            mock_ret.retrieve.return_value = RetrievalResult(
                query="q", retrieved_chunks=[], total_chunks=0,
                max_similarity_score=0.0, retrieval_duration_ms=1.0,
            )
            mock_rag.generate_answer.return_value = ChatResponse(
                answer=FALLBACK_RESPONSE, sources=[],
                response_time_ms=1.0, fallback_used=True,
            )

            response = test_client.post(
                "/api/v1/chat/message",
                json={"session_id": str(uuid.uuid4()), "message": "Hello?"},
            )

        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "response_time_ms" in data
        assert "fallback_used" in data
