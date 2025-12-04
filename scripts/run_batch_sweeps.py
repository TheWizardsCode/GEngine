#!/usr/bin/env python3
"""Run batch simulation sweeps with configurable parameter grids.

Executes multi-dimensional parameter sweeps across strategies, difficulties,
seeds, worlds, and tick budgets using parallel execution for balance analysis.

Examples
--------
Basic sweep with default configuration::

    uv run python scripts/run_batch_sweeps.py --output-dir build/sweeps

Sweep with specific parameters::

    uv run python scripts/run_batch_sweeps.py \\
        --strategies balanced aggressive --seeds 42 123 --ticks 100 200

Use custom configuration file::

    uv run python scripts/run_batch_sweeps.py --config content/config/batch_sweeps.yml
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

import yaml

# Set environment to avoid import issues in worker processes
os.environ.setdefault("ECHOES_CONFIG_ROOT", "content/config")

# Default configuration path
DEFAULT_CONFIG_PATH = Path("content/config/batch_sweeps.yml")

# Available strategies
AVAILABLE_STRATEGIES = ["balanced", "aggressive", "diplomatic", "hybrid"]

# Available difficulty presets
AVAILABLE_DIFFICULTIES = ["tutorial", "easy", "normal", "hard", "brutal"]


@dataclass
class SweepParameters:
    """Parameters for a single sweep run."""

    strategy: str
    difficulty: str
    seed: int
    world: str
    tick_budget: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "difficulty": self.difficulty,
            "seed": self.seed,
            "world": self.world,
            "tick_budget": self.tick_budget,
        }


@dataclass
class SweepResult:
    """Result from a single sweep run."""

    sweep_id: int
    parameters: SweepParameters
    final_stability: float
    actions_taken: int
    ticks_run: int
    story_seeds_activated: list[str] = field(default_factory=list)
    action_counts: dict[str, int] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sweep_id": self.sweep_id,
            "parameters": self.parameters.to_dict(),
            "results": {
                "final_stability": round(self.final_stability, 4),
                "actions_taken": self.actions_taken,
                "ticks_run": self.ticks_run,
                "story_seeds_activated": self.story_seeds_activated,
                "action_counts": self.action_counts,
            },
            "telemetry": self.telemetry,
            "duration_seconds": round(self.duration_seconds, 3),
            "error": self.error,
        }


@dataclass
class BatchSweepConfig:
    """Configuration for batch sweep execution."""

    strategies: list[str] = field(default_factory=lambda: ["balanced"])
    difficulties: list[str] = field(default_factory=lambda: ["normal"])
    seeds: list[int] = field(default_factory=lambda: [42])
    worlds: list[str] = field(default_factory=lambda: ["default"])
    tick_budgets: list[int] = field(default_factory=lambda: [100])
    max_workers: int | None = None
    timeout_per_sweep: int = 300
    output_dir: Path = field(default_factory=lambda: Path("build/batch_sweeps"))
    include_telemetry: bool = True
    include_summary: bool = True
    sampling_mode: str = "full"
    sample_count: int = 100
    sample_seed: int = 42

    @classmethod
    def from_yaml(cls, path: Path) -> BatchSweepConfig:
        """Load configuration from YAML file."""
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        params = data.get("parameters", {})
        parallel = data.get("parallel", {})
        output = data.get("output", {})
        sampling = data.get("sampling", {})

        return cls(
            strategies=params.get("strategies", ["balanced"]),
            difficulties=params.get("difficulties", ["normal"]),
            seeds=params.get("seeds", [42]),
            worlds=params.get("worlds", ["default"]),
            tick_budgets=params.get("tick_budgets", [100]),
            max_workers=parallel.get("max_workers"),
            timeout_per_sweep=parallel.get("timeout_per_sweep", 300),
            output_dir=Path(output.get("dir", "build/batch_sweeps")),
            include_telemetry=output.get("include_telemetry", True),
            include_summary=output.get("include_summary", True),
            sampling_mode=sampling.get("mode", "full"),
            sample_count=sampling.get("sample_count", 100),
            sample_seed=sampling.get("sample_seed", 42),
        )


@dataclass
class BatchSweepReport:
    """Aggregated report from batch sweep execution."""

    config: dict[str, Any]
    total_sweeps: int
    completed_sweeps: int
    failed_sweeps: int
    results: list[SweepResult]
    strategy_stats: dict[str, dict[str, Any]]
    difficulty_stats: dict[str, dict[str, Any]]
    total_duration_seconds: float
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config,
            "total_sweeps": self.total_sweeps,
            "completed_sweeps": self.completed_sweeps,
            "failed_sweeps": self.failed_sweeps,
            "strategy_stats": self.strategy_stats,
            "difficulty_stats": self.difficulty_stats,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
            "metadata": self.metadata,
            "sweeps": [r.to_dict() for r in self.results],
        }


def generate_parameter_grid(config: BatchSweepConfig) -> list[SweepParameters]:
    """Generate parameter combinations from configuration.

    Creates Cartesian product of all parameter lists, optionally applying
    sampling for large parameter spaces.

    Parameters
    ----------
    config
        Batch sweep configuration with parameter lists.

    Returns
    -------
    list[SweepParameters]
        List of parameter combinations to test.
    """
    # Generate full Cartesian product
    combinations = list(
        itertools.product(
            config.strategies,
            config.difficulties,
            config.seeds,
            config.worlds,
            config.tick_budgets,
        )
    )

    # Apply sampling if not in full mode
    if config.sampling_mode != "full" and len(combinations) > config.sample_count:
        import random

        rng = random.Random(config.sample_seed)

        if config.sampling_mode == "random":
            combinations = rng.sample(combinations, config.sample_count)
        elif config.sampling_mode == "latin_hypercube":
            # Simple approximation: stratified sampling
            combinations = rng.sample(combinations, config.sample_count)

    return [
        SweepParameters(
            strategy=strategy,
            difficulty=difficulty,
            seed=seed,
            world=world,
            tick_budget=tick_budget,
        )
        for strategy, difficulty, seed, world, tick_budget in combinations
    ]


def run_single_sweep(
    sweep_id: int,
    params: SweepParameters,
    include_telemetry: bool = True,
) -> SweepResult:
    """Run a single sweep with the given parameters.

    This function is designed to be called in a separate process.

    Parameters
    ----------
    sweep_id
        Unique identifier for this sweep.
    params
        Parameters for the sweep.
    include_telemetry
        Whether to include full telemetry in results.

    Returns
    -------
    SweepResult
        Results from the sweep execution.
    """
    start_time = perf_counter()
    try:
        # Import inside function for process isolation
        from gengine.ai_player import ActorConfig, AIActor
        from gengine.ai_player.strategies import StrategyType
        from gengine.echoes.settings import load_simulation_config
        from gengine.echoes.sim import SimEngine

        # Map strategy name to type
        strategy_map = {
            "balanced": StrategyType.BALANCED,
            "aggressive": StrategyType.AGGRESSIVE,
            "diplomatic": StrategyType.DIPLOMATIC,
            "hybrid": StrategyType.HYBRID,
        }
        strategy_type = strategy_map.get(params.strategy.lower(), StrategyType.BALANCED)

        # Load config for difficulty preset
        config_root = Path("content/config/sweeps") / f"difficulty-{params.difficulty}"
        if config_root.exists():
            config = load_simulation_config(config_root=config_root)
        else:
            config = load_simulation_config()

        # Initialize engine
        engine = SimEngine(config=config)
        engine.initialize_state(world=params.world)

        # Set seed by advancing one tick
        engine.advance_ticks(1, seed=params.seed)

        # Create actor with config
        # Ensure analysis_interval doesn't exceed tick_budget
        analysis_interval = min(10, params.tick_budget)
        actor_config = ActorConfig(
            strategy_type=strategy_type,
            tick_budget=params.tick_budget,
            analysis_interval=analysis_interval,
            log_decisions=False,
        )
        actor = AIActor(engine=engine, config=actor_config)

        # Run the simulation
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

        # Build telemetry if requested
        telemetry: dict[str, Any] = {}
        if include_telemetry:
            telemetry = {
                "environment": final_state.get("environment", {}),
                "faction_legitimacy": final_state.get("faction_legitimacy", {}),
                "economy": final_state.get("economy", {}),
                "profiling": engine.state.metadata.get("profiling", {}),
            }

        duration = perf_counter() - start_time

        return SweepResult(
            sweep_id=sweep_id,
            parameters=params,
            final_stability=report.final_stability,
            actions_taken=report.actions_taken,
            ticks_run=report.ticks_run,
            story_seeds_activated=story_seeds,
            action_counts=report.telemetry.get("action_counts", {}),
            telemetry=telemetry,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = perf_counter() - start_time
        return SweepResult(
            sweep_id=sweep_id,
            parameters=params,
            final_stability=0.0,
            actions_taken=0,
            ticks_run=0,
            duration_seconds=duration,
            error=str(e),
        )


def _get_git_commit() -> str | None:
    """Get current git commit hash if available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def _build_metadata(config: BatchSweepConfig) -> dict[str, Any]:
    """Build metadata dictionary for sweep report."""
    metadata: dict[str, Any] = {}

    # Git commit
    git_commit = _get_git_commit()
    if git_commit:
        metadata["git_commit"] = git_commit

    # Timestamp
    metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Runtime info
    metadata["runtime"] = {
        "python_version": sys.version,
        "max_workers": config.max_workers,
    }

    return metadata


def _calculate_stats(
    results: list[SweepResult], key_func: Any
) -> dict[str, dict[str, Any]]:
    """Calculate statistics grouped by a key function."""
    grouped: dict[str, list[SweepResult]] = {}
    for r in results:
        key = key_func(r)
        grouped.setdefault(key, []).append(r)

    stats: dict[str, dict[str, Any]] = {}
    for key, group in grouped.items():
        successful = [g for g in group if g.error is None]
        stabilities = [g.final_stability for g in successful]
        actions = [g.actions_taken for g in successful]

        stats[key] = {
            "count": len(group),
            "completed": len(successful),
            "failed": len(group) - len(successful),
            "avg_stability": (
                sum(stabilities) / len(stabilities) if stabilities else 0.0
            ),
            "min_stability": min(stabilities) if stabilities else 0.0,
            "max_stability": max(stabilities) if stabilities else 0.0,
            "avg_actions": sum(actions) / len(actions) if actions else 0.0,
            "total_actions": sum(actions),
        }

    return stats


def run_batch_sweeps(
    config: BatchSweepConfig,
    verbose: bool = False,
) -> BatchSweepReport:
    """Run batch sweeps with the given configuration.

    Parameters
    ----------
    config
        Batch sweep configuration.
    verbose
        If True, print progress to stderr.

    Returns
    -------
    BatchSweepReport
        Aggregated results from all sweeps.
    """
    start_time = perf_counter()

    # Generate parameter grid
    parameter_grid = generate_parameter_grid(config)

    if verbose:
        sys.stderr.write(
            f"Starting batch sweep: {len(parameter_grid)} combinations\n"
            f"  Strategies: {config.strategies}\n"
            f"  Difficulties: {config.difficulties}\n"
            f"  Seeds: {config.seeds}\n"
            f"  Worlds: {config.worlds}\n"
            f"  Tick budgets: {config.tick_budgets}\n"
        )

    # Run sweeps in parallel
    results: list[SweepResult] = []
    completed = 0

    max_workers = config.max_workers or min(4, os.cpu_count() or 1)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                run_single_sweep, i, params, config.include_telemetry
            ): i
            for i, params in enumerate(parameter_grid)
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1

            if verbose and completed % 10 == 0:
                sys.stderr.write(
                    f"Progress: {completed}/{len(parameter_grid)} sweeps completed\n"
                )

    # Sort results by sweep_id for consistent ordering
    results.sort(key=lambda r: r.sweep_id)

    # Calculate statistics
    strategy_stats = _calculate_stats(results, lambda r: r.parameters.strategy)
    difficulty_stats = _calculate_stats(results, lambda r: r.parameters.difficulty)

    total_duration = perf_counter() - start_time

    if verbose:
        sys.stderr.write(
            f"\nBatch sweep complete: {len(results)} sweeps in {total_duration:.1f}s\n"
        )

    return BatchSweepReport(
        config={
            "strategies": config.strategies,
            "difficulties": config.difficulties,
            "seeds": config.seeds,
            "worlds": config.worlds,
            "tick_budgets": config.tick_budgets,
            "sampling_mode": config.sampling_mode,
        },
        total_sweeps=len(parameter_grid),
        completed_sweeps=sum(1 for r in results if r.error is None),
        failed_sweeps=sum(1 for r in results if r.error is not None),
        results=results,
        strategy_stats=strategy_stats,
        difficulty_stats=difficulty_stats,
        total_duration_seconds=total_duration,
        metadata=_build_metadata(config),
    )


def write_sweep_outputs(
    report: BatchSweepReport,
    output_dir: Path,
    verbose: bool = False,
) -> None:
    """Write individual sweep results and summary to output directory.

    Parameters
    ----------
    report
        Batch sweep report.
    output_dir
        Directory to write output files.
    verbose
        If True, print progress to stderr.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write individual sweep results
    for result in report.results:
        params = result.parameters
        filename = (
            f"sweep_{result.sweep_id:04d}_"
            f"{params.strategy}_{params.difficulty}_"
            f"seed{params.seed}_tick{params.tick_budget}.json"
        )
        output_path = output_dir / filename
        output_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True))

    # Write summary report
    summary_path = output_dir / "batch_sweep_summary.json"
    summary_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True))

    if verbose:
        sys.stderr.write(f"Results written to {output_dir}\n")
        sys.stderr.write(f"  Individual sweeps: {len(report.results)} files\n")
        sys.stderr.write(f"  Summary: {summary_path}\n")


def print_summary_table(report: BatchSweepReport) -> None:
    """Print a human-readable summary of batch sweep results."""
    print("\n" + "=" * 80)
    print("BATCH SWEEP RESULTS")
    print("=" * 80)
    print(
        f"\nSweeps: {report.completed_sweeps}/{report.total_sweeps} completed "
        f"({report.failed_sweeps} failed)"
    )
    print(f"Total duration: {report.total_duration_seconds:.1f}s")

    # Strategy breakdown
    print("\n" + "-" * 80)
    print("BY STRATEGY")
    print("-" * 80)
    print(
        f"{'Strategy':<12} {'Count':>8} {'Completed':>10} {'Avg Stab':>10} "
        f"{'Min Stab':>10} {'Max Stab':>10}"
    )
    print("-" * 80)

    for strategy, stats in report.strategy_stats.items():
        print(
            f"{strategy:<12} {stats['count']:>8} {stats['completed']:>10} "
            f"{stats['avg_stability']:>10.3f} {stats['min_stability']:>10.3f} "
            f"{stats['max_stability']:>10.3f}"
        )

    # Difficulty breakdown
    print("\n" + "-" * 80)
    print("BY DIFFICULTY")
    print("-" * 80)
    print(
        f"{'Difficulty':<12} {'Count':>8} {'Completed':>10} {'Avg Stab':>10} "
        f"{'Min Stab':>10} {'Max Stab':>10}"
    )
    print("-" * 80)

    for difficulty, stats in report.difficulty_stats.items():
        print(
            f"{difficulty:<12} {stats['count']:>8} {stats['completed']:>10} "
            f"{stats['avg_stability']:>10.3f} {stats['min_stability']:>10.3f} "
            f"{stats['max_stability']:>10.3f}"
        )

    print("=" * 80)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for running batch sweeps."""
    parser = argparse.ArgumentParser(
        description="Run batch simulation sweeps with configurable parameter grids.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  uv run python scripts/run_batch_sweeps.py

  # Run with specific strategies and seeds
  uv run python scripts/run_batch_sweeps.py --strategies balanced aggressive --seeds 42 123

  # Use custom configuration file
  uv run python scripts/run_batch_sweeps.py --config content/config/batch_sweeps.yml

  # Save results to specific directory
  uv run python scripts/run_batch_sweeps.py --output-dir build/my_sweeps
""",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Configuration file path (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--strategies",
        "-s",
        nargs="+",
        choices=AVAILABLE_STRATEGIES,
        default=None,
        help="Override strategies to test",
    )
    parser.add_argument(
        "--difficulties",
        "-d",
        nargs="+",
        choices=AVAILABLE_DIFFICULTIES,
        default=None,
        help="Override difficulty presets to test",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=None,
        help="Override random seeds to test",
    )
    parser.add_argument(
        "--worlds",
        "-w",
        nargs="+",
        default=None,
        help="Override world bundles to test",
    )
    parser.add_argument(
        "--ticks",
        "-t",
        nargs="+",
        type=int,
        default=None,
        help="Override tick budgets to test",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Max parallel workers (default: auto)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Output directory for sweep results",
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
        help="Print progress during execution",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing individual sweep files",
    )

    args = parser.parse_args(argv)

    # Load configuration from file
    config = BatchSweepConfig.from_yaml(args.config)

    # Apply CLI overrides
    if args.strategies:
        config.strategies = args.strategies
    if args.difficulties:
        config.difficulties = args.difficulties
    if args.seeds:
        config.seeds = args.seeds
    if args.worlds:
        config.worlds = args.worlds
    if args.ticks:
        config.tick_budgets = args.ticks
    if args.workers:
        config.max_workers = args.workers
    if args.output_dir:
        config.output_dir = args.output_dir

    # Run batch sweeps
    report = run_batch_sweeps(config, verbose=args.verbose)

    # Write outputs
    if not args.no_write:
        write_sweep_outputs(report, config.output_dir, verbose=args.verbose)

    # Print results
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print_summary_table(report)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
