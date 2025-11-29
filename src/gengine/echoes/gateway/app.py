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

from ..cli.shell import PROMPT, ShellBackend, ServiceBackend
from ..client import SimServiceClient
from ..settings import SimulationConfig, load_simulation_config
from .llm_client import LLMClient
from .session import GatewaySession

LOGGER = logging.getLogger("gengine.echoes.gateway")
BackendFactory = Callable[[], ShellBackend]


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

    active_config = config or load_simulation_config()
    active_settings = settings or GatewaySettings.from_env()

    if backend_factory is None:
        backend_factory = _service_backend_factory(active_settings.service_url)

    app = FastAPI(title="Echoes Gateway Service", version="0.1.0")
    manager = _GatewayManager(
        backend_factory,
        active_config,
        llm_service_url=active_settings.llm_service_url,
    )
    app.state.gateway_settings = active_settings

    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:  # pragma: no cover - trivial
        health = {
            "status": "ok",
            "service_url": active_settings.service_url,
        }
        if active_settings.llm_service_url:
            health["llm_service_url"] = active_settings.llm_service_url
        return health

    @app.websocket("/ws")
    async def websocket_handler(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            session = manager.open_session()
        except Exception as exc:  # pragma: no cover - catastrophic setup failure
            LOGGER.exception("Gateway failed to open session: %s", exc)
            await websocket.send_json({"type": "error", "error": str(exc)})
            await websocket.close()
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
                if message_data is None:
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
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": "Command field required.",
                        }
                    )
                    continue
                
                try:
                    if is_nl and session.llm_client:
                        result = await asyncio.to_thread(session.execute_natural_language, command)
                    else:
                        result = await asyncio.to_thread(session.execute, command)
                except Exception as exc:  # pragma: no cover - unexpected failure
                    LOGGER.exception("Gateway session crashed: %s", exc)
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": str(exc),
                        }
                    )
                    continue
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
    ) -> None:
        self._backend_factory = backend_factory
        self._config = config
        self._llm_service_url = llm_service_url

    def open_session(self) -> GatewaySession:
        backend = self._backend_factory()
        llm_client = None
        if self._llm_service_url:
            llm_client = LLMClient(self._llm_service_url)
            # Check LLM service health
            if not llm_client.healthcheck():
                LOGGER.warning("LLM service unhealthy at %s", self._llm_service_url)
        return GatewaySession(backend, limits=self._config.limits, llm_client=llm_client)


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
            return {"command": payload.decode("utf-8", errors="ignore"), "natural_language": False}
    
    if isinstance(data, dict):
        command = data.get("command")
        if isinstance(command, str):
            is_nl = data.get("natural_language", False)
            return {"command": command, "natural_language": bool(is_nl)}
    
    return None
