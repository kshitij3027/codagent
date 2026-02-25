# Codebase Concerns

**Analysis Date:** 2026-02-24

## Project Status

**Current State:** Scaffold phase - no implementation code present. Project structure exists (`.gitignore`, `requirements.txt`) but core functionality not yet implemented.

**Key File:** `success-criteria.md` - Contains complete specification but no code yet exists.

## Missing Critical Implementation

**Core Agent Loop:**
- Issue: No `src/` directory or main agent implementation exists
- Files: Missing - needs creation
- Impact: Cannot run agent at all until this is implemented
- Fix approach: Implement Pydantic AI agent loop with proper state management, tool execution pipeline, and conversation history tracking

**Model Integration:**
- Issue: Three model providers (OpenAI GPT-5, Claude 4.5, OpenRouter Groq) specified but no abstraction layer exists
- Files: Missing - needs model factory/adapter pattern
- Impact: Model switching will be error-prone without abstraction; tight coupling risk
- Fix approach: Create model provider interface (`src/models/base.py`) with concrete implementations for each provider. Use environment-based factory pattern to instantiate correct model.

**Tool System:**
- Issue: Single `shell` tool specified with complex requirements (shell piping, redirection, stdout/stderr capture) but no tool execution framework defined
- Files: Missing - needs tool framework
- Impact: Unsafe shell execution without proper validation/sandboxing; output handling complexity
- Fix approach: Build tool abstraction in `src/tools/base.py` and `src/tools/shell.py`. Add input validation, timeout handling, and proper stdout/stderr separation.

## Security Considerations

**Arbitrary Shell Execution:**
- Risk: The `shell` tool accepts arbitrary shell commands with piping and redirection. No mention of validation, sandboxing, or security restrictions.
- Impact: User (or compromised agent) could delete files, access credentials, exfiltrate data, or perform privilege escalation
- Current mitigation: Project specifies "approval mode" which requires user confirmation before execution
- Recommendations:
  1. Implement command validation/filtering - whitelist safe operations
  2. Use shell sandboxing (subprocess with restricted environment)
  3. Add timeout enforcement to prevent hanging processes
  4. Implement audit logging of all executed commands
  5. Consider restricting to safe paths only (not root, /etc, /sys, etc.)
  6. Add rate limiting to prevent command spam

**Environment Variable Exposure:**
- Risk: `.env` file will contain API keys for OpenAI, Claude, OpenRouter, and potentially others. Easy to accidentally leak in logs or error messages.
- Files: `.env` (not yet created)
- Impact: Credential compromise, unauthorized API usage, costs to user
- Current mitigation: `.env` in `.gitignore`
- Recommendations:
  1. Never log full API keys - hash or truncate
  2. Implement secret detection in error messages
  3. Use environment variable masking in debug output
  4. Consider using python-dotenv with explicit required variables check
  5. Add startup validation that all required env vars are present

**Model Prompt Injection:**
- Risk: Agent accepts user prompts and passes to language models without sanitization. No mention of prompt validation or injection prevention.
- Impact: Malicious prompts could override system instructions, reveal system state, or manipulate agent behavior
- Recommendations:
  1. Implement input validation on user prompts
  2. Use system prompt hardening techniques
  3. Consider filtering for suspicious patterns (e.g., attempts to override instructions)
  4. Log all user prompts for security audit

## Architecture Concerns

**Conversation State Management:**
- Issue: Requirements specify "maintain conversation, accumulating messages" but no persistence or session management approach defined
- Impact: Conversations lost on crash; memory grows unbounded; no session history
- Fix approach: Implement message buffer with optional persistence (`src/conversation/history.py`). Consider max token limits to prevent unbounded growth. Add session save/load functionality.

**Control-C Handling:**
- Issue: Requires abort mid-execution with state preservation, but no signal handling framework exists
- Impact: Incomplete tool execution could leave system in bad state; data loss possible
- Fix approach: Implement signal handler in main loop, add graceful shutdown with state checkpoint

**Multi-Model Switching:**
- Issue: Runtime model selection via `/model` command, but no mechanism to switch mid-conversation or handle model differences
- Impact: Switching models mid-conversation could break context (different tokenization, capabilities, API contracts)
- Fix approach: Add model switching validation - only allow at conversation boundaries. Document differences between models.

**UI/Display Requirements:**
- Issue: Rich library for "elegant" terminal output with colored boxes, spinners, and animations - but no UI framework designed
- Files: Missing - needs `src/ui/` module
- Impact: Feature bloat risk; UI bugs could obstruct functionality; animation adds latency
- Fix approach: Build abstraction layer (`src/ui/base.py`) with simple implementations first, then enhance. Use threading for animations to avoid blocking.

## Testing & Verification Gaps

**Untested Areas:**
- What's not tested: Entire codebase not yet written
- Files: No test files exist (`tests/`, `test_*.py`)
- Risk: Cannot catch regressions, edge cases, or integration issues
- Priority: HIGH - must add tests during implementation

**Specific Test Coverage Gaps (once implemented):**
1. Model provider switching and error handling
2. Shell command execution with piping/redirection
3. Conversation history limits and overflow
4. Signal handling (Ctrl-C) at various points
5. Approval mode vs YOLO mode toggle
6. `/model`, `/approval`, `/new` command parsing
7. Environment variable loading and validation
8. Error cases: network failures, API rate limits, model errors

## Performance Bottlenecks

**Model Response Latency:**
- Problem: Agent loops on model responses. Three different APIs (OpenAI, Claude, Groq) have different latencies (100ms-5s+)
- Impact: User waits during thinking; no progress indication specified beyond spinner
- Improvement path: Implement streaming responses to show partial output. Add timing telemetry to identify slowest providers.

**Shell Output Size:**
- Problem: Capturing full stdout/stderr without size limits could consume memory for large outputs
- Impact: `ls -R /` or similar could crash agent
- Improvement path: Add output size limit with warning. Implement output streaming for large outputs.

**Conversation History Growth:**
- Problem: Accumulating all messages without cleanup
- Impact: Over time, token count grows, API calls get slower, memory usage increases
- Improvement path: Implement message summarization or truncation after N messages. Consider sliding window approach.

## Fragile Areas & Safe Modification

**Tool Execution Pipeline:**
- Files: `src/tools/` (to be created)
- Why fragile: Shell commands are inherently unsafe. Any bug in execution framework could enable attacks.
- Safe modification:
  1. All changes must go through code review
  2. Add tests for sandbox validation
  3. Keep tool definitions separate from execution logic
  4. Never execute untrusted command strings without validation

**Model Provider Abstraction:**
- Files: `src/models/` (to be created)
- Why fragile: Each provider has different API contracts, error codes, authentication. Bugs here cascade to entire agent.
- Safe modification:
  1. Each provider implementation should be isolated
  2. Add comprehensive error handling per provider
  3. Test against real APIs (not mocks) to catch integration issues
  4. Document provider-specific quirks

**Conversation State:**
- Files: `src/conversation/` (to be created)
- Why fragile: Message history is critical - corruption here breaks agent. State mutations could be non-deterministic.
- Safe modification:
  1. Use immutable data structures where possible
  2. Add validation on state transitions
  3. Implement message schema validation
  4. Log state changes for debugging

## Known Risks & Dependencies

**Pydantic AI Maturity:**
- Risk: Project relies on Pydantic AI which is relatively new (early 2024+). API stability not guaranteed in early versions.
- Impact: Updates could break code; tool definitions or model integration could change
- Migration plan: Pin Pydantic AI version in requirements.txt. Monitor releases for breaking changes. Have upgrade test plan.

**Model Provider Stability:**
- Risk: Three external APIs (OpenAI, OpenRouter, Anthropic) with different reliability levels
- Impact: Outages affect agent; API deprecations require code changes
- Mitigation: Implement retry logic with exponential backoff. Add fallback to secondary provider. Cache model responses where safe.

**Rich Library Animation Performance:**
- Risk: Spinner animations in terminal could be resource-intensive or cause flicker
- Impact: Poor UX on slow terminals; latency if not threaded
- Recommendations: Use threading for animations. Make animations optional. Test on slow terminals.

**Python Version Requirements:**
- Risk: Not specified in `requirements.txt`. Pydantic AI may have minimum version (3.8+).
- Impact: Users with old Python could have issues
- Fix approach: Add `python_requires = ">=3.10"` to project metadata. Document in README.

## Missing Features (Future Debt)

**Logging & Debugging:**
- What's missing: No logging framework specified. No debug mode. No error reporting.
- Files: Missing - needs `src/logging/` configuration
- Blocks: Cannot diagnose issues in production; debugging difficult

**Configuration Management:**
- What's missing: Command-line arguments not specified. Config file format undefined.
- Blocks: Cannot adjust behavior without code changes

**Persistence & Session Recovery:**
- What's missing: No persistence mechanism for conversations or agent state
- Blocks: Cannot resume sessions after crash

**Metrics & Observability:**
- What's missing: No telemetry, timing data, or usage metrics
- Blocks: Cannot optimize performance or understand usage patterns

## Critical Path Items (Do First)

**Phase 1 - Core Infrastructure (BLOCKING all other work):**
1. Set up project structure (`src/`, `tests/`, `config/`)
2. Implement Pydantic AI agent loop with tool abstraction
3. Implement shell tool with security validation
4. Add basic conversation history
5. Add approval mode toggle

**Phase 2 - Model Support:**
1. Implement model provider abstraction
2. Add OpenAI provider
3. Add Claude provider
4. Add OpenRouter provider
5. Implement model switching via `/model` command

**Phase 3 - UX & Commands:**
1. Implement Rich UI framework
2. Add `/approval`, `/model`, `/new` command handlers
3. Implement spinner/thinking animation
4. Add color-coded output

**Phase 4 - Safety & Hardening:**
1. Add comprehensive input validation
2. Implement command execution sandboxing
3. Add audit logging
4. Security review of all tool execution

---

*Concerns audit: 2026-02-24*
