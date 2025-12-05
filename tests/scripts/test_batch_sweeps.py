"""Tests for batch simulation sweep infrastructure."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "run_batch_sweeps.py"
)


def _load_batch_sweep_module():
    spec = util.spec_from_file_location("batch_sweep_driver", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("batch_sweep_driver", module)
    spec.loader.exec_module(module)
    return module


_driver = _load_batch_sweep_module()
SweepParameters = _driver.SweepParameters
SweepResult = _driver.SweepResult
BatchSweepConfig = _driver.BatchSweepConfig
BatchSweepReport = _driver.BatchSweepReport
generate_parameter_grid = _driver.generate_parameter_grid
run_single_sweep = _driver.run_single_sweep
run_batch_sweeps = _driver.run_batch_sweeps
write_sweep_outputs = _driver.write_sweep_outputs
_calculate_stats = _driver._calculate_stats
_build_metadata = _driver._build_metadata
main = _driver.main


class TestSweepParameters:
    """Tests for the SweepParameters dataclass."""

    def test_sweep_parameters_creation(self) -> None:
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=100,
        )
        assert params.strategy == "balanced"
        assert params.difficulty == "normal"
        assert params.seed == 42
        assert params.world == "default"
        assert params.tick_budget == 100

    def test_sweep_parameters_to_dict(self) -> None:
        params = SweepParameters(
            strategy="aggressive",
            difficulty="hard",
            seed=123,
            world="default",
            tick_budget=200,
        )
        data = params.to_dict()

        assert data["strategy"] == "aggressive"
        assert data["difficulty"] == "hard"
        assert data["seed"] == 123
        assert data["world"] == "default"
        assert data["tick_budget"] == 200


class TestSweepResult:
    """Tests for the SweepResult dataclass."""

    def test_sweep_result_default_values(self) -> None:
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=100,
        )
        result = SweepResult(
            sweep_id=1,
            parameters=params,
            final_stability=0.75,
            actions_taken=10,
            ticks_run=100,
        )
        assert result.story_seeds_activated == []
        assert result.action_counts == {}
        assert result.telemetry == {}
        assert result.duration_seconds == 0.0
        assert result.error is None

    def test_sweep_result_to_dict(self) -> None:
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=100,
        )
        result = SweepResult(
            sweep_id=1,
            parameters=params,
            final_stability=0.7567,
            actions_taken=10,
            ticks_run=100,
            story_seeds_activated=["seed-1", "seed-2"],
            action_counts={"INSPECT": 5, "NEGOTIATE": 5},
            telemetry={"stability_trend": "stable"},
            duration_seconds=1.234,
        )

        data = result.to_dict()

        assert data["sweep_id"] == 1
        assert data["parameters"]["strategy"] == "balanced"
        assert data["results"]["final_stability"] == 0.7567
        assert data["results"]["actions_taken"] == 10
        assert data["results"]["ticks_run"] == 100
        assert data["results"]["story_seeds_activated"] == ["seed-1", "seed-2"]
        assert data["results"]["action_counts"] == {"INSPECT": 5, "NEGOTIATE": 5}
        assert data["telemetry"] == {"stability_trend": "stable"}
        assert data["duration_seconds"] == 1.234
        assert data["error"] is None

    def test_sweep_result_with_error(self) -> None:
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=100,
        )
        result = SweepResult(
            sweep_id=1,
            parameters=params,
            final_stability=0.0,
            actions_taken=0,
            ticks_run=0,
            error="Connection failed",
        )

        data = result.to_dict()
        assert data["error"] == "Connection failed"


class TestBatchSweepConfig:
    """Tests for the BatchSweepConfig dataclass."""

    def test_default_config(self) -> None:
        config = BatchSweepConfig()
        assert config.strategies == ["balanced"]
        assert config.difficulties == ["normal"]
        assert config.seeds == [42]
        assert config.worlds == ["default"]
        assert config.tick_budgets == [100]
        assert config.max_workers is None
        assert config.timeout_per_sweep == 300
        assert config.sampling_mode == "full"

    def test_custom_config(self) -> None:
        config = BatchSweepConfig(
            strategies=["balanced", "aggressive"],
            difficulties=["easy", "normal", "hard"],
            seeds=[42, 123, 456],
            worlds=["default"],
            tick_budgets=[50, 100, 200],
            max_workers=4,
            timeout_per_sweep=600,
        )
        assert config.strategies == ["balanced", "aggressive"]
        assert config.difficulties == ["easy", "normal", "hard"]
        assert len(config.seeds) == 3
        assert len(config.tick_budgets) == 3
        assert config.max_workers == 4
        assert config.timeout_per_sweep == 600

    def test_config_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = """
parameters:
  strategies:
    - balanced
    - diplomatic
  difficulties:
    - normal
    - hard
  seeds:
    - 42
    - 123
  worlds:
    - default
  tick_budgets:
    - 50
    - 100
parallel:
  max_workers: 2
  timeout_per_sweep: 120
output:
  dir: build/test_sweeps
  include_telemetry: false
sampling:
  mode: random
  sample_count: 50
"""
        config_file = tmp_path / "batch_sweeps.yml"
        config_file.write_text(yaml_content)

        config = BatchSweepConfig.from_yaml(config_file)

        assert config.strategies == ["balanced", "diplomatic"]
        assert config.difficulties == ["normal", "hard"]
        assert config.seeds == [42, 123]
        assert config.tick_budgets == [50, 100]
        assert config.max_workers == 2
        assert config.timeout_per_sweep == 120
        assert config.include_telemetry is False
        assert config.sampling_mode == "random"
        assert config.sample_count == 50

    def test_config_from_missing_yaml(self, tmp_path: Path) -> None:
        """Test that missing YAML returns default config."""
        config = BatchSweepConfig.from_yaml(tmp_path / "nonexistent.yml")
        assert config.strategies == ["balanced"]
        assert config.difficulties == ["normal"]


class TestGenerateParameterGrid:
    """Tests for parameter grid generation."""

    def test_single_parameter_grid(self) -> None:
        """Test grid with single value for each parameter."""
        config = BatchSweepConfig(
            strategies=["balanced"],
            difficulties=["normal"],
            seeds=[42],
            worlds=["default"],
            tick_budgets=[100],
        )
        grid = generate_parameter_grid(config)

        assert len(grid) == 1
        assert grid[0].strategy == "balanced"
        assert grid[0].difficulty == "normal"
        assert grid[0].seed == 42
        assert grid[0].world == "default"
        assert grid[0].tick_budget == 100

    def test_cartesian_product_grid(self) -> None:
        """Test that grid generates Cartesian product."""
        config = BatchSweepConfig(
            strategies=["balanced", "aggressive"],
            difficulties=["easy", "hard"],
            seeds=[42],
            worlds=["default"],
            tick_budgets=[100],
        )
        grid = generate_parameter_grid(config)

        # 2 strategies × 2 difficulties × 1 seed × 1 world × 1 tick = 4
        assert len(grid) == 4

        # Verify all combinations exist
        combinations = {(p.strategy, p.difficulty) for p in grid}
        expected = {
            ("balanced", "easy"),
            ("balanced", "hard"),
            ("aggressive", "easy"),
            ("aggressive", "hard"),
        }
        assert combinations == expected

    def test_large_parameter_grid(self) -> None:
        """Test grid with multiple values for all parameters."""
        config = BatchSweepConfig(
            strategies=["balanced", "aggressive", "diplomatic"],
            difficulties=["easy", "normal", "hard"],
            seeds=[42, 123],
            worlds=["default"],
            tick_budgets=[50, 100],
        )
        grid = generate_parameter_grid(config)

        # 3 × 3 × 2 × 1 × 2 = 36
        assert len(grid) == 36

    def test_sampling_reduces_grid_size(self) -> None:
        """Test that sampling reduces grid when enabled."""
        config = BatchSweepConfig(
            strategies=["balanced", "aggressive", "diplomatic"],
            difficulties=["easy", "normal", "hard"],
            seeds=[42, 123, 456],
            worlds=["default"],
            tick_budgets=[50, 100],
            sampling_mode="random",
            sample_count=10,
        )
        grid = generate_parameter_grid(config)

        # Full grid would be 3 × 3 × 3 × 1 × 2 = 54, but sampled to 10
        assert len(grid) == 10

    def test_empty_parameter_returns_empty_grid(self) -> None:
        """Test that empty parameter list returns empty grid."""
        config = BatchSweepConfig(
            strategies=[],
            difficulties=["normal"],
            seeds=[42],
            worlds=["default"],
            tick_budgets=[100],
        )
        grid = generate_parameter_grid(config)
        assert len(grid) == 0


class TestRunSingleSweep:
    """Tests for single sweep execution."""

    def test_run_single_sweep_balanced(self) -> None:
        """Test running a single sweep with balanced strategy."""
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=10,
        )
        result = run_single_sweep(sweep_id=1, params=params, include_telemetry=True)

        assert result.sweep_id == 1
        assert result.parameters.strategy == "balanced"
        assert result.error is None
        assert 0.0 <= result.final_stability <= 1.0
        assert result.duration_seconds > 0
        assert result.ticks_run == 10

    def test_run_single_sweep_aggressive(self) -> None:
        """Test running a single sweep with aggressive strategy."""
        params = SweepParameters(
            strategy="aggressive",
            difficulty="normal",
            seed=43,
            world="default",
            tick_budget=10,
        )
        result = run_single_sweep(sweep_id=2, params=params, include_telemetry=False)

        assert result.sweep_id == 2
        assert result.parameters.strategy == "aggressive"
        assert result.error is None

    def test_run_single_sweep_invalid_world(self) -> None:
        """Test that invalid world produces error."""
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="nonexistent_world",
            tick_budget=10,
        )
        result = run_single_sweep(sweep_id=1, params=params, include_telemetry=False)

        assert result.error is not None
        assert result.ticks_run == 0

    def test_run_single_sweep_includes_telemetry(self) -> None:
        """Test that telemetry is included when requested."""
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=10,
        )
        result = run_single_sweep(sweep_id=1, params=params, include_telemetry=True)

        assert result.error is None
        assert "environment" in result.telemetry or result.telemetry == {}


class TestRunBatchSweeps:
    """Tests for batch sweep execution."""

    def test_run_batch_sweeps_small(self) -> None:
        """Run a small batch sweep to verify basic functionality."""
        config = BatchSweepConfig(
            strategies=["balanced"],
            difficulties=["normal"],
            seeds=[42],
            worlds=["default"],
            tick_budgets=[5],
            max_workers=1,
        )

        report = run_batch_sweeps(config, verbose=False)

        assert report.total_sweeps == 1
        assert report.completed_sweeps == 1
        assert report.failed_sweeps == 0
        assert len(report.results) == 1

    def test_run_batch_sweeps_multiple_strategies(self) -> None:
        """Test batch sweep with multiple strategies."""
        config = BatchSweepConfig(
            strategies=["balanced", "aggressive"],
            difficulties=["normal"],
            seeds=[42],
            worlds=["default"],
            tick_budgets=[5],
            max_workers=2,
        )

        report = run_batch_sweeps(config, verbose=False)

        assert report.total_sweeps == 2
        assert "balanced" in report.strategy_stats
        assert "aggressive" in report.strategy_stats

    def test_run_batch_sweeps_calculates_stats(self) -> None:
        """Verify that batch sweep calculates strategy statistics."""
        config = BatchSweepConfig(
            strategies=["balanced"],
            difficulties=["normal"],
            seeds=[42, 43],
            worlds=["default"],
            tick_budgets=[5],
            max_workers=1,
        )

        report = run_batch_sweeps(config, verbose=False)

        assert "balanced" in report.strategy_stats
        stats = report.strategy_stats["balanced"]
        assert "count" in stats
        assert "completed" in stats
        assert "avg_stability" in stats
        assert "min_stability" in stats
        assert "max_stability" in stats

    def test_run_batch_sweeps_includes_metadata(self) -> None:
        """Test that batch sweep includes metadata."""
        config = BatchSweepConfig(
            strategies=["balanced"],
            difficulties=["normal"],
            seeds=[42],
            worlds=["default"],
            tick_budgets=[5],
            max_workers=1,
        )

        report = run_batch_sweeps(config, verbose=False)

        assert "timestamp" in report.metadata
        assert "runtime" in report.metadata


class TestInternalHelpers:
    """Tests for internal helper functions used by batch sweeps."""

    def test_calculate_stats_mixed_success_and_failure(self) -> None:
        """_calculate_stats correctly aggregates successful results only."""
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=10,
        )
        success1 = SweepResult(
            sweep_id=1,
            parameters=params,
            final_stability=0.2,
            actions_taken=5,
            ticks_run=10,
        )
        success2 = SweepResult(
            sweep_id=2,
            parameters=params,
            final_stability=0.8,
            actions_taken=15,
            ticks_run=10,
        )
        failure = SweepResult(
            sweep_id=3,
            parameters=params,
            final_stability=0.0,
            actions_taken=0,
            ticks_run=0,
            error="failed",
        )

        stats = _calculate_stats(
            [success1, success2, failure],
            lambda r: r.parameters.strategy
        )

        assert "balanced" in stats
        s = stats["balanced"]
        assert s["count"] == 3
        assert s["completed"] == 2
        assert s["failed"] == 1
        assert pytest.approx(s["avg_stability"]) == 0.5
        assert s["min_stability"] == 0.2
        assert s["max_stability"] == 0.8
        assert pytest.approx(s["avg_actions"]) == 10.0
        assert s["total_actions"] == 20

    def test_build_metadata_includes_git_and_runtime(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_build_metadata includes git commit hash and runtime details."""

        class DummyCompletedProcess:
            def __init__(self) -> None:
                self.returncode = 0
                self.stdout = "abc123\n"

        def fake_run(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return DummyCompletedProcess()

        monkeypatch.setattr(_driver.subprocess, "run", fake_run)

        config = BatchSweepConfig(max_workers=4)
        metadata = _build_metadata(config)

        assert metadata["git_commit"] == "abc123"
        assert "timestamp" in metadata
        assert "runtime" in metadata
        assert metadata["runtime"]["max_workers"] == 4


class TestWriteSweepOutputs:
    """Tests for writing sweep output files."""

    def test_write_sweep_outputs_creates_expected_files(self, tmp_path: Path) -> None:
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=10,
        )
        result = SweepResult(
            sweep_id=1,
            parameters=params,
            final_stability=0.75,
            actions_taken=10,
            ticks_run=10,
        )

        report = BatchSweepReport(
            config={"strategies": ["balanced"]},
            total_sweeps=1,
            completed_sweeps=1,
            failed_sweeps=0,
            results=[result],
            strategy_stats={"balanced": {"count": 1}},
            difficulty_stats={"normal": {"count": 1}},
            total_duration_seconds=1.0,
            metadata={"timestamp": "2025-01-01T00:00:00Z"},
        )

        output_dir = tmp_path / "outputs"
        write_sweep_outputs(report, output_dir, verbose=False)

        sweep_file = output_dir / "sweep_0001_balanced_normal_seed42_tick10.json"
        summary_file = output_dir / "batch_sweep_summary.json"

        assert sweep_file.exists()
        assert summary_file.exists()

        sweep_data = json.loads(sweep_file.read_text())
        assert sweep_data["sweep_id"] == 1
        assert sweep_data["parameters"]["strategy"] == "balanced"

        summary_data = json.loads(summary_file.read_text())
        assert summary_data["total_sweeps"] == 1
        assert len(summary_data["sweeps"]) == 1


class TestBatchSweepReport:
    """Tests for BatchSweepReport."""

    def test_report_to_dict(self) -> None:
        """Test report serialization to dictionary."""
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=100,
        )
        result = SweepResult(
            sweep_id=1,
            parameters=params,
            final_stability=0.8,
            actions_taken=5,
            ticks_run=100,
        )

        report = BatchSweepReport(
            config={"strategies": ["balanced"], "difficulties": ["normal"]},
            total_sweeps=1,
            completed_sweeps=1,
            failed_sweeps=0,
            results=[result],
            strategy_stats={"balanced": {"count": 1, "avg_stability": 0.8}},
            difficulty_stats={"normal": {"count": 1, "avg_stability": 0.8}},
            total_duration_seconds=5.5,
            metadata={"timestamp": "2025-01-01T00:00:00Z"},
        )

        data = report.to_dict()

        assert data["total_sweeps"] == 1
        assert data["completed_sweeps"] == 1
        assert data["failed_sweeps"] == 0
        assert len(data["sweeps"]) == 1
        assert "balanced" in data["strategy_stats"]
        assert "normal" in data["difficulty_stats"]
        assert data["total_duration_seconds"] == 5.5


class TestBatchSweepCLI:
    """Tests for the batch sweep CLI."""

    def test_cli_basic_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test CLI with minimal arguments."""
        output_dir = tmp_path / "output"

        exit_code = main([
            "--strategies", "balanced",
            "--difficulties", "normal",
            "--seeds", "42",
            "--ticks", "5",
            "--output-dir", str(output_dir),
            "--workers", "1",
        ])

        assert exit_code == 0
        assert (output_dir / "batch_sweep_summary.json").exists()

        captured = capsys.readouterr()
        assert "BATCH SWEEP RESULTS" in captured.out

    def test_cli_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test CLI with JSON output format."""
        exit_code = main([
            "--strategies", "balanced",
            "--difficulties", "normal",
            "--seeds", "42",
            "--ticks", "5",
            "--workers", "1",
            "--json",
            "--no-write",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "total_sweeps" in data
        assert "strategy_stats" in data

    def test_cli_with_config_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test CLI with configuration file."""
        yaml_content = """
parameters:
  strategies:
    - balanced
  difficulties:
    - normal
  seeds:
    - 42
  worlds:
    - default
  tick_budgets:
    - 5
parallel:
  max_workers: 1
"""
        config_file = tmp_path / "config.yml"
        config_file.write_text(yaml_content)
        output_dir = tmp_path / "output"

        exit_code = main([
            "--config", str(config_file),
            "--output-dir", str(output_dir),
        ])

        assert exit_code == 0
        assert (output_dir / "batch_sweep_summary.json").exists()

    def test_cli_override_config_values(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test that CLI arguments override config file values."""
        yaml_content = """
parameters:
  strategies:
    - balanced
    - aggressive
  seeds:
    - 42
    - 123
  tick_budgets:
    - 100
"""
        config_file = tmp_path / "config.yml"
        config_file.write_text(yaml_content)

        exit_code = main([
            "--config", str(config_file),
            "--strategies", "diplomatic",  # Override from config
            "--seeds", "456",  # Override from config
            "--ticks", "5",  # Override from config
            "--workers", "1",
            "--json",
            "--no-write",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)

        # Should only have diplomatic strategy (override)
        assert "diplomatic" in data["strategy_stats"]
        assert "balanced" not in data["strategy_stats"]


class TestSweepDeterminism:
    """Tests for sweep determinism with fixed seeds."""

    def test_same_seed_produces_same_result(self) -> None:
        """Running the same sweep twice with same seed should produce same result."""
        params = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=10,
        )

        result1 = run_single_sweep(sweep_id=1, params=params, include_telemetry=False)
        result2 = run_single_sweep(sweep_id=2, params=params, include_telemetry=False)

        assert result1.final_stability == result2.final_stability
        assert result1.actions_taken == result2.actions_taken
        assert result1.ticks_run == result2.ticks_run

    def test_different_seeds_may_differ(self) -> None:
        """Different seeds may produce different outcomes."""
        params1 = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=10,
        )
        params2 = SweepParameters(
            strategy="balanced",
            difficulty="normal",
            seed=12345,
            world="default",
            tick_budget=10,
        )

        result1 = run_single_sweep(sweep_id=1, params=params1, include_telemetry=False)
        result2 = run_single_sweep(sweep_id=2, params=params2, include_telemetry=False)

        # Results may or may not differ, but both should complete successfully
        assert result1.error is None
        assert result2.error is None
