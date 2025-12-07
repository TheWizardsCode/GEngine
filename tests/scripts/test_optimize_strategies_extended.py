"""Extended tests for strategy parameter optimization."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from importlib import util
from pathlib import Path
from unittest.mock import MagicMock, patch

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

OptimizationConfig = _driver.OptimizationConfig
FitnessResult = _driver.FitnessResult
OptimizationResult = _driver.OptimizationResult
run_bayesian_optimization = _driver.run_bayesian_optimization
evaluate_configuration = _driver.evaluate_configuration
store_optimization_result = _driver.store_optimization_result
cmd_optimize = _driver.cmd_optimize
HAS_SKOPT = _driver.HAS_SKOPT


class TestCLIExtended:
    """Extended tests for the CLI interface."""

    def test_cmd_optimize_basic(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test basic optimize command execution."""
        with patch.object(_driver, "run_optimization") as mock_run:
            # Setup mock return
            mock_run.return_value = OptimizationResult(
                config={"algorithm": "random"},
                best_parameters={"stability_low": 0.6},
                best_fitness=0.1,
                all_results=[],
                pareto_frontier=[],
                total_evaluations=10,
                total_duration_seconds=1.0,
                metadata={"algorithm": "random"},
            )

            # Create dummy config
            config_path = tmp_path / "config.yml"
            config_path.write_text("settings:\n  algorithm: random\n")

            # Run command
            args = argparse.Namespace(
                command="optimize",
                config=config_path,
                algorithm=None,
                samples=None,
                ticks=None,
                seed=None,
                output_dir=tmp_path / "output",
                json=False,
                no_store=True,
                verbose=False,
                database=tmp_path / "db.sqlite",
            )

            exit_code = cmd_optimize(args)

            assert exit_code == 0
            assert mock_run.called
            
            # Check output
            captured = capsys.readouterr()
            assert "OPTIMIZATION COMPLETE" in captured.out
            assert "Best Fitness: 0.1000" in captured.out

    def test_cmd_optimize_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test optimize command with JSON output."""
        with patch.object(_driver, "run_optimization") as mock_run:
            mock_run.return_value = OptimizationResult(
                config={"algorithm": "grid"},
                best_parameters={"p": 1.0},
                best_fitness=0.0,
                all_results=[],
                pareto_frontier=[],
                total_evaluations=1,
                total_duration_seconds=0.1,
                metadata={},
            )

            args = argparse.Namespace(
                command="optimize",
                config=tmp_path / "config.yml",
                algorithm="grid",
                samples=None,
                ticks=None,
                seed=None,
                output_dir=tmp_path / "output",
                json=True,
                no_store=True,
                verbose=False,
                database=tmp_path / "db.sqlite",
            )

            exit_code = cmd_optimize(args)

            assert exit_code == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["best_fitness"] == 0.0
            assert data["config"]["algorithm"] == "grid"


class TestBayesianOptimization:
    """Tests for Bayesian optimization."""

    def test_run_bayesian_optimization(self) -> None:
        """Test Bayesian optimization run."""
        config = OptimizationConfig(
            algorithm="bayesian",
            n_samples=5,
            bayesian_n_initial=2,
            parameter_ranges=[
                _driver.ParameterRange("x", 0.0, 1.0),
            ],
            targets=[_driver.OptimizationTarget("y")],
        )

        # Mock evaluation function
        def eval_fn(params, cfg):
            return FitnessResult(
                parameters=params,
                combined_fitness=params["x"] ** 2,  # Simple quadratic
            )

        # Mock skopt components
        with patch.object(_driver, "HAS_SKOPT", True), \
             patch.object(_driver, "gp_minimize", create=True) as mock_gp, \
             patch.object(_driver, "Real", create=True) as mock_real:
            
            # Setup mock return for gp_minimize
            mock_result = MagicMock()
            mock_result.x = [0.5]
            mock_result.fun = 0.25
            mock_gp.return_value = mock_result

            # We need to make sure the objective function passed to gp_minimize
            # calls our eval_fn.
            # gp_minimize calls the objective function with a list of values
            def side_effect(func, *args, **kwargs):
                # Call the objective function a few times
                func([0.1])
                func([0.2])
                return mock_result
            
            mock_gp.side_effect = side_effect

            result = run_bayesian_optimization(config, evaluate_fn=eval_fn, seed=42)

            assert result.metadata["algorithm"] == "bayesian"
            assert result.best_fitness == 0.25
            assert mock_gp.called
            assert mock_real.called


class TestErrorHandling:
    """Tests for error handling."""

    def test_store_optimization_result_db_error(self, tmp_path: Path) -> None:
        """Test handling of database errors."""
        # Create a directory where the file should be to cause IsADirectoryError
        db_path = tmp_path / "bad_db"
        db_path.mkdir()
        
        result = OptimizationResult(
            config={},
            best_parameters={},
            best_fitness=0.0,
            all_results=[],
            pareto_frontier=[],
            metadata={},
        )

        with pytest.raises(sqlite3.OperationalError):
            store_optimization_result(result, db_path)


class TestEvaluateConfiguration:
    """Tests for evaluate_configuration."""

    @patch("gengine.ai_player.AIActor")
    @patch("gengine.echoes.sim.SimEngine")
    @patch("gengine.ai_player.strategies.create_strategy")
    def test_evaluate_configuration_success(
        self,
        mock_create_strategy: MagicMock,
        mock_sim_engine: MagicMock,
        mock_ai_actor: MagicMock,
    ) -> None:
        """Test successful evaluation of a configuration."""
        # Setup mocks
        mock_strategy = MagicMock()
        mock_create_strategy.return_value = mock_strategy

        mock_engine_instance = MagicMock()
        mock_sim_engine.return_value = mock_engine_instance

        mock_report = MagicMock()
        mock_report.final_stability = 0.8
        mock_report.actions_taken = 10
        mock_report.ticks_run = 100

        mock_actor_instance = MagicMock()
        mock_actor_instance.run.return_value = mock_report
        mock_ai_actor.return_value = mock_actor_instance

        # Config
        config = OptimizationConfig(
            strategies=["balanced"],
            seeds=[42],
            tick_budget=100,
            targets=[_driver.OptimizationTarget("stability", direction="maximize")],
        )
        
        # Parameters
        params = {"stability_low": 0.6}

        # Run evaluation
        result = evaluate_configuration(params, config, verbose=False)

        assert result.combined_fitness != float("inf")
        assert result.sweep_count == 1
        assert result.avg_stability == 0.8
        
        # Verify mocks were called
        mock_create_strategy.assert_called()
        mock_sim_engine.assert_called()
        mock_ai_actor.assert_called()

    @patch("gengine.ai_player.strategies.create_strategy")
    def test_evaluate_configuration_failure(
        self,
        mock_create_strategy: MagicMock,
    ) -> None:
        """Test evaluation failure handling."""
        # Setup mock to raise exception
        mock_create_strategy.side_effect = ValueError("Simulation failed")

        config = OptimizationConfig(
            strategies=["balanced"],
            seeds=[42],
        )
        
        params = {"stability_low": 0.6}

        # Run evaluation
        result = evaluate_configuration(params, config, verbose=True)

        # Should return infinite fitness on error
        assert result.combined_fitness == float("inf")
        assert result.sweep_count == 0
