"""FastAPI application for LLM service."""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field

from .providers import LLMProvider, create_provider
from .settings import LLMSettings


class LLMMetrics:
    """Prometheus metrics tracking for the LLM service."""

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        """Initialize Prometheus metrics with optional custom registry."""
        self._registry = registry or CollectorRegistry()
        
        # Request counters
        self._total_requests = Counter(
            "llm_requests_total",
            "Total number of requests processed",
            registry=self._registry,
        )
        self._parse_intent_requests = Counter(
            "llm_parse_intent_requests_total",
            "Total parse_intent requests",
            registry=self._registry,
        )
        self._narrate_requests = Counter(
            "llm_narrate_requests_total",
            "Total narrate requests",
            registry=self._registry,
        )

        # Error counters
        self._total_errors = Counter(
            "llm_errors_total",
            "Total number of errors",
            registry=self._registry,
        )
        self._parse_intent_errors = Counter(
            "llm_parse_intent_errors_total",
            "Total parse_intent errors",
            registry=self._registry,
        )
        self._narrate_errors = Counter(
            "llm_narrate_errors_total",
            "Total narrate errors",
            registry=self._registry,
        )
        self._errors_by_type = Counter(
            "llm_errors_by_type_total",
            "Errors by endpoint and type",
            ["endpoint", "error_type"],
            registry=self._registry,
        )

        # Latency histograms (in seconds for Prometheus convention)
        self._parse_intent_latency = Histogram(
            "llm_parse_intent_latency_seconds",
            "parse_intent request latency in seconds",
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=self._registry,
        )
        self._narrate_latency = Histogram(
            "llm_narrate_latency_seconds",
            "narrate request latency in seconds",
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=self._registry,
        )

        # Token usage counters
        self._total_input_tokens = Counter(
            "llm_input_tokens_total",
            "Total input tokens used",
            registry=self._registry,
        )
        self._total_output_tokens = Counter(
            "llm_output_tokens_total",
            "Total output tokens used",
            registry=self._registry,
        )

    @property
    def registry(self) -> CollectorRegistry:
        """Return the Prometheus registry."""
        return self._registry

    def record_parse_intent(
        self,
        latency_seconds: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record a parse_intent request."""
        self._total_requests.inc()
        self._parse_intent_requests.inc()
        self._parse_intent_latency.observe(latency_seconds)
        if input_tokens > 0:
            self._total_input_tokens.inc(input_tokens)
        if output_tokens > 0:
            self._total_output_tokens.inc(output_tokens)

    def record_narrate(
        self,
        latency_seconds: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record a narrate request."""
        self._total_requests.inc()
        self._narrate_requests.inc()
        self._narrate_latency.observe(latency_seconds)
        if input_tokens > 0:
            self._total_input_tokens.inc(input_tokens)
        if output_tokens > 0:
            self._total_output_tokens.inc(output_tokens)

    def record_error(self, endpoint: str, error_type: str) -> None:
        """Record an error by endpoint and type."""
        self._total_errors.inc()
        if endpoint == "parse_intent":
            self._parse_intent_errors.inc()
        elif endpoint == "narrate":
            self._narrate_errors.inc()
        self._errors_by_type.labels(endpoint=endpoint, error_type=error_type).inc()


def _extract_token_usage(result: Any) -> tuple[int, int]:
    """Extract token usage from LLM result.

    Tries result attributes first, then falls back to metadata dict.
    Returns (input_tokens, output_tokens).
    """
    # Try direct attributes first
    input_tokens = getattr(result, "input_tokens", None)
    output_tokens = getattr(result, "output_tokens", None)

    # Fall back to metadata dict if available
    if input_tokens is None and hasattr(result, "metadata") and result.metadata:
        input_tokens = result.metadata.get("input_tokens")
    if output_tokens is None and hasattr(result, "metadata") and result.metadata:
        output_tokens = result.metadata.get("output_tokens")

    return (input_tokens or 0, output_tokens or 0)


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
    
    # Initialize metrics
    metrics = LLMMetrics()
    app.state.llm_metrics = metrics

    @app.get("/healthz")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "provider": app.state.llm_settings.provider,
            "model": app.state.llm_settings.model or "N/A",
        }

    @app.get("/metrics")
    async def get_metrics() -> Response:
        """Return LLM service metrics in Prometheus text format."""
        return Response(
            content=generate_latest(metrics.registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.post("/parse_intent", response_model=ParseIntentResponse)
    async def parse_intent(request: ParseIntentRequest) -> ParseIntentResponse:
        """Parse natural language input into structured intents.
        
        Takes user input and game context, returns structured intent objects
        that can be routed to the simulation service.
        """
        start_time = time.perf_counter()
        try:
            result = await app.state.llm_provider.parse_intent(
                request.user_input,
                request.context,
            )
            latency_seconds = time.perf_counter() - start_time
            # Extract token usage from result attributes or metadata
            input_tokens, output_tokens = _extract_token_usage(result)
            metrics.record_parse_intent(latency_seconds, input_tokens, output_tokens)
            return ParseIntentResponse(
                intents=result.intents,
                raw_response=result.raw_response,
                confidence=result.confidence,
            )
        except Exception as e:
            metrics.record_error("parse_intent", type(e).__name__)
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
        start_time = time.perf_counter()
        try:
            result = await app.state.llm_provider.narrate(
                request.events,
                request.context,
            )
            latency_seconds = time.perf_counter() - start_time
            # Extract token usage from result attributes or metadata
            input_tokens, output_tokens = _extract_token_usage(result)
            metrics.record_narrate(latency_seconds, input_tokens, output_tokens)
            return NarrateResponse(
                narrative=result.narrative,
                raw_response=result.raw_response,
                metadata=result.metadata,
            )
        except Exception as e:
            metrics.record_error("narrate", type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Narration failed: {str(e)}",
            ) from e

    return app
