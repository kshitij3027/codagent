"""Agent factory with system prompt and shell tool registration.

Creates a Pydantic AI Agent configured as a terminal coding agent with a
single shell tool.  The ``run_agent_turn`` coroutine executes one
prompt-response cycle, updating conversation history along the way.
"""

from __future__ import annotations

from pydantic_ai import Agent

from codagent.conversation import ConversationHistory
from codagent.tools.shell import shell_tool


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a coding agent. You help users with programming tasks by executing \
shell commands. You have a single tool: `shell` -- use it to interact with \
the filesystem, run tests, install packages, and perform any CLI operation.

Behavior:
- Be concise. You are a senior dev pairing with the user, not a tutorial.
- If a request is ambiguous, ask for clarification before acting.
- On command failure (non-zero exit), analyze the error and try a different \
approach. Give up after 3 failed attempts and explain what went wrong.
- After completing a multi-step task, provide a brief summary of what was done.
- Think step-by-step about what commands to run, but keep explanations short.\
"""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------


def create_agent(model_string: str) -> Agent:
    """Create a Pydantic AI Agent configured as a terminal coding agent.

    The agent has:
    - A system prompt instructing concise, senior-dev-pairing behavior.
    - A ``shell`` tool (registered via ``@agent.tool_plain``) that delegates
      to the approval-gated ``shell_tool`` from ``codagent.tools.shell``.

    Args:
        model_string: Pydantic AI model identifier (e.g. ``"openai:gpt-5"``).

    Returns:
        A configured :class:`pydantic_ai.Agent` instance.
    """
    agent = Agent(
        model=model_string,
        system_prompt=SYSTEM_PROMPT,
    )

    # Register the shell tool so the model can call it.
    # The wrapper's docstring is what the model sees as the tool description.
    @agent.tool_plain
    async def shell(command: str) -> str:
        """Execute a shell command. Returns stdout, stderr, and exit code.

        Use this to interact with the filesystem, run tests, install packages,
        and perform any command-line operation needed to complete the user's task.
        """
        return await shell_tool(command)

    return agent


# ---------------------------------------------------------------------------
# Single-turn execution
# ---------------------------------------------------------------------------


async def run_agent_turn(
    agent: Agent,
    prompt: str,
    history: ConversationHistory,
) -> str:
    """Run one agent turn: send *prompt*, let the agent act, return its reply.

    Uses ``agent.run()`` (not ``agent.iter()``) for Phase 1 simplicity.
    The approval gate lives inside the shell tool function, so we don't
    need node-level visibility here.  Phase 2 can switch to ``iter()``
    when the Rich UI needs to render intermediate states.

    Args:
        agent: The configured Pydantic AI Agent.
        prompt: The user's natural-language input.
        history: Conversation history accumulator (updated in-place).

    Returns:
        The model's text response for this turn.
    """
    result = await agent.run(prompt, message_history=history.get())
    history.update(result.all_messages())
    return result.output
