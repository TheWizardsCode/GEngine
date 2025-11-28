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


def test_state_endpoint_requires_district_id() -> None:
    client, _ = _client()

    response = client.get("/state", params={"detail": "district"})

    assert response.status_code == 400


def test_state_endpoint_returns_summary() -> None:
    client, _ = _client()

    response = client.get("/state", params={"detail": "summary"})

    assert response.status_code == 200
    assert "data" in response.json()


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


def test_tick_endpoint_rejects_large_requests() -> None:
    client, _ = _client()

    response = client.post("/tick", json={"ticks": 500})

    assert response.status_code == 400
    assert "limit" in response.json()["detail"]
