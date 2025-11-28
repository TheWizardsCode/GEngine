"""Tests for the Echoes CLI shell helpers."""

from __future__ import annotations

from pathlib import Path

from gengine.echoes.cli import run_commands
from gengine.echoes.content import load_world_bundle
from gengine.echoes.cli.shell import EchoesShell
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
    shell = EchoesShell(engine)
    other_snapshot = tmp_path / "snap.json"
    shell.execute(f"save {other_snapshot}")

    response = shell.execute(f"load snapshot {other_snapshot}")

    assert "Loaded snapshot" in response.output
    assert shell.state.tick == 0