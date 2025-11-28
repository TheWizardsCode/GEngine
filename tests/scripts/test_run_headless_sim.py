"""Tests for the headless simulation driver."""

from __future__ import annotations

import json
from importlib import util
from pathlib import Path
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_headless_sim.py"


def _load_headless_module():
    spec = util.spec_from_file_location("headless_driver", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("headless_driver", module)
    spec.loader.exec_module(module)
    return module


_driver = _load_headless_module()
headless_main = _driver.main
run_headless_sim = _driver.run_headless_sim


@pytest.fixture()
def minimal_config(tmp_path: Path) -> Path:
    config_root = tmp_path / "config"
    config_root.mkdir()
    (config_root / "simulation.yml").write_text(
        "limits:\n  engine_max_ticks: 2\n  cli_run_cap: 2\n  cli_script_command_cap: 5\n  service_tick_cap: 2\n"
        "lod:\n  mode: balanced\n  max_events_per_tick: 4\n  volatility_scale:\n    detailed: 1.0\n    balanced: 0.8\n    coarse: 0.5\nprofiling:\n  log_ticks: false\n"
        "  history_window: 5\n  capture_subsystems: true\n"
    )
    return config_root


def test_run_headless_sim_supports_batches(tmp_path: Path, minimal_config: Path) -> None:
    output = tmp_path / "report.json"

    summary = run_headless_sim(
        ticks=5,
        config_root=minimal_config,
        output=output,
    )

    assert summary["ticks_executed"] == 5
    assert summary["batches"][-1]["ending_tick"] == summary["end_tick"]
    assert summary["agent_actions"] >= 1
    assert summary["faction_actions"] >= 0
    assert "last_environment" in summary
    assert "faction_legitimacy" in summary
    assert "last_economy" in summary
    assert "profiling" in summary
    assert "anomalies" in summary
    assert isinstance(summary["anomaly_examples"], list)
    assert "suppressed_events" in summary
    assert "last_event_digest" in summary
    assert "ranked_archive" in summary["last_event_digest"]
    for batch in summary["batches"]:
        assert batch["ticks"] <= 2
        assert "tick_ms" in batch
        assert "slowest_subsystem" in batch
        assert "anomalies" in batch
    data = json.loads(output.read_text())
    assert data["ticks_requested"] == 5
    assert "agent_intent_breakdown" in data
    assert "faction_action_breakdown" in data
    assert "last_economy" in data
    assert "anomaly_examples" in data
    assert "suppressed_events" in data
    assert "last_event_digest" in data
    assert "ranked_archive" in data["last_event_digest"]


def test_headless_cli_entrypoint(monkeypatch, capsys, minimal_config: Path, tmp_path: Path) -> None:
    output = tmp_path / "batch.json"
    exit_code = headless_main(
        [
            "--world",
            "default",
            "--ticks",
            "1",
            "--config-root",
            str(minimal_config),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "\"ticks_requested\": 1" in captured.out
    assert output.exists()
    saved = json.loads(output.read_text())
    assert "agent_actions" in saved
    assert "faction_actions" in saved
    assert "last_economy" in saved
    assert "last_event_digest" in saved
    assert "ranked_archive" in saved["last_event_digest"]