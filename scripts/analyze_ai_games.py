#!/usr/bin/env python3
"""Analyze AI tournament results for balance and coverage insights.

Reads tournament results JSON and generates reports identifying:
- Win rate comparisons across strategies
- Balance anomalies (dominant strategies, overpowered actions)
- Story seed coverage (unused/underused seeds)
- Action distribution patterns

Examples
--------
Analyze a tournament results file::

    uv run python scripts/analyze_ai_games.py --input build/tournament.json

Generate detailed report::

    uv run python scripts/analyze_ai_games.py \\
        --input build/tournament.json --verbose --output build/analysis.json

Compare against authored story seeds::

    uv run python scripts/analyze_ai_games.py \\
        --input build/tournament.json --world default
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence


@dataclass
class BalanceAnomaly:
    """Represents a detected balance issue."""

    anomaly_type: str
    severity: str  # "low", "medium", "high"
    description: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "data": self.data,
        }


@dataclass
class AnalysisReport:
    """Complete analysis report from tournament data."""

    tournament_config: dict[str, Any]
    strategy_comparison: dict[str, dict[str, Any]]
    win_rate_analysis: dict[str, Any]
    action_analysis: dict[str, Any]
    story_seed_analysis: dict[str, Any]
    anomalies: list[BalanceAnomaly]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tournament_config": self.tournament_config,
            "strategy_comparison": self.strategy_comparison,
            "win_rate_analysis": self.win_rate_analysis,
            "action_analysis": self.action_analysis,
            "story_seed_analysis": self.story_seed_analysis,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "recommendations": self.recommendations,
        }


def load_tournament_results(path: Path) -> dict[str, Any]:
    """Load tournament results from JSON file."""
    with open(path) as f:
        return json.load(f)


def get_authored_story_seeds(world: str) -> list[str]:
    """Load story seed IDs from the world content."""
    try:
        import yaml

        seeds_path = Path(f"content/worlds/{world}/story_seeds.yml")
        if not seeds_path.exists():
            return []

        with open(seeds_path) as f:
            data = yaml.safe_load(f)
            if not data or "seeds" not in data:
                return []
            return [s.get("id", "") for s in data.get("seeds", []) if s.get("id")]
    except Exception:
        return []


def analyze_win_rates(strategy_stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Analyze win rate patterns across strategies."""
    win_rates = {s: stats.get("win_rate", 0.0) for s, stats in strategy_stats.items()}

    if not win_rates:
        return {"error": "No strategy data available"}

    sorted_rates = sorted(win_rates.items(), key=lambda x: x[1], reverse=True)
    best_strategy, best_rate = sorted_rates[0]
    worst_strategy, worst_rate = sorted_rates[-1]
    win_rate_delta = best_rate - worst_rate

    avg_win_rate = sum(win_rates.values()) / len(win_rates)
    variance = sum((r - avg_win_rate) ** 2 for r in win_rates.values()) / len(win_rates)

    return {
        "win_rates": {k: round(v, 4) for k, v in win_rates.items()},
        "best_strategy": best_strategy,
        "best_win_rate": round(best_rate, 4),
        "worst_strategy": worst_strategy,
        "worst_win_rate": round(worst_rate, 4),
        "win_rate_delta": round(win_rate_delta, 4),
        "average_win_rate": round(avg_win_rate, 4),
        "win_rate_variance": round(variance, 6),
        "is_balanced": win_rate_delta < 0.15,
    }


def analyze_actions(strategy_stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Analyze action usage patterns across strategies."""
    # Aggregate action counts
    total_actions: dict[str, int] = {}
    action_by_strategy: dict[str, dict[str, int]] = {}

    for strategy, stats in strategy_stats.items():
        breakdown = stats.get("action_breakdown", {})
        action_by_strategy[strategy] = breakdown
        for action, count in breakdown.items():
            total_actions[action] = total_actions.get(action, 0) + count

    if not total_actions:
        return {"error": "No action data available"}

    # Find most/least used actions
    sorted_actions = sorted(total_actions.items(), key=lambda x: x[1], reverse=True)
    most_used = sorted_actions[0] if sorted_actions else ("none", 0)
    least_used = sorted_actions[-1] if sorted_actions else ("none", 0)

    # Calculate action dominance
    total = sum(total_actions.values())
    action_percentages = (
        {a: c / total for a, c in total_actions.items()} if total else {}
    )

    return {
        "total_actions": total_actions,
        "action_by_strategy": action_by_strategy,
        "most_used_action": most_used[0],
        "most_used_count": most_used[1],
        "least_used_action": least_used[0],
        "least_used_count": least_used[1],
        "action_percentages": {k: round(v, 4) for k, v in action_percentages.items()},
        "dominant_action": (
            most_used[0] if action_percentages.get(most_used[0], 0) > 0.5 else None
        ),
    }


def analyze_story_seeds(
    results: dict[str, Any],
    authored_seeds: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze story seed activation patterns."""
    seen_seeds = set(results.get("all_story_seeds_seen", []))

    # Aggregate per-game seed data
    seed_counts: dict[str, int] = {}
    total_games = 0

    for _strategy, games in results.get("games", {}).items():
        for game in games:
            if game.get("error") is None:
                total_games += 1
                for seed in game.get("story_seeds_activated", []):
                    seed_counts[seed] = seed_counts.get(seed, 0) + 1

    # Compare against authored seeds
    unused_seeds: list[str] = []
    if authored_seeds:
        unused_seeds = [s for s in authored_seeds if s not in seen_seeds]

    # Calculate activation rates
    activation_rates = {}
    if total_games > 0:
        activation_rates = {s: c / total_games for s, c in seed_counts.items()}

    return {
        "seeds_seen": sorted(seen_seeds),
        "seed_counts": seed_counts,
        "activation_rates": {k: round(v, 4) for k, v in activation_rates.items()},
        "total_games_analyzed": total_games,
        "authored_seeds": authored_seeds or [],
        "unused_seeds": unused_seeds,
        "coverage_rate": (
            len(seen_seeds) / len(authored_seeds)
            if authored_seeds
            else 1.0
        ),
    }


def detect_anomalies(
    win_rate_analysis: dict[str, Any],
    action_analysis: dict[str, Any],
    story_seed_analysis: dict[str, Any],
    strategy_stats: dict[str, dict[str, Any]],
) -> list[BalanceAnomaly]:
    """Detect balance anomalies from analysis results."""
    anomalies: list[BalanceAnomaly] = []

    # Check for dominant strategy
    if win_rate_analysis.get("win_rate_delta", 0) > 0.2:
        anomalies.append(
            BalanceAnomaly(
                anomaly_type="dominant_strategy",
                severity="high",
                description=(
                    f"Strategy '{win_rate_analysis['best_strategy']}' has "
                    f"significantly higher win rate "
                    f"({win_rate_analysis['best_win_rate']:.1%}) "
                    f"than '{win_rate_analysis['worst_strategy']}' "
                    f"({win_rate_analysis['worst_win_rate']:.1%})"
                ),
                data={
                    "best_strategy": win_rate_analysis["best_strategy"],
                    "worst_strategy": win_rate_analysis["worst_strategy"],
                    "delta": win_rate_analysis["win_rate_delta"],
                },
            )
        )
    elif win_rate_analysis.get("win_rate_delta", 0) > 0.15:
        anomalies.append(
            BalanceAnomaly(
                anomaly_type="strategy_imbalance",
                severity="medium",
                description=(
                    f"Moderate win rate gap between strategies "
                    f"({win_rate_analysis['win_rate_delta']:.1%})"
                ),
                data={"delta": win_rate_analysis["win_rate_delta"]},
            )
        )

    # Check for dominant action
    dominant_action = action_analysis.get("dominant_action")
    if dominant_action:
        pct = action_analysis["action_percentages"].get(dominant_action, 0)
        anomalies.append(
            BalanceAnomaly(
                anomaly_type="dominant_action",
                severity="medium",
                description=(
                    f"Action '{dominant_action}' accounts for {pct:.1%} of all actions"
                ),
                data={
                    "action": dominant_action,
                    "percentage": pct,
                },
            )
        )

    # Check for unused story seeds
    unused = story_seed_analysis.get("unused_seeds", [])
    if unused:
        severity = "high" if len(unused) > 2 else "low"
        anomalies.append(
            BalanceAnomaly(
                anomaly_type="unused_story_seeds",
                severity=severity,
                description=(
                    f"{len(unused)} story seeds never activated: "
                    f"{', '.join(unused)}"
                ),
                data={"unused_seeds": unused},
            )
        )

    # Check for low seed coverage
    coverage = story_seed_analysis.get("coverage_rate", 1.0)
    if coverage < 0.5 and story_seed_analysis.get("authored_seeds"):
        anomalies.append(
            BalanceAnomaly(
                anomaly_type="low_seed_coverage",
                severity="medium",
                description=f"Only {coverage:.1%} of story seeds were activated",
                data={"coverage_rate": coverage},
            )
        )

    # Check for strategy with very low action count
    for strategy, stats in strategy_stats.items():
        avg_actions = stats.get("avg_actions", 0)
        if avg_actions < 1.0:
            anomalies.append(
                BalanceAnomaly(
                    anomaly_type="low_activity_strategy",
                    severity="low",
                    description=(
                        f"Strategy '{strategy}' averages only {avg_actions:.1f} "
                        "actions per game"
                    ),
                    data={"strategy": strategy, "avg_actions": avg_actions},
                )
            )

    return anomalies


def generate_recommendations(
    anomalies: list[BalanceAnomaly],
    win_rate_analysis: dict[str, Any],
    action_analysis: dict[str, Any],
    story_seed_analysis: dict[str, Any],
) -> list[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations: list[str] = []

    # Strategy balance recommendations
    if not win_rate_analysis.get("is_balanced", True):
        best = win_rate_analysis.get("best_strategy", "")
        worst = win_rate_analysis.get("worst_strategy", "")
        recommendations.append(
            f"Consider buffing '{worst}' strategy or adding constraints to '{best}'"
        )

    # Action balance recommendations
    dominant = action_analysis.get("dominant_action")
    if dominant:
        recommendations.append(
            f"Review effectiveness of '{dominant}' action - may be overpowered"
        )

    least_used = action_analysis.get("least_used_action")
    if least_used and action_analysis.get("least_used_count", 0) < 5:
        recommendations.append(
            f"Action '{least_used}' is rarely used - consider making it more attractive"
        )

    # Story seed recommendations
    unused = story_seed_analysis.get("unused_seeds", [])
    if unused:
        recommendations.append(
            f"Review trigger conditions for unused seeds: {', '.join(unused[:3])}"
        )

    coverage = story_seed_analysis.get("coverage_rate", 1.0)
    if coverage < 0.7 and story_seed_analysis.get("authored_seeds"):
        recommendations.append(
            "Consider increasing game length or lowering seed activation thresholds "
            "to improve coverage"
        )

    # General recommendations
    if not recommendations:
        recommendations.append(
            "No significant balance issues detected - system appears well-tuned"
        )

    return recommendations


def analyze_tournament(
    results: dict[str, Any],
    authored_seeds: list[str] | None = None,
) -> AnalysisReport:
    """Perform complete analysis on tournament results.

    Parameters
    ----------
    results
        Tournament results dictionary (from JSON file).
    authored_seeds
        Optional list of all authored story seed IDs for coverage comparison.

    Returns
    -------
    AnalysisReport
        Complete analysis with findings, anomalies, and recommendations.
    """
    strategy_stats = results.get("strategy_stats", {})

    win_rate_analysis = analyze_win_rates(strategy_stats)
    action_analysis = analyze_actions(strategy_stats)
    story_seed_analysis = analyze_story_seeds(results, authored_seeds)

    anomalies = detect_anomalies(
        win_rate_analysis,
        action_analysis,
        story_seed_analysis,
        strategy_stats,
    )

    recommendations = generate_recommendations(
        anomalies,
        win_rate_analysis,
        action_analysis,
        story_seed_analysis,
    )

    return AnalysisReport(
        tournament_config=results.get("config", {}),
        strategy_comparison={
            strategy: {
                "win_rate": stats.get("win_rate", 0.0),
                "avg_stability": stats.get("avg_stability", 0.0),
                "avg_actions": stats.get("avg_actions", 0.0),
                "games_completed": stats.get("games_completed", 0),
            }
            for strategy, stats in strategy_stats.items()
        },
        win_rate_analysis=win_rate_analysis,
        action_analysis=action_analysis,
        story_seed_analysis=story_seed_analysis,
        anomalies=anomalies,
        recommendations=recommendations,
    )


def print_analysis_report(report: AnalysisReport) -> None:
    """Print a human-readable analysis report."""
    print("\n" + "=" * 80)
    print("AI TOURNAMENT ANALYSIS REPORT")
    print("=" * 80)

    # Tournament config
    config = report.tournament_config
    print(f"\nTournament: {config.get('num_games', 0)} games, "
          f"{config.get('ticks_per_game', 0)} ticks each")
    print(f"Strategies: {', '.join(config.get('strategies', []))}")

    # Strategy comparison
    print("\n" + "-" * 80)
    print("STRATEGY COMPARISON")
    print("-" * 80)
    print(
        f"{'Strategy':<12} {'Win Rate':>10} {'Avg Stab':>10} "
        f"{'Avg Actions':>12} {'Games':>8}"
    )
    print("-" * 52)

    for strategy, stats in report.strategy_comparison.items():
        print(
            f"{strategy:<12} {stats['win_rate']:>10.1%} "
            f"{stats['avg_stability']:>10.3f} "
            f"{stats['avg_actions']:>12.1f} {stats['games_completed']:>8}"
        )

    # Win rate analysis
    wra = report.win_rate_analysis
    print("\n" + "-" * 80)
    print("WIN RATE ANALYSIS")
    print("-" * 80)
    print(
        f"Best strategy: {wra.get('best_strategy', 'N/A')} "
        f"({wra.get('best_win_rate', 0):.1%})"
    )
    print(
        f"Worst strategy: {wra.get('worst_strategy', 'N/A')} "
        f"({wra.get('worst_win_rate', 0):.1%})"
    )
    print(f"Win rate delta: {wra.get('win_rate_delta', 0):.1%}")
    balanced_str = "✓ Balanced" if wra.get("is_balanced") else "⚠ Imbalanced"
    print(f"Balance status: {balanced_str}")

    # Action analysis
    aa = report.action_analysis
    print("\n" + "-" * 80)
    print("ACTION ANALYSIS")
    print("-" * 80)
    most_used = aa.get("most_used_action", "N/A")
    most_count = aa.get("most_used_count", 0)
    print(f"Most used: {most_used} ({most_count} times)")
    least_used = aa.get("least_used_action", "N/A")
    least_count = aa.get("least_used_count", 0)
    print(f"Least used: {least_used} ({least_count} times)")
    if aa.get("dominant_action"):
        print(f"⚠ Dominant action: {aa['dominant_action']}")

    # Story seed analysis
    ssa = report.story_seed_analysis
    print("\n" + "-" * 80)
    print("STORY SEED COVERAGE")
    print("-" * 80)
    print(f"Seeds activated: {len(ssa.get('seeds_seen', []))}")
    if ssa.get("authored_seeds"):
        print(f"Authored seeds: {len(ssa['authored_seeds'])}")
        print(f"Coverage rate: {ssa.get('coverage_rate', 0):.1%}")
    if ssa.get("unused_seeds"):
        print(f"Unused seeds: {', '.join(ssa['unused_seeds'])}")

    # Anomalies
    if report.anomalies:
        print("\n" + "-" * 80)
        print("DETECTED ANOMALIES")
        print("-" * 80)
        for anomaly in report.anomalies:
            severity_icon = {"low": "ℹ", "medium": "⚠", "high": "❌"}.get(
                anomaly.severity, "?"
            )
            print(f"{severity_icon} [{anomaly.severity.upper()}] {anomaly.description}")

    # Recommendations
    print("\n" + "-" * 80)
    print("RECOMMENDATIONS")
    print("-" * 80)
    for i, rec in enumerate(report.recommendations, 1):
        print(f"{i}. {rec}")

    print("\n" + "=" * 80)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for analyzing AI tournament results."""
    parser = argparse.ArgumentParser(
        description="Analyze AI tournament results for balance and coverage insights.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze tournament results
  uv run python scripts/analyze_ai_games.py --input build/tournament.json

  # Compare against authored story seeds
  uv run python scripts/analyze_ai_games.py \\
      --input build/tournament.json --world default

  # Save analysis to JSON
  uv run python scripts/analyze_ai_games.py \\
      --input build/tournament.json -o build/analysis.json
""",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to tournament results JSON file",
    )
    parser.add_argument(
        "--world",
        "-w",
        default=None,
        help="World name to load authored story seeds for coverage comparison",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Path to write JSON analysis report",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of human-readable report",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Include detailed data in output",
    )

    args = parser.parse_args(argv)

    if not args.input.exists():
        sys.stderr.write(f"Error: Input file not found: {args.input}\n")
        return 1

    results = load_tournament_results(args.input)

    # Load authored seeds if world specified
    authored_seeds = None
    if args.world:
        authored_seeds = get_authored_story_seeds(args.world)
        if args.verbose:
            sys.stderr.write(
                f"Loaded {len(authored_seeds)} authored story seeds "
                f"from '{args.world}'\n"
            )

    report = analyze_tournament(results, authored_seeds)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        if args.verbose:
            print(f"Analysis written to {args.output}")

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print_analysis_report(report)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
