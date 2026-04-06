"""Slash command handlers and dispatch for the interactive REPL.

Provides runtime control via slash commands: /model, /approval, /yolo,
/new, /help. The dispatch function is called from the REPL loop before
the user panel and agent turn, so slash commands never reach the LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from codagent.config import Settings
    from codagent.conversation import ConversationHistory
    from codagent.display import Display


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _show_model_list(settings: Settings, agent: Agent, display: Display) -> None:
    """Display all available models with the active one indicated."""
    from codagent.models import MODEL_REGISTRY

    display.console.print()
    display.console.print("  [bold cyan]Available Models[/bold cyan]")
    display.console.print()
    for name in sorted(MODEL_REGISTRY.keys()):
        if name == settings.default_model:
            display.console.print(
                f"  [bold bright_green]> {name}[/bold bright_green]  [dim](active)[/dim]"
            )
        else:
            display.console.print(f"  [dim]  {name}[/dim]")
    display.console.print()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def handle_model(
    args: str, agent: Agent, settings: Settings, display: Display
) -> None:
    """Handle /model [name] -- switch model or list available models."""
    if not args:
        _show_model_list(settings, agent, display)
        return

    from codagent.models import get_model

    name = args.strip().lower()
    try:
        model_string = get_model(name)
    except ValueError:
        from codagent.models import list_models

        available = ", ".join(list_models())
        display.console.print(
            f"  [bold red]Unknown model '{name}'.[/bold red] "
            f"Available: {available}"
        )
        return

    agent.model = model_string
    settings.default_model = name
    display.console.print(
        f"  [bold green]Switched to {name} ({model_string})[/bold green]"
    )


def handle_approval(settings: Settings, display: Display) -> None:
    """Handle /approval -- switch to approval mode."""
    if settings.mode == "approval":
        display.console.print("  [dim]Already in approval mode.[/dim]")
        return

    settings.mode = "approval"
    display.console.print(
        "  [bold green]Mode: approval -- commands require confirmation "
        "before execution[/bold green]"
    )


def handle_yolo(settings: Settings, display: Display) -> None:
    """Handle /yolo -- switch to yolo mode."""
    if settings.mode == "yolo":
        display.console.print("  [dim]Already in yolo mode.[/dim]")
        return

    settings.mode = "yolo"
    display.console.print(
        "  [bold yellow]Mode: yolo -- commands will auto-execute "
        "(dangerous commands still require approval)[/bold yellow]"
    )


def handle_new(history: ConversationHistory, display: Display) -> None:
    """Handle /new -- clear conversation history."""
    history.clear()
    display.console.print("  [dim]Conversation cleared.[/dim]")


def handle_help(display: Display) -> None:
    """Handle /help -- show available commands and keyboard shortcuts."""
    from rich import box
    from rich.table import Table

    # Commands table
    cmd_table = Table(
        box=box.SIMPLE,
        header_style="bold cyan",
        padding=(0, 2),
    )
    cmd_table.add_column("Command", style="bold", no_wrap=True)
    cmd_table.add_column("Description")

    cmd_table.add_row("/model [name]", "Switch model or list available models")
    cmd_table.add_row("/approval", "Switch to approval mode (confirm before execute)")
    cmd_table.add_row("/yolo", "Switch to yolo mode (auto-execute commands)")
    cmd_table.add_row("/new", "Clear conversation history")
    cmd_table.add_row("/help", "Show this help")
    cmd_table.add_row("/exit", "Exit the agent")

    # Keyboard shortcuts table
    kb_table = Table(
        box=box.SIMPLE,
        header_style="bold cyan",
        padding=(0, 2),
    )
    kb_table.add_column("Shortcut", style="bold")
    kb_table.add_column("Action")

    kb_table.add_row("Enter", "Submit prompt")
    kb_table.add_row("Escape+Enter", "Insert newline")
    kb_table.add_row("Ctrl-C", "Cancel current / exit")
    kb_table.add_row("Up/Down", "Command history")
    kb_table.add_row("Tab", "Complete slash command")

    display.console.print()
    display.console.print(cmd_table)
    display.console.print(kb_table)
    display.console.print()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

# Map command names to their handler callables. Each handler has a different
# signature, so we dispatch manually rather than using a uniform interface.
_COMMANDS = {
    "/model",
    "/approval",
    "/yolo",
    "/new",
    "/help",
}


def dispatch_slash_command(
    text: str,
    agent: Agent,
    settings: Settings,
    history: ConversationHistory,
    display: Display,
) -> bool:
    """Dispatch a slash command if the text starts with '/'.

    Returns True if the text was a known slash command (handled),
    False if the text does not start with '/' or the command is unknown.
    """
    if not text.startswith("/"):
        return False

    parts = text.split(None, 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command == "/model":
        handle_model(args, agent, settings, display)
        return True
    elif command == "/approval":
        handle_approval(settings, display)
        return True
    elif command == "/yolo":
        handle_yolo(settings, display)
        return True
    elif command == "/new":
        handle_new(history, display)
        return True
    elif command == "/help":
        handle_help(display)
        return True

    return False
