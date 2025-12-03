"""Tests for LLM mock providers and comprehensive mocking scenarios.

This module provides robust mock providers for OpenAI/Anthropic that can be used
in tests without making real API calls. It covers success, failure, and timeout
paths for LLM integration.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gengine.echoes.llm.providers import (
    IntentParseResult,
    LLMProvider,
    NarrateResult,
    StubProvider,
)
from gengine.echoes.llm.settings import LLMSettings


# ==============================================================================
# Mock Provider Infrastructure
# ==============================================================================


@dataclass
class MockResponse:
    """Configurable mock response for testing."""

    intents: list[dict[str, Any]] = field(default_factory=list)
    raw_response: str = '{"mock": "response"}'
    confidence: float = 0.9
    narrative: str = "Mock narrative for testing."
    metadata: dict[str, Any] | None = None
    should_raise: Exception | None = None
    delay_seconds: float = 0.0


class ConfigurableMockProvider(LLMProvider):
    """A fully configurable mock LLM provider for testing.

    This provider allows tests to configure exactly what responses are returned,
    including errors and delays, without making any real API calls.
    """

    def __init__(
        self,
        settings: LLMSettings,
        parse_response: MockResponse | None = None,
        narrate_response: MockResponse | None = None,
    ) -> None:
        super().__init__(settings)
        self._parse_response = parse_response or MockResponse(
            intents=[{"type": "observe", "target": "city"}],
        )
        self._narrate_response = narrate_response or MockResponse()
        self._call_count = 0
        self._parse_calls: list[tuple[str, dict[str, Any]]] = []
        self._narrate_calls: list[tuple[list[dict[str, Any]], dict[str, Any]]] = []

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def parse_calls(self) -> list[tuple[str, dict[str, Any]]]:
        return self._parse_calls

    @property
    def narrate_calls(self) -> list[tuple[list[dict[str, Any]], dict[str, Any]]]:
        return self._narrate_calls

    def set_parse_response(self, response: MockResponse) -> None:
        self._parse_response = response

    def set_narrate_response(self, response: MockResponse) -> None:
        self._narrate_response = response

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        self._call_count += 1
        self._parse_calls.append((user_input, context))

        if self._parse_response.delay_seconds > 0:
            await asyncio.sleep(self._parse_response.delay_seconds)

        if self._parse_response.should_raise:
            raise self._parse_response.should_raise

        return IntentParseResult(
            intents=self._parse_response.intents,
            raw_response=self._parse_response.raw_response,
            confidence=self._parse_response.confidence,
        )

    async def narrate(
        self,
        events: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> NarrateResult:
        self._call_count += 1
        self._narrate_calls.append((events, context))

        if self._narrate_response.delay_seconds > 0:
            await asyncio.sleep(self._narrate_response.delay_seconds)

        if self._narrate_response.should_raise:
            raise self._narrate_response.should_raise

        return NarrateResult(
            narrative=self._narrate_response.narrative,
            raw_response=self._narrate_response.raw_response,
            metadata=self._narrate_response.metadata,
        )


# ==============================================================================
# Test Classes
# ==============================================================================


class TestConfigurableMockProvider:
    """Tests for the configurable mock provider itself."""

    @pytest.fixture
    def settings(self) -> LLMSettings:
        return LLMSettings(provider="stub")

    @pytest.mark.anyio
    async def test_default_parse_response(self, settings: LLMSettings) -> None:
        """Provider returns default parse response."""
        provider = ConfigurableMockProvider(settings)
        result = await provider.parse_intent("test input", {})

        assert len(result.intents) == 1
        assert result.intents[0]["type"] == "observe"
        assert result.confidence == 0.9

    @pytest.mark.anyio
    async def test_custom_parse_response(self, settings: LLMSettings) -> None:
        """Provider returns configured parse response."""
        custom_response = MockResponse(
            intents=[{"type": "inspect", "target": "district"}],
            confidence=0.95,
            raw_response='{"custom": "response"}',
        )
        provider = ConfigurableMockProvider(settings, parse_response=custom_response)

        result = await provider.parse_intent("check status", {"tick": 10})

        assert len(result.intents) == 1
        assert result.intents[0]["type"] == "inspect"
        assert result.confidence == 0.95
        assert '{"custom": "response"}' in result.raw_response

    @pytest.mark.anyio
    async def test_parse_raises_configured_error(self, settings: LLMSettings) -> None:
        """Provider raises configured exception for parse_intent."""
        error_response = MockResponse(should_raise=ValueError("API Error"))
        provider = ConfigurableMockProvider(settings, parse_response=error_response)

        with pytest.raises(ValueError, match="API Error"):
            await provider.parse_intent("test", {})

    @pytest.mark.anyio
    async def test_narrate_raises_configured_error(self, settings: LLMSettings) -> None:
        """Provider raises configured exception for narrate."""
        error_response = MockResponse(should_raise=RuntimeError("Network Error"))
        provider = ConfigurableMockProvider(settings, narrate_response=error_response)

        with pytest.raises(RuntimeError, match="Network Error"):
            await provider.narrate([], {})

    @pytest.mark.anyio
    async def test_parse_delay(self, settings: LLMSettings) -> None:
        """Provider delays response for configured time."""
        delayed_response = MockResponse(delay_seconds=0.1)
        provider = ConfigurableMockProvider(settings, parse_response=delayed_response)

        start = asyncio.get_event_loop().time()
        await provider.parse_intent("test", {})
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed >= 0.09  # Allow small variance

    @pytest.mark.anyio
    async def test_call_tracking(self, settings: LLMSettings) -> None:
        """Provider tracks all calls made."""
        provider = ConfigurableMockProvider(settings)

        await provider.parse_intent("input1", {"ctx": 1})
        await provider.parse_intent("input2", {"ctx": 2})
        await provider.narrate([{"event": "a"}], {"tick": 5})

        assert provider.call_count == 3
        assert len(provider.parse_calls) == 2
        assert len(provider.narrate_calls) == 1
        assert provider.parse_calls[0] == ("input1", {"ctx": 1})
        assert provider.narrate_calls[0][0] == [{"event": "a"}]

    @pytest.mark.anyio
    async def test_set_response_dynamically(self, settings: LLMSettings) -> None:
        """Provider response can be changed between calls."""
        provider = ConfigurableMockProvider(settings)

        result1 = await provider.parse_intent("first", {})
        assert result1.intents[0]["type"] == "observe"

        provider.set_parse_response(
            MockResponse(intents=[{"type": "stabilize", "target": "district"}])
        )

        result2 = await provider.parse_intent("second", {})
        assert result2.intents[0]["type"] == "stabilize"


class TestMockOpenAIScenarios:
    """Test OpenAI provider with mocked API responses for various scenarios."""

    @pytest.fixture
    def settings(self) -> LLMSettings:
        return LLMSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-4-turbo-preview",
            timeout_seconds=30,
            max_retries=2,
        )

    @pytest.mark.anyio
    async def test_openai_timeout_handling(self, settings: LLMSettings) -> None:
        """OpenAI provider handles timeout gracefully."""
        from openai import OpenAIError

        from gengine.echoes.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(settings)

        # Mock a timeout scenario
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(100)  # Very long delay

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=OpenAIError("Request timed out"),
        ):
            result = await provider.parse_intent(
                "test command",
                context={"session_id": "timeout-test"},
            )

        # Should return empty intents with error info
        assert len(result.intents) == 0
        assert result.confidence == 0.0
        assert "timed out" in result.raw_response.lower() or "error" in result.raw_response.lower()

    @pytest.mark.anyio
    async def test_openai_rate_limit_error(self, settings: LLMSettings) -> None:
        """OpenAI provider handles rate limit errors."""
        from openai import RateLimitError

        from gengine.echoes.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(settings)

        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=mock_response,
                body=None,
            ),
        ):
            result = await provider.parse_intent(
                "test command",
                context={"session_id": "ratelimit-test"},
            )

        assert len(result.intents) == 0
        assert result.confidence == 0.0

    @pytest.mark.anyio
    async def test_openai_deploy_resource_function_call(
        self, settings: LLMSettings
    ) -> None:
        """OpenAI provider handles deploy_resource function call."""
        from gengine.echoes.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(settings)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.name = "deploy_resource"
        mock_response.choices[0].message.function_call.arguments = (
            '{"resource_type": "materials", "amount": 100, '
            '"target_district": "industrial-tier", "purpose": "stabilize"}'
        )
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Deploy 100 materials to the industrial tier",
                context={"session_id": "test-deploy"},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "DEPLOY_RESOURCE"
        assert intent["resource_type"] == "materials"
        assert intent["amount"] == 100
        assert intent["target_district"] == "industrial-tier"

    @pytest.mark.anyio
    async def test_openai_covert_action_function_call(
        self, settings: LLMSettings
    ) -> None:
        """OpenAI provider handles covert_action function call."""
        from gengine.echoes.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(settings)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.name = "covert_action"
        mock_response.choices[0].message.function_call.arguments = (
            '{"action_type": "sabotage", "target_faction": "compact-majority", '
            '"risk_level": "high"}'
        )
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Sabotage the Compact Majority",
                context={"session_id": "test-covert"},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "COVERT_ACTION"
        assert intent["action_type"] == "sabotage"
        assert intent["target_faction"] == "compact-majority"
        assert intent["risk_level"] == "high"

    @pytest.mark.anyio
    async def test_openai_unknown_function_ignored(
        self, settings: LLMSettings
    ) -> None:
        """OpenAI provider handles unknown function names gracefully."""
        from gengine.echoes.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(settings)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.name = "unknown_function"
        mock_response.choices[0].message.function_call.arguments = '{"some": "data"}'
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Do something unknown",
                context={"session_id": "test-unknown"},
            )

        # Unknown functions should result in empty intents
        assert len(result.intents) == 0
        assert result.confidence == 0.3


class TestMockAnthropicScenarios:
    """Test Anthropic provider with mocked API responses for various scenarios."""

    @pytest.fixture
    def settings(self) -> LLMSettings:
        return LLMSettings(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
            timeout_seconds=30,
            max_retries=2,
        )

    @pytest.mark.anyio
    async def test_anthropic_timeout_handling(self, settings: LLMSettings) -> None:
        """Anthropic provider handles timeout gracefully."""
        from anthropic import AnthropicError

        from gengine.echoes.llm.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(settings)

        with patch.object(
            provider.client.messages,
            "create",
            side_effect=AnthropicError("Request timed out"),
        ):
            result = await provider.parse_intent(
                "test command",
                context={"session_id": "timeout-test"},
            )

        assert len(result.intents) == 0
        assert result.confidence == 0.0

    @pytest.mark.anyio
    async def test_anthropic_covert_action_intent(self, settings: LLMSettings) -> None:
        """Anthropic provider parses covert action intent."""
        from gengine.echoes.llm.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(settings)

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """{
            "intent_type": "COVERT_ACTION",
            "confidence": 0.85,
            "parameters": {
                "action_type": "infiltrate",
                "target_district": "spire",
                "risk_level": "medium"
            }
        }"""
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Infiltrate the Spire",
                context={"session_id": "test-covert"},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "COVERT_ACTION"
        assert intent["action_type"] == "infiltrate"
        assert intent["target_district"] == "spire"
        assert intent["risk_level"] == "medium"

    @pytest.mark.anyio
    async def test_anthropic_pass_policy_intent(self, settings: LLMSettings) -> None:
        """Anthropic provider parses pass policy intent."""
        from gengine.echoes.llm.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(settings)

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """{
            "intent_type": "PASS_POLICY",
            "confidence": 0.92,
            "parameters": {
                "policy_id": "energy-rationing",
                "duration_ticks": 5
            }
        }"""
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Enact energy rationing for 5 ticks",
                context={"session_id": "test-policy"},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "PASS_POLICY"
        assert intent["policy_id"] == "energy-rationing"
        assert intent["duration_ticks"] == 5

    @pytest.mark.anyio
    async def test_anthropic_json_with_extra_text(self, settings: LLMSettings) -> None:
        """Anthropic provider extracts JSON from response with extra text."""
        from gengine.echoes.llm.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(settings)

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        # Response with preamble text before JSON
        mock_response.content[0].text = """Based on your request, I'll parse this as an inspect intent.

        {
            "intent_type": "INSPECT",
            "confidence": 0.88,
            "parameters": {
                "target_type": "district",
                "target_id": "perimeter-hollow"
            }
        }

        This should help you understand the district better."""
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Check perimeter hollow",
                context={"session_id": "test-extract"},
            )

        # Should still extract the JSON correctly
        assert len(result.intents) == 1
        assert result.intents[0]["intent"] == "INSPECT"
        assert result.intents[0]["target_id"] == "perimeter-hollow"

    @pytest.mark.anyio
    async def test_anthropic_empty_content(self, settings: LLMSettings) -> None:
        """Anthropic provider handles empty content response."""
        from gengine.echoes.llm.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(settings)

        mock_response = MagicMock()
        mock_response.content = []
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "test command",
                context={"session_id": "test-empty"},
            )

        assert len(result.intents) == 0


class TestMockProviderIntegration:
    """Integration tests using mock providers in realistic scenarios."""

    @pytest.mark.anyio
    async def test_sequential_commands_different_intents(self) -> None:
        """Mock provider handles sequence of different command types."""
        settings = LLMSettings(provider="stub")
        provider = ConfigurableMockProvider(settings)

        # First command: inspect
        provider.set_parse_response(
            MockResponse(intents=[{"type": "inspect", "target": "district"}])
        )
        result1 = await provider.parse_intent("check the district", {})

        # Second command: negotiate
        provider.set_parse_response(
            MockResponse(intents=[{"type": "negotiate", "target": "faction"}])
        )
        result2 = await provider.parse_intent("talk to faction", {})

        # Third command: stabilize
        provider.set_parse_response(
            MockResponse(intents=[{"type": "stabilize", "target": "district"}])
        )
        result3 = await provider.parse_intent("calm the unrest", {})

        assert result1.intents[0]["type"] == "inspect"
        assert result2.intents[0]["type"] == "negotiate"
        assert result3.intents[0]["type"] == "stabilize"
        assert provider.call_count == 3

    @pytest.mark.anyio
    async def test_error_recovery_scenario(self) -> None:
        """Mock provider can simulate error then recovery."""
        settings = LLMSettings(provider="stub")
        provider = ConfigurableMockProvider(settings)

        # First call fails
        provider.set_parse_response(MockResponse(should_raise=RuntimeError("API Down")))

        with pytest.raises(RuntimeError):
            await provider.parse_intent("first attempt", {})

        # Second call succeeds (API recovered)
        provider.set_parse_response(
            MockResponse(intents=[{"type": "observe", "target": "city"}])
        )
        result = await provider.parse_intent("second attempt", {})

        assert len(result.intents) == 1
        assert result.intents[0]["type"] == "observe"

    @pytest.mark.anyio
    async def test_mixed_success_and_failure_narration(self) -> None:
        """Narration can alternate between success and failure."""
        settings = LLMSettings(provider="stub")
        provider = ConfigurableMockProvider(settings)

        # Success
        provider.set_narrate_response(
            MockResponse(narrative="The city grows tense.")
        )
        result1 = await provider.narrate([{"type": "unrest"}], {})
        assert "tense" in result1.narrative

        # Failure
        provider.set_narrate_response(
            MockResponse(should_raise=TimeoutError("Service timeout"))
        )
        with pytest.raises(TimeoutError):
            await provider.narrate([{"type": "event"}], {})

        # Success again
        provider.set_narrate_response(
            MockResponse(narrative="Peace returns to the streets.")
        )
        result2 = await provider.narrate([{"type": "calm"}], {})
        assert "Peace" in result2.narrative


class TestStubProviderEdgeCases:
    """Additional edge case tests for the built-in StubProvider."""

    @pytest.fixture
    def stub_provider(self) -> StubProvider:
        settings = LLMSettings(provider="stub")
        return StubProvider(settings)

    @pytest.mark.anyio
    async def test_empty_user_input(self, stub_provider: StubProvider) -> None:
        """StubProvider handles empty input."""
        result = await stub_provider.parse_intent("", {})
        assert len(result.intents) > 0
        # Empty input should default to observe
        assert result.intents[0]["type"] == "observe"

    @pytest.mark.anyio
    async def test_mixed_case_keywords(self, stub_provider: StubProvider) -> None:
        """StubProvider handles mixed case keywords."""
        result1 = await stub_provider.parse_intent("INSPECT the area", {})
        result2 = await stub_provider.parse_intent("ChEcK status", {})
        result3 = await stub_provider.parse_intent("STATUS report", {})

        assert result1.intents[0]["type"] == "inspect"
        assert result2.intents[0]["type"] == "inspect"
        assert result3.intents[0]["type"] == "inspect"

    @pytest.mark.anyio
    async def test_complex_user_input(self, stub_provider: StubProvider) -> None:
        """StubProvider extracts intent from complex input."""
        complex_input = (
            "I want to check on the status of the industrial district "
            "and see how the pollution levels are affecting the workers"
        )
        result = await stub_provider.parse_intent(complex_input, {})

        assert len(result.intents) > 0
        # Should detect "check" or "status" keyword
        assert result.intents[0]["type"] == "inspect"

    @pytest.mark.anyio
    async def test_narrate_with_metadata(self, stub_provider: StubProvider) -> None:
        """StubProvider narrate returns expected metadata."""
        events = [{"type": "event1"}, {"type": "event2"}]
        result = await stub_provider.narrate(events, {"tick": 50})

        assert result.metadata is not None
        assert result.metadata["stub_mode"] is True
        assert result.metadata["event_count"] == 2

    @pytest.mark.anyio
    async def test_context_passed_through(self, stub_provider: StubProvider) -> None:
        """Verify context is accessible (even if not used by stub)."""
        context = {
            "tick": 100,
            "district": "industrial-tier",
            "stability": 0.5,
            "session_id": "test-session",
        }
        result = await stub_provider.parse_intent("check status", context)

        # Stub provider returns result regardless of context
        assert result.confidence == 1.0
        assert len(result.intents) > 0
