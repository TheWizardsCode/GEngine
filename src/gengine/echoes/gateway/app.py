"""FastAPI Gateway that proxies CLI sessions to the simulation service."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from dataclasses import dataclass
from typing import Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from ..cli.shell import PROMPT, ServiceBackend, ShellBackend
from ..client import SimServiceClient
from ..settings import SimulationConfig, load_simulation_config
from .llm_client import LLMClient
from .session import GatewaySession

LOGGER = logging.getLogger("gengine.echoes.gateway")
BackendFactory = Callable[[], ShellBackend]


class GatewayMetrics:
    """Prometheus metrics tracking for the gateway service.
    
    Note on message counters:
    - websocket_messages: All messages received via WebSocket (including invalid)
    - natural_language_requests: Valid natural language commands executed
    - command_requests: Valid regular commands executed
    
    The sum of natural_language_requests + command_requests will be
    <= websocket_messages since invalid messages are counted in
    websocket_messages but not the request counters.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        """Initialize Prometheus metrics with optional custom registry."""
        self._registry = registry or CollectorRegistry()
        
        # Request counters
        self._total_requests = Counter(
            "gateway_requests_total",
            "Total number of requests processed",
            registry=self._registry,
        )
        self._requests_by_type = Counter(
            "gateway_requests_by_type_total",
            "Requests by type",
            ["request_type"],
            registry=self._registry,
        )
        self._websocket_messages = Counter(
            "gateway_websocket_messages_total",
            "Total WebSocket messages received (including invalid)",
            registry=self._registry,
        )
        self._natural_language_requests = Counter(
            "gateway_natural_language_requests_total",
            "Valid natural language commands processed",
            registry=self._registry,
        )
        self._command_requests = Counter(
            "gateway_command_requests_total",
            "Valid regular commands processed",
            registry=self._registry,
        )

        # Error counters
        self._total_errors = Counter(
            "gateway_errors_total",
            "Total number of errors",
            registry=self._registry,
        )
        self._errors_by_type = Counter(
            "gateway_errors_by_type_total",
            "Errors by type",
            ["error_type"],
            registry=self._registry,
        )

        # Latency histogram (in seconds for Prometheus convention)
        self._request_latency = Histogram(
            "gateway_request_latency_seconds",
            "Request latency in seconds",
            ["request_type"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self._registry,
        )

        # Connection gauges
        self._active_connections = Gauge(
            "gateway_active_connections",
            "Number of active WebSocket connections",
            registry=self._registry,
        )
        self._total_connections = Counter(
            "gateway_connections_total",
            "Total number of WebSocket connections",
            registry=self._registry,
        )
        self._total_disconnections = Counter(
            "gateway_disconnections_total",
            "Total number of WebSocket disconnections",
            registry=self._registry,
        )

        # LLM integration metrics
        self._llm_requests = Counter(
            "gateway_llm_requests_total",
            "Total LLM service requests",
            registry=self._registry,
        )
        self._llm_errors = Counter(
            "gateway_llm_errors_total",
            "Total LLM service errors",
            registry=self._registry,
        )
        self._llm_latency = Histogram(
            "gateway_llm_latency_seconds",
            "LLM service request latency in seconds",
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
            registry=self._registry,
        )

    @property
    def registry(self) -> CollectorRegistry:
        """Return the Prometheus registry."""
        return self._registry

    def record_request(self, request_type: str, latency_seconds: float) -> None:
        """Record a request with its type and latency."""
        self._total_requests.inc()
        self._requests_by_type.labels(request_type=request_type).inc()
        self._request_latency.labels(request_type=request_type).observe(latency_seconds)

    def record_error(self, error_type: str) -> None:
        """Record an error by type."""
        self._total_errors.inc()
        self._errors_by_type.labels(error_type=error_type).inc()

    def record_websocket_message(self) -> None:
        """Record a WebSocket message received."""
        self._websocket_messages.inc()

    def record_natural_language_request(self) -> None:
        """Record a natural language request."""
        self._natural_language_requests.inc()

    def record_command_request(self) -> None:
        """Record a regular command request."""
        self._command_requests.inc()

    def record_llm_request(self, latency_seconds: float) -> None:
        """Record an LLM service request."""
        self._llm_requests.inc()
        self._llm_latency.observe(latency_seconds)

    def record_llm_error(self) -> None:
        """Record an LLM service error."""
        self._llm_errors.inc()

    def connection_opened(self) -> None:
        """Record a new connection."""
        self._active_connections.inc()
        self._total_connections.inc()

    def connection_closed(self) -> None:
        """Record a connection closure."""
        self._active_connections.dec()
        self._total_disconnections.inc()


@dataclass
class GatewaySettings:
    """Configuration for the gateway service."""

    service_url: str = "http://localhost:8000"
    llm_service_url: str | None = None
    host: str = "0.0.0.0"
    port: int = 8100

    @classmethod
    def from_env(cls) -> "GatewaySettings":
        return cls(
            service_url=os.environ.get("ECHOES_GATEWAY_SERVICE_URL", "http://localhost:8000"),
            llm_service_url=os.environ.get("ECHOES_GATEWAY_LLM_URL"),
            host=os.environ.get("ECHOES_GATEWAY_HOST", "0.0.0.0"),
            port=int(os.environ.get("ECHOES_GATEWAY_PORT", "8100")),
        )


def create_gateway_app(
    *,
    backend_factory: BackendFactory | None = None,
    config: SimulationConfig | None = None,
    settings: GatewaySettings | None = None,
) -> FastAPI:
    """Build the FastAPI application that fronts CLI sessions."""
    import time

    active_config = config or load_simulation_config()
    active_settings = settings or GatewaySettings.from_env()

    if backend_factory is None:
        backend_factory = _service_backend_factory(active_settings.service_url)

    app = FastAPI(title="Echoes Gateway Service", version="0.1.0")
    metrics = GatewayMetrics()
    manager = _GatewayManager(
        backend_factory,
        active_config,
        llm_service_url=active_settings.llm_service_url,
        metrics=metrics,
    )
    app.state.gateway_settings = active_settings
    app.state.gateway_metrics = metrics

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:  # pragma: no cover - trivial
        health = {
            "status": "ok",
            "service_url": active_settings.service_url,
        }
        if active_settings.llm_service_url:
            health["llm_service_url"] = active_settings.llm_service_url
        return health

    @app.get("/metrics")
    async def get_metrics() -> Response:
        """Return gateway metrics in Prometheus text format."""
        return Response(
            content=generate_latest(metrics.registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.websocket("/ws")
    async def websocket_handler(websocket: WebSocket) -> None:
        await websocket.accept()
        metrics.connection_opened()
        try:
            session = manager.open_session()
        except Exception as exc:  # pragma: no cover - catastrophic setup failure
            LOGGER.exception("Gateway failed to open session: %s", exc)
            metrics.record_error("session_open_failed")
            await websocket.send_json({"type": "error", "error": str(exc)})
            await websocket.close()
            metrics.connection_closed()
            return

        try:
            welcome = await asyncio.to_thread(session.welcome)
            await websocket.send_json(
                {
                    "type": "welcome",
                    "session": session.session_id,
                    "output": welcome,
                    "prompt": PROMPT,
                }
            )
            while True:
                try:
                    message_data = await _receive_message(websocket)
                except WebSocketDisconnect:
                    break
                metrics.record_websocket_message()
                if message_data is None:
                    metrics.record_error("invalid_payload")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": "Command payload required.",
                        }
                    )
                    continue
                
                # Check if this is a natural language command
                command = message_data.get("command")
                is_nl = message_data.get("natural_language", False)
                
                if command is None:
                    metrics.record_error("missing_command")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": "Command field required.",
                        }
                    )
                    continue
                
                start_time = time.perf_counter()
                try:
                    if is_nl and session.llm_client:
                        metrics.record_natural_language_request()
                        llm_start = time.perf_counter()
                        result = await asyncio.to_thread(
                            session.execute_natural_language, command
                        )
                        llm_latency = time.perf_counter() - llm_start
                        metrics.record_llm_request(llm_latency)
                    else:
                        metrics.record_command_request()
                        result = await asyncio.to_thread(session.execute, command)
                except Exception as exc:  # pragma: no cover - unexpected failure
                    LOGGER.exception("Gateway session crashed: %s", exc)
                    metrics.record_error("execution_error")
                    if is_nl:
                        metrics.record_llm_error()
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": str(exc),
                        }
                    )
                    continue
                
                latency_seconds = time.perf_counter() - start_time
                request_type = "natural_language" if is_nl else "command"
                metrics.record_request(request_type, latency_seconds)
                
                await websocket.send_json(
                    {
                        "type": "result",
                        "session": session.session_id,
                        "output": result.output,
                        "should_exit": result.should_exit,
                        "prompt": PROMPT,
                    }
                )
                if result.should_exit:
                    break
        except WebSocketDisconnect:
            LOGGER.info("Gateway session %s disconnected", session.session_id)
        finally:
            metrics.connection_closed()
            await asyncio.to_thread(session.close)
            with contextlib.suppress(WebSocketDisconnect):
                await websocket.close()

    return app


def _service_backend_factory(service_url: str) -> BackendFactory:
    def _factory() -> ShellBackend:
        client = SimServiceClient(service_url)
        return ServiceBackend(client)

    return _factory


class _GatewayManager:
    def __init__(
        self,
        backend_factory: BackendFactory,
        config: SimulationConfig,
        llm_service_url: str | None = None,
        metrics: GatewayMetrics | None = None,
    ) -> None:
        self._backend_factory = backend_factory
        self._config = config
        self._llm_service_url = llm_service_url
        self._metrics = metrics

    def open_session(self) -> GatewaySession:
        backend = self._backend_factory()
        llm_client = None
        if self._llm_service_url:
            llm_client = LLMClient(self._llm_service_url)
            # Check LLM service health
            if not llm_client.healthcheck():
                LOGGER.warning("LLM service unhealthy at %s", self._llm_service_url)
                if self._metrics:
                    self._metrics.record_llm_error()
        return GatewaySession(
            backend, limits=self._config.limits, llm_client=llm_client
        )


async def _receive_message(websocket: WebSocket) -> dict[str, str | bool] | None:
    """Receive and parse message from WebSocket.
    
    Returns dict with 'command' and optional 'natural_language' flag,
    or None if message is invalid.
    """
    try:
        message = await websocket.receive()
    except RuntimeError as exc:  # starlette raises RuntimeError after disconnect
        raise WebSocketDisconnect(code=1000) from exc
    
    text = message.get("text")
    data = None
    
    if text is not None:
        text = text.strip()
        if not text:
            return {"command": ""}
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Plain text command (backwards compatible)
            return {"command": text, "natural_language": False}
    else:
        payload = message.get("bytes")
        if payload is None:
            return None
        try:
            data = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Binary decoded as text command
            decoded = payload.decode("utf-8", errors="ignore")
            return {"command": decoded, "natural_language": False}
    
    if isinstance(data, dict):
        command = data.get("command")
        if isinstance(command, str):
            is_nl = data.get("natural_language", False)
            return {"command": command, "natural_language": bool(is_nl)}
    
    return None
