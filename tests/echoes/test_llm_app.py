"""Tests for LLM service FastAPI app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gengine.echoes.llm.app import create_llm_app, LLMMetrics
from gengine.echoes.llm.settings import LLMSettings


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
        """Verify that /metrics endpoint returns expected structure."""
        settings = LLMSettings(provider="stub")
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        
        # Check service identification
        assert data["service"] == "llm"
        
        # Check requests section
        assert "requests" in data
        assert data["requests"]["total"] == 0
        assert data["requests"]["parse_intent"] == 0
        assert data["requests"]["narrate"] == 0
        
        # Check errors section
        assert "errors" in data
        assert data["errors"]["total"] == 0
        
        # Check latency section
        assert "latency_ms" in data
        assert "parse_intent" in data["latency_ms"]
        assert "narrate" in data["latency_ms"]
        
        # Check provider section
        assert "provider" in data
        assert data["provider"]["name"] == "stub"
        
        # Check token usage section
        assert "token_usage" in data

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
        data = response.json()
        
        assert data["requests"]["total"] == 1
        assert data["requests"]["parse_intent"] == 1
        assert data["latency_ms"]["parse_intent"]["avg"] > 0

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
        data = response.json()
        
        assert data["requests"]["total"] == 1
        assert data["requests"]["narrate"] == 1
        assert data["latency_ms"]["narrate"]["avg"] > 0

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
    """Tests for LLMMetrics class."""

    def test_initial_state(self) -> None:
        """Metrics start at zero."""
        metrics = LLMMetrics()
        assert metrics.total_requests == 0
        assert metrics.total_errors == 0
        assert metrics.parse_intent_requests == 0
        assert metrics.narrate_requests == 0

    def test_record_parse_intent(self) -> None:
        """Recording a parse_intent request increments counters."""
        metrics = LLMMetrics()
        metrics.record_parse_intent(50.0, input_tokens=100, output_tokens=50)
        
        assert metrics.total_requests == 1
        assert metrics.parse_intent_requests == 1
        assert len(metrics.parse_intent_latencies) == 1
        assert metrics.total_input_tokens == 100
        assert metrics.total_output_tokens == 50

    def test_record_narrate(self) -> None:
        """Recording a narrate request increments counters."""
        metrics = LLMMetrics()
        metrics.record_narrate(75.0, input_tokens=200, output_tokens=100)
        
        assert metrics.total_requests == 1
        assert metrics.narrate_requests == 1
        assert len(metrics.narrate_latencies) == 1
        assert metrics.total_input_tokens == 200
        assert metrics.total_output_tokens == 100

    def test_record_error(self) -> None:
        """Recording an error increments error counters."""
        metrics = LLMMetrics()
        metrics.record_error("parse_intent", "ValueError")
        
        assert metrics.total_errors == 1
        assert metrics.parse_intent_errors == 1
        assert metrics.errors_by_type["parse_intent:ValueError"] == 1

    def test_latency_stats_empty(self) -> None:
        """Empty latencies return zeros."""
        metrics = LLMMetrics()
        data = metrics.to_dict()
        
        assert data["latency_ms"]["parse_intent"]["avg"] == 0.0
        assert data["latency_ms"]["narrate"]["avg"] == 0.0

    def test_latency_stats_calculated(self) -> None:
        """Latency statistics are calculated correctly."""
        metrics = LLMMetrics()
        for i in range(10):
            metrics.record_parse_intent(float(i * 10))
        
        data = metrics.to_dict()
        assert data["latency_ms"]["parse_intent"]["min"] == 0.0
        assert data["latency_ms"]["parse_intent"]["max"] == 90.0
        assert data["latency_ms"]["parse_intent"]["avg"] == 45.0

    def test_to_dict_structure(self) -> None:
        """to_dict returns expected structure."""
        metrics = LLMMetrics()
        metrics.record_parse_intent(50.0)
        metrics.record_error("parse_intent", "TestError")
        
        data = metrics.to_dict(provider="openai", model="gpt-4")
        
        assert "requests" in data
        assert "errors" in data
        assert "latency_ms" in data
        assert "provider" in data
        assert "token_usage" in data
        assert data["provider"]["name"] == "openai"
        assert data["provider"]["model"] == "gpt-4"
