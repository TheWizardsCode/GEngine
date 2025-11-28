"""Tests for the typed HTTP client interacting with the service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gengine.echoes.client import SimServiceClient
from gengine.echoes.service import create_app
from gengine.echoes.sim import SimEngine


def build_client() -> SimServiceClient:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    http_client = TestClient(app)
    return SimServiceClient(base_url="http://testserver", client=http_client)


def test_client_tick_round_trip() -> None:
    client = build_client()

    payload = client.tick(1)

    assert payload["ticks_advanced"] == 1
    client.close()


def test_client_state_and_metrics() -> None:
    client = build_client()

    summary = client.state("summary")
    metrics = client.metrics()

    assert "data" in summary
    assert "environment" in metrics
    client.close()


def test_client_submit_actions() -> None:
    client = build_client()

    response = client.submit_actions([{ "intent": "noop" }])

    assert response["results"][0]["status"] == "noop"
    client.close()


def test_client_focus_helpers() -> None:
    client = build_client()

    focus_state = client.focus_state()
    assert "focus" in focus_state
    assert "history" in focus_state

    district_id = focus_state["focus"].get("district_id")
    update = client.set_focus(district_id)
    assert update["focus"]["district_id"] == district_id
    client.close()


def test_client_context_manager_closes_default() -> None:
    with SimServiceClient("http://example.com") as client:
        assert isinstance(client, SimServiceClient)
