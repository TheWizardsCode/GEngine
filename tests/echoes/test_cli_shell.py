"""Tests for the Echoes CLI shell helpers."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from gengine.echoes.cli import run_commands
from gengine.echoes.cli.shell import (
    EchoesShell,
    LocalBackend,
    ServiceBackend,
    main as cli_main,
)
from gengine.echoes.client import SimServiceClient
from gengine.echoes.content import load_world_bundle
from gengine.echoes.service import create_app
from gengine.echoes.sim import SimEngine


def test_run_commands_executes_sequence(tmp_path: Path) -> None:
    out = run_commands(
        [
            "summary",
            "next",
            "run 2",
            "map",
            f"save {tmp_path / 'state.json'}",
            "exit",
        ]
    )

    assert "Current world summary" in out[0]
    assert "Tick" in out[1]
    assert (tmp_path / "state.json").exists()
    assert "City overview" in out[3]
    assert "industrial-tier" in out[3]
    assert out[-1] == "Exiting shell."


def test_shell_load_switches_world(tmp_path: Path) -> None:
    state = load_world_bundle()
    engine = SimEngine(state=state)
    backend = LocalBackend(engine)
    shell = EchoesShell(backend)
    other_snapshot = tmp_path / "snap.json"
    shell.execute(f"save {other_snapshot}")

    response = shell.execute(f"load snapshot {other_snapshot}")

    assert "Loaded snapshot" in response.output
    assert engine.state.tick == 0


def test_shell_service_backend_reports_summary() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    test_client = TestClient(app)
    client = SimServiceClient(base_url="http://testserver", client=test_client)
    backend = ServiceBackend(client)
    shell = EchoesShell(backend)

    summary = shell.execute("summary")
    assert "Current world summary" in summary.output

    map_output = shell.execute("map")
    assert "City overview" in map_output.output

    load_result = shell.execute("load world default")
    assert "requires local backend" in load_result.output

    client.close()


def test_local_backend_save_and_load(tmp_path: Path) -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    backend = LocalBackend(engine)
    snapshot_path = tmp_path / "local.json"

    save_msg = backend.save_snapshot(snapshot_path)
    assert snapshot_path.exists()
    assert "Saved snapshot" in save_msg

    world_msg = backend.load_world("default")
    assert "Loaded world" in world_msg

    snap_msg = backend.load_snapshot(snapshot_path)
    assert "Loaded snapshot" in snap_msg


def test_service_backend_map_and_save(tmp_path: Path) -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    test_client = TestClient(app)
    client = SimServiceClient(base_url="http://testserver", client=test_client)
    backend = ServiceBackend(client)

    city_view = backend.render_map(None)
    assert "City overview" in city_view

    first_id = engine.state.city.districts[0].id
    district_view = backend.render_map(first_id)
    assert engine.state.city.districts[0].name in district_view

    snapshot_path = tmp_path / "remote.json"
    backend.save_snapshot(snapshot_path)
    payload = json.loads(snapshot_path.read_text())
    assert payload["tick"] == 0

    with pytest.raises(NotImplementedError):
        backend.load_world("default")
    with pytest.raises(NotImplementedError):
        backend.load_snapshot(snapshot_path)

    client.close()


def test_cli_main_script_local(capsys) -> None:
    exit_code = cli_main(["--world", "default", "--script", "summary;exit"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Current world summary" in captured.out


def test_cli_main_script_service(monkeypatch, capsys) -> None:
    base_state = load_world_bundle()
    summary = base_state.summary()
    snapshot = base_state.snapshot()
    district = base_state.city.districts[0]
    district_panel = {
        "id": district.id,
        "name": district.name,
        "population": district.population,
        "modifiers": district.modifiers.model_dump(),
    }

    class FakeClient:
        close_called = False

        def __init__(self, url: str) -> None:  # pragma: no cover - simple stub
            self._tick = base_state.tick

        def state(self, detail: str = "summary", district_id: str | None = None):
            if detail == "summary":
                return {"data": summary}
            if detail == "snapshot":
                return {"data": snapshot}
            if detail == "district":
                return {"data": district_panel}
            raise ValueError(detail)

        def tick(self, count: int) -> dict[str, object]:
            self._tick += count
            report = {
                "tick": self._tick,
                "events": [],
                "environment": {
                    "stability": 0.5,
                    "unrest": 0.5,
                    "pollution": 0.5,
                    "climate_risk": 0.5,
                    "security": 0.5,
                },
                "districts": [],
            }
            return {"reports": [report]}

        def close(self) -> None:
            FakeClient.close_called = True

    monkeypatch.setattr("gengine.echoes.cli.shell.SimServiceClient", FakeClient)

    exit_code = cli_main(["--service-url", "http://fake", "--script", "summary;run 1;exit"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Current world summary" in captured.out
    assert FakeClient.close_called


def test_shell_help_and_error_paths() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    shell = EchoesShell(LocalBackend(engine))

    assert "Available commands" in shell.execute("help").output
    assert "Usage: next" in shell.execute("next 2").output
    assert "Usage: run <count>" in shell.execute("run").output
    assert "Unknown district" in shell.execute("map nowhere").output
    assert "Usage: save" in shell.execute("save").output
    assert "Usage" in shell.execute("load").output
    assert "Unknown command" in shell.execute("foobar").output


def test_run_commands_with_service_backend() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    client = SimServiceClient(base_url="http://testserver", client=TestClient(app))
    backend = ServiceBackend(client)

    outputs = run_commands(["summary", "exit"], backend=backend)

    assert "Current world summary" in outputs[0]
    client.close()


def test_cli_main_interactive(monkeypatch, capsys) -> None:
    inputs = iter(["help", "exit"])

    def fake_input(_: str) -> str:
        try:
            return next(inputs)
        except StopIteration:  # pragma: no cover - defensive
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)

    exit_code = cli_main(["--world", "default"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Available commands" in captured.out