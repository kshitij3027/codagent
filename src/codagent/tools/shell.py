"""Shell execution tool with approval gate, truncation, timeout, and dangerous command detection.

This module provides the single tool the agent uses to interact with the system.
All commands run through execute_command() which handles async subprocess execution,
output truncation, and timeout. The shell_tool() function adds the approval gate
layer on top.

For streaming display integration, call ``set_display(display)`` before running the
agent. When a Display is configured, shell_tool() uses ``execute_command_streaming()``
for real-time line-by-line output, and ``prompt_user_approval()`` renders styled
Rich prompts instead of bare print/input.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from codagent.config import get_settings

if TYPE_CHECKING:
    from codagent.display import Display

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRUNCATION_LIMIT: int = 10_000
"""Maximum characters of combined stdout+stderr returned to the model."""

# Compiled dangerous command patterns (case-insensitive matching).
# These always require explicit user approval, even in yolo mode.
DANGEROUS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"rm\s+(-\w*\s+)*-rf\s+[/~*]", re.IGNORECASE),
    re.compile(r"rm\s+(-\w*\s+)*-fr\s+[/~*]", re.IGNORECASE),
    re.compile(r"DROP\s+(TABLE|DATABASE)", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+\w+\s*;?\s*$", re.IGNORECASE),
    re.compile(r"git\s+push\s+.*--force", re.IGNORECASE),
    re.compile(r"git\s+push\s+.*-f\b", re.IGNORECASE),
    re.compile(r"mkfs\.", re.IGNORECASE),
    re.compile(r"dd\s+if=", re.IGNORECASE),
    re.compile(r">\s*/dev/sd", re.IGNORECASE),
    re.compile(r":\(\)\{.*\|.*&\}\s*;", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Module-level display reference (set by agent integration layer)
# ---------------------------------------------------------------------------

_display: Display | None = None
"""Optional Display instance for Rich-styled output. Set via ``set_display()``."""


def set_display(display: Display) -> None:
    """Configure the module-level Display for styled approval and streaming output.

    Call this once during application startup, before the agent runs.
    When set, ``shell_tool()`` uses ``execute_command_streaming()`` with
    real-time line callbacks, and ``prompt_user_approval()`` uses Rich styling.

    Args:
        display: The Display instance from the terminal UI layer.
    """
    global _display
    _display = display


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------


async def execute_command(command: str, timeout: int = 120) -> str:
    """Execute a shell command asynchronously and return formatted output.

    Uses asyncio.create_subprocess_shell for non-blocking execution.
    Output is truncated at TRUNCATION_LIMIT characters with a visible marker.
    Commands that exceed the timeout are killed.

    Args:
        command: The shell command string to execute.
        timeout: Maximum seconds to wait before killing the process.

    Returns:
        Formatted string with exit code, stdout, and stderr.
    """
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()  # Reap the process to avoid zombies
        return f"[TIMEOUT] Command timed out after {timeout}s and was killed."

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    output = stdout
    if stderr:
        output += f"\n[stderr]\n{stderr}"

    # Truncate if output exceeds the limit
    if len(output) > TRUNCATION_LIMIT:
        total = len(output)
        output = (
            output[:TRUNCATION_LIMIT]
            + f"\n\n... [output truncated at {TRUNCATION_LIMIT} chars, {total} chars total]"
        )

    return f"Exit code: {proc.returncode}\n{output}"


# ---------------------------------------------------------------------------
# Streaming execution
# ---------------------------------------------------------------------------


async def execute_command_streaming(
    command: str,
    on_line: Callable[[str], Awaitable[None]],
    timeout: int = 120,
) -> str:
    """Execute a shell command with line-by-line streaming output.

    Like ``execute_command()``, but calls ``on_line(line)`` for each line
    read from stdout/stderr, enabling real-time display updates.

    Reads stdout and stderr concurrently via ``asyncio.gather()`` to avoid
    pipe deadlock (research Pitfall 7). After ``TRUNCATION_LIMIT`` chars,
    output is still read (to prevent deadlock) but no longer forwarded to
    ``on_line`` or collected.

    Args:
        command: The shell command string to execute.
        on_line: Async callback invoked with each output line.
        timeout: Maximum seconds before the process is killed.

    Returns:
        Formatted string with exit code and combined output, same format
        as ``execute_command()``.
    """
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    collected: list[str] = []
    total_chars = 0

    async def read_stream(
        stream: asyncio.StreamReader, prefix: str = ""
    ) -> None:
        nonlocal total_chars
        async for line_bytes in stream:
            line = line_bytes.decode("utf-8", errors="replace")
            total_chars += len(line)
            if total_chars <= TRUNCATION_LIMIT:
                collected.append(prefix + line)
                await on_line(prefix + line)
            # else: still read to avoid pipe deadlock, but discard

    try:
        await asyncio.wait_for(
            asyncio.gather(
                read_stream(proc.stdout, prefix=""),
                read_stream(proc.stderr, prefix="[stderr] "),
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return f"[TIMEOUT] Command timed out after {timeout}s and was killed."

    await proc.wait()

    output = "".join(collected)
    if total_chars > TRUNCATION_LIMIT:
        output += (
            f"\n\n... [output truncated at {TRUNCATION_LIMIT} chars, "
            f"{total_chars} chars total]"
        )

    return f"Exit code: {proc.returncode}\n{output}"


# ---------------------------------------------------------------------------
# Dangerous command detection
# ---------------------------------------------------------------------------


def is_dangerous(command: str) -> bool:
    """Check whether a command matches any known dangerous pattern.

    Returns True if the command matches at least one pattern from
    DANGEROUS_PATTERNS (e.g. rm -rf /, DROP TABLE, force push).
    """
    return any(pattern.search(command) for pattern in DANGEROUS_PATTERNS)


# ---------------------------------------------------------------------------
# Approval gate
# ---------------------------------------------------------------------------


async def prompt_user_approval(
    command: str, reason: str | None = None
) -> bool:
    """Prompt the user to approve a command before execution.

    When a Display is configured (via ``set_display()``), uses Rich markup
    for styled command/reason output and ``console.input()`` for the prompt.
    Otherwise, falls back to bare ``print()`` / ``input()``.

    Uses ``run_in_executor`` to avoid blocking the async event loop while
    waiting for user input (keeps Ctrl-C responsive).

    Args:
        command: The command to display for approval.
        reason: Optional reason shown to the user (e.g. "Dangerous command").

    Returns:
        True if the user approves (enter, y, yes), False otherwise.
    """
    loop = asyncio.get_event_loop()

    if _display is not None:
        console = _display.console

        def _prompt_rich() -> str:
            console.print(f"[bold yellow]{command}[/bold yellow]")
            if reason:
                console.print(f"[dim]{reason}[/dim]")
            return console.input("[bold]Approve? [Y/n] [/bold]")

        response = await loop.run_in_executor(None, _prompt_rich)
    else:

        def _prompt_plain() -> str:
            print(f"[command] {command}")
            if reason:
                print(f"[reason] {reason}")
            return input("Approve? [Y/n] ")

        response = await loop.run_in_executor(None, _prompt_plain)

    return response.strip().lower() in ("", "y", "yes")


# ---------------------------------------------------------------------------
# Shell tool (registered on the agent in agent.py)
# ---------------------------------------------------------------------------


async def shell_tool(command: str) -> str:
    """Execute a shell command. Returns stdout, stderr, and exit code.

    Use this to interact with the filesystem, run tests, install packages,
    and perform any CLI operation.
    """
    settings = get_settings()

    # Always check dangerous commands first — even in yolo mode
    if is_dangerous(command):
        approved = await prompt_user_approval(
            command,
            reason="Dangerous command detected -- requires explicit approval",
        )
        if not approved:
            return (
                "Command rejected by user. Dangerous command was not executed. "
                "Ask the user what they'd like to do instead."
            )

    # In approval mode, prompt for every command
    if settings.mode == "approval":
        approved = await prompt_user_approval(command)
        if not approved:
            return (
                "Command rejected by user. The user chose not to run this command. "
                "Ask the user what they'd like to do instead."
            )

    # Execute the command — streaming when display is available
    if _display is not None:
        display = _display  # local ref for closure

        async def _on_line(line: str) -> None:
            display.stream_tool_line(line)

        display.start_tool_output_stream()
        try:
            result = await execute_command_streaming(
                command,
                on_line=_on_line,
                timeout=settings.command_timeout,
            )
        finally:
            display.finish_tool_output_stream()
        return result

    return await execute_command(command, timeout=settings.command_timeout)
