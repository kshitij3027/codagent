# Phase 2: Terminal UI - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Rich, polished terminal interface with real-time streaming output, color-coded panels, thinking spinners, and enhanced prompt-toolkit input. Covers DISP-01 through DISP-04. Slash command logic and runtime model switching are Phase 3 — this phase handles only the visual/input layer.

</domain>

<decisions>
## Implementation Decisions

### Panel styling
- Vibrant, high-contrast color scheme — each panel type should visually pop and be immediately distinguishable
- Full box borders with labeled titles per panel type (e.g., "🧠 Thinking", "🛠️ Tool Call")
- 4 distinct panel types: User prompt, Model response, Tool call (command), Tool output
- Claude picks specific color assignments — ensure contrast works across common dark terminal backgrounds

### Streaming behavior
- Token-by-token streaming for model responses — each token rendered as the API yields it
- Live stdout/stderr streaming for tool execution — output appears line by line inside the tool output panel as the command runs
- Direct replace from spinner to response — spinner disappears, response text starts immediately, no transition effect

### Thinking spinner
- Claude's discretion on spinner style — should fit the vibrant panel aesthetic
- Spinner visible during model inference, disappears when first token arrives

### Input experience
- Simple symbol prompt (e.g., "❯" or "→") — minimal, one character
- Multi-line input with Shift+Enter for new lines, Enter to submit
- Dropdown menu for slash command tab completion — shows matching commands with descriptions (like fish shell)
- Command history persists across sessions — saved to disk (e.g., ~/.coding-agent/history)

### Layout & density
- Comfortable spacing — moderate padding inside panels, balanced spacing between them
- Full terminal width — panels stretch to fill available width
- Show all tool output as-is — Phase 1 truncation at ~10K chars handles length upstream
- Render markdown in model response panels — use Rich's markdown rendering with syntax-highlighted code blocks

### Claude's Discretion
- Specific color palette assignments for each panel type
- Spinner animation style and label
- Exact padding/margin values within "comfortable" range
- Prompt symbol choice
- Markdown rendering configuration details

</decisions>

<specifics>
## Specific Ideas

- Panel labels should include emoji icons (e.g., "🧠 Thinking", "🛠️ Tool Call") for quick visual scanning
- Tab completion should feel like fish shell — dropdown with descriptions, not bare completions
- Streaming should feel alive — token-by-token like ChatGPT or Claude.ai

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-terminal-ui*
*Context gathered: 2026-02-26*
