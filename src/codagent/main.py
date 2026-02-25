"""Main REPL loop, startup, shutdown, and entry point.

This is the entry point that ties everything together: loads config, creates
the agent, sets up signal handling, and runs the interactive prompt loop.
"""

from __future__ import annotations

import asyncio
import sys

from codagent import __version__
from codagent.agent import create_agent, run_agent_turn
from codagent.config import load_settings
from codagent.conversation import ConversationHistory
from codagent.models import get_default_model, get_model
from codagent.signals import SignalState, setup_signal_handler


# ---------------------------------------------------------------------------
# Async main
# ---------------------------------------------------------------------------


async def async_main() -> None:
    """Run the interactive coding agent REPL.

    1. Startup: load settings, create agent, set up signal handler, print banner.
    2. REPL loop: prompt -> agent turn -> print response -> repeat.
    3. Shutdown: print goodbye and exit.
    """
    # -- Startup --
    settings = load_settings()
    model_string = get_default_model()
    agent = create_agent(model_string)
    history = ConversationHistory()
    signal_state = SignalState()

    loop = asyncio.get_event_loop()
    setup_signal_handler(loop, signal_state)

    # Derive a friendly name from the model string for the banner
    friendly_name = settings.default_model
    print()
    print(f"  codagent v{__version__}")
    print(f"  Model: {friendly_name} ({model_string})")
    print(f"  Mode: {settings.mode}")
    print(f"  Type your request or Ctrl-C to exit.")
    print()

    # -- REPL Loop --
    while True:
        try:
            # Non-blocking input via run_in_executor keeps the event loop
            # responsive for Ctrl-C during the input prompt (Pitfall 1 & 7).
            user_input = await loop.run_in_executor(None, _get_input)
        except (EOFError, KeyboardInterrupt):
            # EOFError: piped input ended. KeyboardInterrupt: fallback.
            break

        if not user_input or not user_input.strip():
            continue

        stripped = user_input.strip().lower()
        if stripped in ("exit", "quit"):
            break

        # Create the agent task so the signal handler can cancel it
        signal_state.agent_task = asyncio.create_task(
            run_agent_turn(agent, user_input.strip(), history)
        )

        try:
            response = await signal_state.agent_task
        except asyncio.CancelledError:
            # SGNL-01: Ctrl-C during agent run -- return to prompt
            print("\n[interrupted]")
            continue
        except Exception as e:
            # Don't crash the loop on model/network errors
            print(f"\n[error] {e}")
            continue
        finally:
            # Clear the task so Ctrl-C at idle exits the program (SGNL-02)
            signal_state.agent_task = None

        print(response)

    # -- Shutdown --
    print("Goodbye.")


def _get_input() -> str:
    """Read a line of user input (runs in a thread via run_in_executor)."""
    return input(">>> ")


# ---------------------------------------------------------------------------
# Synchronous entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Synchronous entry point for the ``codagent`` console script.

    Wraps :func:`async_main` in ``asyncio.run()`` and suppresses
    traceback noise on Ctrl-C / SystemExit.
    """
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        # Suppress traceback on Ctrl-C at idle prompt
        pass


if __name__ == "__main__":
    main()
