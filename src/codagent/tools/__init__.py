"""Shell execution tools for the coding agent."""

from codagent.tools.shell import (
    DANGEROUS_PATTERNS,
    TRUNCATION_LIMIT,
    execute_command,
    is_dangerous,
    prompt_user_approval,
    shell_tool,
)

__all__ = [
    "execute_command",
    "is_dangerous",
    "prompt_user_approval",
    "shell_tool",
    "DANGEROUS_PATTERNS",
    "TRUNCATION_LIMIT",
]
