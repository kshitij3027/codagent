"""Shell execution tool with approval gate, truncation, timeout, and dangerous command detection.

This module provides the single tool the agent uses to interact with the system.
All commands run through execute_command() which handles async subprocess execution,
output truncation, and timeout. The shell_tool() function adds the approval gate
layer on top.
"""

from __future__ import annotations

import asyncio
import re

from codagent.config import get_settings

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

    Uses run_in_executor to avoid blocking the async event loop while
    waiting for user input (keeps Ctrl-C responsive).

    Args:
        command: The command to display for approval.
        reason: Optional reason shown to the user (e.g. "Dangerous command").

    Returns:
        True if the user approves (enter, y, yes), False otherwise.
    """
    loop = asyncio.get_event_loop()

    def _prompt() -> str:
        print(f"[command] {command}")
        if reason:
            print(f"[reason] {reason}")
        return input("Approve? [Y/n] ")

    response = await loop.run_in_executor(None, _prompt)
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

    # Execute the command
    return await execute_command(command, timeout=settings.command_timeout)
