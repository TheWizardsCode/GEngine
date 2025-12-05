#!/usr/bin/env python3
"""Manage balance validation baselines for CI integration.

Provides tools for storing, updating, and comparing balance sweep results
against baseline data for regression detection in CI workflows.

Examples
--------
Compare current sweep against baseline::

    python scripts/manage_balance_baseline.py compare \\
        --current build/ci_sweeps/batch_sweep_summary.json \\
        --baseline content/baselines/balance_baseline.json

Update baseline from successful sweep::

    python scripts/manage_balance_baseline.py update \\
        --source build/ci_sweeps/batch_sweep_summary.json \\
        --output content/baselines/balance_baseline.json

Generate comparison chart::

    python scripts/manage_balance_baseline.py chart \\
        --current build/ci_sweeps/batch_sweep_summary.json \\
        --baseline content/baselines/balance_baseline.json \\
        --output build/comparison_chart.png
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
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


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class RegressionAlert:
    """Alert for a detected balance regression."""

    metric_name: str
    strategy: str | None
    baseline_value: float
    current_value: float
    delta_percent: float
    severity: str  # "warning" or "failure"
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "strategy": self.strategy,
            "baseline_value": round(self.baseline_value, 4),
            "current_value": round(self.current_value, 4),
            "delta_percent": round(self.delta_percent, 2),
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class ComparisonResult:
    """Result of comparing current sweep against baseline."""

    timestamp: str
    baseline_path: str
    current_path: str
    regressions: list[RegressionAlert] = field(default_factory=list)
    baseline_stats: dict[str, Any] = field(default_factory=dict)
    current_stats: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    passed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "baseline_path": self.baseline_path,
            "current_path": self.current_path,
            "regressions": [r.to_dict() for r in self.regressions],
            "baseline_stats": self.baseline_stats,
            "current_stats": self.current_stats,
            "summary": self.summary,
            "passed": self.passed,
        }


@dataclass
class BaselineConfig:
    """Configuration for baseline thresholds."""

    stability_delta_warning: float = 5.0  # percentage
    stability_delta_failure: float = 10.0  # percentage
    win_rate_delta_warning: float = 5.0  # percentage
    win_rate_delta_failure: float = 10.0  # percentage
    unused_content_warning: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaselineConfig:
        return cls(
            stability_delta_warning=data.get("stability_delta_warning", 5.0),
            stability_delta_failure=data.get("stability_delta_failure", 10.0),
            win_rate_delta_warning=data.get("win_rate_delta_warning", 5.0),
            win_rate_delta_failure=data.get("win_rate_delta_failure", 10.0),
            unused_content_warning=data.get("unused_content_warning", True),
        )


# ============================================================================
# Baseline Management Functions
# ============================================================================


def load_baseline(path: Path) -> dict[str, Any] | None:
    """Load baseline data from JSON file.

    Parameters
    ----------
    path
        Path to baseline JSON file.

    Returns
    -------
    dict[str, Any] | None
        Baseline data or None if file doesn't exist.
    """
    if not path.exists():
        return None

    with open(path) as f:
        return json.load(f)


def load_sweep_summary(path: Path) -> dict[str, Any] | None:
    """Load sweep summary from batch_sweep_summary.json.

    Parameters
    ----------
    path
        Path to sweep summary JSON file.

    Returns
    -------
    dict[str, Any] | None
        Sweep summary data or None if file doesn't exist.
    """
    if not path.exists():
        return None

    with open(path) as f:
        return json.load(f)


def extract_strategy_stats(sweep_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract strategy statistics from sweep summary.

    Parameters
    ----------
    sweep_data
        Sweep summary data.

    Returns
    -------
    dict[str, dict[str, Any]]
        Strategy statistics keyed by strategy name.
    """
    return sweep_data.get("strategy_stats", {})


def extract_difficulty_stats(sweep_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract difficulty statistics from sweep summary.

    Parameters
    ----------
    sweep_data
        Sweep summary data.

    Returns
    -------
    dict[str, dict[str, Any]]
        Difficulty statistics keyed by difficulty name.
    """
    return sweep_data.get("difficulty_stats", {})


def compute_win_rate(strategy_stats: dict[str, Any]) -> float:
    """Compute win rate from strategy statistics.

    Win is defined as stability >= 0.5.

    Parameters
    ----------
    strategy_stats
        Statistics for a single strategy.

    Returns
    -------
    float
        Win rate as a fraction (0.0 to 1.0).
    """
    avg_stability = strategy_stats.get("avg_stability", 0.0)
    # Approximate win rate based on average stability
    # In actual sweep data, we'd count individual games
    if avg_stability >= 0.5:
        # Scale win rate based on how far above threshold
        return min(1.0, 0.5 + (avg_stability - 0.5))
    else:
        # Scale win rate based on how far below threshold
        return max(0.0, avg_stability)


def compare_strategy_stats(
    baseline_stats: dict[str, dict[str, Any]],
    current_stats: dict[str, dict[str, Any]],
    config: BaselineConfig,
) -> list[RegressionAlert]:
    """Compare strategy statistics against baseline.

    Parameters
    ----------
    baseline_stats
        Baseline strategy statistics.
    current_stats
        Current sweep strategy statistics.
    config
        Threshold configuration.

    Returns
    -------
    list[RegressionAlert]
        List of detected regressions.
    """
    alerts: list[RegressionAlert] = []

    for strategy, current in current_stats.items():
        baseline = baseline_stats.get(strategy)
        if not baseline:
            continue

        # Compare average stability
        baseline_stab = baseline.get("avg_stability", 0.0)
        current_stab = current.get("avg_stability", 0.0)

        if baseline_stab > 0:
            delta_percent = ((current_stab - baseline_stab) / baseline_stab) * 100

            # Only flag decreases (negative deltas)
            if delta_percent < -config.stability_delta_failure:
                alerts.append(
                    RegressionAlert(
                        metric_name="avg_stability",
                        strategy=strategy,
                        baseline_value=baseline_stab,
                        current_value=current_stab,
                        delta_percent=delta_percent,
                        severity="failure",
                        description=(
                            f"Strategy '{strategy}' stability dropped by "
                            f"{abs(delta_percent):.1f}% (from {baseline_stab:.3f} "
                            f"to {current_stab:.3f})"
                        ),
                    )
                )
            elif delta_percent < -config.stability_delta_warning:
                alerts.append(
                    RegressionAlert(
                        metric_name="avg_stability",
                        strategy=strategy,
                        baseline_value=baseline_stab,
                        current_value=current_stab,
                        delta_percent=delta_percent,
                        severity="warning",
                        description=(
                            f"Strategy '{strategy}' stability decreased by "
                            f"{abs(delta_percent):.1f}% (from {baseline_stab:.3f} "
                            f"to {current_stab:.3f})"
                        ),
                    )
                )

        # Compare win rates - prefer explicit win_rate if available
        baseline_wr = baseline.get("win_rate")
        current_wr = current.get("win_rate")

        # Only compute from stability if not explicitly provided
        if baseline_wr is None:
            baseline_wr = compute_win_rate(baseline)
        if current_wr is None:
            current_wr = compute_win_rate(current)

        if baseline_wr > 0:
            wr_delta_percent = ((current_wr - baseline_wr) / baseline_wr) * 100

            if wr_delta_percent < -config.win_rate_delta_failure:
                alerts.append(
                    RegressionAlert(
                        metric_name="win_rate",
                        strategy=strategy,
                        baseline_value=baseline_wr,
                        current_value=current_wr,
                        delta_percent=wr_delta_percent,
                        severity="failure",
                        description=(
                            f"Strategy '{strategy}' win rate dropped by "
                            f"{abs(wr_delta_percent):.1f}% (from {baseline_wr:.1%} "
                            f"to {current_wr:.1%})"
                        ),
                    )
                )
            elif wr_delta_percent < -config.win_rate_delta_warning:
                alerts.append(
                    RegressionAlert(
                        metric_name="win_rate",
                        strategy=strategy,
                        baseline_value=baseline_wr,
                        current_value=current_wr,
                        delta_percent=wr_delta_percent,
                        severity="warning",
                        description=(
                            f"Strategy '{strategy}' win rate decreased by "
                            f"{abs(wr_delta_percent):.1f}% (from {baseline_wr:.1%} "
                            f"to {current_wr:.1%})"
                        ),
                    )
                )

    return alerts


def compare_against_baseline(
    baseline_path: Path,
    current_path: Path,
    stability_threshold: float = 5.0,
) -> ComparisonResult:
    """Compare current sweep results against baseline.

    Parameters
    ----------
    baseline_path
        Path to baseline JSON file.
    current_path
        Path to current sweep summary.
    stability_threshold
        Threshold percentage for stability regression detection.

    Returns
    -------
    ComparisonResult
        Comparison result with any detected regressions.
    """
    baseline = load_baseline(baseline_path)
    current = load_sweep_summary(current_path)

    result = ComparisonResult(
        timestamp=datetime.now(timezone.utc).isoformat(),
        baseline_path=str(baseline_path),
        current_path=str(current_path),
    )

    if not baseline:
        result.summary = "No baseline found - establishing new baseline"
        result.passed = True
        if current:
            result.current_stats = {
                "strategy_stats": extract_strategy_stats(current),
                "difficulty_stats": extract_difficulty_stats(current),
            }
        return result

    if not current:
        result.summary = "No current sweep data found"
        result.passed = False
        return result

    # Extract stats
    baseline_strategy_stats = baseline.get("strategy_stats", {})
    current_strategy_stats = extract_strategy_stats(current)

    result.baseline_stats = {
        "strategy_stats": baseline_strategy_stats,
        "difficulty_stats": baseline.get("difficulty_stats", {}),
    }
    result.current_stats = {
        "strategy_stats": current_strategy_stats,
        "difficulty_stats": extract_difficulty_stats(current),
    }

    # Get threshold config from baseline or use defaults
    thresholds = baseline.get("thresholds", {})
    config = BaselineConfig.from_dict(thresholds)
    # Override with CLI threshold if provided
    config.stability_delta_warning = stability_threshold
    config.stability_delta_failure = stability_threshold * 2

    # Compare strategy stats
    alerts = compare_strategy_stats(
        baseline_strategy_stats, current_strategy_stats, config
    )
    result.regressions = alerts

    # Determine pass/fail
    failures = [a for a in alerts if a.severity == "failure"]
    warnings = [a for a in alerts if a.severity == "warning"]

    if failures:
        result.passed = False
        result.summary = (
            f"FAILED: {len(failures)} regression(s) detected, "
            f"{len(warnings)} warning(s)"
        )
    elif warnings:
        result.passed = True
        result.summary = f"PASSED with {len(warnings)} warning(s)"
    else:
        result.passed = True
        result.summary = "PASSED: No regressions detected"

    return result


def create_baseline(
    sweep_path: Path,
    output_path: Path,
    git_commit: str | None = None,
) -> dict[str, Any]:
    """Create a new baseline from sweep results.

    Parameters
    ----------
    sweep_path
        Path to sweep summary JSON file.
    output_path
        Path to write baseline JSON file.
    git_commit
        Git commit hash to record in baseline.

    Returns
    -------
    dict[str, Any]
        Created baseline data.
    """
    sweep = load_sweep_summary(sweep_path)
    if not sweep:
        raise ValueError(f"Could not load sweep data from {sweep_path}")

    now = datetime.now(timezone.utc).isoformat()

    baseline = {
        "version": "1.0",
        "created_at": now,
        "updated_at": now,
        "git_commit": git_commit or sweep.get("metadata", {}).get("git_commit"),
        "description": "Balance validation baseline",
        "strategy_stats": extract_strategy_stats(sweep),
        "difficulty_stats": extract_difficulty_stats(sweep),
        "total_sweeps": sweep.get("total_sweeps", 0),
        "completed_sweeps": sweep.get("completed_sweeps", 0),
        "failed_sweeps": sweep.get("failed_sweeps", 0),
        "total_duration_seconds": sweep.get("total_duration_seconds", 0),
        "thresholds": {
            "stability_delta_warning": 5.0,
            "stability_delta_failure": 10.0,
            "win_rate_delta_warning": 5.0,
            "win_rate_delta_failure": 10.0,
            "unused_content_warning": True,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2)

    return baseline


def update_baseline(
    sweep_path: Path,
    output_path: Path,
    git_commit: str | None = None,
) -> dict[str, Any]:
    """Update existing baseline with new sweep results.

    Parameters
    ----------
    sweep_path
        Path to sweep summary JSON file.
    output_path
        Path to write updated baseline JSON file.
    git_commit
        Git commit hash to record.

    Returns
    -------
    dict[str, Any]
        Updated baseline data.
    """
    existing = load_baseline(output_path)
    sweep = load_sweep_summary(sweep_path)

    if not sweep:
        raise ValueError(f"Could not load sweep data from {sweep_path}")

    now = datetime.now(timezone.utc).isoformat()

    baseline = {
        "version": "1.0",
        "created_at": existing.get("created_at", now) if existing else now,
        "updated_at": now,
        "git_commit": git_commit or sweep.get("metadata", {}).get("git_commit"),
        "description": "Balance validation baseline",
        "strategy_stats": extract_strategy_stats(sweep),
        "difficulty_stats": extract_difficulty_stats(sweep),
        "total_sweeps": sweep.get("total_sweeps", 0),
        "completed_sweeps": sweep.get("completed_sweeps", 0),
        "failed_sweeps": sweep.get("failed_sweeps", 0),
        "total_duration_seconds": sweep.get("total_duration_seconds", 0),
        "thresholds": existing.get("thresholds", {}) if existing else {
            "stability_delta_warning": 5.0,
            "stability_delta_failure": 10.0,
            "win_rate_delta_warning": 5.0,
            "win_rate_delta_failure": 10.0,
            "unused_content_warning": True,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2)

    return baseline


# ============================================================================
# Visualization Functions
# ============================================================================


def generate_comparison_chart(
    baseline_path: Path,
    current_path: Path,
    output_path: Path,
) -> bool:
    """Generate comparison chart showing baseline vs current stats.

    Parameters
    ----------
    baseline_path
        Path to baseline JSON file.
    current_path
        Path to current sweep summary.
    output_path
        Path to save chart image.

    Returns
    -------
    bool
        True if chart was generated successfully.
    """
    if not HAS_MATPLOTLIB:
        sys.stderr.write("Warning: matplotlib not available for chart generation\n")
        return False

    baseline = load_baseline(baseline_path)
    current = load_sweep_summary(current_path)

    if not baseline or not current:
        sys.stderr.write("Warning: Missing baseline or current data for chart\n")
        return False

    baseline_stats = baseline.get("strategy_stats", {})
    current_stats = extract_strategy_stats(current)

    # Get strategies present in both
    strategies = sorted(set(baseline_stats.keys()) & set(current_stats.keys()))
    if not strategies:
        sys.stderr.write("Warning: No common strategies to compare\n")
        return False

    # Extract data for plotting
    baseline_stability = [baseline_stats[s].get("avg_stability", 0) for s in strategies]
    current_stability = [current_stats[s].get("avg_stability", 0) for s in strategies]

    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart comparing stability
    x = range(len(strategies))
    width = 0.35

    ax1.bar([i - width / 2 for i in x], baseline_stability, width, label="Baseline")
    ax1.bar([i + width / 2 for i in x], current_stability, width, label="Current")
    ax1.set_xlabel("Strategy")
    ax1.set_ylabel("Average Stability")
    ax1.set_title("Strategy Stability: Baseline vs Current")
    ax1.set_xticks(x)
    ax1.set_xticklabels(strategies)
    ax1.legend()
    ax1.set_ylim(0, 1)

    # Delta chart
    deltas = [
        ((c - b) / b * 100) if b > 0 else 0
        for b, c in zip(baseline_stability, current_stability, strict=True)
    ]
    colors = ["green" if d >= 0 else "red" for d in deltas]

    ax2.bar(strategies, deltas, color=colors)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax2.axhline(y=-5, color="orange", linestyle="--", linewidth=0.5, label="Warning")
    ax2.axhline(y=-10, color="red", linestyle="--", linewidth=0.5, label="Failure")
    ax2.set_xlabel("Strategy")
    ax2.set_ylabel("Stability Delta (%)")
    ax2.set_title("Stability Change from Baseline")
    ax2.legend()

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return True


# ============================================================================
# CLI Commands
# ============================================================================


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle the compare command."""
    result = compare_against_baseline(
        baseline_path=args.baseline,
        current_path=args.current,
        stability_threshold=args.stability_threshold,
    )

    # Write output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.to_dict(), indent=2))
        if not args.quiet:
            print(f"Comparison result written to {args.output}")

    # Print summary
    if not args.quiet:
        print(f"\n{result.summary}")
        if result.regressions:
            print("\nRegressions detected:")
            for reg in result.regressions:
                icon = "❌" if reg.severity == "failure" else "⚠️"
                print(f"  {icon} [{reg.severity.upper()}] {reg.description}")

    return 0 if result.passed else 1


def cmd_update(args: argparse.Namespace) -> int:
    """Handle the update command."""
    try:
        baseline = update_baseline(
            sweep_path=args.source,
            output_path=args.output,
            git_commit=args.git_commit,
        )

        if not args.quiet:
            print(f"Baseline updated: {args.output}")
            print(f"  Strategies: {list(baseline.get('strategy_stats', {}).keys())}")
            print(f"  Total sweeps: {baseline.get('total_sweeps', 0)}")
            print(f"  Git commit: {baseline.get('git_commit', 'N/A')}")

        return 0
    except Exception as e:
        sys.stderr.write(f"Error updating baseline: {e}\n")
        return 1


def cmd_create(args: argparse.Namespace) -> int:
    """Handle the create command."""
    try:
        baseline = create_baseline(
            sweep_path=args.source,
            output_path=args.output,
            git_commit=args.git_commit,
        )

        if not args.quiet:
            print(f"Baseline created: {args.output}")
            print(f"  Strategies: {list(baseline.get('strategy_stats', {}).keys())}")
            print(f"  Total sweeps: {baseline.get('total_sweeps', 0)}")

        return 0
    except Exception as e:
        sys.stderr.write(f"Error creating baseline: {e}\n")
        return 1


def cmd_chart(args: argparse.Namespace) -> int:
    """Handle the chart command."""
    success = generate_comparison_chart(
        baseline_path=args.baseline,
        current_path=args.current,
        output_path=args.output,
    )

    if success:
        if not args.quiet:
            print(f"Chart generated: {args.output}")
        return 0
    else:
        sys.stderr.write("Failed to generate chart\n")
        return 1


def cmd_show(args: argparse.Namespace) -> int:
    """Handle the show command."""
    baseline = load_baseline(args.baseline)

    if not baseline:
        sys.stderr.write(f"Baseline not found: {args.baseline}\n")
        return 1

    if args.json:
        print(json.dumps(baseline, indent=2))
    else:
        print(f"\nBaseline: {args.baseline}")
        print("=" * 60)
        print(f"Version: {baseline.get('version', 'N/A')}")
        print(f"Created: {baseline.get('created_at', 'N/A')}")
        print(f"Updated: {baseline.get('updated_at', 'N/A')}")
        print(f"Git commit: {baseline.get('git_commit', 'N/A')}")
        print(f"\nTotal sweeps: {baseline.get('total_sweeps', 0)}")
        print(f"Completed: {baseline.get('completed_sweeps', 0)}")
        print(f"Failed: {baseline.get('failed_sweeps', 0)}")

        print("\nStrategy Stats:")
        for strategy, stats in baseline.get("strategy_stats", {}).items():
            avg_stab = stats.get("avg_stability", 0)
            win_rate = stats.get("win_rate", compute_win_rate(stats))
            print(f"  {strategy}: stability={avg_stab:.3f}, win_rate={win_rate:.1%}")

        print("\nThresholds:")
        thresholds = baseline.get("thresholds", {})
        print(f"  Stability warning: {thresholds.get('stability_delta_warning', 5)}%")
        print(f"  Stability failure: {thresholds.get('stability_delta_failure', 10)}%")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for baseline management."""
    parser = argparse.ArgumentParser(
        description="Manage balance validation baselines for CI integration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare current sweep against baseline
  python scripts/manage_balance_baseline.py compare \\
      --current build/ci_sweeps/batch_sweep_summary.json \\
      --baseline content/baselines/balance_baseline.json

  # Update baseline from successful sweep
  python scripts/manage_balance_baseline.py update \\
      --source build/ci_sweeps/batch_sweep_summary.json \\
      --output content/baselines/balance_baseline.json

  # Generate comparison chart
  python scripts/manage_balance_baseline.py chart \\
      --current build/ci_sweeps/batch_sweep_summary.json \\
      --baseline content/baselines/balance_baseline.json \\
      --output build/comparison.png
""",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare current sweep against baseline"
    )
    compare_parser.add_argument(
        "--current",
        "-c",
        type=Path,
        required=True,
        help="Path to current sweep summary JSON",
    )
    compare_parser.add_argument(
        "--baseline",
        "-b",
        type=Path,
        required=True,
        help="Path to baseline JSON file",
    )
    compare_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to write comparison result JSON",
    )
    compare_parser.add_argument(
        "--stability-threshold",
        type=float,
        default=5.0,
        help="Stability delta threshold percentage (default: 5.0)",
    )
    compare_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )

    # Update command
    update_parser = subparsers.add_parser(
        "update", help="Update baseline from sweep results"
    )
    update_parser.add_argument(
        "--source",
        "-s",
        type=Path,
        required=True,
        help="Path to sweep summary JSON",
    )
    update_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Path to baseline JSON file to update",
    )
    update_parser.add_argument(
        "--git-commit",
        type=str,
        help="Git commit hash to record",
    )
    update_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )

    # Create command
    create_parser = subparsers.add_parser(
        "create", help="Create new baseline from sweep results"
    )
    create_parser.add_argument(
        "--source",
        "-s",
        type=Path,
        required=True,
        help="Path to sweep summary JSON",
    )
    create_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Path to write new baseline JSON",
    )
    create_parser.add_argument(
        "--git-commit",
        type=str,
        help="Git commit hash to record",
    )
    create_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )

    # Chart command
    chart_parser = subparsers.add_parser(
        "chart", help="Generate comparison chart"
    )
    chart_parser.add_argument(
        "--current",
        "-c",
        type=Path,
        required=True,
        help="Path to current sweep summary JSON",
    )
    chart_parser.add_argument(
        "--baseline",
        "-b",
        type=Path,
        required=True,
        help="Path to baseline JSON file",
    )
    chart_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Path to save chart image",
    )
    chart_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )

    # Show command
    show_parser = subparsers.add_parser(
        "show", help="Display baseline information"
    )
    show_parser.add_argument(
        "--baseline",
        "-b",
        type=Path,
        default=Path("content/baselines/balance_baseline.json"),
        help="Path to baseline JSON file",
    )
    show_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args(argv)

    handlers = {
        "compare": cmd_compare,
        "update": cmd_update,
        "create": cmd_create,
        "chart": cmd_chart,
        "show": cmd_show,
    }

    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
