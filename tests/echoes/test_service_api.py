"""Tests for the FastAPI simulation service (Phase 3, M3.2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gengine.echoes.service import create_app
from gengine.echoes.sim import SimEngine


def _client() -> tuple[TestClient, SimEngine]:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    return TestClient(app), engine


def test_tick_endpoint_advances_state() -> None:
    client, engine = _client()

    response = client.post("/tick", json={"ticks": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["ticks_advanced"] == 2
    assert engine.state.tick == 2
    first_report = body["reports"][0]
    assert first_report["agent_actions"]
    assert "faction_actions" in first_report
    assert "faction_legitimacy" in first_report
    assert "faction_legitimacy_delta" in first_report
    assert "economy" in first_report
    assert "environment_impact" in first_report
    assert "timings" in first_report
    assert "anomalies" in first_report
    assert "director_analysis" in first_report
    assert "director_events" in first_report


def test_state_endpoint_requires_district_id() -> None:
    client, _ = _client()

    response = client.get("/state", params={"detail": "district"})

    assert response.status_code == 400


def test_state_endpoint_returns_summary() -> None:
    client, _ = _client()

    response = client.get("/state", params={"detail": "summary"})

    assert response.status_code == 200
    assert "data" in response.json()


def test_state_endpoint_returns_post_mortem() -> None:
    client, engine = _client()
    engine.advance_ticks(5)

    response = client.get("/state", params={"detail": "post-mortem"})

    assert response.status_code == 200
    payload = response.json()["data"]
    expected_keys = {
        "tick",
        "environment",
        "environment_trend",
        "faction_trends",
        "featured_events",
        "story_seeds",
        "notes",
    }
    assert expected_keys <= payload.keys()
    assert payload["environment"]
    assert set(payload["environment_trend"]["delta"]) == {"stability", "unrest", "pollution"}
    assert isinstance(payload["faction_trends"], list)
    assert isinstance(payload["featured_events"], list)
    assert isinstance(payload["story_seeds"], list)
    assert isinstance(payload["notes"], list)


def test_actions_endpoint_returns_receipts() -> None:
    client, _ = _client()

    response = client.post("/actions", json={"actions": [{"intent": "noop"}]})

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"]
    assert payload["results"][0]["status"] == "noop"


def test_metrics_endpoint_reports_environment() -> None:
    client, engine = _client()
    engine.advance_ticks(1)

    response = client.get("/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tick"] == engine.state.tick
    assert "environment" in payload
    assert payload["profiling"]
    assert "slowest_subsystem" in payload["profiling"]


def test_tick_endpoint_rejects_large_requests() -> None:
    client, _ = _client()

    response = client.post("/tick", json={"ticks": 500})

    assert response.status_code == 400
    assert "limit" in response.json()["detail"]


def test_focus_endpoint_reports_state_and_validates() -> None:
    client, _ = _client()

    state_response = client.get("/focus")
    assert state_response.status_code == 200
    payload = state_response.json()
    assert payload["focus"]["district_id"]
    assert isinstance(payload.get("history"), list)

    bad_response = client.post("/focus", json={"district_id": "unknown"})
    assert bad_response.status_code == 400

    good_response = client.post("/focus", json={"district_id": payload["focus"]["district_id"]})
    assert good_response.status_code == 200
    assert "history" in good_response.json()
