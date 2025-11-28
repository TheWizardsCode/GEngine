"""Tests for simulation configuration helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from gengine.echoes.settings import load_simulation_config


def test_load_simulation_config_from_custom_root(tmp_path: Path) -> None:
    config_path = tmp_path / "simulation.yml"
    config_path.write_text(
        "limits:\n  cli_run_cap: 7\n  engine_max_ticks: 10\n  cli_script_command_cap: 4\n  service_tick_cap: 8\n"
        "lod:\n  mode: detailed\n\nprofiling:\n  log_ticks: false\n"
    )

    config = load_simulation_config(config_root=tmp_path)

    assert config.limits.cli_run_cap == 7
    assert config.lod.mode == "detailed"
    assert config.profiling.log_ticks is False


def test_load_simulation_config_handles_missing_file(tmp_path: Path) -> None:
    config = load_simulation_config(config_root=tmp_path)

    assert config.limits.cli_run_cap == 50


def test_load_simulation_config_requires_mapping(tmp_path: Path) -> None:
    config_path = tmp_path / "simulation.yml"
    config_path.write_text("- not a mapping")

    with pytest.raises(ValueError):
        load_simulation_config(config_root=tmp_path)
