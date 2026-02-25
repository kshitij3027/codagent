# Phase 1: Core Agent Loop - Research

**Researched:** 2026-02-25
**Domain:** Python async agent loop with shell execution, multi-provider LLM support, signal handling
**Confidence:** HIGH

## Summary

Phase 1 builds a functional terminal coding agent: a Pydantic AI-powered ReAct loop that receives natural language prompts, executes shell commands via a single `shell` tool, and iterates until the task is complete. The agent supports three model providers (OpenAI GPT-5, Anthropic Claude 4.5, xAI Grok Code Fast via OpenRouter), two execution modes (approval and yolo), in-memory conversation history, Ctrl-C signal handling, and `.env`-based configuration. All output in this phase is plain text -- Rich UI comes in Phase 2.

The core technical challenge is wiring Pydantic AI's `agent.iter()` node-by-node execution API to an approval gate that intercepts tool calls before execution, while keeping the async event loop responsive to SIGINT for Ctrl-C abort. The recommended approach uses `agent.iter()` to step through `CallToolsNode` events where the approval check happens inside the tool function itself (before subprocess execution), avoiding the complexity of the deferred tools API for this use case.

**Primary recommendation:** Use Pydantic AI's `agent.iter()` for the outer loop with an approval gate inside the `shell` tool function. Use `asyncio.create_subprocess_shell()` with `communicate()` + `wait_for()` timeout for shell execution. Use `loop.add_signal_handler(SIGINT, ...)` for two-tier Ctrl-C handling.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Concise responses between tool calls -- brief explanations, not verbose narration. Like a senior dev pairing.
- Ask for clarification on ambiguous requests before acting (e.g., "fix the tests" -> ask which tests or what's failing)
- On command failure (non-zero exit), automatically analyze the error and retry with a different approach -- up to a reasonable limit before giving up
- After completing a multi-step task, provide a brief summary of what was done (e.g., "Done -- created 3 files and ran tests (all passed).")
- Display the command AND a one-line reason before asking for approval (e.g., "Checking project structure: `ls -la src/`")
- Simple y/n prompt -- pressing Enter (empty input) defaults to 'yes'
- On rejection (user says no): agent stops the current run and asks the user what they'd like to do instead
- Default mode on startup: approval (user must confirm each command)
- Maintain a blocklist of dangerous command patterns that still require approval even in yolo mode (e.g., `rm -rf /`, `DROP TABLE`, force pushes)
- All other commands execute automatically without pausing in yolo mode

### Claude's Discretion
- Whether to explain the plan before executing (plan-first vs just-go)
- Whether to display elapsed time for commands
- Exact system prompt wording and personality tone
- Error retry limit and backoff strategy
- Truncation marker format for shell output exceeding ~10K chars
- Startup banner content and format

### Deferred Ideas (OUT OF SCOPE)
- Dedicated file read/write/edit tools -- currently shell handles all filesystem interaction; consider as v2 enhancement if shell-only proves limiting
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CORE-01 | Agent loop using Pydantic AI receives user prompt and iteratively calls tools until task is complete | Pydantic AI `agent.iter()` provides node-by-node async iteration through UserPromptNode -> ModelRequestNode -> CallToolsNode cycle. `agent.run()` with `message_history` for multi-turn. |
| CORE-02 | System prompt instructs model it is a coding agent, should reason about problems, and use the shell tool | Pydantic AI supports static `system_prompt` param on Agent() and dynamic `@agent.instructions` decorator. System prompt persists across message history. |
| CORE-03 | Conversation history maintained in memory across turns within a session | `result.all_messages()` returns full history; pass to next `agent.run(message_history=...)`. In-memory list accumulation pattern. |
| SHEL-01 | Single `shell` tool takes a command string, executes it, and returns stdout + stderr | `@agent.tool_plain` decorator with `asyncio.create_subprocess_shell()` + `communicate()` for deadlock-safe output capture. |
| SHEL-02 | Shell output truncated at ~10K characters to prevent context window overflow | Post-`communicate()` truncation of combined stdout+stderr string with a visible marker before returning to model. |
| SHEL-03 | Subprocess has a timeout to kill commands that hang | `asyncio.wait_for(proc.communicate(), timeout=N)` catches `TimeoutError`, then `proc.kill()`. |
| MODL-01 | Environment variables loaded from `.env` file on startup | `python-dotenv` `load_dotenv()` called at startup before any provider initialization. |
| MODL-02 | Support three model providers: GPT-5 (OpenAI), Claude 4.5 (Anthropic), Grok Code (OpenRouter) | `pydantic-ai-slim[openai,anthropic,openrouter]`. Model strings: `openai:gpt-5`, `anthropic:claude-4.5-sonnet`, `openrouter:x-ai/grok-code-fast-1`. |
| MODE-01 | Approval mode (default): user confirms each tool call before execution | Approval gate inside shell tool function checks mode; if approval mode, prints command+reason, prompts y/n, returns denial message to model on rejection. |
| MODE-02 | Yolo mode: tool calls execute automatically without user confirmation | Same tool function; if yolo mode, skip prompt (but still check dangerous command blocklist). |
| SGNL-01 | Ctrl-C during agent work aborts current operation and returns to user prompt | `loop.add_signal_handler(signal.SIGINT, handler)` cancels the current agent run task; outer loop catches `CancelledError` and returns to prompt. |
| SGNL-02 | Ctrl-C at idle prompt exits the program | When at the input prompt (no agent task running), SIGINT triggers `sys.exit(0)` or allows default `KeyboardInterrupt` to propagate. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic-ai-slim[openai,anthropic,openrouter] | >=1.63.0 | Agent framework with ReAct loop, tool calling, multi-provider support | Pinned in project STATE.md; type-safe, production-grade agent framework |
| python-dotenv | >=1.2.1 | Load `.env` file into `os.environ` | Pinned in STATE.md; standard .env loading for Python projects |
| Python | >=3.10 | Runtime | Pinned in STATE.md; required for modern asyncio features and type hints |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio (stdlib) | -- | Async event loop, subprocess management, signal handling | Core of the agent loop; subprocess execution; SIGINT handling |
| subprocess (stdlib) | -- | Fallback reference only | Not used directly; asyncio.create_subprocess_shell preferred |
| signal (stdlib) | -- | Signal constants (SIGINT) | Used with loop.add_signal_handler() |
| shlex (stdlib) | -- | Shell escaping utilities | Not needed for create_subprocess_shell (passes to shell directly) |
| os (stdlib) | -- | Environment variable access | Post-dotenv access to API keys and config |
| sys (stdlib) | -- | Exit handling | sys.exit() for clean shutdown |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Approval gate inside tool function | Pydantic AI deferred tools (`requires_approval=True`) | Deferred tools require managing `DeferredToolRequests`/`DeferredToolResults` and resuming runs -- significantly more complex for a simple y/n CLI prompt. The `deferred_handler` inline approach is newer (Jan 2026) and not yet stable. In-tool gate is simpler and fully sufficient. |
| `asyncio.create_subprocess_shell()` | `subprocess.run()` (sync) | sync subprocess blocks the event loop, preventing Ctrl-C handling and future streaming. Async is required. |
| `agent.iter()` node stepping | `agent.run()` / `agent.run_sync()` | `run()` is opaque -- you can't intercept between model response and tool execution. `iter()` gives visibility into each node for logging/display, which Phase 2 will need. Starting with `iter()` avoids a rewrite. |
| In-memory message list | Database/file persistence | Out of scope per requirements. In-memory is correct for v1. |

**Installation:**
```bash
pip install "pydantic-ai-slim[openai,anthropic,openrouter]" python-dotenv
```

Or with uv (project uses uv v0.10.6 per STATE.md):
```bash
uv add "pydantic-ai-slim[openai,anthropic,openrouter]" python-dotenv
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  codagent/              # Package name (or similar)
    __init__.py
    main.py              # Entry point: async main loop, startup, shutdown
    agent.py             # Agent creation, system prompt, model registry
    config.py            # Settings class, .env loading, mode state
    models.py            # Model provider registry, model switching
    tools/
      __init__.py
      shell.py           # Shell tool: approval gate + subprocess execution
    conversation.py      # Conversation history management
    signals.py           # SIGINT handler setup, state tracking
pyproject.toml           # Project metadata, dependencies
.env.example             # Example environment variables
```

Build order (from STATE.md): `config.py` -> `models.py` -> `tools/shell.py` -> `conversation.py` -> `agent.py` -> `main.py`

### Pattern 1: Agent Loop with `agent.iter()`
**What:** Step through the agent execution node-by-node using async iteration
**When to use:** Always -- this is the main execution pattern
**Example:**
```python
# Source: https://ai.pydantic.dev/agent/ (iter() documentation)
from pydantic_ai import Agent
from pydantic_ai.agent import CallToolsNode, ModelRequestNode

agent = Agent(
    model='openai:gpt-5',
    system_prompt='You are a coding agent. Use the shell tool to execute commands.',
    tools=[shell_tool],
)

async def run_agent_turn(user_prompt: str, message_history: list) -> list:
    async with agent.iter(user_prompt, message_history=message_history) as run:
        async for node in run:
            if isinstance(node, CallToolsNode):
                # Tool execution happens here (approval gate is inside the tool)
                pass
            elif isinstance(node, ModelRequestNode):
                # Model is being called
                pass
        # Collect updated history
        return run.result.all_messages()
```

### Pattern 2: Approval Gate Inside Tool Function
**What:** Check execution mode and prompt user before running the subprocess
**When to use:** For the shell tool in approval mode
**Example:**
```python
# Source: Pydantic AI tools documentation + project CONTEXT.md decisions
import asyncio

DANGEROUS_PATTERNS = [
    'rm -rf /', 'rm -rf ~', 'rm -rf *',
    'DROP TABLE', 'DROP DATABASE', 'DELETE FROM',
    'git push --force', 'git push -f',
    'mkfs.', 'dd if=',
    ':(){:|:&};:',  # fork bomb
    '> /dev/sda',
]

async def shell_tool(command: str) -> str:
    """Execute a shell command and return stdout + stderr."""
    # Check dangerous commands (always, even in yolo)
    if is_dangerous(command):
        approved = await prompt_user_approval(command, reason="Dangerous command detected")
        if not approved:
            return "Command rejected by user. Dangerous command was not executed."

    # Check approval mode
    if config.mode == 'approval':
        approved = await prompt_user_approval(command, reason=None)
        if not approved:
            return "Command rejected by user."

    # Execute
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=120
        )
        output = combine_and_truncate(stdout, stderr, limit=10_000)
        return f"Exit code: {proc.returncode}\n{output}"
    except asyncio.TimeoutError:
        proc.kill()
        return "Command timed out after 120 seconds and was killed."
```

### Pattern 3: Two-Tier SIGINT Handling
**What:** First Ctrl-C cancels current agent run; second Ctrl-C (or Ctrl-C at idle) exits program
**When to use:** Always -- core UX requirement
**Example:**
```python
# Source: Python docs asyncio event loop + superfastpython.com patterns
import signal
import asyncio

class SignalState:
    def __init__(self):
        self.agent_task: asyncio.Task | None = None  # Set when agent is running

def setup_signal_handler(loop, state: SignalState):
    def handle_sigint():
        if state.agent_task and not state.agent_task.done():
            # Agent is running -> cancel it (returns to prompt)
            state.agent_task.cancel()
        else:
            # Idle -> exit program
            raise SystemExit(0)

    loop.add_signal_handler(signal.SIGINT, handle_sigint)
```

### Pattern 4: Multi-Turn Conversation Loop
**What:** Accumulate message history across user turns
**When to use:** The outer REPL loop
**Example:**
```python
# Source: https://ai.pydantic.dev/message-history/
message_history = []

while True:
    user_input = await get_user_input()  # prompt-toolkit in Phase 2, input() for now
    if not user_input:
        continue

    result = await agent.run(user_input, message_history=message_history)
    message_history = result.all_messages()
    print(result.output)
```

### Pattern 5: Model Provider Registry
**What:** Map friendly names to Pydantic AI model strings; switch at runtime
**When to use:** MODL-02 implementation
**Example:**
```python
# Source: https://ai.pydantic.dev/models/ + https://ai.pydantic.dev/models/openrouter/
MODEL_REGISTRY = {
    'gpt5': 'openai:gpt-5',
    'claude': 'anthropic:claude-4.5-sonnet',
    'groq': 'openrouter:x-ai/grok-code-fast-1',
}

# Runtime switching: pass model= to agent.run() or agent.iter()
result = await agent.run(prompt, model=MODEL_REGISTRY[selected_model], message_history=history)
```

### Anti-Patterns to Avoid
- **Blocking subprocess in async code:** Never use `subprocess.run()` inside an async tool function. It blocks the event loop, preventing Ctrl-C handling and any concurrent operations. Use `asyncio.create_subprocess_shell()`.
- **`Popen` + manual `wait()`:** Pipe deadlock risk with large output. Always use `communicate()`.
- **Deferred tools for simple CLI approval:** The `DeferredToolRequests`/`DeferredToolResults` pattern is designed for async/batch approval workflows (dashboards, email). For a synchronous CLI y/n prompt, an in-tool approval gate is simpler and avoids managing resume state.
- **Global signal.signal() in async code:** Use `loop.add_signal_handler()` instead. `signal.signal()` callbacks cannot safely interact with the event loop.
- **Storing raw message objects without copying:** `all_messages()` returns a reference. If you mutate it or the agent mutates it, conversations corrupt. Store the returned list directly (Pydantic AI returns a new list each call).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent ReAct loop | Custom LLM call + tool dispatch loop | Pydantic AI `Agent` with `agent.iter()` | Handles tool schema generation, argument validation, retry logic, usage tracking, message format across providers |
| Model provider abstraction | Custom HTTP clients per provider | Pydantic AI model classes (`openai:`, `anthropic:`, `openrouter:`) | Handles auth, serialization, streaming, rate limiting, error mapping per provider |
| Tool argument parsing | JSON parsing of model tool calls | Pydantic AI `@agent.tool_plain` | Auto-generates JSON schema from type hints + docstrings; validates arguments |
| .env file loading | Custom file parser | `python-dotenv` `load_dotenv()` | Handles comments, multiline values, variable expansion, `.env` file discovery |
| Message history serialization | Custom serializer | Pydantic AI `ModelMessagesTypeAdapter` | Type-safe serialization/deserialization of the complete message hierarchy |

**Key insight:** Pydantic AI eliminates the need to build the agent loop, tool dispatch, provider abstraction, and message management from scratch. The framework handles the hardest parts (cross-provider message format normalization, tool schema generation, retry logic). Our job is wiring: config, shell tool, approval gate, signal handling, and the outer REPL.

## Common Pitfalls

### Pitfall 1: Blocking the Event Loop with Synchronous I/O
**What goes wrong:** Using `input()` or `subprocess.run()` inside async code blocks the entire event loop. Ctrl-C stops working, the agent appears frozen.
**Why it happens:** Python's `input()` and `subprocess.run()` are blocking calls that prevent the event loop from processing signals or other tasks.
**How to avoid:** Use `asyncio.create_subprocess_shell()` for commands. For user input in Phase 1, use `loop.run_in_executor(None, input, prompt)` to run `input()` in a thread; Phase 2 replaces this with prompt-toolkit's `prompt_async()`.
**Warning signs:** Program doesn't respond to Ctrl-C during user input or command execution.

### Pitfall 2: Pipe Deadlocks with Large Output
**What goes wrong:** Subprocess hangs when stdout/stderr buffers fill (typically ~64KB). Neither process can proceed.
**Why it happens:** Using `proc.stdout.read()` + `proc.wait()` separately. If the buffer fills before you read it, the child blocks on write while the parent blocks on wait.
**How to avoid:** Always use `proc.communicate()` which reads both streams concurrently and waits for termination atomically.
**Warning signs:** Agent hangs on commands that produce more than a few KB of output (e.g., `find /`, `cat large_file.txt`).

### Pitfall 3: Context Window Overflow from Shell Output
**What goes wrong:** A single `ls -laR` or `cat` of a large file returns megabytes of text, consuming the model's entire context window. Subsequent reasoning degrades or fails.
**Why it happens:** No output truncation. The full output is passed back to the model as a tool result.
**How to avoid:** Truncate combined stdout+stderr to ~10K characters with a visible marker (e.g., `\n... [output truncated at 10000 chars, 45000 chars total] ...`). The marker tells the model output was cut so it can request specific portions if needed.
**Warning signs:** Token usage spikes; model starts producing low-quality or confused responses after a large output.

### Pitfall 4: OpenRouter Model Names Change Without Notice
**What goes wrong:** Hardcoded model name string `openrouter:x-ai/grok-code-fast-1` stops working because OpenRouter updated the model identifier.
**Why it happens:** OpenRouter model names are mutable; providers rename/version models regularly.
**How to avoid:** Make model names configurable (env var or config), not hardcoded constants. Log the actual model name on startup. Consider a fallback model. Document that model names should be verified against the OpenRouter models page.
**Warning signs:** `404` or `model_not_found` errors from OpenRouter API.

### Pitfall 5: Swallowed Ctrl-C During Subprocess Execution
**What goes wrong:** Pressing Ctrl-C while a subprocess is running kills the subprocess but also crashes the agent (or does nothing).
**Why it happens:** SIGINT propagates to the subprocess process group by default. If the parent also receives it and has no handler, it crashes. Or the signal is consumed by the subprocess and never reaches the Python handler.
**How to avoid:** Use `loop.add_signal_handler(signal.SIGINT, ...)` to handle SIGINT at the event loop level. The handler cancels the agent task, which propagates to `wait_for()`, which triggers `proc.kill()`. The outer loop catches `CancelledError` and returns to the prompt.
**Warning signs:** Ctrl-C kills the entire program instead of just aborting the current agent run.

### Pitfall 6: Message History Grows Unbounded
**What goes wrong:** After many turns, conversation history consumes all available context window tokens. The model starts losing earlier context or API calls fail with token limit errors.
**Why it happens:** `all_messages()` accumulates every turn. No pruning or compaction.
**How to avoid:** For Phase 1, set `usage_limits=UsageLimits(request_limit=N)` per run to bound individual runs. Monitor total message count. Context compaction is explicitly deferred to v2 (CTXT-01), but be aware of the growth. Consider a simple "last N messages" window if the issue arises during testing.
**Warning signs:** Increasing latency per turn; API errors about token limits.

### Pitfall 7: Approval Prompt Blocks Event Loop
**What goes wrong:** Using synchronous `input("Approve? [Y/n] ")` blocks the async event loop. Ctrl-C does not work during the approval prompt.
**Why it happens:** `input()` is a blocking call.
**How to avoid:** Wrap in `loop.run_in_executor()` or use an async input mechanism. Phase 2 replaces with prompt-toolkit `prompt_async()`.
**Warning signs:** Program unresponsive to Ctrl-C while waiting for approval.

## Code Examples

Verified patterns from official sources:

### Creating the Agent with System Prompt
```python
# Source: https://ai.pydantic.dev/agent/
from pydantic_ai import Agent

agent = Agent(
    model='openai:gpt-5',
    system_prompt=(
        'You are a coding agent. You help users with programming tasks by executing '
        'shell commands. Reason about the problem, then use the shell tool to interact '
        'with the filesystem and run commands. Be concise -- like a senior dev pairing. '
        'After completing a task, provide a brief summary of what was done.'
    ),
)
```

### Registering the Shell Tool
```python
# Source: https://ai.pydantic.dev/tools/
@agent.tool_plain
async def shell(command: str) -> str:
    """Execute a shell command. Returns stdout, stderr, and exit code.

    Use this tool to interact with the filesystem, run tests, install packages,
    and perform any command-line operation needed to complete the user's task.
    """
    # Approval gate and execution logic here (see Pattern 2 above)
    ...
```

### Multi-Turn Conversation with History
```python
# Source: https://ai.pydantic.dev/message-history/
from pydantic_ai import Agent

agent = Agent(model='openai:gpt-5', system_prompt='...')

message_history = []

# Turn 1
result = await agent.run('Create a hello.py file', message_history=message_history or None)
message_history = result.all_messages()

# Turn 2 -- agent remembers Turn 1
result = await agent.run('Now add a main guard to it', message_history=message_history)
message_history = result.all_messages()
```

### Async Shell Execution with Timeout and Truncation
```python
# Source: https://docs.python.org/3/library/asyncio-subprocess.html
import asyncio

TRUNCATION_LIMIT = 10_000  # ~10K characters

async def execute_command(command: str, timeout: int = 120) -> str:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()  # Reap the process
        return f"[TIMEOUT] Command timed out after {timeout}s and was killed."

    stdout = stdout_bytes.decode('utf-8', errors='replace')
    stderr = stderr_bytes.decode('utf-8', errors='replace')

    output = stdout
    if stderr:
        output += f"\n[stderr]\n{stderr}"

    if len(output) > TRUNCATION_LIMIT:
        total = len(output)
        output = output[:TRUNCATION_LIMIT] + f"\n\n... [output truncated at {TRUNCATION_LIMIT} chars, {total} chars total]"

    return f"Exit code: {proc.returncode}\n{output}"
```

### Loading Environment Configuration
```python
# Source: https://pypi.org/project/python-dotenv/
from dotenv import load_dotenv
import os

def load_config():
    load_dotenv()  # Loads .env from current directory or parents

    return {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'openrouter_api_key': os.getenv('OPENROUTER_API_KEY'),
        'default_model': os.getenv('DEFAULT_MODEL', 'gpt5'),
        'default_mode': os.getenv('DEFAULT_MODE', 'approval'),
        'command_timeout': int(os.getenv('COMMAND_TIMEOUT', '120')),
    }
```

### Dangerous Command Detection
```python
import re

DANGEROUS_PATTERNS = [
    r'rm\s+(-\w*\s+)*-rf\s+[/~*]',   # rm -rf / or ~ or *
    r'rm\s+(-\w*\s+)*-fr\s+[/~*]',   # rm -fr variant
    r'DROP\s+(TABLE|DATABASE)',         # SQL destructive
    r'DELETE\s+FROM\s+\w+\s*;?\s*$',   # DELETE without WHERE
    r'git\s+push\s+.*--force',         # force push
    r'git\s+push\s+.*-f\b',           # force push short flag
    r'mkfs\.',                          # format filesystem
    r'dd\s+if=',                        # raw disk write
    r'>\s*/dev/sd',                     # overwrite disk device
    r':\(\)\{.*\|.*&\}\s*;',           # fork bomb
]

def is_dangerous(command: str) -> bool:
    return any(re.search(pattern, command, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom LLM HTTP calls + manual tool parsing | Pydantic AI Agent with typed tools | 2024-2025 | Eliminates boilerplate; providers handled automatically |
| `agent.run()` / `agent.run_sync()` opaque execution | `agent.iter()` node-by-node stepping | Pydantic AI 2025+ | Enables mid-loop inspection, logging, and human-in-the-loop without deferred tools |
| `subprocess.run()` in sync code | `asyncio.create_subprocess_shell()` in async code | Always for async apps | Non-blocking execution; compatible with signal handling |
| Deferred tools batch approval (`DeferredToolRequests`) | `deferred_handler` inline resolution OR in-tool gate | Jan 2026 (deferred_handler still new) | For CLI agents, in-tool gate remains simplest; `deferred_handler` is promising but newer |
| OpenRouter via custom OpenAI-compatible client | Native `openrouter:` prefix in Pydantic AI | Pydantic AI 2025+ | First-class OpenRouter support with proper provider class |

**Deprecated/outdated:**
- `agent.run_sync()` for agent loops that need Ctrl-C: Use `agent.run()` (async) or `agent.iter()` instead. `run_sync()` blocks and prevents signal handling.
- Global `signal.signal(SIGINT, handler)` in asyncio: Use `loop.add_signal_handler()` which is event-loop-safe.

## Open Questions

1. **Exact GPT-5 and Claude 4.5 model name strings**
   - What we know: Pydantic AI uses `openai:gpt-5` and `anthropic:claude-4.5-sonnet` naming convention
   - What's unclear: The exact model IDs may differ (e.g., `gpt-5-latest`, `claude-4-5-sonnet-latest`). Model names evolve.
   - Recommendation: Make model strings configurable via environment variables with sensible defaults. Verify against live API at implementation time. Log the resolved model name on startup.

2. **Grok Code Fast 1 model name on OpenRouter**
   - What we know: Currently `x-ai/grok-code-fast-1` based on OpenRouter listings (Feb 2025). This is an xAI model, not a Groq model despite the user spec saying "Groq Code."
   - What's unclear: The user spec says "Groq Code (CodeFast)" but the actual model on OpenRouter is "Grok Code Fast 1" from xAI. This may be a naming confusion or the user may mean a different model.
   - Recommendation: Use `openrouter:x-ai/grok-code-fast-1` as default but confirm with user. Make configurable via env var `OPENROUTER_MODEL`.

3. **Approval prompt async behavior in Phase 1 (no prompt-toolkit)**
   - What we know: Phase 1 has no Rich or prompt-toolkit. We need a y/n prompt that doesn't block the event loop.
   - What's unclear: Whether `loop.run_in_executor(None, input, "prompt")` is sufficient or if edge cases exist with SIGINT during executor-wrapped input.
   - Recommendation: Use `run_in_executor` for Phase 1. Test Ctrl-C behavior during approval prompt. Phase 2 replaces with prompt-toolkit `prompt_async()`.

4. **`agent.iter()` vs `agent.run()` for approval pattern**
   - What we know: Both work. `iter()` gives node-by-node visibility. `run()` is simpler but opaque.
   - What's unclear: Whether `iter()` adds meaningful value in Phase 1 where there's no Rich UI to show intermediate states. The approval gate lives inside the tool regardless.
   - Recommendation: Start with `agent.run()` for simplicity in Phase 1 (approval gate is in the tool function, not at the node level). Consider `agent.iter()` if logging intermediate states proves valuable, or defer to Phase 2 when the Rich UI needs node-by-node rendering.

## Sources

### Primary (HIGH confidence)
- [Pydantic AI Agents docs](https://ai.pydantic.dev/agent/) - Agent creation, iter(), run(), system prompts, model settings
- [Pydantic AI Tools docs](https://ai.pydantic.dev/tools/) - @agent.tool, @agent.tool_plain, RunContext, tool registration
- [Pydantic AI Deferred Tools docs](https://ai.pydantic.dev/deferred-tools/) - DeferredToolRequests, requires_approval, ToolApproved/ToolDenied, deferred_handler
- [Pydantic AI Message History docs](https://ai.pydantic.dev/message-history/) - all_messages(), new_messages(), message_history parameter, conversation patterns
- [Pydantic AI Models Overview](https://ai.pydantic.dev/models/) - Provider naming, model strings, FallbackModel
- [Pydantic AI OpenRouter docs](https://ai.pydantic.dev/models/openrouter/) - OpenRouter configuration, model naming, OPENROUTER_API_KEY
- [Pydantic AI API: Agent](https://ai.pydantic.dev/api/agent/) - iter() signature, AgentRun, node types
- [Python asyncio subprocess docs](https://docs.python.org/3/library/asyncio-subprocess.html) - create_subprocess_shell, communicate, PIPE, timeout patterns
- [Python asyncio event loop docs](https://docs.python.org/3/library/asyncio-eventloop.html) - add_signal_handler

### Secondary (MEDIUM confidence)
- [DeepWiki: Pydantic AI Agent Run Lifecycle](https://deepwiki.com/pydantic/pydantic-ai/2.1-agent-run-lifecycle) - Node type details, execution flow
- [Martin Fowler: Building your own CLI Coding Agent with Pydantic-AI](https://martinfowler.com/articles/build-own-coding-agent.html) - Reference architecture, lessons learned
- [Asyncio Ctrl-C handling patterns](https://superfastpython.com/asyncio-control-c-sigint/) - Two-tier SIGINT, task cancellation patterns
- [OpenRouter: Grok Code Fast 1](https://openrouter.ai/x-ai/grok-code-fast-1) - Model name, provider, 256k context

### Tertiary (LOW confidence)
- [pydantic-ai-blocking-approval PyPI](https://libraries.io/pypi/pydantic-ai-blocking-approval) - Third-party blocking approval package (not recommended; in-tool gate is simpler)
- [GitHub Issue #3959: deferred_handler](https://github.com/pydantic/pydantic-ai/issues/3959) - deferred_handler proposal (new, API may change)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pinned versions in STATE.md, verified against official Pydantic AI docs and PyPI
- Architecture: HIGH - Patterns verified against official docs; build order from STATE.md; iter() and tool patterns confirmed
- Pitfalls: HIGH - Based on documented asyncio subprocess behavior, Pydantic AI official docs, and known Python async patterns
- Model names: MEDIUM - OpenRouter model names verified as of Feb 2025 but known to be mutable; GPT-5 and Claude 4.5 names are plausible but unverified against live API

**Research date:** 2025-02-25
**Valid until:** 2025-03-25 (30 days -- stable domain, but verify OpenRouter model names before implementation)
