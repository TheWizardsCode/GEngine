"""Tests for the FastAPI service launcher."""

from __future__ import annotations

from types import SimpleNamespace

from gengine.echoes.service import main as service_main


def test_service_main_loads_config_and_runs(monkeypatch) -> None:
    captured = {}
    fake_app = object()
    fake_config = object()

    def fake_create_app(*, auto_world: str, config):
        captured["world"] = auto_world
        captured["config"] = config
        return fake_app

    def fake_run(app, host: str, port: int):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setenv("ECHOES_SERVICE_HOST", "127.0.0.1")
    monkeypatch.setenv("ECHOES_SERVICE_PORT", "9000")
    monkeypatch.setenv("ECHOES_SERVICE_WORLD", "default")
    monkeypatch.setattr("gengine.echoes.service.main.create_app", fake_create_app)
    monkeypatch.setattr(
        "gengine.echoes.service.main.load_simulation_config",
        lambda: fake_config,
    )
    monkeypatch.setattr(
        "gengine.echoes.service.main.uvicorn",
        SimpleNamespace(run=fake_run),
    )

    service_main.main()

    assert captured["world"] == "default"
    assert captured["config"] is fake_config
    assert captured["app"] is fake_app
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 9000
