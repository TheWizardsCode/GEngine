"""Integration tests for OpenAI provider with mocked API responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gengine.echoes.llm.openai_provider import OpenAIProvider
from gengine.echoes.llm.settings import LLMSettings


class TestOpenAIProvider:
    """Test OpenAI provider with mocked API calls."""

    @pytest.fixture
    def settings(self) -> LLMSettings:
        return LLMSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-4-turbo-preview",
            temperature=0.3,
            max_tokens=1000,
            timeout_seconds=30,
            max_retries=2,
        )

    @pytest.fixture
    def provider(self, settings: LLMSettings) -> OpenAIProvider:
        return OpenAIProvider(settings)

    @pytest.mark.anyio
    async def test_parse_intent_inspect(self, provider: OpenAIProvider) -> None:
        """Test parsing an inspect intent using function calling."""
        # Mock OpenAI API response with function call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.name = "inspect_target"
        mock_response.choices[0].message.function_call.arguments = (
            '{"target_type": "district", "target_id": "industrial-tier", '
            '"focus_areas": ["production", "unrest"]}'
        )
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Check the industrial district production and unrest",
                context={"session_id": "test-123", "tick": 100},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "INSPECT"
        assert intent["session_id"] == "test-123"
        assert intent["target_type"] == "district"
        assert intent["target_id"] == "industrial-tier"
        assert intent["focus_areas"] == ["production", "unrest"]
        assert result.confidence == 0.9

    @pytest.mark.anyio
    async def test_parse_intent_negotiate(self, provider: OpenAIProvider) -> None:
        """Test parsing a negotiate intent."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.name = "negotiate_with_faction"
        mock_response.choices[0].message.function_call.arguments = (
            '{"targets": ["union-flux"], "levers": {"materials": 50}, '
            '"goal": "reduce protests"}'
        )
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Negotiate with Union of Flux to reduce protests by offering materials",
                context={"session_id": "test-123"},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "NEGOTIATE"
        assert intent["targets"] == ["union-flux"]
        assert intent["levers"] == {"materials": 50}
        assert intent["goal"] == "reduce protests"

    @pytest.mark.anyio
    async def test_parse_intent_no_function_call(
        self, provider: OpenAIProvider
    ) -> None:
        """Test handling response without function call."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.function_call = None
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "What's the weather?",
                context={"session_id": "test-123"},
            )

        assert len(result.intents) == 0
        assert result.confidence == 0.3

    @pytest.mark.anyio
    async def test_parse_intent_api_error(self, provider: OpenAIProvider) -> None:
        """Test handling OpenAI API error."""
        from openai import OpenAIError

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=OpenAIError("API error"),
        ):
            result = await provider.parse_intent(
                "Test command",
                context={"session_id": "test-123"},
            )

        assert len(result.intents) == 0
        assert result.confidence == 0.0
        assert "API error" in result.raw_response

    @pytest.mark.anyio
    async def test_narrate_events(self, provider: OpenAIProvider) -> None:
        """Test generating narrative from events."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "Tensions rise in the Industrial Tier as workers protest "
            "against the new policies. Meanwhile, the Union of Flux "
            "gains support among the populace."
        )
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 42
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        events = [
            {"description": "Worker protest in Industrial Tier"},
            {"description": "Union of Flux gains support"},
        ]

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.narrate(
                events,
                context={"district": "industrial-tier", "tick": 100},
            )

        assert "Tensions rise" in result.narrative
        assert result.metadata["event_count"] == 2
        assert result.metadata["tokens_used"] == 42
        assert result.metadata["model"] == "gpt-4-turbo-preview"

    @pytest.mark.anyio
    async def test_narrate_no_events(self, provider: OpenAIProvider) -> None:
        """Test narrating with no events."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "The city remains quiet for now."
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 10
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.narrate([], context={})

        assert "quiet" in result.narrative.lower()
        assert result.metadata["event_count"] == 0

    @pytest.mark.anyio
    async def test_narrate_api_error(self, provider: OpenAIProvider) -> None:
        """Test handling API error during narration."""
        from openai import OpenAIError

        with patch.object(
            provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=OpenAIError("Rate limit exceeded"),
        ):
            result = await provider.narrate(
                [{"description": "Test event"}],
                context={},
            )

        assert result.narrative == ""
        assert "error" in result.metadata
        assert "Rate limit" in result.raw_response
