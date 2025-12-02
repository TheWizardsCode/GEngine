"""FastAPI application for LLM service."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .providers import LLMProvider, create_provider
from .settings import LLMSettings


class ParseIntentRequest(BaseModel):
    """Request payload for /parse_intent endpoint."""

    user_input: str = Field(..., description="Natural language input from user")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Game state context for intent parsing",
    )


class ParseIntentResponse(BaseModel):
    """Response from /parse_intent endpoint."""

    intents: list[dict[str, Any]] = Field(..., description="Parsed intent objects")
    raw_response: str = Field(..., description="Raw LLM response")
    confidence: float | None = Field(None, description="Confidence score if available")


class NarrateRequest(BaseModel):
    """Request payload for /narrate endpoint."""

    events: list[dict[str, Any]] = Field(..., description="Game events to narrate")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Game state context for narrative generation",
    )


class NarrateResponse(BaseModel):
    """Response from /narrate endpoint."""

    narrative: str = Field(..., description="Generated narrative text")
    raw_response: str = Field(..., description="Raw LLM response")
    metadata: dict[str, Any] | None = Field(None, description="Generation metadata")


def create_llm_app(
    *,
    provider: LLMProvider | None = None,
    settings: LLMSettings | None = None,
) -> FastAPI:
    """Create FastAPI application for LLM service.

    Parameters
    ----------
    provider
        Pre-configured LLM provider. If None, creates from settings.
    settings
        LLM settings. If None and provider is None, loads from environment.

    Returns
    -------
    FastAPI
        Configured FastAPI application
    """
    if provider is None:
        if settings is None:
            settings = LLMSettings.from_env()
        provider = create_provider(settings)

    app = FastAPI(
        title="Echoes LLM Service",
        description="Natural language intent parsing and narrative generation",
        version="0.1.0",
    )

    # Store provider in app state
    app.state.llm_provider = provider
    app.state.llm_settings = provider.settings

    @app.get("/healthz")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "provider": app.state.llm_settings.provider,
            "model": app.state.llm_settings.model or "N/A",
        }

    @app.post("/parse_intent", response_model=ParseIntentResponse)
    async def parse_intent(request: ParseIntentRequest) -> ParseIntentResponse:
        """Parse natural language input into structured intents.

        Takes user input and game context, returns structured intent objects
        that can be routed to the simulation service.
        """
        try:
            result = await app.state.llm_provider.parse_intent(
                request.user_input,
                request.context,
            )
            return ParseIntentResponse(
                intents=result.intents,
                raw_response=result.raw_response,
                confidence=result.confidence,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Intent parsing failed: {str(e)}",
            ) from e

    @app.post("/narrate", response_model=NarrateResponse)
    async def narrate(request: NarrateRequest) -> NarrateResponse:
        """Generate narrative description of game events.

        Takes game events and context, returns natural language narrative
        suitable for presenting to the player.
        """
        try:
            result = await app.state.llm_provider.narrate(
                request.events,
                request.context,
            )
            return NarrateResponse(
                narrative=result.narrative,
                raw_response=result.raw_response,
                metadata=result.metadata,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Narration failed: {str(e)}",
            ) from e

    return app
