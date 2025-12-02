"""Tests for the Echoes gateway service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gengine.echoes.cli.shell import LocalBackend
from gengine.echoes.gateway.app import GatewaySettings, GatewayMetrics, create_gateway_app
from gengine.echoes.sim import SimEngine


def test_gateway_healthcheck(sim_config, gateway_settings) -> None:
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
    )
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service_url"] == "local"


def test_gateway_metrics_endpoint(sim_config, gateway_settings) -> None:
    """Verify that the /metrics endpoint returns expected structure."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
    )
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    
    # Check service identification
    assert data["service"] == "gateway"
    assert data["service_url"] == "local"
    
    # Check requests section
    assert "requests" in data
    assert data["requests"]["total"] == 0
    assert "by_type" in data["requests"]
    
    # Check errors section
    assert "errors" in data
    assert data["errors"]["total"] == 0
    
    # Check latency section
    assert "latency_ms" in data
    assert "avg" in data["latency_ms"]
    
    # Check connections section
    assert "connections" in data
    assert data["connections"]["active"] == 0
    
    # Check LLM integration section
    assert "llm_integration" in data


def test_gateway_metrics_track_websocket_connections(sim_config, gateway_settings) -> None:
    """Verify that WebSocket connections are tracked in metrics."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
    )
    client = TestClient(app)
    
    # Initial metrics
    response = client.get("/metrics")
    initial = response.json()
    assert initial["connections"]["total"] == 0
    
    # Connect and disconnect
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        websocket.send_json({"command": "exit"})
        _ = websocket.receive_json()
    
    # Check metrics after connection
    response = client.get("/metrics")
    data = response.json()
    assert data["connections"]["total"] == 1
    assert data["connections"]["disconnections"] == 1


def test_gateway_metrics_track_commands(sim_config, gateway_settings) -> None:
    """Verify that commands are tracked in metrics."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
    )
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        websocket.send_json({"command": "summary"})
        _ = websocket.receive_json()
        websocket.send_json({"command": "exit"})
        _ = websocket.receive_json()
    
    response = client.get("/metrics")
    data = response.json()
    
    # Should have recorded the "summary" command (exit is not counted because it exits)
    # Actually both are recorded
    assert data["requests"]["total"] >= 1
    assert data["requests"]["commands"] >= 1


def test_gateway_websocket_summary_and_exit(sim_config, gateway_settings) -> None:
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
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


def test_gateway_requires_command_payload(sim_config, gateway_settings) -> None:
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        websocket.send_text("{}")
        error = websocket.receive_json()
        assert error["type"] == "error"
        assert "Command payload" in error["error"]
        websocket.close()


def test_gateway_handles_text_commands(sim_config, gateway_settings) -> None:
    """Verify that plain text commands are accepted by the gateway."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
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


def test_gateway_handles_bytes_commands(sim_config, gateway_settings) -> None:
    """Verify that byte-encoded JSON commands are accepted."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
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


def test_gateway_executes_multiple_commands(sim_config, gateway_settings) -> None:
    """Verify that the gateway can execute a sequence of commands."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
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


def test_gateway_handles_empty_string_command(sim_config, gateway_settings) -> None:
    """Verify that empty string commands are handled gracefully."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
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


def test_gateway_app_uses_service_backend_factory_by_default(sim_config) -> None:
    """Verify that create_gateway_app creates service backend factory.

    Tests that the default factory is used when none is provided.
    """
    settings = GatewaySettings(service_url="http://localhost:8000")
    # Call without backend_factory to trigger the default factory creation
    app = create_gateway_app(config=sim_config, settings=settings)
    assert app is not None
    assert hasattr(app.state, "gateway_settings")
    assert app.state.gateway_settings.service_url == "http://localhost:8000"


def test_gateway_handles_invalid_json_bytes(sim_config, gateway_settings) -> None:
    """Verify that invalid JSON bytes are handled gracefully."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
    )
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        _ = websocket.receive_json()
        # Send invalid JSON as bytes
        websocket.send_bytes(b"not valid json")
        response = websocket.receive_json()
        assert response["type"] == "result"
        websocket.send_text("exit")
        final = websocket.receive_json()
        assert final["should_exit"] is True


def test_gateway_handles_non_dict_json(sim_config, gateway_settings) -> None:
    """Verify that non-dict JSON payloads are handled gracefully."""
    app = create_gateway_app(
        backend_factory=_local_backend_factory(sim_config),
        config=sim_config,
        settings=gateway_settings,
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


class TestGatewayMetrics:
    """Tests for GatewayMetrics class."""

    def test_initial_state(self) -> None:
        """Metrics start at zero."""
        metrics = GatewayMetrics()
        assert metrics.total_requests == 0
        assert metrics.total_errors == 0
        assert metrics.active_connections == 0

    def test_record_request(self) -> None:
        """Recording a request increments counters and stores latency."""
        metrics = GatewayMetrics()
        metrics.record_request("command", 50.0)
        
        assert metrics.total_requests == 1
        assert metrics.requests_by_type["command"] == 1
        assert len(metrics.latencies) == 1
        assert metrics.latencies[0] == 50.0

    def test_record_error(self) -> None:
        """Recording an error increments error counters."""
        metrics = GatewayMetrics()
        metrics.record_error("execution_error")
        
        assert metrics.total_errors == 1
        assert metrics.errors_by_type["execution_error"] == 1

    def test_record_llm_request(self) -> None:
        """Recording an LLM request tracks separately."""
        metrics = GatewayMetrics()
        metrics.record_llm_request(100.0)
        
        assert metrics.llm_requests == 1
        assert len(metrics.llm_latencies) == 1
        assert metrics.llm_latencies[0] == 100.0

    def test_latency_stats_empty(self) -> None:
        """Empty latencies return zeros."""
        metrics = GatewayMetrics()
        data = metrics.to_dict()
        
        assert data["latency_ms"]["avg"] == 0.0
        assert data["latency_ms"]["min"] == 0.0
        assert data["latency_ms"]["max"] == 0.0

    def test_latency_stats_calculated(self) -> None:
        """Latency statistics are calculated correctly."""
        metrics = GatewayMetrics()
        for i in range(10):
            metrics.record_request("test", float(i * 10))
        
        data = metrics.to_dict()
        assert data["latency_ms"]["min"] == 0.0
        assert data["latency_ms"]["max"] == 90.0
        assert data["latency_ms"]["avg"] == 45.0

    def test_to_dict_structure(self) -> None:
        """to_dict returns expected structure."""
        metrics = GatewayMetrics()
        metrics.record_request("command", 50.0)
        metrics.record_error("test_error")
        metrics.active_connections = 2
        
        data = metrics.to_dict()
        
        assert "requests" in data
        assert "errors" in data
        assert "latency_ms" in data
        assert "connections" in data
        assert "llm_integration" in data
        assert data["connections"]["active"] == 2
