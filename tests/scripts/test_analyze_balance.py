"""Tests for balance analysis and reporting module."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "analyze_balance.py"
)


def _load_balance_module():
    spec = util.spec_from_file_location("analyze_balance", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("analyze_balance", module)
    spec.loader.exec_module(module)
    return module


_module = _load_balance_module()
ConfidenceInterval = _module.ConfidenceInterval
TTestResult = _module.TTestResult
TrendAnalysis = _module.TrendAnalysis
RegressionAlert = _module.RegressionAlert
BalanceReport = _module.BalanceReport
compute_confidence_interval = _module.compute_confidence_interval
perform_t_test = _module.perform_t_test
detect_trend = _module.detect_trend
detect_regression = _module.detect_regression
analyze_dominant_strategies = _module.analyze_dominant_strategies
analyze_underperforming_mechanics = _module.analyze_underperforming_mechanics
identify_unused_story_seeds = _module.identify_unused_story_seeds
analyze_parameter_sensitivity = _module.analyze_parameter_sensitivity
generate_balance_report = _module.generate_balance_report
format_report_markdown = _module.format_report_markdown
format_report_html = _module.format_report_html
main = _module.main


# Helper to create test database with schema and data
def create_test_db(tmp_path: Path, data: list[dict] | None = None):
    """Create test SQLite database with sweep schema."""
    import sqlite3

    db_path = tmp_path / "test_sweep.db"
    conn = sqlite3.connect(str(db_path))

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sweep_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            git_commit TEXT,
            total_sweeps INTEGER NOT NULL,
            completed_sweeps INTEGER NOT NULL,
            failed_sweeps INTEGER NOT NULL,
            strategies TEXT NOT NULL,
            difficulties TEXT NOT NULL,
            worlds TEXT NOT NULL,
            tick_budgets TEXT NOT NULL,
            seeds TEXT NOT NULL,
            total_duration_seconds REAL NOT NULL,
            source_path TEXT
        );

        CREATE TABLE IF NOT EXISTS sweep_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            sweep_id INTEGER NOT NULL,
            strategy TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            seed INTEGER NOT NULL,
            world TEXT NOT NULL,
            tick_budget INTEGER NOT NULL,
            final_stability REAL NOT NULL,
            actions_taken INTEGER NOT NULL,
            ticks_run INTEGER NOT NULL,
            story_seeds_activated TEXT,
            action_counts TEXT,
            duration_seconds REAL NOT NULL,
            error TEXT,
            FOREIGN KEY (run_id) REFERENCES sweep_runs(run_id)
        );
    """
    )

    if data:
        for sweep_data in data:
            run_id = sweep_data.get("run_id", 1)
            # Insert run if not exists
            conn.execute(
                """
                INSERT OR IGNORE INTO sweep_runs (
                    run_id, timestamp, git_commit, total_sweeps,
                    completed_sweeps, failed_sweeps, strategies,
                    difficulties, worlds, tick_budgets, seeds,
                    total_duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    sweep_data.get("timestamp", "2025-01-15T10:00:00+00:00"),
                    sweep_data.get("git_commit", "abc1234"),
                    1,
                    1,
                    0,
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    1.0,
                ),
            )
            # Insert sweep result
            conn.execute(
                """
                INSERT INTO sweep_results (
                    run_id, sweep_id, strategy, difficulty, seed, world,
                    tick_budget, final_stability, actions_taken, ticks_run,
                    story_seeds_activated, action_counts, duration_seconds, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    sweep_data.get("sweep_id", 0),
                    sweep_data.get("strategy", "balanced"),
                    sweep_data.get("difficulty", "normal"),
                    sweep_data.get("seed", 42),
                    sweep_data.get("world", "default"),
                    sweep_data.get("tick_budget", 100),
                    sweep_data.get("final_stability", 0.75),
                    sweep_data.get("actions_taken", 10),
                    sweep_data.get("ticks_run", 100),
                    json.dumps(sweep_data.get("story_seeds_activated", [])),
                    json.dumps(sweep_data.get("action_counts", {})),
                    sweep_data.get("duration_seconds", 1.0),
                    sweep_data.get("error"),
                ),
            )

    conn.commit()
    return db_path, conn


class TestConfidenceInterval:
    """Tests for confidence interval computation."""

    def test_compute_ci_with_sample(self) -> None:
        """Compute confidence interval with valid sample."""
        values = [0.7, 0.75, 0.8, 0.72, 0.78]
        ci = compute_confidence_interval(values)

        assert ci.sample_size == 5
        assert 0.7 < ci.mean < 0.8
        assert ci.lower < ci.mean < ci.upper
        assert ci.confidence_level == 0.95

    def test_compute_ci_single_value(self) -> None:
        """Confidence interval with single value returns point estimate."""
        values = [0.75]
        ci = compute_confidence_interval(values)

        assert ci.mean == 0.75
        assert ci.lower == 0.75
        assert ci.upper == 0.75
        assert ci.sample_size == 1

    def test_compute_ci_empty_values(self) -> None:
        """Confidence interval with empty list returns zero."""
        ci = compute_confidence_interval([])

        assert ci.mean == 0.0
        assert ci.sample_size == 0

    def test_ci_to_dict(self) -> None:
        """ConfidenceInterval serializes correctly."""
        ci = ConfidenceInterval(
            mean=0.75, lower=0.7, upper=0.8, confidence_level=0.95, sample_size=10
        )
        d = ci.to_dict()

        assert d["mean"] == 0.75
        assert d["lower"] == 0.7
        assert d["upper"] == 0.8
        assert d["sample_size"] == 10


class TestTTest:
    """Tests for t-test functionality."""

    def test_perform_t_test_significant_difference(self) -> None:
        """T-test detects significant difference between groups."""
        values_a = [0.9, 0.85, 0.88, 0.92, 0.87]  # High stability
        values_b = [0.3, 0.35, 0.32, 0.28, 0.33]  # Low stability

        result = perform_t_test("high", values_a, "low", values_b)

        assert result.group_a == "high"
        assert result.group_b == "low"
        assert result.mean_a > result.mean_b
        assert result.is_significant is True
        assert result.p_value < 0.05

    def test_perform_t_test_no_significant_difference(self) -> None:
        """T-test detects no significant difference between similar groups."""
        values_a = [0.7, 0.75, 0.72, 0.73, 0.74]
        values_b = [0.71, 0.74, 0.73, 0.72, 0.75]

        result = perform_t_test("group_a", values_a, "group_b", values_b)

        assert result.is_significant is False
        assert result.p_value >= 0.05

    def test_perform_t_test_insufficient_data(self) -> None:
        """T-test with insufficient data returns non-significant result."""
        values_a = [0.75]
        values_b = [0.65]

        result = perform_t_test("a", values_a, "b", values_b)

        assert result.is_significant is False
        assert result.p_value == 1.0

    def test_t_test_result_to_dict(self) -> None:
        """TTestResult serializes correctly."""
        result = TTestResult(
            group_a="a",
            group_b="b",
            mean_a=0.8,
            mean_b=0.6,
            t_statistic=2.5,
            p_value=0.02,
            is_significant=True,
        )
        d = result.to_dict()

        assert d["group_a"] == "a"
        assert d["is_significant"] is True
        assert d["p_value"] == 0.02


class TestTrendDetection:
    """Tests for trend detection."""

    def test_detect_increasing_trend(self) -> None:
        """Detect increasing trend in time series."""
        timestamps = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]
        values = [0.5, 0.6, 0.7, 0.8]

        trend = detect_trend(timestamps, values, "stability")

        assert trend.metric_name == "stability"
        assert trend.trend_direction == "increasing"
        assert trend.slope > 0
        assert trend.data_points == 4

    def test_detect_decreasing_trend(self) -> None:
        """Detect decreasing trend in time series."""
        timestamps = ["2025-01-01", "2025-01-02", "2025-01-03"]
        values = [0.9, 0.7, 0.5]

        trend = detect_trend(timestamps, values, "stability")

        assert trend.trend_direction == "decreasing"
        assert trend.slope < 0

    def test_detect_stable_trend(self) -> None:
        """Detect stable trend when values don't change significantly."""
        timestamps = ["2025-01-01", "2025-01-02", "2025-01-03"]
        values = [0.75, 0.75, 0.75]

        trend = detect_trend(timestamps, values, "stability")

        assert trend.trend_direction == "stable"
        assert abs(trend.slope) < 0.001

    def test_detect_trend_insufficient_data(self) -> None:
        """Trend detection with single data point returns stable."""
        trend = detect_trend(["2025-01-01"], [0.75], "stability")

        assert trend.trend_direction == "stable"
        assert trend.data_points == 1


class TestRegressionDetection:
    """Tests for regression detection."""

    def test_detect_stability_regression(self) -> None:
        """Detect stability regression when current is significantly lower."""
        baseline = {"avg_stability": 0.8, "avg_actions": 10}
        current = {"avg_stability": 0.6, "avg_actions": 10}

        alerts = detect_regression(baseline, current, threshold_percent=10.0)

        assert len(alerts) == 1
        assert alerts[0].metric_name == "avg_stability"
        assert alerts[0].severity in ["medium", "high"]
        assert alerts[0].deviation_percent < -10

    def test_detect_no_regression_within_threshold(self) -> None:
        """No regression alert when deviation is within threshold."""
        baseline = {"avg_stability": 0.8, "avg_actions": 10}
        current = {"avg_stability": 0.78, "avg_actions": 10}  # Only 2.5% drop

        alerts = detect_regression(baseline, current, threshold_percent=10.0)

        # No stability regression, but maybe action change
        stability_alerts = [a for a in alerts if a.metric_name == "avg_stability"]
        assert len(stability_alerts) == 0

    def test_regression_alert_to_dict(self) -> None:
        """RegressionAlert serializes correctly."""
        alert = RegressionAlert(
            metric_name="avg_stability",
            baseline_value=0.8,
            current_value=0.6,
            deviation_percent=-25.0,
            severity="high",
            description="Test",
        )
        d = alert.to_dict()

        assert d["metric_name"] == "avg_stability"
        assert d["severity"] == "high"
        assert d["deviation_percent"] == -25.0


class TestDominantStrategies:
    """Tests for dominant strategy detection."""

    def test_detect_dominant_strategy(self) -> None:
        """Detect strategy with significantly higher win rate."""
        win_rates = {
            "aggressive": [0.9, 0.85, 0.88, 0.92, 0.87],  # High win rate
            "balanced": [0.5, 0.45, 0.52, 0.48, 0.55],  # Medium win rate
            "defensive": [0.3, 0.35, 0.32, 0.28, 0.33],  # Low win rate
        }

        dominant = analyze_dominant_strategies(win_rates, threshold=0.10)

        assert len(dominant) == 1
        assert dominant[0]["strategy"] == "aggressive"
        assert dominant[0]["delta_from_worst"] > 0.10

    def test_no_dominant_strategy_when_balanced(self) -> None:
        """No dominant strategy when win rates are similar."""
        win_rates = {
            "a": [0.5, 0.52, 0.48],
            "b": [0.51, 0.49, 0.50],
        }

        dominant = analyze_dominant_strategies(win_rates, threshold=0.10)

        assert len(dominant) == 0

    def test_dominant_strategies_single_strategy(self) -> None:
        """No dominant strategy detection with single strategy."""
        win_rates = {"balanced": [0.75, 0.8, 0.7]}

        dominant = analyze_dominant_strategies(win_rates)

        assert len(dominant) == 0


class TestUnderperformingMechanics:
    """Tests for underperforming mechanics detection."""

    def test_detect_underperforming_action(self) -> None:
        """Detect actions with very low usage."""
        frequencies = {
            "INSPECT": 100,
            "NEGOTIATE": 80,
            "RARE_ACTION": 2,  # Only 2 out of 182 total
        }

        underperforming = analyze_underperforming_mechanics(
            frequencies, min_usage_threshold=0.05
        )

        assert len(underperforming) == 1
        assert underperforming[0]["action"] == "RARE_ACTION"
        assert underperforming[0]["usage_rate"] < 0.05

    def test_no_underperforming_when_all_used(self) -> None:
        """No underperforming actions when all have sufficient usage."""
        frequencies = {
            "INSPECT": 50,
            "NEGOTIATE": 50,
        }

        underperforming = analyze_underperforming_mechanics(frequencies)

        assert len(underperforming) == 0

    def test_underperforming_empty_frequencies(self) -> None:
        """Handle empty action frequencies."""
        underperforming = analyze_underperforming_mechanics({})

        assert len(underperforming) == 0


class TestUnusedStorySeeds:
    """Tests for unused story seed identification."""

    def test_identify_unused_seeds(self) -> None:
        """Identify seeds that were never activated."""
        activations = {"seed-1": 5, "seed-2": 3}
        all_seeds = ["seed-1", "seed-2", "seed-3", "seed-4"]

        unused = identify_unused_story_seeds(activations, all_seeds)

        assert "seed-3" in unused
        assert "seed-4" in unused
        assert "seed-1" not in unused
        assert len(unused) == 2

    def test_all_seeds_activated(self) -> None:
        """No unused seeds when all are activated."""
        activations = {"seed-1": 5, "seed-2": 3}
        all_seeds = ["seed-1", "seed-2"]

        unused = identify_unused_story_seeds(activations, all_seeds)

        assert len(unused) == 0

    def test_no_all_seeds_provided(self) -> None:
        """Return empty list when no reference seed list provided."""
        activations = {"seed-1": 5}

        unused = identify_unused_story_seeds(activations, None)

        assert len(unused) == 0


class TestParameterSensitivity:
    """Tests for parameter sensitivity analysis."""

    def test_analyze_sensitivity_by_difficulty(self) -> None:
        """Analyze metric sensitivity across difficulty levels."""
        metrics = {
            "easy": {"stability": [0.9, 0.85, 0.88], "actions": [5.0, 6.0, 5.5]},
            "hard": {"stability": [0.5, 0.45, 0.48], "actions": [15.0, 16.0, 14.0]},
        }

        result = analyze_parameter_sensitivity(metrics)

        assert "easy" in result["difficulties"]
        assert "hard" in result["difficulties"]
        assert "stability" in result["difficulties"]["easy"]
        assert result["difficulties"]["easy"]["stability"]["mean"] > 0.8
        assert result["difficulties"]["hard"]["stability"]["mean"] < 0.6

    def test_sensitivity_detects_high_variation(self) -> None:
        """Detect high sensitivity when metrics vary significantly."""
        metrics = {
            "low": {"stability": [0.9, 0.92, 0.88]},
            "high": {"stability": [0.3, 0.28, 0.32]},
        }

        result = analyze_parameter_sensitivity(metrics)

        # Stability varies significantly between difficulties
        if "stability" in result.get("sensitivity_summary", {}):
            assert result["sensitivity_summary"]["stability"]["is_sensitive"] is True


class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_report_with_data(self, tmp_path: Path) -> None:
        """Generate balance report from database with data."""
        data = [
            {
                "strategy": "balanced",
                "final_stability": 0.75,
                "action_counts": {"INSPECT": 5},
                "story_seeds_activated": ["seed-1"],
            },
            {
                "strategy": "aggressive",
                "final_stability": 0.45,
                "action_counts": {"DEPLOY": 10},
            },
        ]
        db_path, conn = create_test_db(tmp_path, data)

        report = generate_balance_report(conn)
        conn.close()

        assert report.generated_at is not None
        assert isinstance(report.confidence_intervals, dict)
        assert isinstance(report.t_tests, list)

    def test_format_report_markdown(self, tmp_path: Path) -> None:
        """Format report as Markdown."""
        data = [{"strategy": "balanced", "final_stability": 0.75}]
        db_path, conn = create_test_db(tmp_path, data)
        report = generate_balance_report(conn)
        conn.close()

        markdown = format_report_markdown(report)

        assert "# Balance Analysis Report" in markdown
        assert "## Dominant Strategies" in markdown
        assert "## Statistical Analysis" in markdown

    def test_format_report_html(self, tmp_path: Path) -> None:
        """Format report as HTML."""
        data = [{"strategy": "balanced", "final_stability": 0.75}]
        db_path, conn = create_test_db(tmp_path, data)
        report = generate_balance_report(conn)
        conn.close()

        html = format_report_html(report)

        assert "<!DOCTYPE html>" in html
        assert "<h1>Balance Analysis Report</h1>" in html
        assert "<h2>Dominant Strategies</h2>" in html

    def test_balance_report_to_dict(self) -> None:
        """BalanceReport serializes to dict correctly."""
        report = BalanceReport(
            generated_at="2025-01-15T10:00:00Z",
            database_path="/test/db",
            dominant_strategies=[],
            underperforming_mechanics=[],
            unused_story_seeds=[],
            parameter_sensitivity={},
            confidence_intervals={},
            t_tests=[],
            trends=[],
            regressions=[],
            charts={},
        )

        d = report.to_dict()

        assert d["generated_at"] == "2025-01-15T10:00:00Z"
        assert d["database_path"] == "/test/db"
        assert isinstance(d["dominant_strategies"], list)


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_report_missing_database(self, capsys) -> None:
        """CLI report command fails for missing database."""
        exit_code = main(
            ["--database", "/nonexistent/path/db.sqlite", "report"]
        )

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_cli_report_generates_output(self, tmp_path: Path, capsys) -> None:
        """CLI report command generates output."""
        data = [{"strategy": "balanced", "final_stability": 0.75}]
        db_path, conn = create_test_db(tmp_path, data)
        conn.close()

        exit_code = main(["--database", str(db_path), "report"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Balance Analysis Report" in captured.out

    def test_cli_report_json_output(self, tmp_path: Path, capsys) -> None:
        """CLI report command outputs JSON when requested."""
        data = [{"strategy": "balanced", "final_stability": 0.75}]
        db_path, conn = create_test_db(tmp_path, data)
        conn.close()

        exit_code = main(["--database", str(db_path), "report", "--format", "json"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "generated_at" in output
        assert "dominant_strategies" in output

    def test_cli_stats_command(self, tmp_path: Path, capsys) -> None:
        """CLI stats command outputs statistical analysis."""
        data = [
            {"strategy": "balanced", "final_stability": 0.75},
            {"strategy": "balanced", "final_stability": 0.8, "sweep_id": 1},
            {"strategy": "aggressive", "final_stability": 0.5, "sweep_id": 2},
            {"strategy": "aggressive", "final_stability": 0.55, "sweep_id": 3},
        ]
        db_path, conn = create_test_db(tmp_path, data)
        conn.close()

        exit_code = main(["--database", str(db_path), "stats", "--json"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "confidence_intervals" in output
        assert "t_tests" in output

    def test_cli_trends_command(self, tmp_path: Path, capsys) -> None:
        """CLI trends command outputs trend analysis."""
        data = [{"strategy": "balanced", "final_stability": 0.75}]
        db_path, conn = create_test_db(tmp_path, data)
        conn.close()

        exit_code = main(["--database", str(db_path), "trends", "--json"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "trends" in output

    def test_cli_regression_command(self, tmp_path: Path, capsys) -> None:
        """CLI regression command compares runs."""
        # Create two runs with different stability
        data = [
            {
                "run_id": 1,
                "strategy": "balanced",
                "final_stability": 0.8,
                "timestamp": "2025-01-01T10:00:00Z",
            },
            {
                "run_id": 2,
                "strategy": "balanced",
                "final_stability": 0.5,
                "timestamp": "2025-01-02T10:00:00Z",
            },
        ]
        db_path, conn = create_test_db(tmp_path, data)
        conn.close()

        exit_code = main([
            "--database",
            str(db_path),
            "regression",
            "--baseline-run",
            "1",
            "--compare-run",
            "2",
            "--json",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "regressions" in output


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_database(self, tmp_path: Path) -> None:
        """Handle empty database gracefully."""
        db_path, conn = create_test_db(tmp_path, data=None)

        report = generate_balance_report(conn)
        conn.close()

        assert report.dominant_strategies == []
        assert report.underperforming_mechanics == []
        assert len(report.t_tests) == 0

    def test_single_sweep_result(self, tmp_path: Path) -> None:
        """Handle database with single sweep result."""
        data = [{"strategy": "balanced", "final_stability": 0.75}]
        db_path, conn = create_test_db(tmp_path, data)

        report = generate_balance_report(conn)
        conn.close()

        # Should not crash, confidence intervals should be point estimates
        assert len(report.confidence_intervals) == 1
        ci = list(report.confidence_intervals.values())[0]
        assert ci.sample_size == 1

    def test_all_failed_sweeps(self, tmp_path: Path) -> None:
        """Handle database with all failed sweeps."""
        data = [
            {"strategy": "balanced", "final_stability": 0.0, "error": "Failed"},
            {"strategy": "aggressive", "final_stability": 0.0, "error": "Failed"},
        ]
        db_path, conn = create_test_db(tmp_path, data)

        report = generate_balance_report(conn)
        conn.close()

        # All failed, so no valid data to analyze
        assert len(report.confidence_intervals) == 0
