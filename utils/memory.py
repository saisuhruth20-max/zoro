"""
Conversation memory store — keeps per-user chat history for the AI.
"""

from collections import defaultdict, deque
from typing import TypedDict

from config import Config


class Message(TypedDict):
    role: str    # "user" | "assistant"
    content: str


class ConversationMemory:
    """
    In-memory store for per-user conversation history.

    Each user gets a fixed-size deque that auto-drops the oldest turn
    when the limit is reached, keeping memory footprint bounded.
    """

    def __init__(self, max_turns: int = Config.MEMORY_MAX_TURNS) -> None:
        self._max_turns = max_turns
        # Each deque holds Message dicts
        self._store: dict[int, deque[Message]] = defaultdict(
            lambda: deque(maxlen=max_turns * 2)  # *2 because each turn = user + assistant
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def add_user_message(self, user_id: int, content: str) -> None:
        """Append a user message to the user's history."""
        self._store[user_id].append({"role": "user", "content": content})

    def add_assistant_message(self, user_id: int, content: str) -> None:
        """Append an assistant message to the user's history."""
        self._store[user_id].append({"role": "assistant", "content": content})

    def get_history(self, user_id: int) -> list[Message]:
        """Return the full conversation history for a user as a list."""
        return list(self._store[user_id])

    def clear(self, user_id: int) -> None:
        """Clear conversation history for a specific user."""
        self._store[user_id].clear()

    def clear_all(self) -> None:
        """Clear all stored conversation histories."""
        self._store.clear()

    def has_history(self, user_id: int) -> bool:
        """Return True if the user has any stored messages."""
        return bool(self._store[user_id])


# Module-level singleton — import and use this instance everywhere
memory = ConversationMemory()
