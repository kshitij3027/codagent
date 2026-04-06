"""Main REPL loop, startup, shutdown, and entry point.

This is the entry point that ties everything together: loads config, creates
the agent, sets up signal handling, and runs the interactive prompt loop.

Phase 2 integration: Rich display (panels, spinner, streaming), prompt-toolkit
input (async, history, completions, multi-line), and streaming agent execution
via agent.iter() with node-level display control.
"""

from __future__ import annotations

import asyncio

from prompt_toolkit.patch_stdout import patch_stdout

from codagent import __version__
from codagent.agent import create_agent, run_agent_turn_streaming
from codagent.config import load_settings
from codagent.conversation import ConversationHistory
from codagent.display import Display
from codagent.input import create_prompt_session, get_user_input
from codagent.models import get_default_model
from codagent.signals import SignalState, setup_signal_handler
from codagent.tools.shell import set_display


# ---------------------------------------------------------------------------
# Async main
# ---------------------------------------------------------------------------


async def async_main() -> None:
    """Run the interactive coding agent REPL.

    1. Startup: load settings, create agent, set up signal handler, render banner.
    2. REPL loop: prompt (prompt-toolkit) -> echo user panel -> streaming agent
       turn -> repeat.
    3. Shutdown: print goodbye and exit.

    Uses ``patch_stdout()`` to prevent Rich console output from corrupting the
    prompt-toolkit input line (Pattern 6 from Phase 2 research).
    """
    # -- Startup --
    settings = load_settings()
    model_string = get_default_model()
    agent = create_agent(model_string)
    history = ConversationHistory()
    signal_state = SignalState()
    display = Display()
    session = create_prompt_session(settings.history_path)

    # Configure shell tool to use display for streaming output and styled approval
    set_display(display)

    loop = asyncio.get_event_loop()
    setup_signal_handler(loop, signal_state)

    # Rich-styled startup banner
    friendly_name = settings.default_model
    display.console.print()
    display.console.print(f"  [bold bright_cyan]codagent[/bold bright_cyan] v{__version__}")
    display.console.print(f"  [dim]Model:[/dim] {friendly_name} ({model_string})")
    display.console.print(f"  [dim]Mode:[/dim] {settings.mode}")
    display.console.print(f"  [dim]Enter submits \u00b7 Escape+Enter for newline \u00b7 Ctrl-C to exit[/dim]")
    display.console.print()

    # -- REPL Loop --
    with patch_stdout():
        while True:
            try:
                user_input = await get_user_input(session)
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input or not user_input.strip():
                continue

            stripped = user_input.strip()
            if stripped.lower() in ("exit", "quit", "/exit"):
                break

            # Handle slash commands before agent turn
            if stripped.startswith("/"):
                from codagent.commands import dispatch_slash_command
                if dispatch_slash_command(stripped, agent, settings, history, display):
                    continue
                # Unknown slash command -- show error, do NOT send to agent
                display.console.print(
                    f"[bold red]Unknown command:[/bold red] {stripped.split()[0]}. "
                    "Type /help for available commands."
                )
                continue

            # Show the user's prompt in a styled panel
            display.show_panel(stripped, "user")

            # Re-register signal handler before each agent turn.
            # prompt-toolkit's prompt_async() may override our SIGINT handler
            # during input; re-registering ensures Ctrl-C works during agent runs.
            setup_signal_handler(loop, signal_state)

            # Run agent turn with streaming display
            signal_state.agent_task = asyncio.create_task(
                run_agent_turn_streaming(agent, stripped, history, display)
            )

            try:
                response = await signal_state.agent_task
            except asyncio.CancelledError:
                # Clean up any active Live display left by cancellation
                display.cleanup()
                display.console.print("\n[dim][interrupted][/dim]")
                continue
            except Exception as e:
                display.console.print(f"\n[bold red][error][/bold red] {e}")
                continue
            finally:
                signal_state.agent_task = None

    # -- Shutdown --
    display.console.print("[dim]Goodbye.[/dim]")


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
