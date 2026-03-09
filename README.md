# Codagent

Terminal-based AI coding agent that translates natural language into shell commands.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-green)

Connect an LLM to your terminal through a single `shell` tool. The agent iteratively executes commands until your task is complete — with a Rich terminal UI featuring streaming output, color-coded panels, and a thinking spinner. Safety guardrails include approval mode, dangerous command detection, and configurable timeouts.

## Quick Start

```bash
# Clone & install
git clone https://github.com/kshitij3027/codagent.git
cd codagent
pip install -e .

# Configure
cp .env.example .env
# Edit .env — add at least one API key

# Run
codagent
```

## Configuration

Environment variables (set in `.env`):

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `OPENROUTER_API_KEY` | OpenRouter API key | — |
| `DEFAULT_MODEL` | Model to use (`gpt5`, `claude`, `groq`) | `gpt5` |
| `DEFAULT_MODE` | `approval` or `yolo` | `approval` |
| `COMMAND_TIMEOUT` | Shell command timeout in seconds (0 = none) | `120` |
| `OPENROUTER_MODEL` | Override the OpenRouter model string | `x-ai/grok-code-fast-1` |

At least one API key is required.

## Supported Models

| Name | Provider | Model String |
|---|---|---|
| `gpt5` | OpenAI | `gpt-5` |
| `claude` | Anthropic | `claude-4.5-sonnet` |
| `groq` | OpenRouter | `x-ai/grok-code-fast-1` |

The OpenRouter model string can change without notice — use `OPENROUTER_MODEL` to override it.

## Safety & Execution Modes

**Approval mode** (default) — every command requires user confirmation before execution.

**Yolo mode** — commands auto-execute, except dangerous ones which always require approval.

Dangerous patterns that always require approval:

- `rm -rf /`, `rm -rf ~`, `rm -rf *`
- `DROP TABLE`, `DROP DATABASE`, `DELETE FROM`
- `git push --force`, `git push -f`
- `mkfs.*`, `dd if=`
- Writing to `/dev/sd*`
- Fork bombs

Output is truncated at ~10K characters to prevent context overflow.

## Docker

```bash
docker build -t codagent .
docker run -it -e OPENAI_API_KEY=sk-... codagent
```

Uses [tini](https://github.com/krallin/tini) as PID 1 for proper signal forwarding — Ctrl-C works correctly.

## Architecture

- **Agent** — Pydantic AI with ReAct loop and streaming via `agent.iter()`
- **Tool** — Single async `shell` tool with approval gate and streaming output
- **Display** — Rich panels, spinner, real-time streaming (stderr bypass for `patch_stdout`)
- **Input** — prompt-toolkit with history, auto-suggest, and slash command completion
- **Signals** — Two-tier Ctrl-C: cancel running agent, then exit at idle

## Project Structure

```
src/codagent/
├── main.py          # REPL entry point
├── agent.py         # Agent factory & streaming execution
├── config.py        # Settings from .env
├── display.py       # Rich display layer
├── input.py         # prompt-toolkit input
├── models.py        # Model provider registry
├── conversation.py  # Multi-turn history
├── signals.py       # Ctrl-C handling
└── tools/
    └── shell.py     # Shell execution + approval gate
```

## Tech Stack

- [Pydantic AI](https://ai.pydantic.dev/) — agent framework
- [Rich](https://rich.readthedocs.io/) — terminal UI
- [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/) — input handling
- [python-dotenv](https://pypi.org/project/python-dotenv/) — configuration

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Submit prompt |
| `Esc` + `Enter` | Newline (multi-line input) |
| `Ctrl-C` | Cancel running agent / exit at idle |
| `Up` / `Down` | Navigate input history |
| `Tab` | Slash command completion |
