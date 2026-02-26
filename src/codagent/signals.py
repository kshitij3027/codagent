"""Two-tier SIGINT (Ctrl-C) handler for the agent REPL.

Tier 1 -- Ctrl-C while the agent is running: cancels the current agent task
and returns the user to the input prompt (SGNL-01).

Tier 2 -- Ctrl-C at the idle input prompt (no agent task running): exits the
program cleanly (SGNL-02).

Uses ``loop.add_signal_handler()`` which is event-loop-safe, unlike the
stdlib ``signal.signal()`` approach.

Phase 2 note: prompt-toolkit's ``prompt_async()`` is fully async and does not
use ``run_in_executor`` with a blocking thread. This means ``SystemExit`` now
propagates cleanly -- prompt-toolkit restores terminal state (raw mode, cursor)
on exit. The forced-exit workaround from Phase 1 is no longer needed.
"""

from __future__ import annotations

import asyncio
import signal


class SignalState:
    """Shared mutable state between the REPL loop and the signal handler.

    The ``agent_task`` attribute is set to the running :class:`asyncio.Task`
    when the agent is processing a turn, and cleared back to ``None`` when
    the turn completes (or is cancelled).
    """

    def __init__(self) -> None:
        self.agent_task: asyncio.Task | None = None


def setup_signal_handler(
    loop: asyncio.AbstractEventLoop, state: SignalState
) -> None:
    """Register a two-tier SIGINT handler on the event loop.

    Args:
        loop: The running asyncio event loop.
        state: Shared state that tracks the active agent task.
    """

    def _handle_sigint() -> None:
        if state.agent_task is not None and not state.agent_task.done():
            # Agent is running -- cancel it (returns to prompt)
            state.agent_task.cancel()
        else:
            # Idle -- exit the program cleanly.
            # SystemExit propagates up through prompt-toolkit's prompt_async(),
            # which properly restores terminal state before exiting.
            raise SystemExit(0)

    loop.add_signal_handler(signal.SIGINT, _handle_sigint)
