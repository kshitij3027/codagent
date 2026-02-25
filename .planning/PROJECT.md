# Coding Agent

## What This Is

A terminal-based AI coding agent that connects language models to the file system via a single `shell` tool. The user prompts the agent, and it iteratively calls shell commands to read, write, and manipulate code until the task is complete. Built with Pydantic AI for the agent loop, Rich for a polished terminal UI, and Prompt Toolkit for user input.

## Core Value

The agent reliably translates natural language coding requests into shell commands, executes them, and iterates until the task is done — with a clear, elegant terminal interface that shows exactly what's happening at every step.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Agent loop using Pydantic AI that receives user prompts and calls tools iteratively until complete
- [ ] Multi-model support: GPT-5 (OpenAI), Claude 4.5 (Anthropic), Groq Code/CodeFast (OpenRouter)
- [ ] Single `shell` tool that takes a command string, executes it, and returns stdout + stderr
- [ ] Shell output truncated at a reasonable limit to avoid flooding model context
- [ ] System prompt that instructs the model it is a coding agent, should think through problems, and use the shell tool
- [ ] Two execution modes: approval (user confirms each tool call) and yolo (auto-run)
- [ ] Default startup: approval mode with GPT-5
- [ ] Rich-based terminal UI with color-coded output, boxed interactions, and a thinking spinner
- [ ] Real-time streaming display of tool calls (inputs and outputs shown as they happen)
- [ ] Prompt Toolkit input with history and completion
- [ ] Slash commands: `/model` (switch model), `/approval` (toggle mode), `/new` (reset conversation)
- [ ] Conversation maintained in memory across turns until `/new` or program exit
- [ ] Ctrl-C during agent work aborts and returns to prompt; Ctrl-C at idle exits program
- [ ] Environment variables loaded from `.env` file on startup (API keys, config)

### Out of Scope

- Persistent conversation history across sessions — memory only for v1
- File-specific tools (read, write, edit) — the shell tool handles everything
- Web browsing or search capabilities — shell commands only
- Plugin or extension system — single-tool architecture
- Multi-agent orchestration — single agent loop

## Context

- Pydantic AI provides the agent framework with tool registration and model abstraction
- Three model providers require different API configurations: OpenAI direct, Anthropic direct, OpenRouter for Groq
- The existing repo has placeholder files (requirements.txt, README, .gitignore) — effectively greenfield
- Environment variables in `.env` configure API keys and model-specific settings (see `example.env`)

## Constraints

- **Framework**: Pydantic AI for agent loop — non-negotiable
- **UI**: Rich for output display, Prompt Toolkit for input — non-negotiable
- **Language**: Python
- **Tool**: Single `shell` tool only — all file system interaction through shell commands
- **Models**: Must support all three providers (OpenAI, Anthropic, OpenRouter)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single shell tool instead of multiple file tools | Simpler architecture, model decides how to interact with filesystem | — Pending |
| Pydantic AI over LangChain/other frameworks | User preference, cleaner abstractions | — Pending |
| Truncate long shell output | Prevents context window overflow and token waste | — Pending |
| Approval mode as default | Safe default for new users, prevents unintended command execution | — Pending |

---
*Last updated: 2026-02-24 after initialization*
