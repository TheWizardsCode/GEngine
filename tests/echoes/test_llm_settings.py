"""Tests for LLM settings module."""

from __future__ import annotations

import os

import pytest

from gengine.echoes.llm.settings import LLMSettings


class TestLLMSettings:
    """Tests for LLMSettings."""

    def test_default_settings(self) -> None:
        settings = LLMSettings()
        assert settings.provider == "stub"
        assert settings.api_key is None
        assert settings.model is None
        assert settings.temperature == 0.7
        assert settings.max_tokens == 1000
        assert settings.timeout_seconds == 30
        assert settings.enable_rag is False
        assert settings.rag_db_path == "build/knowledge_base/index.db"
        assert settings.rag_top_k == 3
        assert settings.rag_min_score == 0.5
        assert settings.verbose_logging is False

    def test_custom_settings(self) -> None:
        settings = LLMSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=500,
            timeout_seconds=60,
        )
        assert settings.provider == "openai"
        assert settings.api_key == "test-key"
        assert settings.model == "gpt-4"
        assert settings.temperature == 0.5
        assert settings.max_tokens == 500
        assert settings.timeout_seconds == 60

    def test_from_env_defaults(self) -> None:
        old_env = {
            "ECHOES_LLM_PROVIDER": os.environ.get("ECHOES_LLM_PROVIDER"),
            "ECHOES_LLM_API_KEY": os.environ.get("ECHOES_LLM_API_KEY"),
            "ECHOES_LLM_MODEL": os.environ.get("ECHOES_LLM_MODEL"),
            "ECHOES_LLM_TEMPERATURE": os.environ.get("ECHOES_LLM_TEMPERATURE"),
            "ECHOES_LLM_MAX_TOKENS": os.environ.get("ECHOES_LLM_MAX_TOKENS"),
            "ECHOES_LLM_TIMEOUT": os.environ.get("ECHOES_LLM_TIMEOUT"),
            "ECHOES_LLM_BASE_URL": os.environ.get("ECHOES_LLM_BASE_URL"),
        }
        try:
            for key in old_env:
                os.environ.pop(key, None)

            settings = LLMSettings.from_env()
            assert settings.provider == "stub"
            assert settings.api_key is None
            assert settings.temperature == 0.7
        finally:
            for key, value in old_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

    def test_from_env_custom(self) -> None:
        old_env = {
            "ECHOES_LLM_PROVIDER": os.environ.get("ECHOES_LLM_PROVIDER"),
            "ECHOES_LLM_API_KEY": os.environ.get("ECHOES_LLM_API_KEY"),
            "ECHOES_LLM_MODEL": os.environ.get("ECHOES_LLM_MODEL"),
            "ECHOES_LLM_TEMPERATURE": os.environ.get("ECHOES_LLM_TEMPERATURE"),
            "ECHOES_LLM_MAX_TOKENS": os.environ.get("ECHOES_LLM_MAX_TOKENS"),
            "ECHOES_LLM_TIMEOUT": os.environ.get("ECHOES_LLM_TIMEOUT"),
            "ECHOES_LLM_BASE_URL": os.environ.get("ECHOES_LLM_BASE_URL"),
        }
        try:
            os.environ["ECHOES_LLM_PROVIDER"] = "anthropic"
            os.environ["ECHOES_LLM_API_KEY"] = "test-api-key"
            os.environ["ECHOES_LLM_MODEL"] = "claude-3-sonnet-20240229"
            os.environ["ECHOES_LLM_TEMPERATURE"] = "0.3"
            os.environ["ECHOES_LLM_MAX_TOKENS"] = "2000"
            os.environ["ECHOES_LLM_TIMEOUT"] = "45"
            os.environ["ECHOES_LLM_BASE_URL"] = "http://custom-base"

            settings = LLMSettings.from_env()
            assert settings.provider == "anthropic"
            assert settings.api_key == "test-api-key"
            assert settings.model == "claude-3-sonnet-20240229"
            assert settings.temperature == 0.3
            assert settings.max_tokens == 2000
            assert settings.timeout_seconds == 45
            assert settings.base_url == "http://custom-base"
        finally:
            for key, value in old_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

    def test_validate_stub_provider(self) -> None:
        settings = LLMSettings(provider="stub")
        settings.validate()  # Should not raise

    def test_validate_invalid_provider(self) -> None:
        settings = LLMSettings(provider="invalid")
        with pytest.raises(ValueError, match="Invalid provider"):
            settings.validate()

    def test_validate_missing_api_key(self) -> None:
        settings = LLMSettings(provider="openai", model="gpt-4")
        with pytest.raises(ValueError, match="API key required"):
            settings.validate()

    def test_validate_missing_model(self) -> None:
        settings = LLMSettings(provider="openai", api_key="test-key")
        with pytest.raises(ValueError, match="Model identifier required"):
            settings.validate()

    def test_validate_invalid_temperature(self) -> None:
        settings = LLMSettings(temperature=-0.1)
        with pytest.raises(ValueError, match="Temperature must be between"):
            settings.validate()

        settings = LLMSettings(temperature=2.1)
        with pytest.raises(ValueError, match="Temperature must be between"):
            settings.validate()

    def test_validate_invalid_max_tokens(self) -> None:
        settings = LLMSettings(max_tokens=0)
        with pytest.raises(ValueError, match="max_tokens must be at least 1"):
            settings.validate()

    def test_validate_invalid_timeout(self) -> None:
        settings = LLMSettings(timeout_seconds=0)
        with pytest.raises(ValueError, match="timeout_seconds must be at least 1"):
            settings.validate()

    def test_validate_foundry_provider_missing_base_url(self) -> None:
        settings = LLMSettings(
            provider="foundry_local",
            model="phi-local",
        )
        with pytest.raises(ValueError, match="Base URL required"):
            settings.validate()

    def test_validate_foundry_provider_missing_model(self) -> None:
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
        )
        with pytest.raises(ValueError, match="Model identifier required"):
            settings.validate()

    def test_validate_foundry_provider_success(self) -> None:
        settings = LLMSettings(
            provider="foundry_local",
            model="phi-4",
            base_url="http://localhost:5272",
        )
        settings.validate()

    def test_rag_settings_defaults(self) -> None:
        settings = LLMSettings()
        assert settings.enable_rag is False
        assert settings.rag_db_path == "build/knowledge_base/index.db"
        assert settings.rag_top_k == 3
        assert settings.rag_min_score == 0.5

    def test_rag_settings_custom(self) -> None:
        settings = LLMSettings(
            enable_rag=True,
            rag_db_path="custom/path.db",
            rag_top_k=5,
            rag_min_score=0.7,
        )
        assert settings.enable_rag is True
        assert settings.rag_db_path == "custom/path.db"
        assert settings.rag_top_k == 5
        assert settings.rag_min_score == 0.7

    def test_validate_invalid_rag_top_k(self) -> None:
        settings = LLMSettings(rag_top_k=0)
        with pytest.raises(ValueError, match="rag_top_k must be at least 1"):
            settings.validate()

    def test_validate_invalid_rag_min_score(self) -> None:
        settings = LLMSettings(rag_min_score=-0.1)
        with pytest.raises(ValueError, match="rag_min_score must be between"):
            settings.validate()

        settings = LLMSettings(rag_min_score=1.1)
        with pytest.raises(ValueError, match="rag_min_score must be between"):
            settings.validate()

    def test_from_env_rag_settings(self) -> None:
        old_env = {
            "ECHOES_LLM_ENABLE_RAG": os.environ.get("ECHOES_LLM_ENABLE_RAG"),
            "ECHOES_LLM_RAG_DB_PATH": os.environ.get("ECHOES_LLM_RAG_DB_PATH"),
            "ECHOES_LLM_RAG_TOP_K": os.environ.get("ECHOES_LLM_RAG_TOP_K"),
            "ECHOES_LLM_RAG_MIN_SCORE": os.environ.get("ECHOES_LLM_RAG_MIN_SCORE"),
        }
        try:
            os.environ["ECHOES_LLM_ENABLE_RAG"] = "true"
            os.environ["ECHOES_LLM_RAG_DB_PATH"] = "test/kb.db"
            os.environ["ECHOES_LLM_RAG_TOP_K"] = "5"
            os.environ["ECHOES_LLM_RAG_MIN_SCORE"] = "0.7"

            settings = LLMSettings.from_env()
            assert settings.enable_rag is True
            assert settings.rag_db_path == "test/kb.db"
            assert settings.rag_top_k == 5
            assert settings.rag_min_score == 0.7
        finally:
            for key, value in old_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

    def test_verbose_logging_env_var(self) -> None:
        old_value = os.environ.get("ECHOES_LLM_VERBOSE")
        try:
            os.environ["ECHOES_LLM_VERBOSE"] = "true"
            settings = LLMSettings.from_env()
            assert settings.verbose_logging is True
        finally:
            if old_value is not None:
                os.environ["ECHOES_LLM_VERBOSE"] = old_value
            else:
                os.environ.pop("ECHOES_LLM_VERBOSE", None)
