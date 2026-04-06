# Phase 3: Slash Commands and Runtime Control - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can switch models, toggle execution mode, and reset conversation at runtime via slash commands with tab completion. The commands are `/model`, `/approval`, `/yolo`, `/new`, and `/help`. Tab completion already exists in `input.py` — this phase adds the actual handlers and wires them into the REPL loop.

</domain>

<decisions>
## Implementation Decisions

### /model switching
- Friendly name only — user types `/model claude`, `/model gpt5`, `/model groq` (MODEL_REGISTRY keys)
- Full Pydantic AI model strings (e.g., `anthropic:claude-4.5-sonnet`) are NOT accepted as arguments
- Bare `/model` with no argument: show the current active model AND list all available models
- After successful switch: one-line confirmation showing friendly name + resolved string, e.g. `Switched to claude (anthropic:claude-4.5-sonnet)`
- Conversation history carries over on model switch — user can switch mid-task without losing context
- Invalid model name: error message listing available models

### Mode commands
- Two separate commands, NOT a toggle: `/approval` switches to approval mode, `/yolo` switches to yolo mode
- Feedback after switch: one-line with explanation, e.g. `Mode: yolo — commands will auto-execute (dangerous commands still require approval)`
- No-op case (already in that mode): confirm current state, e.g. `Already in approval mode.`
- Add `/yolo` to the SlashCommandCompleter alongside existing `/approval` — both appear in tab completion with their own descriptions

### /new conversation reset
- Resets conversation history ONLY — model selection, mode (approval/yolo), and all config persist
- No confirmation prompt — instant reset (conversation is ephemeral in-memory state, not destructive)
- Post-reset feedback: one-line `Conversation cleared.` then normal prompt appears
- Implementation: clear the ConversationHistory object, do NOT recreate the Pydantic AI agent instance

### /help output
- Shows slash commands AND keyboard shortcuts (two sections)
- Styled as a Rich table: Command | Description columns
- Does NOT show current state (model, mode) — that's what bare `/model` is for
- Does NOT show version — that's in the startup banner
- Pure reference card: static content, no dynamic state

### Claude's Discretion
- Exact Rich table styling and column widths for /help
- Error message wording for invalid /model arguments
- Whether slash command dispatch lives in main.py or a dedicated commands.py module

</decisions>

<specifics>
## Specific Ideas

- Mode feedback should remind users about the dangerous command guardrail when switching to yolo — users should never worry that yolo means "no safety"
- `/model` bare output should make it obvious which model is currently active (e.g., checkmark or arrow indicator next to the active one)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-slash-commands-and-runtime-control*
*Context gathered: 2026-04-05*
