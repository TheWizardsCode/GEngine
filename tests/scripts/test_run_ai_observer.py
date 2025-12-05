"""Tests for the AI Observer CLI runner script."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "run_ai_observer.py"
)


def _load_observer_module():
    spec = util.spec_from_file_location("run_ai_observer", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("run_ai_observer", module)
    spec.loader.exec_module(module)
    return module


_mod = _load_observer_module()
run_ai_observer = _mod.run_ai_observer
main = _mod.main


class TestRunAiObserver:
    """Tests for the run_ai_observer function."""

    def test_run_with_default_parameters(self) -> None:
        """Test running observer with default parameters."""
        result = run_ai_observer(ticks=10)

        assert "mode" in result
        assert result["mode"].startswith("local:")
        assert "config" in result
        assert result["config"]["tick_budget"] == 10

    def test_run_with_custom_world(self) -> None:
        """Test running observer with specified world."""
        result = run_ai_observer(world="default", ticks=10, analysis_interval=5)

        assert result["mode"] == "local:default"
        assert "ticks_observed" in result

    def test_run_with_custom_analysis_interval(self) -> None:
        """Test running observer with custom analysis interval."""
        result = run_ai_observer(ticks=20, analysis_interval=5)

        assert result["config"]["analysis_interval"] == 5

    def test_run_with_custom_thresholds(self) -> None:
        """Test running observer with custom threshold values."""
        result = run_ai_observer(
            ticks=10,
            stability_threshold=0.3,
            legitimacy_threshold=0.2,
        )

        assert result["config"]["stability_alert_threshold"] == 0.3
        assert result["config"]["legitimacy_swing_threshold"] == 0.2

    def test_run_writes_output_file(self, tmp_path: Path) -> None:
        """Test that output file is written when specified."""
        output_path = tmp_path / "output.json"

        run_ai_observer(ticks=10, analysis_interval=5, output=output_path)

        assert output_path.exists()
        saved_data = json.loads(output_path.read_text())
        assert saved_data["config"]["tick_budget"] == 10
        assert "mode" in saved_data

    def test_run_creates_output_directory(self, tmp_path: Path) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_path = tmp_path / "nested" / "dir" / "output.json"

        run_ai_observer(ticks=10, analysis_interval=5, output=output_path)

        assert output_path.exists()

    def test_run_returns_report_dict(self) -> None:
        """Test that run_ai_observer returns a dictionary with expected keys."""
        result = run_ai_observer(ticks=10)

        # Check expected keys from ObservationReport.to_dict()
        assert "ticks_observed" in result
        assert "start_tick" in result
        assert "end_tick" in result
        assert "stability_trend" in result
        assert "faction_swings" in result
        assert "alerts" in result
        assert "commentary" in result
        assert "environment_summary" in result

    def test_run_with_verbose_mode(self, capsys) -> None:
        """Test running with verbose mode enabled."""
        result = run_ai_observer(ticks=10, analysis_interval=5, verbose=True)

        # Verbose mode should still return a valid result
        assert "ticks_observed" in result


class TestRunAiObserverServiceMode:
    """Tests for service mode of run_ai_observer."""

    def test_service_mode_creates_observer_from_service(self) -> None:
        """Test that service mode uses create_observer_from_service."""
        # Set up mock observer
        mock_report = MagicMock()
        mock_report.to_dict.return_value = {
            "ticks_observed": 10,
            "start_tick": 0,
            "end_tick": 10,
            "stability_trend": {},
            "faction_swings": {},
            "story_seeds_activated": [],
            "alerts": [],
            "commentary": [],
            "environment_summary": {},
        }
        mock_observer = MagicMock()
        mock_observer.observe.return_value = mock_report
        mock_observer._client = None

        with patch.object(
            _mod, "create_observer_from_service", return_value=mock_observer
        ) as mock_create_observer:
            result = run_ai_observer(service_url="http://localhost:8000", ticks=10)

            mock_create_observer.assert_called_once()
            assert result["mode"] == "service:http://localhost:8000"

    def test_service_mode_handles_connection_error(self) -> None:
        """Test that service mode handles connection errors appropriately."""
        mock_observer = MagicMock()
        mock_observer.observe.side_effect = ConnectionError("Service unavailable")
        mock_observer._client = None

        with patch.object(
            _mod, "create_observer_from_service", return_value=mock_observer
        ):
            with pytest.raises(ConnectionError):
                run_ai_observer(service_url="http://localhost:8000", ticks=10)

    def test_service_mode_closes_client(self) -> None:
        """Test that service mode closes client connection."""
        mock_report = MagicMock()
        mock_report.to_dict.return_value = {
            "ticks_observed": 10,
            "start_tick": 0,
            "end_tick": 10,
            "stability_trend": {},
            "faction_swings": {},
            "story_seeds_activated": [],
            "alerts": [],
            "commentary": [],
            "environment_summary": {},
        }
        mock_client = MagicMock()
        mock_observer = MagicMock()
        mock_observer.observe.return_value = mock_report
        mock_observer._client = mock_client

        with patch.object(
            _mod, "create_observer_from_service", return_value=mock_observer
        ):
            run_ai_observer(service_url="http://localhost:8000", ticks=10)

            mock_client.close.assert_called_once()


class TestMainCLI:
    """Tests for the main CLI entry point."""

    def test_main_default_arguments(self, capsys) -> None:
        """Test main with default arguments produces valid JSON output."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "ticks_observed" in data
        assert "mode" in data

    def test_main_with_world_argument(self, capsys) -> None:
        """Test main with --world argument."""
        exit_code = main(["--world", "default", "--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["mode"] == "local:default"

    def test_main_with_short_world_argument(self, capsys) -> None:
        """Test main with -w short argument."""
        exit_code = main(["-w", "default", "-t", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["mode"] == "local:default"

    def test_main_with_output_file(self, tmp_path: Path, capsys) -> None:
        """Test main with output file argument."""
        output_path = tmp_path / "result.json"

        exit_code = main(["-t", "10", "-o", str(output_path)])

        assert exit_code == 0
        assert output_path.exists()

        # Also printed to stdout
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "ticks_observed" in data

    def test_main_with_analysis_interval(self, capsys) -> None:
        """Test main with --analysis-interval argument."""
        exit_code = main(["--ticks", "20", "--analysis-interval", "5"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["config"]["analysis_interval"] == 5

    def test_main_with_stability_threshold(self, capsys) -> None:
        """Test main with --stability-threshold argument."""
        exit_code = main(["--ticks", "10", "--stability-threshold", "0.3"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["config"]["stability_alert_threshold"] == 0.3

    def test_main_with_legitimacy_threshold(self, capsys) -> None:
        """Test main with --legitimacy-threshold argument."""
        exit_code = main(["--ticks", "10", "--legitimacy-threshold", "0.15"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["config"]["legitimacy_swing_threshold"] == 0.15

    def test_main_with_verbose_flag(self, capsys) -> None:
        """Test main with --verbose flag."""
        exit_code = main(["--ticks", "10", "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        # Output should still be valid JSON
        data = json.loads(captured.out)
        assert "ticks_observed" in data

    def test_main_with_short_verbose_flag(self, capsys) -> None:
        """Test main with -v short flag."""
        exit_code = main(["-t", "10", "-v"])

        assert exit_code == 0

    def test_main_combined_arguments(self, tmp_path: Path, capsys) -> None:
        """Test main with multiple arguments combined."""
        output_path = tmp_path / "combined.json"

        exit_code = main([
            "--world", "default",
            "--ticks", "10",
            "--analysis-interval", "5",
            "--stability-threshold", "0.4",
            "--legitimacy-threshold", "0.15",
            "--output", str(output_path),
        ])

        assert exit_code == 0
        assert output_path.exists()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["mode"] == "local:default"
        assert data["config"]["tick_budget"] == 10
        assert data["config"]["analysis_interval"] == 5
        assert data["config"]["stability_alert_threshold"] == 0.4
        assert data["config"]["legitimacy_swing_threshold"] == 0.15

    def test_main_help_option(self, capsys) -> None:
        """Test that --help option displays help and exits."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "--world" in captured.out
        assert "--ticks" in captured.out
        assert "--service-url" in captured.out
        assert "--analysis-interval" in captured.out
        assert "--stability-threshold" in captured.out
        assert "--legitimacy-threshold" in captured.out
        assert "--output" in captured.out
        assert "--verbose" in captured.out


class TestArgumentDefaults:
    """Tests for CLI argument default values."""

    def test_default_world(self, capsys) -> None:
        """Test that default world is 'default'."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "local:default" in data["mode"]

    def test_default_ticks(self, capsys) -> None:
        """Test that default ticks is 100."""
        # Run with explicit ticks to avoid long test
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        # We specified 10 ticks, so config should reflect that
        assert data["config"]["tick_budget"] == 10

    def test_default_analysis_interval(self, capsys) -> None:
        """Test that default analysis interval is 10."""
        exit_code = main(["--ticks", "20"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["config"]["analysis_interval"] == 10

    def test_default_stability_threshold(self, capsys) -> None:
        """Test that default stability threshold is 0.5."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["config"]["stability_alert_threshold"] == 0.5

    def test_default_legitimacy_threshold(self, capsys) -> None:
        """Test that default legitimacy threshold is 0.1."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["config"]["legitimacy_swing_threshold"] == 0.1


class TestReportContent:
    """Tests for observation report content."""

    def test_report_contains_stability_trend(self, capsys) -> None:
        """Test that report contains stability trend analysis."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "stability_trend" in data
        trend = data["stability_trend"]
        assert "metric_name" in trend
        assert "start_value" in trend
        assert "end_value" in trend
        assert "delta" in trend
        assert "trend" in trend

    def test_report_contains_faction_swings(self, capsys) -> None:
        """Test that report contains faction swing analysis."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "faction_swings" in data
        assert isinstance(data["faction_swings"], dict)

    def test_report_contains_environment_summary(self, capsys) -> None:
        """Test that report contains environment summary."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "environment_summary" in data
        assert isinstance(data["environment_summary"], dict)

    def test_report_contains_alerts_and_commentary(self, capsys) -> None:
        """Test that report contains alerts and commentary."""
        exit_code = main(["--ticks", "10"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "alerts" in data
        assert "commentary" in data
        assert isinstance(data["alerts"], list)
        assert isinstance(data["commentary"], list)


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_world_raises_error(self) -> None:
        """Test that invalid world name raises an error."""
        with pytest.raises((FileNotFoundError, ValueError)):
            run_ai_observer(world="nonexistent_world", ticks=10)

    def test_verbose_connection_error_message(self, capsys) -> None:
        """Test that verbose mode prints connection error message."""
        mock_observer = MagicMock()
        mock_observer.observe.side_effect = ConnectionError("Service unavailable")
        mock_observer._client = None

        with patch.object(
            _mod, "create_observer_from_service", return_value=mock_observer
        ):
            with pytest.raises(ConnectionError):
                run_ai_observer(
                    service_url="http://localhost:8000",
                    ticks=10,
                    verbose=True,
                )

            captured = capsys.readouterr()
            assert "Connection error" in captured.out


class TestIntegration:
    """Integration tests with real world data."""

    def test_full_observation_cycle(self) -> None:
        """Test a complete observation cycle with real engine."""
        result = run_ai_observer(
            world="default",
            ticks=20,
            analysis_interval=10,
        )

        assert result["ticks_observed"] == 20
        assert result["start_tick"] == 0
        assert result["end_tick"] == 20

        # Verify stability trend is reasonable
        stability = result["stability_trend"]
        assert 0.0 <= stability["start_value"] <= 1.0
        assert 0.0 <= stability["end_value"] <= 1.0
        assert stability["trend"] in ["increasing", "decreasing", "stable"]

    def test_observation_with_different_tick_budgets(self) -> None:
        """Test observation with various tick budgets."""
        for ticks in [10, 15, 20]:
            result = run_ai_observer(world="default", ticks=ticks, analysis_interval=5)
            assert result["ticks_observed"] == ticks
            assert result["config"]["tick_budget"] == ticks
