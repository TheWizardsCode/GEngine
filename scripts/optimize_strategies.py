#!/usr/bin/env python3
"""Strategy parameter optimization for game balance tuning.

Implements automated strategy parameter tuning using optimization algorithms
to find well-balanced strategy configurations. Supports grid search, random
search, and optionally Bayesian optimization.

Examples
--------
Run grid search optimization with default parameters::

    uv run python scripts/optimize_strategies.py optimize --algorithm grid

Run random search with custom parameter ranges::

    uv run python scripts/optimize_strategies.py optimize --algorithm random \\
        --stability-low-range 0.5 0.8 --stability-critical-range 0.3 0.5

View Pareto frontier of optimal configurations::

    uv run python scripts/optimize_strategies.py pareto \\
        --database build/sweep_results.db

Generate optimization report::

    uv run python scripts/optimize_strategies.py report \\
        --output build/optimization_report.md
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import random
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Sequence

import yaml

# Set environment to avoid import issues
os.environ.setdefault("ECHOES_CONFIG_ROOT", "content/config")

# Default configuration path
DEFAULT_CONFIG_PATH = Path("content/config/optimization.yml")
DEFAULT_DB_PATH = Path("build/sweep_results.db")

# Try to import optional Bayesian optimization
try:
    from skopt import gp_minimize
    from skopt.space import Real

    HAS_SKOPT = True
except ImportError:
    HAS_SKOPT = False


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ParameterRange:
    """Range specification for a tunable parameter.

    Attributes
    ----------
    name
        Parameter name (must match StrategyConfig field).
    min_value
        Minimum value in the range.
    max_value
        Maximum value in the range.
    step
        Step size for grid search (None for continuous).
    param_type
        Type of parameter ("float" or "int").
    """

    name: str
    min_value: float
    max_value: float
    step: float | None = None
    param_type: str = "float"

    def __post_init__(self) -> None:
        """Validate parameter range."""
        if self.min_value > self.max_value:
            raise ValueError(
                f"min_value ({self.min_value}) must be <= max_value ({self.max_value})"
            )
        if self.step is not None and self.step <= 0:
            raise ValueError(f"step must be positive, got {self.step}")

    def generate_grid_values(self) -> list[float]:
        """Generate discrete values for grid search.

        Returns
        -------
        list[float]
            List of parameter values to test.
        """
        if self.step is None:
            # Default to 5 evenly spaced points
            n_points = 5
            step = (self.max_value - self.min_value) / (n_points - 1)
        else:
            step = self.step

        values: list[float] = []
        current = self.min_value
        while current <= self.max_value + 1e-9:  # Small epsilon for float comparison
            if self.param_type == "int":
                values.append(int(round(current)))
            else:
                values.append(round(current, 4))
            current += step
        return values

    def sample_random(self, rng: random.Random | None = None) -> float:
        """Sample a random value from the range.

        Parameters
        ----------
        rng
            Random number generator (optional).

        Returns
        -------
        float
            Random value within the range.
        """
        if rng is None:
            rng = random.Random()

        value = rng.uniform(self.min_value, self.max_value)
        if self.param_type == "int":
            return int(round(value))
        return round(value, 4)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "step": self.step,
            "param_type": self.param_type,
        }


@dataclass
class OptimizationTarget:
    """Target objective for optimization.

    Attributes
    ----------
    name
        Target name (e.g., "win_rate_delta", "diversity").
    weight
        Weight for multi-objective optimization (higher = more important).
    direction
        Optimization direction ("minimize" or "maximize").
    threshold
        Optional threshold for acceptable values.
    """

    name: str
    weight: float = 1.0
    direction: str = "minimize"
    threshold: float | None = None

    def __post_init__(self) -> None:
        """Validate target."""
        if self.direction not in ("minimize", "maximize"):
            raise ValueError("direction must be 'minimize' or 'maximize'")
        if self.weight <= 0:
            raise ValueError(f"weight must be positive, got {self.weight}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "weight": self.weight,
            "direction": self.direction,
            "threshold": self.threshold,
        }


@dataclass
class OptimizationConfig:
    """Configuration for optimization run.

    Attributes
    ----------
    parameter_ranges
        List of parameter ranges to explore.
    targets
        List of optimization targets.
    algorithm
        Optimization algorithm ("grid", "random", "bayesian").
    max_iterations
        Maximum number of configurations to evaluate.
    n_samples
        Number of samples for random/bayesian search.
    sweeps_per_config
        Number of sweep simulations per configuration.
    tick_budget
        Ticks per sweep simulation.
    seeds
        Random seeds for simulations.
    strategies
        Strategies to include in optimization.
    output_dir
        Directory for output files.
    bayesian_n_initial
        Initial random samples for Bayesian optimization.
    """

    parameter_ranges: list[ParameterRange] = field(default_factory=list)
    targets: list[OptimizationTarget] = field(default_factory=list)
    algorithm: str = "random"
    max_iterations: int = 100
    n_samples: int = 50
    sweeps_per_config: int = 5
    tick_budget: int = 100
    seeds: list[int] = field(default_factory=lambda: [42, 123, 456])
    strategies: list[str] = field(
        default_factory=lambda: ["balanced", "aggressive", "diplomatic"]
    )
    output_dir: Path = field(default_factory=lambda: Path("build/optimization"))
    bayesian_n_initial: int = 10

    @classmethod
    def from_yaml(cls, path: Path) -> OptimizationConfig:
        """Load configuration from YAML file.

        Parameters
        ----------
        path
            Path to YAML configuration file.

        Returns
        -------
        OptimizationConfig
            Loaded configuration.
        """
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        params = data.get("parameters", {})
        targets_data = data.get("targets", [])
        settings = data.get("settings", {})

        # Parse parameter ranges
        parameter_ranges: list[ParameterRange] = []
        for name, spec in params.items():
            if isinstance(spec, dict):
                parameter_ranges.append(
                    ParameterRange(
                        name=name,
                        min_value=spec.get("min", 0.0),
                        max_value=spec.get("max", 1.0),
                        step=spec.get("step"),
                        param_type=spec.get("type", "float"),
                    )
                )
            elif isinstance(spec, list) and len(spec) >= 2:
                parameter_ranges.append(
                    ParameterRange(name=name, min_value=spec[0], max_value=spec[1])
                )

        # Parse targets
        targets: list[OptimizationTarget] = []
        for target_spec in targets_data:
            if isinstance(target_spec, dict):
                targets.append(
                    OptimizationTarget(
                        name=target_spec.get("name", "win_rate_delta"),
                        weight=target_spec.get("weight", 1.0),
                        direction=target_spec.get("direction", "minimize"),
                        threshold=target_spec.get("threshold"),
                    )
                )
            elif isinstance(target_spec, str):
                targets.append(OptimizationTarget(name=target_spec))

        return cls(
            parameter_ranges=parameter_ranges,
            targets=targets or [OptimizationTarget(name="win_rate_delta")],
            algorithm=settings.get("algorithm", "random"),
            max_iterations=settings.get("max_iterations", 100),
            n_samples=settings.get("n_samples", 50),
            sweeps_per_config=settings.get("sweeps_per_config", 5),
            tick_budget=settings.get("tick_budget", 100),
            seeds=settings.get("seeds", [42, 123, 456]),
            strategies=settings.get(
                "strategies", ["balanced", "aggressive", "diplomatic"]
            ),
            output_dir=Path(settings.get("output_dir", "build/optimization")),
            bayesian_n_initial=settings.get("bayesian_n_initial", 10),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parameter_ranges": [p.to_dict() for p in self.parameter_ranges],
            "targets": [t.to_dict() for t in self.targets],
            "algorithm": self.algorithm,
            "max_iterations": self.max_iterations,
            "n_samples": self.n_samples,
            "sweeps_per_config": self.sweeps_per_config,
            "tick_budget": self.tick_budget,
            "seeds": self.seeds,
            "strategies": self.strategies,
            "output_dir": str(self.output_dir),
            "bayesian_n_initial": self.bayesian_n_initial,
        }


@dataclass
class FitnessResult:
    """Result of fitness evaluation for a configuration.

    Attributes
    ----------
    parameters
        Configuration parameter values.
    fitness_scores
        Individual fitness scores per target.
    combined_fitness
        Weighted combined fitness score.
    win_rates
        Win rates by strategy.
    win_rate_delta
        Maximum win rate delta between strategies.
    diversity_score
        Strategic diversity score.
    avg_stability
        Average stability across sweeps.
    sweep_count
        Number of sweeps evaluated.
    duration_seconds
        Evaluation duration.
    """

    parameters: dict[str, float]
    fitness_scores: dict[str, float] = field(default_factory=dict)
    combined_fitness: float = 0.0
    win_rates: dict[str, float] = field(default_factory=dict)
    win_rate_delta: float = 0.0
    diversity_score: float = 0.0
    avg_stability: float = 0.0
    sweep_count: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parameters": {k: round(v, 4) for k, v in self.parameters.items()},
            "fitness_scores": {k: round(v, 4) for k, v in self.fitness_scores.items()},
            "combined_fitness": round(self.combined_fitness, 4),
            "win_rates": {k: round(v, 4) for k, v in self.win_rates.items()},
            "win_rate_delta": round(self.win_rate_delta, 4),
            "diversity_score": round(self.diversity_score, 4),
            "avg_stability": round(self.avg_stability, 4),
            "sweep_count": self.sweep_count,
            "duration_seconds": round(self.duration_seconds, 2),
        }


@dataclass
class ParetoPoint:
    """Point on the Pareto frontier.

    Attributes
    ----------
    parameters
        Configuration parameter values.
    objectives
        Objective values (name -> value).
    rank
        Pareto rank (1 = non-dominated).
    """

    parameters: dict[str, float]
    objectives: dict[str, float]
    rank: int = 1

    def dominates(self, other: ParetoPoint, directions: dict[str, str]) -> bool:
        """Check if this point dominates another.

        Parameters
        ----------
        other
            Other Pareto point to compare.
        directions
            Optimization directions per objective.

        Returns
        -------
        bool
            True if this point dominates the other.
        """
        dominated_any = False
        for obj_name, value in self.objectives.items():
            other_value = other.objectives.get(obj_name, float("inf"))
            direction = directions.get(obj_name, "minimize")

            if direction == "minimize":
                if value > other_value:
                    return False
                if value < other_value:
                    dominated_any = True
            else:  # maximize
                if value < other_value:
                    return False
                if value > other_value:
                    dominated_any = True

        return dominated_any

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parameters": {k: round(v, 4) for k, v in self.parameters.items()},
            "objectives": {k: round(v, 4) for k, v in self.objectives.items()},
            "rank": self.rank,
        }


@dataclass
class OptimizationResult:
    """Result of an optimization run.

    Attributes
    ----------
    config
        Optimization configuration used.
    best_parameters
        Best parameter configuration found.
    best_fitness
        Best fitness score achieved.
    all_results
        All fitness results evaluated.
    pareto_frontier
        Pareto optimal configurations.
    total_evaluations
        Total number of evaluations performed.
    total_duration_seconds
        Total optimization duration.
    metadata
        Additional metadata.
    """

    config: dict[str, Any]
    best_parameters: dict[str, float]
    best_fitness: float
    all_results: list[FitnessResult]
    pareto_frontier: list[ParetoPoint]
    total_evaluations: int = 0
    total_duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": self.config,
            "best_parameters": {
                k: round(v, 4) for k, v in self.best_parameters.items()
            },
            "best_fitness": round(self.best_fitness, 4),
            "all_results": [r.to_dict() for r in self.all_results],
            "pareto_frontier": [p.to_dict() for p in self.pareto_frontier],
            "total_evaluations": self.total_evaluations,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
            "metadata": self.metadata,
        }


# ============================================================================
# Fitness Functions
# ============================================================================


def compute_win_rate_delta(win_rates: dict[str, float]) -> float:
    """Compute maximum win rate delta between strategies.

    Parameters
    ----------
    win_rates
        Win rates per strategy.

    Returns
    -------
    float
        Maximum delta between any two strategies' win rates.
    """
    if len(win_rates) < 2:
        return 0.0

    values = list(win_rates.values())
    return max(values) - min(values)


def compute_diversity_score(win_rates: dict[str, float]) -> float:
    """Compute strategic diversity score.

    A higher score indicates more diverse strategy outcomes.
    Perfect diversity (all strategies equally viable) = 1.0.

    Parameters
    ----------
    win_rates
        Win rates per strategy.

    Returns
    -------
    float
        Diversity score between 0 and 1.
    """
    if len(win_rates) < 2:
        return 1.0

    values = list(win_rates.values())
    n = len(values)

    # Compute entropy-based diversity
    total = sum(values) or 1.0
    normalized = [v / total for v in values]

    # Shannon entropy normalized to [0, 1]
    entropy = 0.0
    for p in normalized:
        if p > 0:
            entropy -= p * math.log(p)

    max_entropy = math.log(n)
    return entropy / max_entropy if max_entropy > 0 else 1.0


def compute_fitness(
    sweep_results: list[dict[str, Any]],
    targets: list[OptimizationTarget],
    strategies: list[str],
) -> FitnessResult:
    """Compute fitness scores from sweep results.

    Parameters
    ----------
    sweep_results
        List of sweep result dictionaries.
    targets
        Optimization targets.
    strategies
        Strategies being evaluated.

    Returns
    -------
    FitnessResult
        Computed fitness result.
    """
    if not sweep_results:
        return FitnessResult(
            parameters={},
            combined_fitness=float("inf"),
        )

    # Compute win rates per strategy
    strategy_wins: dict[str, int] = {s: 0 for s in strategies}
    strategy_counts: dict[str, int] = {s: 0 for s in strategies}
    total_stability = 0.0
    stability_threshold = 0.5

    for result in sweep_results:
        strategy = result.get("strategy", "unknown")
        stability = result.get("final_stability", 0.0)

        if strategy in strategy_counts:
            strategy_counts[strategy] += 1
            if stability >= stability_threshold:
                strategy_wins[strategy] += 1
            total_stability += stability

    # Calculate win rates
    win_rates: dict[str, float] = {}
    for s in strategies:
        count = strategy_counts.get(s, 0)
        wins = strategy_wins.get(s, 0)
        win_rates[s] = wins / count if count > 0 else 0.0

    # Compute metrics
    win_rate_delta = compute_win_rate_delta(win_rates)
    diversity_score = compute_diversity_score(win_rates)
    avg_stability = total_stability / len(sweep_results) if sweep_results else 0.0

    # Compute individual fitness scores
    fitness_scores: dict[str, float] = {}
    for target in targets:
        if target.name == "win_rate_delta":
            fitness_scores[target.name] = win_rate_delta
        elif target.name == "diversity":
            # For diversity, higher is better, so negate for minimization
            fitness_scores[target.name] = 1.0 - diversity_score
        elif target.name == "stability":
            # For stability, higher is better, so negate for minimization
            fitness_scores[target.name] = 1.0 - avg_stability
        else:
            fitness_scores[target.name] = 0.0

    # Compute combined weighted fitness
    combined_fitness = 0.0
    total_weight = sum(t.weight for t in targets)

    for target in targets:
        score = fitness_scores.get(target.name, 0.0)
        if target.direction == "maximize":
            score = -score  # Invert for maximization targets
        combined_fitness += (target.weight / total_weight) * score

    return FitnessResult(
        parameters={},  # Will be set by caller
        fitness_scores=fitness_scores,
        combined_fitness=combined_fitness,
        win_rates=win_rates,
        win_rate_delta=win_rate_delta,
        diversity_score=diversity_score,
        avg_stability=avg_stability,
        sweep_count=len(sweep_results),
    )


# ============================================================================
# Parameter Generation
# ============================================================================


def generate_grid_configurations(
    parameter_ranges: list[ParameterRange],
) -> list[dict[str, float]]:
    """Generate all parameter combinations for grid search.

    Parameters
    ----------
    parameter_ranges
        List of parameter ranges.

    Returns
    -------
    list[dict[str, float]]
        List of parameter configurations.
    """
    if not parameter_ranges:
        return [{}]

    # Generate grid values for each parameter
    param_grids: dict[str, list[float]] = {}
    for param in parameter_ranges:
        param_grids[param.name] = param.generate_grid_values()

    # Generate Cartesian product
    keys = list(param_grids.keys())
    value_lists = [param_grids[k] for k in keys]

    configurations: list[dict[str, float]] = []
    for values in itertools.product(*value_lists):
        config = dict(zip(keys, values))
        configurations.append(config)

    return configurations


def generate_random_configurations(
    parameter_ranges: list[ParameterRange],
    n_samples: int,
    seed: int | None = None,
) -> list[dict[str, float]]:
    """Generate random parameter configurations.

    Parameters
    ----------
    parameter_ranges
        List of parameter ranges.
    n_samples
        Number of samples to generate.
    seed
        Random seed for reproducibility.

    Returns
    -------
    list[dict[str, float]]
        List of parameter configurations.
    """
    if not parameter_ranges:
        return [{}]

    rng = random.Random(seed)
    configurations: list[dict[str, float]] = []

    for _ in range(n_samples):
        config: dict[str, float] = {}
        for param in parameter_ranges:
            config[param.name] = param.sample_random(rng)
        configurations.append(config)

    return configurations


def generate_latin_hypercube_configurations(
    parameter_ranges: list[ParameterRange],
    n_samples: int,
    seed: int | None = None,
) -> list[dict[str, float]]:
    """Generate configurations using Latin Hypercube Sampling.

    Parameters
    ----------
    parameter_ranges
        List of parameter ranges.
    n_samples
        Number of samples to generate.
    seed
        Random seed for reproducibility.

    Returns
    -------
    list[dict[str, float]]
        List of parameter configurations.
    """
    if not parameter_ranges:
        return [{}]

    rng = random.Random(seed)
    n_params = len(parameter_ranges)

    # Generate stratified samples for each dimension
    samples: list[list[float]] = []
    for i in range(n_params):
        # Divide range into n_samples strata
        strata = list(range(n_samples))
        rng.shuffle(strata)

        param = parameter_ranges[i]
        param_samples: list[float] = []

        for j in strata:
            # Sample uniformly within stratum
            low = param.min_value + (param.max_value - param.min_value) * j / n_samples
            high = (
                param.min_value
                + (param.max_value - param.min_value) * (j + 1) / n_samples
            )
            value = rng.uniform(low, high)

            if param.param_type == "int":
                value = int(round(value))
            else:
                value = round(value, 4)

            param_samples.append(value)

        samples.append(param_samples)

    # Combine into configurations
    configurations: list[dict[str, float]] = []
    for j in range(n_samples):
        config = {parameter_ranges[i].name: samples[i][j] for i in range(n_params)}
        configurations.append(config)

    return configurations


# ============================================================================
# Pareto Frontier
# ============================================================================


def compute_pareto_frontier(
    results: list[FitnessResult],
    targets: list[OptimizationTarget],
) -> list[ParetoPoint]:
    """Compute Pareto frontier from fitness results.

    Parameters
    ----------
    results
        List of fitness results.
    targets
        Optimization targets.

    Returns
    -------
    list[ParetoPoint]
        Pareto optimal points.
    """
    if not results:
        return []

    # Create Pareto points
    directions = {t.name: t.direction for t in targets}
    points: list[ParetoPoint] = []

    for result in results:
        objectives: dict[str, float] = {}
        for target in targets:
            objectives[target.name] = result.fitness_scores.get(target.name, 0.0)

        points.append(
            ParetoPoint(
                parameters=result.parameters.copy(),
                objectives=objectives,
            )
        )

    # Compute Pareto ranks using non-dominated sorting
    frontier: list[ParetoPoint] = []

    for point in points:
        is_dominated = False
        for other in points:
            if point is other:
                continue
            if other.dominates(point, directions):
                is_dominated = True
                break

        if not is_dominated:
            point.rank = 1
            frontier.append(point)

    return frontier


# ============================================================================
# Sweep Evaluation
# ============================================================================


def evaluate_configuration(
    parameters: dict[str, float],
    config: OptimizationConfig,
    verbose: bool = False,
) -> FitnessResult:
    """Evaluate a parameter configuration by running sweeps.

    Parameters
    ----------
    parameters
        Parameter values to evaluate.
    config
        Optimization configuration.
    verbose
        Print progress information.

    Returns
    -------
    FitnessResult
        Fitness result for the configuration.
    """
    start_time = perf_counter()

    try:
        # Import here to avoid issues in worker processes
        from gengine.ai_player import ActorConfig, AIActor
        from gengine.ai_player.strategies import (
            StrategyConfig,
            StrategyType,
            create_strategy,
        )
        from gengine.echoes.sim import SimEngine

        # Map strategy names to types
        strategy_map = {
            "balanced": StrategyType.BALANCED,
            "aggressive": StrategyType.AGGRESSIVE,
            "diplomatic": StrategyType.DIPLOMATIC,
            "hybrid": StrategyType.HYBRID,
        }

        # Build StrategyConfig from parameters
        strategy_config_kwargs: dict[str, Any] = {}
        for key, value in parameters.items():
            strategy_config_kwargs[key] = value

        sweep_results: list[dict[str, Any]] = []

        for strategy_name in config.strategies:
            strategy_type = strategy_map.get(
                strategy_name.lower(), StrategyType.BALANCED
            )

            for seed in config.seeds:
                try:
                    # Create strategy with custom config
                    strategy_config = StrategyConfig(**strategy_config_kwargs)
                    strategy = create_strategy(
                        strategy_type=strategy_type,
                        session_id=f"opt-{strategy_name}-{seed}",
                        config=strategy_config,
                    )

                    # Initialize engine
                    engine = SimEngine()
                    engine.initialize_state(world="default")
                    engine.advance_ticks(1, seed=seed)

                    # Create actor
                    analysis_interval = min(10, config.tick_budget)
                    actor_config = ActorConfig(
                        strategy_type=strategy_type,
                        tick_budget=config.tick_budget,
                        analysis_interval=analysis_interval,
                        log_decisions=False,
                    )
                    actor = AIActor(
                        engine=engine, config=actor_config, strategy=strategy
                    )

                    # Run simulation
                    report = actor.run()

                    sweep_results.append(
                        {
                            "strategy": strategy_name,
                            "seed": seed,
                            "final_stability": report.final_stability,
                            "actions_taken": report.actions_taken,
                            "ticks_run": report.ticks_run,
                        }
                    )

                except Exception as e:
                    if verbose:
                        sys.stderr.write(f"Sweep error: {e}\n")
                    continue

        # Compute fitness
        fitness = compute_fitness(sweep_results, config.targets, config.strategies)
        fitness.parameters = parameters.copy()
        fitness.duration_seconds = perf_counter() - start_time

        return fitness

    except Exception as e:
        if verbose:
            sys.stderr.write(f"Evaluation error: {e}\n")
        return FitnessResult(
            parameters=parameters.copy(),
            combined_fitness=float("inf"),
            duration_seconds=perf_counter() - start_time,
        )


def evaluate_configuration_mock(
    parameters: dict[str, float],
    config: OptimizationConfig,
    rng: random.Random | None = None,
) -> FitnessResult:
    """Mock evaluation for testing without running simulations.

    Parameters
    ----------
    parameters
        Parameter values to evaluate.
    config
        Optimization configuration.
    rng
        Random number generator.

    Returns
    -------
    FitnessResult
        Mock fitness result.
    """
    if rng is None:
        rng = random.Random()

    # Generate plausible mock results
    win_rates = {s: rng.uniform(0.3, 0.8) for s in config.strategies}

    # Apply some parameter influence
    stability_low = parameters.get("stability_low", 0.6)
    # Lower thresholds tend to produce more balanced results
    balance_factor = 1.0 - abs(stability_low - 0.65) * 2

    for s in win_rates:
        win_rates[s] *= (0.8 + balance_factor * 0.2)
        win_rates[s] = min(1.0, max(0.0, win_rates[s]))

    win_rate_delta = compute_win_rate_delta(win_rates)
    diversity_score = compute_diversity_score(win_rates)

    fitness_scores = {
        "win_rate_delta": win_rate_delta,
        "diversity": 1.0 - diversity_score,
        "stability": rng.uniform(0.3, 0.7),
    }

    combined = sum(fitness_scores.values()) / len(fitness_scores)

    return FitnessResult(
        parameters=parameters.copy(),
        fitness_scores=fitness_scores,
        combined_fitness=combined,
        win_rates=win_rates,
        win_rate_delta=win_rate_delta,
        diversity_score=diversity_score,
        avg_stability=rng.uniform(0.5, 0.8),
        sweep_count=len(config.strategies) * len(config.seeds),
    )


# ============================================================================
# Optimization Algorithms
# ============================================================================


def run_grid_search(
    config: OptimizationConfig,
    evaluate_fn: Callable[
        [dict[str, float], OptimizationConfig], FitnessResult
    ] | None = None,
    verbose: bool = False,
) -> OptimizationResult:
    """Run grid search optimization.

    Parameters
    ----------
    config
        Optimization configuration.
    evaluate_fn
        Custom evaluation function (for testing).
    verbose
        Print progress information.

    Returns
    -------
    OptimizationResult
        Optimization result.
    """
    start_time = perf_counter()

    def default_evaluate(
        p: dict[str, float], c: OptimizationConfig
    ) -> FitnessResult:
        return evaluate_configuration(p, c, verbose)

    if evaluate_fn is None:
        evaluate_fn = default_evaluate

    # Generate grid configurations
    configurations = generate_grid_configurations(config.parameter_ranges)

    # Limit to max_iterations
    if len(configurations) > config.max_iterations:
        configurations = configurations[: config.max_iterations]

    if verbose:
        sys.stderr.write(f"Grid search: {len(configurations)} configurations\n")

    # Evaluate all configurations
    all_results: list[FitnessResult] = []
    best_result: FitnessResult | None = None

    for i, params in enumerate(configurations):
        result = evaluate_fn(params, config)
        all_results.append(result)

        is_better = (
            best_result is None
            or result.combined_fitness < best_result.combined_fitness
        )
        if is_better:
            best_result = result

        if verbose and (i + 1) % 10 == 0:
            sys.stderr.write(
                f"Progress: {i + 1}/{len(configurations)} "
                f"(best fitness: {best_result.combined_fitness:.4f})\n"
            )

    # Compute Pareto frontier
    pareto = compute_pareto_frontier(all_results, config.targets)

    return OptimizationResult(
        config=config.to_dict(),
        best_parameters=best_result.parameters if best_result else {},
        best_fitness=best_result.combined_fitness if best_result else float("inf"),
        all_results=all_results,
        pareto_frontier=pareto,
        total_evaluations=len(all_results),
        total_duration_seconds=perf_counter() - start_time,
        metadata={
            "algorithm": "grid_search",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def run_random_search(
    config: OptimizationConfig,
    evaluate_fn: Callable[
        [dict[str, float], OptimizationConfig], FitnessResult
    ] | None = None,
    seed: int | None = None,
    verbose: bool = False,
) -> OptimizationResult:
    """Run random search optimization.

    Parameters
    ----------
    config
        Optimization configuration.
    evaluate_fn
        Custom evaluation function (for testing).
    seed
        Random seed for reproducibility.
    verbose
        Print progress information.

    Returns
    -------
    OptimizationResult
        Optimization result.
    """
    start_time = perf_counter()

    def default_evaluate(
        p: dict[str, float], c: OptimizationConfig
    ) -> FitnessResult:
        return evaluate_configuration(p, c, verbose)

    if evaluate_fn is None:
        evaluate_fn = default_evaluate

    # Generate random configurations
    configurations = generate_random_configurations(
        config.parameter_ranges, config.n_samples, seed
    )

    if verbose:
        sys.stderr.write(f"Random search: {len(configurations)} samples\n")

    # Evaluate all configurations
    all_results: list[FitnessResult] = []
    best_result: FitnessResult | None = None

    for i, params in enumerate(configurations):
        result = evaluate_fn(params, config)
        all_results.append(result)

        is_better = (
            best_result is None
            or result.combined_fitness < best_result.combined_fitness
        )
        if is_better:
            best_result = result

        if verbose and (i + 1) % 10 == 0:
            sys.stderr.write(
                f"Progress: {i + 1}/{len(configurations)} "
                f"(best fitness: {best_result.combined_fitness:.4f})\n"
            )

    # Compute Pareto frontier
    pareto = compute_pareto_frontier(all_results, config.targets)

    return OptimizationResult(
        config=config.to_dict(),
        best_parameters=best_result.parameters if best_result else {},
        best_fitness=best_result.combined_fitness if best_result else float("inf"),
        all_results=all_results,
        pareto_frontier=pareto,
        total_evaluations=len(all_results),
        total_duration_seconds=perf_counter() - start_time,
        metadata={
            "algorithm": "random_search",
            "seed": seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def run_bayesian_optimization(
    config: OptimizationConfig,
    evaluate_fn: Callable[
        [dict[str, float], OptimizationConfig], FitnessResult
    ] | None = None,
    seed: int | None = None,
    verbose: bool = False,
) -> OptimizationResult:
    """Run Bayesian optimization using scikit-optimize.

    Parameters
    ----------
    config
        Optimization configuration.
    evaluate_fn
        Custom evaluation function (for testing).
    seed
        Random seed for reproducibility.
    verbose
        Print progress information.

    Returns
    -------
    OptimizationResult
        Optimization result.

    Raises
    ------
    ImportError
        If scikit-optimize is not installed.
    """
    if not HAS_SKOPT:
        raise ImportError(
            "Bayesian optimization requires scikit-optimize. "
            "Install with: pip install scikit-optimize"
        )

    start_time = perf_counter()

    def default_evaluate(
        p: dict[str, float], c: OptimizationConfig
    ) -> FitnessResult:
        return evaluate_configuration(p, c, verbose)

    if evaluate_fn is None:
        evaluate_fn = default_evaluate

    # Build search space
    dimensions = []
    param_names = []
    for param in config.parameter_ranges:
        dimensions.append(Real(param.min_value, param.max_value, name=param.name))
        param_names.append(param.name)

    # Track all results
    all_results: list[FitnessResult] = []

    def objective(x: list[float]) -> float:
        params = dict(zip(param_names, x))
        result = evaluate_fn(params, config)
        all_results.append(result)

        if verbose and len(all_results) % 5 == 0:
            sys.stderr.write(
                f"Bayesian iteration {len(all_results)}: "
                f"fitness={result.combined_fitness:.4f}\n"
            )

        return result.combined_fitness

    if verbose:
        sys.stderr.write(
            f"Bayesian optimization: {config.n_samples} iterations "
            f"({config.bayesian_n_initial} initial)\n"
        )

    # Run optimization
    opt_result = gp_minimize(
        objective,
        dimensions,
        n_calls=config.n_samples,
        n_initial_points=config.bayesian_n_initial,
        random_state=seed,
        verbose=verbose,
    )

    # Extract best result
    best_params = dict(zip(param_names, opt_result.x))
    best_fitness = opt_result.fun

    # Compute Pareto frontier
    pareto = compute_pareto_frontier(all_results, config.targets)

    return OptimizationResult(
        config=config.to_dict(),
        best_parameters=best_params,
        best_fitness=best_fitness,
        all_results=all_results,
        pareto_frontier=pareto,
        total_evaluations=len(all_results),
        total_duration_seconds=perf_counter() - start_time,
        metadata={
            "algorithm": "bayesian",
            "seed": seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def run_optimization(
    config: OptimizationConfig,
    evaluate_fn: Callable[
        [dict[str, float], OptimizationConfig], FitnessResult
    ] | None = None,
    seed: int | None = None,
    verbose: bool = False,
) -> OptimizationResult:
    """Run optimization with the specified algorithm.

    Parameters
    ----------
    config
        Optimization configuration.
    evaluate_fn
        Custom evaluation function (for testing).
    seed
        Random seed for reproducibility.
    verbose
        Print progress information.

    Returns
    -------
    OptimizationResult
        Optimization result.
    """
    if config.algorithm == "grid":
        return run_grid_search(config, evaluate_fn, verbose)
    elif config.algorithm == "random":
        return run_random_search(config, evaluate_fn, seed, verbose)
    elif config.algorithm == "bayesian":
        return run_bayesian_optimization(config, evaluate_fn, seed, verbose)
    else:
        raise ValueError(f"Unknown algorithm: {config.algorithm}")


# ============================================================================
# Result Storage Integration
# ============================================================================


def store_optimization_result(
    result: OptimizationResult,
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Store optimization result in the sweep database.

    Parameters
    ----------
    result
        Optimization result to store.
    db_path
        Path to the database.

    Returns
    -------
    int
        ID of the stored optimization run.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))

    try:
        # Create optimization table if not exists
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS optimization_runs (
                opt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                config TEXT NOT NULL,
                best_parameters TEXT NOT NULL,
                best_fitness REAL NOT NULL,
                total_evaluations INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                pareto_frontier TEXT,
                metadata TEXT
            )
            """
        )

        # Insert result
        cursor = conn.execute(
            """
            INSERT INTO optimization_runs (
                timestamp, algorithm, config, best_parameters, best_fitness,
                total_evaluations, duration_seconds, pareto_frontier, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.metadata.get(
                    "timestamp", datetime.now(timezone.utc).isoformat()
                ),
                result.metadata.get("algorithm", "unknown"),
                json.dumps(result.config),
                json.dumps(result.best_parameters),
                result.best_fitness,
                result.total_evaluations,
                result.total_duration_seconds,
                json.dumps([p.to_dict() for p in result.pareto_frontier]),
                json.dumps(result.metadata),
            ),
        )

        conn.commit()
        return cursor.lastrowid or 0

    finally:
        conn.close()


def query_optimization_runs(
    db_path: Path = DEFAULT_DB_PATH,
    algorithm: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Query optimization runs from the database.

    Parameters
    ----------
    db_path
        Path to the database.
    algorithm
        Filter by algorithm.
    limit
        Maximum number of runs to return.

    Returns
    -------
    list[dict[str, Any]]
        List of optimization run records.
    """
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        query = "SELECT * FROM optimization_runs WHERE 1=1"
        params: list[Any] = []

        if algorithm:
            query += " AND algorithm = ?"
            params.append(algorithm)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "opt_id": row["opt_id"],
                    "timestamp": row["timestamp"],
                    "algorithm": row["algorithm"],
                    "config": json.loads(row["config"] or "{}"),
                    "best_parameters": json.loads(row["best_parameters"] or "{}"),
                    "best_fitness": row["best_fitness"],
                    "total_evaluations": row["total_evaluations"],
                    "duration_seconds": row["duration_seconds"],
                    "pareto_frontier": json.loads(row["pareto_frontier"] or "[]"),
                    "metadata": json.loads(row["metadata"] or "{}"),
                }
            )

        return results

    except sqlite3.OperationalError:
        # Table doesn't exist
        return []
    finally:
        conn.close()


# ============================================================================
# Report Generation
# ============================================================================


def format_optimization_report_markdown(result: OptimizationResult) -> str:
    """Generate Markdown report from optimization result.

    Parameters
    ----------
    result
        Optimization result.

    Returns
    -------
    str
        Markdown formatted report.
    """
    lines = [
        "# Strategy Parameter Optimization Report",
        "",
        f"**Algorithm:** {result.metadata.get('algorithm', 'unknown')}",
        f"**Generated:** {result.metadata.get('timestamp', 'unknown')}",
        f"**Total Evaluations:** {result.total_evaluations}",
        f"**Duration:** {result.total_duration_seconds:.1f}s",
        "",
        "---",
        "",
        "## Best Configuration",
        "",
        f"**Combined Fitness:** {result.best_fitness:.4f}",
        "",
        "### Parameters",
        "",
    ]

    for name, value in result.best_parameters.items():
        lines.append(f"- **{name}:** {value:.4f}")

    lines.extend(["", "---", "", "## Pareto Frontier", ""])

    if result.pareto_frontier:
        lines.append(
            "Configurations representing optimal trade-offs between objectives:"
        )
        lines.append("")

        for i, point in enumerate(result.pareto_frontier[:10]):  # Top 10
            lines.append(f"### Configuration {i + 1}")
            lines.append("")
            lines.append("**Objectives:**")
            for obj_name, obj_value in point.objectives.items():
                lines.append(f"- {obj_name}: {obj_value:.4f}")
            lines.append("")
            lines.append("**Parameters:**")
            for param_name, param_value in point.parameters.items():
                lines.append(f"- {param_name}: {param_value:.4f}")
            lines.append("")
    else:
        lines.append("No Pareto frontier computed.")

    lines.extend(["", "---", "", "## Summary Statistics", ""])

    # Compute summary from all results
    if result.all_results:
        fitness_values = [r.combined_fitness for r in result.all_results]
        lines.append(
            f"- **Min Fitness:** {min(fitness_values):.4f}"
        )
        lines.append(
            f"- **Max Fitness:** {max(fitness_values):.4f}"
        )
        lines.append(
            f"- **Mean Fitness:** {sum(fitness_values) / len(fitness_values):.4f}"
        )

        # Win rate delta statistics
        deltas = [r.win_rate_delta for r in result.all_results if r.win_rate_delta > 0]
        if deltas:
            lines.append("")
            lines.append("**Win Rate Delta Distribution:**")
            lines.append(f"- Min: {min(deltas):.4f}")
            lines.append(f"- Max: {max(deltas):.4f}")
            lines.append(f"- Mean: {sum(deltas) / len(deltas):.4f}")

    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================


def cmd_optimize(args: argparse.Namespace) -> int:
    """Handle the optimize command."""
    # Load configuration
    config = OptimizationConfig.from_yaml(args.config)

    # Apply CLI overrides
    if args.algorithm:
        config.algorithm = args.algorithm
    if args.samples:
        config.n_samples = args.samples
    if args.ticks:
        config.tick_budget = args.ticks
    if args.output_dir:
        config.output_dir = args.output_dir

    # Add default parameter ranges if none specified
    if not config.parameter_ranges:
        config.parameter_ranges = [
            ParameterRange("stability_low", 0.5, 0.8, step=0.1),
            ParameterRange("stability_critical", 0.3, 0.5, step=0.1),
            ParameterRange("faction_low_legitimacy", 0.3, 0.6, step=0.1),
        ]

    # Add default targets if none specified
    if not config.targets:
        config.targets = [
            OptimizationTarget("win_rate_delta", weight=1.0, direction="minimize"),
            OptimizationTarget("diversity", weight=0.5, direction="maximize"),
        ]

    if args.verbose:
        sys.stderr.write(f"Starting optimization with {config.algorithm} algorithm\n")
        sys.stderr.write(f"Parameters: {[p.name for p in config.parameter_ranges]}\n")
        sys.stderr.write(f"Targets: {[t.name for t in config.targets]}\n")

    # Run optimization
    result = run_optimization(config, seed=args.seed, verbose=args.verbose)

    # Store result
    if not args.no_store:
        db_path = args.database or DEFAULT_DB_PATH
        opt_id = store_optimization_result(result, db_path)
        if args.verbose:
            sys.stderr.write(f"Stored optimization run with ID {opt_id}\n")

    # Write output
    config.output_dir.mkdir(parents=True, exist_ok=True)

    if args.json:
        output = json.dumps(result.to_dict(), indent=2)
        print(output)
    else:
        # Write detailed JSON
        json_path = config.output_dir / "optimization_result.json"
        json_path.write_text(json.dumps(result.to_dict(), indent=2))

        # Write Markdown report
        md_path = config.output_dir / "optimization_report.md"
        md_path.write_text(format_optimization_report_markdown(result))

        # Print summary
        print("\n" + "=" * 60)
        print("OPTIMIZATION COMPLETE")
        print("=" * 60)
        print(f"\nAlgorithm: {config.algorithm}")
        print(f"Evaluations: {result.total_evaluations}")
        print(f"Duration: {result.total_duration_seconds:.1f}s")
        print(f"\nBest Fitness: {result.best_fitness:.4f}")
        print("\nBest Parameters:")
        for name, value in result.best_parameters.items():
            print(f"  {name}: {value:.4f}")
        print(f"\nPareto Frontier: {len(result.pareto_frontier)} points")
        print(f"\nResults written to: {config.output_dir}")

    return 0


def cmd_pareto(args: argparse.Namespace) -> int:
    """Handle the pareto command."""
    runs = query_optimization_runs(
        db_path=args.database,
        algorithm=args.algorithm,
        limit=args.limit,
    )

    if not runs:
        print("No optimization runs found.")
        return 0

    if args.json:
        output = {"runs": runs}
        print(json.dumps(output, indent=2))
        return 0

    print("\n" + "=" * 80)
    print("OPTIMIZATION RUNS - PARETO FRONTIERS")
    print("=" * 80)

    for run in runs:
        print(f"\n--- Run {run['opt_id']} ({run['algorithm']}) ---")
        print(f"Timestamp: {run['timestamp']}")
        print(f"Best Fitness: {run['best_fitness']:.4f}")
        print(f"Evaluations: {run['total_evaluations']}")
        print("\nPareto Frontier:")

        for i, point in enumerate(run["pareto_frontier"][:5]):  # Top 5
            objs = ", ".join(f"{k}={v:.3f}" for k, v in point["objectives"].items())
            print(f"  {i + 1}. {objs}")

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Handle the report command."""
    runs = query_optimization_runs(
        db_path=args.database,
        limit=1,
    )

    if not runs:
        print("No optimization runs found.")
        return 0

    run = runs[0]

    # Reconstruct result for report
    result = OptimizationResult(
        config=run["config"],
        best_parameters=run["best_parameters"],
        best_fitness=run["best_fitness"],
        all_results=[],  # Not stored in DB
        pareto_frontier=[
            ParetoPoint(
                parameters=p["parameters"],
                objectives=p["objectives"],
                rank=p.get("rank", 1),
            )
            for p in run["pareto_frontier"]
        ],
        total_evaluations=run["total_evaluations"],
        total_duration_seconds=run["duration_seconds"],
        metadata=run["metadata"],
    )

    report = format_optimization_report_markdown(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for strategy parameter optimization."""
    parser = argparse.ArgumentParser(
        description="Optimize strategy parameters for game balance.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run grid search optimization
  python scripts/optimize_strategies.py optimize --algorithm grid

  # Run random search with more samples
  python scripts/optimize_strategies.py optimize --algorithm random --samples 100

  # View Pareto frontier from past runs
  python scripts/optimize_strategies.py pareto --database build/sweep_results.db

  # Generate optimization report
  python scripts/optimize_strategies.py report --output build/opt_report.md
""",
    )

    parser.add_argument(
        "--database",
        "-d",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Database path (default: {DEFAULT_DB_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Optimize command
    opt_parser = subparsers.add_parser(
        "optimize", help="Run strategy parameter optimization"
    )
    opt_parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Configuration file path (default: {DEFAULT_CONFIG_PATH})",
    )
    opt_parser.add_argument(
        "--algorithm",
        "-a",
        choices=["grid", "random", "bayesian"],
        help="Optimization algorithm",
    )
    opt_parser.add_argument(
        "--samples",
        "-n",
        type=int,
        help="Number of samples for random/bayesian search",
    )
    opt_parser.add_argument(
        "--ticks",
        "-t",
        type=int,
        help="Tick budget per sweep",
    )
    opt_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility",
    )
    opt_parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        help="Output directory for results",
    )
    opt_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of files",
    )
    opt_parser.add_argument(
        "--no-store",
        action="store_true",
        help="Don't store result in database",
    )
    opt_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print progress information",
    )

    # Pareto command
    pareto_parser = subparsers.add_parser(
        "pareto", help="View Pareto frontier from optimization runs"
    )
    pareto_parser.add_argument(
        "--algorithm",
        "-a",
        type=str,
        help="Filter by algorithm",
    )
    pareto_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=10,
        help="Maximum runs to show",
    )
    pareto_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate optimization report"
    )
    report_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path",
    )

    args = parser.parse_args(argv)

    handlers = {
        "optimize": cmd_optimize,
        "pareto": cmd_pareto,
        "report": cmd_report,
    }

    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
