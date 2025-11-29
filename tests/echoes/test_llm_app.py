"""Tests for LLM service FastAPI app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gengine.echoes.llm.app import create_llm_app
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
