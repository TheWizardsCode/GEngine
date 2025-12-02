"""Integration tests for Anthropic provider with mocked API responses."""

from unittest.mock import MagicMock, patch

import pytest

from gengine.echoes.llm.anthropic_provider import AnthropicProvider
from gengine.echoes.llm.settings import LLMSettings


class TestAnthropicProvider:
    """Test Anthropic provider with mocked API calls."""

    @pytest.fixture
    def settings(self) -> LLMSettings:
        return LLMSettings(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,
            max_tokens=1000,
            timeout_seconds=30,
            max_retries=2,
        )

    @pytest.fixture
    def provider(self, settings: LLMSettings) -> AnthropicProvider:
        return AnthropicProvider(settings)

    @pytest.mark.anyio
    async def test_parse_intent_inspect(self, provider: AnthropicProvider) -> None:
        """Test parsing an inspect intent using structured outputs."""
        # Mock Anthropic API response with JSON
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """{
            "intent_type": "INSPECT",
            "confidence": 0.95,
            "parameters": {
                "target_type": "district",
                "target_id": "perimeter-hollow",
                "focus_areas": ["security", "morale"]
            },
            "narrative_context": "Checking security and morale in Perimeter Hollow"
        }"""
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Check security and morale in Perimeter Hollow",
                context={"session_id": "test-456", "tick": 200},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "INSPECT"
        assert intent["session_id"] == "test-456"
        assert intent["target_type"] == "district"
        assert intent["target_id"] == "perimeter-hollow"
        assert intent["focus_areas"] == ["security", "morale"]
        assert result.confidence == 0.95

    @pytest.mark.anyio
    async def test_parse_intent_deploy_resource(
        self, provider: AnthropicProvider
    ) -> None:
        """Test parsing a deploy resource intent."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """{
            "intent_type": "DEPLOY_RESOURCE",
            "confidence": 0.9,
            "parameters": {
                "resource_type": "energy",
                "amount": 100,
                "target_district": "spire",
                "purpose": "power infrastructure"
            }
        }"""
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Send 100 energy to the Spire for infrastructure",
                context={"session_id": "test-456"},
            )

        assert len(result.intents) == 1
        intent = result.intents[0]
        assert intent["intent"] == "DEPLOY_RESOURCE"
        assert intent["resource_type"] == "energy"
        assert intent["amount"] == 100
        assert intent["target_district"] == "spire"

    @pytest.mark.anyio
    async def test_parse_intent_invalid_json(self, provider: AnthropicProvider) -> None:
        """Test handling malformed JSON response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "This is not valid JSON: {incomplete"
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Test command",
                context={"session_id": "test-456"},
            )

        assert len(result.intents) == 0
        assert result.confidence == 0.0

    @pytest.mark.anyio
    async def test_parse_intent_no_json(self, provider: AnthropicProvider) -> None:
        """Test handling response without JSON."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "I'm sorry, I don't understand that command."
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Nonsense command",
                context={"session_id": "test-456"},
            )

        assert len(result.intents) == 0

    @pytest.mark.anyio
    async def test_parse_intent_api_error(self, provider: AnthropicProvider) -> None:
        """Test handling Anthropic API error."""
        from anthropic import AnthropicError

        with patch.object(
            provider.client.messages,
            "create",
            side_effect=AnthropicError("API error"),
        ):
            result = await provider.parse_intent(
                "Test command",
                context={"session_id": "test-456"},
            )

        assert len(result.intents) == 0
        assert result.confidence == 0.0
        assert "API error" in result.raw_response

    @pytest.mark.anyio
    async def test_narrate_events(self, provider: AnthropicProvider) -> None:
        """Test generating narrative from events."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = (
            "In the shadowy streets of Perimeter Hollow, whispers of "
            "dissent grow louder. The Compact Majority tightens its grip, "
            "while the Union of Flux mobilizes its supporters."
        )
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        events = [
            {"description": "Protests in Perimeter Hollow"},
            {"description": "Compact Majority increases security"},
            {"description": "Union of Flux holds rally"},
        ]

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.narrate(
                events,
                context={"district": "perimeter-hollow", "sentiment": "tense"},
            )

        assert "Perimeter Hollow" in result.narrative
        assert result.metadata["event_count"] == 3
        assert result.metadata["tokens_used"] == 150  # input + output
        assert result.metadata["model"] == "claude-3-5-sonnet-20241022"

    @pytest.mark.anyio
    async def test_narrate_no_events(self, provider: AnthropicProvider) -> None:
        """Test narrating with no events."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "An eerie calm settles over the city."
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 8
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.narrate([], context={})

        assert "calm" in result.narrative.lower()
        assert result.metadata["event_count"] == 0

    @pytest.mark.anyio
    async def test_narrate_api_error(self, provider: AnthropicProvider) -> None:
        """Test handling API error during narration."""
        from anthropic import AnthropicError

        with patch.object(
            provider.client.messages,
            "create",
            side_effect=AnthropicError("Overloaded"),
        ):
            result = await provider.narrate(
                [{"description": "Test event"}],
                context={},
            )

        assert result.narrative == ""
        assert "error" in result.metadata
        assert "Overloaded" in result.raw_response

    @pytest.mark.anyio
    async def test_parse_intent_missing_intent_type(
        self, provider: AnthropicProvider
    ) -> None:
        """Test handling response with missing intent_type."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """{
            "confidence": 0.5,
            "parameters": {"some": "data"}
        }"""
        mock_response.model_dump_json.return_value = '{"mock": "response"}'

        with patch.object(
            provider.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await provider.parse_intent(
                "Test command",
                context={"session_id": "test-456"},
            )

        assert len(result.intents) == 0
