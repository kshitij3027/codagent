# Stack Research

**Domain:** Terminal-based AI coding agent (Python)
**Researched:** 2026-02-24
**Confidence:** HIGH (all core libraries verified via PyPI and official docs)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pydantic-ai-slim | 1.63.0 | Agent loop, tool registration, multi-model support, streaming | Reached v1.0 in September 2025 — API stable. Purpose-built for agentic loops with typed tools, structured output, and first-class support for OpenAI, Anthropic, and OpenRouter. Lighter than `pydantic-ai` full because it avoids bundling unused model SDKs. |
| rich | 14.3.3 | Terminal output — panels, spinners, Live display, syntax highlighting | The standard for polished Python terminal UIs. Live context manager + Spinner enables real-time streaming display. Markdown rendering built-in. Pydantic AI's own docs examples use Rich for streaming output. |
| prompt-toolkit | 3.0.52 | User input — async-safe prompt, FileHistory, slash-command completion | The standard interactive input library (powers IPython, pgcli, etc.). `PromptSession.prompt_async()` is the correct async entry point — does not block the event loop. FileHistory gives free persistent up-arrow history. |
| python-dotenv | 1.2.1 | Load `.env` file into environment variables at startup | Industry standard for 12-factor config. One call (`load_dotenv()`) populates all API keys from `.env` before any client is initialized. |
| Python | >=3.10 | Runtime | pydantic-ai requires Python 3.10+ (dropped 3.9 at v1.0). asyncio with `asyncio.run()` is the correct entry point for async agent loops. |

### Model Provider Extras (pydantic-ai-slim)

| Extra | Installs | Environment Variable | Model String Format |
|-------|----------|---------------------|---------------------|
| `openai` | `openai` SDK | `OPENAI_API_KEY` | `openai:gpt-4o`, `openai:gpt-5` |
| `anthropic` | `anthropic` SDK | `ANTHROPIC_API_KEY` | `anthropic:claude-sonnet-4-6` |
| `openrouter` | httpx-based provider | `OPENROUTER_API_KEY` | `openrouter:anthropic/claude-sonnet-4-5` |

Install all three at once:
```bash
pip install "pydantic-ai-slim[openai,anthropic,openrouter]"
```

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio (stdlib) | 3.10+ | Async event loop | Always — the agent loop, streaming, and prompt_async all require it |
| subprocess (stdlib) | 3.10+ | Shell command execution inside the `shell` tool | Always — no third-party library needed for running commands |
| shlex (stdlib) | 3.10+ | Safe shell tokenization | Use when splitting user command strings before passing to subprocess |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Package manager and virtual environment | Version 0.10.6 (Feb 2026). 10–100x faster than pip. Use `uv add` instead of `pip install`. Use `pyproject.toml` + `uv.lock` instead of `requirements.txt`. |
| pyproject.toml | Project metadata, dependency declaration | Standard (PEP 517/518/621). Replaces setup.py + requirements.txt. uv manages it natively. |

---

## Key Integration Patterns

### Agent Loop Pattern (pydantic-ai-slim)

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

agent = Agent(
    model=OpenAIChatModel("gpt-4o"),
    system_prompt="You are a coding agent...",
)

@agent.tool_plain
async def shell(command: str) -> str:
    """Execute a shell command and return stdout + stderr."""
    ...

# Non-streaming run
result = await agent.run(user_prompt, message_history=history)

# Streaming run (for real-time terminal output)
async with agent.run_stream(user_prompt) as stream:
    async for chunk in stream.stream_output():
        ...
```

### Streaming Event Loop for Tool-Call Display

Use `agent.iter()` to access fine-grained events including tool calls and text deltas:

```python
async with agent.iter(user_prompt) as run:
    async for node in run:
        if Agent.is_model_request_node(node):
            async with node.stream(run.ctx) as events:
                async for event in events:
                    # PartStartEvent, PartDeltaEvent (TextPartDelta, ToolCallPartDelta)
                    # FunctionToolCallEvent, FunctionToolResultEvent
                    ...
```

Event types to handle:
- `PartDeltaEvent` with `TextPartDelta` → stream text to terminal
- `FunctionToolCallEvent` → display tool name + args (approval gate here)
- `FunctionToolResultEvent` → display tool output (truncated)
- `FinalResultEvent` → conversation turn complete

### Approval Mode (Human-in-the-Loop)

Use pydantic-ai's **Deferred Tools** feature (`requires_approval=True` or `ApprovalRequired` exception):

```python
from pydantic_ai import Agent
from pydantic_ai.exceptions import ApprovalRequired

@agent.tool_plain
async def shell(command: str) -> str:
    if approval_mode:
        raise ApprovalRequired()
    return run_command(command)
```

When a deferred tool triggers, the agent returns a `DeferredToolRequests` object. Gather user input (approve/deny), build `DeferredToolResults`, then resume with a new `agent.run()` passing the original message history plus the `DeferredToolResults`.

### Async Input (prompt-toolkit)

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout

session = PromptSession(history=FileHistory("~/.coding_agent_history"))

async def get_input() -> str:
    with patch_stdout():  # Prevents Rich output from mangling the prompt
        return await session.prompt_async("> ")
```

`patch_stdout()` is the critical detail: it redirects other print/console output so Rich's streaming output does not corrupt the input line. Use it whenever Rich and prompt-toolkit coexist.

### Rich Display

```python
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

# Thinking spinner while model generates
with console.status("[bold green]Thinking...", spinner="dots"):
    result = await agent.run(prompt)

# Live streaming for token-by-token output
with Live(console=console, refresh_per_second=20) as live:
    async for chunk in stream.stream_output():
        live.update(Markdown(chunk))
```

---

## Installation

```bash
# Using uv (recommended)
uv init coding-agent
cd coding-agent
uv add "pydantic-ai-slim[openai,anthropic,openrouter]" rich prompt-toolkit python-dotenv

# Or using pip
pip install "pydantic-ai-slim[openai,anthropic,openrouter]" rich prompt-toolkit python-dotenv
```

`pyproject.toml` dependencies section:
```toml
[project]
requires-python = ">=3.10"
dependencies = [
    "pydantic-ai-slim[openai,anthropic,openrouter]>=1.63.0",
    "rich>=14.3.3",
    "prompt-toolkit>=3.0.52",
    "python-dotenv>=1.2.1",
]
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| pydantic-ai-slim | LangChain | When you need a massive ecosystem of pre-built integrations (RAG, memory, chains). LangChain is heavyweight with legacy abstractions and multiple ways to do the same thing. For a focused single-tool agent, it's overcomplicated. |
| pydantic-ai-slim | LlamaIndex | When your agent is data/knowledge-centric (RAG, document workflows). Overkill for a shell-tool agent. |
| pydantic-ai-slim (full install) | pydantic-ai (bundle) | Use the full bundle only if you want Pydantic Logfire observability included by default. Slim gives you exactly the SDKs you need. |
| prompt-toolkit `prompt_async()` | Rich's `Prompt.ask()` | Rich's built-in prompt is synchronous and limited — use it only for simple one-off confirmations (e.g., "Approve? y/n") between turns, not as the primary input loop. |
| asyncio `run()` entry point | Threading | Pydantic AI, prompt-toolkit, and Rich Live are all designed for asyncio. Threading creates race conditions on terminal I/O. Do not mix. |
| uv + pyproject.toml | pip + requirements.txt | `requirements.txt` is acceptable if you're already in a project that uses it. The project already has a `requirements.txt` — upgrade to `pyproject.toml` as a first step for a cleaner workflow. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| LangChain | Heavyweight, legacy abstractions, many ways to do the same thing — makes a simple shell-tool agent harder, not easier | pydantic-ai-slim |
| Textual | Full-screen TUI framework — designed for apps with persistent layouts (dashboards, editors). Overkill for a conversational scrolling terminal | Rich + prompt-toolkit |
| `pydantic-ai` (full bundle) | Installs all model SDKs including ones you don't use | `pydantic-ai-slim[openai,anthropic,openrouter]` |
| `input()` or `sys.stdin.readline()` | Blocking — freezes asyncio event loop, no history, no completion | `PromptSession.prompt_async()` |
| `prompt()` (not `prompt_async()`) | prompt-toolkit's sync `prompt()` blocks the event loop in async contexts | `await session.prompt_async()` |
| `threading.Thread` for background model calls | Creates race conditions on Rich console output and prompt-toolkit input | `asyncio.create_task()` |
| `subprocess.run()` (blocking) | Blocks the event loop during shell command execution | `asyncio.create_subprocess_shell()` with `communicate()` |
| Rich's `Prompt` for main input loop | Synchronous, no history, no completion — appropriate only for y/n confirmation prompts | `PromptSession.prompt_async()` from prompt-toolkit |

---

## Stack Patterns by Variant

**If approval mode (default):**
- Use pydantic-ai's deferred tools (`requires_approval=True`) for clean pause/resume
- Display tool name + args in a Rich Panel before prompting user
- Use `Rich.Prompt.ask("Approve? [y/n]")` for the simple yes/no (sync is OK here — agent loop is paused)
- Resume by passing `DeferredToolResults` to a new `agent.run()` with the same history

**If yolo mode (auto-run):**
- Skip deferred tools entirely; tool executes immediately
- Display tool call + output inline using `console.print()` with color-coded panels

**If switching models at runtime:**
- Pydantic AI supports `model=` as a parameter on each `agent.run()` call — you do not need separate Agent instances per model
- Build a simple dict mapping model name → model string and swap at runtime

**If streaming token output:**
- Use `agent.iter()` + `node.stream()` + `PartDeltaEvent` for per-token display
- Wrap in a Rich `Live` context for smooth rendering
- Use `TextPartDelta` for text tokens, `ToolCallPartDelta` for streaming tool arguments

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| pydantic-ai-slim>=1.63.0 | Python >=3.10 | v1.0 (Sept 2025) dropped Python 3.9. API stable until v2. |
| rich>=14.3.3 | Python >=3.8 | Rich 14.x is the current major; no breaking changes expected. |
| prompt-toolkit>=3.0.52 | Python >=3.8 | 3.0.x series has been stable for years. `prompt_async()` requires 3.0+. |
| python-dotenv>=1.2.1 | Python >=3.9 | Stable. `load_dotenv()` API has not changed. |
| pydantic-ai-slim + openai extra | openai SDK (auto-managed) | pydantic-ai manages openai SDK version as a transitive dep — do not pin it separately. |
| pydantic-ai-slim + anthropic extra | anthropic SDK (auto-managed) | Same — let pydantic-ai manage the anthropic SDK version. |

---

## Sources

- PyPI: `pydantic-ai` — Version 1.63.0 released Feb 23, 2026 — HIGH confidence
  https://pypi.org/project/pydantic-ai/
- Official docs: Pydantic AI installation, models, streaming — HIGH confidence
  https://ai.pydantic.dev/install/ | https://ai.pydantic.dev/models/ | https://ai.pydantic.dev/deferred-tools/
- Official docs: Pydantic AI OpenAI model setup — HIGH confidence
  https://ai.pydantic.dev/models/openai/
- Official docs: Pydantic AI Anthropic model setup — HIGH confidence
  https://ai.pydantic.dev/models/anthropic/
- Official docs: Pydantic AI OpenRouter model setup — HIGH confidence
  https://ai.pydantic.dev/models/openrouter/
- Official docs: Pydantic AI streaming events (iter, run_stream_events) — HIGH confidence
  https://ai.pydantic.dev/api/agent/ | https://deepwiki.com/pydantic/pydantic-ai/4.1-streaming-and-real-time-processing
- PyPI: `rich` — Version 14.3.3 released Feb 19, 2026 — HIGH confidence
  https://pypi.org/project/rich/
- Rich docs: Live display — MEDIUM confidence (async patterns not explicitly documented)
  https://rich.readthedocs.io/en/latest/live.html
- PyPI: `prompt-toolkit` — Version 3.0.52 released Aug 27, 2025 — HIGH confidence
  https://pypi.org/project/prompt-toolkit/
- Official docs: prompt-toolkit async integration and `prompt_async()` — HIGH confidence
  https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/asyncio.html
- PyPI: `python-dotenv` — Version 1.2.1 released Oct 26, 2025 — HIGH confidence
  https://pypi.org/project/python-dotenv/
- PyPI: `uv` — Version 0.10.6 released Feb 25, 2026 — HIGH confidence
  https://pypi.org/project/uv/
- Pydantic AI changelog — v1.0 release Sept 4 2025, API stability guarantee — HIGH confidence
  https://ai.pydantic.dev/changelog/
- pydantic-ai stream-markdown example (Rich + Live) — MEDIUM confidence
  https://ai.pydantic.dev/examples/stream-markdown/
- patch_stdout() for Rich + prompt-toolkit coexistence — MEDIUM confidence (documented in prompt-toolkit, community confirmed)
  https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html

---
*Stack research for: terminal-based AI coding agent (Python)*
*Researched: 2026-02-24*
