# Feature Research

**Domain:** Terminal-based AI coding agents
**Researched:** 2026-02-24
**Confidence:** HIGH (multiple current sources, verified across competitors)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or unsafe to use.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Natural language task input | Core premise — the whole value is "tell it what to do in English" | LOW | Must handle multi-turn conversation, not just one-shot |
| Shell/command execution | Without it, the agent cannot act on the filesystem | LOW | Must capture stdout + stderr and return to model |
| Multi-file read + write | Users expect agents to handle tasks spanning multiple files | MEDIUM | Pure shell covers this; dedicated read/write tools are optional |
| Multi-turn conversation in session | Users expect the agent to remember what was discussed in the same session | LOW | In-memory conversation history; session reset on /new or exit |
| Approval mode (confirm before executing) | Safety default — users do not trust auto-run for unfamiliar tasks | LOW | Toggle between confirm-each-action and auto-run; all major tools have this |
| Auto-run / yolo mode | Power users and CI workflows require full autonomy without prompts | LOW | Must be explicit opt-in, not default |
| Streaming output display | Users expect to see the agent "thinking" and acting in real time, not staring at a blank screen | MEDIUM | Spinner during model inference + stream tool call inputs/outputs as they happen |
| Color-coded terminal UI | Plain text output is hard to parse; users expect visual differentiation of agent vs user vs tool output | MEDIUM | Use of Rich or equivalent is now expected; monochrome CLIs feel dated |
| Model configuration via environment variables | All tools load API keys from .env or shell env; hardcoding keys is a dealbreaker | LOW | Standard pattern: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc. loaded at startup |
| Graceful interrupt (Ctrl-C) | Users expect to be able to abort a runaway agent without killing the process entirely | LOW | Ctrl-C during agent loop = abort + return to prompt; Ctrl-C at idle = exit |
| Context reset command | Long sessions degrade model quality; users need a way to start fresh | LOW | /new or /clear slash command; resets conversation, not config |
| Shell output truncation | Without truncation, large outputs (build logs, ls -la on big dirs) overflow context and waste tokens | LOW | Truncate at reasonable token limit (10k tokens / ~40k chars); show head + tail with truncation notice |
| System prompt establishing agent role | Without a role prompt, the model does not behave as a coding agent consistently | LOW | Sets up "you are a coding agent, use shell tools to complete tasks" behavior |

**Confidence: HIGH** — All 13 table stakes features verified across Claude Code, Aider, Codex CLI, Gemini CLI, OpenCode, and Cline in 2025-2026 sources.

---

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valued — this is where products compete.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Multi-model support with runtime switching | Developers increasingly want to choose and switch models mid-workflow based on cost/quality tradeoffs; lock-in is a friction point | MEDIUM | Claude Code is locked to Anthropic; Aider, OpenCode, Kilo (500+ models) compete here; our multi-provider support (OpenAI, Anthropic, OpenRouter) is a genuine differentiator |
| Polished Rich-based UI with boxed interactions | Most terminal tools are either plain text or require full-screen TUI takeover; a clean "boxed" layout that shows exactly what's happening at each step without overwhelming is underused | MEDIUM | Claude Code is praised for UX polish; other tools are functional but sparse; Rich components (panels, spinners, syntax-highlighted code) are differentiating when combined well |
| Input history and completion (Prompt Toolkit) | Terminal tools that lack input history feel like a regression from the shell itself; tab completion of slash commands adds discoverability | LOW | Standard readline behavior is table stakes in shells; in AI agent CLIs it's still uncommon enough to be differentiating |
| Thoughtful approval UX at decision points | Claude Code is praised for "plan first, then act" — showing what it intends to do and allowing discussion before execution; this is qualitatively different from just showing a confirm [y/n] prompt | MEDIUM | Binary approve/reject (table stakes). Showing full planned action set and enabling discussion is differentiating |
| Slash command palette | Discoverable commands (/model, /approval, /new) lower onboarding friction and give power users efficient control; most tools bury config in flags | LOW | Small to build, high perceived quality impact; directly addresses "how do I do X?" moment |
| Clear display of tool call inputs and outputs | Users report frustration with "black box" agents; showing exactly what command was run and what came back builds trust and makes debugging easy | LOW | Claude Code is praised for this; OpenCode has real-time tool display; most tools hide internals behind spinners |
| Stable multi-provider model abstraction | Supporting 3+ API providers (OpenAI direct, Anthropic direct, OpenRouter for Groq) with a unified interface is hard to do well; most tools pick one provider | HIGH | Pydantic AI handles abstraction; main complexity is auth differences and model-specific parameter handling (temperature, max_tokens, etc.) |
| Output verbosity control | Developers in CI or scripting contexts want minimal output; interactive users want rich feedback; a --quiet mode or equivalent serves both | LOW | Aider, OpenCode have this; mostly missing from newer tools |

**Confidence: MEDIUM-HIGH** — Derived from competitor analysis and developer survey data (Stack Overflow 2025, Faros AI developer reviews 2026, multiple hands-on comparisons).

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create scope creep, architectural complexity, or user distrust — deliberately NOT building these in v1.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Persistent conversation history across sessions | Developers ask for this because they want the agent to "remember" past decisions | Context from old sessions is often stale, misleading, or contradictory; loading stale context causes agents to make worse decisions; adds storage complexity for marginal benefit | Let users write important context to CLAUDE.md / project README; start fresh each session deliberately |
| Dedicated file-read/file-write/file-edit tools (instead of shell) | Seems safer and more structured than raw shell commands | Multiplies tool surface area with no functional gain when shell handles everything; forces model to choose between tool types adding decision overhead; limits flexibility (agent can't do `sed`, `grep`, `diff` via file tools) | Single `shell` tool that handles all filesystem interaction; simpler, more powerful, fewer failure modes |
| Web browsing / search capabilities | Developers want agents that can look up docs or APIs | Dramatically expands attack surface (SSRF, prompt injection via malicious web content); complex to implement safely; shell tool can already do `curl` for specific targeted fetches | Out of scope in v1; if needed, user can pipe curl output themselves |
| Plugin / extension system | Developers request customizability | High architectural complexity for v1; forces premature API stabilization; most users do not actually use plugin systems in practice | Defer; v1 serves 90% of use cases without it |
| Multi-agent orchestration (spawning sub-agents) | Claude Code advertises this as a differentiator | Extremely complex to implement correctly; exponential failure modes; token costs multiply fast; coordination logic is a research problem | Single agent loop with good tool use handles most tasks; multi-agent is a v2+ consideration |
| Full-screen TUI takeover | Some tools (Codex CLI 2026) do full-screen interactive terminal; looks impressive | Breaks normal terminal composability; can't easily pipe output, run in scripts, or integrate with other tools; alienates power users who live in tmux/screen | Rich-based inline output keeps composability while still looking polished |
| Auto-commit to git without explicit user action | Aider auto-commits every change; seems convenient | Users lose trust when agent touches version control without permission; recovery from bad auto-commits is painful; violates principle of least surprise | Show git diff after changes; let user decide when to commit; offer /commit slash command as opt-in |
| Real-time pair programming / collaboration | Sounds like a killer feature | Requires WebSocket infrastructure, session sharing, auth, conflict resolution — product-within-product complexity | Not the core use case; single-developer terminal agent is the validated use case |

**Confidence: MEDIUM** — Anti-features derived from developer complaints (Faros AI 2026 reviews, Stack Overflow 2025 survey, research paper "Professional Software Developers Don't Vibe, They Control"), competitor design choices and their tradeoffs.

---

## Feature Dependencies

```
[Shell execution]
    └──requires──> [Streaming output display]
                       └──requires──> [Spinner / real-time feedback]

[Multi-turn conversation]
    └──requires──> [Context reset command (/new)]

[Multi-model support]
    └──requires──> [Model configuration via env vars]
                       └──requires──> [.env file loading at startup]

[Approval mode]
    └──enhances──> [Clear display of tool call inputs/outputs]
                       (approval decisions are meaningless without seeing what you're approving)

[Slash commands (/model)]
    └──requires──> [Multi-model support]

[Slash commands (/approval)]
    └──requires──> [Approval mode toggle]

[Input history + completion]
    └──enhances──> [Slash command palette]
                       (tab-complete slash commands for discoverability)

[Shell output truncation]
    └──requires──> [Shell execution]
    └──prevents──> [Context window overflow]

[Multi-model support]
    ──conflicts──> [Full-screen TUI takeover]
                       (full TUI makes runtime model switching UX awkward)
```

### Dependency Notes

- **Streaming requires shell execution first**: You cannot stream tool outputs until the tool execution layer is stable and reliable.
- **Approval display requires visibility into tool calls**: The quality of the approval UX is directly gated on how much tool call detail is surfaced to the user. Build the tool call display layer before polishing the approval UX.
- **Multi-model is gated on env/config layer**: All three provider configs (OpenAI, Anthropic, OpenRouter) need to load correctly before model switching is testable.
- **Slash commands should come after core loop is stable**: /model and /approval are convenience wrappers; building them before the agent loop is solid creates churn.
- **Context reset (/new) must clear conversation but preserve config**: Users expect /new to reset the chat, not unload their API keys or model selection.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Agent loop (Pydantic AI) that receives user prompt and calls shell tool iteratively until complete — core premise
- [ ] Single `shell` tool: takes command string, executes, returns stdout + stderr — foundation of all filesystem interaction
- [ ] Shell output truncation at ~10k token limit — prevents context overflow on first real use
- [ ] System prompt establishing coding agent role — required for consistent behavior
- [ ] Multi-turn conversation maintained in memory for session duration — required for non-trivial tasks
- [ ] Approval mode (confirm each tool call) as default — safety for new users
- [ ] Auto-run / yolo mode as explicit opt-in — required for power users and CI
- [ ] Rich-based terminal UI: color-coded panels, spinner during inference, streamed tool call display — UX polish that separates this from a toy script
- [ ] Prompt Toolkit input with history — table stakes for interactive terminal tool
- [ ] Slash commands: /model, /approval, /new — discoverability and efficiency
- [ ] Multi-model support: GPT-5 (OpenAI), Claude (Anthropic), Groq via OpenRouter — differentiating and part of PROJECT.md requirements
- [ ] .env file loading at startup for API keys — standard expected pattern
- [ ] Ctrl-C abort behavior: abort loop during agent work, exit at idle prompt — correct terminal citizenship

### Add After Validation (v1.x)

Features to add once core agent loop is validated and in regular use.

- [ ] Context compaction / summarization when conversation grows long — add when users report context degradation on long sessions
- [ ] /commit slash command for AI-generated commit messages — add when users ask for git workflow integration
- [ ] Output verbosity flag (--quiet) — add when users try to script or pipe the agent
- [ ] Per-project configuration file (e.g., .agent/config.toml) — add when users want different model defaults per project

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] MCP (Model Context Protocol) server integration — powerful but complex; add when users hit limitations of shell-only approach
- [ ] Persistent cross-session memory — add only if validated user need; privacy and staleness risks are real
- [ ] Multi-agent orchestration (spawn sub-agents for parallel work) — extreme complexity; validated need only
- [ ] LSP integration for code intelligence — adds significant setup complexity; shell-based linting covers most needs
- [ ] Browser / web automation — scope creep risk; security surface area concerns

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Agent loop (Pydantic AI) | HIGH | MEDIUM | P1 |
| Shell tool (execute + return output) | HIGH | LOW | P1 |
| Shell output truncation | HIGH | LOW | P1 |
| Approval / yolo modes | HIGH | LOW | P1 |
| Multi-model support (3 providers) | HIGH | MEDIUM | P1 |
| Rich terminal UI (streaming, spinner, panels) | HIGH | MEDIUM | P1 |
| Multi-turn conversation in-session | HIGH | LOW | P1 |
| Slash commands (/model, /approval, /new) | MEDIUM | LOW | P1 |
| Prompt Toolkit input (history, completion) | MEDIUM | LOW | P1 |
| .env file loading at startup | HIGH | LOW | P1 |
| Ctrl-C abort behavior | MEDIUM | LOW | P1 |
| Context compaction / summarization | MEDIUM | MEDIUM | P2 |
| /commit slash command | MEDIUM | LOW | P2 |
| --quiet / verbosity control | LOW | LOW | P2 |
| Per-project config file | MEDIUM | MEDIUM | P2 |
| MCP server integration | MEDIUM | HIGH | P3 |
| Persistent cross-session memory | LOW | HIGH | P3 |
| Multi-agent orchestration | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch (v1)
- P2: Should have, add after validation (v1.x)
- P3: Nice to have, future consideration (v2+)

---

## Competitor Feature Analysis

| Feature | Claude Code | Aider | Codex CLI | Gemini CLI | OpenCode | Our Approach |
|---------|-------------|-------|-----------|------------|----------|--------------|
| Model flexibility | Anthropic-only | 100+ LLMs | OpenAI-only | Google-only | 75+ providers | 3 providers (OpenAI, Anthropic, OpenRouter/Groq) — meaningful multi-provider without Kilo-level complexity |
| Tool architecture | Multiple specialized tools | Multiple tools | Multiple tools | Multiple tools | Multiple tools | Single `shell` tool — simpler, more composable, model decides how to interact |
| Approval modes | Yes (plan + approve) | Yes (auto-commit default) | Yes (3 levels) | Yes | Yes | Yes (approval default, yolo opt-in) — safer default than Aider |
| Streaming display | Yes (polished) | Moderate | Yes | Yes | Yes | Yes — with Rich panels and spinner |
| Terminal UI quality | Excellent | Functional | Full-screen TUI | Minimal | Moderate | Target: Claude Code quality; inline (not full-screen) |
| Git integration | Deep (auto-checkpoint) | Auto-commit | Branch/PR creation | Basic | Basic | Minimal in v1 — shell handles git commands; /commit as v1.x add |
| Context reset | /clear | /clear | Built-in | /clear | Built-in | /new slash command |
| Input history | Yes | Yes | Yes | Yes | Yes | Yes (Prompt Toolkit) |
| MCP integration | Yes (praised as flawless) | No | Yes (experimental) | Yes (extensive) | Partial | Defer to v2+ |
| Session persistence | No (in-memory) | No | Optional | No | No | In-memory only (v1) — deliberate choice |
| Slash commands | Yes (/clear, /commit, etc.) | Yes | Yes | Yes | Yes | Yes (/model, /approval, /new) |
| Open source | No (proprietary) | Yes (MIT) | No | Yes (Apache 2.0) | Yes (MIT) | Yes |

---

## Sources

- [The 2026 Guide to Coding CLI Tools: 15 AI Agents Compared — Tembo](https://www.tembo.io/blog/coding-cli-tools-comparison) — Comprehensive feature matrix across 15 tools (HIGH confidence)
- [Top 5 CLI Coding Agents in 2026 — Pinggy](https://pinggy.io/blog/top_cli_based_ai_coding_agents/) — Feature summaries per tool (MEDIUM confidence)
- [Best AI Coding Agents for 2026: Real-World Developer Reviews — Faros AI](https://www.faros.ai/blog/best-ai-coding-agents-2026) — Developer perspective on what matters most (HIGH confidence)
- [Claude Code GitHub Repository — Anthropic](https://github.com/anthropics/claude-code) — Official feature list (HIGH confidence)
- [Aider — AI Pair Programming in Your Terminal](https://aider.chat/) — Official feature list including auto-commit, codebase mapping, 100+ models (HIGH confidence)
- [Codex CLI Features — OpenAI Developers](https://developers.openai.com/codex/cli/features/) — Official approval modes documentation (HIGH confidence)
- [Agentic CLI Tools Compared: Claude Code vs Cline vs Aider — AIMultiple](https://aimultiple.com/agentic-cli) — UX and workflow comparison (MEDIUM confidence)
- [I Tested the 3 Major Terminal AI Agents — DEV Community](https://dev.to/thedavestack/i-tested-the-3-major-terminal-ai-agents-and-this-is-my-winner-6oj) — Hands-on evaluation of Claude Code, OpenCode, Gemini CLI (MEDIUM confidence)
- [AI Coding: Managing Context — Pete Hodgson](https://blog.thepete.net/blog/2025/10/29/ai-coding-managing-context/) — Context management patterns (MEDIUM confidence)
- [Why You Need To Clear Your Coding Agent's Context Window — Will Ness](https://willness.dev/blog/one-session-per-task) — Session reset workflow rationale (MEDIUM confidence)
- [Cline GitHub — autonomous coding agent](https://github.com/cline/cline) — Approval-every-step philosophy, browser automation, plan+act modes (HIGH confidence)
- [AI Coding Assistants for Terminal: Claude Code, Gemini CLI & Qodo Compared — Prompt Security](https://prompt.security/blog/ai-coding-assistants-make-a-cli-comeback) — Security and safety feature comparison (MEDIUM confidence)
- [Professional Software Developers Don't Vibe, They Control — arXiv 2512.14012](https://arxiv.org/abs/2512.14012) — Research on developer control preferences vs autonomy (HIGH confidence)
- [Context Engineering for AI Agents — Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) — Shell output truncation best practices (MEDIUM confidence)
- [10 Things Developers Want from their Agentic IDEs in 2025 — RedMonk](https://redmonk.com/kholterhoff/2025/12/22/10-things-developers-want-from-their-agentic-ides-in-2025/) — Developer priority survey (HIGH confidence)

---

*Feature research for: Terminal-based AI coding agents*
*Researched: 2026-02-24*
