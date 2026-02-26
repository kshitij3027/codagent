"""Agent factory with system prompt and shell tool registration.

Creates a Pydantic AI Agent configured as a terminal coding agent with a
single shell tool.

Provides two execution modes:
- ``run_agent_turn()``  -- Phase 1 batch mode via ``agent.run()``
- ``run_agent_turn_streaming()`` -- Phase 2 streaming via ``agent.iter()``
  with node-level display control (spinner, token streaming, tool panels).
"""

from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    TextPartDelta,
)

from codagent.conversation import ConversationHistory
from codagent.display import Display
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
- If a request is genuinely ambiguous (you cannot determine WHAT the user \
wants), ask for clarification. If the user's intent is clear but the command \
is destructive or risky, call the shell tool anyway -- it has a built-in \
approval gate that will prompt the user before executing dangerous commands.
- On command failure (non-zero exit), analyze the error and try a different \
approach. Give up after 3 failed attempts and explain what went wrong.
- When a command is rejected by the user (the tool returns a rejection \
message), acknowledge the rejection, do NOT re-suggest or re-offer the same \
command, and ask the user what they would like to do instead.
- After completing a multi-step task, provide a brief summary of what was done.
- Think step-by-step about what commands to run, but keep explanations short.
- The shell tool has a built-in safety layer: dangerous commands (rm -rf, \
DROP TABLE, force push, etc.) always show an explicit approval prompt to the \
user before executing, even in yolo mode. You do not need to act as a safety \
gate -- always call the tool when the user requests a shell operation.\
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
        This tool has a built-in approval gate: dangerous commands (rm -rf, DROP TABLE,
        force push, etc.) always require explicit user approval before executing.
        In approval mode, ALL commands require user approval before executing.
        If the user rejects a command, the tool returns a rejection message --
        respect it and do not re-offer the same command.
        """
        return await shell_tool(command)

    return agent


# ---------------------------------------------------------------------------
# Streaming turn execution (Phase 2 — agent.iter())
# ---------------------------------------------------------------------------


async def run_agent_turn_streaming(
    agent: Agent,
    prompt: str,
    history: ConversationHistory,
    display: Display,
) -> str:
    """Run one agent turn with streaming display via ``agent.iter()``.

    Iterates over the agent's execution graph node by node:

    - **ModelRequestNode**: Shows a thinking spinner, then streams tokens
      one-by-one as the API yields them. The spinner is replaced by the
      response stream on the first token.
    - **CallToolsNode**: Displays tool call commands in a panel, then shows
      tool results. (Actual line-by-line tool output streaming happens
      inside ``shell_tool`` via the Display callback set by ``set_display``.)
    - **End node**: No-op — the final result was already streamed.

    Args:
        agent: The configured Pydantic AI Agent.
        prompt: The user's natural-language input.
        history: Conversation history accumulator (updated in-place).
        display: The Rich Display instance for rendering output.

    Returns:
        The model's text response for this turn.
    """
    async with agent.iter(prompt, message_history=history.get()) as agent_run:
        async for node in agent_run:
            if Agent.is_model_request_node(node):
                # Show spinner while model is thinking
                display.show_spinner("Thinking...")
                spinner_active = True

                async with node.stream(agent_run.ctx) as request_stream:
                    async for event in request_stream:
                        if isinstance(event, PartDeltaEvent) and isinstance(
                            event.delta, TextPartDelta
                        ):
                            if spinner_active:
                                # First token: transition from spinner to response stream
                                display.hide_spinner()
                                display.start_response_stream()
                                spinner_active = False
                            display.stream_token(event.delta.content_delta)

                # If model only called tools (no text tokens emitted),
                # clean up spinner without printing empty response
                if spinner_active:
                    display.hide_spinner()
                    # Stop the Live context that spinner started
                    if display._live is not None:
                        display._live.stop()
                        display._live = None
                    spinner_active = False
                else:
                    # Text was streamed — finalize the response panel
                    display.finish_response_stream()

            elif Agent.is_call_tools_node(node):
                async with node.stream(agent_run.ctx) as tool_stream:
                    async for event in tool_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            # Show the command being called in a tool_call panel
                            tool_name = event.part.tool_name
                            tool_args = event.part.args
                            if isinstance(tool_args, dict) and "command" in tool_args:
                                display.show_panel(
                                    tool_args["command"], "tool_call"
                                )
                            else:
                                display.show_panel(
                                    f"{tool_name}({tool_args})", "tool_call"
                                )
                        elif isinstance(event, FunctionToolResultEvent):
                            # Tool output was already streamed line-by-line
                            # via shell_tool's on_line callback. But if there's
                            # content not already shown (e.g., rejection message
                            # or non-shell tool result), display it.
                            content = event.result.content
                            if isinstance(content, str) and content:
                                # Only show if it looks like a rejection/error
                                # (shell output was already streamed to display)
                                pass
                            elif content:
                                display.show_panel(str(content), "tool_output")

            elif Agent.is_end_node(node):
                # Final result already streamed via model request node
                pass

    history.update(agent_run.result.all_messages())
    return agent_run.result.output


# ---------------------------------------------------------------------------
# Batch turn execution (Phase 1 — deprecated, kept for backward compatibility)
# ---------------------------------------------------------------------------


async def run_agent_turn(
    agent: Agent,
    prompt: str,
    history: ConversationHistory,
) -> str:
    """Run one agent turn: send *prompt*, let the agent act, return its reply.

    .. deprecated::
        Use ``run_agent_turn_streaming()`` instead for Phase 2 Rich UI.
        This function is kept for backward compatibility during the transition
        and will be removed when Plan 04 completes the REPL integration.

    Uses ``agent.run()`` (not ``agent.iter()``) — no streaming display.

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
