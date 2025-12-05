"""Designer workflow implementations for the Balance Studio.

Provides guided workflows that encapsulate common balance iteration tasks:
- Running exploratory sweeps
- Comparing configurations
- Testing tuning changes
- Viewing historical reports

These workflows leverage existing sweep and analysis infrastructure while
providing a designer-friendly interface.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .overlays import ConfigOverlay, create_tuning_overlay


@dataclass
class WorkflowResult:
    """Result from executing a workflow.

    Attributes
    ----------
    workflow_name
        Name of the workflow that was executed.
    success
        Whether the workflow completed successfully.
    message
        Human-readable summary of the result.
    output_path
        Path to any generated output files.
    data
        Structured result data.
    errors
        List of error messages if any.
    """

    workflow_name: str
    success: bool
    message: str
    output_path: Path | None = None
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "workflow_name": self.workflow_name,
            "success": self.success,
            "message": self.message,
            "output_path": str(self.output_path) if self.output_path else None,
            "data": self.data,
            "errors": self.errors,
        }


@dataclass
class ExploratorySweepConfig:
    """Configuration for an exploratory sweep workflow.

    Attributes
    ----------
    strategies
        AI strategies to test.
    difficulties
        Difficulty presets to test.
    seeds
        Random seeds for reproducibility.
    tick_budget
        Tick budget for each sweep.
    output_dir
        Directory to write results.
    overlay
        Optional overlay to apply during sweep.
    """

    strategies: list[str] = field(
        default_factory=lambda: ["balanced", "aggressive", "diplomatic"]
    )
    difficulties: list[str] = field(default_factory=lambda: ["normal"])
    seeds: list[int] = field(default_factory=lambda: [42, 123, 456])
    tick_budget: int = 100
    output_dir: Path = field(default_factory=lambda: Path("build/studio_sweeps"))
    overlay: ConfigOverlay | None = None


def run_exploratory_sweep(
    config: ExploratorySweepConfig,
    verbose: bool = False,
) -> WorkflowResult:
    """Run an exploratory sweep workflow.

    Executes batch sweeps with the specified configuration and generates
    a summary report for designer review.

    Parameters
    ----------
    config
        Sweep configuration.
    verbose
        If True, print progress messages.

    Returns
    -------
    WorkflowResult
        Result of the sweep execution.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = config.output_dir / f"sweep_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # If overlay provided, create a temporary config directory
    config_root = None
    if config.overlay:
        config_root = output_dir / "config"
        config_root.mkdir(exist_ok=True)

        # Write overlay as simulation.yml
        overlay_path = config_root / "simulation.yml"
        config.overlay.to_yaml(overlay_path)

    # Build sweep command
    cmd = [
        sys.executable,
        "scripts/run_batch_sweeps.py",
        "--strategies",
        *config.strategies,
        "--difficulties",
        *config.difficulties,
        "--seeds",
        *[str(s) for s in config.seeds],
        "--ticks",
        str(config.tick_budget),
        "--output-dir",
        str(output_dir),
    ]

    if verbose:
        cmd.append("--verbose")

    if verbose:
        sys.stderr.write(f"Running sweep: {' '.join(cmd)}\n")

    # Set config root if using overlay
    env = os.environ.copy()
    if config_root:
        env["ECHOES_CONFIG_ROOT"] = str(config_root)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout
            env=env,
        )

        if result.returncode != 0:
            return WorkflowResult(
                workflow_name="exploratory_sweep",
                success=False,
                message="Sweep failed to complete",
                output_path=output_dir,
                errors=[result.stderr],
            )

        # Load summary if available
        summary_path = output_dir / "batch_sweep_summary.json"
        summary_data: dict[str, Any] = {}
        if summary_path.exists():
            with open(summary_path) as f:
                summary_data = json.load(f)

        return WorkflowResult(
            workflow_name="exploratory_sweep",
            success=True,
            message=f"Sweep completed with {summary_data.get('completed_sweeps', 0)} "
            f"of {summary_data.get('total_sweeps', 0)} sweeps",
            output_path=output_dir,
            data=summary_data,
        )

    except subprocess.TimeoutExpired:
        return WorkflowResult(
            workflow_name="exploratory_sweep",
            success=False,
            message="Sweep timed out after 30 minutes",
            output_path=output_dir,
            errors=["Timeout exceeded"],
        )
    except FileNotFoundError as e:
        return WorkflowResult(
            workflow_name="exploratory_sweep",
            success=False,
            message="Sweep script not found",
            errors=[str(e)],
        )


@dataclass
class CompareConfigsConfig:
    """Configuration for comparing two configurations.

    Attributes
    ----------
    config_a_path
        Path to first configuration (or overlay).
    config_b_path
        Path to second configuration (or overlay).
    name_a
        Display name for first config.
    name_b
        Display name for second config.
    strategies
        Strategies to test for comparison.
    seeds
        Seeds for reproducibility.
    tick_budget
        Tick budget per sweep.
    output_dir
        Output directory for results.
    """

    config_a_path: Path
    config_b_path: Path
    name_a: str = "Config A"
    name_b: str = "Config B"
    strategies: list[str] = field(default_factory=lambda: ["balanced"])
    seeds: list[int] = field(default_factory=lambda: [42])
    tick_budget: int = 100
    output_dir: Path = field(default_factory=lambda: Path("build/studio_compare"))


def run_config_comparison(
    config: CompareConfigsConfig,
    verbose: bool = False,
) -> WorkflowResult:
    """Compare two configurations by running sweeps with each.

    Parameters
    ----------
    config
        Comparison configuration.
    verbose
        If True, print progress messages.

    Returns
    -------
    WorkflowResult
        Result including comparison data.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = config.output_dir / f"compare_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {
        "config_a": {"name": config.name_a, "path": str(config.config_a_path)},
        "config_b": {"name": config.name_b, "path": str(config.config_b_path)},
        "sweeps": {},
    }

    errors: list[str] = []

    for label, config_path, name in [
        ("a", config.config_a_path, config.name_a),
        ("b", config.config_b_path, config.name_b),
    ]:
        if verbose:
            sys.stderr.write(f"Running sweeps for {name}...\n")

        sweep_output = output_dir / f"sweep_{label}"
        sweep_output.mkdir(exist_ok=True)

        cmd = [
            sys.executable,
            "scripts/run_batch_sweeps.py",
            "--strategies",
            *config.strategies,
            "--seeds",
            *[str(s) for s in config.seeds],
            "--ticks",
            str(config.tick_budget),
            "--output-dir",
            str(sweep_output),
        ]

        env = os.environ.copy()
        if config_path.is_dir():
            env["ECHOES_CONFIG_ROOT"] = str(config_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,
                env=env,
            )

            summary_path = sweep_output / "batch_sweep_summary.json"
            if summary_path.exists():
                with open(summary_path) as f:
                    results["sweeps"][label] = json.load(f)
            elif result.returncode != 0:
                errors.append(f"Sweep {label} failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            errors.append(f"Sweep {label} timed out")
        except Exception as e:
            errors.append(f"Sweep {label} error: {e}")

    # Calculate comparison metrics if both sweeps succeeded
    if "a" in results["sweeps"] and "b" in results["sweeps"]:
        stats_a = results["sweeps"]["a"].get("strategy_stats", {})
        stats_b = results["sweeps"]["b"].get("strategy_stats", {})

        comparison: dict[str, Any] = {}
        for strategy in config.strategies:
            if strategy in stats_a and strategy in stats_b:
                avg_a = stats_a[strategy].get("avg_stability", 0)
                avg_b = stats_b[strategy].get("avg_stability", 0)
                comparison[strategy] = {
                    "stability_a": avg_a,
                    "stability_b": avg_b,
                    "delta": avg_b - avg_a,
                    "delta_percent": (
                        ((avg_b - avg_a) / avg_a * 100) if avg_a > 0 else 0
                    ),
                }

        results["comparison"] = comparison

        # Write comparison report
        report_path = output_dir / "comparison_report.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)

        return WorkflowResult(
            workflow_name="compare_configs",
            success=True,
            message=f"Compared {config.name_a} vs {config.name_b}",
            output_path=output_dir,
            data=results,
        )

    return WorkflowResult(
        workflow_name="compare_configs",
        success=False,
        message="Failed to complete comparison",
        output_path=output_dir,
        data=results,
        errors=errors,
    )


@dataclass
class TuningTestConfig:
    """Configuration for testing a tuning change.

    Attributes
    ----------
    name
        Name of the tuning experiment.
    changes
        Dictionary of configuration changes to test.
    description
        Description of what's being tested.
    baseline_config
        Path to baseline config directory.
    strategies
        Strategies to test.
    seeds
        Seeds for reproducibility.
    tick_budget
        Tick budget per sweep.
    output_dir
        Output directory.
    """

    name: str
    changes: dict[str, Any]
    description: str = ""
    baseline_config: Path | None = None
    strategies: list[str] = field(default_factory=lambda: ["balanced"])
    seeds: list[int] = field(default_factory=lambda: [42, 123])
    tick_budget: int = 100
    output_dir: Path = field(default_factory=lambda: Path("build/studio_tuning"))


def run_tuning_test(
    config: TuningTestConfig,
    verbose: bool = False,
) -> WorkflowResult:
    """Test a tuning change by comparing baseline to modified config.

    Parameters
    ----------
    config
        Tuning test configuration.
    verbose
        If True, print progress messages.

    Returns
    -------
    WorkflowResult
        Result with comparison between baseline and tuned config.
    """
    # Create overlay from changes
    overlay = create_tuning_overlay(
        name=config.name,
        changes=config.changes,
        description=config.description,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = config.output_dir / f"tuning_{config.name}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the overlay for reference
    overlay_path = output_dir / "overlay.yml"
    overlay.to_yaml(overlay_path)

    # Create modified config directory
    modified_config = output_dir / "modified_config"
    modified_config.mkdir(exist_ok=True)

    # Load base config and apply overlay
    import yaml

    base_config_path = config.baseline_config or Path("content/config")
    base_sim_yml = base_config_path / "simulation.yml"

    if base_sim_yml.exists():
        with open(base_sim_yml) as f:
            base_data = yaml.safe_load(f) or {}
        merged = overlay.apply(base_data)
        with open(modified_config / "simulation.yml", "w") as f:
            yaml.safe_dump(merged, f, default_flow_style=False)
    else:
        # Write overlay as-is if no base config
        overlay.to_yaml(modified_config / "simulation.yml")

    # Run comparison
    compare_config = CompareConfigsConfig(
        config_a_path=base_config_path,
        config_b_path=modified_config,
        name_a="Baseline",
        name_b=f"Tuned ({config.name})",
        strategies=config.strategies,
        seeds=config.seeds,
        tick_budget=config.tick_budget,
        output_dir=output_dir,
    )

    result = run_config_comparison(compare_config, verbose=verbose)

    # Enhance result with tuning-specific info
    result.workflow_name = "tuning_test"
    result.data["overlay"] = overlay.to_dict()
    result.data["changes_applied"] = config.changes

    return result


def list_historical_reports(
    reports_dir: Path = Path("build"),
    pattern: str = "**/batch_sweep_summary.json",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List available historical sweep reports.

    Parameters
    ----------
    reports_dir
        Directory to search for reports.
    pattern
        Glob pattern for finding report files.
    limit
        Maximum number of reports to return.

    Returns
    -------
    list[dict[str, Any]]
        List of report metadata.
    """
    reports: list[dict[str, Any]] = []

    for path in sorted(reports_dir.glob(pattern), reverse=True):
        try:
            with open(path) as f:
                data = json.load(f)

            metadata = data.get("metadata", {})
            reports.append(
                {
                    "path": str(path),
                    "timestamp": metadata.get("timestamp", "unknown"),
                    "git_commit": metadata.get("git_commit"),
                    "total_sweeps": data.get("total_sweeps", 0),
                    "completed_sweeps": data.get("completed_sweeps", 0),
                    "strategies": data.get("config", {}).get("strategies", []),
                    "difficulties": data.get("config", {}).get("difficulties", []),
                }
            )

            if len(reports) >= limit:
                break
        except (json.JSONDecodeError, KeyError):
            continue

    return reports


def view_historical_report(
    report_path: Path,
    output_format: str = "summary",
) -> WorkflowResult:
    """View a historical sweep report.

    Parameters
    ----------
    report_path
        Path to the report file.
    output_format
        Format for output: "summary", "json", or "html".

    Returns
    -------
    WorkflowResult
        Result with report data.
    """
    if not report_path.exists():
        return WorkflowResult(
            workflow_name="view_report",
            success=False,
            message=f"Report not found: {report_path}",
            errors=[f"File does not exist: {report_path}"],
        )

    try:
        with open(report_path) as f:
            data = json.load(f)

        return WorkflowResult(
            workflow_name="view_report",
            success=True,
            message=f"Loaded report with {data.get('total_sweeps', 0)} sweeps",
            output_path=report_path,
            data=data,
        )
    except json.JSONDecodeError as e:
        return WorkflowResult(
            workflow_name="view_report",
            success=False,
            message="Failed to parse report",
            errors=[str(e)],
        )


def get_workflow_menu() -> list[dict[str, str]]:
    """Get the list of available workflows with descriptions.

    Returns
    -------
    list[dict[str, str]]
        List of workflow descriptions.
    """
    return [
        {
            "id": "exploratory_sweep",
            "name": "Run Exploratory Sweep",
            "description": (
                "Execute batch sweeps across strategies and difficulties to "
                "explore balance space."
            ),
        },
        {
            "id": "compare_configs",
            "name": "Compare Two Configs",
            "description": (
                "Run side-by-side sweeps with different configurations and "
                "compare results."
            ),
        },
        {
            "id": "tuning_test",
            "name": "Test Tuning Change",
            "description": (
                "Create a config overlay with specific changes and compare "
                "against baseline."
            ),
        },
        {
            "id": "view_reports",
            "name": "View Historical Reports",
            "description": (
                "Browse and view previously generated sweep reports and "
                "analysis results."
            ),
        },
    ]
