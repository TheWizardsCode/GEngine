"""Configuration for LLM service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMSettings:
    """Configuration for LLM service and providers.

    Attributes
    ----------
    provider
        LLM provider to use: "openai", "anthropic", or "stub"
    api_key
        API key for the provider (not needed for stub mode)
    model
        Model identifier (e.g., "gpt-4", "claude-3-sonnet-20240229")
    temperature
        Sampling temperature (0.0-1.0)
    max_tokens
        Maximum tokens in response
    timeout_seconds
        Request timeout in seconds
    """

    provider: str = "stub"
    api_key: str | None = None
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 30
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> LLMSettings:
        """Load settings from environment variables.

        Environment Variables
        ---------------------
        ECHOES_LLM_PROVIDER : str
            Provider name (default: "stub")
        ECHOES_LLM_API_KEY : str
            API key for the provider
        ECHOES_LLM_MODEL : str
            Model identifier
        ECHOES_LLM_TEMPERATURE : float
            Sampling temperature (default: 0.7)
        ECHOES_LLM_MAX_TOKENS : int
            Max response tokens (default: 1000)
        ECHOES_LLM_TIMEOUT : int
            Request timeout in seconds (default: 30)
        """
        provider = os.getenv("ECHOES_LLM_PROVIDER", "stub")
        api_key = os.getenv("ECHOES_LLM_API_KEY")
        model = os.getenv("ECHOES_LLM_MODEL")

        temperature = float(os.getenv("ECHOES_LLM_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("ECHOES_LLM_MAX_TOKENS", "1000"))
        timeout_seconds = int(os.getenv("ECHOES_LLM_TIMEOUT", "30"))
        max_retries = int(os.getenv("ECHOES_LLM_MAX_RETRIES", "2"))

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    def validate(self) -> None:
        """Validate settings and raise ValueError if invalid."""
        if self.provider not in ("stub", "openai", "anthropic", "tinyllama"):
            raise ValueError(
                f"Invalid provider '{self.provider}'. "
                "Must be 'stub', 'openai', 'anthropic', or 'tinyllama'."
            )

        if self.provider not in ("stub", "tinyllama") and not self.api_key:
            raise ValueError(f"API key required for provider '{self.provider}'")

        if self.provider not in ("stub", "tinyllama") and not self.model:
            raise ValueError(
                f"Model identifier required for provider '{self.provider}'"
            )

        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")

        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")

        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")
