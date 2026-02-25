"""Configuration loading and settings management.

Loads environment variables from .env file and provides a Settings
singleton accessible via get_settings().
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    """Application settings loaded from environment variables.

    The `mode` field is mutable at runtime -- it toggles between
    "approval" and "yolo" via slash commands.
    """

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    default_model: str = "gpt5"
    mode: str = "approval"
    command_timeout: int = 120
    openrouter_model: Optional[str] = None


# Module-level singleton
_settings: Optional[Settings] = None


def load_settings() -> Settings:
    """Load settings from environment variables (after loading .env file).

    Calling this multiple times reloads from the environment each time.
    The singleton is updated on each call.
    """
    global _settings

    load_dotenv()

    _settings = Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY") or None,
        default_model=os.getenv("DEFAULT_MODEL", "gpt5"),
        mode=os.getenv("DEFAULT_MODE", "approval"),
        command_timeout=int(os.getenv("COMMAND_TIMEOUT", "120")),
        openrouter_model=os.getenv("OPENROUTER_MODEL") or None,
    )

    return _settings


def get_settings() -> Settings:
    """Get the current settings singleton.

    Raises RuntimeError if load_settings() has not been called yet.
    """
    if _settings is None:
        raise RuntimeError(
            "Settings not loaded. Call load_settings() at startup."
        )
    return _settings
