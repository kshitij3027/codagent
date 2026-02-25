"""Conversation history management for multi-turn agent interactions.

Wraps a list of Pydantic AI messages, providing get/update/clear operations.
The agent passes this history to each agent.run() call so the model retains
context from previous turns within a session.
"""

from __future__ import annotations


class ConversationHistory:
    """Accumulates Pydantic AI messages across turns.

    Pydantic AI expects ``message_history=None`` on the first turn (not an
    empty list), so :meth:`get` returns ``None`` when the history is empty.
    """

    def __init__(self) -> None:
        self._messages: list = []

    def get(self) -> list | None:
        """Return the message list, or ``None`` if no history yet.

        Pydantic AI treats ``None`` as "no prior history" which is the
        correct signal for the very first turn.
        """
        return self._messages if self._messages else None

    def update(self, messages: list) -> None:
        """Replace the stored history with a new message list.

        Typically called with ``result.all_messages()`` after each turn.
        Pydantic AI returns a new list each call, so storing it directly
        is safe (no aliasing issues).
        """
        self._messages = messages

    def clear(self) -> None:
        """Reset the history to empty (e.g. for a ``/new`` command)."""
        self._messages = []

    def turn_count(self) -> int:
        """Count user messages in the history.

        Each user turn produces a ``ModelRequest`` that contains at least
        one ``UserPromptPart``.  We count messages whose ``kind`` is
        ``'request'`` as a proxy for turn count.
        """
        count = 0
        for msg in self._messages:
            # Pydantic AI message objects have a 'kind' attribute
            if hasattr(msg, "kind") and msg.kind == "request":
                count += 1
        return count
