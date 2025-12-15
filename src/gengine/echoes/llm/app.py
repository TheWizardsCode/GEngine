"""FastAPI application for LLM service."""

from __future__ import annotations

import logging
import time
from pathlib import Path
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
from .rag import (
    RAGRetriever,
    StubEmbeddingClient,
    VectorStore,
    format_retrieved_context,
)
from .settings import LLMSettings

logger = logging.getLogger(__name__)


def _log_rag_details(
    *,
    endpoint: str,
    query: str,
    documents: list[Any],
    context_chars: int,
) -> None:
    """Emit verbose log lines describing the RAG query/response lifecycle."""
    snippet = query.strip().replace("\n", " ")[:300]
    logger.info("[RAG][%s] Query: %s", endpoint, snippet or "<empty>")
    if not documents:
        logger.info("[RAG][%s] No documents retrieved", endpoint)
        return
    logger.info(
        "[RAG][%s] Retrieved %d docs (%d chars of context)",
        endpoint,
        len(documents),
        context_chars,
    )
    for idx, doc in enumerate(documents, 1):
        metadata = getattr(doc, "metadata", {}) or {}
        source = metadata.get("source", "unknown")
        score = getattr(doc, "score", 0.0)
        preview = (getattr(doc, "content", "") or "").strip().replace("\n", " ")[:160]
        logger.info(
            "[RAG][%s] #%d score=%.2f source=%s preview=%s",
            endpoint,
            idx,
            score,
            source,
            preview or "<empty>",
        )


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

        # RAG metrics
        self._rag_hits = Counter(
            "llm_rag_hits_total",
            "Total number of RAG context retrievals",
            registry=self._registry,
        )
        self._rag_latency = Histogram(
            "llm_rag_latency_seconds",
            "RAG retrieval latency in seconds",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
            registry=self._registry,
        )
        self._rag_context_chars = Histogram(
            "llm_rag_context_chars",
            "Number of characters in RAG context",
            buckets=[100, 500, 1000, 2000, 5000, 10000],
            registry=self._registry,
        )
        
        # Streaming metrics
        self._streaming_enabled_total = Counter(
            "llm_streaming_enabled_total",
            "Total number of requests with streaming enabled",
            registry=self._registry,
        )
        self._streaming_disabled_total = Counter(
            "llm_streaming_disabled_total",
            "Total number of requests with streaming disabled",
            ["reason"],
            registry=self._registry,
        )
        self._streaming_chunks = Histogram(
            "llm_streaming_chunks",
            "Number of chunks in streaming responses",
            buckets=[1, 5, 10, 20, 50, 100, 200],
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

    def record_rag_retrieval(
        self,
        latency_seconds: float,
        context_chars: int,
    ) -> None:
        """Record a RAG retrieval operation."""
        self._rag_hits.inc()
        self._rag_latency.observe(latency_seconds)
        self._rag_context_chars.observe(context_chars)
    
    def record_streaming_enabled(self) -> None:
        """Record that streaming was enabled for a request."""
        self._streaming_enabled_total.inc()
    
    def record_streaming_disabled(self, reason: str) -> None:
        """Record that streaming was disabled for a request with a reason."""
        self._streaming_disabled_total.labels(reason=reason).inc()
    
    def record_streaming_chunks(self, chunk_count: int) -> None:
        """Record the number of chunks in a streaming response."""
        self._streaming_chunks.observe(chunk_count)


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

    # Initialize RAG retriever if enabled
    app.state.rag_retriever = None
    if provider.settings.enable_rag:
        try:
            db_path = provider.settings.rag_db_path
            if Path(db_path).exists():
                logger.info(f"Initializing RAG retriever with database: {db_path}")
                vector_store = VectorStore(db_path)
                embedding_client = StubEmbeddingClient(dimension=128)
                app.state.rag_retriever = RAGRetriever(vector_store, embedding_client)
                logger.info(f"RAG enabled with {vector_store.count()} documents")
            else:
                logger.warning(
                    f"RAG enabled but knowledge base not found at {db_path}. "
                    "Run scripts/build_llm_knowledge_base.py to create it. "
                    "Continuing without RAG."
                )
        except Exception as e:
            logger.error(
                f"Failed to initialize RAG retriever: {e}. Continuing without RAG."
            )
            app.state.rag_retriever = None

    @app.get("/healthz")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        health = {
            "status": "ok",
            "provider": app.state.llm_settings.provider,
            "model": app.state.llm_settings.model or "N/A",
            "rag_enabled": app.state.llm_settings.enable_rag,
        }
        if app.state.rag_retriever:
            health["rag_documents"] = app.state.rag_retriever.vector_store.count()
        return health

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
            # Retrieve RAG context if enabled
            rag_context = ""
            if app.state.rag_retriever:
                rag_start = time.perf_counter()
                try:
                    retrieved_docs = await app.state.rag_retriever.retrieve(
                        request.user_input,
                        top_k=app.state.llm_settings.rag_top_k,
                        min_score=app.state.llm_settings.rag_min_score,
                    )
                    rag_context = format_retrieved_context(retrieved_docs)
                    rag_latency = time.perf_counter() - rag_start
                    metrics.record_rag_retrieval(rag_latency, len(rag_context))
                    logger.debug(
                        f"Retrieved {len(retrieved_docs)} documents "
                        f"({len(rag_context)} chars) in {rag_latency:.3f}s"
                    )
                    if app.state.llm_settings.verbose_logging:
                        _log_rag_details(
                            endpoint="parse_intent",
                            query=request.user_input,
                            documents=retrieved_docs,
                            context_chars=len(rag_context),
                        )
                except Exception as e:
                    logger.warning(
                        f"RAG retrieval failed: {e}. Continuing without context."
                    )

            # Augment context with RAG results
            enhanced_context = request.context.copy()
            if rag_context:
                enhanced_context["_rag_context"] = rag_context

            result = await app.state.llm_provider.parse_intent(
                request.user_input,
                enhanced_context,
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
        
        # Check if streaming should be enabled
        provider_supports_streaming = app.state.llm_provider.supports_streaming()
        streaming_enabled = (
            app.state.llm_settings.enable_streaming and provider_supports_streaming
        )
        
        # Emit telemetry about streaming decision
        if streaming_enabled:
            metrics.record_streaming_enabled()
            logger.debug("Streaming enabled for narrate request")
        else:
            if not app.state.llm_settings.enable_streaming:
                reason = "disabled_by_config"
                logger.info(
                    "Streaming disabled: configuration override "
                    "(--no-streaming or ECHOES_LLM_NO_STREAMING=true)"
                )
            elif not provider_supports_streaming:
                reason = "provider_unsupported"
                logger.info(
                    "Streaming disabled: provider '%s' does not support streaming",
                    app.state.llm_settings.provider
                )
            else:
                reason = "unknown"
            metrics.record_streaming_disabled(reason)
        
        try:
            # Retrieve RAG context if enabled
            rag_context = ""
            if app.state.rag_retriever:
                rag_start = time.perf_counter()
                try:
                    # Build query from events
                    event_summary = " ".join(
                        str(e.get("type", "")) for e in request.events
                    )
                    retrieved_docs = await app.state.rag_retriever.retrieve(
                        event_summary,
                        top_k=app.state.llm_settings.rag_top_k,
                        min_score=app.state.llm_settings.rag_min_score,
                    )
                    rag_context = format_retrieved_context(retrieved_docs)
                    rag_latency = time.perf_counter() - rag_start
                    metrics.record_rag_retrieval(rag_latency, len(rag_context))
                    logger.debug(
                        f"Retrieved {len(retrieved_docs)} documents "
                        f"({len(rag_context)} chars) in {rag_latency:.3f}s"
                    )
                    if app.state.llm_settings.verbose_logging:
                        _log_rag_details(
                            endpoint="narrate",
                            query=event_summary,
                            documents=retrieved_docs,
                            context_chars=len(rag_context),
                        )
                except Exception as e:
                    logger.warning(
                        f"RAG retrieval failed: {e}. Continuing without context."
                    )

            # Augment context with RAG results
            enhanced_context = request.context.copy()
            if rag_context:
                enhanced_context["_rag_context"] = rag_context

            result = await app.state.llm_provider.narrate(
                request.events,
                enhanced_context,
            )
            latency_seconds = time.perf_counter() - start_time
            
            # Record streaming chunk count if streaming was used
            if result.metadata and result.metadata.get("streaming"):
                chunk_count = result.metadata.get("chunk_count", 0)
                if chunk_count > 0:
                    metrics.record_streaming_chunks(chunk_count)
            
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
