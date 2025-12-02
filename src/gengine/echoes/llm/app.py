"""FastAPI application for LLM service."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .providers import LLMProvider, create_provider
from .settings import LLMSettings


@dataclass
class LLMMetrics:
    """Metrics tracking for the LLM service."""

    # Request counts
    total_requests: int = 0
    parse_intent_requests: int = 0
    narrate_requests: int = 0

    # Error tracking
    total_errors: int = 0
    parse_intent_errors: int = 0
    narrate_errors: int = 0
    errors_by_type: dict[str, int] = field(default_factory=dict)

    # Latency tracking (in ms)
    parse_intent_latencies: list[float] = field(default_factory=list)
    narrate_latencies: list[float] = field(default_factory=list)
    max_latency_samples: int = 1000

    # Token usage (if available from provider)
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def record_parse_intent(self, latency_ms: float, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Record a parse_intent request."""
        self.total_requests += 1
        self.parse_intent_requests += 1
        self._add_latency(self.parse_intent_latencies, latency_ms)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def record_narrate(self, latency_ms: float, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Record a narrate request."""
        self.total_requests += 1
        self.narrate_requests += 1
        self._add_latency(self.narrate_latencies, latency_ms)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def record_error(self, endpoint: str, error_type: str) -> None:
        """Record an error by endpoint and type."""
        self.total_errors += 1
        if endpoint == "parse_intent":
            self.parse_intent_errors += 1
        elif endpoint == "narrate":
            self.narrate_errors += 1
        key = f"{endpoint}:{error_type}"
        self.errors_by_type[key] = self.errors_by_type.get(key, 0) + 1

    def _add_latency(self, latencies: list[float], latency_ms: float) -> None:
        """Add latency sample, maintaining max samples."""
        if len(latencies) >= self.max_latency_samples:
            latencies.pop(0)
        latencies.append(latency_ms)

    def to_dict(self, provider: str = "unknown", model: str | None = None) -> dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        parse_intent_stats = self._calculate_latency_stats(self.parse_intent_latencies)
        narrate_stats = self._calculate_latency_stats(self.narrate_latencies)

        return {
            "requests": {
                "total": self.total_requests,
                "parse_intent": self.parse_intent_requests,
                "narrate": self.narrate_requests,
            },
            "errors": {
                "total": self.total_errors,
                "parse_intent": self.parse_intent_errors,
                "narrate": self.narrate_errors,
                "by_type": dict(self.errors_by_type),
            },
            "latency_ms": {
                "parse_intent": parse_intent_stats,
                "narrate": narrate_stats,
            },
            "provider": {
                "name": provider,
                "model": model or "N/A",
            },
            "token_usage": {
                "total_input": self.total_input_tokens,
                "total_output": self.total_output_tokens,
            },
        }

    def _calculate_latency_stats(self, latencies: list[float]) -> dict[str, float]:
        """Calculate latency statistics from samples."""
        if not latencies:
            return {"avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p95": 0.0}

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        return {
            "avg": round(sum(latencies) / n, 2),
            "min": round(min(latencies), 2),
            "max": round(max(latencies), 2),
            "p50": round(sorted_latencies[n // 2], 2),
            "p95": round(sorted_latencies[int(n * 0.95)] if n >= 20 else sorted_latencies[-1], 2),
        }


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
    async def get_metrics() -> dict[str, Any]:
        """Return LLM service metrics for Prometheus scraping."""
        return {
            "service": "llm",
            **metrics.to_dict(
                provider=app.state.llm_settings.provider,
                model=app.state.llm_settings.model,
            ),
        }

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
            latency_ms = (time.perf_counter() - start_time) * 1000
            # Extract token usage from metadata if available
            input_tokens = getattr(result, "input_tokens", 0) or 0
            output_tokens = getattr(result, "output_tokens", 0) or 0
            metrics.record_parse_intent(latency_ms, input_tokens, output_tokens)
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
            )

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
            latency_ms = (time.perf_counter() - start_time) * 1000
            # Extract token usage from metadata if available
            input_tokens = 0
            output_tokens = 0
            if result.metadata:
                input_tokens = result.metadata.get("input_tokens", 0) or 0
                output_tokens = result.metadata.get("output_tokens", 0) or 0
            metrics.record_narrate(latency_ms, input_tokens, output_tokens)
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
            )

    return app
