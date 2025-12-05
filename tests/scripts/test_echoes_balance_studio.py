"""Tests for Balance Studio CLI and components."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

import pytest
import yaml

from gengine.balance_studio.overlays import (
    ConfigOverlay,
    create_tuning_overlay,
    deep_merge,
    load_overlay_directory,
    merge_overlays,
)
from gengine.balance_studio.report_viewer import (
    ReportViewerConfig,
    generate_interactive_html,
    write_html_report,
)
from gengine.balance_studio.workflows import (
    ExploratorySweepConfig,
    WorkflowResult,
    get_workflow_menu,
    list_historical_reports,
    view_historical_report,
)

# Load CLI main from script file

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "echoes_balance_studio.py"
)


def _load_cli_module():
    spec = util.spec_from_file_location("echoes_balance_studio_cli", _SCRIPT_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("echoes_balance_studio_cli", module)
    spec.loader.exec_module(module)
    return module


_cli = _load_cli_module()
main = _cli.main


class TestConfigOverlay:
    """Tests for ConfigOverlay dataclass and loading."""

    def test_overlay_from_yaml(self, tmp_path: Path) -> None:
        """Test loading overlay from YAML file."""
        overlay_file = tmp_path / "test_overlay.yml"
        overlay_file.write_text(
            yaml.dump(
                {
                    "name": "test_overlay",
                    "description": "A test overlay",
                    "overrides": {"economy": {"regen_scale": 1.5}},
                    "metadata": {"author": "tester"},
                }
            )
        )

        overlay = ConfigOverlay.from_yaml(overlay_file)

        assert overlay.name == "test_overlay"
        assert overlay.description == "A test overlay"
        assert overlay.overrides == {"economy": {"regen_scale": 1.5}}
        assert overlay.metadata == {"author": "tester"}
        assert overlay.source_path == overlay_file

    def test_overlay_from_yaml_missing_file(self, tmp_path: Path) -> None:
        """Test loading overlay from missing file raises error."""
        with pytest.raises(FileNotFoundError):
            ConfigOverlay.from_yaml(tmp_path / "nonexistent.yml")

    def test_overlay_from_dict(self) -> None:
        """Test creating overlay from dictionary."""
        data = {
            "name": "inline_test",
            "description": "Inline overlay",
            "overrides": {"limits": {"engine_max_ticks": 500}},
        }

        overlay = ConfigOverlay.from_dict(data)

        assert overlay.name == "inline_test"
        assert overlay.description == "Inline overlay"
        assert overlay.overrides == {"limits": {"engine_max_ticks": 500}}

    def test_overlay_apply(self) -> None:
        """Test applying overlay to base config."""
        base_config = {
            "economy": {"regen_scale": 0.8, "demand_population_scale": 100000},
            "limits": {"engine_max_ticks": 200},
        }

        overlay = ConfigOverlay(
            name="test",
            overrides={"economy": {"regen_scale": 1.2}},
        )

        result = overlay.apply(base_config)

        assert result["economy"]["regen_scale"] == 1.2
        assert result["economy"]["demand_population_scale"] == 100000
        assert result["limits"]["engine_max_ticks"] == 200

    def test_overlay_to_yaml(self, tmp_path: Path) -> None:
        """Test writing overlay to YAML file."""
        overlay = ConfigOverlay(
            name="save_test",
            description="Testing save",
            overrides={"test": {"value": 42}},
        )

        output_path = tmp_path / "saved_overlay.yml"
        overlay.to_yaml(output_path)

        assert output_path.exists()
        with open(output_path) as f:
            loaded = yaml.safe_load(f)

        assert loaded["name"] == "save_test"
        assert loaded["overrides"]["test"]["value"] == 42


class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_deep_merge_simple(self) -> None:
        """Test merging flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self) -> None:
        """Test merging nested dictionaries."""
        base = {"level1": {"a": 1, "b": {"c": 2}}}
        override = {"level1": {"b": {"d": 3}}}

        result = deep_merge(base, override)

        assert result["level1"]["a"] == 1
        assert result["level1"]["b"]["c"] == 2
        assert result["level1"]["b"]["d"] == 3

    def test_deep_merge_preserves_original(self) -> None:
        """Test that original dicts are not modified."""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}

        result = deep_merge(base, override)

        assert "c" not in base["a"]
        assert result["a"]["c"] == 2


class TestLoadOverlayDirectory:
    """Tests for loading overlays from directory."""

    def test_load_directory_with_overlays(self, tmp_path: Path) -> None:
        """Test loading multiple overlays from directory."""
        (tmp_path / "overlay1.yml").write_text(
            yaml.dump({"name": "overlay1", "overrides": {"a": 1}})
        )
        (tmp_path / "overlay2.yaml").write_text(
            yaml.dump({"name": "overlay2", "overrides": {"b": 2}})
        )

        overlays = load_overlay_directory(tmp_path)

        assert len(overlays) == 2
        names = {o.name for o in overlays}
        assert "overlay1" in names
        assert "overlay2" in names

    def test_load_directory_empty(self, tmp_path: Path) -> None:
        """Test loading from empty directory."""
        overlays = load_overlay_directory(tmp_path)
        assert overlays == []

    def test_load_directory_nonexistent(self, tmp_path: Path) -> None:
        """Test loading from nonexistent directory."""
        overlays = load_overlay_directory(tmp_path / "nonexistent")
        assert overlays == []


class TestCreateTuningOverlay:
    """Tests for create_tuning_overlay helper."""

    def test_create_tuning_overlay(self) -> None:
        """Test creating a tuning overlay."""
        overlay = create_tuning_overlay(
            name="test_tuning",
            changes={"economy": {"regen_scale": 1.5}},
            description="Testing regen boost",
        )

        assert overlay.name == "test_tuning"
        assert overlay.description == "Testing regen boost"
        assert overlay.overrides == {"economy": {"regen_scale": 1.5}}
        assert overlay.metadata["type"] == "tuning_experiment"


class TestMergeOverlays:
    """Tests for merge_overlays function."""

    def test_merge_overlays(self) -> None:
        """Test merging multiple overlays."""
        overlay1 = ConfigOverlay(name="o1", overrides={"a": 1, "b": 2})
        overlay2 = ConfigOverlay(name="o2", overrides={"b": 3, "c": 4})

        result = merge_overlays([overlay1, overlay2])

        assert result.name == "o1 + o2"
        assert result.overrides == {"a": 1, "b": 3, "c": 4}

    def test_merge_empty_list(self) -> None:
        """Test merging empty list of overlays."""
        result = merge_overlays([])
        assert result.name == "empty"
        assert result.overrides == {}


class TestReportViewer:
    """Tests for report viewer HTML generation."""

    def test_generate_html_basic(self) -> None:
        """Test generating basic HTML report."""
        data = {
            "total_sweeps": 10,
            "completed_sweeps": 9,
            "failed_sweeps": 1,
            "total_duration_seconds": 120.5,
            "metadata": {"timestamp": "2024-01-01T00:00:00Z"},
            "strategy_stats": {
                "balanced": {"count": 5, "completed": 5, "avg_stability": 0.75}
            },
            "difficulty_stats": {},
            "sweeps": [],
        }

        html = generate_interactive_html(data)

        assert "<!DOCTYPE html>" in html
        assert "Balance Studio Report" in html
        assert "10" in html  # total_sweeps
        assert "balanced" in html

    def test_generate_html_with_config(self) -> None:
        """Test generating HTML with custom config."""
        data = {
            "total_sweeps": 5,
            "completed_sweeps": 5,
            "failed_sweeps": 0,
            "total_duration_seconds": 60.0,
            "metadata": {},
            "strategy_stats": {},
            "difficulty_stats": {},
            "sweeps": [],
        }

        config = ReportViewerConfig(
            title="Custom Report",
            theme="dark",
            include_charts=False,
        )

        html = generate_interactive_html(data, config)

        assert "Custom Report" in html
        assert "#1a1a2e" in html  # dark theme background

    def test_write_html_report(self, tmp_path: Path) -> None:
        """Test writing HTML report to file."""
        data = {
            "total_sweeps": 3,
            "completed_sweeps": 3,
            "failed_sweeps": 0,
            "total_duration_seconds": 30.0,
            "metadata": {},
            "strategy_stats": {},
            "difficulty_stats": {},
            "sweeps": [],
        }

        output_path = tmp_path / "report.html"
        write_html_report(data, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content


class TestWorkflows:
    """Tests for workflow functions."""

    def test_workflow_result_serialization(self) -> None:
        """Test WorkflowResult to_dict serialization."""
        result = WorkflowResult(
            workflow_name="test",
            success=True,
            message="Test passed",
            output_path=Path("/tmp/output"),
            data={"key": "value"},
            errors=[],
        )

        d = result.to_dict()

        assert d["workflow_name"] == "test"
        assert d["success"] is True
        assert d["message"] == "Test passed"
        assert d["output_path"] == "/tmp/output"
        assert d["data"] == {"key": "value"}

    def test_get_workflow_menu(self) -> None:
        """Test getting workflow menu."""
        menu = get_workflow_menu()

        assert len(menu) == 4
        ids = {w["id"] for w in menu}
        assert "exploratory_sweep" in ids
        assert "compare_configs" in ids
        assert "tuning_test" in ids
        assert "view_reports" in ids

    def test_list_historical_reports_empty(self, tmp_path: Path) -> None:
        """Test listing reports in empty directory."""
        reports = list_historical_reports(tmp_path)
        assert reports == []

    def test_list_historical_reports_with_data(self, tmp_path: Path) -> None:
        """Test listing reports with actual data."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary = sweep_dir / "batch_sweep_summary.json"
        summary.write_text(
            json.dumps(
                {
                    "total_sweeps": 5,
                    "completed_sweeps": 5,
                    "metadata": {"timestamp": "2024-01-01T00:00:00Z"},
                    "config": {"strategies": ["balanced"], "difficulties": ["normal"]},
                }
            )
        )

        reports = list_historical_reports(tmp_path)

        assert len(reports) == 1
        assert reports[0]["total_sweeps"] == 5

    def test_view_historical_report_not_found(self, tmp_path: Path) -> None:
        """Test viewing nonexistent report."""
        result = view_historical_report(tmp_path / "nonexistent.json")

        assert not result.success
        assert "not found" in result.message.lower()

    def test_view_historical_report_success(self, tmp_path: Path) -> None:
        """Test viewing existing report."""
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps({"total_sweeps": 10}))

        result = view_historical_report(report_path)

        assert result.success
        assert result.data["total_sweeps"] == 10


class TestCLI:
    """Tests for CLI command handling."""

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        with pytest.raises(SystemExit) as exc:
            main(["--help"])

        assert exc.value.code == 0

    def test_cli_view_reports_empty(self, tmp_path: Path) -> None:
        """Test view-reports command with empty directory."""
        result = main(["view-reports", "--reports-dir", str(tmp_path), "--json"])
        assert result == 0

    def test_cli_generate_report_missing_input(self, tmp_path: Path) -> None:
        """Test generate-report with missing input."""
        result = main(
            [
                "generate-report",
                "--input",
                str(tmp_path / "nonexistent.json"),
                "--output",
                str(tmp_path / "report.html"),
            ]
        )
        assert result == 1

    def test_cli_generate_report_success(self, tmp_path: Path) -> None:
        """Test generate-report with valid input."""
        input_file = tmp_path / "input.json"
        input_file.write_text(
            json.dumps(
                {
                    "total_sweeps": 5,
                    "completed_sweeps": 5,
                    "failed_sweeps": 0,
                    "total_duration_seconds": 30.0,
                    "metadata": {},
                    "strategy_stats": {},
                    "difficulty_stats": {},
                    "sweeps": [],
                }
            )
        )

        output_file = tmp_path / "report.html"
        result = main(
            [
                "generate-report",
                "--input",
                str(input_file),
                "--output",
                str(output_file),
            ]
        )

        assert result == 0
        assert output_file.exists()

    def test_cli_test_tuning_no_changes(self, tmp_path: Path) -> None:
        """Test test-tuning command with no changes."""
        result = main(
            [
                "test-tuning",
                "--name",
                "empty_test",
                "--output-dir",
                str(tmp_path),
            ]
        )
        # Should fail because no --change arguments
        assert result == 1


class TestExploratorySweepConfig:
    """Tests for ExploratorySweepConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ExploratorySweepConfig()

        assert config.strategies == ["balanced", "aggressive", "diplomatic"]
        assert config.difficulties == ["normal"]
        assert config.seeds == [42, 123, 456]
        assert config.tick_budget == 100

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ExploratorySweepConfig(
            strategies=["balanced"],
            difficulties=["hard"],
            seeds=[1, 2, 3],
            tick_budget=200,
        )

        assert config.strategies == ["balanced"]
        assert config.difficulties == ["hard"]
        assert config.seeds == [1, 2, 3]
        assert config.tick_budget == 200
