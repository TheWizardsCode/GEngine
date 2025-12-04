#!/usr/bin/env python3
"""Run AI tournaments with parallel games and varied strategies.

Executes N parallel games with varied AI strategies, world configs, and seeds
to produce comparative balance reports.

Examples
--------
Basic tournament with default settings::

    uv run python scripts/run_ai_tournament.py \\
        --games 100 --output build/tournament.json

Tournament with specific strategies::

    uv run python scripts/run_ai_tournament.py \\
        --games 50 --strategies balanced aggressive --ticks 200

Verbose mode with progress output::

    uv run python scripts/run_ai_tournament.py --games 20 --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

# Set environment to avoid import issues in worker processes
os.environ.setdefault("ECHOES_CONFIG_ROOT", "content/config")


@dataclass
class GameResult:
    """Result from a single tournament game."""

    game_id: int
    strategy: str
    seed: int
    ticks_run: int
    final_stability: float
    actions_taken: int
    story_seeds_activated: list[str] = field(default_factory=list)
    action_counts: dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_id": self.game_id,
            "strategy": self.strategy,
            "seed": self.seed,
            "ticks_run": self.ticks_run,
            "final_stability": round(self.final_stability, 4),
            "actions_taken": self.actions_taken,
            "story_seeds_activated": self.story_seeds_activated,
            "action_counts": self.action_counts,
            "duration_seconds": round(self.duration_seconds, 3),
            "error": self.error,
        }


@dataclass
class TournamentConfig:
    """Configuration for running a tournament."""

    num_games: int = 100
    ticks_per_game: int = 100
    strategies: list[str] = field(
        default_factory=lambda: ["balanced", "aggressive", "diplomatic"]
    )
    base_seed: int = 42
    world: str = "default"
    max_workers: int | None = None
    stability_win_threshold: float = 0.5


@dataclass
class TournamentReport:
    """Aggregated report from a tournament."""

    config: dict[str, Any]
    total_games: int
    completed_games: int
    failed_games: int
    games_by_strategy: dict[str, list[GameResult]]
    strategy_stats: dict[str, dict[str, Any]]
    all_story_seeds: set[str]
    unused_story_seeds: list[str]
    total_duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config,
            "total_games": self.total_games,
            "completed_games": self.completed_games,
            "failed_games": self.failed_games,
            "strategy_stats": self.strategy_stats,
            "all_story_seeds_seen": sorted(self.all_story_seeds),
            "unused_story_seeds": self.unused_story_seeds,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
            "games": {
                strategy: [g.to_dict() for g in games]
                for strategy, games in self.games_by_strategy.items()
            },
        }


def run_single_game(
    game_id: int,
    strategy_name: str,
    seed: int,
    ticks: int,
    world: str,
) -> GameResult:
    """Run a single game with the given parameters.

    This function is designed to be called in a separate process.
    """
    start_time = perf_counter()
    try:
        # Import inside function for process isolation
        from gengine.ai_player import ActorConfig, AIActor
        from gengine.ai_player.strategies import StrategyType
        from gengine.echoes.sim import SimEngine

        # Map strategy name to type
        strategy_map = {
            "balanced": StrategyType.BALANCED,
            "aggressive": StrategyType.AGGRESSIVE,
            "diplomatic": StrategyType.DIPLOMATIC,
            "hybrid": StrategyType.HYBRID,
        }
        strategy_type = strategy_map.get(strategy_name.lower(), StrategyType.BALANCED)

        # Initialize engine with seed
        engine = SimEngine()
        engine.initialize_state(world=world)

        # Set seed by advancing one tick
        engine.advance_ticks(1, seed=seed)

        # Create actor with config
        config = ActorConfig(
            strategy_type=strategy_type,
            tick_budget=ticks,
            analysis_interval=10,
            log_decisions=False,
        )
        actor = AIActor(engine=engine, config=config)

        # Run the game
        report = actor.run()

        # Extract story seeds from final state
        final_state = engine.query_view("summary")
        story_seeds = []
        seed_data = final_state.get("story_seeds", [])
        if isinstance(seed_data, list):
            for seed_info in seed_data:
                if isinstance(seed_info, dict):
                    seed_id = seed_info.get("seed_id") or seed_info.get("id", "unknown")
                    story_seeds.append(seed_id)

        duration = perf_counter() - start_time

        return GameResult(
            game_id=game_id,
            strategy=strategy_name,
            seed=seed,
            ticks_run=report.ticks_run,
            final_stability=report.final_stability,
            actions_taken=report.actions_taken,
            story_seeds_activated=story_seeds,
            action_counts=report.telemetry.get("action_counts", {}),
            duration_seconds=duration,
        )

    except Exception as e:
        duration = perf_counter() - start_time
        return GameResult(
            game_id=game_id,
            strategy=strategy_name,
            seed=seed,
            ticks_run=0,
            final_stability=0.0,
            actions_taken=0,
            duration_seconds=duration,
            error=str(e),
        )


def run_tournament(
    config: TournamentConfig,
    verbose: bool = False,
) -> TournamentReport:
    """Run a complete tournament with the given configuration.

    Parameters
    ----------
    config
        Tournament configuration.
    verbose
        If True, print progress to stderr.

    Returns
    -------
    TournamentReport
        Aggregated results from all games.
    """
    start_time = perf_counter()

    # Build list of game tasks
    tasks: list[tuple[int, str, int, int, str]] = []
    game_id = 0
    games_per_strategy = config.num_games // len(config.strategies)
    remainder = config.num_games % len(config.strategies)

    for i, strategy in enumerate(config.strategies):
        num_games = games_per_strategy + (1 if i < remainder else 0)
        for _j in range(num_games):
            seed = config.base_seed + game_id
            tasks.append((game_id, strategy, seed, config.ticks_per_game, config.world))
            game_id += 1

    if verbose:
        sys.stderr.write(
            f"Starting tournament: {len(tasks)} games, "
            f"{len(config.strategies)} strategies, "
            f"{config.ticks_per_game} ticks each\n"
        )

    # Run games in parallel
    results: list[GameResult] = []
    completed = 0

    max_workers = config.max_workers or min(4, os.cpu_count() or 1)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                run_single_game, gid, strategy, seed, ticks, world
            ): gid
            for gid, strategy, seed, ticks, world in tasks
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1

            if verbose and completed % 10 == 0:
                sys.stderr.write(
                    f"Progress: {completed}/{len(tasks)} games completed\n"
                )

    # Aggregate results by strategy
    games_by_strategy: dict[str, list[GameResult]] = {}
    for strategy in config.strategies:
        games_by_strategy[strategy] = [r for r in results if r.strategy == strategy]

    # Calculate statistics per strategy
    strategy_stats: dict[str, dict[str, Any]] = {}
    all_story_seeds: set[str] = set()

    for strategy, games in games_by_strategy.items():
        successful = [g for g in games if g.error is None]
        failed = [g for g in games if g.error is not None]

        stabilities = [g.final_stability for g in successful]
        threshold = config.stability_win_threshold
        wins = [g for g in successful if g.final_stability >= threshold]
        total_actions = sum(g.actions_taken for g in successful)

        # Collect story seeds
        for g in successful:
            all_story_seeds.update(g.story_seeds_activated)

        # Action breakdown
        action_totals: dict[str, int] = {}
        for g in successful:
            for action, count in g.action_counts.items():
                action_totals[action] = action_totals.get(action, 0) + count

        strategy_stats[strategy] = {
            "games_played": len(games),
            "games_completed": len(successful),
            "games_failed": len(failed),
            "win_rate": len(wins) / len(successful) if successful else 0.0,
            "avg_stability": (
                sum(stabilities) / len(stabilities) if stabilities else 0.0
            ),
            "min_stability": min(stabilities) if stabilities else 0.0,
            "max_stability": max(stabilities) if stabilities else 0.0,
            "total_actions": total_actions,
            "avg_actions": total_actions / len(successful) if successful else 0.0,
            "action_breakdown": action_totals,
            "avg_duration_seconds": (
                sum(g.duration_seconds for g in successful) / len(successful)
                if successful
                else 0.0
            ),
        }

    # Identify unused story seeds (compare with known seeds from content)
    # For now, we'll just report what we saw
    unused_story_seeds: list[str] = []  # Would compare against authored seeds

    total_duration = perf_counter() - start_time

    if verbose:
        sys.stderr.write(
            f"\nTournament complete: {len(results)} games in {total_duration:.1f}s\n"
        )

    return TournamentReport(
        config={
            "num_games": config.num_games,
            "ticks_per_game": config.ticks_per_game,
            "strategies": config.strategies,
            "base_seed": config.base_seed,
            "world": config.world,
            "stability_win_threshold": config.stability_win_threshold,
        },
        total_games=len(tasks),
        completed_games=sum(1 for r in results if r.error is None),
        failed_games=sum(1 for r in results if r.error is not None),
        games_by_strategy=games_by_strategy,
        strategy_stats=strategy_stats,
        all_story_seeds=all_story_seeds,
        unused_story_seeds=unused_story_seeds,
        total_duration_seconds=total_duration,
    )


def print_summary_table(report: TournamentReport) -> None:
    """Print a human-readable summary of tournament results."""
    print("\n" + "=" * 80)
    print("AI TOURNAMENT RESULTS")
    print("=" * 80)
    print(
        f"\nGames: {report.completed_games}/{report.total_games} completed "
        f"({report.failed_games} failed)"
    )
    print(f"Total duration: {report.total_duration_seconds:.1f}s")
    print()

    # Strategy comparison table
    print(
        f"{'Strategy':<12} {'Win Rate':>10} {'Avg Stab':>10} {'Min Stab':>10} "
        f"{'Max Stab':>10} {'Avg Actions':>12}"
    )
    print("-" * 80)

    for strategy, stats in report.strategy_stats.items():
        print(
            f"{strategy:<12} {stats['win_rate']:>10.1%} "
            f"{stats['avg_stability']:>10.3f} "
            f"{stats['min_stability']:>10.3f} {stats['max_stability']:>10.3f} "
            f"{stats['avg_actions']:>12.1f}"
        )

    print("-" * 80)

    # Story seeds summary
    if report.all_story_seeds:
        print(f"\nStory seeds activated: {', '.join(sorted(report.all_story_seeds))}")

    # Balance observations
    print("\n" + "=" * 80)
    print("BALANCE OBSERVATIONS")
    print("=" * 80)

    # Find dominant strategy
    win_rates = [(s, stats["win_rate"]) for s, stats in report.strategy_stats.items()]
    if win_rates:
        win_rates.sort(key=lambda x: x[1], reverse=True)
        best = win_rates[0]
        worst = win_rates[-1]
        delta = best[1] - worst[1]

        print(f"\nBest strategy: {best[0]} ({best[1]:.1%} win rate)")
        print(f"Worst strategy: {worst[0]} ({worst[1]:.1%} win rate)")
        print(f"Win rate delta: {delta:.1%}")

        if delta > 0.2:
            print("\n⚠️  WARNING: Large win rate delta suggests balance issues")

    print("=" * 80)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for running AI tournaments."""
    parser = argparse.ArgumentParser(
        description="Run AI tournaments with parallel games and varied strategies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 100 games with default settings
  uv run python scripts/run_ai_tournament.py --games 100

  # Run with specific strategies
  uv run python scripts/run_ai_tournament.py --games 50 --strategies balanced aggressive

  # Save results to file
  uv run python scripts/run_ai_tournament.py --games 100 --output build/tournament.json
""",
    )
    parser.add_argument(
        "--games",
        "-g",
        type=int,
        default=100,
        help="Total number of games to run (default: 100)",
    )
    parser.add_argument(
        "--ticks",
        "-t",
        type=int,
        default=100,
        help="Ticks per game (default: 100)",
    )
    parser.add_argument(
        "--strategies",
        "-s",
        nargs="+",
        choices=["balanced", "aggressive", "diplomatic", "hybrid"],
        default=["balanced", "aggressive", "diplomatic"],
        help="Strategies to test (default: balanced aggressive diplomatic)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed (default: 42)",
    )
    parser.add_argument(
        "--world",
        "-w",
        default="default",
        help="World bundle to use (default: default)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Max parallel workers (default: auto)",
    )
    parser.add_argument(
        "--win-threshold",
        type=float,
        default=0.5,
        help="Stability threshold for a 'win' (default: 0.5)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Path to write JSON results",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of table",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print progress during tournament",
    )

    args = parser.parse_args(argv)

    config = TournamentConfig(
        num_games=args.games,
        ticks_per_game=args.ticks,
        strategies=args.strategies,
        base_seed=args.seed,
        world=args.world,
        max_workers=args.workers,
        stability_win_threshold=args.win_threshold,
    )

    report = run_tournament(config, verbose=args.verbose)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        if args.verbose:
            print(f"\nResults written to {args.output}")

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print_summary_table(report)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
