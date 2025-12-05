"""Tests for strategy parameter optimization infrastructure."""

from __future__ import annotations

import json
import random
import sys
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "optimize_strategies.py"
)


def _load_optimization_module():
    spec = util.spec_from_file_location("optimize_strategies", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("optimize_strategies", module)
    spec.loader.exec_module(module)
    return module


_driver = _load_optimization_module()

ParameterRange = _driver.ParameterRange
OptimizationTarget = _driver.OptimizationTarget
OptimizationConfig = _driver.OptimizationConfig
FitnessResult = _driver.FitnessResult
ParetoPoint = _driver.ParetoPoint
OptimizationResult = _driver.OptimizationResult
generate_grid_configurations = _driver.generate_grid_configurations
generate_random_configurations = _driver.generate_random_configurations
generate_latin_hypercube_configurations = (
    _driver.generate_latin_hypercube_configurations
)
compute_win_rate_delta = _driver.compute_win_rate_delta
compute_diversity_score = _driver.compute_diversity_score
compute_fitness = _driver.compute_fitness
compute_pareto_frontier = _driver.compute_pareto_frontier
run_grid_search = _driver.run_grid_search
run_random_search = _driver.run_random_search
run_optimization = _driver.run_optimization
evaluate_configuration_mock = _driver.evaluate_configuration_mock
store_optimization_result = _driver.store_optimization_result
query_optimization_runs = _driver.query_optimization_runs
format_optimization_report_markdown = _driver.format_optimization_report_markdown
main = _driver.main


class TestParameterRange:
    """Tests for the ParameterRange dataclass."""

    def test_parameter_range_creation(self) -> None:
        """Test basic parameter range creation."""
        param = ParameterRange(
            name="stability_low",
            min_value=0.5,
            max_value=0.8,
            step=0.1,
        )
        assert param.name == "stability_low"
        assert param.min_value == 0.5
        assert param.max_value == 0.8
        assert param.step == 0.1
        assert param.param_type == "float"

    def test_parameter_range_validation(self) -> None:
        """Test parameter range validation."""
        with pytest.raises(ValueError, match="min_value.*must be <= max_value"):
            ParameterRange(name="test", min_value=0.8, max_value=0.5)

        with pytest.raises(ValueError, match="step must be positive"):
            ParameterRange(name="test", min_value=0.0, max_value=1.0, step=-0.1)

    def test_generate_grid_values(self) -> None:
        """Test grid value generation."""
        param = ParameterRange(
            name="test",
            min_value=0.0,
            max_value=1.0,
            step=0.25,
        )
        values = param.generate_grid_values()
        assert values == [0.0, 0.25, 0.5, 0.75, 1.0]

    def test_generate_grid_values_default_step(self) -> None:
        """Test grid value generation with default step."""
        param = ParameterRange(name="test", min_value=0.0, max_value=1.0)
        values = param.generate_grid_values()
        assert len(values) == 5  # Default 5 points
        assert values[0] == 0.0
        assert values[-1] == 1.0

    def test_sample_random(self) -> None:
        """Test random sampling from range."""
        param = ParameterRange(name="test", min_value=0.0, max_value=1.0)
        rng = random.Random(42)

        for _ in range(100):
            value = param.sample_random(rng)
            assert 0.0 <= value <= 1.0

    def test_sample_random_int(self) -> None:
        """Test random sampling for integer parameters."""
        param = ParameterRange(
            name="test",
            min_value=1,
            max_value=10,
            param_type="int",
        )
        rng = random.Random(42)

        for _ in range(100):
            value = param.sample_random(rng)
            assert isinstance(value, int)
            assert 1 <= value <= 10

    def test_to_dict(self) -> None:
        """Test parameter range serialization."""
        param = ParameterRange(
            name="test",
            min_value=0.5,
            max_value=0.8,
            step=0.1,
        )
        data = param.to_dict()
        assert data["name"] == "test"
        assert data["min_value"] == 0.5
        assert data["max_value"] == 0.8
        assert data["step"] == 0.1


class TestOptimizationTarget:
    """Tests for the OptimizationTarget dataclass."""

    def test_target_creation(self) -> None:
        """Test basic target creation."""
        target = OptimizationTarget(
            name="win_rate_delta",
            weight=1.0,
            direction="minimize",
        )
        assert target.name == "win_rate_delta"
        assert target.weight == 1.0
        assert target.direction == "minimize"

    def test_target_validation(self) -> None:
        """Test target validation."""
        with pytest.raises(ValueError, match="direction must be"):
            OptimizationTarget(name="test", direction="invalid")

        with pytest.raises(ValueError, match="weight must be positive"):
            OptimizationTarget(name="test", weight=0)

    def test_to_dict(self) -> None:
        """Test target serialization."""
        target = OptimizationTarget(
            name="diversity",
            weight=0.5,
            direction="maximize",
            threshold=0.8,
        )
        data = target.to_dict()
        assert data["name"] == "diversity"
        assert data["weight"] == 0.5
        assert data["direction"] == "maximize"
        assert data["threshold"] == 0.8


class TestOptimizationConfig:
    """Tests for the OptimizationConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = OptimizationConfig()
        assert config.algorithm == "random"
        assert config.max_iterations == 100
        assert config.n_samples == 50
        assert len(config.seeds) == 3

    def test_config_from_yaml(self, tmp_path: Path) -> None:
        """Test loading configuration from YAML."""
        yaml_content = """
parameters:
  stability_low:
    min: 0.5
    max: 0.8
    step: 0.1
  stability_critical:
    min: 0.3
    max: 0.5

targets:
  - name: win_rate_delta
    weight: 1.0
    direction: minimize
  - name: diversity
    weight: 0.5
    direction: maximize

settings:
  algorithm: grid
  max_iterations: 50
  n_samples: 25
  tick_budget: 50
"""
        config_file = tmp_path / "optimization.yml"
        config_file.write_text(yaml_content)

        config = OptimizationConfig.from_yaml(config_file)

        assert len(config.parameter_ranges) == 2
        assert config.parameter_ranges[0].name == "stability_low"
        assert len(config.targets) == 2
        assert config.algorithm == "grid"
        assert config.max_iterations == 50

    def test_config_from_missing_yaml(self, tmp_path: Path) -> None:
        """Test that missing YAML returns default config."""
        config = OptimizationConfig.from_yaml(tmp_path / "nonexistent.yml")
        assert config.algorithm == "random"

    def test_to_dict(self) -> None:
        """Test configuration serialization."""
        config = OptimizationConfig(
            parameter_ranges=[
                ParameterRange("test", 0.0, 1.0),
            ],
            targets=[
                OptimizationTarget("win_rate_delta"),
            ],
            algorithm="grid",
        )
        data = config.to_dict()
        assert len(data["parameter_ranges"]) == 1
        assert len(data["targets"]) == 1
        assert data["algorithm"] == "grid"


class TestParameterGeneration:
    """Tests for parameter configuration generation."""

    def test_generate_grid_configurations(self) -> None:
        """Test grid configuration generation."""
        params = [
            ParameterRange("a", 0.0, 1.0, step=0.5),
            ParameterRange("b", 0.0, 1.0, step=0.5),
        ]
        configs = generate_grid_configurations(params)

        # 3 values for a × 3 values for b = 9 configurations
        assert len(configs) == 9

        # Check all combinations exist
        expected_values = [0.0, 0.5, 1.0]
        for c in configs:
            assert c["a"] in expected_values
            assert c["b"] in expected_values

    def test_generate_grid_empty_params(self) -> None:
        """Test grid generation with empty parameters."""
        configs = generate_grid_configurations([])
        assert configs == [{}]

    def test_generate_random_configurations(self) -> None:
        """Test random configuration generation."""
        params = [
            ParameterRange("a", 0.0, 1.0),
            ParameterRange("b", 0.0, 1.0),
        ]
        configs = generate_random_configurations(params, n_samples=100, seed=42)

        assert len(configs) == 100

        for c in configs:
            assert 0.0 <= c["a"] <= 1.0
            assert 0.0 <= c["b"] <= 1.0

    def test_generate_random_deterministic(self) -> None:
        """Test that random generation is deterministic with seed."""
        params = [ParameterRange("a", 0.0, 1.0)]
        configs1 = generate_random_configurations(params, n_samples=10, seed=42)
        configs2 = generate_random_configurations(params, n_samples=10, seed=42)

        assert configs1 == configs2

    def test_generate_latin_hypercube(self) -> None:
        """Test Latin Hypercube Sampling."""
        params = [
            ParameterRange("a", 0.0, 1.0),
            ParameterRange("b", 0.0, 1.0),
        ]
        configs = generate_latin_hypercube_configurations(
            params, n_samples=10, seed=42
        )

        assert len(configs) == 10

        # Check that values are within range
        for c in configs:
            assert 0.0 <= c["a"] <= 1.0
            assert 0.0 <= c["b"] <= 1.0


class TestFitnessFunctions:
    """Tests for fitness computation functions."""

    def test_compute_win_rate_delta(self) -> None:
        """Test win rate delta computation."""
        win_rates = {"balanced": 0.7, "aggressive": 0.5, "diplomatic": 0.6}
        delta = compute_win_rate_delta(win_rates)
        assert delta == pytest.approx(0.2)  # 0.7 - 0.5

    def test_compute_win_rate_delta_single(self) -> None:
        """Test win rate delta with single strategy."""
        delta = compute_win_rate_delta({"balanced": 0.5})
        assert delta == 0.0

    def test_compute_diversity_score(self) -> None:
        """Test diversity score computation."""
        # Equal win rates should give high diversity
        equal_rates = {"a": 0.5, "b": 0.5, "c": 0.5}
        diversity = compute_diversity_score(equal_rates)
        assert diversity == pytest.approx(1.0, abs=0.01)

        # One dominant strategy should give low diversity
        dominant_rates = {"a": 0.9, "b": 0.05, "c": 0.05}
        diversity = compute_diversity_score(dominant_rates)
        assert diversity < 0.7

    def test_compute_fitness(self) -> None:
        """Test fitness computation from sweep results."""
        sweep_results = [
            {"strategy": "balanced", "final_stability": 0.6},
            {"strategy": "balanced", "final_stability": 0.7},
            {"strategy": "aggressive", "final_stability": 0.5},
            {"strategy": "aggressive", "final_stability": 0.4},
            {"strategy": "diplomatic", "final_stability": 0.6},
            {"strategy": "diplomatic", "final_stability": 0.6},
        ]
        targets = [
            OptimizationTarget("win_rate_delta", weight=1.0, direction="minimize"),
        ]
        strategies = ["balanced", "aggressive", "diplomatic"]

        fitness = compute_fitness(sweep_results, targets, strategies)

        # balanced: 2/2 wins (0.6>=0.5, 0.7>=0.5) = 1.0
        # aggressive: 1/2 wins (0.5>=0.5, 0.4<0.5) = 0.5
        # diplomatic: 2/2 wins = 1.0
        # delta = 1.0 - 0.5 = 0.5
        assert fitness.win_rates["balanced"] == 1.0
        assert fitness.win_rates["aggressive"] == 0.5
        assert fitness.win_rate_delta == pytest.approx(0.5)

    def test_compute_fitness_empty_results(self) -> None:
        """Test fitness computation with empty results."""
        fitness = compute_fitness([], [OptimizationTarget("win_rate_delta")], [])
        assert fitness.combined_fitness == float("inf")


class TestParetoFrontier:
    """Tests for Pareto frontier computation."""

    def test_compute_pareto_frontier(self) -> None:
        """Test Pareto frontier computation."""
        results = [
            FitnessResult(
                parameters={"a": 0.5},
                fitness_scores={"delta": 0.1, "stability": 0.8},
            ),
            FitnessResult(
                parameters={"a": 0.6},
                fitness_scores={"delta": 0.05, "stability": 0.6},
            ),
            FitnessResult(
                parameters={"a": 0.7},
                fitness_scores={"delta": 0.2, "stability": 0.9},
            ),
        ]
        targets = [
            OptimizationTarget("delta", direction="minimize"),
            OptimizationTarget("stability", direction="minimize"),
        ]

        frontier = compute_pareto_frontier(results, targets)

        # At least one point should be on the frontier
        assert len(frontier) >= 1

        # All frontier points should have rank 1
        for point in frontier:
            assert point.rank == 1

    def test_pareto_point_dominates(self) -> None:
        """Test Pareto dominance check."""
        point_a = ParetoPoint(
            parameters={},
            objectives={"delta": 0.1, "stability": 0.5},
        )
        point_b = ParetoPoint(
            parameters={},
            objectives={"delta": 0.2, "stability": 0.6},
        )
        directions = {"delta": "minimize", "stability": "minimize"}

        # A should dominate B (both objectives better)
        assert point_a.dominates(point_b, directions)
        assert not point_b.dominates(point_a, directions)

    def test_pareto_point_to_dict(self) -> None:
        """Test Pareto point serialization."""
        point = ParetoPoint(
            parameters={"a": 0.5, "b": 0.6},
            objectives={"delta": 0.1, "diversity": 0.8},
            rank=1,
        )
        data = point.to_dict()
        assert data["parameters"]["a"] == 0.5
        assert data["objectives"]["delta"] == 0.1
        assert data["rank"] == 1


class TestOptimizationAlgorithms:
    """Tests for optimization algorithms."""

    def _make_mock_evaluate(self, rng_seed: int = 42):
        """Create a mock evaluation function."""
        rng = random.Random(rng_seed)
        return lambda params, config: evaluate_configuration_mock(params, config, rng)

    def test_run_grid_search(self) -> None:
        """Test grid search optimization."""
        config = OptimizationConfig(
            parameter_ranges=[
                ParameterRange("stability_low", 0.5, 0.7, step=0.1),
            ],
            targets=[
                OptimizationTarget("win_rate_delta"),
            ],
            max_iterations=100,
        )

        result = run_grid_search(
            config,
            evaluate_fn=self._make_mock_evaluate(),
        )

        # Should have evaluated 3 configurations (0.5, 0.6, 0.7)
        assert result.total_evaluations == 3
        assert result.best_fitness < float("inf")
        assert len(result.best_parameters) > 0

    def test_run_random_search(self) -> None:
        """Test random search optimization."""
        config = OptimizationConfig(
            parameter_ranges=[
                ParameterRange("stability_low", 0.5, 0.8),
            ],
            targets=[
                OptimizationTarget("win_rate_delta"),
            ],
            n_samples=20,
        )

        result = run_random_search(
            config,
            evaluate_fn=self._make_mock_evaluate(),
            seed=42,
        )

        assert result.total_evaluations == 20
        assert result.best_fitness < float("inf")
        assert result.metadata.get("algorithm") == "random_search"

    def test_run_optimization_selects_algorithm(self) -> None:
        """Test that run_optimization dispatches correctly."""
        config = OptimizationConfig(
            parameter_ranges=[
                ParameterRange("stability_low", 0.5, 0.7, step=0.1),
            ],
            targets=[
                OptimizationTarget("win_rate_delta"),
            ],
            algorithm="grid",
        )

        result = run_optimization(
            config,
            evaluate_fn=self._make_mock_evaluate(),
        )

        assert result.metadata.get("algorithm") == "grid_search"

    def test_run_optimization_invalid_algorithm(self) -> None:
        """Test that invalid algorithm raises error."""
        config = OptimizationConfig(algorithm="invalid")

        with pytest.raises(ValueError, match="Unknown algorithm"):
            run_optimization(config)


class TestResultStorage:
    """Tests for result storage integration."""

    def test_store_and_query_optimization_result(self, tmp_path: Path) -> None:
        """Test storing and querying optimization results."""
        db_path = tmp_path / "test.db"

        result = OptimizationResult(
            config={"algorithm": "grid"},
            best_parameters={"stability_low": 0.6},
            best_fitness=0.15,
            all_results=[],
            pareto_frontier=[
                ParetoPoint(
                    parameters={"stability_low": 0.6},
                    objectives={"delta": 0.15},
                ),
            ],
            total_evaluations=10,
            total_duration_seconds=5.0,
            metadata={"algorithm": "grid_search"},
        )

        # Store result
        opt_id = store_optimization_result(result, db_path)
        assert opt_id > 0

        # Query results
        runs = query_optimization_runs(db_path)
        assert len(runs) == 1
        assert runs[0]["opt_id"] == opt_id
        assert runs[0]["best_fitness"] == 0.15
        assert runs[0]["best_parameters"]["stability_low"] == 0.6

    def test_query_empty_database(self, tmp_path: Path) -> None:
        """Test querying non-existent database."""
        runs = query_optimization_runs(tmp_path / "nonexistent.db")
        assert runs == []


class TestReportGeneration:
    """Tests for report generation."""

    def test_format_optimization_report_markdown(self) -> None:
        """Test Markdown report generation."""
        result = OptimizationResult(
            config={"algorithm": "random"},
            best_parameters={"stability_low": 0.65, "stability_critical": 0.4},
            best_fitness=0.12,
            all_results=[
                FitnessResult(
                    parameters={"stability_low": 0.6},
                    combined_fitness=0.15,
                    win_rate_delta=0.15,
                ),
                FitnessResult(
                    parameters={"stability_low": 0.65},
                    combined_fitness=0.12,
                    win_rate_delta=0.12,
                ),
            ],
            pareto_frontier=[
                ParetoPoint(
                    parameters={"stability_low": 0.65},
                    objectives={"win_rate_delta": 0.12},
                ),
            ],
            total_evaluations=20,
            total_duration_seconds=10.0,
            metadata={"algorithm": "random_search"},
        )

        report = format_optimization_report_markdown(result)

        assert "Strategy Parameter Optimization Report" in report
        assert "Best Configuration" in report
        assert "stability_low" in report
        assert "0.65" in report
        assert "Pareto Frontier" in report


class TestCLI:
    """Tests for the CLI interface."""

    def test_cli_pareto_no_runs(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test pareto command with no runs."""
        db_path = tmp_path / "empty.db"

        exit_code = main([
            "--database", str(db_path),
            "pareto",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No optimization runs found" in captured.out

    def test_cli_pareto_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test pareto command with JSON output."""
        db_path = tmp_path / "test.db"

        # Store a result first
        result = OptimizationResult(
            config={"algorithm": "grid"},
            best_parameters={"stability_low": 0.6},
            best_fitness=0.15,
            all_results=[],
            pareto_frontier=[],
            total_evaluations=10,
            total_duration_seconds=5.0,
            metadata={"algorithm": "grid_search"},
        )
        store_optimization_result(result, db_path)

        exit_code = main([
            "--database", str(db_path),
            "pareto",
            "--json",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "runs" in data
        assert len(data["runs"]) == 1

    def test_cli_report_no_runs(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test report command with no runs."""
        db_path = tmp_path / "empty.db"

        exit_code = main([
            "--database", str(db_path),
            "report",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No optimization runs found" in captured.out

    def test_cli_report_with_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test report command with file output."""
        db_path = tmp_path / "test.db"
        output_path = tmp_path / "report.md"

        # Store a result first
        result = OptimizationResult(
            config={"algorithm": "random"},
            best_parameters={"stability_low": 0.65},
            best_fitness=0.12,
            all_results=[],
            pareto_frontier=[
                ParetoPoint(
                    parameters={"stability_low": 0.65},
                    objectives={"delta": 0.12},
                ),
            ],
            total_evaluations=20,
            total_duration_seconds=10.0,
            metadata={"algorithm": "random_search"},
        )
        store_optimization_result(result, db_path)

        exit_code = main([
            "--database", str(db_path),
            "report",
            "--output", str(output_path),
        ])

        assert exit_code == 0
        assert output_path.exists()
        content = output_path.read_text()
        assert "Strategy Parameter Optimization Report" in content


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_parameter_ranges(self) -> None:
        """Test optimization with no parameter ranges."""
        config = OptimizationConfig(
            parameter_ranges=[],
            targets=[OptimizationTarget("win_rate_delta")],
        )

        configs = generate_grid_configurations(config.parameter_ranges)
        assert configs == [{}]

    def test_single_target(self) -> None:
        """Test optimization with single target."""
        results = [
            FitnessResult(
                parameters={"a": 0.5},
                fitness_scores={"delta": 0.1},
                combined_fitness=0.1,
            ),
            FitnessResult(
                parameters={"a": 0.6},
                fitness_scores={"delta": 0.2},
                combined_fitness=0.2,
            ),
        ]
        targets = [OptimizationTarget("delta")]

        frontier = compute_pareto_frontier(results, targets)

        # Best point should be on frontier
        assert len(frontier) >= 1
        assert any(p.objectives.get("delta") == 0.1 for p in frontier)

    def test_all_identical_results(self) -> None:
        """Test Pareto frontier with identical results."""
        results = [
            FitnessResult(
                parameters={"a": float(i)},
                fitness_scores={"delta": 0.5, "diversity": 0.5},
            )
            for i in range(5)
        ]
        targets = [
            OptimizationTarget("delta"),
            OptimizationTarget("diversity"),
        ]

        frontier = compute_pareto_frontier(results, targets)

        # All points are non-dominated when identical
        assert len(frontier) == 5

    def test_fitness_result_serialization(self) -> None:
        """Test FitnessResult serialization."""
        result = FitnessResult(
            parameters={"stability_low": 0.65432},
            fitness_scores={"delta": 0.12345},
            combined_fitness=0.12345,
            win_rates={"balanced": 0.66667},
            win_rate_delta=0.15,
            diversity_score=0.85,
            avg_stability=0.72,
            sweep_count=15,
            duration_seconds=2.345,
        )
        data = result.to_dict()

        # Check rounding
        assert data["parameters"]["stability_low"] == 0.6543
        assert data["fitness_scores"]["delta"] == 0.1235
        assert data["combined_fitness"] == 0.1235
        assert data["win_rates"]["balanced"] == 0.6667
        assert data["duration_seconds"] == 2.35

    def test_optimization_result_serialization(self) -> None:
        """Test OptimizationResult serialization."""
        result = OptimizationResult(
            config={"algorithm": "grid"},
            best_parameters={"a": 0.5},
            best_fitness=0.1,
            all_results=[],
            pareto_frontier=[],
            total_evaluations=10,
            total_duration_seconds=5.5,
            metadata={"key": "value"},
        )
        data = result.to_dict()

        assert data["best_parameters"]["a"] == 0.5
        assert data["best_fitness"] == 0.1
        assert data["total_evaluations"] == 10
        assert data["total_duration_seconds"] == 5.5
        assert data["metadata"]["key"] == "value"
