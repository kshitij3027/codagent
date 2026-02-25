# Project State: Coding Agent

*Living memory for the project. Updated at every milestone.*

---

## Project Reference

**Core Value:** The agent reliably translates natural language coding requests into shell commands, executes them, and iterates until the task is done — with a clear, elegant terminal interface that shows exactly what's happening at every step.

**Current Focus:** Phase 1 — Core Agent Loop

---

## Current Position

**Active Phase:** 1 — Core Agent Loop
**Active Plan:** None (planning not yet started)
**Status:** Not started

```
Progress: [----------] 0%

Phase 1: Core Agent Loop       [ ] Not started
Phase 2: Terminal UI           [ ] Not started
Phase 3: Slash Commands        [ ] Not started
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases total | 3 |
| Phases complete | 0 |
| Requirements total | 19 |
| Requirements complete | 0 |
| Plans total | TBD |
| Plans complete | 0 |

---

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

### Architecture Notes

- Four-layer system: Input (prompt-toolkit) → Agent Core (pydantic-ai ReAct) → Tool Execution (shell tool + approval gate) → Output (Rich)
- Build order within Phase 1: `config.py` → `models.py` → `tools/shell.py` → `conversation.py` → `agent.py` → `main.py`
- Use `subprocess.run(capture_output=True)` — never `Popen + wait()` (pipe deadlock risk)
- Use `loop.add_signal_handler(signal.SIGINT, handler)` for Ctrl-C
- Use `prompt_async()` not `prompt()` in prompt-toolkit (blocking vs async)
- Use `patch_stdout()` for Rich + prompt-toolkit coexistence

### Research Flags (verify at implementation time)

- OpenRouter Groq model name strings change without notice — verify against live API before implementing model registry
- Pydantic AI deferred tools API (`ApprovalRequired`/`DeferredToolRequests`) — verify against v1.63.0 docs; simpler alternative is approval gate inside the tool function before subprocess execution
- Rich Live + asyncio async patterns — community-confirmed but not in official Rich docs; test the specific combination (Live + Spinner + streaming text + prompt-toolkit `patch_stdout()`) early in Phase 2
- Cross-provider history on `/model` switch — confirm exact behavior of `result.all_messages()` when switching providers

### Stack (pinned versions)

- `pydantic-ai-slim[openai,anthropic,openrouter]` v1.63.0
- `rich` v14.3.3
- `prompt-toolkit` v3.0.52
- `python-dotenv` v1.2.1
- `uv` v0.10.6
- Python >= 3.10

### Todos

- [ ] Verify current OpenRouter Groq model name strings before implementing model registry (Phase 1)
- [ ] Test Rich Live + asyncio combination early in Phase 2 before building full display layer

### Blockers

None.

---

## Session Continuity

**Last updated:** 2026-02-24 (roadmap created)
**Next action:** Run `/gsd:plan-phase 1` to create execution plan for Phase 1

---
*State initialized: 2026-02-24*
