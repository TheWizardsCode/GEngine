"""Tests for Balance Studio CLI and components."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path
from unittest.mock import MagicMock, patch

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

@pytest.fixture
def mock_cli_workflows():
    """Mock workflow functions in the CLI module."""
    # We need to patch the functions in the loaded module _cli
    # The module name is 'echoes_balance_studio_cli'
    module_name = "echoes_balance_studio_cli"
    
    with patch(f"{module_name}.run_exploratory_sweep") as mock_sweep, \
         patch(f"{module_name}.run_config_comparison") as mock_compare, \
         patch(f"{module_name}.run_tuning_test") as mock_tuning, \
         patch(f"{module_name}.list_historical_reports") as mock_list, \
         patch(f"{module_name}.view_historical_report") as mock_view, \
         patch(f"{module_name}.write_html_report") as mock_write:
        
        # Setup default success returns
        mock_sweep.return_value = MagicMock(success=True, message="Success", output_path="out", errors=[])
        
        # Fix for JSON serialization: to_dict should return a real dict
        compare_result = MagicMock(success=True, message="Success", output_path="out", data={}, errors=[])
        compare_result.to_dict.return_value = {"success": True, "message": "Success"}
        mock_compare.return_value = compare_result
        
        mock_tuning.return_value = MagicMock(success=True, message="Success", output_path="out", data={}, errors=[])
        mock_list.return_value = []
        mock_view.return_value = MagicMock(success=True, message="Success", data={})
        
        yield {
            "sweep": mock_sweep,
            "compare": mock_compare,
            "tuning": mock_tuning,
            "list": mock_list,
            "view": mock_view,
            "write": mock_write
        }

class TestInteractiveMode:
    """Tests for interactive mode workflows."""

    def test_interactive_mode_quit(self, mock_cli_workflows):
        """Test quitting interactive mode."""
        with patch("builtins.input", side_effect=["q"]):
            assert _cli.interactive_mode() == 0

    def test_interactive_mode_invalid(self, mock_cli_workflows):
        """Test invalid input in interactive mode."""
        # The function returns 1 on invalid input (it does not loop)
        with patch("builtins.input", side_effect=["invalid"]):
            assert _cli.interactive_mode() == 1

    def test_interactive_mode_sweep(self, mock_cli_workflows):
        """Test selecting sweep workflow."""
        with patch("builtins.input", side_effect=["1", "", "", "", ""]): # Select 1, then defaults for sweep
            assert _cli.interactive_mode() == 0
            mock_cli_workflows["sweep"].assert_called_once()

    def test_interactive_sweep_defaults(self, mock_cli_workflows):
        """Test interactive sweep with defaults."""
        with patch("builtins.input", side_effect=["", "", "", ""]): # All defaults
            assert _cli.interactive_sweep() == 0
            args = mock_cli_workflows["sweep"].call_args[0][0]
            assert args.strategies == ["balanced", "aggressive", "diplomatic"]
            assert args.difficulties == ["normal"]
            assert args.seeds == [42, 123, 456]
            assert args.tick_budget == 100

    def test_interactive_sweep_custom(self, mock_cli_workflows):
        """Test interactive sweep with custom inputs."""
        with patch("builtins.input", side_effect=["strat1, strat2", "hard", "1, 2", "50"]):
            assert _cli.interactive_sweep() == 0
            args = mock_cli_workflows["sweep"].call_args[0][0]
            assert args.strategies == ["strat1", "strat2"]
            assert args.difficulties == ["hard"]
            assert args.seeds == [1, 2]
            assert args.tick_budget == 50

    def test_interactive_compare_success(self, mock_cli_workflows):
        """Test interactive compare workflow."""
        with patch("builtins.input", side_effect=["path/a", "Name A", "path/b", "Name B"]):
            assert _cli.interactive_compare() == 0
            args = mock_cli_workflows["compare"].call_args[0][0]
            assert str(args.config_a_path) == "path/a"
            assert args.name_a == "Name A"
            assert str(args.config_b_path) == "path/b"
            assert args.name_b == "Name B"

    def test_interactive_compare_missing_path(self, mock_cli_workflows):
        """Test interactive compare with missing path."""
        with patch("builtins.input", side_effect=[""]):
            assert _cli.interactive_compare() == 1

    def test_interactive_tuning_success(self, mock_cli_workflows):
        """Test interactive tuning workflow."""
        with patch("builtins.input", side_effect=["test_exp", "economy.regen=1.5", "invalid", "flag=true", ""]):
            assert _cli.interactive_tuning() == 0
            args = mock_cli_workflows["tuning"].call_args[0][0]
            assert args.name == "test_exp"
            assert args.changes == {"economy": {"regen": 1.5}, "flag": True}

    def test_interactive_tuning_no_changes(self, mock_cli_workflows):
        """Test interactive tuning with no changes."""
        with patch("builtins.input", side_effect=["test_exp", ""]):
            assert _cli.interactive_tuning() == 1

    def test_interactive_view_reports_empty(self, mock_cli_workflows):
        """Test viewing reports when none exist."""
        mock_cli_workflows["list"].return_value = []
        assert _cli.interactive_view_reports() == 0

    def test_interactive_view_reports_select(self, mock_cli_workflows):
        """Test selecting a report to view."""
        mock_cli_workflows["list"].return_value = [
            {"timestamp": "2023", "completed_sweeps": 1, "total_sweeps": 1, "strategies": ["s"], "path": "p"}
        ]
        mock_cli_workflows["view"].return_value.data = {"strategy_stats": {"s": {"avg_stability": 0.5}}}
        
        with patch("builtins.input", side_effect=["1"]):
            assert _cli.interactive_view_reports() == 0
            mock_cli_workflows["view"].assert_called_once()

    def test_interactive_view_reports_quit(self, mock_cli_workflows):
        """Test quitting report viewer."""
        mock_cli_workflows["list"].return_value = [{"timestamp": "2023", "completed_sweeps": 1, "total_sweeps": 1, "strategies": ["s"]}]
        with patch("builtins.input", side_effect=["q"]):
            assert _cli.interactive_view_reports() == 0

class TestCommandHandlers:
    """Tests for CLI command handlers."""

    def test_cmd_sweep(self, mock_cli_workflows):
        """Test sweep command."""
        args = MagicMock()
        args.strategies = ["s1"]
        args.difficulties = ["d1"]
        args.seeds = [1]
        args.ticks = 10
        args.output_dir = "out"
        args.overlay = None
        args.json = False
        args.verbose = False
        
        assert _cli.cmd_sweep(args) == 0
        mock_cli_workflows["sweep"].assert_called_once()

    def test_cmd_compare(self, mock_cli_workflows):
        """Test compare command."""
        args = MagicMock()
        args.config_a = "a"
        args.config_b = "b"
        args.name_a = "A"
        args.name_b = "B"
        args.strategies = ["s"]
        args.seeds = [1]
        args.ticks = 10
        args.output_dir = "out"
        args.json = True
        args.verbose = True
        
        assert _cli.cmd_compare(args) == 0
        mock_cli_workflows["compare"].assert_called_once()

    def test_cmd_test_tuning(self, mock_cli_workflows):
        """Test tuning command."""
        args = MagicMock()
        args.name = "test"
        args.change = ["a=1", "b.c=2.5", "d=true"]
        args.description = "desc"
        args.baseline = None
        args.strategies = ["s"]
        args.seeds = [1]
        args.ticks = 10
        args.output_dir = "out"
        args.json = False
        args.verbose = False
        
        assert _cli.cmd_test_tuning(args) == 0
        call_args = mock_cli_workflows["tuning"].call_args[0][0]
        assert call_args.changes == {"a": 1, "b": {"c": 2.5}, "d": True}

    def test_cmd_view_reports(self, mock_cli_workflows):
        """Test view-reports command."""
        args = MagicMock()
        args.reports_dir = "dir"
        args.limit = 5
        args.json = False
        
        mock_cli_workflows["list"].return_value = [{"timestamp": "t", "completed_sweeps": 1, "total_sweeps": 1, "strategies": ["s"], "path": "p"}]
        
        assert _cli.cmd_view_reports(args) == 0
        mock_cli_workflows["list"].assert_called_once()

    def test_cmd_generate_report(self, mock_cli_workflows, tmp_path):
        """Test generate-report command."""
        input_file = tmp_path / "in.json"
        input_file.write_text("{}")
        output_file = tmp_path / "out.html"
        
        args = MagicMock()
        args.input = str(input_file)
        args.output = str(output_file)
        args.title = "Title"
        args.theme = "light"
        args.no_charts = False
        args.include_raw = False
        
        assert _cli.cmd_generate_report(args) == 0
        mock_cli_workflows["write"].assert_called_once()

    def test_cmd_generate_report_missing_input(self, mock_cli_workflows, tmp_path):
        """Test generate-report with missing input."""
        args = MagicMock()
        args.input = str(tmp_path / "missing.json")
        
        assert _cli.cmd_generate_report(args) == 1
