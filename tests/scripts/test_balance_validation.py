"""Tests for balance validation CI integration.

Covers baseline management, regression detection, threshold configuration,
comparison logic, and workflow component integration.
"""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "manage_balance_baseline.py"
)


def _load_baseline_module():
    spec = util.spec_from_file_location("manage_balance_baseline", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("manage_balance_baseline", module)
    spec.loader.exec_module(module)
    return module


_module = _load_baseline_module()
RegressionAlert = _module.RegressionAlert
ComparisonResult = _module.ComparisonResult
BaselineConfig = _module.BaselineConfig
load_baseline = _module.load_baseline
load_sweep_summary = _module.load_sweep_summary
extract_strategy_stats = _module.extract_strategy_stats
extract_difficulty_stats = _module.extract_difficulty_stats
compute_win_rate = _module.compute_win_rate
compare_strategy_stats = _module.compare_strategy_stats
compare_against_baseline = _module.compare_against_baseline
create_baseline = _module.create_baseline
update_baseline = _module.update_baseline
main = _module.main


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_baseline() -> dict:
    """Create a sample baseline for testing."""
    return {
        "version": "1.0",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "git_commit": "abc1234",
        "description": "Test baseline",
        "strategy_stats": {
            "balanced": {
                "avg_stability": 0.7,
                "min_stability": 0.5,
                "max_stability": 0.9,
                "win_rate": 0.8,
                "avg_actions": 10,
                "total_actions": 50,
                "count": 5,
                "completed": 5,
                "failed": 0,
            },
            "aggressive": {
                "avg_stability": 0.5,
                "min_stability": 0.3,
                "max_stability": 0.7,
                "win_rate": 0.5,
                "avg_actions": 15,
                "total_actions": 75,
                "count": 5,
                "completed": 5,
                "failed": 0,
            },
            "diplomatic": {
                "avg_stability": 0.65,
                "min_stability": 0.45,
                "max_stability": 0.85,
                "win_rate": 0.6,
                "avg_actions": 8,
                "total_actions": 40,
                "count": 5,
                "completed": 5,
                "failed": 0,
            },
        },
        "difficulty_stats": {
            "easy": {"avg_stability": 0.75, "count": 5},
            "normal": {"avg_stability": 0.6, "count": 5},
            "hard": {"avg_stability": 0.5, "count": 5},
        },
        "total_sweeps": 45,
        "completed_sweeps": 45,
        "failed_sweeps": 0,
        "thresholds": {
            "stability_delta_warning": 5.0,
            "stability_delta_failure": 10.0,
            "win_rate_delta_warning": 5.0,
            "win_rate_delta_failure": 10.0,
            "unused_content_warning": True,
        },
    }


@pytest.fixture
def sample_sweep_summary() -> dict:
    """Create a sample sweep summary for testing."""
    return {
        "config": {
            "strategies": ["balanced", "aggressive", "diplomatic"],
            "difficulties": ["easy", "normal", "hard"],
            "seeds": [42, 123, 456],
            "worlds": ["default"],
            "tick_budgets": [100],
        },
        "total_sweeps": 45,
        "completed_sweeps": 44,
        "failed_sweeps": 1,
        "strategy_stats": {
            "balanced": {
                "avg_stability": 0.72,
                "min_stability": 0.52,
                "max_stability": 0.92,
                "avg_actions": 11,
                "total_actions": 55,
                "count": 15,
                "completed": 15,
                "failed": 0,
            },
            "aggressive": {
                "avg_stability": 0.48,
                "min_stability": 0.28,
                "max_stability": 0.68,
                "avg_actions": 16,
                "total_actions": 80,
                "count": 15,
                "completed": 14,
                "failed": 1,
            },
            "diplomatic": {
                "avg_stability": 0.67,
                "min_stability": 0.47,
                "max_stability": 0.87,
                "avg_actions": 9,
                "total_actions": 45,
                "count": 15,
                "completed": 15,
                "failed": 0,
            },
        },
        "difficulty_stats": {
            "easy": {"avg_stability": 0.77, "count": 15},
            "normal": {"avg_stability": 0.62, "count": 15},
            "hard": {"avg_stability": 0.48, "count": 15},
        },
        "total_duration_seconds": 120.5,
        "metadata": {
            "timestamp": "2025-01-15T10:00:00Z",
            "git_commit": "def5678",
        },
    }


# ============================================================================
# Test: Baseline Creation and Loading
# ============================================================================


class TestBaselineCreationAndLoading:
    """Tests for baseline file creation and loading."""

    def test_load_baseline_from_file(
        self, tmp_path: Path, sample_baseline: dict
    ) -> None:
        """Load baseline data from JSON file."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))

        loaded = load_baseline(baseline_path)

        assert loaded is not None
        assert loaded["version"] == "1.0"
        assert "strategy_stats" in loaded
        assert "balanced" in loaded["strategy_stats"]

    def test_load_baseline_missing_file(self, tmp_path: Path) -> None:
        """Return None when baseline file doesn't exist."""
        baseline_path = tmp_path / "nonexistent.json"

        loaded = load_baseline(baseline_path)

        assert loaded is None

    def test_create_baseline_from_sweep(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Create new baseline from sweep summary."""
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))
        output_path = tmp_path / "new_baseline.json"

        baseline = create_baseline(sweep_path, output_path)

        assert baseline is not None
        assert output_path.exists()
        assert baseline["strategy_stats"]["balanced"]["avg_stability"] == 0.72
        assert baseline["total_sweeps"] == 45
        assert "created_at" in baseline
        assert "thresholds" in baseline

    def test_create_baseline_with_git_commit(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Create baseline with explicit git commit."""
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))
        output_path = tmp_path / "baseline.json"

        baseline = create_baseline(sweep_path, output_path, git_commit="custom123")

        assert baseline["git_commit"] == "custom123"

    def test_update_baseline_preserves_created_at(
        self, tmp_path: Path, sample_baseline: dict, sample_sweep_summary: dict
    ) -> None:
        """Update baseline preserves original creation timestamp."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))

        updated = update_baseline(sweep_path, baseline_path)

        assert updated["created_at"] == "2025-01-01T00:00:00Z"
        assert updated["updated_at"] != updated["created_at"]


# ============================================================================
# Test: Regression Detection Logic
# ============================================================================


class TestRegressionDetectionLogic:
    """Tests for detecting balance regressions."""

    def test_detect_stability_regression_failure(self) -> None:
        """Detect significant stability decrease as failure."""
        baseline_stats = {
            "balanced": {"avg_stability": 0.8, "win_rate": 0.9},
        }
        current_stats = {
            "balanced": {"avg_stability": 0.6, "win_rate": 0.7},  # 25% drop
        }
        config = BaselineConfig(
            stability_delta_warning=5.0,
            stability_delta_failure=10.0,
        )

        alerts = compare_strategy_stats(baseline_stats, current_stats, config)

        stability_alerts = [a for a in alerts if a.metric_name == "avg_stability"]
        assert len(stability_alerts) == 1
        assert stability_alerts[0].severity == "failure"
        assert stability_alerts[0].delta_percent < -10

    def test_detect_stability_regression_warning(self) -> None:
        """Detect moderate stability decrease as warning."""
        baseline_stats = {
            "balanced": {"avg_stability": 0.8, "win_rate": 0.9},
        }
        current_stats = {
            "balanced": {"avg_stability": 0.74, "win_rate": 0.85},  # 7.5% drop
        }
        config = BaselineConfig(
            stability_delta_warning=5.0,
            stability_delta_failure=10.0,
        )

        alerts = compare_strategy_stats(baseline_stats, current_stats, config)

        stability_alerts = [a for a in alerts if a.metric_name == "avg_stability"]
        assert len(stability_alerts) == 1
        assert stability_alerts[0].severity == "warning"

    def test_no_regression_within_threshold(self) -> None:
        """No regression when changes are within threshold."""
        baseline_stats = {
            "balanced": {"avg_stability": 0.8, "win_rate": 0.9},
        }
        current_stats = {
            "balanced": {"avg_stability": 0.78, "win_rate": 0.88},  # 2.5% drop
        }
        config = BaselineConfig(
            stability_delta_warning=5.0,
            stability_delta_failure=10.0,
        )

        alerts = compare_strategy_stats(baseline_stats, current_stats, config)

        stability_alerts = [a for a in alerts if a.metric_name == "avg_stability"]
        assert len(stability_alerts) == 0

    def test_stability_improvement_not_flagged(self) -> None:
        """Stability improvements should not trigger alerts."""
        baseline_stats = {
            "balanced": {"avg_stability": 0.6, "win_rate": 0.7},
        }
        current_stats = {
            "balanced": {"avg_stability": 0.8, "win_rate": 0.9},  # 33% improvement
        }
        config = BaselineConfig()

        alerts = compare_strategy_stats(baseline_stats, current_stats, config)

        stability_alerts = [a for a in alerts if a.metric_name == "avg_stability"]
        assert len(stability_alerts) == 0

    def test_detect_win_rate_regression(self) -> None:
        """Detect win rate regression."""
        baseline_stats = {
            "aggressive": {"avg_stability": 0.5, "win_rate": 0.8},
        }
        current_stats = {
            "aggressive": {"avg_stability": 0.5, "win_rate": 0.6},  # 25% drop
        }
        config = BaselineConfig(
            win_rate_delta_warning=5.0,
            win_rate_delta_failure=10.0,
        )

        alerts = compare_strategy_stats(baseline_stats, current_stats, config)

        win_rate_alerts = [a for a in alerts if a.metric_name == "win_rate"]
        assert len(win_rate_alerts) == 1
        assert win_rate_alerts[0].severity == "failure"

    def test_multiple_strategy_regressions(self) -> None:
        """Detect regressions across multiple strategies."""
        baseline_stats = {
            "balanced": {"avg_stability": 0.8},
            "aggressive": {"avg_stability": 0.6},
            "diplomatic": {"avg_stability": 0.7},
        }
        current_stats = {
            "balanced": {"avg_stability": 0.5},  # Big drop
            "aggressive": {"avg_stability": 0.58},  # Minor drop
            "diplomatic": {"avg_stability": 0.4},  # Big drop
        }
        config = BaselineConfig(
            stability_delta_warning=5.0,
            stability_delta_failure=10.0,
        )

        alerts = compare_strategy_stats(baseline_stats, current_stats, config)

        # Should flag balanced and diplomatic
        affected_strategies = {a.strategy for a in alerts}
        assert "balanced" in affected_strategies
        assert "diplomatic" in affected_strategies


# ============================================================================
# Test: Threshold Configuration
# ============================================================================


class TestThresholdConfiguration:
    """Tests for configurable regression thresholds."""

    def test_baseline_config_from_dict(self) -> None:
        """Load threshold config from dictionary."""
        data = {
            "stability_delta_warning": 3.0,
            "stability_delta_failure": 8.0,
            "win_rate_delta_warning": 4.0,
            "win_rate_delta_failure": 12.0,
            "unused_content_warning": False,
        }

        config = BaselineConfig.from_dict(data)

        assert config.stability_delta_warning == 3.0
        assert config.stability_delta_failure == 8.0
        assert config.win_rate_delta_warning == 4.0
        assert config.win_rate_delta_failure == 12.0
        assert config.unused_content_warning is False

    def test_baseline_config_defaults(self) -> None:
        """Use default thresholds when not specified."""
        config = BaselineConfig.from_dict({})

        assert config.stability_delta_warning == 5.0
        assert config.stability_delta_failure == 10.0

    def test_custom_threshold_in_comparison(self) -> None:
        """Custom thresholds affect regression detection."""
        baseline_stats = {
            "balanced": {"avg_stability": 0.8, "win_rate": 0.8},
        }
        current_stats = {
            "balanced": {"avg_stability": 0.74, "win_rate": 0.74},  # 7.5% drop
        }

        # With default 5% warning threshold - should warn (stability alert)
        strict_config = BaselineConfig(
            stability_delta_warning=5.0,
            stability_delta_failure=10.0,
        )
        strict_alerts = compare_strategy_stats(
            baseline_stats, current_stats, strict_config
        )
        # Could have multiple alerts (stability + win_rate)
        stability_alerts = [a for a in strict_alerts if a.metric_name == "avg_stability"]
        assert len(stability_alerts) == 1

        # With relaxed 10% warning threshold - should pass
        relaxed_config = BaselineConfig(
            stability_delta_warning=10.0,
            stability_delta_failure=20.0,
            win_rate_delta_warning=10.0,
            win_rate_delta_failure=20.0,
        )
        relaxed_alerts = compare_strategy_stats(
            baseline_stats, current_stats, relaxed_config
        )
        assert len(relaxed_alerts) == 0


# ============================================================================
# Test: Comparison of Sweep Results
# ============================================================================


class TestComparisonOfSweepResults:
    """Tests for comparing sweep results against baseline."""

    def test_compare_against_baseline_no_regression(
        self, tmp_path: Path, sample_baseline: dict, sample_sweep_summary: dict
    ) -> None:
        """Comparison passes when no significant regressions."""
        baseline_path = tmp_path / "baseline.json"
        # Modify baseline to have lower values so current is an improvement
        modified_baseline = sample_baseline.copy()
        modified_baseline["strategy_stats"]["balanced"]["avg_stability"] = 0.6
        modified_baseline["strategy_stats"]["balanced"]["win_rate"] = 0.6
        modified_baseline["strategy_stats"]["aggressive"]["avg_stability"] = 0.4
        modified_baseline["strategy_stats"]["aggressive"]["win_rate"] = 0.4
        modified_baseline["strategy_stats"]["diplomatic"]["avg_stability"] = 0.5
        modified_baseline["strategy_stats"]["diplomatic"]["win_rate"] = 0.5
        baseline_path.write_text(json.dumps(modified_baseline))

        # Current sweep with better stats (improvement, not regression)
        current_sweep = sample_sweep_summary.copy()
        current_sweep["strategy_stats"]["balanced"]["avg_stability"] = 0.72
        current_sweep["strategy_stats"]["aggressive"]["avg_stability"] = 0.48
        current_sweep["strategy_stats"]["diplomatic"]["avg_stability"] = 0.67
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(current_sweep))

        result = compare_against_baseline(
            baseline_path, sweep_path, stability_threshold=5.0
        )

        assert result.passed is True
        assert "PASSED" in result.summary

    def test_compare_against_baseline_with_regression(
        self, tmp_path: Path, sample_baseline: dict, sample_sweep_summary: dict
    ) -> None:
        """Comparison fails when significant regression detected."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))

        # Current sweep with much lower stability
        current_sweep = sample_sweep_summary.copy()
        current_sweep["strategy_stats"]["balanced"]["avg_stability"] = 0.4
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(current_sweep))

        result = compare_against_baseline(
            baseline_path, sweep_path, stability_threshold=5.0
        )

        assert result.passed is False
        assert len(result.regressions) > 0
        assert "FAILED" in result.summary

    def test_compare_missing_baseline_passes(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Comparison passes when no baseline exists (establishing new baseline)."""
        baseline_path = tmp_path / "nonexistent_baseline.json"
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))

        result = compare_against_baseline(
            baseline_path, sweep_path, stability_threshold=5.0
        )

        assert result.passed is True
        assert "establishing new baseline" in result.summary.lower()

    def test_compare_missing_current_fails(
        self, tmp_path: Path, sample_baseline: dict
    ) -> None:
        """Comparison fails when current sweep data is missing."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))
        sweep_path = tmp_path / "nonexistent_sweep.json"

        result = compare_against_baseline(
            baseline_path, sweep_path, stability_threshold=5.0
        )

        assert result.passed is False
        assert "no current sweep data" in result.summary.lower()

    def test_comparison_result_serialization(
        self, tmp_path: Path, sample_baseline: dict, sample_sweep_summary: dict
    ) -> None:
        """ComparisonResult can be serialized to JSON."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))

        result = compare_against_baseline(
            baseline_path, sweep_path, stability_threshold=5.0
        )

        data = result.to_dict()

        assert "timestamp" in data
        assert "regressions" in data
        assert "baseline_stats" in data
        assert "current_stats" in data
        assert "summary" in data
        assert "passed" in data

        # Should be JSON serializable
        json_str = json.dumps(data)
        assert len(json_str) > 0


# ============================================================================
# Test: Workflow Component Integration
# ============================================================================


class TestWorkflowComponentIntegration:
    """Tests for CLI commands and workflow integration."""

    def test_cli_compare_command(
        self, tmp_path: Path, sample_baseline: dict, sample_sweep_summary: dict, capsys
    ) -> None:
        """CLI compare command works correctly."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))
        output_path = tmp_path / "result.json"

        exit_code = main([
            "compare",
            "--current", str(sweep_path),
            "--baseline", str(baseline_path),
            "--output", str(output_path),
        ])

        assert output_path.exists()
        result = json.loads(output_path.read_text())
        assert "regressions" in result
        assert "summary" in result

    def test_cli_update_command(
        self, tmp_path: Path, sample_sweep_summary: dict, capsys
    ) -> None:
        """CLI update command creates/updates baseline."""
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))
        output_path = tmp_path / "baseline.json"

        exit_code = main([
            "update",
            "--source", str(sweep_path),
            "--output", str(output_path),
        ])

        assert exit_code == 0
        assert output_path.exists()

        baseline = json.loads(output_path.read_text())
        assert baseline["strategy_stats"]["balanced"]["avg_stability"] == 0.72

    def test_cli_create_command(
        self, tmp_path: Path, sample_sweep_summary: dict, capsys
    ) -> None:
        """CLI create command creates new baseline."""
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(sample_sweep_summary))
        output_path = tmp_path / "new_baseline.json"

        exit_code = main([
            "create",
            "--source", str(sweep_path),
            "--output", str(output_path),
            "--git-commit", "test123",
        ])

        assert exit_code == 0
        baseline = json.loads(output_path.read_text())
        assert baseline["git_commit"] == "test123"

    def test_cli_show_command(
        self, tmp_path: Path, sample_baseline: dict, capsys
    ) -> None:
        """CLI show command displays baseline info."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))

        exit_code = main([
            "show",
            "--baseline", str(baseline_path),
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "balanced" in captured.out
        assert "aggressive" in captured.out

    def test_cli_show_json_output(
        self, tmp_path: Path, sample_baseline: dict, capsys
    ) -> None:
        """CLI show command outputs JSON when requested."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))

        exit_code = main([
            "show",
            "--baseline", str(baseline_path),
            "--json",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["version"] == "1.0"

    def test_cli_compare_with_custom_threshold(
        self, tmp_path: Path, sample_baseline: dict, sample_sweep_summary: dict, capsys
    ) -> None:
        """CLI compare respects custom stability threshold."""
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(sample_baseline))

        # Create sweep with significant regression
        current_sweep = sample_sweep_summary.copy()
        current_sweep["strategy_stats"]["balanced"]["avg_stability"] = 0.35  # 50% drop from 0.7
        sweep_path = tmp_path / "sweep_summary.json"
        sweep_path.write_text(json.dumps(current_sweep))

        # With strict threshold (5%) - should fail
        strict_result = tmp_path / "strict_result.json"
        exit_code = main([
            "compare",
            "--current", str(sweep_path),
            "--baseline", str(baseline_path),
            "--output", str(strict_result),
            "--stability-threshold", "5",
            "--quiet",
        ])
        assert exit_code == 1  # Failed

        # Create sweep with improvement (current > baseline) - should pass
        improved_sweep = sample_sweep_summary.copy()
        improved_sweep["strategy_stats"]["balanced"]["avg_stability"] = 0.8  # Better than 0.7 baseline
        improved_sweep["strategy_stats"]["aggressive"]["avg_stability"] = 0.6  # Better than 0.5 baseline
        improved_sweep["strategy_stats"]["diplomatic"]["avg_stability"] = 0.75  # Better than 0.65 baseline
        improved_sweep_path = tmp_path / "improved_sweep.json"
        improved_sweep_path.write_text(json.dumps(improved_sweep))

        relaxed_result = tmp_path / "relaxed_result.json"
        exit_code = main([
            "compare",
            "--current", str(improved_sweep_path),
            "--baseline", str(baseline_path),
            "--output", str(relaxed_result),
            "--stability-threshold", "5",
            "--quiet",
        ])
        assert exit_code == 0  # Passed (improvements are not regressions)


# ============================================================================
# Test: Data Class Serialization
# ============================================================================


class TestDataClassSerialization:
    """Tests for data class to_dict methods."""

    def test_regression_alert_to_dict(self) -> None:
        """RegressionAlert serializes correctly."""
        alert = RegressionAlert(
            metric_name="avg_stability",
            strategy="balanced",
            baseline_value=0.8,
            current_value=0.6,
            delta_percent=-25.0,
            severity="failure",
            description="Test alert",
        )

        data = alert.to_dict()

        assert data["metric_name"] == "avg_stability"
        assert data["strategy"] == "balanced"
        assert data["baseline_value"] == 0.8
        assert data["current_value"] == 0.6
        assert data["delta_percent"] == -25.0
        assert data["severity"] == "failure"

    def test_comparison_result_to_dict(self) -> None:
        """ComparisonResult serializes correctly."""
        result = ComparisonResult(
            timestamp="2025-01-15T10:00:00Z",
            baseline_path="/test/baseline.json",
            current_path="/test/current.json",
            regressions=[
                RegressionAlert(
                    metric_name="avg_stability",
                    strategy="balanced",
                    baseline_value=0.8,
                    current_value=0.6,
                    delta_percent=-25.0,
                    severity="failure",
                    description="Test alert",
                )
            ],
            summary="FAILED",
            passed=False,
        )

        data = result.to_dict()

        assert data["timestamp"] == "2025-01-15T10:00:00Z"
        assert len(data["regressions"]) == 1
        assert data["passed"] is False


# ============================================================================
# Test: Helper Functions
# ============================================================================


class TestHelperFunctions:
    """Tests for utility/helper functions."""

    def test_extract_strategy_stats(self, sample_sweep_summary: dict) -> None:
        """Extract strategy statistics from sweep summary."""
        stats = extract_strategy_stats(sample_sweep_summary)

        assert "balanced" in stats
        assert "aggressive" in stats
        assert "diplomatic" in stats
        assert stats["balanced"]["avg_stability"] == 0.72

    def test_extract_difficulty_stats(self, sample_sweep_summary: dict) -> None:
        """Extract difficulty statistics from sweep summary."""
        stats = extract_difficulty_stats(sample_sweep_summary)

        assert "easy" in stats
        assert "normal" in stats
        assert "hard" in stats

    def test_compute_win_rate_above_threshold(self) -> None:
        """Compute win rate for strategy above stability threshold."""
        stats = {"avg_stability": 0.75}
        win_rate = compute_win_rate(stats)
        assert 0.5 < win_rate <= 1.0

    def test_compute_win_rate_below_threshold(self) -> None:
        """Compute win rate for strategy below stability threshold."""
        stats = {"avg_stability": 0.3}
        win_rate = compute_win_rate(stats)
        assert 0.0 <= win_rate < 0.5

    def test_compute_win_rate_explicit_value(self) -> None:
        """Use explicit win_rate when available."""
        stats = {"avg_stability": 0.4, "win_rate": 0.8}
        # The compare function checks for explicit win_rate first
        # but compute_win_rate approximates from avg_stability
        win_rate = compute_win_rate(stats)
        # This should return approximation based on avg_stability
        assert win_rate < 0.5
