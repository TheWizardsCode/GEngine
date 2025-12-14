"""Configuration for LLM service."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class LLMSettings:
    """Configuration for LLM service and providers.

    Attributes
    ----------
    provider
        LLM provider to use: "openai", "anthropic", "foundry_local", or "stub"
    api_key
        API key for the provider (not needed for stub mode)
    model
        Model identifier (e.g., "gpt-4", "claude-3-sonnet-20240229")
    base_url
        Base URL for HTTP-compatible providers (foundry_local)
    temperature
        Sampling temperature (0.0-1.0)
    max_tokens
        Maximum tokens in response
    timeout_seconds
        Request timeout in seconds
    enable_rag
        Enable Retrieval-Augmented Generation (RAG) for context retrieval
    rag_db_path
        Path to the RAG knowledge base database file
    rag_top_k
        Number of top documents to retrieve for RAG context
    rag_min_score
        Minimum relevance score threshold for retrieved documents
    """

    provider: str = "stub"
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 30
    max_retries: int = 2
    enable_rag: bool = False
    rag_db_path: str = "build/knowledge_base/index.db"
    rag_top_k: int = 3
    rag_min_score: float = 0.5

    def loggable_dict(self) -> dict[str, Any]:
        """Return a sanitized dict for logging without exposing secrets."""
        data = asdict(self)
        if data.get("api_key"):
            data["api_key"] = "***redacted***"
        return data

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
        ECHOES_LLM_BASE_URL : str
            Base URL for HTTP-compatible providers (default varies per provider)
        ECHOES_LLM_ENABLE_RAG : bool
            Enable RAG context retrieval (default: false)
        ECHOES_LLM_RAG_DB_PATH : str
            Path to RAG knowledge base (default: build/knowledge_base/index.db)
        ECHOES_LLM_RAG_TOP_K : int
            Number of top documents to retrieve (default: 3)
        ECHOES_LLM_RAG_MIN_SCORE : float
            Minimum relevance score for documents (default: 0.5)
        """
        provider = os.getenv("ECHOES_LLM_PROVIDER", "stub")
        api_key = os.getenv("ECHOES_LLM_API_KEY")
        model = os.getenv("ECHOES_LLM_MODEL")
        base_url = os.getenv("ECHOES_LLM_BASE_URL")

        temperature = float(os.getenv("ECHOES_LLM_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("ECHOES_LLM_MAX_TOKENS", "1000"))
        timeout_seconds = int(os.getenv("ECHOES_LLM_TIMEOUT", "30"))
        max_retries = int(os.getenv("ECHOES_LLM_MAX_RETRIES", "2"))

        enable_rag = os.getenv("ECHOES_LLM_ENABLE_RAG", "false").lower() in ("true", "1", "yes")
        rag_db_path = os.getenv("ECHOES_LLM_RAG_DB_PATH", "build/knowledge_base/index.db")
        rag_top_k = int(os.getenv("ECHOES_LLM_RAG_TOP_K", "3"))
        rag_min_score = float(os.getenv("ECHOES_LLM_RAG_MIN_SCORE", "0.5"))

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            enable_rag=enable_rag,
            rag_db_path=rag_db_path,
            rag_top_k=rag_top_k,
            rag_min_score=rag_min_score,
        )

    def validate(self) -> None:
        """Validate settings and raise ValueError if invalid."""
        if self.provider not in ("stub", "openai", "anthropic", "foundry_local"):
            raise ValueError(
                f"Invalid provider '{self.provider}'. "
                "Must be 'stub', 'openai', 'anthropic', or 'foundry_local'."
            )

        if self.provider in ("openai", "anthropic") and not self.api_key:
            raise ValueError(f"API key required for provider '{self.provider}'")

        if self.provider != "stub" and not self.model:
            raise ValueError(
                f"Model identifier required for provider '{self.provider}'"
            )

        if self.provider == "foundry_local" and not self.base_url:
            raise ValueError("Base URL required for provider 'foundry_local'")

        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")

        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")

        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")

        if self.rag_top_k < 1:
            raise ValueError("rag_top_k must be at least 1")

        if not 0.0 <= self.rag_min_score <= 1.0:
            raise ValueError("rag_min_score must be between 0.0 and 1.0")
