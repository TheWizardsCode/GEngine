#!/usr/bin/env python3
"""Designer-facing balance studio for Echoes of Emergence.

Provides guided workflows for balance iteration accessible to non-engineers:
- Run exploratory sweep: Interactive parameter selection with sensible defaults
- Compare two configs: Side-by-side comparison of sweep results
- Test tuning change: Apply YAML overlays and run quick validation
- View historical reports: Browse and view past balance reports

Examples
--------
Run the interactive balance studio::

    uv run echoes-balance-studio

Run exploratory sweep with defaults::

    uv run echoes-balance-studio sweep --strategies balanced aggressive --ticks 50

Compare two configurations::

    uv run echoes-balance-studio compare --config-a content/config/simulation.yml \\
        --config-b content/config/sweeps/difficulty-hard/simulation.yml

Test a tuning change with overlay::

    uv run echoes-balance-studio test-tuning \\
        --overlay content/config/overlays/example_tuning.yml

View historical reports::

    uv run echoes-balance-studio history --days 30
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

import yaml

# Ensure config environment is set
os.environ.setdefault("ECHOES_CONFIG_ROOT", "content/config")

# Default paths
DEFAULT_BASE_CONFIG = Path("content/config/simulation.yml")
DEFAULT_OVERLAY_DIR = Path("content/config/overlays")
DEFAULT_OUTPUT_DIR = Path("build/balance_studio")
DEFAULT_DB_PATH = Path("build/sweep_results.db")

# Available options
AVAILABLE_STRATEGIES = ["balanced", "aggressive", "diplomatic", "hybrid"]
AVAILABLE_DIFFICULTIES = ["tutorial", "easy", "normal", "hard", "brutal"]


# ============================================================================
# Config Overlay System
# ============================================================================


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Deep merge overlay into base configuration.

    Parameters
    ----------
    base
        Base configuration dictionary.
    overlay
        Overlay configuration to merge in.

    Returns
    -------
    dict[str, Any]
        Merged configuration with overlay values taking precedence.
    """
    result = copy.deepcopy(base)

    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)

    return result


def load_config(path: Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Parameters
    ----------
    path
        Path to YAML configuration file.

    Returns
    -------
    dict[str, Any]
        Configuration dictionary.
    """
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}


def load_config_with_overlay(
    base_path: Path,
    overlay_path: Path | None = None,
) -> dict[str, Any]:
    """Load base configuration and optionally merge an overlay.

    Parameters
    ----------
    base_path
        Path to base configuration file.
    overlay_path
        Optional path to overlay file to merge.

    Returns
    -------
    dict[str, Any]
        Merged configuration.
    """
    base = load_config(base_path)

    if overlay_path:
        overlay = load_config(overlay_path)
        return deep_merge(base, overlay)

    return base


def save_config(config: dict[str, Any], path: Path) -> None:
    """Save configuration to YAML file.

    Parameters
    ----------
    config
        Configuration dictionary.
    path
        Output path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def list_overlays(overlay_dir: Path = DEFAULT_OVERLAY_DIR) -> list[Path]:
    """List available overlay files.

    Parameters
    ----------
    overlay_dir
        Directory containing overlay files.

    Returns
    -------
    list[Path]
        List of overlay file paths.
    """
    if not overlay_dir.exists():
        return []

    return sorted(overlay_dir.glob("*.yml")) + sorted(overlay_dir.glob("*.yaml"))


def validate_overlay(overlay: dict[str, Any]) -> list[str]:
    """Validate an overlay configuration.

    Parameters
    ----------
    overlay
        Overlay configuration dictionary.

    Returns
    -------
    list[str]
        List of validation warnings (empty if valid).
    """
    warnings: list[str] = []

    # Check for recognized top-level keys
    known_keys = {
        "limits", "lod", "profiling", "focus", "director", "economy",
        "environment", "progression", "per_agent_progression", "campaign",
        "_meta"  # Allow metadata for overlays
    }

    for key in overlay:
        if key not in known_keys:
            warnings.append(f"Unknown top-level key: '{key}'")

    return warnings


# ============================================================================
# Sweep Execution
# ============================================================================


def run_exploratory_sweep(
    strategies: list[str] | None = None,
    difficulties: list[str] | None = None,
    seeds: list[int] | None = None,
    tick_budget: int = 50,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    config_overlay: Path | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run an exploratory balance sweep with sensible defaults.

    Parameters
    ----------
    strategies
        Strategies to test (defaults to all).
    difficulties
        Difficulties to test (defaults to ["normal"]).
    seeds
        Random seeds (defaults to [42, 123, 456]).
    tick_budget
        Ticks per sweep (default 50).
    output_dir
        Output directory for results.
    config_overlay
        Optional overlay to apply to base config.
    verbose
        Print progress to stderr.

    Returns
    -------
    dict[str, Any]
        Sweep results summary.
    """
    from scripts.run_batch_sweeps import (
        BatchSweepConfig,
        run_batch_sweeps,
        write_sweep_outputs,
    )

    # Apply defaults
    if strategies is None:
        strategies = ["balanced", "aggressive"]
    if difficulties is None:
        difficulties = ["normal"]
    if seeds is None:
        seeds = [42, 123, 456]

    # Prepare output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # If overlay specified, create temporary merged config
    if config_overlay:
        merged = load_config_with_overlay(DEFAULT_BASE_CONFIG, config_overlay)
        temp_config_dir = output_dir / "temp_config"
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        save_config(merged, temp_config_dir / "simulation.yml")
        # Set environment variable for the overlay config
        os.environ["ECHOES_CONFIG_ROOT"] = str(temp_config_dir)

    # Create sweep configuration
    config = BatchSweepConfig(
        strategies=strategies,
        difficulties=difficulties,
        seeds=seeds,
        worlds=["default"],
        tick_budgets=[tick_budget],
        max_workers=min(4, os.cpu_count() or 1),
        output_dir=output_dir,
        include_telemetry=True,
    )

    if verbose:
        sys.stderr.write("Running exploratory sweep:\n")
        sys.stderr.write(f"  Strategies: {strategies}\n")
        sys.stderr.write(f"  Difficulties: {difficulties}\n")
        sys.stderr.write(f"  Seeds: {seeds}\n")
        sys.stderr.write(f"  Tick budget: {tick_budget}\n")
        if config_overlay:
            sys.stderr.write(f"  Overlay: {config_overlay}\n")

    # Run sweeps
    report = run_batch_sweeps(config, verbose=verbose)

    # Write outputs
    write_sweep_outputs(report, output_dir, verbose=verbose)

    return report.to_dict()


def compare_configs(
    config_a_path: Path,
    config_b_path: Path,
    strategies: list[str] | None = None,
    tick_budget: int = 30,
    seeds: list[int] | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    verbose: bool = False,
) -> dict[str, Any]:
    """Compare two configurations by running identical sweeps.

    Parameters
    ----------
    config_a_path
        Path to first configuration.
    config_b_path
        Path to second configuration.
    strategies
        Strategies to test.
    tick_budget
        Ticks per sweep.
    seeds
        Random seeds.
    output_dir
        Output directory.
    verbose
        Print progress.

    Returns
    -------
    dict[str, Any]
        Comparison results with delta analysis.
    """
    from scripts.run_batch_sweeps import (
        BatchSweepConfig,
        run_batch_sweeps,
    )

    if strategies is None:
        strategies = ["balanced"]
    if seeds is None:
        seeds = [42, 123]

    results: dict[str, Any] = {
        "config_a": str(config_a_path),
        "config_b": str(config_b_path),
        "comparison": {},
    }

    for label, config_path in [("a", config_a_path), ("b", config_b_path)]:
        config_root = config_path.parent

        config = BatchSweepConfig(
            strategies=strategies,
            difficulties=["normal"],
            seeds=seeds,
            worlds=["default"],
            tick_budgets=[tick_budget],
            max_workers=2,
            include_telemetry=False,
        )

        # Set environment for config root
        old_env = os.environ.get("ECHOES_CONFIG_ROOT")
        os.environ["ECHOES_CONFIG_ROOT"] = str(config_root)

        try:
            if verbose:
                sys.stderr.write(f"Running sweep with config {label}: {config_path}\n")
            report = run_batch_sweeps(config, verbose=verbose)
            results[f"config_{label}_results"] = report.to_dict()
        finally:
            if old_env:
                os.environ["ECHOES_CONFIG_ROOT"] = old_env
            else:
                os.environ.pop("ECHOES_CONFIG_ROOT", None)

    # Compute deltas
    if "config_a_results" in results and "config_b_results" in results:
        a_stats = results["config_a_results"].get("strategy_stats", {})
        b_stats = results["config_b_results"].get("strategy_stats", {})

        for strategy in set(a_stats.keys()) | set(b_stats.keys()):
            a_avg = a_stats.get(strategy, {}).get("avg_stability", 0.0)
            b_avg = b_stats.get(strategy, {}).get("avg_stability", 0.0)
            delta = b_avg - a_avg

            results["comparison"][strategy] = {
                "config_a_avg_stability": round(a_avg, 4),
                "config_b_avg_stability": round(b_avg, 4),
                "delta": round(delta, 4),
                "change_percent": round((delta / a_avg * 100) if a_avg else 0, 2),
            }

    return results


def test_tuning_change(
    overlay_path: Path,
    base_config: Path = DEFAULT_BASE_CONFIG,
    strategy: str = "balanced",
    tick_budget: int = 30,
    seed: int = 42,
    verbose: bool = False,
) -> dict[str, Any]:
    """Test a tuning change by running a quick validation sweep.

    Parameters
    ----------
    overlay_path
        Path to overlay file.
    base_config
        Path to base configuration.
    strategy
        Strategy to test.
    tick_budget
        Ticks to run.
    seed
        Random seed.
    verbose
        Print progress.

    Returns
    -------
    dict[str, Any]
        Validation results with baseline comparison.
    """
    from scripts.run_batch_sweeps import (
        BatchSweepConfig,
        run_batch_sweeps,
    )

    # Validate overlay
    overlay = load_config(overlay_path)
    warnings = validate_overlay(overlay)

    results: dict[str, Any] = {
        "overlay": str(overlay_path),
        "overlay_content": overlay,
        "validation_warnings": warnings,
        "baseline": {},
        "with_overlay": {},
        "comparison": {},
    }

    config = BatchSweepConfig(
        strategies=[strategy],
        difficulties=["normal"],
        seeds=[seed],
        worlds=["default"],
        tick_budgets=[tick_budget],
        max_workers=1,
        include_telemetry=True,
    )

    # Run baseline
    if verbose:
        sys.stderr.write("Running baseline sweep...\n")

    old_env = os.environ.get("ECHOES_CONFIG_ROOT")
    os.environ["ECHOES_CONFIG_ROOT"] = str(base_config.parent)

    try:
        baseline_report = run_batch_sweeps(config, verbose=verbose)
        results["baseline"] = baseline_report.to_dict()
    finally:
        if old_env:
            os.environ["ECHOES_CONFIG_ROOT"] = old_env
        else:
            os.environ.pop("ECHOES_CONFIG_ROOT", None)

    # Run with overlay
    if verbose:
        sys.stderr.write("Running sweep with overlay...\n")

    merged = load_config_with_overlay(base_config, overlay_path)
    temp_dir = Path("/tmp/balance_studio_test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    save_config(merged, temp_dir / "simulation.yml")

    os.environ["ECHOES_CONFIG_ROOT"] = str(temp_dir)

    try:
        overlay_report = run_batch_sweeps(config, verbose=verbose)
        results["with_overlay"] = overlay_report.to_dict()
    finally:
        if old_env:
            os.environ["ECHOES_CONFIG_ROOT"] = old_env
        else:
            os.environ.pop("ECHOES_CONFIG_ROOT", None)

    # Compute comparison
    baseline_stab = (
        results["baseline"]
        .get("strategy_stats", {})
        .get(strategy, {})
        .get("avg_stability", 0.0)
    )
    overlay_stab = (
        results["with_overlay"]
        .get("strategy_stats", {})
        .get(strategy, {})
        .get("avg_stability", 0.0)
    )
    delta = overlay_stab - baseline_stab

    if delta > 0.01:
        impact = "positive"
    elif delta < -0.01:
        impact = "negative"
    else:
        impact = "neutral"

    results["comparison"] = {
        "baseline_stability": round(baseline_stab, 4),
        "overlay_stability": round(overlay_stab, 4),
        "delta": round(delta, 4),
        "impact": impact,
    }

    return results


# ============================================================================
# Historical Reports
# ============================================================================


def get_historical_reports(
    db_path: Path = DEFAULT_DB_PATH,
    days: int | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Get list of historical sweep runs.

    Parameters
    ----------
    db_path
        Path to SQLite database.
    days
        Filter to last N days.
    limit
        Maximum reports to return.

    Returns
    -------
    list[dict[str, Any]]
        List of run summaries.
    """
    import sqlite3

    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            run_id,
            timestamp,
            git_commit,
            total_sweeps,
            completed_sweeps,
            failed_sweeps,
            strategies,
            difficulties,
            total_duration_seconds
        FROM sweep_runs
        WHERE 1=1
    """
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND timestamp >= ?"
        params.append(cutoff.isoformat())

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        reports = []
        for row in rows:
            reports.append({
                "run_id": row["run_id"],
                "timestamp": row["timestamp"],
                "git_commit": row["git_commit"],
                "total_sweeps": row["total_sweeps"],
                "completed_sweeps": row["completed_sweeps"],
                "failed_sweeps": row["failed_sweeps"],
                "strategies": json.loads(row["strategies"] or "[]"),
                "difficulties": json.loads(row["difficulties"] or "[]"),
                "duration_seconds": row["total_duration_seconds"],
            })

        return reports
    finally:
        conn.close()


def view_report_details(
    run_id: int,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, Any]:
    """Get detailed results for a specific run.

    Parameters
    ----------
    run_id
        Run ID to query.
    db_path
        Path to SQLite database.

    Returns
    -------
    dict[str, Any]
        Detailed run results.
    """
    import sqlite3

    if not db_path.exists():
        return {"error": "Database not found"}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # Get run metadata
        cursor = conn.execute(
            "SELECT * FROM sweep_runs WHERE run_id = ?",
            (run_id,)
        )
        run_row = cursor.fetchone()

        if not run_row:
            return {"error": f"Run {run_id} not found"}

        # Get sweep results
        cursor = conn.execute(
            """
            SELECT strategy, difficulty,
                   AVG(final_stability) as avg_stability,
                   COUNT(*) as count,
                   SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END) as completed
            FROM sweep_results
            WHERE run_id = ?
            GROUP BY strategy, difficulty
            """,
            (run_id,)
        )
        result_rows = cursor.fetchall()

        results_by_strategy: dict[str, list[dict[str, Any]]] = {}
        for row in result_rows:
            strategy = row["strategy"]
            if strategy not in results_by_strategy:
                results_by_strategy[strategy] = []
            results_by_strategy[strategy].append({
                "difficulty": row["difficulty"],
                "avg_stability": round(row["avg_stability"], 4),
                "count": row["count"],
                "completed": row["completed"],
            })

        return {
            "run_id": run_row["run_id"],
            "timestamp": run_row["timestamp"],
            "git_commit": run_row["git_commit"],
            "total_sweeps": run_row["total_sweeps"],
            "completed_sweeps": run_row["completed_sweeps"],
            "failed_sweeps": run_row["failed_sweeps"],
            "duration_seconds": run_row["total_duration_seconds"],
            "results_by_strategy": results_by_strategy,
        }
    finally:
        conn.close()


# ============================================================================
# Enhanced HTML Report
# ============================================================================


def generate_enhanced_html_report(
    db_path: Path = DEFAULT_DB_PATH,
    days: int | None = None,
    filter_strategy: str | None = None,
    filter_difficulty: str | None = None,
    output_path: Path | None = None,
) -> str:
    """Generate an enhanced HTML balance report with filtering/sorting.

    Parameters
    ----------
    db_path
        Path to SQLite database.
    days
        Filter to last N days.
    filter_strategy
        Filter to specific strategy.
    filter_difficulty
        Filter to specific difficulty.
    output_path
        Optional path to save HTML file.

    Returns
    -------
    str
        HTML report content.
    """
    import sqlite3

    if not db_path.exists():
        return "<html><body><h1>Error: Database not found</h1></body></html>"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Query data with optional filters
    query = """
        SELECT
            sr.strategy,
            sr.difficulty,
            sr.final_stability,
            sr.actions_taken,
            sr.ticks_run,
            runs.timestamp,
            runs.git_commit
        FROM sweep_results sr
        JOIN sweep_runs runs ON sr.run_id = runs.run_id
        WHERE sr.error IS NULL
    """
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND runs.timestamp >= ?"
        params.append(cutoff.isoformat())

    if filter_strategy:
        query += " AND sr.strategy = ?"
        params.append(filter_strategy)

    if filter_difficulty:
        query += " AND sr.difficulty = ?"
        params.append(filter_difficulty)

    query += " ORDER BY runs.timestamp DESC, sr.strategy, sr.difficulty"

    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        # Aggregate statistics
        stats_by_strategy: dict[str, dict[str, Any]] = {}
        stats_by_difficulty: dict[str, dict[str, Any]] = {}

        for row in rows:
            strategy = row["strategy"]
            difficulty = row["difficulty"]
            stability = row["final_stability"]

            if strategy not in stats_by_strategy:
                stats_by_strategy[strategy] = {"stabilities": [], "actions": []}
            stats_by_strategy[strategy]["stabilities"].append(stability)
            stats_by_strategy[strategy]["actions"].append(row["actions_taken"])

            if difficulty not in stats_by_difficulty:
                stats_by_difficulty[difficulty] = {"stabilities": [], "actions": []}
            stats_by_difficulty[difficulty]["stabilities"].append(stability)
            stats_by_difficulty[difficulty]["actions"].append(row["actions_taken"])

        # Calculate aggregates
        for _key, stats in stats_by_strategy.items():
            stabilities = stats["stabilities"]
            actions = stats["actions"]
            stats["count"] = len(stabilities)
            if stabilities:
                stats["avg_stability"] = sum(stabilities) / len(stabilities)
            else:
                stats["avg_stability"] = 0
            stats["min_stability"] = min(stabilities) if stabilities else 0
            stats["max_stability"] = max(stabilities) if stabilities else 0
            stats["avg_actions"] = sum(actions) / len(actions) if actions else 0
            wins = sum(1 for s in stabilities if s >= 0.5)
            stats["win_rate"] = wins / len(stabilities) if stabilities else 0

        for _key, stats in stats_by_difficulty.items():
            stabilities = stats["stabilities"]
            actions = stats["actions"]
            stats["count"] = len(stabilities)
            if stabilities:
                stats["avg_stability"] = sum(stabilities) / len(stabilities)
            else:
                stats["avg_stability"] = 0
            stats["min_stability"] = min(stabilities) if stabilities else 0
            stats["max_stability"] = max(stabilities) if stabilities else 0
            stats["avg_actions"] = sum(actions) / len(actions) if actions else 0
            wins = sum(1 for s in stabilities if s >= 0.5)
            stats["win_rate"] = wins / len(stabilities) if stabilities else 0

        # Build HTML
        html = _build_enhanced_html(
            stats_by_strategy,
            stats_by_difficulty,
            filter_strategy,
            filter_difficulty,
            days,
            len(rows),
        )

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)

        return html
    finally:
        conn.close()


def _build_enhanced_html(
    stats_by_strategy: dict[str, dict[str, Any]],
    stats_by_difficulty: dict[str, dict[str, Any]],
    filter_strategy: str | None,
    filter_difficulty: str | None,
    days: int | None,
    total_results: int,
) -> str:
    """Build enhanced HTML report with filtering UI."""
    timestamp = datetime.now(timezone.utc).isoformat()

    # CSS styles split for line length
    filter_css = (
        ".filters { background: #f8f9fa; padding: 15px; "
        "border-radius: 8px; margin-bottom: 20px; }"
    )
    btn_css = (
        ".filters button { background: #3498db; color: white; "
        "padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }"
    )
    sumbox_css = (
        ".summary-box { display: inline-block; padding: 15px; margin: 10px; "
        "background: #ecf0f1; border-radius: 8px; min-width: 150px; "
        "text-align: center; }"
    )
    active_css = (
        ".active-filter { background: #e8f4f8; padding: 5px 10px; "
        "border-radius: 4px; display: inline-block; margin: 2px; }"
    )
    url_js = (
        "  var url = window.location.pathname + "
        "(params.length ? '?' + params.join('&') : '');"
    )

    html = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        "<title>Balance Studio Report</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 20px; max-width: 1400px; }",
        "h1 { color: #2c3e50; }",
        "h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 8px; }",
        filter_css,
        ".filters label { margin-right: 10px; }",
        ".filters select { margin-right: 20px; padding: 5px; }",
        btn_css,
        ".filters button:hover { background: #2980b9; }",
        "table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
        "th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }",
        "th { background: #3498db; color: white; cursor: pointer; }",
        "th:hover { background: #2980b9; }",
        "tr:nth-child(even) { background: #f2f2f2; }",
        "tr:hover { background: #e8e8e8; }",
        ".stat-good { color: #27ae60; font-weight: bold; }",
        ".stat-warn { color: #f39c12; font-weight: bold; }",
        ".stat-bad { color: #e74c3c; font-weight: bold; }",
        sumbox_css,
        ".summary-box h3 { margin: 0 0 10px 0; color: #7f8c8d; font-size: 14px; }",
        ".summary-box .value { font-size: 24px; font-weight: bold; color: #2c3e50; }",
        active_css,
        "</style>",
        "<script>",
        "function sortTable(table, column) {",
        "  var rows = Array.from(table.querySelectorAll('tbody tr'));",
        "  var asc = table.getAttribute('data-sort-' + column) !== 'asc';",
        "  rows.sort(function(a, b) {",
        "    var aVal = a.cells[column].textContent;",
        "    var bVal = b.cells[column].textContent;",
        "    var aNum = parseFloat(aVal.replace('%', ''));",
        "    var bNum = parseFloat(bVal.replace('%', ''));",
        "    if (!isNaN(aNum) && !isNaN(bNum)) return asc ? aNum - bNum : bNum - aNum;",
        "    return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);",
        "  });",
        "  var tbody = table.querySelector('tbody');",
        "  rows.forEach(function(row) { tbody.appendChild(row); });",
        "  table.setAttribute('data-sort-' + column, asc ? 'asc' : 'desc');",
        "}",
        "function applyFilters() {",
        "  var strategy = document.getElementById('filter-strategy').value;",
        "  var difficulty = document.getElementById('filter-difficulty').value;",
        "  var days = document.getElementById('filter-days').value;",
        "  var params = [];",
        "  if (strategy) params.push('strategy=' + strategy);",
        "  if (difficulty) params.push('difficulty=' + difficulty);",
        "  if (days) params.push('days=' + days);",
        url_js,
        "  window.location.href = url;",
        "}",
        "</script>",
        "</head><body>",
        "<h1>🎮 Balance Studio Report</h1>",
        f"<p><em>Generated: {timestamp}</em></p>",
    ]

    # Summary boxes
    html.append("<div>")
    sb = "<div class='summary-box'><h3>Total Results</h3>"
    html.append(f"{sb}<div class='value'>{total_results}</div></div>")

    if stats_by_strategy:
        all_stabilities = []
        for s in stats_by_strategy.values():
            all_stabilities.extend(s.get("stabilities", []))
        if all_stabilities:
            avg = sum(all_stabilities) / len(all_stabilities)
            sb_avg = "<div class='summary-box'><h3>Avg Stability</h3>"
            html.append(f"{sb_avg}<div class='value'>{avg:.2f}</div></div>")
            wins = sum(1 for s in all_stabilities if s >= 0.5)
            win_rate = wins / len(all_stabilities) * 100
            sb_win = "<div class='summary-box'><h3>Win Rate</h3>"
            html.append(f"{sb_win}<div class='value'>{win_rate:.1f}%</div></div>")

    html.append("</div>")

    # Active filters
    if filter_strategy or filter_difficulty or days:
        html.append("<p><strong>Active Filters:</strong> ")
        if filter_strategy:
            af = "<span class='active-filter'>"
            html.append(f"{af}Strategy: {filter_strategy}</span>")
        if filter_difficulty:
            af = "<span class='active-filter'>"
            html.append(f"{af}Difficulty: {filter_difficulty}</span>")
        if days:
            html.append(f"<span class='active-filter'>Last {days} days</span>")
        html.append("</p>")

    # Filter UI
    html.append("<div class='filters'>")
    html.append("<label>Strategy:</label>")
    html.append("<select id='filter-strategy'>")
    html.append("<option value=''>All</option>")
    for s in AVAILABLE_STRATEGIES:
        selected = "selected" if s == filter_strategy else ""
        html.append(f"<option value='{s}' {selected}>{s}</option>")
    html.append("</select>")

    html.append("<label>Difficulty:</label>")
    html.append("<select id='filter-difficulty'>")
    html.append("<option value=''>All</option>")
    for d in AVAILABLE_DIFFICULTIES:
        selected = "selected" if d == filter_difficulty else ""
        html.append(f"<option value='{d}' {selected}>{d}</option>")
    html.append("</select>")

    html.append("<label>Days:</label>")
    html.append("<select id='filter-days'>")
    html.append("<option value=''>All time</option>")
    for d in [7, 14, 30, 60, 90]:
        selected = "selected" if d == days else ""
        html.append(f"<option value='{d}' {selected}>Last {d} days</option>")
    html.append("</select>")

    html.append("<button onclick='applyFilters()'>Apply Filters</button>")
    html.append("</div>")

    # Strategy table
    html.append("<h2>📊 Results by Strategy</h2>")
    html.append("<table id='strategy-table'>")
    html.append("<thead><tr>")
    th_strat = "onclick='sortTable(document.getElementById(\"strategy-table\"), "
    html.append(f"<th {th_strat}0)'>Strategy ↕</th>")
    html.append(f"<th {th_strat}1)'>Count ↕</th>")
    html.append(f"<th {th_strat}2)'>Avg Stability ↕</th>")
    html.append(f"<th {th_strat}3)'>Min ↕</th>")
    html.append(f"<th {th_strat}4)'>Max ↕</th>")
    html.append(f"<th {th_strat}5)'>Win Rate ↕</th>")
    html.append(f"<th {th_strat}6)'>Avg Actions ↕</th>")
    html.append("</tr></thead><tbody>")

    for strategy, stats in sorted(stats_by_strategy.items()):
        win_rate = stats["win_rate"] * 100
        if win_rate >= 60:
            win_class = "stat-good"
        elif win_rate >= 40:
            win_class = "stat-warn"
        else:
            win_class = "stat-bad"
        html.append("<tr>")
        html.append(f"<td><strong>{strategy}</strong></td>")
        html.append(f"<td>{stats['count']}</td>")
        html.append(f"<td>{stats['avg_stability']:.3f}</td>")
        html.append(f"<td>{stats['min_stability']:.3f}</td>")
        html.append(f"<td>{stats['max_stability']:.3f}</td>")
        html.append(f"<td class='{win_class}'>{win_rate:.1f}%</td>")
        html.append(f"<td>{stats['avg_actions']:.1f}</td>")
        html.append("</tr>")

    html.append("</tbody></table>")

    # Difficulty table
    html.append("<h2>🎯 Results by Difficulty</h2>")
    html.append("<table id='difficulty-table'>")
    html.append("<thead><tr>")
    th_diff = "onclick='sortTable(document.getElementById(\"difficulty-table\"), "
    html.append(f"<th {th_diff}0)'>Difficulty ↕</th>")
    html.append(f"<th {th_diff}1)'>Count ↕</th>")
    html.append(f"<th {th_diff}2)'>Avg Stability ↕</th>")
    html.append(f"<th {th_diff}3)'>Min ↕</th>")
    html.append(f"<th {th_diff}4)'>Max ↕</th>")
    html.append(f"<th {th_diff}5)'>Win Rate ↕</th>")
    html.append("</tr></thead><tbody>")

    for difficulty, stats in sorted(stats_by_difficulty.items()):
        win_rate = stats["win_rate"] * 100
        if win_rate >= 60:
            win_class = "stat-good"
        elif win_rate >= 40:
            win_class = "stat-warn"
        else:
            win_class = "stat-bad"
        html.append("<tr>")
        html.append(f"<td><strong>{difficulty}</strong></td>")
        html.append(f"<td>{stats['count']}</td>")
        html.append(f"<td>{stats['avg_stability']:.3f}</td>")
        html.append(f"<td>{stats['min_stability']:.3f}</td>")
        html.append(f"<td>{stats['max_stability']:.3f}</td>")
        html.append(f"<td class='{win_class}'>{win_rate:.1f}%</td>")
        html.append("</tr>")

    html.append("</tbody></table>")

    html.append("</body></html>")
    return "\n".join(html)


# ============================================================================
# CLI Commands
# ============================================================================


def cmd_sweep(args: argparse.Namespace) -> int:
    """Handle the sweep command."""
    strategies = args.strategies if args.strategies else None
    difficulties = args.difficulties if args.difficulties else None
    seeds = args.seeds if args.seeds else None
    overlay = Path(args.overlay) if args.overlay else None

    result = run_exploratory_sweep(
        strategies=strategies,
        difficulties=difficulties,
        seeds=seeds,
        tick_budget=args.ticks,
        output_dir=Path(args.output_dir),
        config_overlay=overlay,
        verbose=args.verbose,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("EXPLORATORY SWEEP COMPLETE")
        print("=" * 60)
        print(f"Total sweeps: {result.get('total_sweeps', 0)}")
        print(f"Completed: {result.get('completed_sweeps', 0)}")
        print(f"Failed: {result.get('failed_sweeps', 0)}")
        print(f"Duration: {result.get('total_duration_seconds', 0):.1f}s")

        if "strategy_stats" in result:
            print("\nStrategy Results:")
            for strategy, stats in result["strategy_stats"].items():
                avg = stats.get('avg_stability', 0)
                print(f"  {strategy}: avg_stability={avg:.3f}")

        print(f"\nResults saved to: {args.output_dir}")

    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle the compare command."""
    config_a = Path(args.config_a)
    config_b = Path(args.config_b)

    if not config_a.exists():
        sys.stderr.write(f"Error: Config A not found: {config_a}\n")
        return 1
    if not config_b.exists():
        sys.stderr.write(f"Error: Config B not found: {config_b}\n")
        return 1

    strategies = args.strategies if args.strategies else None
    seeds = args.seeds if args.seeds else None

    result = compare_configs(
        config_a_path=config_a,
        config_b_path=config_b,
        strategies=strategies,
        tick_budget=args.ticks,
        seeds=seeds,
        output_dir=Path(args.output_dir),
        verbose=args.verbose,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("CONFIG COMPARISON")
        print("=" * 60)
        print(f"Config A: {result['config_a']}")
        print(f"Config B: {result['config_b']}")

        if result.get("comparison"):
            print("\nComparison Results:")
            for strategy, comp in result["comparison"].items():
                delta = comp["delta"]
                direction = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
                change_pct = comp['change_percent']
                print(f"  {strategy}:")
                print(f"    Config A: {comp['config_a_avg_stability']:.3f}")
                print(f"    Config B: {comp['config_b_avg_stability']:.3f}")
                print(f"    Delta: {direction} {delta:+.3f} ({change_pct:+.1f}%)")

    return 0


def cmd_test_tuning(args: argparse.Namespace) -> int:
    """Handle the test-tuning command."""
    overlay_path = Path(args.overlay)
    base_config = Path(args.base_config) if args.base_config else DEFAULT_BASE_CONFIG

    if not overlay_path.exists():
        sys.stderr.write(f"Error: Overlay not found: {overlay_path}\n")
        return 1
    if not base_config.exists():
        sys.stderr.write(f"Error: Base config not found: {base_config}\n")
        return 1

    result = test_tuning_change(
        overlay_path=overlay_path,
        base_config=base_config,
        strategy=args.strategy,
        tick_budget=args.ticks,
        seed=args.seed,
        verbose=args.verbose,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("TUNING CHANGE TEST")
        print("=" * 60)
        print(f"Overlay: {result['overlay']}")

        if result.get("validation_warnings"):
            print("\n⚠️  Validation Warnings:")
            for warning in result["validation_warnings"]:
                print(f"  - {warning}")

        if result.get("comparison"):
            comp = result["comparison"]
            impact = comp["impact"]
            if impact == "positive":
                icon = "✅"
            elif impact == "negative":
                icon = "❌"
            else:
                icon = "➡️"

            print("\nResults:")
            print(f"  Baseline stability: {comp['baseline_stability']:.3f}")
            print(f"  With overlay: {comp['overlay_stability']:.3f}")
            print(f"  Delta: {comp['delta']:+.3f}")
            print(f"  Impact: {icon} {impact}")

    return 0


def cmd_history(args: argparse.Namespace) -> int:
    """Handle the history command."""
    db_path = Path(args.database)

    reports = get_historical_reports(
        db_path=db_path,
        days=args.days,
        limit=args.limit,
    )

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print("\n" + "=" * 60)
        print("HISTORICAL SWEEP RUNS")
        print("=" * 60)

        if not reports:
            print("No sweep runs found.")
            print(f"Database path: {db_path}")
            return 0

        print(f"{'ID':<6} {'Timestamp':<22} {'Sweeps':<8} {'Done':<6} {'Duration':>10}")
        print("-" * 60)

        for report in reports:
            print(
                f"{report['run_id']:<6} "
                f"{report['timestamp'][:19]:<22} "
                f"{report['total_sweeps']:<8} "
                f"{report['completed_sweeps']:<6} "
                f"{report['duration_seconds']:>9.1f}s"
            )

    return 0


def cmd_view(args: argparse.Namespace) -> int:
    """Handle the view command."""
    db_path = Path(args.database)

    result = view_report_details(
        run_id=args.run_id,
        db_path=db_path,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            sys.stderr.write(f"Error: {result['error']}\n")
            return 1

        print("\n" + "=" * 60)
        print(f"SWEEP RUN #{result['run_id']} DETAILS")
        print("=" * 60)
        print(f"Timestamp: {result['timestamp']}")
        print(f"Git commit: {result.get('git_commit', 'N/A')}")
        print(f"Total sweeps: {result['total_sweeps']}")
        print(f"Completed: {result['completed_sweeps']}")
        print(f"Duration: {result['duration_seconds']:.1f}s")

        if result.get("results_by_strategy"):
            print("\nResults by Strategy:")
            for strategy, results_list in result["results_by_strategy"].items():
                print(f"\n  {strategy}:")
                for r in results_list:
                    diff = r['difficulty']
                    stab = r['avg_stability']
                    n = r['count']
                    comp = r['completed']
                    print(f"    {diff}: avg_stability={stab:.3f} (n={n}, done={comp})")

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Handle the report command."""
    db_path = Path(args.database)
    output_path = Path(args.output) if args.output else None

    html = generate_enhanced_html_report(
        db_path=db_path,
        days=args.days,
        filter_strategy=args.strategy,
        filter_difficulty=args.difficulty,
        output_path=output_path,
    )

    if output_path:
        print(f"Report saved to: {output_path}")
    else:
        print(html)

    return 0


def cmd_overlays(args: argparse.Namespace) -> int:
    """Handle the overlays command."""
    overlay_dir = Path(args.overlay_dir)

    overlays = list_overlays(overlay_dir)

    if args.json:
        print(json.dumps([str(o) for o in overlays], indent=2))
    else:
        print("\n" + "=" * 60)
        print("AVAILABLE OVERLAYS")
        print("=" * 60)
        print(f"Directory: {overlay_dir}")

        if not overlays:
            print("\nNo overlay files found.")
            return 0

        print(f"\n{'File':<40} {'Keys'}")
        print("-" * 60)

        for overlay_path in overlays:
            config = load_config(overlay_path)
            keys = ", ".join(config.keys()) if config else "(empty)"
            print(f"{overlay_path.name:<40} {keys}")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the balance studio."""
    parser = argparse.ArgumentParser(
        description="Designer-facing balance studio for Echoes of Emergence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflows:
  sweep       Run an exploratory balance sweep with sensible defaults
  compare     Compare two configurations side-by-side
  test-tuning Test a tuning change by applying a YAML overlay
  history     View historical sweep runs
  view        View details of a specific sweep run
  report      Generate an enhanced HTML balance report
  overlays    List available overlay files

Examples:
  # Run exploratory sweep with default parameters
  echoes-balance-studio sweep

  # Run sweep with specific strategies
  echoes-balance-studio sweep --strategies balanced aggressive --ticks 50

  # Compare two configurations
  echoes-balance-studio compare \\
      --config-a content/config/simulation.yml \\
      --config-b content/config/sweeps/difficulty-hard/simulation.yml

  # Test a tuning change
  echoes-balance-studio test-tuning --overlay content/config/overlays/example_tuning.yml

  # View historical reports
  echoes-balance-studio history --days 30

  # Generate HTML report with filters
  echoes-balance-studio report --strategy balanced --output build/report.html
""",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sweep command
    sweep_parser = subparsers.add_parser(
        "sweep", help="Run an exploratory balance sweep"
    )
    sweep_parser.add_argument(
        "--strategies", "-s", nargs="+", choices=AVAILABLE_STRATEGIES,
        help="Strategies to test (default: balanced, aggressive)"
    )
    sweep_parser.add_argument(
        "--difficulties", "-d", nargs="+", choices=AVAILABLE_DIFFICULTIES,
        help="Difficulties to test (default: normal)"
    )
    sweep_parser.add_argument(
        "--seeds", nargs="+", type=int,
        help="Random seeds (default: 42, 123, 456)"
    )
    sweep_parser.add_argument(
        "--ticks", "-t", type=int, default=50,
        help="Tick budget per sweep (default: 50)"
    )
    sweep_parser.add_argument(
        "--overlay", "-o", type=str,
        help="Path to overlay file to apply"
    )
    sweep_parser.add_argument(
        "--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    sweep_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    sweep_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print progress"
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare two configurations"
    )
    compare_parser.add_argument(
        "--config-a", "-a", type=str, required=True,
        help="Path to first configuration"
    )
    compare_parser.add_argument(
        "--config-b", "-b", type=str, required=True,
        help="Path to second configuration"
    )
    compare_parser.add_argument(
        "--strategies", "-s", nargs="+", choices=AVAILABLE_STRATEGIES,
        help="Strategies to test"
    )
    compare_parser.add_argument(
        "--seeds", nargs="+", type=int,
        help="Random seeds"
    )
    compare_parser.add_argument(
        "--ticks", "-t", type=int, default=30,
        help="Tick budget (default: 30)"
    )
    compare_parser.add_argument(
        "--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory"
    )
    compare_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    compare_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print progress"
    )

    # Test tuning command
    tuning_parser = subparsers.add_parser(
        "test-tuning", help="Test a tuning change with an overlay"
    )
    tuning_parser.add_argument(
        "--overlay", "-o", type=str, required=True,
        help="Path to overlay file"
    )
    tuning_parser.add_argument(
        "--base-config", "-b", type=str,
        help=f"Path to base config (default: {DEFAULT_BASE_CONFIG})"
    )
    tuning_parser.add_argument(
        "--strategy", "-s", type=str, default="balanced",
        choices=AVAILABLE_STRATEGIES,
        help="Strategy to test (default: balanced)"
    )
    tuning_parser.add_argument(
        "--ticks", "-t", type=int, default=30,
        help="Tick budget (default: 30)"
    )
    tuning_parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)"
    )
    tuning_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )
    tuning_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print progress"
    )

    # History command
    history_parser = subparsers.add_parser(
        "history", help="View historical sweep runs"
    )
    history_parser.add_argument(
        "--database", "-d", type=str, default=str(DEFAULT_DB_PATH),
        help=f"Path to database (default: {DEFAULT_DB_PATH})"
    )
    history_parser.add_argument(
        "--days", type=int,
        help="Filter to last N days"
    )
    history_parser.add_argument(
        "--limit", "-l", type=int, default=20,
        help="Maximum reports to show (default: 20)"
    )
    history_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    # View command
    view_parser = subparsers.add_parser(
        "view", help="View details of a specific sweep run"
    )
    view_parser.add_argument(
        "run_id", type=int,
        help="Run ID to view"
    )
    view_parser.add_argument(
        "--database", "-d", type=str, default=str(DEFAULT_DB_PATH),
        help=f"Path to database (default: {DEFAULT_DB_PATH})"
    )
    view_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate enhanced HTML balance report"
    )
    report_parser.add_argument(
        "--database", "-d", type=str, default=str(DEFAULT_DB_PATH),
        help=f"Path to database (default: {DEFAULT_DB_PATH})"
    )
    report_parser.add_argument(
        "--days", type=int,
        help="Filter to last N days"
    )
    report_parser.add_argument(
        "--strategy", "-s", type=str, choices=AVAILABLE_STRATEGIES,
        help="Filter by strategy"
    )
    report_parser.add_argument(
        "--difficulty", type=str, choices=AVAILABLE_DIFFICULTIES,
        help="Filter by difficulty"
    )
    report_parser.add_argument(
        "--output", "-o", type=str,
        help="Output HTML file path"
    )

    # Overlays command
    overlays_parser = subparsers.add_parser(
        "overlays", help="List available overlay files"
    )
    overlays_parser.add_argument(
        "--overlay-dir", type=str, default=str(DEFAULT_OVERLAY_DIR),
        help=f"Overlay directory (default: {DEFAULT_OVERLAY_DIR})"
    )
    overlays_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args(argv)

    handlers = {
        "sweep": cmd_sweep,
        "compare": cmd_compare,
        "test-tuning": cmd_test_tuning,
        "history": cmd_history,
        "view": cmd_view,
        "report": cmd_report,
        "overlays": cmd_overlays,
    }

    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
