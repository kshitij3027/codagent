"""Two-tier SIGINT (Ctrl-C) handler for the agent REPL.

Tier 1 -- Ctrl-C while the agent is running: cancels the current agent task
and returns the user to the input prompt (SGNL-01).

Tier 2 -- Ctrl-C at the idle input prompt (no agent task running): exits the
program cleanly (SGNL-02).

Uses ``loop.add_signal_handler()`` which is event-loop-safe, unlike the
stdlib ``signal.signal()`` approach.
"""

from __future__ import annotations

import asyncio
import os
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
            # Idle -- exit the program.
            # Use os._exit(0) instead of raise SystemExit(0) because the
            # input() thread (run_in_executor) blocks Python's shutdown
            # sequence — threading._shutdown tries to join the blocked
            # thread, causing a deadlock and traceback.  os._exit bypasses
            # the asyncio/threading shutdown entirely.  Safe here because
            # there is no state to persist at idle.
            print("\nGoodbye.")
            os._exit(0)

    loop.add_signal_handler(signal.SIGINT, _handle_sigint)
