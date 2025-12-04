#!/usr/bin/env python3
"""Aggregate batch sweep results into a queryable SQLite database.

Collects sweep outputs from batch sweep JSON files into a SQLite database
that supports historical tracking and trend analysis across balance iterations.

Examples
--------
Ingest sweep results from a directory::

    uv run python scripts/aggregate_sweep_results.py ingest build/batch_sweeps

Query aggregated statistics::

    uv run python scripts/aggregate_sweep_results.py query --strategy balanced

Show recent sweep runs::

    uv run python scripts/aggregate_sweep_results.py runs --days 30
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

# Default database path
DEFAULT_DB_PATH = Path("build/sweep_results.db")

# Schema version for migrations
SCHEMA_VERSION = 1


@dataclass
class SweepRecord:
    """Individual sweep result stored in the database."""

    sweep_id: int
    run_id: int
    strategy: str
    difficulty: str
    seed: int
    world: str
    tick_budget: int
    final_stability: float
    actions_taken: int
    ticks_run: int
    story_seeds_activated: list[str] = field(default_factory=list)
    action_counts: dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "sweep_id": self.sweep_id,
            "run_id": self.run_id,
            "strategy": self.strategy,
            "difficulty": self.difficulty,
            "seed": self.seed,
            "world": self.world,
            "tick_budget": self.tick_budget,
            "final_stability": self.final_stability,
            "actions_taken": self.actions_taken,
            "ticks_run": self.ticks_run,
            "story_seeds_activated": self.story_seeds_activated,
            "action_counts": self.action_counts,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


@dataclass
class SweepRunMetadata:
    """Metadata for a batch sweep run."""

    run_id: int
    timestamp: str
    git_commit: str | None
    total_sweeps: int
    completed_sweeps: int
    failed_sweeps: int
    strategies: list[str]
    difficulties: list[str]
    worlds: list[str]
    tick_budgets: list[int]
    seeds: list[int]
    total_duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "git_commit": self.git_commit,
            "total_sweeps": self.total_sweeps,
            "completed_sweeps": self.completed_sweeps,
            "failed_sweeps": self.failed_sweeps,
            "strategies": self.strategies,
            "difficulties": self.difficulties,
            "worlds": self.worlds,
            "tick_budgets": self.tick_budgets,
            "seeds": self.seeds,
            "total_duration_seconds": self.total_duration_seconds,
        }


@dataclass
class AggregatedStats:
    """Aggregated statistics across sweeps."""

    group_key: str
    group_value: str
    count: int
    completed: int
    failed: int
    win_rate: float
    avg_stability: float
    min_stability: float
    max_stability: float
    avg_actions: float
    total_actions: int
    story_seed_activation_rate: float
    action_frequencies: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "group_key": self.group_key,
            "group_value": self.group_value,
            "count": self.count,
            "completed": self.completed,
            "failed": self.failed,
            "win_rate": round(self.win_rate, 4),
            "avg_stability": round(self.avg_stability, 4),
            "min_stability": round(self.min_stability, 4),
            "max_stability": round(self.max_stability, 4),
            "avg_actions": round(self.avg_actions, 2),
            "total_actions": self.total_actions,
            "story_seed_activation_rate": round(self.story_seed_activation_rate, 4),
            "action_frequencies": {
                k: round(v, 4) for k, v in self.action_frequencies.items()
            },
        }


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


def init_database(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database with schema.

    Parameters
    ----------
    db_path
        Path to the database file.

    Returns
    -------
    sqlite3.Connection
        Database connection.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Create schema
    conn.executescript(
        """
        -- Schema version tracking
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        );

        -- Sweep run metadata
        CREATE TABLE IF NOT EXISTS sweep_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            git_commit TEXT,
            total_sweeps INTEGER NOT NULL,
            completed_sweeps INTEGER NOT NULL,
            failed_sweeps INTEGER NOT NULL,
            strategies TEXT NOT NULL,
            difficulties TEXT NOT NULL,
            worlds TEXT NOT NULL,
            tick_budgets TEXT NOT NULL,
            seeds TEXT NOT NULL,
            total_duration_seconds REAL NOT NULL,
            source_path TEXT,
            UNIQUE(timestamp, git_commit, source_path)
        );

        -- Individual sweep results
        CREATE TABLE IF NOT EXISTS sweep_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            sweep_id INTEGER NOT NULL,
            strategy TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            seed INTEGER NOT NULL,
            world TEXT NOT NULL,
            tick_budget INTEGER NOT NULL,
            final_stability REAL NOT NULL,
            actions_taken INTEGER NOT NULL,
            ticks_run INTEGER NOT NULL,
            story_seeds_activated TEXT,
            action_counts TEXT,
            duration_seconds REAL NOT NULL,
            error TEXT,
            FOREIGN KEY (run_id) REFERENCES sweep_runs(run_id),
            UNIQUE(run_id, sweep_id)
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_sweep_results_strategy
            ON sweep_results(strategy);
        CREATE INDEX IF NOT EXISTS idx_sweep_results_difficulty
            ON sweep_results(difficulty);
        CREATE INDEX IF NOT EXISTS idx_sweep_results_world
            ON sweep_results(world);
        CREATE INDEX IF NOT EXISTS idx_sweep_runs_timestamp
            ON sweep_runs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_sweep_runs_git_commit
            ON sweep_runs(git_commit);

        -- Insert schema version if not exists
        INSERT OR IGNORE INTO schema_version (version) VALUES ({schema_version});
    """.format(schema_version=SCHEMA_VERSION)
    )

    conn.commit()
    return conn


def ingest_sweep_summary(
    conn: sqlite3.Connection, summary_path: Path
) -> SweepRunMetadata | None:
    """Ingest a batch sweep summary JSON file into the database.

    Parameters
    ----------
    conn
        Database connection.
    summary_path
        Path to batch_sweep_summary.json file.

    Returns
    -------
    SweepRunMetadata | None
        Metadata for the ingested run, or None if already exists.
    """
    if not summary_path.exists():
        return None

    with open(summary_path) as f:
        data = json.load(f)

    # Extract metadata
    metadata = data.get("metadata", {})
    timestamp = metadata.get("timestamp", datetime.now(timezone.utc).isoformat())
    git_commit = metadata.get("git_commit")
    config = data.get("config", {})

    # Check for duplicate
    cursor = conn.execute(
        """
        SELECT run_id FROM sweep_runs
        WHERE timestamp = ? AND git_commit IS ? AND source_path = ?
        """,
        (timestamp, git_commit, str(summary_path)),
    )
    existing = cursor.fetchone()
    if existing:
        return None

    # Insert sweep run metadata
    cursor = conn.execute(
        """
        INSERT INTO sweep_runs (
            timestamp, git_commit, total_sweeps, completed_sweeps,
            failed_sweeps, strategies, difficulties, worlds,
            tick_budgets, seeds, total_duration_seconds, source_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            git_commit,
            data.get("total_sweeps", 0),
            data.get("completed_sweeps", 0),
            data.get("failed_sweeps", 0),
            json.dumps(config.get("strategies", [])),
            json.dumps(config.get("difficulties", [])),
            json.dumps(config.get("worlds", [])),
            json.dumps(config.get("tick_budgets", [])),
            json.dumps(config.get("seeds", [])),
            data.get("total_duration_seconds", 0.0),
            str(summary_path),
        ),
    )
    run_id = cursor.lastrowid

    # Insert individual sweep results
    for sweep in data.get("sweeps", []):
        params = sweep.get("parameters", {})
        results = sweep.get("results", {})

        conn.execute(
            """
            INSERT OR IGNORE INTO sweep_results (
                run_id, sweep_id, strategy, difficulty, seed, world,
                tick_budget, final_stability, actions_taken, ticks_run,
                story_seeds_activated, action_counts, duration_seconds, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                sweep.get("sweep_id", 0),
                params.get("strategy", ""),
                params.get("difficulty", ""),
                params.get("seed", 0),
                params.get("world", ""),
                params.get("tick_budget", 0),
                results.get("final_stability", 0.0),
                results.get("actions_taken", 0),
                results.get("ticks_run", 0),
                json.dumps(results.get("story_seeds_activated", [])),
                json.dumps(results.get("action_counts", {})),
                sweep.get("duration_seconds", 0.0),
                sweep.get("error"),
            ),
        )

    conn.commit()

    return SweepRunMetadata(
        run_id=run_id,
        timestamp=timestamp,
        git_commit=git_commit,
        total_sweeps=data.get("total_sweeps", 0),
        completed_sweeps=data.get("completed_sweeps", 0),
        failed_sweeps=data.get("failed_sweeps", 0),
        strategies=config.get("strategies", []),
        difficulties=config.get("difficulties", []),
        worlds=config.get("worlds", []),
        tick_budgets=config.get("tick_budgets", []),
        seeds=config.get("seeds", []),
        total_duration_seconds=data.get("total_duration_seconds", 0.0),
    )


def ingest_sweep_directory(
    conn: sqlite3.Connection, directory: Path, verbose: bool = False
) -> list[SweepRunMetadata]:
    """Ingest all batch sweep summaries from a directory.

    Parameters
    ----------
    conn
        Database connection.
    directory
        Directory containing batch sweep outputs.
    verbose
        If True, print progress.

    Returns
    -------
    list[SweepRunMetadata]
        List of metadata for ingested runs.
    """
    results: list[SweepRunMetadata] = []

    # Find all summary files
    summary_files = list(directory.glob("**/batch_sweep_summary.json"))

    for summary_path in summary_files:
        if verbose:
            sys.stderr.write(f"Ingesting: {summary_path}\n")

        metadata = ingest_sweep_summary(conn, summary_path)
        if metadata:
            results.append(metadata)
            if verbose:
                msg = f"  Added run {metadata.run_id}: {metadata.total_sweeps} sweeps\n"
                sys.stderr.write(msg)
        elif verbose:
            sys.stderr.write("  Skipped (already exists)\n")

    return results


def query_sweep_results(
    conn: sqlite3.Connection,
    strategy: str | None = None,
    difficulty: str | None = None,
    world: str | None = None,
    run_id: int | None = None,
    days: int | None = None,
    git_commit: str | None = None,
    limit: int | None = None,
) -> list[SweepRecord]:
    """Query sweep results with optional filters.

    Parameters
    ----------
    conn
        Database connection.
    strategy
        Filter by strategy name.
    difficulty
        Filter by difficulty level.
    world
        Filter by world name.
    run_id
        Filter by specific run ID.
    days
        Filter to results from last N days.
    git_commit
        Filter by git commit hash (prefix match).
    limit
        Maximum number of results to return.

    Returns
    -------
    list[SweepRecord]
        Matching sweep records.
    """
    query = """
        SELECT sr.*, runs.timestamp, runs.git_commit as run_git_commit
        FROM sweep_results sr
        JOIN sweep_runs runs ON sr.run_id = runs.run_id
        WHERE 1=1
    """
    params: list[Any] = []

    if strategy:
        query += " AND sr.strategy = ?"
        params.append(strategy)

    if difficulty:
        query += " AND sr.difficulty = ?"
        params.append(difficulty)

    if world:
        query += " AND sr.world = ?"
        params.append(world)

    if run_id is not None:
        query += " AND sr.run_id = ?"
        params.append(run_id)

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND runs.timestamp >= ?"
        params.append(cutoff.isoformat())

    if git_commit:
        query += " AND runs.git_commit LIKE ?"
        params.append(f"{git_commit}%")

    query += " ORDER BY runs.timestamp DESC, sr.sweep_id"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    records: list[SweepRecord] = []
    for row in rows:
        records.append(
            SweepRecord(
                sweep_id=row["sweep_id"],
                run_id=row["run_id"],
                strategy=row["strategy"],
                difficulty=row["difficulty"],
                seed=row["seed"],
                world=row["world"],
                tick_budget=row["tick_budget"],
                final_stability=row["final_stability"],
                actions_taken=row["actions_taken"],
                ticks_run=row["ticks_run"],
                story_seeds_activated=json.loads(row["story_seeds_activated"] or "[]"),
                action_counts=json.loads(row["action_counts"] or "{}"),
                duration_seconds=row["duration_seconds"],
                error=row["error"],
            )
        )

    return records


def query_sweep_runs(
    conn: sqlite3.Connection,
    days: int | None = None,
    git_commit: str | None = None,
    limit: int | None = None,
) -> list[SweepRunMetadata]:
    """Query sweep run metadata.

    Parameters
    ----------
    conn
        Database connection.
    days
        Filter to runs from last N days.
    git_commit
        Filter by git commit hash (prefix match).
    limit
        Maximum number of runs to return.

    Returns
    -------
    list[SweepRunMetadata]
        Matching run metadata.
    """
    query = "SELECT * FROM sweep_runs WHERE 1=1"
    params: list[Any] = []

    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query += " AND timestamp >= ?"
        params.append(cutoff.isoformat())

    if git_commit:
        query += " AND git_commit LIKE ?"
        params.append(f"{git_commit}%")

    query += " ORDER BY timestamp DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    runs: list[SweepRunMetadata] = []
    for row in rows:
        runs.append(
            SweepRunMetadata(
                run_id=row["run_id"],
                timestamp=row["timestamp"],
                git_commit=row["git_commit"],
                total_sweeps=row["total_sweeps"],
                completed_sweeps=row["completed_sweeps"],
                failed_sweeps=row["failed_sweeps"],
                strategies=json.loads(row["strategies"] or "[]"),
                difficulties=json.loads(row["difficulties"] or "[]"),
                worlds=json.loads(row["worlds"] or "[]"),
                tick_budgets=json.loads(row["tick_budgets"] or "[]"),
                seeds=json.loads(row["seeds"] or "[]"),
                total_duration_seconds=row["total_duration_seconds"],
            )
        )

    return runs


def compute_aggregated_stats(
    records: list[SweepRecord],
    group_by: str = "strategy",
    stability_threshold: float = 0.5,
) -> list[AggregatedStats]:
    """Compute aggregated statistics from sweep records.

    Parameters
    ----------
    records
        List of sweep records to aggregate.
    group_by
        Field to group by ("strategy", "difficulty", "world").
    stability_threshold
        Stability threshold for win rate calculation.

    Returns
    -------
    list[AggregatedStats]
        Aggregated statistics per group.
    """
    # Group records
    groups: dict[str, list[SweepRecord]] = {}
    for record in records:
        key = getattr(record, group_by, "unknown")
        groups.setdefault(key, []).append(record)

    stats: list[AggregatedStats] = []

    for group_value, group_records in groups.items():
        # Separate successful and failed
        successful = [r for r in group_records if r.error is None]
        failed = [r for r in group_records if r.error is not None]

        # Calculate stability stats
        stabilities = [r.final_stability for r in successful]
        avg_stability = sum(stabilities) / len(stabilities) if stabilities else 0.0
        min_stability = min(stabilities) if stabilities else 0.0
        max_stability = max(stabilities) if stabilities else 0.0

        # Win rate: stability above threshold
        wins = sum(1 for s in stabilities if s >= stability_threshold)
        win_rate = wins / len(stabilities) if stabilities else 0.0

        # Action stats
        actions = [r.actions_taken for r in successful]
        avg_actions = sum(actions) / len(actions) if actions else 0.0
        total_actions = sum(actions)

        # Story seed activation rate
        activated_count = sum(1 for r in successful if r.story_seeds_activated)
        seed_activation_rate = (
            activated_count / len(successful) if successful else 0.0
        )

        # Action frequency distribution
        action_totals: dict[str, int] = {}
        for r in successful:
            for action, count in r.action_counts.items():
                action_totals[action] = action_totals.get(action, 0) + count

        total_action_count = sum(action_totals.values())
        action_frequencies = (
            {k: v / total_action_count for k, v in action_totals.items()}
            if total_action_count > 0
            else {}
        )

        stats.append(
            AggregatedStats(
                group_key=group_by,
                group_value=group_value,
                count=len(group_records),
                completed=len(successful),
                failed=len(failed),
                win_rate=win_rate,
                avg_stability=avg_stability,
                min_stability=min_stability,
                max_stability=max_stability,
                avg_actions=avg_actions,
                total_actions=total_actions,
                story_seed_activation_rate=seed_activation_rate,
                action_frequencies=action_frequencies,
            )
        )

    return stats


def compute_stats_by_strategy(
    conn: sqlite3.Connection,
    days: int | None = None,
    stability_threshold: float = 0.5,
) -> list[AggregatedStats]:
    """Compute aggregated statistics grouped by strategy.

    Parameters
    ----------
    conn
        Database connection.
    days
        Filter to results from last N days.
    stability_threshold
        Stability threshold for win rate calculation.

    Returns
    -------
    list[AggregatedStats]
        Statistics per strategy.
    """
    records = query_sweep_results(conn, days=days)
    return compute_aggregated_stats(
        records, group_by="strategy", stability_threshold=stability_threshold
    )


def compute_stats_by_difficulty(
    conn: sqlite3.Connection,
    days: int | None = None,
    stability_threshold: float = 0.5,
) -> list[AggregatedStats]:
    """Compute aggregated statistics grouped by difficulty.

    Parameters
    ----------
    conn
        Database connection.
    days
        Filter to results from last N days.
    stability_threshold
        Stability threshold for win rate calculation.

    Returns
    -------
    list[AggregatedStats]
        Statistics per difficulty level.
    """
    records = query_sweep_results(conn, days=days)
    return compute_aggregated_stats(
        records, group_by="difficulty", stability_threshold=stability_threshold
    )


def print_stats_table(stats: list[AggregatedStats]) -> None:
    """Print aggregated statistics as a formatted table."""
    if not stats:
        print("No data available.")
        return

    print("\n" + "=" * 100)
    print(f"AGGREGATED STATISTICS BY {stats[0].group_key.upper()}")
    print("=" * 100)

    # Header
    print(
        f"{'Group':<15} {'Count':>8} {'Done':>6} {'Fail':>6} {'Win%':>8} "
        f"{'Avg Stab':>10} {'Min':>8} {'Max':>8} {'Seed Act':>10}"
    )
    print("-" * 100)

    for s in stats:
        print(
            f"{s.group_value:<15} {s.count:>8} {s.completed:>6} {s.failed:>6} "
            f"{s.win_rate * 100:>7.1f}% {s.avg_stability:>10.4f} "
            f"{s.min_stability:>8.4f} {s.max_stability:>8.4f} "
            f"{s.story_seed_activation_rate * 100:>9.1f}%"
        )

    print("=" * 100)


def print_runs_table(runs: list[SweepRunMetadata]) -> None:
    """Print sweep runs as a formatted table."""
    if not runs:
        print("No sweep runs found.")
        return

    print("\n" + "=" * 100)
    print("SWEEP RUNS")
    print("=" * 100)

    # Header
    print(
        f"{'Run ID':>8} {'Timestamp':<26} {'Commit':<10} {'Total':>8} "
        f"{'Done':>8} {'Failed':>8} {'Duration':>10}"
    )
    print("-" * 100)

    for run in runs:
        commit = run.git_commit or "N/A"
        print(
            f"{run.run_id:>8} {run.timestamp:<26} {commit:<10} "
            f"{run.total_sweeps:>8} {run.completed_sweeps:>8} "
            f"{run.failed_sweeps:>8} {run.total_duration_seconds:>9.1f}s"
        )

    print("=" * 100)


def cmd_ingest(args: argparse.Namespace) -> int:
    """Handle the ingest command."""
    db_path = args.database
    directory = Path(args.directory)

    if not directory.exists():
        sys.stderr.write(f"Error: Directory not found: {directory}\n")
        return 1

    conn = init_database(db_path)
    try:
        results = ingest_sweep_directory(conn, directory, verbose=args.verbose)

        if args.json:
            output = {"ingested_runs": [r.to_dict() for r in results]}
            print(json.dumps(output, indent=2))
        else:
            print(f"\nIngested {len(results)} new sweep run(s) from {directory}")
            for metadata in results:
                print(f"  Run {metadata.run_id}: {metadata.total_sweeps} sweeps")

        return 0
    finally:
        conn.close()


def cmd_query(args: argparse.Namespace) -> int:
    """Handle the query command."""
    db_path = args.database

    if not db_path.exists():
        sys.stderr.write(f"Error: Database not found: {db_path}\n")
        return 1

    conn = init_database(db_path)
    try:
        records = query_sweep_results(
            conn,
            strategy=args.strategy,
            difficulty=args.difficulty,
            world=args.world,
            run_id=args.run_id,
            days=args.days,
            git_commit=args.commit,
            limit=args.limit,
        )

        if args.json:
            output = {"results": [r.to_dict() for r in records]}
            print(json.dumps(output, indent=2))
        else:
            if not records:
                print("No matching results found.")
                return 0

            print(f"\nFound {len(records)} matching sweep result(s)")
            print("-" * 80)

            for record in records[:20]:  # Show first 20
                status = "✓" if record.error is None else "✗"
                print(
                    f"  {status} Run {record.run_id}, Sweep {record.sweep_id}: "
                    f"{record.strategy}/{record.difficulty} "
                    f"stability={record.final_stability:.3f} "
                    f"actions={record.actions_taken}"
                )

            if len(records) > 20:
                print(f"  ... and {len(records) - 20} more")

        return 0
    finally:
        conn.close()


def cmd_stats(args: argparse.Namespace) -> int:
    """Handle the stats command."""
    db_path = args.database

    if not db_path.exists():
        sys.stderr.write(f"Error: Database not found: {db_path}\n")
        return 1

    conn = init_database(db_path)
    try:
        if args.by == "strategy":
            stats = compute_stats_by_strategy(
                conn, days=args.days, stability_threshold=args.threshold
            )
        else:
            stats = compute_stats_by_difficulty(
                conn, days=args.days, stability_threshold=args.threshold
            )

        if args.json:
            output = {"stats": [s.to_dict() for s in stats]}
            print(json.dumps(output, indent=2))
        else:
            print_stats_table(stats)

        return 0
    finally:
        conn.close()


def cmd_runs(args: argparse.Namespace) -> int:
    """Handle the runs command."""
    db_path = args.database

    if not db_path.exists():
        sys.stderr.write(f"Error: Database not found: {db_path}\n")
        return 1

    conn = init_database(db_path)
    try:
        runs = query_sweep_runs(
            conn, days=args.days, git_commit=args.commit, limit=args.limit
        )

        if args.json:
            output = {"runs": [r.to_dict() for r in runs]}
            print(json.dumps(output, indent=2))
        else:
            print_runs_table(runs)

        return 0
    finally:
        conn.close()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for sweep result aggregation."""
    parser = argparse.ArgumentParser(
        description="Aggregate batch sweep results into a queryable database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest sweep results from a directory
  python scripts/aggregate_sweep_results.py ingest build/batch_sweeps

  # Query results for a specific strategy
  python scripts/aggregate_sweep_results.py query --strategy balanced

  # Show aggregated statistics
  python scripts/aggregate_sweep_results.py stats --by strategy

  # List recent sweep runs
  python scripts/aggregate_sweep_results.py runs --days 30
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

    # Ingest command
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest batch sweep results into database"
    )
    ingest_parser.add_argument(
        "directory",
        type=str,
        help="Directory containing batch sweep JSON outputs",
    )
    ingest_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    ingest_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Query command
    query_parser = subparsers.add_parser(
        "query", help="Query sweep results"
    )
    query_parser.add_argument(
        "--strategy", "-s", type=str, help="Filter by strategy"
    )
    query_parser.add_argument(
        "--difficulty", type=str, help="Filter by difficulty"
    )
    query_parser.add_argument(
        "--world", "-w", type=str, help="Filter by world"
    )
    query_parser.add_argument(
        "--run-id", "-r", type=int, help="Filter by run ID"
    )
    query_parser.add_argument(
        "--days", type=int, help="Filter to last N days"
    )
    query_parser.add_argument(
        "--commit", "-c", type=str, help="Filter by git commit prefix"
    )
    query_parser.add_argument(
        "--limit", "-l", type=int, help="Maximum results to return"
    )
    query_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Show aggregated statistics"
    )
    stats_parser.add_argument(
        "--by",
        choices=["strategy", "difficulty"],
        default="strategy",
        help="Group statistics by field",
    )
    stats_parser.add_argument(
        "--days", type=int, help="Filter to last N days"
    )
    stats_parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Stability threshold for win rate (default: 0.5)",
    )
    stats_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    # Runs command
    runs_parser = subparsers.add_parser(
        "runs", help="List sweep runs"
    )
    runs_parser.add_argument(
        "--days", type=int, help="Filter to last N days"
    )
    runs_parser.add_argument(
        "--commit", "-c", type=str, help="Filter by git commit prefix"
    )
    runs_parser.add_argument(
        "--limit", "-l", type=int, help="Maximum runs to return"
    )
    runs_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    args = parser.parse_args(argv)

    # Dispatch to command handler
    handlers = {
        "ingest": cmd_ingest,
        "query": cmd_query,
        "stats": cmd_stats,
        "runs": cmd_runs,
    }

    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
