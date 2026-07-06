"""
conversation_service.py — In-memory conversational memory layer.
"""

from typing import Dict, List

from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global in-memory dictionary acting as our session store for this phase.
_session_store: Dict[str, ChatMessageHistory] = {}


class TrimmedChatMessageHistory(ChatMessageHistory):
    """
    Subclass of ChatMessageHistory that automatically enforces a rolling window limit
    upon adding new messages, avoiding memory overflow.
    """
    session_id: str
    max_history_messages: int

    def __init__(self, session_id: str, max_history_messages: int, **kwargs):
        super().__init__(session_id=session_id, max_history_messages=max_history_messages, **kwargs)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add new messages and immediately trim the history if it exceeds the limit."""
        super().add_messages(messages)
        
        # Enforce memory limits (trim old messages)
        if len(self.messages) > self.max_history_messages:
            self.messages = self.messages[-self.max_history_messages :]
            logger.warning(
                "conversation_trimmed",
                extra={
                    "session_id": self.session_id,
                    "message_count": len(self.messages),
                    "history_length": self.max_history_messages,
                },
            )
            
        logger.info(
            "conversation_updated",
            extra={
                "session_id": self.session_id,
                "message_count": len(self.messages),
                "history_length": len(self.messages),
            },
        )


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Retrieve or create an in-memory conversation history for the given session_id.
    
    This factory function is passed to RunnableWithMessageHistory.
    """
    if not session_id or not session_id.strip():
        logger.error("invalid_session_id", extra={"session_id": session_id})
        raise ValueError("Invalid session_id: Session ID cannot be empty.")
        
    settings = get_settings()

    if session_id not in _session_store:
        _session_store[session_id] = TrimmedChatMessageHistory(
            session_id=session_id,
            max_history_messages=settings.max_history_messages
        )
        logger.info(
            "conversation_created",
            extra={
                "session_id": session_id, 
                "message_count": 0, 
                "history_length": 0
            },
        )
    else:
        history = _session_store[session_id]
        if len(history.messages) == 0:
            # Handle empty history (e.g. newly created but not yet updated)
            pass
            
        logger.info(
            "conversation_retrieved",
            extra={
                "session_id": session_id, 
                "message_count": len(history.messages), 
                "history_length": len(history.messages)
            },
        )
        
    return _session_store[session_id]
