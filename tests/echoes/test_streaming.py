"""Tests for streaming functionality in LLM providers and service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from gengine.echoes.llm.foundry_local_provider import FoundryLocalProvider
from gengine.echoes.llm.providers import StubProvider
from gengine.echoes.llm.settings import LLMSettings


@pytest.mark.unit
class TestStreamingCapabilityDetection:
    """Test that providers correctly report streaming capability."""

    def test_foundry_local_supports_streaming(self):
        """FoundryLocalProvider should report streaming support."""
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
            model="test-model",
        )
        provider = FoundryLocalProvider(settings)
        assert provider.supports_streaming() is True

    def test_stub_provider_no_streaming(self):
        """StubProvider should not support streaming."""
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)
        assert provider.supports_streaming() is False


@pytest.mark.unit
class TestStreamingSettings:
    """Test streaming configuration via settings and environment."""

    def test_streaming_enabled_by_default(self):
        """Streaming should be enabled by default."""
        settings = LLMSettings()
        assert settings.enable_streaming is True

    def test_streaming_disabled_via_setting(self):
        """Streaming can be disabled via enable_streaming=False."""
        settings = LLMSettings(enable_streaming=False)
        assert settings.enable_streaming is False

    @patch.dict("os.environ", {"ECHOES_LLM_NO_STREAMING": "true"})
    def test_streaming_disabled_via_env_var(self):
        """ECHOES_LLM_NO_STREAMING=true should disable streaming."""
        settings = LLMSettings.from_env()
        assert settings.enable_streaming is False

    @patch.dict("os.environ", {"ECHOES_LLM_NO_STREAMING": "false"})
    def test_streaming_enabled_via_env_var_false(self):
        """ECHOES_LLM_NO_STREAMING=false should keep streaming enabled."""
        settings = LLMSettings.from_env()
        assert settings.enable_streaming is True

    @patch.dict("os.environ", {"ECHOES_LLM_NO_STREAMING": "1"})
    def test_streaming_disabled_via_env_var_one(self):
        """ECHOES_LLM_NO_STREAMING=1 should disable streaming."""
        settings = LLMSettings.from_env()
        assert settings.enable_streaming is False


@pytest.mark.unit
@pytest.mark.anyio
class TestFoundryLocalStreaming:
    """Test Foundry Local provider streaming behavior."""

    async def test_narrate_uses_streaming_when_enabled(self):
        """narrate() should use streaming when enabled and supported."""
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
            model="test-model",
            enable_streaming=True,
        )
        provider = FoundryLocalProvider(settings)

        # Mock the narrate_stream method
        async def mock_stream(*args, **kwargs):
            yield "The city "
            yield "is quiet "
            yield "tonight."

        provider.narrate_stream = mock_stream

        events = [{"description": "Agent moves through the district"}]
        result = await provider.narrate(events, {})

        assert result.narrative == "The city is quiet tonight."
        assert result.metadata is not None
        assert result.metadata.get("streaming") is True
        assert result.metadata.get("chunk_count") == 3

    async def test_narrate_uses_buffered_when_streaming_disabled(self):
        """narrate() should use buffered mode when streaming is disabled."""
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
            model="test-model",
            enable_streaming=False,
        )
        provider = FoundryLocalProvider(settings)

        # Mock the _chat_completion method for buffered mode
        async def mock_completion(*args, **kwargs):
            return (
                {
                    "choices": [
                        {
                            "message": {
                                "content": "The city remains in equilibrium."
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                    },
                },
                '{"choices":[{"message":{"content":"The city remains..."}}]}',
            )

        provider._chat_completion = mock_completion

        events = [{"description": "Nothing happens"}]
        result = await provider.narrate(events, {})

        assert result.narrative == "The city remains in equilibrium."
        assert result.metadata is not None
        assert result.metadata.get("streaming") is False
        assert result.metadata.get("prompt_tokens") == 10
        assert result.metadata.get("completion_tokens") == 5

    async def test_narrate_stream_parses_sse_chunks(self):
        """narrate_stream() should parse Server-Sent Events correctly."""
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
            model="test-model",
        )
        provider = FoundryLocalProvider(settings)

        # Mock httpx.AsyncClient.stream
        mock_response = MagicMock()

        async def mock_lines():
            yield "data: " + '{"choices":[{"delta":{"content":"Hello"}}]}'
            yield "data: " + '{"choices":[{"delta":{"content":" world"}}]}'
            yield "data: " + '{"choices":[{"delta":{"content":"!"}}]}'
            yield "data: [DONE]"

        mock_response.aiter_lines = mock_lines
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.stream = MagicMock()
        mock_client.stream.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_client.stream.return_value.__aexit__ = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_client):
            chunks = []
            async for chunk in provider.narrate_stream(
                [{"description": "test"}], {}
            ):
                chunks.append(chunk)

        assert chunks == ["Hello", " world", "!"]

    async def test_narrate_stream_handles_empty_content(self):
        """narrate_stream() should skip chunks with no content."""
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
            model="test-model",
        )
        provider = FoundryLocalProvider(settings)

        # Mock httpx.AsyncClient.stream
        mock_response = MagicMock()

        async def mock_lines():
            yield "data: " + '{"choices":[{"delta":{}}]}'  # No content
            yield "data: " + '{"choices":[{"delta":{"content":"Text"}}]}'
            yield "data: " + '{"choices":[{"delta":{"content":null}}]}'  # JSON null
            yield "data: [DONE]"

        mock_response.aiter_lines = mock_lines
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.stream = MagicMock()
        mock_client.stream.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_client.stream.return_value.__aexit__ = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_client):
            chunks = []
            async for chunk in provider.narrate_stream(
                [{"description": "test"}], {}
            ):
                chunks.append(chunk)

        assert chunks == ["Text"]

    async def test_narrate_stream_handles_malformed_json(self):
        """narrate_stream() should skip malformed JSON chunks."""
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
            model="test-model",
        )
        provider = FoundryLocalProvider(settings)

        # Mock httpx.AsyncClient.stream
        mock_response = MagicMock()

        async def mock_lines():
            yield "data: {invalid json"
            yield "data: " + '{"choices":[{"delta":{"content":"Good"}}]}'
            yield "data: [DONE]"

        mock_response.aiter_lines = mock_lines
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.stream = MagicMock()
        mock_client.stream.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_client.stream.return_value.__aexit__ = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_client):
            chunks = []
            async for chunk in provider.narrate_stream(
                [{"description": "test"}], {}
            ):
                chunks.append(chunk)

        # Should have skipped the malformed chunk
        assert chunks == ["Good"]


@pytest.mark.unit
@pytest.mark.anyio
class TestStreamingErrorHandling:
    """Test error handling in streaming scenarios."""

    async def test_narrate_falls_back_on_streaming_error(self):
        """If streaming fails, narrate() should return an error result."""
        settings = LLMSettings(
            provider="foundry_local",
            base_url="http://localhost:5272",
            model="test-model",
            enable_streaming=True,
        )
        provider = FoundryLocalProvider(settings)

        # Mock narrate_stream to raise an exception
        async def mock_stream_error(*args, **kwargs):
            raise RuntimeError("Streaming connection failed")
            yield  # Make it a generator

        provider.narrate_stream = mock_stream_error

        events = [{"description": "Test event"}]
        result = await provider.narrate(events, {})

        assert result.narrative == ""
        assert "error" in result.metadata
        assert "failed" in result.metadata["error"].lower()


@pytest.mark.unit
class TestStreamingMetrics:
    """Test that streaming metrics are properly recorded."""

    def test_metrics_have_streaming_counters(self):
        """LLMMetrics should have streaming-specific counters."""
        from gengine.echoes.llm.app import LLMMetrics

        metrics = LLMMetrics()

        # Test that streaming methods exist
        assert hasattr(metrics, "record_streaming_enabled")
        assert hasattr(metrics, "record_streaming_disabled")
        assert hasattr(metrics, "record_streaming_chunks")

    def test_metrics_record_streaming_enabled(self):
        """record_streaming_enabled() should increment counter."""
        from gengine.echoes.llm.app import LLMMetrics

        metrics = LLMMetrics()

        # Should not raise
        metrics.record_streaming_enabled()
        metrics.record_streaming_enabled()

    def test_metrics_record_streaming_disabled_with_reason(self):
        """record_streaming_disabled() should accept reason labels."""
        from gengine.echoes.llm.app import LLMMetrics

        metrics = LLMMetrics()

        # Should not raise
        metrics.record_streaming_disabled("disabled_by_config")
        metrics.record_streaming_disabled("provider_unsupported")

    def test_metrics_record_chunk_counts(self):
        """record_streaming_chunks() should record histogram values."""
        from gengine.echoes.llm.app import LLMMetrics

        metrics = LLMMetrics()

        # Should not raise
        metrics.record_streaming_chunks(5)
        metrics.record_streaming_chunks(42)
        metrics.record_streaming_chunks(100)
