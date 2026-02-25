---
phase: 01-core-agent-loop
plan: 03
subsystem: agent-core
tags: [pydantic-ai, repl, conversation-history, signal-handling, system-prompt, asyncio]

# Dependency graph
requires:
  - phase: 01-core-agent-loop/01
    provides: "Settings singleton with load_settings/get_settings, model registry with get_default_model"
  - phase: 01-core-agent-loop/02
    provides: "shell_tool function ready for @agent.tool_plain registration"
provides:
  - "ConversationHistory accumulator for multi-turn message persistence"
  - "Agent factory (create_agent) with system prompt and shell tool registration"
  - "run_agent_turn coroutine for single prompt-response cycle"
  - "Two-tier SIGINT handler: cancel agent run or exit program"
  - "Main REPL loop with startup banner, non-blocking input, graceful error handling"
  - "codagent console_scripts entry point"
affects: [02-terminal-ui, 03-slash-commands]

# Tech tracking
tech-stack:
  added: []
  patterns: [agent-factory-with-tool-registration, conversation-history-accumulator, two-tier-sigint, non-blocking-repl-input]

key-files:
  created:
    - src/codagent/conversation.py
    - src/codagent/agent.py
    - src/codagent/signals.py
    - src/codagent/main.py
  modified: []

key-decisions:
  - "Used agent.run() (not agent.iter()) for Phase 1 simplicity -- approval gate is inside tool, no node-level visibility needed yet"
  - "Shell tool registered via @agent.tool_plain wrapper inside create_agent(), delegating to shell_tool from tools module"
  - "Non-blocking input via loop.run_in_executor(None, input) as Phase 1 workaround for prompt-toolkit"

patterns-established:
  - "Agent factory: create_agent(model_string) returns configured Agent with tools registered"
  - "Conversation history: pass history.get() to message_history, update with result.all_messages()"
  - "Signal state: set agent_task before await, clear in finally block"
  - "REPL error handling: CancelledError -> [interrupted], Exception -> [error], never crash the loop"

requirements-completed: [CORE-01, CORE-02, CORE-03, SGNL-01, SGNL-02]

# Metrics
duration: 3min
completed: 2026-02-25
---

# Phase 1 Plan 03: Agent Core Integration Summary

**Pydantic AI agent with system prompt, shell tool, multi-turn conversation history, two-tier Ctrl-C handling, and interactive REPL with non-blocking input**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-25T08:33:27Z
- **Completed:** 2026-02-25T08:36:43Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Complete working REPL: user prompt -> agent reasoning -> shell tool calls -> response -> prompt
- System prompt enforces concise senior-dev-pairing behavior with 3-retry failure handling
- Conversation history maintained across turns via ConversationHistory wrapper (None for first turn, list thereafter)
- Two-tier Ctrl-C: cancel running agent task (SGNL-01) or exit at idle prompt (SGNL-02)
- Graceful error handling: model/network errors displayed without crashing the loop

## Task Commits

Each task was committed atomically:

1. **Task 1: Create conversation history manager, agent factory with system prompt, and signal handler** - `3a03747` (feat)
2. **Task 2: Create main REPL loop with startup, shutdown, and entry point** - `feac832` (feat)

## Files Created/Modified
- `src/codagent/conversation.py` - ConversationHistory class with get/update/clear/turn_count (54 lines)
- `src/codagent/agent.py` - create_agent() factory and run_agent_turn() coroutine with system prompt (100 lines)
- `src/codagent/signals.py` - SignalState class and setup_signal_handler() for two-tier Ctrl-C (49 lines)
- `src/codagent/main.py` - async_main() REPL loop, startup banner, main() entry point (117 lines)

## Decisions Made
- Used `agent.run()` instead of `agent.iter()` for Phase 1 -- the approval gate lives inside the tool function, so node-level visibility adds no value until Phase 2 Rich UI needs to render intermediate states
- Registered shell tool via `@agent.tool_plain` wrapper that delegates to `shell_tool()` from the tools module -- keeps tool docstring (what the model sees) cleanly defined in agent.py
- Input via `loop.run_in_executor(None, input, ">>> ")` -- Phase 1 workaround for non-blocking input; Phase 2 replaces with prompt-toolkit `prompt_async()`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pydantic AI Agent constructor validates the model provider at creation time, requiring an API key even for unit tests. Docker verification tests needed a dummy `OPENAI_API_KEY` env var to create agent instances without making actual API calls.

## User Setup Required
None - no external service configuration required. Users need a valid API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY) to actually use the agent.

## Next Phase Readiness
- Phase 1 is complete: all 3 plans delivered a working terminal coding agent
- The `codagent` command starts a functional REPL that accepts natural language, calls shell commands, and maintains conversation
- Phase 2 (Terminal UI) can enhance the REPL with Rich rendering, prompt-toolkit input, and streaming output
- Phase 3 (Slash Commands) can add /mode, /model, /new commands to the REPL loop

## Self-Check: PASSED

- All 4 created files verified on disk
- Both task commits (3a03747, feac832) verified in git log
- Docker verification passes all tests
- Line counts: conversation.py 54 (min 20), agent.py 100 (min 40), signals.py 49 (min 20), main.py 117 (min 50)

---
*Phase: 01-core-agent-loop*
*Completed: 2026-02-25*
