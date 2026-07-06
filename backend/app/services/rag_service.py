"""
rag_service.py — Retrieval-Augmented Generation layer.

Converts retrieved document chunks into a grounded answer using the local Ollama LLM.
This service is solely responsible for response generation. It never retrieves documents directly.
"""

import time
from typing import List, Set, Tuple

from langchain_core.language_models import BaseChatModel

from langchain_core.runnables.history import RunnableWithMessageHistory

from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.schemas.chat import ChatResponse, SourceAttribution
from app.schemas.retrieval import RetrievalResult
from app.services.conversation_service import get_session_history
from app.services.prompt_templates import get_rag_prompt
from app.utils.text_utils import sanitize_context_for_prompt

logger = get_logger(__name__)

# The strict fallback string dictated by the business requirements
FALLBACK_RESPONSE = "I don't know."


def generate_answer(
    session_id: str,
    query: str,
    retrieval_result: RetrievalResult,
    chat_model: BaseChatModel,
) -> ChatResponse:
    """
    Generate an answer from the retrieved chunks using the LLM.

    If the retrieval result has zero chunks, this function immediately returns
    the fallback string without calling the LLM.

    Parameters
    ----------
    session_id : str
        The unique identifier for the conversation session.
    query : str
        The user's original question.
    retrieval_result : RetrievalResult
        The filtered chunks supplied by the RetrievalService.
    chat_model : BaseChatModel
        The injected ChatOllama language model.

    Returns
    -------
    ChatResponse
        The generated text, timing metadata, and deduplicated source attributions.
    """
    start_time = time.perf_counter()
    query_length = len(query)

    # 1. Fallback Gate: No chunks = No LLM call
    if retrieval_result.total_chunks == 0:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "generation_completed",
            extra={
                "query_length": query_length,
                "context_chunks": 0,
                "response_time_ms": duration_ms,
                "fallback_used": True,
            },
        )
        return ChatResponse(
            answer=FALLBACK_RESPONSE,
            sources=[],
            response_time_ms=duration_ms,
            fallback_used=True,
        )

    logger.info(
        "generation_started",
        extra={
            "query_length": query_length,
            "context_chunks": retrieval_result.total_chunks,
        },
    )

    # 2. Build Context String and Extract Sources
    context_texts: List[str] = []
    seen_sources: Set[Tuple[str, int]] = set()
    sources: List[SourceAttribution] = []

    for chunk in retrieval_result.retrieved_chunks:
        context_texts.append(chunk.text)

        # Extract and deduplicate source attribution
        filename = chunk.filename
        page_num = chunk.page_number
        source_key = (filename, page_num)

        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append(SourceAttribution(filename=filename, page_number=page_num))

    context_str = "\n\n---\n\n".join(context_texts)

    # 3. Apply Context Sanitization
    context_str, patterns_removed = sanitize_context_for_prompt(context_str)
    if patterns_removed > 0:
        logger.warning(
            "context_sanitized",
            extra={
                "query_length": query_length,
                "patterns_removed": patterns_removed,
            },
        )

    # 4. Build LCEL Chain with Message History
    prompt_template = get_rag_prompt()
    chain = prompt_template | chat_model
    
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="query",
        history_messages_key="history",
    )

    # 5. Invoke LLM
    try:
        response = chain_with_history.invoke(
            {"query": query, "context": context_str},
            config={"configurable": {"session_id": session_id}}
        )
        answer = str(response.content).strip()
    except Exception as e:
        logger.error("generation_failed", extra={"error": f"LLM invocation failed: {str(e)}"})
        raise LLMError(message="LLM invocation failed.") from e

    # 6. Fallback check on LLM response
    fallback_used = answer == FALLBACK_RESPONSE
    # If the LLM returns fallback, we strip the sources as no context was successfully applied
    if fallback_used:
        sources = []

    duration_ms = (time.perf_counter() - start_time) * 1000

    # 7. Log and Return
    logger.info(
        "generation_completed",
        extra={
            "query_length": query_length,
            "context_chunks": retrieval_result.total_chunks,
            "response_time_ms": duration_ms,
            "fallback_used": fallback_used,
            "patterns_removed": patterns_removed,
        },
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        response_time_ms=duration_ms,
        fallback_used=fallback_used,
    )
