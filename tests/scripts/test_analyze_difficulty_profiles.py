"""Tests for the difficulty profile analysis script."""

from __future__ import annotations

import json
from importlib import util
from pathlib import Path
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "analyze_difficulty_profiles.py"


def _load_analysis_module():
    spec = util.spec_from_file_location("analysis_driver", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("analysis_driver", module)
    spec.loader.exec_module(module)
    return module


_driver = _load_analysis_module()
DifficultyProfile = _driver.DifficultyProfile
load_difficulty_profiles = _driver.load_difficulty_profiles
compare_profiles = _driver.compare_profiles
main = _driver.main
DIFFICULTY_PRESETS = _driver.DIFFICULTY_PRESETS


@pytest.fixture()
def sample_telemetry() -> dict:
    """Create sample telemetry data."""
    return {
        "ticks_executed": 100,
        "events_emitted": 250,
        "anomalies": 5,
        "suppressed_events": 150,
        "last_environment": {
            "stability": 0.85,
            "unrest": 0.25,
            "pollution": 0.35,
            "biodiversity": 0.7,
        },
        "faction_legitimacy": {
            "union-of-flux": 0.6,
            "cartel-of-mist": 0.4,
        },
        "last_economy": {
            "prices": {
                "energy": 1.2,
                "food": 1.1,
                "water": 1.0,
            }
        },
        "post_mortem": {
            "environment": {
                "start": {"stability": 1.0, "unrest": 0.0},
                "end": {"stability": 0.85, "unrest": 0.25},
                "delta": {"stability": -0.15, "unrest": 0.25},
            }
        },
    }


@pytest.fixture()
def telemetry_dir(tmp_path: Path, sample_telemetry: dict) -> Path:
    """Create a directory with sample telemetry files."""
    for preset in ["easy", "normal", "hard"]:
        telemetry = sample_telemetry.copy()
        # Vary stability by preset to simulate difficulty progression
        if preset == "easy":
            telemetry["last_environment"]["stability"] = 0.95
            telemetry["last_environment"]["unrest"] = 0.1
        elif preset == "normal":
            telemetry["last_environment"]["stability"] = 0.8
            telemetry["last_environment"]["unrest"] = 0.3
        else:  # hard
            telemetry["last_environment"]["stability"] = 0.6
            telemetry["last_environment"]["unrest"] = 0.5

        (tmp_path / f"difficulty-{preset}-sweep.json").write_text(
            json.dumps(telemetry, indent=2)
        )

    return tmp_path


def test_difficulty_profile_from_telemetry(sample_telemetry: dict) -> None:
    """Test creating a DifficultyProfile from telemetry data."""
    profile = DifficultyProfile.from_telemetry("normal", sample_telemetry)

    assert profile.preset == "normal"
    assert profile.stability_end == 0.85
    assert profile.stability_start == 1.0
    assert profile.stability_delta == pytest.approx(-0.15, abs=0.01)
    assert profile.stability_trend == "declining"
    assert profile.unrest_end == 0.25
    assert profile.pollution_end == 0.35
    assert profile.anomalies == 5
    assert profile.suppressed_events == 150
    assert profile.faction_balance == pytest.approx(0.2, abs=0.01)
    assert profile.economic_pressure == pytest.approx(0.2, abs=0.01)
    assert profile.narrative_density == 2.5  # 250 events / 100 ticks


def test_difficulty_profile_stability_trends() -> None:
    """Test stability trend classification."""
    # Improving stability
    data = {
        "last_environment": {"stability": 0.9},
        "post_mortem": {"environment": {"start": {"stability": 0.7}}},
    }
    profile = DifficultyProfile.from_telemetry("test", data)
    assert profile.stability_trend == "improving"

    # Stable
    data = {
        "last_environment": {"stability": 0.85},
        "post_mortem": {"environment": {"start": {"stability": 0.83}}},
    }
    profile = DifficultyProfile.from_telemetry("test", data)
    assert profile.stability_trend == "stable"

    # Declining
    data = {
        "last_environment": {"stability": 0.5},
        "post_mortem": {"environment": {"start": {"stability": 0.9}}},
    }
    profile = DifficultyProfile.from_telemetry("test", data)
    assert profile.stability_trend == "declining"


def test_load_difficulty_profiles(telemetry_dir: Path) -> None:
    """Test loading profiles from telemetry directory."""
    profiles = load_difficulty_profiles(telemetry_dir)

    assert len(profiles) == 3
    assert "easy" in profiles
    assert "normal" in profiles
    assert "hard" in profiles

    # Verify stability progression
    assert profiles["easy"].stability_end > profiles["normal"].stability_end
    assert profiles["normal"].stability_end > profiles["hard"].stability_end


def test_load_difficulty_profiles_subset(telemetry_dir: Path) -> None:
    """Test loading specific presets only."""
    profiles = load_difficulty_profiles(telemetry_dir, presets=["easy", "hard"])

    assert len(profiles) == 2
    assert "easy" in profiles
    assert "hard" in profiles
    assert "normal" not in profiles


def test_load_difficulty_profiles_missing_files(tmp_path: Path) -> None:
    """Test loading from directory with no telemetry files."""
    profiles = load_difficulty_profiles(tmp_path)
    assert len(profiles) == 0


def test_compare_profiles(telemetry_dir: Path) -> None:
    """Test profile comparison analysis."""
    profiles = load_difficulty_profiles(telemetry_dir)
    comparison = compare_profiles(profiles)

    assert comparison["profile_count"] == 3
    assert "metrics" in comparison
    assert "findings" in comparison
    assert "stability" in comparison["metrics"]
    assert "unrest" in comparison["metrics"]

    # Should detect proper difficulty progression
    findings_text = " ".join(comparison["findings"])
    assert "Stability correctly decreases" in findings_text
    assert "Unrest correctly increases" in findings_text


def test_compare_profiles_empty() -> None:
    """Test comparison with no profiles."""
    comparison = compare_profiles({})
    assert "error" in comparison


def test_compare_profiles_detects_collapsed_stability(tmp_path: Path) -> None:
    """Test that comparison detects collapsed stability."""
    telemetry = {
        "last_environment": {"stability": 0.0, "unrest": 1.0, "pollution": 1.0},
        "post_mortem": {"environment": {"start": {"stability": 1.0}}},
        "anomalies": 150,
    }
    (tmp_path / "difficulty-brutal-sweep.json").write_text(json.dumps(telemetry))

    profiles = load_difficulty_profiles(tmp_path)
    comparison = compare_profiles(profiles)

    findings_text = " ".join(comparison["findings"])
    assert "Stability collapsed" in findings_text
    assert "High anomaly count" in findings_text


def test_analysis_main_cli(telemetry_dir: Path, capsys: pytest.CaptureFixture) -> None:
    """Test CLI entry point."""
    exit_code = main(["--telemetry-dir", str(telemetry_dir)])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DIFFICULTY PROFILE ANALYSIS" in captured.out
    assert "COMPARISON FINDINGS" in captured.out


def test_analysis_main_json_output(
    telemetry_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test CLI with JSON output."""
    exit_code = main(["--telemetry-dir", str(telemetry_dir), "--json"])

    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "profiles" in data
    assert "comparison" in data


def test_analysis_main_no_telemetry(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test CLI with no telemetry files."""
    exit_code = main(["--telemetry-dir", str(tmp_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "No telemetry files found" in captured.err
