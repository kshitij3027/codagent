# Phase 3: Slash Commands and Runtime Control - Research

**Researched:** 2026-04-05
**Domain:** Python CLI slash command dispatch, Pydantic AI runtime model switching, Rich table rendering, prompt-toolkit argument completion
**Confidence:** HIGH

## Summary

Phase 3 wires slash command handlers into the existing REPL loop. The infrastructure is already in place: `input.py` has a `SlashCommandCompleter` with tab completion, `models.py` has `MODEL_REGISTRY` with `get_model()` and `list_models()`, `conversation.py` has `ConversationHistory.clear()`, `config.py` has a mutable `settings.mode` field, and `display.py` owns all Rich console output via the `Display` class. This phase adds the command handlers themselves and dispatches them from `main.py` before user input reaches the agent.

The primary technical challenge is `/model` switching. Pydantic AI's `Agent` class has a settable `model` property and `agent.iter()` accepts a `model=` override parameter. Messages are provider-agnostic (verified from official docs: "The message format is independent of the model used, so you can use messages in different agents, or the same agent with different models"), so conversation history carries over across provider switches without serialization issues. This contradicts the earlier STATE.md decision ("Reset history on /model switch") but aligns with the user's CONTEXT.md locked decision to carry history over.

The remaining commands (`/approval`, `/yolo`, `/new`, `/help`) are straightforward state mutations and display operations. The completer needs updates: add `/yolo` as a separate command and extend the completer to handle `/model <name>` argument completion.

**Primary recommendation:** Add a `commands.py` module with a `dispatch_slash_command()` function that receives the parsed command plus current state (agent, settings, history, display) and returns a boolean indicating whether the input was handled. Call it from the REPL loop before sending input to the agent. Use `agent.model = new_model_string` for model switching (simpler than per-call override, persists across turns). Extend `SlashCommandCompleter.get_completions()` to yield model name completions when the input starts with `/model `.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- /model switching: Friendly name only -- user types `/model claude`, `/model gpt5`, `/model groq` (MODEL_REGISTRY keys)
- Full Pydantic AI model strings (e.g., `anthropic:claude-4.5-sonnet`) are NOT accepted as arguments
- Bare `/model` with no argument: show the current active model AND list all available models
- After successful switch: one-line confirmation showing friendly name + resolved string, e.g. `Switched to claude (anthropic:claude-4.5-sonnet)`
- Conversation history carries over on model switch -- user can switch mid-task without losing context
- Invalid model name: error message listing available models
- Two separate commands, NOT a toggle: `/approval` switches to approval mode, `/yolo` switches to yolo mode
- Feedback after switch: one-line with explanation, e.g. `Mode: yolo -- commands will auto-execute (dangerous commands still require approval)`
- No-op case (already in that mode): confirm current state, e.g. `Already in approval mode.`
- Add `/yolo` to the SlashCommandCompleter alongside existing `/approval` -- both appear in tab completion with their own descriptions
- /new resets conversation history ONLY -- model selection, mode (approval/yolo), and all config persist
- No confirmation prompt -- instant reset (conversation is ephemeral in-memory state, not destructive)
- Post-reset feedback: one-line `Conversation cleared.` then normal prompt appears
- Implementation: clear the ConversationHistory object, do NOT recreate the Pydantic AI agent instance
- /help shows slash commands AND keyboard shortcuts (two sections)
- Styled as a Rich table: Command | Description columns
- Does NOT show current state (model, mode) -- that's what bare `/model` is for
- Does NOT show version -- that's in the startup banner
- Pure reference card: static content, no dynamic state

### Claude's Discretion
- Exact Rich table styling and column widths for /help
- Error message wording for invalid /model arguments
- Whether slash command dispatch lives in main.py or a dedicated commands.py module

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MODL-03 | User can switch between models at runtime via `/model` slash command | Pydantic AI Agent has settable `model` property (`agent.model = "openai:gpt-5"`). Messages are provider-agnostic, so history carries over. `models.py` already has `get_model(name)` and `list_models()`. |
| MODE-03 | User can toggle between approval and yolo via `/approval` slash command | `settings.mode` is already mutable. Two separate commands per CONTEXT.md: `/approval` and `/yolo`. Shell tool already reads `get_settings().mode` on each call. |
| CORE-04 | User can reset conversation via `/new` command, clearing history but preserving config | `ConversationHistory.clear()` already exists. Agent instance, settings, and model selection persist -- only `history.clear()` is needed. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic-ai-slim | >=1.63.0 | Agent framework with settable `model` property and `model=` override on `iter()` | Already in use; model switching is a first-class feature |
| rich | >=14.3.3 | Rich Table for /help rendering, Console for feedback messages | Already in use; `Display` class owns all output |
| prompt-toolkit | >=3.0.52 | SlashCommandCompleter extension for /model argument completion | Already in use; completer is already wired in |

### Supporting
No new libraries needed. All Phase 3 functionality uses the existing stack.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `agent.model = X` (property setter) | `agent.iter(model=X)` (per-call override) | Per-call override requires threading model string through `run_agent_turn_streaming()`. Property setter is simpler -- set once, persists across all subsequent turns. Use property setter. |
| Dedicated `commands.py` module | Inline dispatch in `main.py` | Inline keeps it simple for 5 commands, but a module is cleaner for testing and separation. Recommend `commands.py`. |
| Extending `SlashCommandCompleter` for `/model` args | Separate `NestedCompleter` | NestedCompleter is more complex to set up. Extending the existing class with a space-detection branch is simpler and keeps one completer. |

**Installation:**
```bash
# No new packages needed -- all dependencies already installed
```

## Architecture Patterns

### Recommended Project Structure
```
src/codagent/
    commands.py          # NEW: slash command handlers + dispatch
    input.py             # MODIFY: update completer (add /yolo, add /model arg completion)
    main.py              # MODIFY: add dispatch before agent turn
    config.py            # UNCHANGED (mode is already mutable)
    models.py            # MINOR: remove print() debug statements, add formatted list helper
    conversation.py      # UNCHANGED (clear() already exists)
    agent.py             # UNCHANGED
    display.py           # UNCHANGED
```

### Pattern 1: Command Dispatch Table
**What:** A dictionary mapping command names to handler functions, with a single dispatch entry point.
**When to use:** When you have a fixed set of commands that need routing from parsed input.
**Example:**
```python
# Source: Standard Python CLI pattern
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from codagent.config import Settings
    from codagent.conversation import ConversationHistory
    from codagent.display import Display


def handle_model(
    args: str,
    agent: Agent,
    settings: Settings,
    display: Display,
) -> None:
    """Handle /model [name] command."""
    from codagent.models import get_model, list_models, MODEL_REGISTRY

    if not args:
        # Bare /model: show current + list all
        _show_model_list(settings, agent, display)
        return

    name = args.strip().lower()
    try:
        model_string = get_model(name)
    except ValueError:
        available = ", ".join(list_models())
        display.console.print(
            f"[bold red]Unknown model '{name}'.[/bold red] "
            f"Available: {available}"
        )
        return

    agent.model = model_string
    settings.default_model = name  # Track friendly name for display
    display.console.print(
        f"[bold green]Switched to {name}[/bold green] ({model_string})"
    )


def handle_approval(settings: Settings, display: Display) -> None:
    """Handle /approval command."""
    if settings.mode == "approval":
        display.console.print("[dim]Already in approval mode.[/dim]")
        return
    settings.mode = "approval"
    display.console.print(
        "[bold green]Mode: approval[/bold green] "
        "-- commands require confirmation before execution"
    )


def handle_yolo(settings: Settings, display: Display) -> None:
    """Handle /yolo command."""
    if settings.mode == "yolo":
        display.console.print("[dim]Already in yolo mode.[/dim]")
        return
    settings.mode = "yolo"
    display.console.print(
        "[bold yellow]Mode: yolo[/bold yellow] "
        "-- commands will auto-execute "
        "(dangerous commands still require approval)"
    )


def handle_new(history: ConversationHistory, display: Display) -> None:
    """Handle /new command."""
    history.clear()
    display.console.print("[dim]Conversation cleared.[/dim]")


def handle_help(display: Display) -> None:
    """Handle /help command."""
    from rich.table import Table
    from rich import box

    # Commands table
    cmd_table = Table(
        title="Commands",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        padding=(0, 2),
    )
    cmd_table.add_column("Command", style="bold")
    cmd_table.add_column("Description")
    cmd_table.add_row("/model [name]", "Switch model (bare: show current)")
    cmd_table.add_row("/approval", "Switch to approval mode")
    cmd_table.add_row("/yolo", "Switch to yolo mode")
    cmd_table.add_row("/new", "Clear conversation history")
    cmd_table.add_row("/help", "Show this help")
    cmd_table.add_row("/exit", "Exit the agent")

    # Keyboard shortcuts table
    kb_table = Table(
        title="Keyboard Shortcuts",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        padding=(0, 2),
    )
    kb_table.add_column("Shortcut", style="bold")
    kb_table.add_column("Action")
    kb_table.add_row("Enter", "Submit prompt")
    kb_table.add_row("Escape + Enter", "Insert newline")
    kb_table.add_row("Ctrl-C", "Cancel current / exit")
    kb_table.add_row("Up/Down", "Command history")
    kb_table.add_row("Tab", "Complete slash command")

    display.console.print()
    display.console.print(cmd_table)
    display.console.print(kb_table)
    display.console.print()


def dispatch_slash_command(
    text: str,
    agent: Agent,
    settings: Settings,
    history: ConversationHistory,
    display: Display,
) -> bool:
    """Dispatch a slash command. Returns True if handled, False otherwise."""
    if not text.startswith("/"):
        return False

    parts = text.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    handlers = {
        "/model": lambda: handle_model(args, agent, settings, display),
        "/approval": lambda: handle_approval(settings, display),
        "/yolo": lambda: handle_yolo(settings, display),
        "/new": lambda: handle_new(history, display),
        "/help": lambda: handle_help(display),
    }

    handler = handlers.get(command)
    if handler is None:
        return False

    handler()
    return True
```

### Pattern 2: Extended Slash Command Completer with Argument Support
**What:** Extend the existing `SlashCommandCompleter` to handle `/model <name>` argument completion by detecting a space after the command.
**When to use:** When a slash command accepts arguments that should also be tab-completable.
**Example:**
```python
# Source: prompt-toolkit Completer API + existing input.py pattern
from codagent.models import list_models

class SlashCommandCompleter(Completer):
    COMMANDS: Dict[str, str] = {
        "/help": "Show available commands",
        "/model": "Switch the active model",
        "/approval": "Switch to approval mode",
        "/yolo": "Switch to yolo mode (auto-execute)",
        "/new": "Clear conversation history",
        "/exit": "Exit the agent",
    }

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        stripped = text.lstrip()

        if not stripped.startswith("/"):
            return

        # Check if we're completing an argument (space after command)
        if " " in stripped:
            cmd_part, arg_part = stripped.split(maxsplit=1)
            if cmd_part.lower() == "/model":
                # Complete model names
                for name in list_models():
                    if name.startswith(arg_part.lower()):
                        yield Completion(
                            name,
                            start_position=-len(arg_part),
                            display_meta="model",
                        )
            return

        # Complete command names (existing logic)
        for cmd, desc in self.COMMANDS.items():
            if cmd.startswith(stripped):
                yield Completion(
                    cmd,
                    start_position=-len(stripped),
                    display_meta=desc,
                )
```

### Pattern 3: REPL Integration Point
**What:** Dispatch slash commands from the REPL loop BEFORE the input reaches the agent.
**When to use:** Always -- slash commands are local UI operations, not agent prompts.
**Example:**
```python
# In main.py REPL loop, after input validation but before agent turn
stripped = user_input.strip()

# Handle exit
if stripped.lower() in ("exit", "quit", "/exit"):
    break

# Handle slash commands
if stripped.startswith("/"):
    from codagent.commands import dispatch_slash_command
    if dispatch_slash_command(stripped, agent, settings, history, display):
        continue
    # If not handled, fall through (unknown command becomes agent prompt)

# Show user panel and run agent turn...
```

### Anti-Patterns to Avoid
- **Sending slash commands to the agent:** Slash commands are local state operations. Sending `/model claude` to the LLM wastes tokens and causes confusion. Always intercept before the agent turn.
- **Recreating the Agent on model switch:** The Agent class has a settable `model` property. Recreating the agent loses registered tools, system prompt, and other config. Use `agent.model = new_model_string` instead.
- **Using `agent.iter(model=X)` for persistent switch:** The `model=` parameter on `iter()` is a one-shot override. For a persistent `/model` switch, set `agent.model` directly so all subsequent turns use the new model without threading the model string through every call.
- **Toggling mode with a single /approval command:** The user decided two separate commands `/approval` and `/yolo`. A toggle requires the user to remember current state before issuing the command -- separate commands are explicit.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Model string resolution | Manual if/elif for model names | `models.get_model(name)` (already exists) | MODEL_REGISTRY is the single source of truth; `get_model()` handles OpenRouter dynamic resolution |
| Provider-agnostic history | Custom message serialization | Pydantic AI's built-in message format | Messages are already provider-agnostic by design |
| Rich table rendering | Manual string formatting for /help | `rich.table.Table` | Handles column width calculation, wrapping, and alignment automatically |
| Tab completion | Manual input parsing for argument completion | `prompt-toolkit Completer.get_completions()` | Handles cursor position, display_meta, dropdown rendering |

**Key insight:** Phase 3 is almost entirely wiring -- connecting existing infrastructure to new dispatch logic. The model registry, conversation history, mode field, display layer, and completer are all already built. The new code is thin: a dispatch function, 5 handler functions, and a completer extension.

## Common Pitfalls

### Pitfall 1: Debug print() Statements in models.py
**What goes wrong:** `models.py` has `print(f"[model] Resolved '{name}' -> {resolved}")` and `print(f"[model] Default model: {name}")` (lines 71, 93). These bare print() calls will conflict with the Rich console and prompt-toolkit's patch_stdout(). They will produce mangled ANSI output or interleave with the prompt.
**Why it happens:** Phase 1 used plain text output. Phase 2 moved all output to the Display class but did not clean up models.py debug prints.
**How to avoid:** Remove all `print()` calls from `models.py`. If logging is needed, route through `display.console.print()` or Python's `logging` module.
**Warning signs:** Garbled text appearing when switching models.

### Pitfall 2: Slash Command Reaching the Agent
**What goes wrong:** If slash command dispatch happens after the user panel is shown, the user sees their `/model claude` echoed in a styled panel AND the agent receives it as a prompt, wasting tokens.
**Why it happens:** Dispatch placed at the wrong point in the REPL loop.
**How to avoid:** Dispatch slash commands BEFORE `display.show_panel(stripped, "user")` and BEFORE the agent turn. Use `continue` to skip the agent entirely when a command is handled.
**Warning signs:** Agent responding to "I don't understand /model" or trying to run shell commands.

### Pitfall 3: Forgetting to Track Friendly Model Name
**What goes wrong:** After `/model claude`, the banner and bare `/model` output show the old model name because only `agent.model` was updated (with the Pydantic AI model string like `anthropic:claude-4.5-sonnet`) but `settings.default_model` (the friendly name) was not updated.
**Why it happens:** The model switch updates the agent but not the config state that tracks the friendly name.
**How to avoid:** Update both `agent.model = model_string` AND `settings.default_model = friendly_name` in the `/model` handler.
**Warning signs:** Bare `/model` showing wrong current model; UI status area showing stale model name.

### Pitfall 4: SlashCommandCompleter Blocking on /model Space
**What goes wrong:** The existing completer returns no completions when there is a space in the input (line 66: `if " " in stripped: return`). This means `/model cl<TAB>` will not complete to `/model claude`.
**Why it happens:** The original completer was designed for standalone commands only. The space check was a guard against mid-sentence triggering.
**How to avoid:** Modify the space check to specifically handle the `/model ` prefix case, yielding model name completions for the argument portion.
**Warning signs:** Tab completion stops working after typing `/model `.

### Pitfall 5: Inconsistent State After Model Switch Failure
**What goes wrong:** If `get_model(name)` succeeds but `agent.model = model_string` somehow fails (unlikely but possible with bad model strings), `settings.default_model` may already be updated to the new name.
**Why it happens:** Non-atomic state update across two objects.
**How to avoid:** Validate with `get_model()` first (which raises `ValueError` on unknown names), then update both `agent.model` and `settings.default_model` together. The validation-first pattern ensures no partial updates on invalid input.
**Warning signs:** Settings showing model X but agent using model Y.

## Code Examples

### Model List Display (bare /model)
```python
# Source: Rich Table API + models.py existing API
def _show_model_list(
    settings: Settings,
    agent: Agent,
    display: Display,
) -> None:
    """Display current model and available models."""
    from codagent.models import MODEL_REGISTRY, get_model

    current = settings.default_model

    for name in sorted(MODEL_REGISTRY.keys()):
        if name == current:
            display.console.print(
                f"  [bold bright_green]> {name}[/bold bright_green] [dim](active)[/dim]"
            )
        else:
            display.console.print(f"  [dim]  {name}[/dim]")
```

### /help Table with Rich
```python
# Source: Rich Table docs (https://rich.readthedocs.io/en/stable/tables.html)
from rich.table import Table
from rich import box

table = Table(
    title="Commands",
    box=box.SIMPLE,
    show_header=True,
    header_style="bold cyan",
    padding=(0, 2),
)
table.add_column("Command", style="bold", no_wrap=True)
table.add_column("Description")
table.add_row("/model [name]", "Switch model (bare: show current + list)")
table.add_row("/approval", "Switch to approval mode")
# ... etc
```

### Dispatch Integration in REPL
```python
# Source: Existing main.py pattern
# In the while True loop, after get_user_input() and exit check:

if stripped.startswith("/"):
    from codagent.commands import dispatch_slash_command
    handled = dispatch_slash_command(
        stripped, agent, settings, history, display
    )
    if handled:
        continue
    # Unknown slash command: show error, do NOT send to agent
    display.console.print(
        f"[bold red]Unknown command:[/bold red] {stripped.split()[0]}. "
        "Type /help for available commands."
    )
    continue
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Reset history on /model switch | Carry over history (Pydantic AI messages are provider-agnostic) | CONTEXT.md decision (2026-04-05) | Users can switch models mid-task without losing context |
| Single `/approval` toggle command | Separate `/approval` and `/yolo` commands | CONTEXT.md decision (2026-04-05) | Explicit intent, no need to remember current state |
| `agent.run()` batch mode | `agent.iter()` streaming mode | Phase 2 | Model override via `model=` parameter available on `iter()` too |

**Deprecated/outdated:**
- STATE.md decision "Reset history on /model switch" is superseded by CONTEXT.md "Conversation history carries over on model switch." Pydantic AI docs confirm messages are provider-agnostic, validating this approach.
- The `/approval` completer description says "Toggle approval/yolo mode" -- this needs updating to reflect the two-command approach.

## Open Questions

1. **Unknown slash commands: error or pass to agent?**
   - What we know: The CONTEXT.md does not specify behavior for unrecognized `/something` input
   - What's unclear: Should unknown `/foo` show an error, or be sent to the agent as a normal prompt?
   - Recommendation: Show an error with "Unknown command. Type /help for available commands." and do NOT send to the agent. Slash-prefixed input should never reach the LLM. This prevents wasting tokens and confusing the model.

2. **`models.py` debug print() removal**
   - What we know: Lines 71 and 93 have bare `print()` calls that will corrupt Rich output
   - What's unclear: Whether any downstream code relies on these debug prints
   - Recommendation: Remove them. They were Phase 1 debug aids. No code parses their output.

## Sources

### Primary (HIGH confidence)
- [Pydantic AI API Reference - Agent class](https://ai.pydantic.dev/api/agent/) - Confirmed `model` property has getter and setter; `iter()` accepts `model=` override parameter
- [Pydantic AI Message History docs](https://ai.pydantic.dev/message-history/) - Confirmed messages are provider-agnostic: "The message format is independent of the model used, so you can use messages in different agents, or the same agent with different models"
- [Rich Tables documentation](https://rich.readthedocs.io/en/stable/tables.html) - Table constructor, add_column, add_row API
- [Rich box styles](https://rich.readthedocs.io/en/stable/appendix/box.html) - box.SIMPLE, box.ROUNDED, etc.

### Secondary (MEDIUM confidence)
- [prompt-toolkit Completer API](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html) - `get_completions(document, complete_event)`, `document.text_before_cursor`, `Completion(text, start_position, display_meta)`
- [prompt-toolkit GitHub examples](https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/examples/prompts/auto-completion/fuzzy-custom-completer.py) - Custom completer pattern with `get_word_before_cursor()`

### Tertiary (LOW confidence)
None -- all findings verified with primary or secondary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies; all features verified against existing codebase and official docs
- Architecture: HIGH - Pattern is straightforward dispatch; Pydantic AI model setter and provider-agnostic messages confirmed from official docs
- Pitfalls: HIGH - All identified from direct code inspection of existing codebase (debug prints, completer space guard, state tracking)

**Research date:** 2026-04-05
**Valid until:** 2026-05-05 (stable -- no fast-moving dependencies; all libraries already pinned)
