"""FastAPI Gateway that proxies CLI sessions to the simulation service."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from ..cli.shell import PROMPT, ServiceBackend, ShellBackend
from ..client import SimServiceClient
from ..settings import SimulationConfig, load_simulation_config
from .llm_client import LLMClient
from .session import GatewaySession

LOGGER = logging.getLogger("gengine.echoes.gateway")
BackendFactory = Callable[[], ShellBackend]


@dataclass
class GatewayMetrics:
    """Metrics tracking for the gateway service.
    
    Note on message counters:
    - websocket_messages: All messages received via WebSocket (including invalid)
    - natural_language_requests: Valid natural language commands executed
    - command_requests: Valid regular commands executed
    
    The sum of natural_language_requests + command_requests will be <= websocket_messages
    since invalid messages are counted in websocket_messages but not the request counters.
    """

    # Request counts
    total_requests: int = 0
    requests_by_type: dict[str, int] = field(default_factory=dict)
    websocket_messages: int = 0  # All messages received (including invalid)
    natural_language_requests: int = 0  # Valid NL commands processed
    command_requests: int = 0  # Valid regular commands processed

    # Error tracking
    total_errors: int = 0
    errors_by_type: dict[str, int] = field(default_factory=dict)

    # Latency tracking (in ms)
    latencies: list[float] = field(default_factory=list)
    max_latency_samples: int = 1000

    # Connection tracking
    active_connections: int = 0
    total_connections: int = 0
    total_disconnections: int = 0

    # LLM integration stats
    llm_requests: int = 0
    llm_errors: int = 0
    llm_latencies: list[float] = field(default_factory=list)

    def record_request(self, request_type: str, latency_ms: float) -> None:
        """Record a request with its type and latency."""
        self.total_requests += 1
        self.requests_by_type[request_type] = self.requests_by_type.get(request_type, 0) + 1
        self._add_latency(latency_ms)

    def record_error(self, error_type: str) -> None:
        """Record an error by type."""
        self.total_errors += 1
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

    def record_llm_request(self, latency_ms: float) -> None:
        """Record an LLM service request."""
        self.llm_requests += 1
        if len(self.llm_latencies) >= self.max_latency_samples:
            self.llm_latencies.pop(0)
        self.llm_latencies.append(latency_ms)

    def record_llm_error(self) -> None:
        """Record an LLM service error."""
        self.llm_errors += 1

    def _add_latency(self, latency_ms: float) -> None:
        """Add latency sample, maintaining max samples."""
        if len(self.latencies) >= self.max_latency_samples:
            self.latencies.pop(0)
        self.latencies.append(latency_ms)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        latency_stats = self._calculate_latency_stats(self.latencies)
        llm_latency_stats = self._calculate_latency_stats(self.llm_latencies)

        return {
            "requests": {
                "total": self.total_requests,
                "by_type": dict(self.requests_by_type),
                "websocket_messages": self.websocket_messages,  # All messages (including invalid)
                "natural_language": self.natural_language_requests,  # Valid NL commands
                "commands": self.command_requests,  # Valid regular commands
            },
            "errors": {
                "total": self.total_errors,
                "by_type": dict(self.errors_by_type),
            },
            "latency_ms": latency_stats,
            "connections": {
                "active": self.active_connections,
                "total": self.total_connections,
                "disconnections": self.total_disconnections,
            },
            "llm_integration": {
                "requests": self.llm_requests,
                "errors": self.llm_errors,
                "latency_ms": llm_latency_stats,
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
            service_url=os.environ.get(
                "ECHOES_GATEWAY_SERVICE_URL", "http://localhost:8000"
            ),
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
    def healthcheck() -> dict[str, str]:  # pragma: no cover - trivial
        health = {
            "status": "ok",
            "service_url": active_settings.service_url,
        }
        if active_settings.llm_service_url:
            health["llm_service_url"] = active_settings.llm_service_url
        return health

    @app.get("/metrics")
    def get_metrics() -> dict[str, Any]:
        """Return gateway metrics for Prometheus scraping."""
        return {
            "service": "gateway",
            "service_url": active_settings.service_url,
            "llm_service_url": active_settings.llm_service_url,
            **metrics.to_dict(),
        }

    @app.websocket("/ws")
    async def websocket_handler(websocket: WebSocket) -> None:
        await websocket.accept()
        metrics.active_connections += 1
        metrics.total_connections += 1
        try:
            session = manager.open_session()
        except Exception as exc:  # pragma: no cover - catastrophic setup failure
            LOGGER.exception("Gateway failed to open session: %s", exc)
            metrics.record_error("session_open_failed")
            await websocket.send_json({"type": "error", "error": str(exc)})
            await websocket.close()
            metrics.active_connections -= 1
            metrics.total_disconnections += 1
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
                metrics.websocket_messages += 1
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
<<<<<<< HEAD
                
                start_time = time.perf_counter()
                try:
                    if is_nl and session.llm_client:
                        metrics.natural_language_requests += 1
                        llm_start = time.perf_counter()
                        result = await asyncio.to_thread(session.execute_natural_language, command)
                        llm_latency = (time.perf_counter() - llm_start) * 1000
                        metrics.record_llm_request(llm_latency)
=======

                try:
                    if is_nl and session.llm_client:
                        result = await asyncio.to_thread(
                            session.execute_natural_language, command
                        )
>>>>>>> origin/main
                    else:
                        metrics.command_requests += 1
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
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                request_type = "natural_language" if is_nl else "command"
                metrics.record_request(request_type, latency_ms)
                
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
            metrics.active_connections -= 1
            metrics.total_disconnections += 1
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
<<<<<<< HEAD
                if self._metrics:
                    self._metrics.record_llm_error()
        return GatewaySession(backend, limits=self._config.limits, llm_client=llm_client)
=======
        return GatewaySession(
            backend, limits=self._config.limits, llm_client=llm_client
        )
>>>>>>> origin/main


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
            return {
                "command": payload.decode("utf-8", errors="ignore"),
                "natural_language": False,
            }

    if isinstance(data, dict):
        command = data.get("command")
        if isinstance(command, str):
            is_nl = data.get("natural_language", False)
            return {"command": command, "natural_language": bool(is_nl)}

    return None
