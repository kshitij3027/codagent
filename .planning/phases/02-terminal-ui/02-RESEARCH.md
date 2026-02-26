# Phase 2: Terminal UI - Research

**Researched:** 2026-02-26
**Domain:** Terminal UI — Rich rendering, prompt-toolkit input, streaming output, Pydantic AI iter() integration
**Confidence:** HIGH

## Summary

Phase 2 transforms the plain `print()` / `input()` REPL from Phase 1 into a polished terminal interface using **Rich** (output rendering, panels, spinners, markdown) and **prompt-toolkit** (async input, history, tab completion). The central architectural change is switching from `agent.run()` to `agent.iter()` with per-node streaming — this enables the thinking spinner during inference, token-by-token model response rendering, and real-time tool output display.

Both Rich and prompt-toolkit are mature, stable libraries already pinned in STATE.md. The primary integration risk is combining Rich's `Live` display with prompt-toolkit's `patch_stdout()` in the same asyncio event loop — STATE.md flags this as needing early validation. The pattern is well-established in the community but not formally documented in either library's official docs, so it must be tested as a first task.

**Primary recommendation:** Build a thin `display` module that owns the Rich `Console` singleton and exposes `show_spinner()`, `show_panel()`, `stream_text()`, and `stream_lines()` methods. Replace `agent.run()` with `agent.iter()` to get node-level visibility. Replace `input()` with prompt-toolkit `PromptSession.prompt_async()`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Vibrant, high-contrast color scheme — each panel type should visually pop and be immediately distinguishable
- Full box borders with labeled titles per panel type (e.g., "🧠 Thinking", "🛠️ Tool Call")
- 4 distinct panel types: User prompt, Model response, Tool call (command), Tool output
- Token-by-token streaming for model responses — each token rendered as the API yields it
- Live stdout/stderr streaming for tool execution — output appears line by line inside the tool output panel as the command runs
- Direct replace from spinner to response — spinner disappears, response text starts immediately, no transition effect
- Spinner visible during model inference, disappears when first token arrives
- Simple symbol prompt (e.g., "❯" or "→") — minimal, one character
- Multi-line input with Shift+Enter for new lines, Enter to submit
- Dropdown menu for slash command tab completion — shows matching commands with descriptions (like fish shell)
- Command history persists across sessions — saved to disk (e.g., ~/.coding-agent/history)
- Comfortable spacing — moderate padding inside panels, balanced spacing between them
- Full terminal width — panels stretch to fill available width
- Show all tool output as-is — Phase 1 truncation at ~10K chars handles length upstream
- Render markdown in model response panels — use Rich's markdown rendering with syntax-highlighted code blocks
- Panel labels should include emoji icons (e.g., "🧠 Thinking", "🛠️ Tool Call") for quick visual scanning
- Tab completion should feel like fish shell — dropdown with descriptions, not bare completions
- Streaming should feel alive — token-by-token like ChatGPT or Claude.ai

### Claude's Discretion
- Specific color palette assignments for each panel type
- Spinner animation style and label
- Exact padding/margin values within "comfortable" range
- Prompt symbol choice
- Markdown rendering configuration details

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DISP-01 | Rich-based streaming output with thinking spinner during model inference | Rich `Console.status()` spinner + `Live` display for streaming text; `agent.iter()` node-level iteration detects inference vs output states |
| DISP-02 | Each interaction displayed in a styled box with color coding | Rich `Panel` with `border_style`, `title`, `box` parameters; 4 panel types with distinct colors |
| DISP-03 | Tool call inputs and outputs displayed in panels as they happen in real-time | `agent.iter()` yields `CallToolsNode` with `FunctionToolCallEvent`/`FunctionToolResultEvent`; modified shell tool streams subprocess stdout line-by-line via `proc.stdout.readline()` |
| DISP-04 | Prompt Toolkit input with command history and slash command completion | `PromptSession` with `FileHistory`, `FuzzyWordCompleter` or custom `Completer`, `prompt_async()`, custom key bindings for Enter/Shift+Enter |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `rich` | 14.x (latest 14.2.0 as of Jan 2026) | Console output: panels, spinners, markdown, Live display, syntax highlighting | De-facto standard for Python terminal UIs; 50K+ GitHub stars; used by pip, pytest, textual |
| `prompt-toolkit` | 3.0.52 | Async input: PromptSession, FileHistory, completion, key bindings | The Python readline replacement; powers IPython, pgcli, AWS CLI v2; native asyncio in v3 |
| `pydantic-ai-slim` | >=1.63.0 | Agent iteration via `agent.iter()` for node-level streaming | Already in project; `iter()` replaces `run()` to expose intermediate states |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `rich.markdown` | (bundled with rich) | Render markdown in model response panels | When displaying model text output |
| `rich.panel` | (bundled with rich) | Bordered, titled, styled content boxes | Every interaction element |
| `rich.live` | (bundled with rich) | Auto-refreshing display for streaming text | Token-by-token model response rendering |
| `rich.spinner` | (bundled with rich) | Animated thinking indicator | During model inference before first token |
| `rich.box` | (bundled with rich) | Border style constants (ROUNDED, HEAVY, DOUBLE) | Panel border customization |
| `prompt_toolkit.history` | (bundled with prompt-toolkit) | `FileHistory` for persistent command history | Cross-session history storage |
| `prompt_toolkit.completion` | (bundled with prompt-toolkit) | `WordCompleter`, `FuzzyWordCompleter`, custom `Completer` | Slash command tab completion |
| `prompt_toolkit.patch_stdout` | (bundled with prompt-toolkit) | Prevent Rich output from corrupting prompt line | Always active during REPL loop |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Rich Live for streaming | Direct `console.print()` per token | Live provides smooth updates; direct print causes flicker and scrolling |
| Rich Markdown | `mdformat` + manual rendering | Rich's built-in markdown handles syntax highlighting out of the box |
| prompt-toolkit | `readline` stdlib | No async support, no dropdown completions, no fish-style menus |
| Custom Completer | `NestedCompleter` | NestedCompleter for hierarchical commands; custom Completer for description-rich dropdown |

**Installation:**
```bash
uv add rich prompt-toolkit
```

This adds to `pyproject.toml` dependencies alongside the existing `pydantic-ai-slim` and `python-dotenv`.

## Architecture Patterns

### Recommended Project Structure
```
src/codagent/
├── config.py            # (existing) Settings — add history_path
├── models.py            # (existing) Model registry
├── agent.py             # (MODIFY) Switch from agent.run() to agent.iter()
├── conversation.py      # (existing) History management
├── signals.py           # (MODIFY) Update for prompt-toolkit signal handling
├── main.py              # (MODIFY) Replace input() with PromptSession, orchestrate display
├── display.py           # (NEW) Rich rendering: panels, spinner, streaming, markdown
├── input.py             # (NEW) prompt-toolkit: PromptSession, completions, key bindings
└── tools/
    └── shell.py         # (MODIFY) Add streaming stdout/stderr + Rich approval panels
```

### Pattern 1: Agent Iteration with Node-Level Display
**What:** Replace `agent.run()` with `agent.iter()` to get visibility into each step of the agent's execution graph.
**When to use:** Always — this is the core change that enables all Phase 2 display features.
**Example:**
```python
# Source: https://ai.pydantic.dev/agent/ + https://datastud.dev/posts/pydantic-ai-streaming/
from pydantic_ai import Agent
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    TextPartDelta,
)

async def run_agent_turn_streaming(agent, prompt, history, display):
    """Run one agent turn with node-level display control."""
    async with agent.iter(prompt, message_history=history.get()) as agent_run:
        async for node in agent_run:
            if Agent.is_model_request_node(node):
                # Show spinner, then stream tokens as they arrive
                display.show_spinner("Thinking...")
                async with node.stream(agent_run.ctx) as request_stream:
                    async for event in request_stream:
                        if isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                            display.hide_spinner()
                            display.stream_token(event.delta.content_delta)
                display.finish_response_panel()

            elif Agent.is_call_tools_node(node):
                async with node.stream(agent_run.ctx) as tool_stream:
                    async for event in tool_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            display.show_tool_call_panel(event.part.tool_name, event.part.args)
                        elif isinstance(event, FunctionToolResultEvent):
                            display.show_tool_output_panel(event.result.content)

            elif Agent.is_end_node(node):
                pass  # Final result already streamed

    history.update(agent_run.result.all_messages())
```

### Pattern 2: Rich Panel Factory
**What:** A centralized display module that creates consistently styled panels for each interaction type.
**When to use:** Every time content is displayed to the user.
**Example:**
```python
# Source: https://rich.readthedocs.io/en/stable/panel.html
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

console = Console()

# Panel type configurations
PANEL_STYLES = {
    "user":        {"border_style": "bright_cyan",    "title": "❯ You",           "box": box.ROUNDED},
    "response":    {"border_style": "bright_green",   "title": "🧠 Assistant",    "box": box.ROUNDED},
    "tool_call":   {"border_style": "bright_yellow",  "title": "🛠️ Tool Call",    "box": box.HEAVY},
    "tool_output": {"border_style": "bright_magenta", "title": "📋 Output",       "box": box.ROUNDED},
}

def render_panel(content: str, panel_type: str) -> Panel:
    """Create a styled panel for the given interaction type."""
    style = PANEL_STYLES[panel_type]
    renderable = Markdown(content) if panel_type == "response" else content
    return Panel(
        renderable,
        title=style["title"],
        title_align="left",
        border_style=style["border_style"],
        box=style["box"],
        expand=True,
        padding=(1, 2),
    )
```

### Pattern 3: Streaming Text with Rich Live
**What:** Use `Live` display to render model tokens incrementally, building up the response panel in real-time.
**When to use:** During model response streaming (DISP-01, DISP-03).
**Example:**
```python
# Source: https://rich.readthedocs.io/en/stable/live.html
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

class StreamingDisplay:
    """Manages the Rich Live display for token-by-token streaming."""

    def __init__(self, console):
        self.console = console
        self._buffer = ""
        self._live = None

    def start_response_stream(self):
        """Begin a new streaming response panel."""
        self._buffer = ""
        self._live = Live(
            self._build_panel(),
            console=self.console,
            refresh_per_second=15,  # Smooth token-by-token feel
            transient=False,        # Keep final output visible
            vertical_overflow="visible",
        )
        self._live.start()

    def append_token(self, token: str):
        """Add a token to the streaming buffer and update display."""
        self._buffer += token
        if self._live:
            self._live.update(self._build_panel())

    def finish_stream(self):
        """Stop the Live display, leaving final panel in place."""
        if self._live:
            self._live.stop()
            self._live = None

    def _build_panel(self):
        """Build a response panel from the current buffer."""
        from rich.markdown import Markdown
        return Panel(
            Markdown(self._buffer) if self._buffer else Text("..."),
            title="🧠 Assistant",
            title_align="left",
            border_style="bright_green",
            box=box.ROUNDED,
            expand=True,
            padding=(1, 2),
        )
```

### Pattern 4: prompt-toolkit Async Input with Custom Completions
**What:** Replace `input()` with `PromptSession.prompt_async()` for non-blocking input with history and completions.
**When to use:** Main REPL loop input.
**Example:**
```python
# Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.key_binding import KeyBindings
import os

# Custom completer with descriptions (fish-shell style)
class SlashCommandCompleter(Completer):
    """Completes slash commands with descriptions in dropdown."""
    COMMANDS = {
        "/help": "Show available commands",
        "/model": "Switch the active model",
        "/approval": "Toggle approval/yolo mode",
        "/new": "Clear conversation history",
        "/exit": "Exit the agent",
    }

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            for cmd, desc in self.COMMANDS.items():
                if cmd.startswith(text):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display_meta=desc,
                    )

# Key bindings: Enter submits, Escape+Enter inserts newline
bindings = KeyBindings()

@bindings.add("escape", "enter")
def _newline(event):
    """Insert a newline on Escape+Enter (or Alt+Enter)."""
    event.current_buffer.insert_text("\n")

# PromptSession with all features
history_path = os.path.expanduser("~/.coding-agent/history")
os.makedirs(os.path.dirname(history_path), exist_ok=True)

session = PromptSession(
    message="❯ ",
    history=FileHistory(history_path),
    completer=SlashCommandCompleter(),
    auto_suggest=AutoSuggestFromHistory(),
    key_bindings=bindings,
    multiline=False,  # Enter submits by default
    enable_history_search=True,
)

# In the REPL loop:
async def get_input():
    with patch_stdout():
        return await session.prompt_async()
```

### Pattern 5: Real-Time Tool Output Streaming
**What:** Modify the shell tool to stream subprocess stdout/stderr line-by-line instead of collecting it all via `communicate()`.
**When to use:** DISP-03 — tool output appears as it executes, not after completion.
**Example:**
```python
# Source: https://docs.python.org/3/library/asyncio-subprocess.html
import asyncio

async def execute_command_streaming(command: str, on_line, timeout: int = 120) -> str:
    """Execute a shell command, calling on_line(text) for each output line."""
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    collected = []
    total_chars = 0
    TRUNCATION_LIMIT = 10_000

    async def read_stream(stream, prefix=""):
        nonlocal total_chars
        async for line_bytes in stream:
            line = line_bytes.decode("utf-8", errors="replace")
            total_chars += len(line)
            if total_chars <= TRUNCATION_LIMIT:
                collected.append(prefix + line)
                await on_line(prefix + line)

    try:
        await asyncio.wait_for(
            asyncio.gather(
                read_stream(proc.stdout),
                read_stream(proc.stderr, "[stderr] "),
            ),
            timeout=timeout,
        )
        await proc.wait()
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return f"[TIMEOUT] Command timed out after {timeout}s and was killed."

    output = "".join(collected)
    if total_chars > TRUNCATION_LIMIT:
        output += f"\n... [output truncated at {TRUNCATION_LIMIT} chars, {total_chars} total]"

    return f"Exit code: {proc.returncode}\n{output}"
```

### Pattern 6: Rich + prompt-toolkit Coexistence
**What:** Use `patch_stdout()` to prevent Rich console output from corrupting the prompt-toolkit input line.
**When to use:** Always — the REPL loop must wrap all Rich output in `patch_stdout()`.
**Example:**
```python
# Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html
from prompt_toolkit.patch_stdout import patch_stdout

async def async_main():
    session = create_prompt_session()
    console = Console()

    with patch_stdout():
        while True:
            user_input = await session.prompt_async()
            # All Rich console.print() calls within agent turn are safe
            # because patch_stdout redirects them above the prompt
            await run_agent_turn(...)
```

### Anti-Patterns to Avoid
- **Mixing print() and console.print():** Use `console.print()` exclusively once Rich is integrated. Bare `print()` bypasses Rich formatting and can corrupt Live displays.
- **Blocking the event loop with Rich Live:** Never use `time.sleep()` inside a Live context. Use `asyncio.sleep()` or event-driven updates.
- **Creating multiple Console instances:** Use a single `Console()` singleton. Multiple consoles fight over terminal state.
- **Using `agent.run()` for Phase 2:** Must switch to `agent.iter()` — `run()` returns only the final result with no intermediate visibility.
- **Using `input()` with prompt-toolkit:** The stdlib `input()` blocks the event loop and has no history/completion support. Always use `prompt_async()`.
- **Using `multiline=True` naively:** With `multiline=True`, Enter inserts newlines and Meta+Enter submits. The user wants the OPPOSITE (Enter submits, Shift+Enter or Escape+Enter for newlines). Use `multiline=False` with a custom key binding for Escape+Enter to insert newlines.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Terminal color/style management | ANSI escape code wrangling | Rich Console + markup | 256-color and truecolor support, terminal detection, Windows support |
| Animated spinner | Custom thread + cursor manipulation | Rich `Console.status()` or `Spinner` widget | Handles terminal refresh, cursor save/restore, cleanup on interrupt |
| Markdown-to-terminal rendering | Manual parsing + formatting | Rich `Markdown` class | Handles headers, lists, code blocks with syntax highlighting, links |
| Syntax highlighting in code blocks | Regex-based token coloring | Rich's built-in Pygments integration | Hundreds of languages, theme support, zero configuration |
| Input history persistence | File I/O + deduplication | prompt-toolkit `FileHistory` | Thread-safe, handles corruption, cross-session deduplication |
| Tab completion dropdown | Custom popup rendering | prompt-toolkit Completer + completion display | Handles scrolling, fuzzy matching, multi-column layout, keyboard nav |
| Line editing (cursor movement, deletion) | Terminal escape sequences | prompt-toolkit's built-in editing | Emacs/vi bindings, undo, clipboard, word movement — all built in |
| Live display refresh without flicker | Manual cursor positioning + clear | Rich `Live` with `update()` | Handles diff-based refresh, terminal size changes, nested renderables |

**Key insight:** Both Rich and prompt-toolkit have spent years solving terminal rendering edge cases (Windows terminals, SSH sessions, narrow terminals, Unicode width calculation, color fallback). Hand-rolling any of these is a multi-month project that would still miss edge cases.

## Common Pitfalls

### Pitfall 1: Rich Live + prompt-toolkit Interaction
**What goes wrong:** Rich's `Live` display and prompt-toolkit's `PromptSession` both manage terminal cursor position. If not coordinated, they corrupt each other's output — the spinner overwrites the prompt, or typed characters appear inside a panel.
**Why it happens:** Both libraries assume they own stdout. Without `patch_stdout()`, writes from Rich go directly to the terminal while prompt-toolkit is managing the input line.
**How to avoid:** Always wrap the REPL loop in `patch_stdout()`. Use `console.print()` (not `print()`). Stop any active `Live` display before calling `prompt_async()`. Test this combination as the very first task of Phase 2.
**Warning signs:** Garbled text, cursor jumping, disappearing input, panels rendering on top of the prompt.

### Pitfall 2: Spinner-to-Response Transition Flicker
**What goes wrong:** When switching from the thinking spinner to the streaming response, there's a visible flash or blank frame where neither is showing.
**Why it happens:** Stopping one `Live` context and starting another leaves a gap. Or using `transient=True` on the spinner clears it before the response panel is ready.
**How to avoid:** Use a single `Live` context that starts with the spinner renderable and `update()`s to the response panel when the first token arrives. Don't stop/restart Live — just swap the renderable.
**Warning signs:** Blank lines appearing between spinner and response, visible cursor flash.

### Pitfall 3: Blocking the Event Loop During Streaming
**What goes wrong:** Using synchronous Rich APIs (`console.print()` in a tight loop, `Live` with `auto_refresh=True` at high frequency) blocks the asyncio event loop, making Ctrl-C unresponsive and stalling concurrent I/O.
**Why it happens:** Rich's rendering is synchronous. If the refresh rate is too high or the renderable is expensive to layout, each `update()` call takes measurable time.
**How to avoid:** Set `refresh_per_second` to 10-15 (not higher). Use `auto_refresh=True` to let Rich batch updates. Keep renderables simple (Text, not full Markdown) during streaming — render final Markdown only when streaming completes.
**Warning signs:** Ctrl-C takes >1s to respond during streaming, visible lag between tokens, CPU usage spikes.

### Pitfall 4: Shift+Enter Key Binding Limitations
**What goes wrong:** The user expects Shift+Enter to insert a newline (like Slack, ChatGPT), but most terminals don't send a distinct escape sequence for Shift+Enter — it's indistinguishable from Enter.
**Why it happens:** Terminal protocols (VT100) predate Shift key modifiers for Enter. Some modern terminals (kitty, iTerm2) send distinct codes, but many don't.
**How to avoid:** Use `multiline=False` (Enter submits) with Escape+Enter or Alt+Enter for newlines. Document this in the startup banner. The prompt-toolkit community consensus (GitHub issue #529, #728) is that Escape+Enter is the portable alternative.
**Warning signs:** Users report Shift+Enter submitting instead of adding a newline on some terminals.

### Pitfall 5: FileHistory Path Doesn't Exist
**What goes wrong:** `FileHistory("~/.coding-agent/history")` fails because the directory doesn't exist or `~` isn't expanded.
**Why it happens:** `FileHistory` doesn't create parent directories automatically. The tilde (`~`) must be expanded with `os.path.expanduser()`.
**How to avoid:** Call `os.makedirs(os.path.dirname(path), exist_ok=True)` and `os.path.expanduser()` before creating the `FileHistory`.
**Warning signs:** `FileNotFoundError` on first run, or history not persisting across sessions.

### Pitfall 6: Markdown Rendering During Streaming Is Expensive
**What goes wrong:** Re-rendering the full buffer as Markdown on every token update causes noticeable lag, especially with large code blocks.
**Why it happens:** Markdown parsing + Pygments syntax highlighting is CPU-intensive. At 15 updates/second with a growing buffer, this compounds.
**How to avoid:** During streaming, display the buffer as plain `Text` (with basic formatting). Only render as full `Markdown` in the final panel after streaming completes. This matches how ChatGPT/Claude.ai handle it — streaming text looks plain, then renders rich formatting at the end.
**Warning signs:** Growing lag during long responses, frame drops in the Live display, CPU usage climbing linearly.

### Pitfall 7: Subprocess Streaming Deadlock
**What goes wrong:** Reading stdout and stderr separately via `readline()` can deadlock if one pipe fills its buffer while you're reading the other.
**Why it happens:** OS pipe buffers are finite (~64KB on Linux). If stderr fills while you're blocked reading stdout, the subprocess blocks on write and you block on read — deadlock.
**How to avoid:** Read both streams concurrently using `asyncio.gather()` with two `read_stream()` coroutines. Never read one synchronously while the other might be writing.
**Warning signs:** Tool execution hangs indefinitely on commands with mixed stdout/stderr output.

### Pitfall 8: os._exit(0) Is No Longer Needed
**What goes wrong:** The Phase 1 signal handler uses `os._exit(0)` to avoid the `run_in_executor` thread deadlock. If this isn't removed when switching to prompt-toolkit, it bypasses prompt-toolkit's cleanup (which can corrupt the terminal state).
**Why it happens:** prompt-toolkit manages terminal state (alternate screen, raw mode, mouse capture) and needs its shutdown hooks to run.
**How to avoid:** Replace `os._exit(0)` with a clean `SystemExit` or set a shutdown flag that the REPL loop checks. prompt-toolkit's `prompt_async()` is properly cancellable — Ctrl-C raises `KeyboardInterrupt` cleanly.
**Warning signs:** Terminal left in raw mode after exit, no cursor visible, broken terminal requiring `reset`.

## Code Examples

Verified patterns from official sources:

### Rich Console Status (Spinner)
```python
# Source: https://rich.readthedocs.io/en/stable/console.html
from rich.console import Console

console = Console()

# Spinner with customizable animation
with console.status("[bold cyan]🧠 Thinking...", spinner="dots") as status:
    # ... do work ...
    status.update("[bold cyan]🧠 Still thinking...")
# Spinner automatically cleaned up on exit
```

### Rich Panel with Title and Color
```python
# Source: https://rich.readthedocs.io/en/stable/panel.html
from rich.panel import Panel
from rich import box

panel = Panel(
    "Hello, world!",
    title="🧠 Assistant",
    title_align="left",
    border_style="bright_green",
    box=box.ROUNDED,
    expand=True,
    padding=(1, 2),
)
console.print(panel)
```

### Rich Markdown with Syntax Highlighting
```python
# Source: https://rich.readthedocs.io/en/latest/markdown.html
from rich.markdown import Markdown

md = Markdown("""
## Example
Here's some code:
```python
def hello():
    print("world")
```
""", code_theme="monokai")
console.print(md)
```

### Rich Live Display for Streaming
```python
# Source: https://rich.readthedocs.io/en/stable/live.html
from rich.live import Live
from rich.text import Text

buffer = Text()
with Live(buffer, console=console, refresh_per_second=12) as live:
    for token in stream:
        buffer.append(token)
        live.update(buffer)
```

### prompt-toolkit Async Prompt with History
```python
# Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout

session = PromptSession(history=FileHistory("/path/to/history"))

async def repl():
    with patch_stdout():
        while True:
            text = await session.prompt_async("❯ ")
```

### prompt-toolkit Custom Completer with Descriptions
```python
# Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html
from prompt_toolkit.completion import Completer, Completion

class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            yield Completion("/help", start_position=-len(text),
                           display_meta="Show available commands")
```

### Pydantic AI agent.iter() with Streaming
```python
# Source: https://ai.pydantic.dev/agent/ + https://datastud.dev/posts/pydantic-ai-streaming/
from pydantic_ai.messages import PartDeltaEvent, TextPartDelta

async with agent.iter(prompt, message_history=history) as run:
    async for node in run:
        if Agent.is_model_request_node(node):
            async with node.stream(run.ctx) as stream:
                async for event in stream:
                    if isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                        display.append_token(event.delta.content_delta)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `agent.run()` (batch response) | `agent.iter()` (node-level streaming) | Pydantic AI 1.x (2025) | Enables token-by-token streaming and tool call visibility |
| `input()` + `readline` | `prompt_toolkit.PromptSession.prompt_async()` | prompt-toolkit 3.0 (2019+) | Native asyncio, dropdown completions, persistent history |
| `print()` + ANSI escapes | `rich.console.Console.print()` | Rich 10+ (2020+) | Consistent cross-platform styling, markdown, panels |
| Manual terminal refresh | `rich.live.Live` | Rich 10+ (2020+) | Flicker-free updates, auto-refresh, overflow handling |
| `subprocess.run()` | `asyncio.create_subprocess_shell()` + stream readline | Python 3.4+ (asyncio), improved 3.10+ | Non-blocking, line-by-line streaming, event loop compatible |

**Deprecated/outdated:**
- `agent.run()` is still functional but insufficient for Phase 2; must use `agent.iter()` for intermediate visibility
- `input()` via `run_in_executor` — Phase 1 workaround; prompt-toolkit replaces entirely
- `os._exit(0)` for signal handling — Phase 1 workaround for `run_in_executor` thread deadlock; prompt-toolkit eliminates the root cause

## Open Questions

1. **Rich Live + patch_stdout() interaction under load**
   - What we know: Both libraries work individually with asyncio. Community reports success combining them.
   - What's unclear: Behavior under rapid token streaming (15+ updates/sec) while prompt-toolkit's patch_stdout is active. Official docs don't cover this combination.
   - Recommendation: Build a minimal integration test as Wave 0 task — spinner + streaming text + prompt, all in one event loop. If flicker or corruption occurs, fall back to using `console.print()` with `end=""` instead of `Live`.

2. **Shift+Enter portability across terminals**
   - What we know: Modern terminals (kitty, iTerm2, Windows Terminal) may send distinct escape sequences for Shift+Enter. Many terminals (classic xterm, basic SSH) don't.
   - What's unclear: Exact percentage of user terminals that support it.
   - Recommendation: Use Escape+Enter (Alt+Enter) as the newline shortcut — universally supported. Document this in the welcome banner. If Shift+Enter works, it's a bonus.

3. **Pydantic AI event types completeness**
   - What we know: `PartDeltaEvent`, `TextPartDelta`, `FunctionToolCallEvent`, `FunctionToolResultEvent` exist. Import from `pydantic_ai.messages`.
   - What's unclear: Whether all providers (OpenAI, Anthropic, OpenRouter) emit these events identically. Some providers may batch tokens differently.
   - Recommendation: Test streaming with each configured provider early. Handle the case where `content_delta` is empty or missing gracefully.

4. **Approval prompt styling inside panels**
   - What we know: Phase 1 approval prompt uses `input("Approve? [Y/n] ")`. This must be replaced with a styled Rich prompt or prompt-toolkit sub-prompt.
   - What's unclear: Whether prompt-toolkit supports inline sub-prompts within a Rich panel context, or if approval must be a separate prompt.
   - Recommendation: Use `console.input()` (Rich's styled input) for the approval gate, or briefly stop the Live display, use a simple styled prompt, then resume.

## Sources

### Primary (HIGH confidence)
- Rich official docs (v14.1.0): [Live Display](https://rich.readthedocs.io/en/stable/live.html), [Console API](https://rich.readthedocs.io/en/stable/console.html), [Panel](https://rich.readthedocs.io/en/stable/panel.html), [Markdown](https://rich.readthedocs.io/en/latest/markdown.html), [Box Styles](https://rich.readthedocs.io/en/stable/appendix/box.html)
- prompt-toolkit official docs (v3.0.52): [Asking for Input](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html), [Key Bindings](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/advanced_topics/key_bindings.html)
- Pydantic AI official docs: [Agents (iter)](https://ai.pydantic.dev/agent/), [Agent API](https://ai.pydantic.dev/api/agent/)
- Python stdlib: [asyncio subprocess](https://docs.python.org/3/library/asyncio-subprocess.html)

### Secondary (MEDIUM confidence)
- Barrett Studdard's streaming tutorial: [Streaming with Pydantic AI](https://datastud.dev/posts/pydantic-ai-streaming/) — verified against official API, provides working `agent.iter()` + `node.stream()` pattern
- DeepWiki Pydantic AI: [Streaming and Real-time Processing](https://deepwiki.com/pydantic/pydantic-ai/4.1-streaming-and-real-time-processing) — event type taxonomy confirmed
- Rich PyPI: [v14.2.0](https://pypi.org/project/rich/) — version currency verified (Jan 2026)
- prompt-toolkit PyPI: [v3.0.52](https://pypi.org/project/prompt-toolkit/) — version currency verified (Aug 2025)

### Tertiary (LOW confidence)
- prompt-toolkit Shift+Enter GitHub issues: [#529](https://github.com/prompt-toolkit/python-prompt-toolkit/issues/529), [#728](https://github.com/prompt-toolkit/python-prompt-toolkit/issues/728) — community consensus on Escape+Enter, but no official recommendation
- Rich + asyncio GitHub discussion: [#1401](https://github.com/Textualize/rich/discussions/1401) — community patterns, not officially documented

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Both Rich and prompt-toolkit are mature, stable, well-documented; versions verified on PyPI; Pydantic AI iter() documented in official docs
- Architecture: HIGH - Patterns verified across official docs and working code examples; agent.iter() streaming pattern confirmed with multiple sources
- Pitfalls: HIGH - Most pitfalls sourced from official docs (pipe deadlock, patch_stdout) or confirmed GitHub issues (Shift+Enter); Rich Live + prompt-toolkit interaction is MEDIUM (community-verified, not officially documented)
- Event types: MEDIUM - Import paths and event taxonomy verified with multiple sources, but cross-provider behavior needs runtime validation

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (30 days — all three libraries are stable with slow-moving APIs)
