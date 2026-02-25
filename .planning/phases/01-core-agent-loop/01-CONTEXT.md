# Phase 1: Core Agent Loop - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

A working terminal coding agent that receives natural language prompts, executes shell commands via a single `shell` tool, and iterates until the task is complete. Supports three model providers (GPT-5, Claude 4.5, Groq Code), two execution modes (approval/yolo), conversation history in memory, signal handling (Ctrl-C), and .env configuration. All output is plain text — Rich UI comes in Phase 2. Slash commands come in Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Agent behavior
- Concise responses between tool calls — brief explanations, not verbose narration. Like a senior dev pairing.
- Ask for clarification on ambiguous requests before acting (e.g., "fix the tests" → ask which tests or what's failing)
- On command failure (non-zero exit), automatically analyze the error and retry with a different approach — up to a reasonable limit before giving up
- After completing a multi-step task, provide a brief summary of what was done (e.g., "Done — created 3 files and ran tests (all passed).")

### Approval flow
- Display the command AND a one-line reason before asking for approval (e.g., "Checking project structure: `ls -la src/`")
- Simple y/n prompt — pressing Enter (empty input) defaults to 'yes'
- On rejection (user says no): agent stops the current run and asks the user what they'd like to do instead
- Default mode on startup: approval (user must confirm each command)

### Yolo mode safety
- Maintain a blocklist of dangerous command patterns that still require approval even in yolo mode (e.g., `rm -rf /`, `DROP TABLE`, force pushes)
- All other commands execute automatically without pausing

### Claude's Discretion
- Whether to explain the plan before executing (plan-first vs just-go)
- Whether to display elapsed time for commands
- Exact system prompt wording and personality tone
- Error retry limit and backoff strategy
- Truncation marker format for shell output exceeding ~10K chars
- Startup banner content and format

</decisions>

<specifics>
## Specific Ideas

- Agent should feel like a senior dev pairing — concise, competent, not chatty
- Approval prompt should be fast to use — Enter-to-approve minimizes friction when user trusts the command
- "Command + reason" format keeps the user informed without being verbose

</specifics>

<deferred>
## Deferred Ideas

- Dedicated file read/write/edit tools — currently shell handles all filesystem interaction; consider as v2 enhancement if shell-only proves limiting

</deferred>

---

*Phase: 01-core-agent-loop*
*Context gathered: 2026-02-24*
*Updated: 2026-02-24 — added deferred file tools idea*
