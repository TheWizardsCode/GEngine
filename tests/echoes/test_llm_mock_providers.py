"""Tests for LLM mock providers and comprehensive mocking scenarios.

This module provides robust mock providers for OpenAI/Anthropic that can be used
in tests without making real API calls. It covers success, failure, and timeout
paths for LLM integration.
"""

from __future__ import annotations

import pytest

from gengine.echoes.llm.providers import (
    StubProvider,
)
from gengine.echoes.llm.settings import LLMSettings

# ...existing code up to TestStubProviderEdgeCases...

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

# ...existing code after TestStubProviderEdgeCases...
