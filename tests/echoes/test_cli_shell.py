"""Tests for the Echoes CLI shell helpers."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gengine.echoes.cli import run_commands
from gengine.echoes.cli.shell import EchoesShell, LocalBackend, ServiceBackend
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