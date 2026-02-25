# Project Research Summary

**Project:** Terminal-based AI coding agent (Python)
**Domain:** Interactive CLI agent — conversational shell-tool executor with multi-model support
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

This project is a terminal-based AI coding agent: a Python CLI that accepts natural language tasks, runs an agentic loop (reason → act → observe), executes shell commands on behalf of the user, and streams results back in a polished Rich-based terminal UI. The expert approach — validated across Claude Code, Aider, OpenCode, Gemini CLI, gptme, and Codex CLI — converges on a tight, opinionated stack: pydantic-ai-slim as the agent orchestration layer, Rich for terminal output, prompt-toolkit for async input, and a single `shell` tool as the sole execution primitive. The single-tool design is a deliberate architectural choice: it is simpler, more composable, and more powerful than a surface of specialized read/write/edit tools because the shell handles everything and the model decides how to interact with it.

The recommended approach for this project follows a clear build order derived from component dependencies. The core agent loop — config, models, shell tool with truncation, conversation manager, and agent wiring — must be built and validated first, using plain `print()` output, before any Rich or prompt-toolkit work begins. This ensures the agentic loop is correctby itself before layering on display complexity. The terminal UI (Rich streaming, spinners, tool call panels, approval gate display) comes second. Multi-model support and slash commands come third, as they wrap a stable loop rather than building one.

The dominant risk category is the shell tool: interactive command hanging, subprocess pipe deadlock, context window overflow from untruncated output, and infinite agent loops are all Phase 1 concerns that must be addressed at the subprocess call site, not patched later. Security — prompt injection via file content and the "lies-in-the-loop" approval display vulnerability — is a Phase 1 design concern, not a hardening step for later. All critical pitfalls are documented, have known mitigations, and are straightforward to implement from day one if the team is aware of them.

---

## Key Findings

### Recommended Stack

All core libraries are stable, at confirmed current versions, and have high PyPI/official-docs confidence. pydantic-ai-slim reached v1.0 in September 2025 with a stable API guarantee; the slim variant installs only the model SDKs actually needed. The library natively handles streaming, the ReAct loop, tool registration, and multi-provider model abstraction. Rich and prompt-toolkit are mature, industry-standard libraries for their respective roles and have no viable alternatives for this use case.

See `.planning/research/STACK.md` for full integration patterns, version compatibility table, and what not to use.

**Core technologies:**
- `pydantic-ai-slim[openai,anthropic,openrouter]` (v1.63.0): Agent loop, tool registration, multi-model support, streaming — purpose-built for this exact use case, API stable until v2
- `rich` (v14.3.3): Terminal output — panels, spinners, Live display, syntax highlighting — the standard for Python terminal UIs
- `prompt-toolkit` (v3.0.52): Async-safe input, FileHistory, slash-command completion — use `prompt_async()` not `prompt()` (blocking)
- `python-dotenv` (v1.2.1): `.env` loading at startup for API keys — one `load_dotenv()` call before any client is initialized
- `uv` (v0.10.6): Package manager — 10-100x faster than pip; use with `pyproject.toml` + `uv.lock`
- Python >= 3.10: Required by pydantic-ai v1.0+

**Critical version note:** Do not pin the `openai` or `anthropic` SDKs separately — pydantic-ai manages these as transitive dependencies.

---

### Expected Features

The feature landscape is well-researched across 15+ current tools. The full table stakes list (13 features), differentiator analysis, and anti-feature rationale are in `.planning/research/FEATURES.md`.

**Must have (table stakes — v1):**
- Natural language task input with multi-turn conversation — core premise
- Shell command execution (single `shell` tool) — foundation of all filesystem interaction
- Shell output truncation at ~10k token limit — prevents context overflow on first real use
- Approval mode (confirm each tool call) as default — safety for new users
- Auto-run / yolo mode as explicit opt-in — required for power users and CI
- Rich-based terminal UI with streaming, spinner, and color-coded panels — now expected; monochrome feels dated
- prompt-toolkit input with history — table stakes for interactive terminal tools
- Slash commands: `/model`, `/approval`, `/new` — discoverability and efficiency
- Multi-model support: OpenAI, Anthropic, OpenRouter (Groq) — project requirement and genuine differentiator
- `.env` loading at startup — standard expected pattern
- Ctrl-C abort behavior: abort during work, exit at idle — correct terminal citizenship
- System prompt establishing coding agent role — required for consistent behavior
- Context reset command (`/new`) — required for non-trivial multi-session workflows

**Should have (competitive differentiators — v1):**
- Polished Rich UI with boxed tool call display — Claude Code is praised for this; it builds trust and aids debugging
- Clear display of raw tool call inputs and outputs at approval time — transparency that "black box" agents lack
- Multi-model runtime switching without conversation loss — uncommon enough to differentiate
- Slash command palette with tab completion — low cost, high perceived quality impact

**Defer (v2+):**
- MCP server integration — powerful but complex; shell covers most needs
- Persistent cross-session memory — privacy and staleness risks outweigh convenience
- Multi-agent orchestration — extreme complexity, validate need first
- LSP / browser / plugin system — out of scope for v1

**Deliberate anti-features (do not build):**
- Dedicated read/write/edit tools (shell handles everything with less complexity)
- Auto-commit to git without explicit user action (violates principle of least surprise)
- Full-screen TUI takeover (breaks composability; Rich inline output keeps the tool scriptable)
- Persistent history across sessions (stale context causes worse agent decisions)

---

### Architecture Approach

The standard architecture for this class of agent is a four-layer system: Input Layer (prompt-toolkit), Agent Core (pydantic-ai ReAct loop), Tool Execution Layer (single shell tool with approval gate), and Output Layer (Rich). These layers have clean boundaries and no cross-layer dependencies except through explicit interfaces. The project structure maps directly to this: `config.py`, `models.py`, `tools/shell.py`, `conversation.py`, `agent.py`, `ui/` (input, display, approval), and `main.py` as the coordinator. Build order is strictly determined by the dependency graph — config before models before tools before agent before UI.

See `.planning/research/ARCHITECTURE.md` for the full system diagram, data flow, component responsibility table, and anti-patterns.

**Major components:**
1. Input Layer (prompt-toolkit `PromptSession`) — async input, slash command dispatch, FileHistory
2. Conversation Manager — flat `list[ModelMessage]`, accumulated across turns, reset on `/new`
3. Agent Core (pydantic-ai `Agent`) — ReAct loop: UserPromptNode → ModelRequestNode → CallToolsNode → End; created once at startup
4. Model Abstraction (`models.py` registry) — name string → pydantic-ai model instance; `model=` override on each `run_stream()` call
5. Tool Execution Layer (`tools/shell.py`) — `subprocess.run()` with timeout + truncation + approval gate injection
6. Output Layer (Rich `Console`, `Live`, `Spinner`, `Panel`) — all rendering in `ui/display.py`, never inside tools

**Key patterns:**
- ReAct loop (reason + act) — every tool-using agent uses this; pydantic-ai implements it as a state machine automatically
- Single flat message history — one list, no threading, no branching; reset only on `/new`
- Approval gate at tool boundary — show raw command before execution; bypass entirely in yolo mode
- Model abstraction via provider swap — `model=` parameter on `run_stream()` replaces model without touching agent or history

---

### Critical Pitfalls

All 10 pitfalls in `.planning/research/PITFALLS.md` are Phase 1 concerns. The five most impactful, with prevention strategies:

1. **Interactive command hanging** — subprocess blocks indefinitely waiting for stdin TTY that never arrives (`npm create`, `git rebase -i`, editors). Prevention: hard timeout on every subprocess call (30-60s); system prompt instructs model to always use `--yes`/`--non-interactive` flags; detect and reject known interactive-only command patterns before execution.

2. **Context window overflow from untruncated shell output** — a single `npm test` or `cat largefile` can consume 5-15% of a 128K context window; after several such turns, the system prompt and task description are silently dropped and the model hallucinates. Prevention: enforce a hard character truncation limit (2,000-4,000 chars) in the shell tool with a visible truncation marker; make it configurable; never disable it.

3. **Infinite agent loop** — model retries a failing command indefinitely, accumulating API costs with no exit condition. Prevention: maximum tool call iteration limit (e.g., 50 per user prompt) configured in the agent; repeated identical command detection (same command 3x in 5 calls → abort with user message); display iteration count in UI.

4. **Prompt injection via malicious file content** — files read by the agent may contain embedded instructions that override the system prompt (68-93% success rate in September 2025 research). Prevention: approval mode default shows all outputs before next model step; system prompt explicitly states tool output is untrusted data; document yolo mode risks prominently.

5. **Approval mode display integrity ("lies-in-the-loop")** — the approval UI can be manipulated to show one command while another executes if the display is model-generated. Prevention: always display the exact raw command string passed to the shell as the primary UI element, never a model-generated description; never truncate the command in the display.

**Additional Phase 1 pitfalls (must not defer):**
- Subprocess pipe deadlock — use `subprocess.run(capture_output=True)`, never `Popen` + `wait()`
- Context drift (system prompt forgetting in long sessions) — keep system prompt under 500 tokens, bulletted, declarative
- Ctrl-C signal handling race conditions — `loop.add_signal_handler(signal.SIGINT, handler)`, test all 4 states
- Multi-provider abstraction leakage — test each provider independently; reset history on `/model` switch

---

## Implications for Roadmap

Based on the component dependency graph (ARCHITECTURE.md), the feature dependency tree (FEATURES.md), and the pitfall-to-phase mapping (PITFALLS.md), three phases are clearly indicated.

### Phase 1: Core Agent Loop

**Rationale:** Every other component depends on a working, safe agent loop. The shell tool must be correct (timeout, truncation, no pipe deadlock, approval gate) before anything else is testable. The ReAct loop with conversation management must be stable before UI work begins. All 10 critical pitfalls are Phase 1 concerns — none can be deferred safely.

**Delivers:** A functional, safe, text-output-only coding agent. User types a prompt, agent runs shell commands in a loop, asks for approval before each, streams minimal output to the terminal, maintains conversation across turns, and handles Ctrl-C cleanly.

**Addresses (from FEATURES.md):**
- Agent loop (pydantic-ai ReAct)
- Shell tool with output truncation and approval gate
- Yolo mode toggle
- Multi-turn conversation (in-memory)
- System prompt (coding agent role)
- `.env` loading at startup
- Ctrl-C abort behavior (abort during work / exit at idle)
- Multi-model support (all 3 providers wired up)

**Avoids (from PITFALLS.md):**
- Interactive command hanging (timeout + non-interactive flag instruction)
- Subprocess pipe deadlock (correct subprocess API)
- Context window overflow (hard truncation limit)
- Infinite agent loop (max iteration guard + loop detection)
- Prompt injection (system prompt untrusted-data instruction)
- Approval display integrity (raw command string shown, not model text)
- Signal handling race conditions (explicit asyncio signal handler)
- Context drift (concise, declarative system prompt)

**Build order within phase (from ARCHITECTURE.md):**
`config.py` → `models.py` → `tools/shell.py` → `conversation.py` → `agent.py` → `main.py` (minimal, `print()`-based)

---

### Phase 2: Terminal UI Polish

**Rationale:** Once the agent loop is verified correct, the UI layer can be added without risk of coupling display code to execution logic. Rich and prompt-toolkit have no dependency on agent correctness — they only consume the event stream. UI work before loop stability creates churn because display requirements change as loop behavior is refined.

**Delivers:** The polished, production-quality terminal experience. Spinner during inference, streaming token display in a Rich panel, color-coded tool call and tool output boxes, approval prompt showing the raw command with syntax highlighting, prompt-toolkit input with history and slash-command tab completion.

**Uses (from STACK.md):**
- `rich`: `Console`, `Live`, `Spinner`, `Panel`, `Markdown`, syntax highlighting
- `prompt-toolkit`: `PromptSession`, `FileHistory`, `WordCompleter` for slash commands
- `patch_stdout()` — critical for Rich + prompt-toolkit coexistence; prevents output mangling the input line

**Implements (from ARCHITECTURE.md):**
- `ui/display.py` — all Rich rendering; driven by async events from agent loop, never from inside tools
- `ui/approval.py` — approval gate display using raw command string as primary element
- `ui/input.py` — prompt-toolkit session wired to slash command dispatch

**Addresses (from FEATURES.md):**
- Rich-based UI (streaming, spinner, panels) — differentiating UX
- prompt-toolkit input with history — table stakes for interactive terminal tools
- Clear display of tool call inputs and outputs — trust-building transparency

**Avoids (from PITFALLS.md):**
- Coupling UI into tool/agent layer (anti-pattern: return plain strings from tools; render in `ui/`)
- Rich Live + spinner flickering (single `Live` context owns all render state)
- Synchronous subprocess in async event loop (use `asyncio.create_subprocess_exec` or `run_in_executor`)

---

### Phase 3: Slash Commands and Multi-Model Switching

**Rationale:** Slash commands (`/model`, `/approval`, `/new`) are convenience wrappers over features built in Phases 1 and 2. Building them before the loop and UI are stable creates churn. Multi-model switching requires the model registry (Phase 1) and the UI display of current model state (Phase 2) to already exist. `/new` requires the conversation manager (Phase 1) and an appropriate confirmation UX (Phase 2 UI) to be in place.

**Delivers:** Full power-user control surface. `/model [name]` switches the active model at runtime. `/approval` toggles between approval and yolo modes with printed confirmation of new state. `/new` resets conversation with a confirmation prompt. Current model displayed in the prompt prefix or status bar. Tab completion on all slash commands.

**Addresses (from FEATURES.md):**
- Slash command palette (`/model`, `/approval`, `/new`)
- Multi-model runtime switching
- Output confirmation on mode changes (avoids silent state change UX pitfall)

**Avoids (from PITFALLS.md):**
- Multi-provider abstraction leakage — `/model` switch resets conversation history; each provider integration-tested independently
- OpenRouter model name validity — model strings configurable via environment variable

---

### Phase Ordering Rationale

- **Dependency graph drives order:** config → models → tools → agent → UI → slash commands is the strict dependency chain from ARCHITECTURE.md. No phase can be built before the ones it depends on.
- **Safety before UX:** All 10 critical pitfalls are in Phase 1. The agent must be safe before it is pretty. Building Rich output before the shell tool has a timeout and truncation creates a false sense of completeness.
- **Table stakes before differentiators:** Phase 1 covers all 13 table-stakes features. Phase 2 covers the differentiating UI polish. Phase 3 covers convenience features. This ordering matches user expectations (a working agent with plain output is usable; a broken agent with a beautiful spinner is not).
- **Anti-features confirmed deferred:** Persistent history, dedicated file tools, auto-commit, full-screen TUI, and multi-agent orchestration are all excluded from all three phases per FEATURES.md research.

---

### Research Flags

**Phases with standard patterns (skip dedicated research-phase):**
- Phase 1: Shell tool implementation, subprocess patterns, pydantic-ai agent setup, and context management are all well-documented in official docs and open-source references (gptme, Claude Code analysis). The pitfalls are known and the mitigations are established.
- Phase 2: Rich and prompt-toolkit have extensive official documentation. The `patch_stdout()` coexistence pattern is documented and community-confirmed.
- Phase 3: Slash command dispatch over prompt-toolkit `WordCompleter` is well-documented. pydantic-ai model switching via `model=` override is in official docs.

**Phases likely needing targeted research during planning:**
- Phase 1 (OpenRouter model names): OpenRouter model name strings for Groq models change without notice. Before implementing the model registry, verify current exact strings against the OpenRouter API. This is a lookup task, not a design question.
- Phase 1 (Pydantic AI deferred tools): The deferred-tools / `ApprovalRequired` pattern for approval mode is documented but less battle-tested than the yolo mode path. Verify the exact API for `DeferredToolRequests` and `DeferredToolResults` against current pydantic-ai docs at implementation time.
- Phase 3 (Cross-provider history on `/model` switch): Research confirms that transferring conversation history across providers is problematic and recommends resetting. Confirm the exact behavior of `result.all_messages()` when switching providers at implementation time.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All library versions verified on PyPI; integration patterns verified against official pydantic-ai, Rich, and prompt-toolkit docs; no reliance on community inference for core patterns |
| Features | HIGH | Verified across 15+ current tools (2025-2026 sources); table stakes confirmed consistent across all major competitors; differentiator analysis backed by developer survey data |
| Architecture | HIGH | Corroborated across pydantic-ai official docs, Claude Code architecture analysis, and open-source reference (gptme); component boundaries and data flow consistent with multiple independent sources |
| Pitfalls | HIGH | Multiple independent sources including production post-mortems, active GitHub issues on Claude Code/Gemini CLI/OpenCode/Codex, published research (arXiv), and CPython bug database |

**Overall confidence: HIGH**

### Gaps to Address

- **OpenRouter model name strings for Groq:** These change without notice. The research notes the pattern but not the current exact strings. Validate against the OpenRouter API before implementing the model registry.
- **Rich async patterns not fully documented:** Rich's official docs cover `Live` for synchronous use; the async patterns (Rich `Live` inside asyncio event loop) are community-confirmed but not in official docs. The pydantic-ai stream-markdown example serves as a reference, but test the specific combination (Live + Spinner + streaming text + prompt-toolkit `patch_stdout()`) early in Phase 2 before building the full display layer.
- **pydantic-ai deferred tools API:** The `ApprovalRequired`/`DeferredToolRequests`/`DeferredToolResults` pattern is documented but may have changed in recent versions. Verify against v1.63.0 docs at implementation time; the simpler alternative (approval gate inside the tool function, before subprocess execution) is a viable fallback that does not require deferred tools.
- **Windows Ctrl-C behavior:** The research flags that Ctrl-C on Windows differs from macOS/Linux with prompt-toolkit's event loop integration. If Windows is a target platform, allocate extra testing time for signal handling in Phase 1.

---

## Sources

### Primary (HIGH confidence)
- PyPI: `pydantic-ai` v1.63.0, `rich` v14.3.3, `prompt-toolkit` v3.0.52, `python-dotenv` v1.2.1, `uv` v0.10.6
- Pydantic AI official docs: https://ai.pydantic.dev/ — agent lifecycle, models, streaming, deferred tools, message history
- Rich official docs: https://rich.readthedocs.io/en/stable/
- prompt-toolkit official docs: https://python-prompt-toolkit.readthedocs.io/en/master/
- gptme GitHub (open-source Python terminal agent reference): https://github.com/gptme/gptme
- Tembo 2026 CLI tools comparison (15 tools): https://www.tembo.io/blog/coding-cli-tools-comparison
- Faros AI developer reviews 2026: https://www.faros.ai/blog/best-ai-coding-agents-2026
- arXiv:2509.22040 — Prompt injection attacks on coding editors (Sept 2025)
- arXiv:2601.04170 — Agent drift quantification (Jan 2026)
- CPython bug #37424, CPython issue #96827 — subprocess timeout and asyncio Ctrl-C

### Secondary (MEDIUM confidence)
- Claude Code architecture analysis (PromptLayer, ZenML) — single-threaded loop, flat history rationale
- pydantic-ai streaming (DeepWiki) — `stream_text(delta=True)`, `StreamedRunResult`
- pydantic-ai agent run lifecycle (DeepWiki) — state machine nodes, loop termination
- Manus context engineering blog — shell output truncation best practices
- Mario Zechner (pi-coding-agent post-mortem) — MCP token overhead, system prompt token budgets
- GitHub issues: Claude Code #12054, #12507; Gemini CLI #10909; OpenCode #12233/12234

### Tertiary (LOW confidence — verify at implementation)
- Rich Live + asyncio async patterns (community-confirmed, not in official Rich docs)
- `patch_stdout()` for Rich + prompt-toolkit coexistence (documented in prompt-toolkit, community confirmed)
- OpenRouter model name strings for Groq (must be verified against live API before implementation)

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*
