"""Tests for the difficulty sweep runner script."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "run_difficulty_sweeps.py"
)


def _load_sweep_module():
    spec = util.spec_from_file_location("sweep_driver", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("sweep_driver", module)
    spec.loader.exec_module(module)
    return module


_driver = _load_sweep_module()
run_difficulty_sweeps = _driver.run_difficulty_sweeps
main = _driver.main
DIFFICULTY_PRESETS = _driver.DIFFICULTY_PRESETS


@pytest.fixture()
def minimal_config(tmp_path: Path) -> Path:
    """Create minimal config for a single difficulty preset."""
    config_root = tmp_path / "config"
    config_root.mkdir()
    (config_root / "simulation.yml").write_text(
        "limits:\n"
        "  engine_max_ticks: 5\n"
        "  cli_run_cap: 5\n"
        "  cli_script_command_cap: 10\n"
        "  service_tick_cap: 5\n"
        "lod:\n"
        "  mode: balanced\n"
        "  max_events_per_tick: 4\n"
        "  volatility_scale:\n"
        "    detailed: 1.0\n"
        "    balanced: 0.8\n"
        "    coarse: 0.5\n"
        "profiling:\n"
        "  log_ticks: false\n"
        "  history_window: 5\n"
        "  capture_subsystems: true\n"
    )
    return config_root


@pytest.fixture()
def difficulty_configs(tmp_path: Path) -> Path:
    """Create test difficulty preset configs."""
    sweeps_dir = tmp_path / "content" / "config" / "sweeps"

    for preset in ["easy", "normal", "hard"]:
        preset_dir = sweeps_dir / f"difficulty-{preset}"
        preset_dir.mkdir(parents=True)
        (preset_dir / "simulation.yml").write_text(
            "limits:\n"
            "  engine_max_ticks: 3\n"
            "  cli_run_cap: 3\n"
            "  cli_script_command_cap: 5\n"
            "  service_tick_cap: 3\n"
            "lod:\n"
            "  mode: balanced\n"
            "  max_events_per_tick: 4\n"
            "  volatility_scale:\n"
            "    detailed: 1.0\n"
            "    balanced: 0.8\n"
            "    coarse: 0.5\n"
            "profiling:\n"
            "  log_ticks: false\n"
            "  history_window: 5\n"
            "  capture_subsystems: true\n"
        )

    return sweeps_dir.parent.parent.parent


def test_difficulty_presets_defined() -> None:
    """Verify that all difficulty presets are defined."""
    assert "tutorial" in DIFFICULTY_PRESETS
    assert "easy" in DIFFICULTY_PRESETS
    assert "normal" in DIFFICULTY_PRESETS
    assert "hard" in DIFFICULTY_PRESETS
    assert "brutal" in DIFFICULTY_PRESETS


def test_run_difficulty_sweeps_single_preset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test running a single preset sweep."""
    output_dir = tmp_path / "output"

    # Use the real config
    monkeypatch.chdir(Path(__file__).resolve().parents[2])

    results = run_difficulty_sweeps(
        ticks=5,
        seed=42,
        output_dir=output_dir,
        presets=["normal"],
        verbose=False,
    )

    assert "normal" in results
    assert results["normal"]["ticks_executed"] == 5
    assert "last_environment" in results["normal"]
    assert "sweep_metadata" in results["normal"]
    assert results["normal"]["sweep_metadata"]["preset"] == "normal"

    # Check output file was created
    output_file = output_dir / "difficulty-normal-sweep.json"
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["ticks_executed"] == 5


def test_run_difficulty_sweeps_multiple_presets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test running multiple preset sweeps."""
    output_dir = tmp_path / "output"

    monkeypatch.chdir(Path(__file__).resolve().parents[2])

    results = run_difficulty_sweeps(
        ticks=3,
        seed=42,
        output_dir=output_dir,
        presets=["easy", "hard"],
        verbose=False,
    )

    assert len(results) == 2
    assert "easy" in results
    assert "hard" in results

    # Verify both output files exist
    assert (output_dir / "difficulty-easy-sweep.json").exists()
    assert (output_dir / "difficulty-hard-sweep.json").exists()


def test_run_difficulty_sweeps_skips_missing_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing configs are skipped gracefully."""
    output_dir = tmp_path / "output"

    # Create a temp directory without configs
    fake_config_base = tmp_path / "content" / "config" / "sweeps"
    fake_config_base.mkdir(parents=True)

    monkeypatch.chdir(tmp_path)

    results = run_difficulty_sweeps(
        ticks=3,
        seed=42,
        output_dir=output_dir,
        presets=["nonexistent"],
        verbose=True,
    )

    assert len(results) == 0
    captured = capsys.readouterr()
    assert "[SKIP]" in captured.err


def test_sweep_main_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test CLI entry point."""
    output_dir = tmp_path / "output"

    monkeypatch.chdir(Path(__file__).resolve().parents[2])

    exit_code = main(
        [
            "--ticks",
            "3",
            "--seed",
            "42",
            "--output-dir",
            str(output_dir),
            "--preset",
            "normal",
            "--quiet",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DIFFICULTY SWEEP COMPARISON" in captured.out


def test_sweep_main_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test CLI with JSON output format."""
    output_dir = tmp_path / "output"

    monkeypatch.chdir(Path(__file__).resolve().parents[2])

    exit_code = main(
        [
            "--ticks",
            "3",
            "--seed",
            "42",
            "--output-dir",
            str(output_dir),
            "--preset",
            "normal",
            "--quiet",
            "--json",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    # Should be valid JSON
    data = json.loads(captured.out)
    assert "normal" in data
