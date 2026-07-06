"""
test_conversation_service.py — Unit tests for in-memory conversation memory.

Tests session creation, message storage, history trimming, and invalid session handling.
No external I/O occurs.
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.services import conversation_service


def _clear_store():
    """Reset the global in-memory session store between tests."""
    conversation_service._session_store.clear()


class TestGetSessionHistory:
    """Tests for conversation_service.get_session_history()."""

    def setup_method(self):
        _clear_store()

    def test_empty_session_id_raises_value_error(self):
        from app.services.conversation_service import get_session_history

        with pytest.raises(ValueError, match="empty"):
            get_session_history("   ")

    def test_blank_session_id_raises_value_error(self):
        from app.services.conversation_service import get_session_history

        with pytest.raises(ValueError):
            get_session_history("")

    def test_new_session_is_created(self):
        from app.services.conversation_service import get_session_history

        history = get_session_history("session-abc")

        assert history is not None
        assert len(history.messages) == 0

    def test_same_session_id_returns_same_object(self):
        from app.services.conversation_service import get_session_history

        h1 = get_session_history("session-xyz")
        h2 = get_session_history("session-xyz")

        assert h1 is h2

    def test_different_sessions_are_isolated(self):
        from app.services.conversation_service import get_session_history

        h1 = get_session_history("session-1")
        h1.add_messages([HumanMessage(content="Hello from session 1")])

        h2 = get_session_history("session-2")

        assert len(h1.messages) == 1
        assert len(h2.messages) == 0


class TestTrimmedChatMessageHistory:
    """Tests for the rolling-window memory enforcement."""

    def setup_method(self):
        _clear_store()

    def test_messages_within_limit_are_kept(self, settings):
        from app.services.conversation_service import TrimmedChatMessageHistory

        history = TrimmedChatMessageHistory(
            session_id="trim-test-1",
            max_history_messages=10,
        )
        msgs = [HumanMessage(content=f"msg {i}") for i in range(5)]
        history.add_messages(msgs)

        assert len(history.messages) == 5

    def test_messages_exceeding_limit_are_trimmed(self, settings):
        from app.services.conversation_service import TrimmedChatMessageHistory

        limit = 4
        history = TrimmedChatMessageHistory(
            session_id="trim-test-2",
            max_history_messages=limit,
        )
        msgs = [HumanMessage(content=f"msg {i}") for i in range(6)]
        history.add_messages(msgs)

        assert len(history.messages) == limit

    def test_most_recent_messages_are_kept_after_trim(self, settings):
        from app.services.conversation_service import TrimmedChatMessageHistory

        history = TrimmedChatMessageHistory(
            session_id="trim-test-3",
            max_history_messages=3,
        )
        msgs = [HumanMessage(content=f"msg-{i}") for i in range(5)]
        history.add_messages(msgs)

        # Only last 3 messages should remain
        contents = [m.content for m in history.messages]
        assert "msg-2" in contents
        assert "msg-3" in contents
        assert "msg-4" in contents
        assert "msg-0" not in contents
        assert "msg-1" not in contents

    def test_alternating_human_and_ai_messages_stored(self, settings):
        from app.services.conversation_service import TrimmedChatMessageHistory

        history = TrimmedChatMessageHistory(
            session_id="trim-test-4",
            max_history_messages=10,
        )
        history.add_messages([
            HumanMessage(content="What is the return policy?"),
            AIMessage(content="Returns within 30 days."),
        ])

        assert len(history.messages) == 2
        assert isinstance(history.messages[0], HumanMessage)
        assert isinstance(history.messages[1], AIMessage)
