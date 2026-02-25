# Architecture Research

**Domain:** Terminal-based AI coding agent (Python, single-shell-tool)
**Researched:** 2026-02-24
**Confidence:** HIGH — corroborated across Pydantic AI official docs, Claude Code architecture analysis, and multiple open-source agent references (gptme, OpenCode)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INPUT LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Prompt Toolkit Session (PromptSession)                      │   │
│  │  - Input history (InMemoryHistory)                           │   │
│  │  - Word/slash completion (WordCompleter or custom)           │   │
│  │  - Slash command dispatch (/model, /approval, /new)          │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────────┘
                                  │ user_prompt (str)
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT CORE                                   │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────────────────────────────┐   │
│  │ Conversation │    │            Agent Loop (Pydantic AI)       │   │
│  │  Manager     │◄──►│                                          │   │
│  │              │    │  UserPromptNode → ModelRequestNode        │   │
│  │  message[]   │    │       ↑               ↓                  │   │
│  └──────────────┘    │  CallToolsNode ← (tool calls in response) │   │
│                       │       ↓                                  │   │
│                       │  End (no tool calls → return text)       │   │
│                       └──────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────┬───────────────────┘
                           │                      │
              model request│                      │tool call
                           ▼                      ▼
┌──────────────────────────────┐   ┌──────────────────────────────────┐
│      MODEL ABSTRACTION        │   │       TOOL EXECUTION LAYER        │
│                              │   │                                   │
│  Pydantic AI Model interface │   │  shell tool (single tool)         │
│  - OpenAIChatModel           │   │  - takes: command str             │
│  - AnthropicModel            │   │  - executes: subprocess           │
│  - OpenRouterModel (Groq)    │   │  - returns: stdout + stderr       │
│                              │   │  - truncates: at output limit     │
│  Selected via /model command │   │  - approval gate (if mode=approve)│
└──────────────────────────────┘   └──────────────────────────────────┘
                                                   │ tool result
                                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          OUTPUT LAYER (Rich)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Live Display / Console                                      │   │
│  │  - Thinking spinner (during model request)                   │   │
│  │  - Tool call box (command shown before execution)            │   │
│  │  - Tool output box (stdout/stderr after execution)           │   │
│  │  - Assistant text (streamed as tokens arrive)                │   │
│  │  - Approval prompt (if approval mode)                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Input Layer (Prompt Toolkit) | Accept user text, dispatch slash commands, maintain input history | `PromptSession` with `InMemoryHistory`, custom `Completer` for slash commands |
| Conversation Manager | Accumulate and pass `message_history` across turns; reset on `/new` | List of `ModelMessage` objects from Pydantic AI; passed via `message_history=` param |
| Agent Loop (Pydantic AI) | Orchestrate model calls, tool invocations, retries; terminate when no tool calls remain | `Agent.run_stream()` with state machine: UserPromptNode → ModelRequestNode → CallToolsNode → End |
| Model Abstraction | Translate tool calls and messages to provider-specific API format; return normalized responses | `OpenAIChatModel`, `AnthropicModel`, `OpenAIChatModel(provider=OpenAIProvider(base_url=...))` for OpenRouter |
| Tool Execution Layer | Execute the shell command, capture output, apply truncation, enforce approval gate | `subprocess.run()` wrapped in `@agent.tool`; approval prompt injected before execution |
| Output Layer (Rich) | Render streaming model text, tool call boxes, spinner, approval prompts with color and structure | `Console`, `Live`, `Spinner`, `Panel`/`Box`; driven by async events from the agent loop |

## Recommended Project Structure

```
coding_agent/
├── main.py                 # Entry point: .env load, startup defaults, run loop
├── agent.py                # Pydantic AI Agent definition, system prompt, tool registration
├── tools/
│   └── shell.py            # shell tool: subprocess execution, output truncation
├── models.py               # Model registry: name → Pydantic AI model instance mapping
├── conversation.py         # Conversation state: message list, reset, multi-turn passing
├── ui/
│   ├── input.py            # Prompt Toolkit session: history, completer, slash dispatch
│   ├── display.py          # Rich output: spinner, tool boxes, streaming text, panels
│   └── approval.py         # Approval gate: prompt before shell execution
├── config.py               # Config: defaults, env var loading, execution mode
└── .env                    # API keys, default model (not committed)
```

### Structure Rationale

- **agent.py:** The Pydantic AI `Agent` is the central orchestration object. Keeping it isolated from UI code prevents coupling between loop logic and display.
- **tools/shell.py:** The single tool has its own file. This is the most likely place for changes (truncation logic, error handling). Isolated to contain blast radius.
- **models.py:** Model selection (via `/model` slash command) means the mapping from name strings to Pydantic AI model instances needs one canonical location.
- **conversation.py:** Multi-turn state (the `message_history` list) must persist across multiple `agent.run()` calls and be resettable via `/new`. Single responsibility module.
- **ui/:** The entire Rich + Prompt Toolkit surface in one package. Input and output are separate modules because they have no direct dependency on each other; only `main.py` coordinates them.
- **config.py:** Centralizes env var access and execution mode state so nothing reads `os.environ` scattered across modules.

## Architectural Patterns

### Pattern 1: ReAct Loop (Reason + Act)

**What:** The agent alternates between reasoning (model inference) and acting (tool calls) in a tight loop. Each tool result is appended to the message history and fed back to the model on the next iteration. The loop exits only when the model produces a response with no tool calls.

**When to use:** All terminal coding agents use this pattern. It is the standard design for tool-using agents.

**Trade-offs:** Simple to implement and debug. Context window grows with each tool call — must truncate outputs to prevent overflow.

**Example:**
```python
# Pydantic AI's state machine implements this automatically
# The loop in terms of messages looks like:
# [system] → [user: "write a test"] → [model: tool_call(shell, "ls")] →
# [tool: stdout] → [model: tool_call(shell, "cat foo.py")] →
# [tool: stdout] → [model: "I've written the test..."] → END

async with agent.run_stream(user_prompt, message_history=history) as result:
    async for text in result.stream_text(delta=True):
        display.append(text)  # stream tokens to Rich output
    history = result.all_messages()  # accumulate for next turn
```

### Pattern 2: Single Flat Message History

**What:** All conversation turns share one flat list of messages. No threading, no branching, no per-session isolation beyond explicit reset. Claude Code's internal architecture confirms this: "one flat message history, one thread, no competing personas."

**When to use:** Single-user terminal agent with in-memory state only.

**Trade-offs:** Simple to reason about and implement. Not suitable for multi-user or persistent-across-sessions scenarios (out of scope for v1).

**Example:**
```python
# conversation.py
class ConversationManager:
    def __init__(self):
        self._history: list[ModelMessage] = []

    def get(self) -> list[ModelMessage]:
        return self._history

    def update(self, new_messages: list[ModelMessage]) -> None:
        self._history = new_messages  # replace with all_messages() result

    def reset(self) -> None:
        self._history = []  # /new command
```

### Pattern 3: Approval Gate at Tool Boundary

**What:** Before executing a shell command, the agent pauses and displays the proposed command to the user. The user confirms or denies. In "yolo" mode, this gate is bypassed entirely.

**When to use:** Default mode for any agent that can execute arbitrary shell commands. Essential for safety when commands can modify the filesystem.

**Trade-offs:** Adds latency and user friction but prevents destructive unintended commands. Toggle to yolo mode for power users.

**Example:**
```python
# tools/shell.py
@agent.tool
async def shell(ctx: RunContext[AgentDeps], command: str) -> str:
    if ctx.deps.approval_mode:
        display.show_tool_call(command)
        confirmed = await approval.prompt_user(command)
        if not confirmed:
            return "[command rejected by user]"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr
    return truncate(output, limit=ctx.deps.output_limit)
```

### Pattern 4: Model Abstraction via Provider Swap

**What:** The agent is declared once against Pydantic AI's `Model` interface. At runtime, the active model is selected from a registry. Switching models replaces the model instance; the agent loop, tool definitions, and message history are unchanged.

**When to use:** Any agent requiring multi-provider support (OpenAI, Anthropic, OpenRouter).

**Trade-offs:** Clean separation. Edge cases exist in provider-specific message format differences (handled by Pydantic AI internally). OpenRouter requires using `OpenAIChatModel` with a custom `OpenAIProvider(base_url=...)`.

**Example:**
```python
# models.py
MODELS = {
    "gpt-5": lambda: OpenAIChatModel("gpt-5"),
    "claude-4-5": lambda: AnthropicModel("claude-sonnet-4-5"),
    "groq-code": lambda: OpenAIChatModel(
        "openai/codex-mini",
        provider=OpenAIProvider(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY)
    ),
}

def get_model(name: str) -> Model:
    return MODELS[name]()
```

## Data Flow

### Turn Request Flow

```
[User types prompt + presses Enter]
         │
         ▼
[Prompt Toolkit] ─── slash command? ──► [dispatch: /model /approval /new]
         │ no
         ▼
[Conversation Manager: get current history]
         │
         ▼
[Agent.run_stream(prompt, message_history=history, model=active_model)]
         │
         ├── UserPromptNode: attach system prompt + history + user prompt
         │
         ▼
[ModelRequestNode: send to LLM provider (OpenAI/Anthropic/OpenRouter)]
         │
         ├── streaming tokens ──► [Rich display: stream text delta]
         │
         ▼ (model returns tool call)
[CallToolsNode: extract command string]
         │
         ├── approval_mode=True ──► [Rich: show proposed command]
         │                          [Approval gate: wait for y/n]
         │
         ▼
[Tool Execution: subprocess.run(command)]
         │
         ├── stdout + stderr
         ▼
[Truncate output at configured limit]
         │
         ├── Rich: display tool output box
         │
         ▼
[ToolReturnPart appended to message history]
         │
         ▼
[ModelRequestNode again: model sees tool result, decides next action]
         │
         └── no more tool calls ──► End node
                                       │
                                       ▼
                            [Rich: display final assistant text]
                                       │
                                       ▼
                         [Conversation Manager: update history]
                                       │
                                       ▼
                            [Prompt Toolkit: show next prompt]
```

### Key Data Flows

1. **User prompt → model:** `str` → `UserPromptNode` attaches to accumulated `list[ModelMessage]` → serialized to provider API format by Pydantic AI model layer
2. **Tool call → execution → result:** `ToolCallPart(tool_name="shell", args={"command": "..."})` → `subprocess.run()` → `str` (stdout+stderr, truncated) → `ToolReturnPart` back into message history
3. **Streaming tokens → display:** `StreamedRunResult.stream_text(delta=True)` yields `str` deltas → Rich `Console.print()` or `Live` update in real time
4. **History accumulation:** After each `run_stream()`, `result.all_messages()` replaces the conversation manager's list, providing full context on the next turn
5. **Model switch:** `/model groq-code` → `models.get_model("groq-code")` → new `Model` instance → passed as `model=` override on next `run_stream()` call; history is unchanged

## Scaling Considerations

This is a single-user terminal application. Traditional scaling concerns (users, throughput, database) do not apply. The relevant "scaling" concerns are context window size and output volume.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Short tasks (< 10 tool calls) | Default approach: flat message history, full context passed each turn |
| Long tasks (10–50 tool calls) | Output truncation at shell level prevents context overflow; sufficient for v1 |
| Very long tasks (50+ tool calls) | Context compression: summarize older messages using Pydantic AI `history_processors`; or trigger a `/new` to reset |

### Scaling Priorities

1. **First bottleneck — context window overflow:** Shell output without truncation can fill the context window in a few large `cat` or `grep` results. Fix: enforce an output character limit (e.g., 10,000 chars) in the shell tool before the result is appended to history.
2. **Second bottleneck — model latency for long histories:** As the message list grows, prompt tokens increase, and each round-trip gets slower. Fix: `history_processors` to drop or summarize messages beyond a rolling window.

## Anti-Patterns

### Anti-Pattern 1: Coupling UI Code into the Agent or Tool Layer

**What people do:** Print Rich output directly inside the tool function or agent callback, mixing rendering with execution logic.

**Why it's wrong:** Makes the tool untestable. Tool calls execute in Pydantic AI's internal `CallToolsNode` — injecting Rich console calls there ties the entire execution pipeline to terminal output. Testing requires mocking the console globally.

**Do this instead:** Return plain strings from tools. Emit display events from the outer `run_stream()` loop in `main.py` or `ui/display.py`, which reads the streaming result and renders it.

### Anti-Pattern 2: Untruncated Shell Output

**What people do:** Return the full stdout of a shell command to the model without any size limit.

**Why it's wrong:** A single `cat largefile.py` or `npm install` log can be 100KB+. This floods the model context window, increases token cost dramatically, and can cause the model to lose track of the task.

**Do this instead:** Truncate at a character limit (2,000–10,000 chars). Include a message at the truncation point: `\n[output truncated at 10000 chars]`. The model will use targeted follow-up commands if it needs more.

### Anti-Pattern 3: Recreating the Agent on Every Turn

**What people do:** Instantiate a new `Agent(...)` on every user prompt to "reset" state between turns.

**Why it's wrong:** The `Agent` object holds tool registrations and the system prompt. Recreating it is wasteful. Conversation state in Pydantic AI is carried in the `message_history` list, not inside the Agent object itself.

**Do this instead:** Create the `Agent` once at startup. Reset conversation state by clearing the `ConversationManager` list on `/new`. Pass the updated `message_history=` list on each `run_stream()` call.

### Anti-Pattern 4: Hard-Coding Model Strings Throughout the Codebase

**What people do:** Scatter `model="gpt-4o"` or `model="claude-3-5-sonnet"` strings across agent calls, tool handlers, and config.

**Why it's wrong:** Switching models (via `/model` slash command) requires finding and updating every call site. Inconsistencies cause the agent to use a stale model after the user switches.

**Do this instead:** Maintain a single `active_model` variable in `config.py` or a `ConversationState` object. Every `agent.run_stream()` call reads from that one source.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI API | `OpenAIChatModel("gpt-5")` with `OPENAI_API_KEY` env var | Direct SDK via Pydantic AI |
| Anthropic API | `AnthropicModel("claude-sonnet-4-5")` with `ANTHROPIC_API_KEY` env var | Direct SDK via Pydantic AI |
| OpenRouter (Groq) | `OpenAIChatModel("openai/codex-mini", provider=OpenAIProvider(base_url="https://openrouter.ai/api/v1"))` | OpenAI-compatible endpoint; `OPENROUTER_API_KEY` env var |
| Local filesystem | `subprocess.run(command, shell=True)` inside shell tool | No direct SDK; all filesystem interaction goes through shell commands |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Input Layer ↔ Agent Core | `user_prompt: str` passed to `agent.run_stream()` | Input layer also dispatches slash commands that mutate config state |
| Agent Core ↔ Tool Execution | Pydantic AI `@agent.tool` decorator; `RunContext` provides deps (approval mode, output limit) | Tool result returned as `str`; Pydantic AI handles wrapping into `ToolReturnPart` |
| Agent Core ↔ Conversation Manager | `result.all_messages()` returned after each run; stored and passed as `message_history=` next run | One-way after each turn: agent produces new messages; manager stores them |
| Agent Core ↔ Model Abstraction | `model=` parameter on `agent.run_stream()` (runtime override) or `Agent(model=...)` default | Model instance swapped via `/model` command without touching agent definition |
| Agent Core ↔ Output Layer | `result.stream_text(delta=True)` async generator consumed in the calling loop; tool call events surfaced via `result.get_agent_run()` | Rich rendering happens in the caller (main.py / ui/display.py), not inside the agent |

## Build Order Implications

The component dependency graph determines which modules must be built before others can be tested end-to-end.

```
Dependency order (each item depends on items above it):

1. config.py           — no dependencies; env var loading, mode defaults
2. models.py           — depends on config (API keys); defines model registry
3. tools/shell.py      — depends on config (approval mode, output limit)
4. conversation.py     — no dependencies; pure message list management
5. agent.py            — depends on models, tools, conversation; creates Agent
6. ui/approval.py      — no dependencies; pure Prompt Toolkit prompt
7. ui/display.py       — no dependencies; pure Rich rendering
8. ui/input.py         — depends on config (for slash command handlers)
9. main.py             — depends on everything; wires the loop together
```

**Suggested build phases:**
- Phase 1 (core loop, no UI): `config.py` → `models.py` → `tools/shell.py` → `conversation.py` → `agent.py` → `main.py` (minimal, print-based)
- Phase 2 (terminal UI): `ui/display.py` → `ui/approval.py` → `ui/input.py` → integrate into `main.py`
- Phase 3 (multi-model + slash commands): `models.py` registry expansion → slash command dispatch in `ui/input.py`

This order means a working agent loop is verifiable before any Rich/Prompt Toolkit work begins. The shell tool and conversation management can be tested with simple `print()` calls.

## Sources

- [Pydantic AI Agent Documentation](https://ai.pydantic.dev/agent/) — Agent component structure, tool registration, run lifecycle (HIGH confidence)
- [Pydantic AI Message History](https://ai.pydantic.dev/message-history/) — `all_messages()`, `message_history=` parameter, `history_processors` (HIGH confidence)
- [Pydantic AI Model Overview](https://ai.pydantic.dev/models/overview/) — Model interface, provider abstraction, OpenRouter integration (HIGH confidence)
- [Pydantic AI Agent Run Lifecycle (DeepWiki)](https://deepwiki.com/pydantic/pydantic-ai/2.1-agent-run-lifecycle) — State machine nodes, loop termination, tool processing (MEDIUM confidence — third-party analysis)
- [Claude Code Master Agent Loop (PromptLayer)](https://blog.promptlayer.com/claude-code-behind-the-scenes-of-the-master-agent-loop/) — Single-threaded loop design, h2A queue, flat message history rationale (MEDIUM confidence — reverse-engineered analysis)
- [Claude Code Architecture (ZenML)](https://www.zenml.io/llmops-database/claude-code-agent-architecture-single-threaded-master-loop-for-autonomous-coding) — Single-threaded master loop, context compression at 92% (MEDIUM confidence)
- [OpenCode Architecture](https://brlikhon.engineer/blog/opencode-ai-the-complete-guide-to-the-open-source-terminal-coding-agent-revolutionizing-development-in-2026) — Client-server separation, TUI/backend split pattern (MEDIUM confidence)
- [gptme GitHub](https://github.com/gptme/gptme) — Open-source Python terminal agent reference implementation (HIGH confidence — primary source)
- [Rich Live Display Documentation](https://rich.readthedocs.io/en/stable/live.html) — Live display patterns for streaming output (HIGH confidence)
- [Pydantic AI Streaming (DeepWiki)](https://deepwiki.com/pydantic/pydantic-ai/4.1-streaming-and-real-time-processing) — `stream_text(delta=True)`, `StreamedRunResult` (MEDIUM confidence)

---
*Architecture research for: terminal-based AI coding agent*
*Researched: 2026-02-24*
