"""Tests for the echoes-balance-studio CLI tool."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "echoes_balance_studio.py"
)


def _load_balance_studio_module():
    spec = util.spec_from_file_location("balance_studio", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("balance_studio", module)
    spec.loader.exec_module(module)
    return module


_studio = _load_balance_studio_module()

# Import functions from the module
deep_merge = _studio.deep_merge
load_config = _studio.load_config
load_config_with_overlay = _studio.load_config_with_overlay
save_config = _studio.save_config
list_overlays = _studio.list_overlays
validate_overlay = _studio.validate_overlay
get_historical_reports = _studio.get_historical_reports
view_report_details = _studio.view_report_details
generate_enhanced_html_report = _studio.generate_enhanced_html_report
main = _studio.main


class TestDeepMerge:
    """Tests for the deep_merge function."""

    def test_simple_merge(self) -> None:
        """Test merging flat dictionaries."""
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}
        result = deep_merge(base, overlay)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        """Test merging nested dictionaries."""
        base = {
            "economy": {"regen_scale": 0.8, "base_price": 1.0},
            "limits": {"cli_run_cap": 50},
        }
        overlay = {
            "economy": {"regen_scale": 1.0},
        }
        result = deep_merge(base, overlay)

        assert result["economy"]["regen_scale"] == 1.0
        assert result["economy"]["base_price"] == 1.0
        assert result["limits"]["cli_run_cap"] == 50

    def test_does_not_modify_original(self) -> None:
        """Test that deep_merge doesn't modify the original dictionaries."""
        base = {"a": {"b": 1}}
        overlay = {"a": {"c": 2}}

        result = deep_merge(base, overlay)

        assert result == {"a": {"b": 1, "c": 2}}
        assert base == {"a": {"b": 1}}
        assert overlay == {"a": {"c": 2}}

    def test_deeply_nested_merge(self) -> None:
        """Test merging deeply nested structures."""
        base = {"a": {"b": {"c": {"d": 1}}}}
        overlay = {"a": {"b": {"c": {"e": 2}}}}

        result = deep_merge(base, overlay)

        assert result["a"]["b"]["c"]["d"] == 1
        assert result["a"]["b"]["c"]["e"] == 2


class TestConfigLoading:
    """Tests for config loading and saving."""

    def test_load_config_from_yaml(self, tmp_path: Path) -> None:
        """Test loading a YAML config file."""
        config_content = """
economy:
  regen_scale: 0.9
limits:
  cli_run_cap: 100
"""
        config_file = tmp_path / "test_config.yml"
        config_file.write_text(config_content)

        result = load_config(config_file)

        assert result["economy"]["regen_scale"] == 0.9
        assert result["limits"]["cli_run_cap"] == 100

    def test_load_config_missing_file(self, tmp_path: Path) -> None:
        """Test loading a non-existent config returns empty dict."""
        result = load_config(tmp_path / "nonexistent.yml")
        assert result == {}

    def test_load_config_with_overlay(self, tmp_path: Path) -> None:
        """Test loading config with overlay applied."""
        base_content = """
economy:
  regen_scale: 0.8
  base_price: 1.0
"""
        overlay_content = """
economy:
  regen_scale: 1.0
"""
        base_file = tmp_path / "base.yml"
        overlay_file = tmp_path / "overlay.yml"
        base_file.write_text(base_content)
        overlay_file.write_text(overlay_content)

        result = load_config_with_overlay(base_file, overlay_file)

        assert result["economy"]["regen_scale"] == 1.0
        assert result["economy"]["base_price"] == 1.0

    def test_save_config(self, tmp_path: Path) -> None:
        """Test saving config to YAML file."""
        config = {"economy": {"regen_scale": 0.9}}
        output_file = tmp_path / "output" / "config.yml"

        save_config(config, output_file)

        assert output_file.exists()
        loaded = load_config(output_file)
        assert loaded["economy"]["regen_scale"] == 0.9


class TestOverlayValidation:
    """Tests for overlay validation."""

    def test_valid_overlay(self) -> None:
        """Test validating a correct overlay."""
        overlay = {
            "economy": {"regen_scale": 1.0},
            "environment": {"scarcity_pressure_cap": 6000},
        }
        warnings = validate_overlay(overlay)
        assert len(warnings) == 0

    def test_overlay_with_unknown_keys(self) -> None:
        """Test that unknown keys generate warnings."""
        overlay = {
            "economy": {"regen_scale": 1.0},
            "unknown_section": {"value": 123},
        }
        warnings = validate_overlay(overlay)
        assert len(warnings) == 1
        assert "unknown_section" in warnings[0]

    def test_overlay_with_meta(self) -> None:
        """Test that _meta key is allowed."""
        overlay = {
            "_meta": {"name": "Test Overlay"},
            "economy": {"regen_scale": 1.0},
        }
        warnings = validate_overlay(overlay)
        assert len(warnings) == 0


class TestListOverlays:
    """Tests for listing overlay files."""

    def test_list_overlays_with_files(self, tmp_path: Path) -> None:
        """Test listing overlays from a directory."""
        overlay_dir = tmp_path / "overlays"
        overlay_dir.mkdir()
        (overlay_dir / "test1.yml").write_text("economy: {}")
        (overlay_dir / "test2.yaml").write_text("limits: {}")
        (overlay_dir / "not_an_overlay.txt").write_text("ignored")

        overlays = list_overlays(overlay_dir)

        assert len(overlays) == 2
        names = [o.name for o in overlays]
        assert "test1.yml" in names
        assert "test2.yaml" in names

    def test_list_overlays_empty_directory(self, tmp_path: Path) -> None:
        """Test listing overlays from empty directory."""
        overlay_dir = tmp_path / "empty"
        overlay_dir.mkdir()

        overlays = list_overlays(overlay_dir)
        assert overlays == []

    def test_list_overlays_missing_directory(self, tmp_path: Path) -> None:
        """Test listing overlays from non-existent directory."""
        overlays = list_overlays(tmp_path / "nonexistent")
        assert overlays == []


class TestHistoricalReports:
    """Tests for historical report querying."""

    def test_get_historical_reports_no_database(self, tmp_path: Path) -> None:
        """Test querying when database doesn't exist."""
        reports = get_historical_reports(tmp_path / "nonexistent.db")
        assert reports == []

    def test_view_report_details_no_database(self, tmp_path: Path) -> None:
        """Test viewing report when database doesn't exist."""
        result = view_report_details(1, tmp_path / "nonexistent.db")
        assert "error" in result


class TestEnhancedHtmlReport:
    """Tests for enhanced HTML report generation."""

    def test_generate_html_no_database(self, tmp_path: Path) -> None:
        """Test HTML generation when database doesn't exist."""
        html = generate_enhanced_html_report(tmp_path / "nonexistent.db")
        assert "Error" in html
        assert "Database not found" in html

    def test_generate_html_with_filters(self, tmp_path: Path) -> None:
        """Test that filter parameters don't cause errors."""
        html = generate_enhanced_html_report(
            tmp_path / "nonexistent.db",
            days=30,
            filter_strategy="balanced",
            filter_difficulty="normal",
        )
        # Should still return error page, but not crash
        assert "html" in html.lower()


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_overlays_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test the overlays command."""
        overlay_dir = tmp_path / "overlays"
        overlay_dir.mkdir()
        (overlay_dir / "test.yml").write_text("economy:\n  regen_scale: 1.0")

        exit_code = main(["overlays", "--overlay-dir", str(overlay_dir)])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "test.yml" in captured.out

    def test_cli_overlays_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test the overlays command with JSON output."""
        overlay_dir = tmp_path / "overlays"
        overlay_dir.mkdir()
        (overlay_dir / "test.yml").write_text("economy:\n  regen_scale: 1.0")

        exit_code = main([
            "overlays",
            "--overlay-dir", str(overlay_dir),
            "--json"
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert any("test.yml" in path for path in data)

    def test_cli_history_no_database(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test history command with no database."""
        exit_code = main([
            "history",
            "--database", str(tmp_path / "nonexistent.db")
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No sweep runs found" in captured.out

    def test_cli_history_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test history command with JSON output."""
        exit_code = main([
            "history",
            "--database", str(tmp_path / "nonexistent.db"),
            "--json"
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_cli_view_no_database(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test view command with non-existent database."""
        exit_code = main([
            "view", "1",
            "--database", str(tmp_path / "nonexistent.db")
        ])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower() or "Error" in captured.out

    def test_cli_report_no_database(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test report command with non-existent database."""
        exit_code = main([
            "report",
            "--database", str(tmp_path / "nonexistent.db")
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Error" in captured.out or "html" in captured.out.lower()

    def test_cli_compare_missing_config(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test compare command with missing config file."""
        exit_code = main([
            "compare",
            "--config-a", str(tmp_path / "nonexistent_a.yml"),
            "--config-b", str(tmp_path / "nonexistent_b.yml"),
        ])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_cli_test_tuning_missing_overlay(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test test-tuning command with missing overlay file."""
        exit_code = main([
            "test-tuning",
            "--overlay", str(tmp_path / "nonexistent.yml"),
        ])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()


class TestIntegration:
    """Integration tests that require the full simulation environment."""

    @pytest.mark.slow
    def test_sweep_basic(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test running a basic sweep (slow test)."""
        output_dir = tmp_path / "sweep_output"

        exit_code = main([
            "sweep",
            "--strategies", "balanced",
            "--seeds", "42",
            "--ticks", "5",
            "--output-dir", str(output_dir),
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "EXPLORATORY SWEEP COMPLETE" in captured.out
        assert (output_dir / "batch_sweep_summary.json").exists()

    @pytest.mark.slow
    def test_sweep_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test sweep with JSON output."""
        exit_code = main([
            "sweep",
            "--strategies", "balanced",
            "--seeds", "42",
            "--ticks", "5",
            "--output-dir", str(tmp_path / "sweep"),
            "--json",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "total_sweeps" in data
        assert "strategy_stats" in data
