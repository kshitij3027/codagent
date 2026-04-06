"""Model provider registry with friendly name mapping.

Maps user-friendly model names (e.g., "gpt5", "claude", "groq") to
Pydantic AI model strings (e.g., "openai:gpt-5"). The OpenRouter model
string is overridable via the OPENROUTER_MODEL environment variable since
OpenRouter model names can change without notice.
"""

from __future__ import annotations

import os
from typing import Optional

from codagent.config import get_settings


# Default OpenRouter model string (may change -- overridable via env var)
_DEFAULT_OPENROUTER_MODEL = "x-ai/grok-code-fast-1"


def _get_openrouter_model() -> str:
    """Get the OpenRouter model string, checking env var override first."""
    override = os.getenv("OPENROUTER_MODEL")
    if override:
        return override
    # Also check settings if loaded
    try:
        settings = get_settings()
        if settings.openrouter_model:
            return settings.openrouter_model
    except RuntimeError:
        pass
    return _DEFAULT_OPENROUTER_MODEL


MODEL_REGISTRY: dict[str, str] = {
    "gpt5": "openai:gpt-5",
    "claude": "anthropic:claude-4.5-sonnet",
    "groq": "openrouter:{model}",  # placeholder, resolved at call time
}


def get_model(name: str) -> str:
    """Resolve a friendly model name to a Pydantic AI model string.

    Args:
        name: Friendly model name (e.g., "gpt5", "claude", "groq").

    Returns:
        Pydantic AI model string (e.g., "openai:gpt-5").

    Raises:
        ValueError: If the name is not in the registry.
    """
    if name not in MODEL_REGISTRY:
        available = ", ".join(sorted(MODEL_REGISTRY.keys()))
        raise ValueError(
            f"Unknown model '{name}'. Available models: {available}"
        )

    template = MODEL_REGISTRY[name]

    # Resolve OpenRouter model dynamically
    if "{model}" in template:
        openrouter_model = _get_openrouter_model()
        resolved = template.format(model=openrouter_model)
    else:
        resolved = template

    return resolved


def list_models() -> list[str]:
    """Return a sorted list of available friendly model names."""
    return sorted(MODEL_REGISTRY.keys())


def get_default_model() -> str:
    """Get the Pydantic AI model string for the configured default model.

    Reads default_model from settings and resolves it via the registry.

    Returns:
        Pydantic AI model string for the default model.

    Raises:
        RuntimeError: If settings have not been loaded.
        ValueError: If the default model name is not in the registry.
    """
    settings = get_settings()
    name = settings.default_model
    return get_model(name)
