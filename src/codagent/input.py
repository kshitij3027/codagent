"""Prompt-toolkit input layer for the coding agent.

Provides an async prompt with persistent command history, fish-shell-style
slash command completion with descriptions, and multi-line key bindings
(Enter submits, Escape+Enter inserts a newline).

Usage:
    session = create_prompt_session(history_path)
    user_text = await get_user_input(session)
"""

from __future__ import annotations

import os
from typing import Dict

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings


# ---------------------------------------------------------------------------
# Slash-command completer (fish-shell-style dropdown with descriptions)
# ---------------------------------------------------------------------------

class SlashCommandCompleter(Completer):
    """Complete slash commands with descriptions in a dropdown menu.

    Only activates when the cursor is at the beginning of a line (or the
    entire text is a partial slash command).  This prevents the completer
    from triggering mid-sentence.
    """

    COMMANDS: Dict[str, str] = {
        "/help": "Show available commands",
        "/model": "Switch the active model",
        "/approval": "Switch to approval mode",
        "/yolo": "Switch to yolo mode (auto-execute)",
        "/new": "Clear conversation history",
        "/exit": "Exit the agent",
    }

    def get_completions(
        self,
        document: Document,
        complete_event: object,
    ):
        """Yield matching slash-command completions.

        Handles two completion scenarios:
        1. Command completion: ``/mo<TAB>`` -> ``/model``
        2. Argument completion: ``/model cl<TAB>`` -> ``/model claude``

        Currently only ``/model`` supports argument completion (model names).
        """
        text = document.text_before_cursor

        # Only complete when the text is *only* a slash-command fragment
        # (i.e., starts with "/" and has no preceding non-slash content).
        stripped = text.lstrip()
        if not stripped.startswith("/"):
            return

        # Don't trigger if there's other content before the slash
        # (e.g., "some text /he" should NOT trigger)
        if stripped != text.lstrip() and not text.startswith("/"):
            return

        # Branch: argument completion for commands that support it
        if " " in stripped:
            parts = stripped.split(maxsplit=1)
            cmd_part = parts[0].lower()
            arg_part = parts[1] if len(parts) > 1 else ""

            if cmd_part == "/model":
                # Lazy import to avoid circular imports and keep startup fast
                from codagent.models import list_models

                for name in list_models():
                    if name.startswith(arg_part.lower()):
                        yield Completion(
                            name,
                            start_position=-len(arg_part),
                            display_meta="model",
                        )
            # For all other commands with arguments: no completions
            return

        for cmd, desc in self.COMMANDS.items():
            if cmd.startswith(stripped):
                yield Completion(
                    cmd,
                    start_position=-len(stripped),
                    display_meta=desc,
                )


# ---------------------------------------------------------------------------
# Key bindings: Enter submits, Escape+Enter (Alt+Enter) inserts newline
# ---------------------------------------------------------------------------

_bindings = KeyBindings()


@_bindings.add("escape", "enter")
def _insert_newline(event) -> None:
    """Insert a newline on Escape+Enter (or Alt+Enter).

    This is the portable alternative to Shift+Enter, which is not
    reliably distinguishable from Enter across terminal emulators
    (see prompt-toolkit pitfall #4 from research).
    """
    event.current_buffer.insert_text("\n")


# ---------------------------------------------------------------------------
# Factory: create a fully-configured PromptSession
# ---------------------------------------------------------------------------

def create_prompt_session(history_path: str) -> PromptSession:
    """Create a PromptSession with history, completions, and key bindings.

    The history directory is created automatically if it does not exist
    (Pitfall 5 from research: FileHistory does not create parent dirs).

    Args:
        history_path: Absolute path to the persistent history file
                      (e.g., ``~/.coding-agent/history`` — should be
                      pre-expanded via ``os.path.expanduser``).

    Returns:
        A configured ``PromptSession`` ready for ``prompt_async()``.
    """
    os.makedirs(os.path.dirname(history_path), exist_ok=True)

    return PromptSession(
        message="\u276f ",            # "❯ " — minimal symbol prompt
        history=FileHistory(history_path),
        completer=SlashCommandCompleter(),
        key_bindings=_bindings,
        multiline=False,              # Enter submits
        enable_history_search=True,
        auto_suggest=AutoSuggestFromHistory(),
    )


# ---------------------------------------------------------------------------
# Async input helper (called by the REPL loop)
# ---------------------------------------------------------------------------

async def get_user_input(session: PromptSession) -> str:
    """Prompt the user for input asynchronously and return stripped text.

    This is a thin wrapper around ``session.prompt_async()`` so the REPL
    loop does not depend directly on prompt-toolkit internals.

    Args:
        session: A ``PromptSession`` created by ``create_prompt_session``.

    Returns:
        The user's input with leading/trailing whitespace removed.
    """
    text = await session.prompt_async()
    return text.strip()
