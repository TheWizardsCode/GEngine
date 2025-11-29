"""Tests for the Echoes gateway service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gengine.echoes.gateway.app import GatewaySettings, create_gateway_app
from gengine.echoes.cli.shell import LocalBackend
from gengine.echoes.settings import load_simulation_config
from gengine.echoes.sim import SimEngine


def test_gateway_healthcheck() -> None:
    config = load_simulation_config()
    settings = GatewaySettings(service_url="local")
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=settings,
    )
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service_url"] == "local"


def test_gateway_websocket_summary_and_exit() -> None:
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "welcome"
        assert "Current world summary" in welcome["output"]
        websocket.send_json({"command": "summary"})
        response = websocket.receive_json()
        assert response["type"] == "result"
        assert "Current world summary" in response["output"]
        websocket.send_json({"command": "exit"})
        final = websocket.receive_json()
        assert final["should_exit"] is True


def test_gateway_requires_command_payload() -> None:
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        websocket.send_text("{}")
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert "Command payload" in error["error"]
        websocket.close()


def test_gateway_handles_text_commands() -> None:
    """Verify that plain text commands are accepted by the gateway."""
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        websocket.send_text("summary")
        response = websocket.receive_json()
        assert response["type"] == "result"
        assert "Current world summary" in response["output"]
        websocket.send_text("exit")
        final = websocket.receive_json()
        assert final["should_exit"] is True


def test_gateway_handles_bytes_commands() -> None:
    """Verify that byte-encoded JSON commands are accepted."""
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        websocket.send_bytes(b'{"command": "summary"}')
        response = websocket.receive_json()
        assert response["type"] == "result"
        assert "Current world summary" in response["output"]
        websocket.send_bytes(b'{"command": "exit"}')
        final = websocket.receive_json()
        assert final["should_exit"] is True


def test_gateway_executes_multiple_commands() -> None:
    """Verify that the gateway can execute a sequence of commands."""
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        
        websocket.send_json({"command": "summary"})
        result1 = websocket.receive_json()
        assert result1["type"] == "result"
        assert "Current world summary" in result1["output"]
        
        websocket.send_json({"command": "next"})
        result2 = websocket.receive_json()
        assert result2["type"] == "result"
        assert "Tick" in result2["output"]
        
        websocket.send_json({"command": "exit"})
        final = websocket.receive_json()
        assert final["should_exit"] is True


def test_gateway_handles_empty_string_command() -> None:
    """Verify that empty string commands are handled gracefully."""
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        websocket.send_text("")
        response = websocket.receive_json()
        # Empty command should execute as empty string
        assert response["type"] == "result"
        websocket.send_text("exit")
        final = websocket.receive_json()
        assert final["should_exit"] is True


def test_gateway_settings_from_env() -> None:
    """Verify that GatewaySettings.from_env() reads environment variables."""
    import os
    old_env = {
        "ECHOES_GATEWAY_SERVICE_URL": os.environ.get("ECHOES_GATEWAY_SERVICE_URL"),
        "ECHOES_GATEWAY_HOST": os.environ.get("ECHOES_GATEWAY_HOST"),
        "ECHOES_GATEWAY_PORT": os.environ.get("ECHOES_GATEWAY_PORT"),
    }
    try:
        os.environ["ECHOES_GATEWAY_SERVICE_URL"] = "http://test:9000"
        os.environ["ECHOES_GATEWAY_HOST"] = "127.0.0.1"
        os.environ["ECHOES_GATEWAY_PORT"] = "9100"
        
        settings = GatewaySettings.from_env()
        assert settings.service_url == "http://test:9000"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9100
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_gateway_app_uses_service_backend_factory_by_default() -> None:
    """Verify that create_gateway_app creates service backend factory when none provided."""
    config = load_simulation_config()
    settings = GatewaySettings(service_url="http://localhost:8000")
    # Call without backend_factory to trigger the default factory creation
    app = create_gateway_app(config=config, settings=settings)
    assert app is not None
    assert hasattr(app.state, "gateway_settings")
    assert app.state.gateway_settings.service_url == "http://localhost:8000"


def test_gateway_handles_invalid_json_bytes() -> None:
    """Verify that invalid JSON bytes are handled gracefully."""
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        # Send invalid JSON as bytes
        websocket.send_bytes(b'not valid json')
        response = websocket.receive_json()
        assert response["type"] == "result"
        websocket.send_text("exit")
        final = websocket.receive_json()
        assert final["should_exit"] is True


def test_gateway_handles_non_dict_json() -> None:
    """Verify that non-dict JSON payloads are handled gracefully."""
    config = load_simulation_config()
    app = create_gateway_app(
        backend_factory=_local_backend_factory(config),
        config=config,
        settings=GatewaySettings(service_url="local"),
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        # Send JSON array instead of object
        websocket.send_bytes(b'["not", "a", "dict"]')
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "Command payload" in response["error"]
        websocket.close()


def _local_backend_factory(config):
    def _factory() -> LocalBackend:
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")
        return LocalBackend(engine)

    return _factory
