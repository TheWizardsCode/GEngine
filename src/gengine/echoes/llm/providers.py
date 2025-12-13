"""LLM provider abstraction layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .settings import LLMSettings


@dataclass
class IntentParseResult:
    """Result from parsing user input into structured intents.

    Attributes
    ----------
    intents
        List of structured intent objects
    raw_response
        Raw LLM response for debugging
    confidence
        Confidence score (0.0-1.0) if available
    """

    intents: list[dict[str, Any]]
    raw_response: str
    confidence: float | None = None


@dataclass
class NarrateResult:
    """Result from generating narrative response.

    Attributes
    ----------
    narrative
        Generated narrative text
    raw_response
        Raw LLM response for debugging
    metadata
        Optional metadata about generation
    """

    narrative: str
    raw_response: str
    metadata: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, settings: LLMSettings) -> None:
        """Initialize provider with settings.

        Parameters
        ----------
        settings
            LLM configuration settings
        """
        self.settings = settings

    @abstractmethod
    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        """Parse user input into structured intents.

        Parameters
        ----------
        user_input
            Natural language input from user
        context
            Game state context for intent parsing

        Returns
        -------
        IntentParseResult
            Parsed intents with metadata
        """
        pass

    @abstractmethod
    async def narrate(
        self,
        events: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> NarrateResult:
        """Generate narrative description of game events.

        Parameters
        ----------
        events
            List of game events to narrate
        context
            Game state context for narrative generation

        Returns
        -------
        NarrateResult
            Generated narrative with metadata
        """
        pass


class StubProvider(LLMProvider):
    """Stub LLM provider for offline testing.

    Returns deterministic responses without making API calls.
    Useful for testing and development without incurring API costs.
    """

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        """Return stub intent parsing result."""
        # Simple keyword-based intent detection for testing
        user_lower = user_input.lower()
        intents = []

        if "inspect" in user_lower or "check" in user_lower or "status" in user_lower:
            intents.append(
                {
                    "type": "inspect",
                    "target": "district" if "district" in user_lower else "city",
                }
            )
        elif "stabilize" in user_lower or "calm" in user_lower:
            intents.append(
                {
                    "type": "stabilize",
                    "target": "district",
                }
            )
        elif "negotiate" in user_lower or "talk" in user_lower:
            intents.append(
                {
                    "type": "negotiate",
                    "target": "faction",
                }
            )
        else:
            intents.append(
                {
                    "type": "observe",
                    "target": "city",
                }
            )

        return IntentParseResult(
            intents=intents,
            raw_response=f"[STUB] Parsed: {user_input}",
            confidence=1.0,
        )

    async def narrate(
        self,
        events: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> NarrateResult:
        """Return stub narrative result."""
        if not events:
            narrative = "The city remains in a state of uneasy equilibrium."
        else:
            event_count = len(events)
            narrative = (
                f"[STUB] {event_count} event(s) unfolded: "
                f"{', '.join(e.get('type', 'unknown') for e in events[:3])}"
            )
            if event_count > 3:
                narrative += f", and {event_count - 3} more..."

        return NarrateResult(
            narrative=narrative,
            raw_response=f"[STUB] Narrated {len(events)} events",
            metadata={"stub_mode": True, "event_count": len(events)},
        )


def create_provider(settings: LLMSettings) -> LLMProvider:
    """Factory function to create LLM provider based on settings.

    Parameters
    ----------
    settings
        LLM configuration settings

    Returns
    -------
    LLMProvider
        Configured provider instance

    Raises
    ------
    ValueError
        If provider type is unsupported
    """
    settings.validate()

    if settings.provider == "stub":
        return StubProvider(settings)
    elif settings.provider == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(settings)
    elif settings.provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings)
    elif settings.provider == "foundry_local":
        from .foundry_local_provider import FoundryLocalProvider

        return FoundryLocalProvider(settings)
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")
