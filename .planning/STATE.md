---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-02-27T07:02:22Z"
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 8
  completed_plans: 8
---

# Project State: Coding Agent

*Living memory for the project. Updated at every milestone.*

---

## Project Reference

**Core Value:** The agent reliably translates natural language coding requests into shell commands, executes them, and iterates until the task is done — with a clear, elegant terminal interface that shows exactly what's happening at every step.

**Current Focus:** Phase 3 — Slash Commands and Runtime Control

---

## Current Position

**Active Phase:** 3 — Slash Commands and Runtime Control
**Active Plan:** Pending (Phase 3 plans not yet created)
**Status:** Phase 2 complete, Phase 3 ready to plan

```
Progress: [##########] 100%

Phase 1: Core Agent Loop       [X] Complete (4/4 plans complete, incl. UAT gap closure)
Phase 2: Terminal UI           [X] Complete (4/4 plans complete)
Phase 3: Slash Commands        [ ] Not started
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases total | 3 |
| Phases complete | 2 |
| Requirements total | 19 |
| Requirements complete | 15 |
| Plans total | 8 |
| Plans complete | 8 |

---
| Phase 02 P04 | 5min | 3 tasks | 4 files |
| Phase 02 P03 | 4min | 2 tasks | 2 files |
| Phase 02 P02 | 2min | 1 tasks | 4 files |
| Phase 02 P01 | 2min | 2 tasks | 1 files |

## Accumulated Context

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Single shell tool | Simpler architecture; model decides how to interact with filesystem |
| Pydantic AI over alternatives | User preference; cleaner abstractions; v1.0 stable API |
| Truncate shell output at ~10K chars | Prevents context window overflow on first real use |
| Approval mode as default | Safe default; prevents unintended command execution |
| Build loop before UI | All 10 critical pitfalls are Phase 1 concerns; safe before pretty |
| Reset history on /model switch | Cross-provider history transfer is problematic; clean reset is safer |
| Dataclass for Settings (not Pydantic BaseSettings) | Simple, mutable mode field, no extra dependency |
| Dynamic OpenRouter model resolution | Model names change without notice; env var override for resilience |
| Singleton settings with get_settings() | Cross-module config access with explicit initialization guard |
| In-tool approval gate (not deferred tools) | Simpler than DeferredToolRequests for CLI y/n; approval gate lives inside shell_tool function |
| Non-blocking input via run_in_executor | Keeps event loop responsive for Ctrl-C during approval prompt (Pitfall 7) |
| Compiled regex for dangerous patterns | Module-level compilation for O(1) cost on repeated is_dangerous() calls |
| agent.run() over agent.iter() for Phase 1 | Approval gate is inside tool; no node-level visibility needed until Phase 2 Rich UI |
| Shell tool registered via wrapper in create_agent() | Keeps tool docstring (what model sees) cleanly defined; delegates to shell_tool from tools module |
| Non-blocking REPL input via run_in_executor | Phase 1 workaround; Phase 2 replaces with prompt-toolkit prompt_async() |
| os._exit(0) for idle Ctrl-C | run_in_executor input() thread blocks Python shutdown; os._exit bypasses deadlock; Phase 2 prompt-toolkit eliminates this |
| Safety architecture in system prompt + docstring | Prevents model self-censoring on dangerous commands; tool-level approval gate handles safety |
| Rejection rule in system prompt (not tool code) | Tool-side rejection messages were already correct; model behavior was the problem |
| Escape+Enter for multi-line input | Shift+Enter not portable across terminals; Escape+Enter is the reliable alternative per prompt-toolkit community |
| SlashCommandCompleter only on standalone slash fragments | Prevents false trigger mid-sentence; only completes when text is purely a slash-command prefix |
| transient=True on all streaming Live contexts | Prevents duplicate output (Live content + final static panel); only final Markdown-rendered panel remains |
| refresh_per_second=12 for Live displays | Balances smoothness vs CPU per research Pitfall 3 |
| Live context for spinner (not Console.status) | Enables flicker-free update() transition to response panel without stop/restart |
| Module-level _display with set_display() in shell.py | Pydantic AI constrains tool signatures; module-level ref lets shell_tool access Display without changing its parameter list |
| Async wrapper for sync stream_tool_line | on_line callback typed as Awaitable; thin async wrapper bridges sync Display method |
| Shell output not re-displayed on FunctionToolResultEvent | Already streamed line-by-line via on_line callback during execution; avoids duplicate display |
| Console stderr routing for Rich output | patch_stdout() intercepts stdout and mangles Rich ANSI codes; stderr bypasses it while going to the same PTY |
| Signal handler re-registration before each agent turn | prompt-toolkit overrides SIGINT handler during prompt_async(); re-registering ensures Ctrl-C cancels agent tasks |
| tini as Docker PID 1 | Python as PID 1 has special Linux signal semantics preventing SIGINT delivery; tini forwards signals properly |
| Display.cleanup() on cancellation | Stops active Live context and resets buffers on Ctrl-C to prevent stale state corrupting next turn |

### Architecture Notes

- Four-layer system: Input (prompt-toolkit) → Agent Core (pydantic-ai ReAct) → Tool Execution (shell tool + approval gate) → Output (Rich)
- Build order within Phase 1: `config.py` → `models.py` → `tools/shell.py` → `conversation.py` → `agent.py` → `main.py`
- Use `asyncio.create_subprocess_shell` + `communicate()` + `wait_for()` — never `subprocess.run()` (blocks event loop) or `Popen + wait()` (pipe deadlock risk)
- Streaming execution: `asyncio.gather(read_stream(stdout), read_stream(stderr))` for concurrent pipe reading (avoids deadlock)
- Use `loop.add_signal_handler(signal.SIGINT, handler)` for Ctrl-C
- Use `prompt_async()` not `prompt()` in prompt-toolkit (blocking vs async)
- Use `patch_stdout()` for Rich + prompt-toolkit coexistence
- Rich Console writes to stderr (not stdout) to bypass patch_stdout() ANSI mangling
- Re-register SIGINT handler before each agent turn (prompt-toolkit overrides it during prompt_async)

### Research Flags (verify at implementation time)

- OpenRouter Groq model name strings change without notice — verify against live API before implementing model registry
- ~~Pydantic AI deferred tools API~~ -- RESOLVED: used in-tool approval gate (simpler for CLI y/n prompt)
- ~~Rich Live + asyncio async patterns~~ -- RESOLVED: Works with Console(file=sys.stderr, force_terminal=True). patch_stdout() mangles stdout ANSI; stderr bypass is the fix. Signal handler re-registration needed after each prompt_async() call.
- Cross-provider history on `/model` switch — confirm exact behavior of `result.all_messages()` when switching providers

### Stack (pinned versions)

- `pydantic-ai-slim[openai,anthropic,openrouter]` v1.63.0
- `rich` v14.3.3
- `prompt-toolkit` v3.0.52
- `python-dotenv` v1.2.1
- `uv` v0.10.6
- Python >= 3.10

### Todos

- [x] Verify current OpenRouter Groq model name strings before implementing model registry (Phase 1) -- made configurable via OPENROUTER_MODEL env var
- [x] Test Rich Live + asyncio combination early in Phase 2 before building full display layer -- RESOLVED: works with Console on stderr + force_terminal=True; patch_stdout() mangles stdout ANSI codes

### Blockers

None.

---

## Session Continuity

**Last updated:** 2026-02-27 (02-04-PLAN complete -- Phase 2 Terminal UI complete, REPL integration with post-checkpoint fixes)
**Last session:** 2026-02-27T07:02:22Z
**Next action:** Plan Phase 3 (Slash Commands and Runtime Control — /model, /approval, /new)

---
*State initialized: 2026-02-24*
