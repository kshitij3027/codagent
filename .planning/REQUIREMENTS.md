# Requirements: Coding Agent

**Defined:** 2026-02-24
**Core Value:** The agent reliably translates natural language coding requests into shell commands, executes them, and iterates until the task is done — with a clear, elegant terminal interface that shows exactly what's happening at every step.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Agent Core

- [x] **CORE-01**: Agent loop using Pydantic AI receives user prompt and iteratively calls tools until task is complete
- [x] **CORE-02**: System prompt instructs model it is a coding agent, should reason about problems, and use the shell tool
- [x] **CORE-03**: Conversation history maintained in memory across turns within a session
- [ ] **CORE-04**: User can reset conversation via `/new` command, clearing history but preserving config

### Shell Execution

- [x] **SHEL-01**: Single `shell` tool takes a command string, executes it, and returns stdout + stderr
- [x] **SHEL-02**: Shell output truncated at ~10K characters to prevent context window overflow
- [x] **SHEL-03**: Subprocess has a timeout to kill commands that hang (e.g. interactive prompts)

### Model Support

- [x] **MODL-01**: Environment variables loaded from `.env` file on startup (API keys, config)
- [x] **MODL-02**: Support three model providers: GPT-5 (OpenAI), Claude 4.5 (Anthropic), Groq Code (OpenRouter)
- [ ] **MODL-03**: User can switch between models at runtime via `/model` slash command

### Execution Modes

- [x] **MODE-01**: Approval mode (default): user confirms each tool call before execution
- [x] **MODE-02**: Yolo mode: tool calls execute automatically without user confirmation
- [ ] **MODE-03**: User can toggle between approval and yolo via `/approval` slash command

### Terminal UI

- [x] **DISP-01**: Rich-based streaming output with thinking spinner during model inference
- [x] **DISP-02**: Each interaction displayed in a styled box with color coding
- [x] **DISP-03**: Tool call inputs and outputs displayed in panels as they happen in real-time
- [x] **DISP-04**: Prompt Toolkit input with command history and slash command completion

### Signal Handling

- [x] **SGNL-01**: Ctrl-C during agent work aborts current operation and returns to user prompt
- [x] **SGNL-02**: Ctrl-C at idle prompt exits the program

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Context Management

- **CTXT-01**: Context compaction or summarization when conversation grows long
- **CTXT-02**: Per-project configuration file (e.g., .agent/config.toml)

### Git Integration

- **GITX-01**: /commit slash command for AI-generated commit messages
- **GITX-02**: Show git diff summary after agent makes file changes

### Output Control

- **OUTP-01**: Output verbosity flag (--quiet) for scripting and CI use

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Persistent conversation history across sessions | Stale context degrades model decisions; in-memory only for v1 |
| Dedicated file read/write/edit tools | Shell tool handles all filesystem interaction; simpler architecture |
| Web browsing / search capabilities | Expands attack surface; shell `curl` covers targeted fetches |
| Plugin / extension system | Premature API stabilization; v1 serves 90% of use cases without it |
| Multi-agent orchestration | Extreme complexity; single agent loop handles most tasks |
| Full-screen TUI takeover | Breaks terminal composability; Rich inline output preferred |
| Auto-commit to git | Violates principle of least surprise; user decides when to commit |
| MCP server integration | Powerful but complex; defer until shell-only limitations are hit |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 1 | Complete |
| CORE-02 | Phase 1 | Complete |
| CORE-03 | Phase 1 | Complete |
| CORE-04 | Phase 3 | Pending |
| SHEL-01 | Phase 1 | Complete |
| SHEL-02 | Phase 1 | Complete |
| SHEL-03 | Phase 1 | Complete |
| MODL-01 | Phase 1 | Complete |
| MODL-02 | Phase 1 | Complete |
| MODL-03 | Phase 3 | Pending |
| MODE-01 | Phase 1 | Complete |
| MODE-02 | Phase 1 | Complete |
| MODE-03 | Phase 3 | Pending |
| DISP-01 | Phase 2 | Complete |
| DISP-02 | Phase 2 | Complete |
| DISP-03 | Phase 2 | Complete |
| DISP-04 | Phase 2 | Complete |
| SGNL-01 | Phase 1 | Complete |
| SGNL-02 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-25 after 01-03-PLAN execution (Phase 1 complete)*
