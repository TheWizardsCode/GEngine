"""Tests for LLM providers."""

from __future__ import annotations

import pytest

from gengine.echoes.llm.providers import (
    IntentParseResult,
    LLMProvider,
    NarrateResult,
    StubProvider,
    create_provider,
)
from gengine.echoes.llm.settings import LLMSettings

pytestmark = pytest.mark.anyio


class TestStubProvider:
    """Tests for StubProvider."""

    async def test_parse_intent_inspect(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

        result = await provider.parse_intent(
            "Check the status of the district",
            {"tick": 0},
        )

        assert isinstance(result, IntentParseResult)
        assert len(result.intents) > 0
        assert result.intents[0]["type"] == "inspect"
        assert result.intents[0]["target"] == "district"
        assert result.confidence == 1.0
        assert "[STUB]" in result.raw_response

    async def test_parse_intent_stabilize(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

        result = await provider.parse_intent(
            "Stabilize the unrest in the area",
            {},
        )

        assert len(result.intents) > 0
        assert result.intents[0]["type"] == "stabilize"

    async def test_parse_intent_negotiate(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

        result = await provider.parse_intent(
            "Talk to the faction leaders",
            {},
        )

        assert len(result.intents) > 0
        assert result.intents[0]["type"] == "negotiate"

    async def test_parse_intent_default(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

        result = await provider.parse_intent(
            "What's happening?",
            {},
        )

        assert len(result.intents) > 0
        assert result.intents[0]["type"] == "observe"

    async def test_narrate_empty_events(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

        result = await provider.narrate([], {})

        assert isinstance(result, NarrateResult)
        assert "equilibrium" in result.narrative.lower()
        assert "[STUB]" in result.raw_response
        assert result.metadata is not None
        assert result.metadata["stub_mode"] is True

    async def test_narrate_with_events(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

        events = [
            {"type": "stability_drop", "district": "industrial-tier"},
            {"type": "faction_action", "faction": "union_of_flux"},
            {"type": "resource_shortage", "resource": "energy"},
        ]

        result = await provider.narrate(events, {"tick": 10})

        assert "3 event(s)" in result.narrative
        assert "stability_drop" in result.narrative
        assert result.metadata["event_count"] == 3

    async def test_narrate_many_events(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

        events = [{"type": f"event_{i}"} for i in range(10)]

        result = await provider.narrate(events, {})

        assert "10 event(s)" in result.narrative
        assert "and 7 more" in result.narrative


class TestCreateProvider:
    """Tests for create_provider factory."""

    def test_create_stub_provider(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = create_provider(settings)

        assert isinstance(provider, StubProvider)
        assert provider.settings.provider == "stub"

    def test_create_openai_provider(self) -> None:
        settings = LLMSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-4",
        )

        provider = create_provider(settings)
        assert provider.settings.provider == "openai"
        assert provider.settings.api_key == "test-key"
        assert provider.settings.model == "gpt-4"

    def test_create_anthropic_provider(self) -> None:
        settings = LLMSettings(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-sonnet-20240229",
        )

        provider = create_provider(settings)
        assert provider.settings.provider == "anthropic"
        assert provider.settings.api_key == "test-key"
        assert provider.settings.model == "claude-3-sonnet-20240229"

    def test_create_invalid_provider(self) -> None:
        settings = LLMSettings(provider="invalid")

        with pytest.raises(ValueError, match="Invalid provider"):
            create_provider(settings)

    def test_validation_called_by_factory(self) -> None:
        settings = LLMSettings(
            provider="openai",
            # Missing api_key and model
        )

        with pytest.raises(ValueError, match="API key required"):
            create_provider(settings)
