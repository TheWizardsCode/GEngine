import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from gengine.balance_studio.workflows import (
    CompareConfigsConfig,
    ExploratorySweepConfig,
    TuningTestConfig,
    WorkflowResult,
    create_tuning_overlay,
    run_config_comparison,
    run_exploratory_sweep,
    run_tuning_test,
    view_historical_report,
)


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_datetime():
    with patch("gengine.balance_studio.workflows.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "20230101_120000"
        yield mock_dt


def test_create_tuning_overlay():
    """Test creating a tuning overlay."""
    name = "test_tuning"
    changes = {"simulation": {"tick_limit": 200}}
    description = "Test description"

    overlay = create_tuning_overlay(name, changes, description)

    assert overlay.name == name
    assert overlay.description == description
    assert overlay.overrides == changes
    assert overlay.metadata["type"] == "tuning_experiment"


def test_run_exploratory_sweep_success(mock_subprocess_run, mock_datetime, tmp_path):
    """Test successful execution of exploratory sweep."""
    config = ExploratorySweepConfig(
        strategies=["balanced"],
        difficulties=["normal"],
        seeds=[42],
        tick_budget=100,
        output_dir=tmp_path,
    )

    # Mock subprocess success
    mock_subprocess_run.return_value.returncode = 0

    # Create dummy summary file that the workflow expects to read
    expected_output_dir = tmp_path / "sweep_20230101_120000"
    expected_output_dir.mkdir(parents=True)
    summary_file = expected_output_dir / "batch_sweep_summary.json"
    summary_data = {"status": "success", "results": []}
    with open(summary_file, "w") as f:
        json.dump(summary_data, f)

    result = run_exploratory_sweep(config)

    assert result.success
    assert result.workflow_name == "exploratory_sweep"
    assert result.data == summary_data
    
    # Verify subprocess call
    mock_subprocess_run.assert_called_once()
    args = mock_subprocess_run.call_args[0][0]
    assert "scripts/run_batch_sweeps.py" in args[1]
    assert "--strategies" in args
    assert "balanced" in args
    assert "--difficulties" in args
    assert "normal" in args


def test_run_exploratory_sweep_failure(mock_subprocess_run, mock_datetime, tmp_path):
    """Test failure in exploratory sweep execution."""
    config = ExploratorySweepConfig(
        strategies=["balanced"],
        output_dir=tmp_path,
    )

    # Mock subprocess failure
    mock_subprocess_run.return_value.returncode = 1
    mock_subprocess_run.return_value.stderr = "Error message"

    result = run_exploratory_sweep(config)

    assert not result.success
    assert "failed" in result.message.lower()
    assert "Error message" in result.errors[0]


def test_run_config_comparison_success(mock_subprocess_run, mock_datetime, tmp_path):
    """Test successful configuration comparison."""
    config = CompareConfigsConfig(
        config_a_path=Path("path/to/a"),
        config_b_path=Path("path/to/b"),
        strategies=["balanced"],
        output_dir=tmp_path,
    )

    # Mock subprocess success for both sweeps
    mock_subprocess_run.return_value.returncode = 0

    # Create dummy summary files for both sweeps
    timestamp = "20230101_120000"
    
    def side_effect(*args, **kwargs):
        # Determine if this is sweep A or B based on args
        cmd_args = args[0]
        output_arg_index = cmd_args.index("--output-dir") + 1
        output_dir = Path(cmd_args[output_arg_index])
        
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "batch_sweep_summary.json"
        
        # Create dummy data with stats for comparison
        # Check if the output directory ends with "sweep_a" or "sweep_b"
        is_sweep_a = output_dir.name == "sweep_a"
        
        data = {
            "strategy_stats": {
                "balanced": {"avg_stability": 10.0 if is_sweep_a else 20.0}
            }
        }
        
        with open(summary_path, "w") as f:
            json.dump(data, f)
            
        return MagicMock(returncode=0)

    mock_subprocess_run.side_effect = side_effect

    result = run_config_comparison(config)

    assert result.success
    assert result.workflow_name == "compare_configs"
    assert "comparison" in result.data
    
    comparison = result.data["comparison"]
    assert "balanced" in comparison
    assert comparison["balanced"]["stability_a"] == 10.0
    assert comparison["balanced"]["stability_b"] == 20.0
    assert comparison["balanced"]["delta"] == 10.0
    assert comparison["balanced"]["delta_percent"] == 100.0


def test_run_tuning_test(mock_subprocess_run, mock_datetime, tmp_path):
    """Test tuning test workflow."""
    config = TuningTestConfig(
        name="test_tuning",
        changes={"simulation": {"tick_limit": 200}},
        output_dir=tmp_path,
    )

    # Mock yaml loading/dumping
    with patch("yaml.safe_load") as mock_safe_load,          patch("yaml.safe_dump") as mock_safe_dump:
        
        mock_safe_load.return_value = {"simulation": {"tick_limit": 100}}
        
        # Mock run_config_comparison to avoid complex subprocess mocking again
        with patch("gengine.balance_studio.workflows.run_config_comparison") as mock_compare:
            mock_compare.return_value = WorkflowResult(
                workflow_name="compare_configs",
                success=True,
                message="Compared Baseline vs Tuned (test_tuning)",
                data={},
                output_path=tmp_path
            )
            
            # We also need to mock file operations for base config
            with patch("builtins.open", create=True) as mock_open:
                # Setup mock for file existence check
                with patch("pathlib.Path.exists") as mock_exists:
                    mock_exists.return_value = True
                    
                    result = run_tuning_test(config)

                    assert result.workflow_name == "tuning_test"
                    assert result.data["changes_applied"] == config.changes
                    mock_compare.assert_called_once()


def test_view_historical_report(tmp_path):
    """Test viewing a historical report."""
    report_path = tmp_path / "report.json"
    data = {"total_sweeps": 10}
    
    with open(report_path, "w") as f:
        json.dump(data, f)
        
    result = view_historical_report(report_path)
    
    assert result.success
    assert result.data == data


def test_view_historical_report_not_found(tmp_path):
    """Test viewing a non-existent report."""
    report_path = tmp_path / "non_existent.json"
    
    result = view_historical_report(report_path)
    
    assert not result.success
    assert "Report not found" in result.message

def test_list_historical_reports(tmp_path):
    """Test listing historical reports."""
    # Create some dummy reports
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    
    report1 = reports_dir / "sweep_1" / "batch_sweep_summary.json"
    report1.parent.mkdir()
    with open(report1, "w") as f:
        json.dump({
            "metadata": {"timestamp": "20230101_120000"},
            "total_sweeps": 10,
            "completed_sweeps": 10
        }, f)
        
    report2 = reports_dir / "sweep_2" / "batch_sweep_summary.json"
    report2.parent.mkdir()
    with open(report2, "w") as f:
        json.dump({
            "metadata": {"timestamp": "20230101_130000"},
            "total_sweeps": 5,
            "completed_sweeps": 5
        }, f)
        
    from gengine.balance_studio.workflows import list_historical_reports
    
    reports = list_historical_reports(reports_dir=reports_dir)
    
    assert len(reports) == 2
    # Should be sorted reverse by path (which usually correlates with time if named correctly)
    # But glob order depends on OS.
    # Let's just check content.
    timestamps = [r["timestamp"] for r in reports]
    assert "20230101_120000" in timestamps
    assert "20230101_130000" in timestamps


def test_get_workflow_menu():
    """Test getting workflow menu."""
    from gengine.balance_studio.workflows import get_workflow_menu
    
    menu = get_workflow_menu()
    
    assert len(menu) == 4
    ids = [item["id"] for item in menu]
    assert "exploratory_sweep" in ids
    assert "compare_configs" in ids
    assert "tuning_test" in ids
    assert "view_reports" in ids


def test_run_exploratory_sweep_with_overlay(mock_subprocess_run, mock_datetime, tmp_path):
    """Test exploratory sweep with overlay."""
    from gengine.balance_studio.overlays import ConfigOverlay
    
    overlay = ConfigOverlay(name="test", overrides={"foo": "bar"})
    config = ExploratorySweepConfig(
        strategies=["balanced"],
        output_dir=tmp_path,
        overlay=overlay
    )

    mock_subprocess_run.return_value.returncode = 0
    
    # Create dummy summary
    expected_output_dir = tmp_path / "sweep_20230101_120000"
    expected_output_dir.mkdir(parents=True)
    summary_file = expected_output_dir / "batch_sweep_summary.json"
    with open(summary_file, "w") as f:
        json.dump({}, f)

    result = run_exploratory_sweep(config)
    
    assert result.success
    
    # Check that overlay was written
    config_root = expected_output_dir / "config"
    assert config_root.exists()
    assert (config_root / "simulation.yml").exists()
    
    # Check env var
    args, kwargs = mock_subprocess_run.call_args
    assert "ECHOES_CONFIG_ROOT" in kwargs["env"]
    assert str(config_root) == kwargs["env"]["ECHOES_CONFIG_ROOT"]


def test_run_exploratory_sweep_timeout(mock_subprocess_run, mock_datetime, tmp_path):
    """Test exploratory sweep timeout."""
    config = ExploratorySweepConfig(
        strategies=["balanced"],
        output_dir=tmp_path,
    )

    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=1800)

    result = run_exploratory_sweep(config)

    assert not result.success
    assert "timed out" in result.message
    assert "Timeout exceeded" in result.errors


def test_run_config_comparison_timeout(mock_subprocess_run, mock_datetime, tmp_path):
    """Test config comparison timeout."""
    config = CompareConfigsConfig(
        config_a_path=Path("a"),
        config_b_path=Path("b"),
        output_dir=tmp_path,
    )

    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=900)

    result = run_config_comparison(config)

    assert not result.success
    assert "timed out" in result.errors[0]
