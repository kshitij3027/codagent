# Roadmap: Coding Agent

**Project:** Terminal-based AI coding agent
**Created:** 2026-02-24
**Depth:** Comprehensive
**Coverage:** 19/19 requirements mapped

---

## Phases

- [x] **Phase 1: Core Agent Loop** - A safe, functional coding agent with plain-text output — the full working system before any UI polish
- [x] **Phase 2: Terminal UI** - Rich streaming display, prompt-toolkit input, and polished real-time output panels
- [ ] **Phase 3: Slash Commands and Runtime Control** - `/model`, `/approval`, `/new` slash commands with tab completion and runtime model/mode switching

---

## Phase Details

### Phase 1: Core Agent Loop

**Goal**: Users can run a functional coding agent that executes shell commands, stays safe, and works end-to-end — with plain terminal output
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03, SHEL-01, SHEL-02, SHEL-03, MODL-01, MODL-02, MODE-01, MODE-02, SGNL-01, SGNL-02

**Success Criteria** (what must be TRUE):
  1. User types a natural language coding task, the agent issues one or more shell commands, and the task is completed or the agent explains why it cannot be completed
  2. In approval mode (default), each shell command is shown to the user before execution and the agent waits for a yes/no — no command runs without acknowledgement
  3. In yolo mode, the agent executes shell commands automatically without pausing, completing multi-step tasks without user intervention
  4. Shell output longer than ~10K characters is truncated with a visible marker; the agent continues working rather than failing or flooding the context
  5. Ctrl-C during an active agent run aborts the run and returns to the user prompt; Ctrl-C at the idle prompt exits the program

**Plans:** 4 plans (3 complete + 1 gap closure)

Plans:
- [x] 01-01-PLAN.md — Project scaffolding, config loading, and model provider registry
- [x] 01-02-PLAN.md — Shell tool with async execution, truncation, timeout, approval gate, and dangerous command blocklist
- [x] 01-03-PLAN.md — Agent core with system prompt, conversation history, main REPL loop, and signal handling
- [x] 01-04-PLAN.md — UAT gap closure: fix rejection handling, dangerous command flow, and Ctrl-C idle exit

---

### Phase 2: Terminal UI

**Goal**: Users experience a polished, production-quality terminal interface with real-time streaming output, spinners, and color-coded panels
**Depends on**: Phase 1
**Requirements**: DISP-01, DISP-02, DISP-03, DISP-04

**Success Criteria** (what must be TRUE):
  1. A thinking spinner is visible during model inference; it disappears when the model produces output
  2. Each agent interaction (user prompt, model response, tool call, tool output) appears in a distinctly styled, color-coded Rich panel
  3. Tool call commands and their outputs are displayed in real-time as they execute, not batched after completion
  4. The input prompt supports up-arrow history navigation and tab completion for slash commands

**Plans:** 4 plans

Plans:
- [x] 02-01-PLAN.md — Rich display layer: panel factory, spinner, streaming text and tool output
- [x] 02-02-PLAN.md — prompt-toolkit input: PromptSession, FileHistory, slash command completion, key bindings
- [x] 02-03-PLAN.md — Agent streaming: switch to agent.iter(), streaming shell execution, styled approval
- [x] 02-04-PLAN.md — REPL integration: wire display + input + streaming into main loop, clean signal handling

---

### Phase 3: Slash Commands and Runtime Control

**Goal**: Users can switch models, toggle execution mode, and reset conversation at runtime via slash commands with tab completion
**Depends on**: Phase 1, Phase 2
**Requirements**: MODL-03, MODE-03, CORE-04

**Success Criteria** (what must be TRUE):
  1. User types `/model claude-4-5` (or another supported model name) and the next prompt runs on that model, with the current model shown in the UI
  2. User types `/approval` and the agent toggles between approval and yolo mode, printing the new mode so the user knows it changed
  3. User types `/new` and the conversation history is cleared; the next prompt starts a fresh session while API keys and model selection are preserved
  4. Tab-completing a partially typed slash command shows all matching options without requiring the user to remember exact command names

**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Slash command handlers (commands.py) and REPL dispatch wiring
- [ ] 03-02-PLAN.md — Tab completion: add /yolo, fix /approval description, /model argument completion

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Agent Loop | 4/4 | Complete | 2026-02-25 |
| 2. Terminal UI | 4/4 | Complete | 2026-02-27 |
| 3. Slash Commands and Runtime Control | 0/2 | In progress | - |

---

## Coverage Map

| Requirement | Phase |
|-------------|-------|
| CORE-01 | Phase 1 |
| CORE-02 | Phase 1 |
| CORE-03 | Phase 1 |
| CORE-04 | Phase 3 |
| SHEL-01 | Phase 1 |
| SHEL-02 | Phase 1 |
| SHEL-03 | Phase 1 |
| MODL-01 | Phase 1 |
| MODL-02 | Phase 1 |
| MODL-03 | Phase 3 |
| MODE-01 | Phase 1 |
| MODE-02 | Phase 1 |
| MODE-03 | Phase 3 |
| DISP-01 | Phase 2 |
| DISP-02 | Phase 2 |
| DISP-03 | Phase 2 |
| DISP-04 | Phase 2 |
| SGNL-01 | Phase 1 |
| SGNL-02 | Phase 1 |

**Total v1:** 19 requirements
**Mapped:** 19
**Unmapped:** 0

---
*Roadmap created: 2026-02-24*
*Last updated: 2026-04-05 after Phase 3 planning (2 plans created)*
