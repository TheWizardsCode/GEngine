"""Tests for LLM service FastAPI app."""

from __future__ import annotations

from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from gengine.echoes.llm.app import (
    LLMMetrics,
    create_llm_app,
)
from gengine.echoes.llm.settings import LLMSettings


def _parse_prometheus_metrics(text: str) -> dict[str, float]:
    """Parse Prometheus text format into a dict of metric name -> value."""
    metrics = {}
    for line in text.strip().split("\n"):
        if line.startswith("#") or not line:
            continue
        # Parse lines like "llm_requests_total 0.0"
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0]
            try:
                value = float(parts[-1])
                metrics[name] = value
            except ValueError:
                pass
    return metrics


class TestLLMApp:
    """Tests for LLM service FastAPI application."""

    def test_health_check(self) -> None:
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["provider"] == "stub"

    def test_metrics_endpoint(self) -> None:
        """Verify that /metrics endpoint returns Prometheus format."""
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Check content type is Prometheus text format
        assert "text/plain" in response.headers.get("content-type", "")
        
        # Parse Prometheus format
        metrics = _parse_prometheus_metrics(response.text)
        
        # Check key metrics exist
        assert "llm_requests_total" in metrics
        assert "llm_errors_total" in metrics

    def test_metrics_track_parse_intent(self) -> None:
        """Verify that parse_intent requests are tracked in metrics."""
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        client.post(
            "/parse_intent",
            json={"user_input": "check status", "context": {}},
        )

        response = client.get("/metrics")
        metrics = _parse_prometheus_metrics(response.text)
        
        assert metrics.get("llm_requests_total", 0) == 1
        assert metrics.get("llm_parse_intent_requests_total", 0) == 1

    def test_metrics_track_narrate(self) -> None:
        """Verify that narrate requests are tracked in metrics."""
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        client.post(
            "/narrate",
            json={"events": [{"type": "test"}], "context": {}},
        )

        response = client.get("/metrics")
        metrics = _parse_prometheus_metrics(response.text)
        
        assert metrics.get("llm_requests_total", 0) == 1
        assert metrics.get("llm_narrate_requests_total", 0) == 1

    def test_parse_intent_basic(self) -> None:
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/parse_intent",
            json={
                "user_input": "Check the status of the industrial district",
                "context": {"tick": 5},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "intents" in data
        assert len(data["intents"]) > 0
        assert data["intents"][0]["type"] == "inspect"
        assert "raw_response" in data
        assert data["confidence"] is not None

    def test_parse_intent_empty_context(self) -> None:
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/parse_intent",
            json={
                "user_input": "What's happening?",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "intents" in data

    def test_narrate_basic(self) -> None:
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/narrate",
            json={
                "events": [
                    {"type": "stability_drop", "district": "industrial-tier"},
                    {"type": "faction_action", "faction": "union_of_flux"},
                ],
                "context": {"tick": 10},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "narrative" in data
        assert "raw_response" in data
        assert "metadata" in data
        assert isinstance(data["narrative"], str)
        assert len(data["narrative"]) > 0

    def test_narrate_empty_events(self) -> None:
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/narrate",
            json={
                "events": [],
                "context": {},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "narrative" in data
        assert "equilibrium" in data["narrative"].lower()

    def test_app_stores_settings_in_state(self) -> None:
        settings = LLMSettings(
            provider="stub",
            temperature=0.5,
            max_tokens=500,
        )
        app = create_llm_app(settings=settings)

        assert hasattr(app.state, "llm_provider")
        assert hasattr(app.state, "llm_settings")
        assert app.state.llm_settings.provider == "stub"
        assert app.state.llm_settings.temperature == 0.5
        assert app.state.llm_settings.max_tokens == 500

    def test_parse_intent_validates_request(self) -> None:
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/parse_intent",
            json={},  # Missing user_input
        )

        assert response.status_code == 422  # Validation error

    def test_narrate_validates_request(self) -> None:
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/narrate",
            json={},  # Missing events
        )

        assert response.status_code == 422  # Validation error


class TestLLMMetrics:
    """Tests for LLMMetrics class with Prometheus."""

    def test_record_parse_intent(self) -> None:
        """Recording a parse_intent request increments counters."""
        metrics = LLMMetrics()
        metrics.record_parse_intent(
            0.050, input_tokens=100, output_tokens=50
        )  # 50ms in seconds
        
        output = generate_latest(metrics.registry).decode("utf-8")
        assert "llm_requests_total 1.0" in output
        assert "llm_parse_intent_requests_total 1.0" in output
        assert "llm_input_tokens_total 100.0" in output
        assert "llm_output_tokens_total 50.0" in output

    def test_record_narrate(self) -> None:
        """Recording a narrate request increments counters."""
        metrics = LLMMetrics()
        metrics.record_narrate(
            0.075, input_tokens=200, output_tokens=100
        )  # 75ms in seconds
        
        output = generate_latest(metrics.registry).decode("utf-8")
        assert "llm_requests_total 1.0" in output
        assert "llm_narrate_requests_total 1.0" in output
        assert "llm_input_tokens_total 200.0" in output
        assert "llm_output_tokens_total 100.0" in output

    def test_record_error(self) -> None:
        """Recording an error increments error counters."""
        metrics = LLMMetrics()
        metrics.record_error("parse_intent", "ValueError")
        
        output = generate_latest(metrics.registry).decode("utf-8")
        assert "llm_errors_total 1.0" in output
        assert "llm_parse_intent_errors_total 1.0" in output
        expected_metric = (
            'llm_errors_by_type_total{endpoint="parse_intent",error_type="ValueError"} '
            '1.0'
        )
        assert expected_metric in output

    def test_record_narrate_error(self) -> None:
        """Recording a narrate error increments narrate error counter."""
        metrics = LLMMetrics()
        metrics.record_error("narrate", "RuntimeError")
        
        output = generate_latest(metrics.registry).decode("utf-8")
        assert "llm_errors_total 1.0" in output
        assert "llm_narrate_errors_total 1.0" in output

    def test_registry_property(self) -> None:
        """Registry property returns the collector registry."""
        metrics = LLMMetrics()
        assert metrics.registry is not None
