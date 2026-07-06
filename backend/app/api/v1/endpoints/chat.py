"""
chat.py — Chat / Q&A endpoints (stubs).

These stubs are wired into the router now so the API surface is complete.
The RAG chain, history management, and similarity gate will be implemented
in Phase 3 and injected here via FastAPI's Depends().

Endpoints:
  POST  /api/v1/chat/message              Send a message and receive an answer
  GET   /api/v1/chat/history/{session_id} Retrieve conversation history
"""

from typing import Annotated

from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    ChatModelDep,
    ChromaCollectionDep,
    EmbeddingsDep,
    SettingsDep,
)
from app.core.exceptions import LLMError, RetrievalError
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import rag_service, retrieval_service

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description=(
        "Accepts a session_id and user message. Retrieves relevant context "
        "and generates a grounded answer via RAG."
    ),
)
async def send_message(
    request: Annotated[ChatRequest, Body(..., description="The chat request payload")],
    settings: SettingsDep,
    collection: ChromaCollectionDep,
    embeddings_client: EmbeddingsDep,
    chat_model: ChatModelDep,
) -> ChatResponse:
    """
    Orchestrate the RAG pipeline.
    """
    logger.info(
        "chat_request_received",
        extra={
            "session_id": request.session_id,
            "query_length": len(request.message),
        },
    )

    try:
        # 1. Retrieve context
        retrieval_result = retrieval_service.retrieve(
            query=request.message,
            collection=collection,
            embeddings_client=embeddings_client,
            settings=settings,
        )

        # 2. Generate answer
        chat_response = rag_service.generate_answer(
            session_id=request.session_id,
            query=request.message,
            retrieval_result=retrieval_result,
            chat_model=chat_model,
        )

        logger.info(
            "chat_request_completed",
            extra={
                "session_id": request.session_id,
                "response_time_ms": chat_response.response_time_ms,
                "fallback_used": chat_response.fallback_used,
            },
        )

        return chat_response

    except Exception as e:
        logger.error(
            "chat_request_failed",
            extra={
                "session_id": request.session_id,
                "error": str(e),
                "type": type(e).__name__,
            },
        )
        raise


@router.get(
    "/history/{session_id}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Get conversation history (not yet implemented)",
)
async def get_history(session_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "detail": (
                f"History retrieval for session_id='{session_id}' "
                "will be implemented in Phase 3."
            )
        },
    )
