#!/usr/bin/env python3
"""Analyze balance from aggregated sweep results in SQLite database.

Generates HTML or Markdown balance reports with statistical analysis,
visualizations, and regression detection.

Examples
--------
Generate a Markdown balance report::

    uv run python scripts/analyze_balance.py report --database build/sweep_results.db

Generate HTML report with charts::

    uv run python scripts/analyze_balance.py report --database build/sweep_results.db \\
        --format html --output build/balance_report.html

Detect regressions against a baseline run::

    uv run python scripts/analyze_balance.py regression \\
        --database build/sweep_results.db --baseline-run 1 --compare-run 2

Show trend analysis::

    uv run python scripts/analyze_balance.py trends --database build/sweep_results.db \\
        --days 30
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

# Optional imports for visualization
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Optional imports for statistics
try:
    from scipy import stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ConfidenceInterval:
    """Confidence interval for a statistic."""

    mean: float
    lower: float
    upper: float
    confidence_level: float = 0.95
    sample_size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean": round(self.mean, 4),
            "lower": round(self.lower, 4),
            "upper": round(self.upper, 4),
            "confidence_level": self.confidence_level,
            "sample_size": self.sample_size,
        }


@dataclass
class TTestResult:
    """Result of a two-sample t-test."""

    group_a: str
    group_b: str
    mean_a: float
    mean_b: float
    t_statistic: float
    p_value: float
    is_significant: bool
    significance_level: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_a": self.group_a,
            "group_b": self.group_b,
            "mean_a": round(self.mean_a, 4),
            "mean_b": round(self.mean_b, 4),
            "t_statistic": round(self.t_statistic, 4),
            "p_value": round(self.p_value, 6),
            "is_significant": self.is_significant,
            "significance_level": self.significance_level,
        }


@dataclass
class TrendAnalysis:
    """Trend analysis for a metric over time."""

    metric_name: str
    slope: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    data_points: int
    timestamps: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "slope": round(self.slope, 6),
            "trend_direction": self.trend_direction,
            "data_points": self.data_points,
            "timestamps": self.timestamps,
            "values": [round(v, 4) for v in self.values],
        }


@dataclass
class RegressionAlert:
    """Alert for a detected regression."""

    metric_name: str
    baseline_value: float
    current_value: float
    deviation_percent: float
    severity: str  # "low", "medium", "high"
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline_value": round(self.baseline_value, 4),
            "current_value": round(self.current_value, 4),
            "deviation_percent": round(self.deviation_percent, 2),
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class BalanceReport:
    """Complete balance analysis report."""

    generated_at: str
    database_path: str
    dominant_strategies: list[dict[str, Any]]
    underperforming_mechanics: list[dict[str, Any]]
    unused_story_seeds: list[str]
    parameter_sensitivity: dict[str, Any]
    confidence_intervals: dict[str, ConfidenceInterval]
    t_tests: list[TTestResult]
    trends: list[TrendAnalysis]
    regressions: list[RegressionAlert]
    charts: dict[str, str]  # Base64-encoded chart images

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "database_path": self.database_path,
            "dominant_strategies": self.dominant_strategies,
            "underperforming_mechanics": self.underperforming_mechanics,
            "unused_story_seeds": self.unused_story_seeds,
            "parameter_sensitivity": self.parameter_sensitivity,
            "confidence_intervals": {
                k: v.to_dict() for k, v in self.confidence_intervals.items()
            },
            "t_tests": [t.to_dict() for t in self.t_tests],
            "trends": [t.to_dict() for t in self.trends],
            "regressions": [r.to_dict() for r in self.regressions],
            "charts": self.charts,
        }


# ============================================================================
# Database Query Functions
# ============================================================================


def query_strategy_win_rates(
    conn: sqlite3.Connection, days: int | None = None
) -> dict[str, list[float]]:
    """Query win rates grouped by strategy.

    Parameters
    ----------
    conn
        Database connection.
    days
        Optional filter to last N days.

    Returns
    -------
    dict[str, list[float]]
        Mapping of strategy name to list of final_stability values.
    """
    query = """
        SELECT sr.strategy, sr.final_stability
        FROM sweep_results sr
        JOIN sweep_runs runs ON sr.run_id = runs.run_id
        WHERE sr.error IS NULL
    """
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND runs.timestamp >= ?"
        params.append(cutoff.isoformat())

    query += " ORDER BY sr.strategy"

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    results: dict[str, list[float]] = {}
    for row in rows:
        strategy = row[0]
        stability = row[1]
        results.setdefault(strategy, []).append(stability)

    return results


def query_action_frequencies(
    conn: sqlite3.Connection, days: int | None = None
) -> dict[str, int]:
    """Query total action counts across all sweeps.

    Parameters
    ----------
    conn
        Database connection.
    days
        Optional filter to last N days.

    Returns
    -------
    dict[str, int]
        Mapping of action name to total count.
    """
    query = """
        SELECT sr.action_counts
        FROM sweep_results sr
        JOIN sweep_runs runs ON sr.run_id = runs.run_id
        WHERE sr.error IS NULL
    """
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND runs.timestamp >= ?"
        params.append(cutoff.isoformat())

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    totals: dict[str, int] = {}
    for row in rows:
        counts = json.loads(row[0] or "{}")
        for action, count in counts.items():
            totals[action] = totals.get(action, 0) + count

    return totals


def query_story_seed_activations(
    conn: sqlite3.Connection, days: int | None = None
) -> dict[str, int]:
    """Query story seed activation counts.

    Parameters
    ----------
    conn
        Database connection.
    days
        Optional filter to last N days.

    Returns
    -------
    dict[str, int]
        Mapping of seed name to activation count.
    """
    query = """
        SELECT sr.story_seeds_activated
        FROM sweep_results sr
        JOIN sweep_runs runs ON sr.run_id = runs.run_id
        WHERE sr.error IS NULL
    """
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND runs.timestamp >= ?"
        params.append(cutoff.isoformat())

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    totals: dict[str, int] = {}
    for row in rows:
        seeds = json.loads(row[0] or "[]")
        for seed in seeds:
            totals[seed] = totals.get(seed, 0) + 1

    return totals


def query_metrics_by_difficulty(
    conn: sqlite3.Connection, days: int | None = None
) -> dict[str, dict[str, list[float]]]:
    """Query stability metrics grouped by difficulty.

    Parameters
    ----------
    conn
        Database connection.
    days
        Optional filter to last N days.

    Returns
    -------
    dict[str, dict[str, list[float]]]
        Mapping of difficulty to metric name to list of values.
    """
    query = """
        SELECT sr.difficulty, sr.final_stability, sr.actions_taken, sr.ticks_run
        FROM sweep_results sr
        JOIN sweep_runs runs ON sr.run_id = runs.run_id
        WHERE sr.error IS NULL
    """
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND runs.timestamp >= ?"
        params.append(cutoff.isoformat())

    query += " ORDER BY sr.difficulty"

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    results: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        difficulty = row[0]
        if difficulty not in results:
            results[difficulty] = {"stability": [], "actions": [], "ticks": []}
        results[difficulty]["stability"].append(row[1])
        results[difficulty]["actions"].append(float(row[2]))
        results[difficulty]["ticks"].append(float(row[3]))

    return results


def query_historical_metrics(
    conn: sqlite3.Connection, days: int | None = None
) -> list[dict[str, Any]]:
    """Query historical metrics per run for trend analysis.

    Parameters
    ----------
    conn
        Database connection.
    days
        Optional filter to last N days.

    Returns
    -------
    list[dict[str, Any]]
        List of run summaries with timestamps and aggregate metrics.
    """
    query = """
        SELECT
            runs.run_id,
            runs.timestamp,
            runs.git_commit,
            AVG(sr.final_stability) as avg_stability,
            AVG(sr.actions_taken) as avg_actions,
            COUNT(*) as sweep_count
        FROM sweep_runs runs
        JOIN sweep_results sr ON runs.run_id = sr.run_id
        WHERE sr.error IS NULL
    """
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND runs.timestamp >= ?"
        params.append(cutoff.isoformat())

    query += " GROUP BY runs.run_id ORDER BY runs.timestamp"

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        results.append(
            {
                "run_id": row[0],
                "timestamp": row[1],
                "git_commit": row[2],
                "avg_stability": row[3],
                "avg_actions": row[4],
                "sweep_count": row[5],
            }
        )

    return results


def query_run_metrics(conn: sqlite3.Connection, run_id: int) -> dict[str, Any]:
    """Query aggregate metrics for a specific run.

    Parameters
    ----------
    conn
        Database connection.
    run_id
        Run ID to query.

    Returns
    -------
    dict[str, Any]
        Run metrics including averages and counts.
    """
    cursor = conn.execute(
        """
        SELECT
            AVG(final_stability) as avg_stability,
            AVG(actions_taken) as avg_actions,
            COUNT(*) as sweep_count,
            SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END) as completed
        FROM sweep_results
        WHERE run_id = ?
        """,
        (run_id,),
    )
    row = cursor.fetchone()

    if not row or row[2] == 0:
        return {}

    return {
        "avg_stability": row[0] or 0.0,
        "avg_actions": row[1] or 0.0,
        "sweep_count": row[2],
        "completed": row[3],
    }


# ============================================================================
# Statistical Analysis Functions
# ============================================================================


def compute_confidence_interval(
    values: list[float], confidence_level: float = 0.95
) -> ConfidenceInterval:
    """Compute confidence interval for a sample.

    Parameters
    ----------
    values
        Sample values.
    confidence_level
        Confidence level (default 0.95 for 95% CI).

    Returns
    -------
    ConfidenceInterval
        Computed confidence interval.
    """
    if len(values) < 2:
        mean = values[0] if values else 0.0
        return ConfidenceInterval(
            mean=mean,
            lower=mean,
            upper=mean,
            confidence_level=confidence_level,
            sample_size=len(values),
        )

    n = len(values)
    mean = sum(values) / n
    std_dev = (sum((x - mean) ** 2 for x in values) / (n - 1)) ** 0.5
    std_error = std_dev / (n**0.5)

    # Use t-distribution if scipy available, else approximate with z
    if HAS_SCIPY:
        t_value = stats.t.ppf((1 + confidence_level) / 2, n - 1)
    else:
        # Approximate z-value for 95% CI
        t_value = 1.96 if confidence_level == 0.95 else 2.576

    margin = t_value * std_error

    return ConfidenceInterval(
        mean=mean,
        lower=mean - margin,
        upper=mean + margin,
        confidence_level=confidence_level,
        sample_size=n,
    )


def perform_t_test(
    group_a: str,
    values_a: list[float],
    group_b: str,
    values_b: list[float],
    significance_level: float = 0.05,
) -> TTestResult:
    """Perform two-sample independent t-test.

    Parameters
    ----------
    group_a
        Name of first group.
    values_a
        Values for first group.
    group_b
        Name of second group.
    values_b
        Values for second group.
    significance_level
        Significance level (default 0.05).

    Returns
    -------
    TTestResult
        T-test result.
    """
    mean_a = sum(values_a) / len(values_a) if values_a else 0.0
    mean_b = sum(values_b) / len(values_b) if values_b else 0.0

    if len(values_a) < 2 or len(values_b) < 2:
        return TTestResult(
            group_a=group_a,
            group_b=group_b,
            mean_a=mean_a,
            mean_b=mean_b,
            t_statistic=0.0,
            p_value=1.0,
            is_significant=False,
            significance_level=significance_level,
        )

    if HAS_SCIPY:
        t_stat, p_value = stats.ttest_ind(values_a, values_b)
    else:
        # Simplified t-test calculation without scipy
        n_a, n_b = len(values_a), len(values_b)
        var_a = sum((x - mean_a) ** 2 for x in values_a) / (n_a - 1)
        var_b = sum((x - mean_b) ** 2 for x in values_b) / (n_b - 1)
        pooled_se = ((var_a / n_a) + (var_b / n_b)) ** 0.5
        t_stat = (mean_a - mean_b) / pooled_se if pooled_se > 0 else 0.0
        # Approximate p-value (very rough estimate)
        # For large t-stats, use smaller p-value to indicate significance
        p_value = 0.01 if abs(t_stat) > 2.0 else 0.5

    return TTestResult(
        group_a=group_a,
        group_b=group_b,
        mean_a=mean_a,
        mean_b=mean_b,
        t_statistic=float(t_stat),
        p_value=float(p_value),
        is_significant=bool(p_value < significance_level),
        significance_level=significance_level,
    )


def detect_trend(
    timestamps: list[str], values: list[float], metric_name: str
) -> TrendAnalysis:
    """Detect trend direction from time series data.

    Parameters
    ----------
    timestamps
        ISO-format timestamps.
    values
        Corresponding metric values.
    metric_name
        Name of the metric.

    Returns
    -------
    TrendAnalysis
        Trend analysis result.
    """
    if len(values) < 2:
        return TrendAnalysis(
            metric_name=metric_name,
            slope=0.0,
            trend_direction="stable",
            data_points=len(values),
            timestamps=timestamps,
            values=values,
        )

    # Simple linear regression to compute slope
    n = len(values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator > 0 else 0.0

    # Determine trend direction based on slope magnitude
    if abs(slope) < 0.001:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    return TrendAnalysis(
        metric_name=metric_name,
        slope=slope,
        trend_direction=direction,
        data_points=n,
        timestamps=timestamps,
        values=values,
    )


def detect_regression(
    baseline_metrics: dict[str, Any],
    current_metrics: dict[str, Any],
    threshold_percent: float = 10.0,
) -> list[RegressionAlert]:
    """Detect regressions by comparing metrics against baseline.

    Parameters
    ----------
    baseline_metrics
        Metrics from baseline run.
    current_metrics
        Metrics from current run.
    threshold_percent
        Deviation threshold to trigger alert (default 10%).

    Returns
    -------
    list[RegressionAlert]
        List of regression alerts.
    """
    alerts: list[RegressionAlert] = []

    for metric_name in ["avg_stability", "avg_actions"]:
        baseline = baseline_metrics.get(metric_name, 0.0)
        current = current_metrics.get(metric_name, 0.0)

        if baseline == 0:
            continue

        deviation = ((current - baseline) / baseline) * 100

        # For stability, a decrease is bad; for actions, large change is notable
        if metric_name == "avg_stability" and deviation < -threshold_percent:
            severity = "high" if deviation < -20 else "medium"
            alerts.append(
                RegressionAlert(
                    metric_name=metric_name,
                    baseline_value=baseline,
                    current_value=current,
                    deviation_percent=deviation,
                    severity=severity,
                    description=(
                        f"Stability dropped by {abs(deviation):.1f}% "
                        f"from {baseline:.3f} to {current:.3f}"
                    ),
                )
            )
        elif abs(deviation) > threshold_percent:
            severity = "low"
            alerts.append(
                RegressionAlert(
                    metric_name=metric_name,
                    baseline_value=baseline,
                    current_value=current,
                    deviation_percent=deviation,
                    severity=severity,
                    description=(
                        f"{metric_name} changed by {deviation:.1f}% "
                        f"from {baseline:.3f} to {current:.3f}"
                    ),
                )
            )

    return alerts


# ============================================================================
# Balance Analysis Functions
# ============================================================================


def analyze_dominant_strategies(
    win_rates: dict[str, list[float]], threshold: float = 0.10
) -> list[dict[str, Any]]:
    """Identify dominant strategies with win rate deltas above threshold.

    Parameters
    ----------
    win_rates
        Mapping of strategy to list of stability values.
    threshold
        Win rate delta threshold (default 0.10 = 10%).

    Returns
    -------
    list[dict[str, Any]]
        List of dominant strategy findings.
    """
    if len(win_rates) < 2:
        return []

    # Compute average win rate (stability >= 0.5) for each strategy
    strategy_win_rates: dict[str, float] = {}
    for strategy, stabilities in win_rates.items():
        wins = sum(1 for s in stabilities if s >= 0.5)
        strategy_win_rates[strategy] = wins / len(stabilities) if stabilities else 0.0

    sorted_strategies = sorted(
        strategy_win_rates.items(), key=lambda x: x[1], reverse=True
    )
    best_strategy, best_rate = sorted_strategies[0]
    worst_strategy, worst_rate = sorted_strategies[-1]

    results: list[dict[str, Any]] = []
    delta = best_rate - worst_rate

    if delta > threshold:
        results.append(
            {
                "type": "dominant_strategy",
                "strategy": best_strategy,
                "win_rate": round(best_rate, 4),
                "delta_from_worst": round(delta, 4),
                "worst_strategy": worst_strategy,
                "worst_win_rate": round(worst_rate, 4),
                "severity": "high" if delta > 0.20 else "medium",
            }
        )

    return results


def analyze_underperforming_mechanics(
    action_frequencies: dict[str, int], min_usage_threshold: float = 0.05
) -> list[dict[str, Any]]:
    """Identify underperforming mechanics that are rarely used.

    Parameters
    ----------
    action_frequencies
        Mapping of action name to total count.
    min_usage_threshold
        Threshold below which an action is considered underperforming.

    Returns
    -------
    list[dict[str, Any]]
        List of underperforming mechanics.
    """
    if not action_frequencies:
        return []

    total = sum(action_frequencies.values())
    if total == 0:
        return []

    results: list[dict[str, Any]] = []

    for action, count in action_frequencies.items():
        usage_rate = count / total
        if usage_rate < min_usage_threshold:
            results.append(
                {
                    "type": "underperforming_mechanic",
                    "action": action,
                    "usage_count": count,
                    "usage_rate": round(usage_rate, 4),
                    "threshold": min_usage_threshold,
                    "severity": "medium" if usage_rate < 0.01 else "low",
                }
            )

    return results


def identify_unused_story_seeds(
    activations: dict[str, int], all_seeds: list[str] | None = None
) -> list[str]:
    """Identify story seeds that were never activated.

    Parameters
    ----------
    activations
        Mapping of seed name to activation count.
    all_seeds
        Optional list of all known story seed IDs.

    Returns
    -------
    list[str]
        List of unused seed IDs.
    """
    if all_seeds:
        return [s for s in all_seeds if s not in activations]
    return []


def analyze_parameter_sensitivity(
    metrics_by_difficulty: dict[str, dict[str, list[float]]]
) -> dict[str, Any]:
    """Analyze how metrics vary with difficulty parameter.

    Parameters
    ----------
    metrics_by_difficulty
        Mapping of difficulty to metric to values.

    Returns
    -------
    dict[str, Any]
        Sensitivity analysis results.
    """
    results: dict[str, Any] = {"difficulties": {}, "sensitivity_summary": {}}

    for difficulty, metrics in metrics_by_difficulty.items():
        results["difficulties"][difficulty] = {}
        for metric_name, values in metrics.items():
            if values:
                avg = sum(values) / len(values)
                std = (
                    (sum((x - avg) ** 2 for x in values) / len(values)) ** 0.5
                    if len(values) > 1
                    else 0.0
                )
                results["difficulties"][difficulty][metric_name] = {
                    "mean": round(avg, 4),
                    "std": round(std, 4),
                    "count": len(values),
                }

    # Compute sensitivity (coefficient of variation) across difficulties
    for metric in ["stability", "actions", "ticks"]:
        means = [
            d.get(metric, {}).get("mean", 0.0)
            for d in results["difficulties"].values()
        ]
        if means and max(means) > 0:
            overall_mean = sum(means) / len(means)
            variance = sum((m - overall_mean) ** 2 for m in means) / len(means)
            cv = (variance**0.5) / overall_mean if overall_mean > 0 else 0.0
            results["sensitivity_summary"][metric] = {
                "coefficient_of_variation": round(cv, 4),
                "is_sensitive": cv > 0.1,
            }

    return results


# ============================================================================
# Visualization Functions
# ============================================================================


def generate_win_rate_chart(win_rates: dict[str, list[float]]) -> str | None:
    """Generate a bar chart of win rates by strategy.

    Parameters
    ----------
    win_rates
        Mapping of strategy to stability values.

    Returns
    -------
    str | None
        Base64-encoded PNG image, or None if matplotlib unavailable.
    """
    if not HAS_MATPLOTLIB or not win_rates:
        return None

    strategies = list(win_rates.keys())
    rates = [
        sum(1 for s in v if s >= 0.5) / len(v) if v else 0 for v in win_rates.values()
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(strategies, rates, color="steelblue")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Win Rate")
    ax.set_title("Win Rate by Strategy")
    ax.set_ylim(0, 1)
    for i, rate in enumerate(rates):
        ax.text(i, rate + 0.02, f"{rate:.1%}", ha="center")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_trend_chart(
    historical: list[dict[str, Any]], metric: str = "avg_stability"
) -> str | None:
    """Generate a line chart of metric trend over time.

    Parameters
    ----------
    historical
        List of run summaries with timestamps.
    metric
        Metric name to plot.

    Returns
    -------
    str | None
        Base64-encoded PNG image, or None if matplotlib unavailable.
    """
    if not HAS_MATPLOTLIB or not historical:
        return None

    timestamps = [h["timestamp"][:10] for h in historical]  # Date only
    values = [h.get(metric, 0) for h in historical]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(range(len(timestamps)), values, marker="o", color="steelblue")
    ax.set_xlabel("Run")
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(f"{metric.replace('_', ' ').title()} Over Time")
    ax.set_xticks(range(len(timestamps)))
    ax.set_xticklabels(timestamps, rotation=45, ha="right")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_action_distribution_chart(
    action_frequencies: dict[str, int],
) -> str | None:
    """Generate a pie chart of action distribution.

    Parameters
    ----------
    action_frequencies
        Mapping of action to count.

    Returns
    -------
    str | None
        Base64-encoded PNG image, or None if matplotlib unavailable.
    """
    if not HAS_MATPLOTLIB or not action_frequencies:
        return None

    actions = list(action_frequencies.keys())
    counts = list(action_frequencies.values())

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(counts, labels=actions, autopct="%1.1f%%", startangle=90)
    ax.set_title("Action Distribution")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ============================================================================
# Report Generation
# ============================================================================


def generate_balance_report(
    conn: sqlite3.Connection,
    days: int | None = None,
    all_story_seeds: list[str] | None = None,
) -> BalanceReport:
    """Generate comprehensive balance report from database.

    Parameters
    ----------
    conn
        Database connection.
    days
        Optional filter to last N days.
    all_story_seeds
        Optional list of all known story seeds for coverage analysis.

    Returns
    -------
    BalanceReport
        Complete balance analysis report.
    """
    # Query data
    win_rates = query_strategy_win_rates(conn, days)
    action_frequencies = query_action_frequencies(conn, days)
    seed_activations = query_story_seed_activations(conn, days)
    metrics_by_difficulty = query_metrics_by_difficulty(conn, days)
    historical = query_historical_metrics(conn, days)

    # Analyze balance
    dominant_strategies = analyze_dominant_strategies(win_rates)
    underperforming = analyze_underperforming_mechanics(action_frequencies)
    unused_seeds = identify_unused_story_seeds(seed_activations, all_story_seeds)
    parameter_sensitivity = analyze_parameter_sensitivity(metrics_by_difficulty)

    # Statistical analysis
    confidence_intervals: dict[str, ConfidenceInterval] = {}
    for strategy, stabilities in win_rates.items():
        confidence_intervals[f"{strategy}_stability"] = compute_confidence_interval(
            stabilities
        )

    # T-tests between strategies
    t_tests: list[TTestResult] = []
    strategies = list(win_rates.keys())
    for i, s1 in enumerate(strategies):
        for s2 in strategies[i + 1 :]:
            result = perform_t_test(s1, win_rates[s1], s2, win_rates[s2])
            t_tests.append(result)

    # Trend analysis
    trends: list[TrendAnalysis] = []
    if historical:
        timestamps = [h["timestamp"] for h in historical]
        stability_values = [h["avg_stability"] for h in historical]
        trends.append(detect_trend(timestamps, stability_values, "avg_stability"))

    # Generate charts
    charts: dict[str, str] = {}
    win_rate_chart = generate_win_rate_chart(win_rates)
    if win_rate_chart:
        charts["win_rate_distribution"] = win_rate_chart

    trend_chart = generate_trend_chart(historical)
    if trend_chart:
        charts["stability_trend"] = trend_chart

    action_chart = generate_action_distribution_chart(action_frequencies)
    if action_chart:
        charts["action_distribution"] = action_chart

    return BalanceReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        database_path=str(conn.execute("PRAGMA database_list").fetchone()[2]),
        dominant_strategies=dominant_strategies,
        underperforming_mechanics=underperforming,
        unused_story_seeds=unused_seeds,
        parameter_sensitivity=parameter_sensitivity,
        confidence_intervals=confidence_intervals,
        t_tests=t_tests,
        trends=trends,
        regressions=[],  # Populated by regression command
        charts=charts,
    )


def format_report_markdown(report: BalanceReport) -> str:
    """Format balance report as Markdown.

    Parameters
    ----------
    report
        Balance report to format.

    Returns
    -------
    str
        Markdown-formatted report.
    """
    lines = [
        "# Balance Analysis Report",
        "",
        f"**Generated:** {report.generated_at}",
        f"**Database:** {report.database_path}",
        "",
        "---",
        "",
        "## Dominant Strategies",
        "",
    ]

    if report.dominant_strategies:
        for ds in report.dominant_strategies:
            lines.append(
                f"- **{ds['strategy']}** has {ds['win_rate']:.1%} win rate "
                f"({ds['delta_from_worst']:.1%} higher than {ds['worst_strategy']})"
            )
            lines.append(f"  - Severity: {ds['severity']}")
    else:
        lines.append("No dominant strategies detected (win rate delta < 10%).")

    lines.extend(["", "## Underperforming Mechanics", ""])

    if report.underperforming_mechanics:
        for um in report.underperforming_mechanics:
            lines.append(
                f"- **{um['action']}** used {um['usage_count']} times "
                f"({um['usage_rate']:.1%} of total)"
            )
    else:
        lines.append("No underperforming mechanics detected.")

    lines.extend(["", "## Unused Story Seeds", ""])

    if report.unused_story_seeds:
        for seed in report.unused_story_seeds:
            lines.append(f"- {seed}")
    else:
        lines.append("All story seeds have been activated at least once.")

    lines.extend(["", "## Parameter Sensitivity Analysis", ""])

    if report.parameter_sensitivity.get("difficulties"):
        for diff, metrics in report.parameter_sensitivity["difficulties"].items():
            lines.append(f"### {diff}")
            for metric, stat in metrics.items():
                lines.append(
                    f"- {metric}: mean={stat['mean']:.3f}, std={stat['std']:.3f} "
                    f"(n={stat['count']})"
                )
        lines.append("")
        lines.append("### Sensitivity Summary")
        for metric, summary in report.parameter_sensitivity.get(
            "sensitivity_summary", {}
        ).items():
            status = "⚠️ Sensitive" if summary["is_sensitive"] else "✓ Stable"
            lines.append(
                f"- {metric}: CV={summary['coefficient_of_variation']:.3f} {status}"
            )
    else:
        lines.append("No difficulty-based parameter sensitivity data available.")

    lines.extend(["", "## Statistical Analysis", "", "### Confidence Intervals", ""])

    for name, ci in report.confidence_intervals.items():
        lines.append(
            f"- **{name}**: {ci.mean:.3f} [{ci.lower:.3f}, {ci.upper:.3f}] "
            f"(95% CI, n={ci.sample_size})"
        )

    lines.extend(["", "### T-Tests Between Strategies", ""])

    if report.t_tests:
        for tt in report.t_tests:
            sig = "✓ Significant" if tt.is_significant else "Not significant"
            lines.append(
                f"- **{tt.group_a}** vs **{tt.group_b}**: p={tt.p_value:.4f} {sig}"
            )
    else:
        lines.append("No t-tests performed.")

    lines.extend(["", "### Trend Analysis", ""])

    if report.trends:
        for trend in report.trends:
            lines.append(
                f"- **{trend.metric_name}**: {trend.trend_direction} "
                f"(slope={trend.slope:.4f}, n={trend.data_points})"
            )
    else:
        lines.append("Insufficient data for trend analysis.")

    lines.extend(["", "## Regressions", ""])

    if report.regressions:
        for reg in report.regressions:
            icon = "❌" if reg.severity == "high" else "⚠️"
            lines.append(f"- {icon} [{reg.severity.upper()}] {reg.description}")
    else:
        lines.append("No regressions detected.")

    return "\n".join(lines)


def format_report_html(report: BalanceReport) -> str:
    """Format balance report as HTML with embedded charts.

    Parameters
    ----------
    report
        Balance report to format.

    Returns
    -------
    str
        HTML-formatted report.
    """
    html = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        "<title>Balance Analysis Report</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 20px; max-width: 1200px; }",
        "h1 { color: #2c3e50; }",
        "h2 { color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }",
        "table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background-color: #3498db; color: white; }",
        ".severity-high { color: #e74c3c; font-weight: bold; }",
        ".severity-medium { color: #f39c12; }",
        ".severity-low { color: #95a5a6; }",
        ".chart { max-width: 100%; margin: 20px 0; }",
        "</style>",
        "</head><body>",
        "<h1>Balance Analysis Report</h1>",
        f"<p><strong>Generated:</strong> {report.generated_at}</p>",
        f"<p><strong>Database:</strong> {report.database_path}</p>",
    ]

    # Dominant Strategies
    html.append("<h2>Dominant Strategies</h2>")
    if report.dominant_strategies:
        html.append(
            "<table><tr><th>Strategy</th><th>Win Rate</th>"
            "<th>Delta</th><th>Severity</th></tr>"
        )
        for ds in report.dominant_strategies:
            html.append(
                f"<tr><td>{ds['strategy']}</td><td>{ds['win_rate']:.1%}</td>"
                f"<td>{ds['delta_from_worst']:.1%}</td>"
                f"<td class='severity-{ds['severity']}'>{ds['severity']}</td></tr>"
            )
        html.append("</table>")
    else:
        html.append("<p>No dominant strategies detected.</p>")

    # Win Rate Chart
    if "win_rate_distribution" in report.charts:
        html.append(
            f"<img class='chart' "
            f"src='data:image/png;base64,{report.charts['win_rate_distribution']}' />"
        )

    # Underperforming Mechanics
    html.append("<h2>Underperforming Mechanics</h2>")
    if report.underperforming_mechanics:
        html.append("<table><tr><th>Action</th><th>Count</th><th>Usage Rate</th></tr>")
        for um in report.underperforming_mechanics:
            html.append(
                f"<tr><td>{um['action']}</td><td>{um['usage_count']}</td>"
                f"<td>{um['usage_rate']:.2%}</td></tr>"
            )
        html.append("</table>")
    else:
        html.append("<p>No underperforming mechanics detected.</p>")

    # Action Distribution Chart
    if "action_distribution" in report.charts:
        html.append(
            f"<img class='chart' "
            f"src='data:image/png;base64,{report.charts['action_distribution']}' />"
        )

    # Unused Story Seeds
    html.append("<h2>Unused Story Seeds</h2>")
    if report.unused_story_seeds:
        html.append("<ul>")
        for seed in report.unused_story_seeds:
            html.append(f"<li>{seed}</li>")
        html.append("</ul>")
    else:
        html.append("<p>All story seeds activated.</p>")

    # Trends
    html.append("<h2>Trends</h2>")
    if report.trends:
        html.append("<table><tr><th>Metric</th><th>Direction</th><th>Slope</th></tr>")
        for trend in report.trends:
            html.append(
                f"<tr><td>{trend.metric_name}</td><td>{trend.trend_direction}</td>"
                f"<td>{trend.slope:.4f}</td></tr>"
            )
        html.append("</table>")
    else:
        html.append("<p>Insufficient data for trend analysis.</p>")

    # Trend Chart
    if "stability_trend" in report.charts:
        html.append(
            f"<img class='chart' "
            f"src='data:image/png;base64,{report.charts['stability_trend']}' />"
        )

    # Regressions
    html.append("<h2>Regressions</h2>")
    if report.regressions:
        html.append(
            "<table><tr><th>Metric</th><th>Baseline</th><th>Current</th>"
            "<th>Change</th><th>Severity</th></tr>"
        )
        for reg in report.regressions:
            html.append(
                f"<tr><td>{reg.metric_name}</td><td>{reg.baseline_value:.3f}</td>"
                f"<td>{reg.current_value:.3f}</td><td>{reg.deviation_percent:.1f}%</td>"
                f"<td class='severity-{reg.severity}'>{reg.severity}</td></tr>"
            )
        html.append("</table>")
    else:
        html.append("<p>No regressions detected.</p>")

    html.append("</body></html>")
    return "\n".join(html)


# ============================================================================
# CLI Commands
# ============================================================================


def cmd_report(args: argparse.Namespace) -> int:
    """Handle the report command."""
    db_path = args.database

    if not db_path.exists():
        sys.stderr.write(f"Error: Database not found: {db_path}\n")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        report = generate_balance_report(conn, days=args.days)

        if args.format == "html":
            output = format_report_html(report)
        elif args.format == "json":
            output = json.dumps(report.to_dict(), indent=2)
        else:
            output = format_report_markdown(report)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output)
            if not args.quiet:
                print(f"Report written to {args.output}")
        else:
            print(output)

        return 0
    finally:
        conn.close()


def cmd_regression(args: argparse.Namespace) -> int:
    """Handle the regression command."""
    db_path = args.database

    if not db_path.exists():
        sys.stderr.write(f"Error: Database not found: {db_path}\n")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        baseline_metrics = query_run_metrics(conn, args.baseline_run)
        current_metrics = query_run_metrics(conn, args.compare_run)

        if not baseline_metrics:
            sys.stderr.write(f"Error: Baseline run {args.baseline_run} not found\n")
            return 1

        if not current_metrics:
            sys.stderr.write(f"Error: Compare run {args.compare_run} not found\n")
            return 1

        alerts = detect_regression(baseline_metrics, current_metrics, args.threshold)

        if args.json:
            output = {"regressions": [a.to_dict() for a in alerts]}
            print(json.dumps(output, indent=2))
        else:
            print(
                f"\nRegression Analysis: Run {args.baseline_run} → "
                f"Run {args.compare_run}"
            )
            print("=" * 60)
            if alerts:
                for alert in alerts:
                    icon = "❌" if alert.severity == "high" else "⚠️"
                    print(f"{icon} [{alert.severity.upper()}] {alert.description}")
            else:
                print("✓ No significant regressions detected.")

        return 0
    finally:
        conn.close()


def cmd_trends(args: argparse.Namespace) -> int:
    """Handle the trends command."""
    db_path = args.database

    if not db_path.exists():
        sys.stderr.write(f"Error: Database not found: {db_path}\n")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        historical = query_historical_metrics(conn, days=args.days)

        if not historical:
            print("No historical data available for trend analysis.")
            return 0

        timestamps = [h["timestamp"] for h in historical]
        stability_values = [h["avg_stability"] for h in historical]
        action_values = [h["avg_actions"] for h in historical]

        trends = [
            detect_trend(timestamps, stability_values, "avg_stability"),
            detect_trend(timestamps, action_values, "avg_actions"),
        ]

        if args.json:
            output = {
                "trends": [t.to_dict() for t in trends],
                "data_points": len(historical),
            }
            print(json.dumps(output, indent=2))
        else:
            print("\nTrend Analysis")
            print("=" * 60)
            print(f"Data points: {len(historical)}")
            print("")
            for trend in trends:
                icon = {"increasing": "↑", "decreasing": "↓", "stable": "→"}
                print(
                    f"  {trend.metric_name}: {icon.get(trend.trend_direction, '?')} "
                    f"{trend.trend_direction} (slope: {trend.slope:.4f})"
                )

        return 0
    finally:
        conn.close()


def cmd_stats(args: argparse.Namespace) -> int:
    """Handle the stats command for confidence intervals and t-tests."""
    db_path = args.database

    if not db_path.exists():
        sys.stderr.write(f"Error: Database not found: {db_path}\n")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        win_rates = query_strategy_win_rates(conn, days=args.days)

        if not win_rates:
            print("No data available for statistical analysis.")
            return 0

        # Compute confidence intervals
        cis: dict[str, ConfidenceInterval] = {}
        for strategy, stabilities in win_rates.items():
            cis[strategy] = compute_confidence_interval(stabilities)

        # Perform t-tests
        t_tests: list[TTestResult] = []
        strategies = list(win_rates.keys())
        for i, s1 in enumerate(strategies):
            for s2 in strategies[i + 1 :]:
                t_tests.append(perform_t_test(s1, win_rates[s1], s2, win_rates[s2]))

        if args.json:
            output = {
                "confidence_intervals": {k: v.to_dict() for k, v in cis.items()},
                "t_tests": [t.to_dict() for t in t_tests],
            }
            print(json.dumps(output, indent=2))
        else:
            print("\nStatistical Analysis")
            print("=" * 60)
            print("\nConfidence Intervals (95%):")
            for strategy, ci in cis.items():
                print(
                    f"  {strategy}: {ci.mean:.3f} [{ci.lower:.3f}, {ci.upper:.3f}] "
                    f"(n={ci.sample_size})"
                )

            print("\nT-Tests:")
            for tt in t_tests:
                sig = "✓" if tt.is_significant else " "
                print(
                    f"  {sig} {tt.group_a} vs {tt.group_b}: "
                    f"t={tt.t_statistic:.3f}, p={tt.p_value:.4f}"
                )

        return 0
    finally:
        conn.close()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for balance analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze balance from aggregated sweep results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Markdown balance report
  python scripts/analyze_balance.py report --database build/sweep_results.db

  # Generate HTML report with charts
  python scripts/analyze_balance.py report --database build/sweep_results.db \\
      --format html --output build/balance_report.html

  # Detect regressions between runs
  python scripts/analyze_balance.py regression --database build/sweep_results.db \\
      --baseline-run 1 --compare-run 2

  # Show trends over time
  python scripts/analyze_balance.py trends --database build/sweep_results.db --days 30
""",
    )
    parser.add_argument(
        "--database",
        "-d",
        type=Path,
        default=Path("build/sweep_results.db"),
        help="Path to SQLite database (default: build/sweep_results.db)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate balance analysis report"
    )
    report_parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "html", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    report_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (prints to stdout if not specified)",
    )
    report_parser.add_argument(
        "--days",
        type=int,
        help="Filter to last N days",
    )
    report_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )

    # Regression command
    reg_parser = subparsers.add_parser(
        "regression", help="Detect regressions between runs"
    )
    reg_parser.add_argument(
        "--baseline-run",
        "-b",
        type=int,
        required=True,
        help="Baseline run ID",
    )
    reg_parser.add_argument(
        "--compare-run",
        "-c",
        type=int,
        required=True,
        help="Run ID to compare against baseline",
    )
    reg_parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=10.0,
        help="Deviation threshold percentage (default: 10)",
    )
    reg_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # Trends command
    trends_parser = subparsers.add_parser(
        "trends", help="Show metric trends over time"
    )
    trends_parser.add_argument(
        "--days",
        type=int,
        help="Filter to last N days",
    )
    trends_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Show statistical analysis (CIs and t-tests)"
    )
    stats_parser.add_argument(
        "--days",
        type=int,
        help="Filter to last N days",
    )
    stats_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args(argv)

    handlers = {
        "report": cmd_report,
        "regression": cmd_regression,
        "trends": cmd_trends,
        "stats": cmd_stats,
    }

    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
