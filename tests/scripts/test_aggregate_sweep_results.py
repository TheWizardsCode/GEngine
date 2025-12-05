"""Tests for sweep result aggregation and storage."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "aggregate_sweep_results.py"
)


def _load_aggregate_module():
    spec = util.spec_from_file_location("aggregate_sweep_results", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("aggregate_sweep_results", module)
    spec.loader.exec_module(module)
    return module


_module = _load_aggregate_module()
SweepRecord = _module.SweepRecord
SweepRunMetadata = _module.SweepRunMetadata
AggregatedStats = _module.AggregatedStats
init_database = _module.init_database
ingest_sweep_summary = _module.ingest_sweep_summary
ingest_sweep_directory = _module.ingest_sweep_directory
query_sweep_results = _module.query_sweep_results
query_sweep_runs = _module.query_sweep_runs
compute_aggregated_stats = _module.compute_aggregated_stats
compute_stats_by_strategy = _module.compute_stats_by_strategy
compute_stats_by_difficulty = _module.compute_stats_by_difficulty
main = _module.main


@pytest.fixture
def sample_sweep_summary() -> dict:
    """Create a sample batch sweep summary for testing."""
    return {
        "config": {
            "strategies": ["balanced", "aggressive"],
            "difficulties": ["normal"],
            "seeds": [42, 123],
            "worlds": ["default"],
            "tick_budgets": [100],
        },
        "total_sweeps": 4,
        "completed_sweeps": 3,
        "failed_sweeps": 1,
        "strategy_stats": {},
        "difficulty_stats": {},
        "total_duration_seconds": 10.5,
        "metadata": {
            "timestamp": "2025-01-15T10:00:00+00:00",
            "git_commit": "abc1234",
            "runtime": {"python_version": "3.12", "max_workers": 4},
        },
        "sweeps": [
            {
                "sweep_id": 0,
                "parameters": {
                    "strategy": "balanced",
                    "difficulty": "normal",
                    "seed": 42,
                    "world": "default",
                    "tick_budget": 100,
                },
                "results": {
                    "final_stability": 0.75,
                    "actions_taken": 10,
                    "ticks_run": 100,
                    "story_seeds_activated": ["seed-1"],
                    "action_counts": {"INSPECT": 5, "NEGOTIATE": 5},
                },
                "duration_seconds": 2.5,
                "error": None,
            },
            {
                "sweep_id": 1,
                "parameters": {
                    "strategy": "balanced",
                    "difficulty": "normal",
                    "seed": 123,
                    "world": "default",
                    "tick_budget": 100,
                },
                "results": {
                    "final_stability": 0.85,
                    "actions_taken": 12,
                    "ticks_run": 100,
                    "story_seeds_activated": [],
                    "action_counts": {"INSPECT": 6, "DEPLOY_RESOURCE": 6},
                },
                "duration_seconds": 2.6,
                "error": None,
            },
            {
                "sweep_id": 2,
                "parameters": {
                    "strategy": "aggressive",
                    "difficulty": "normal",
                    "seed": 42,
                    "world": "default",
                    "tick_budget": 100,
                },
                "results": {
                    "final_stability": 0.45,
                    "actions_taken": 20,
                    "ticks_run": 100,
                    "story_seeds_activated": ["seed-1", "seed-2"],
                    "action_counts": {"DEPLOY_RESOURCE": 15, "NEGOTIATE": 5},
                },
                "duration_seconds": 2.7,
                "error": None,
            },
            {
                "sweep_id": 3,
                "parameters": {
                    "strategy": "aggressive",
                    "difficulty": "normal",
                    "seed": 123,
                    "world": "default",
                    "tick_budget": 100,
                },
                "results": {
                    "final_stability": 0.0,
                    "actions_taken": 0,
                    "ticks_run": 0,
                    "story_seeds_activated": [],
                    "action_counts": {},
                },
                "duration_seconds": 0.1,
                "error": "Connection timeout",
            },
        ],
    }


class TestDatabaseSchema:
    """Tests for database initialization and schema."""

    def test_init_database_creates_tables(self, tmp_path: Path) -> None:
        """Database initialization creates required tables."""
        db_path = tmp_path / "test.db"
        conn = init_database(db_path)

        # Check tables exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}

        assert "sweep_runs" in tables
        assert "sweep_results" in tables
        assert "schema_version" in tables

        conn.close()

    def test_init_database_creates_indexes(self, tmp_path: Path) -> None:
        """Database initialization creates indexes for efficient queries."""
        db_path = tmp_path / "test.db"
        conn = init_database(db_path)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_sweep_results_strategy" in indexes
        assert "idx_sweep_results_difficulty" in indexes
        assert "idx_sweep_runs_timestamp" in indexes

        conn.close()

    def test_init_database_is_idempotent(self, tmp_path: Path) -> None:
        """Calling init_database multiple times doesn't cause errors."""
        db_path = tmp_path / "test.db"

        conn1 = init_database(db_path)
        conn1.close()

        # Second call should succeed without error
        conn2 = init_database(db_path)
        conn2.close()


class TestIngestion:
    """Tests for ingesting sweep results."""

    def test_ingest_sweep_summary(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Ingest a batch sweep summary file."""
        # Create summary file
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        # Initialize database and ingest
        db_path = tmp_path / "test.db"
        conn = init_database(db_path)

        metadata = ingest_sweep_summary(conn, summary_path)

        assert metadata is not None
        assert metadata.run_id == 1
        assert metadata.git_commit == "abc1234"
        assert metadata.total_sweeps == 4
        assert metadata.completed_sweeps == 3
        assert metadata.failed_sweeps == 1

        # Verify data was stored
        cursor = conn.execute("SELECT COUNT(*) FROM sweep_results")
        count = cursor.fetchone()[0]
        assert count == 4

        conn.close()

    def test_ingest_prevents_duplicates(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Ingesting the same file twice doesn't create duplicates."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)

        # First ingest
        metadata1 = ingest_sweep_summary(conn, summary_path)
        assert metadata1 is not None

        # Second ingest should return None (duplicate)
        metadata2 = ingest_sweep_summary(conn, summary_path)
        assert metadata2 is None

        # Verify only one run exists
        cursor = conn.execute("SELECT COUNT(*) FROM sweep_runs")
        count = cursor.fetchone()[0]
        assert count == 1

        conn.close()

    def test_ingest_directory(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Ingest all summaries from a directory."""
        # Create two sweep directories with summaries
        for i in range(2):
            sweep_dir = tmp_path / f"sweeps_{i}"
            sweep_dir.mkdir()
            summary = sample_sweep_summary.copy()
            summary["metadata"] = {
                "timestamp": f"2025-01-1{i}T10:00:00+00:00",
                "git_commit": f"abc{i}234",
            }
            summary_path = sweep_dir / "batch_sweep_summary.json"
            summary_path.write_text(json.dumps(summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)

        results = ingest_sweep_directory(conn, tmp_path)

        assert len(results) == 2

        # Verify both runs exist
        cursor = conn.execute("SELECT COUNT(*) FROM sweep_runs")
        count = cursor.fetchone()[0]
        assert count == 2

        conn.close()


class TestQuerying:
    """Tests for querying sweep results."""

    def test_query_by_strategy(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Query results filtered by strategy."""
        # Setup
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)
        ingest_sweep_summary(conn, summary_path)

        # Query
        results = query_sweep_results(conn, strategy="balanced")

        assert len(results) == 2
        assert all(r.strategy == "balanced" for r in results)

        conn.close()

    def test_query_by_difficulty(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Query results filtered by difficulty."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)
        ingest_sweep_summary(conn, summary_path)

        results = query_sweep_results(conn, difficulty="normal")

        assert len(results) == 4
        assert all(r.difficulty == "normal" for r in results)

        conn.close()

    def test_query_by_run_id(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Query results filtered by run ID."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)
        ingest_sweep_summary(conn, summary_path)

        results = query_sweep_results(conn, run_id=1)

        assert len(results) == 4
        assert all(r.run_id == 1 for r in results)

        conn.close()

    def test_query_with_limit(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Query results with result limit."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)
        ingest_sweep_summary(conn, summary_path)

        results = query_sweep_results(conn, limit=2)

        assert len(results) == 2

        conn.close()

    def test_query_sweep_runs_by_days(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Query sweep runs filtered by recency."""
        # Create a summary with a recent timestamp
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        recent_summary = sample_sweep_summary.copy()
        recent_summary["metadata"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "git_commit": "recent123",
        }
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(recent_summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)
        ingest_sweep_summary(conn, summary_path)

        # Query for last 7 days should find it
        runs = query_sweep_runs(conn, days=7)
        assert len(runs) == 1
        assert runs[0].git_commit == "recent123"

        conn.close()

    def test_query_sweep_runs_by_commit(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Query sweep runs filtered by git commit prefix."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"
        conn = init_database(db_path)
        ingest_sweep_summary(conn, summary_path)

        runs = query_sweep_runs(conn, git_commit="abc")
        assert len(runs) == 1
        assert runs[0].git_commit == "abc1234"

        # Non-matching prefix
        runs = query_sweep_runs(conn, git_commit="xyz")
        assert len(runs) == 0

        conn.close()


class TestAggregation:
    """Tests for aggregation logic."""

    def test_compute_aggregated_stats_by_strategy(self) -> None:
        """Compute aggregated statistics grouped by strategy."""
        records = [
            SweepRecord(
                sweep_id=0,
                run_id=1,
                strategy="balanced",
                difficulty="normal",
                seed=42,
                world="default",
                tick_budget=100,
                final_stability=0.75,
                actions_taken=10,
                ticks_run=100,
                story_seeds_activated=["seed-1"],
                action_counts={"INSPECT": 5, "NEGOTIATE": 5},
            ),
            SweepRecord(
                sweep_id=1,
                run_id=1,
                strategy="balanced",
                difficulty="normal",
                seed=123,
                world="default",
                tick_budget=100,
                final_stability=0.65,
                actions_taken=8,
                ticks_run=100,
                story_seeds_activated=[],
                action_counts={"INSPECT": 8},
            ),
            SweepRecord(
                sweep_id=2,
                run_id=1,
                strategy="aggressive",
                difficulty="normal",
                seed=42,
                world="default",
                tick_budget=100,
                final_stability=0.45,
                actions_taken=20,
                ticks_run=100,
                story_seeds_activated=["seed-1", "seed-2"],
                action_counts={"DEPLOY_RESOURCE": 20},
            ),
        ]

        stats = compute_aggregated_stats(records, group_by="strategy")

        assert len(stats) == 2

        balanced_stats = next(s for s in stats if s.group_value == "balanced")
        assert balanced_stats.count == 2
        assert balanced_stats.completed == 2
        assert balanced_stats.failed == 0
        assert balanced_stats.avg_stability == pytest.approx(0.7, abs=0.01)
        assert balanced_stats.win_rate == 1.0  # Both >= 0.5
        assert balanced_stats.story_seed_activation_rate == 0.5  # 1 of 2

        aggressive_stats = next(s for s in stats if s.group_value == "aggressive")
        assert aggressive_stats.count == 1
        assert aggressive_stats.win_rate == 0.0  # 0.45 < 0.5

    def test_compute_aggregated_stats_with_errors(self) -> None:
        """Aggregation correctly handles failed sweeps."""
        records = [
            SweepRecord(
                sweep_id=0,
                run_id=1,
                strategy="balanced",
                difficulty="normal",
                seed=42,
                world="default",
                tick_budget=100,
                final_stability=0.75,
                actions_taken=10,
                ticks_run=100,
            ),
            SweepRecord(
                sweep_id=1,
                run_id=1,
                strategy="balanced",
                difficulty="normal",
                seed=123,
                world="default",
                tick_budget=100,
                final_stability=0.0,
                actions_taken=0,
                ticks_run=0,
                error="Connection failed",
            ),
        ]

        stats = compute_aggregated_stats(records, group_by="strategy")

        assert len(stats) == 1
        s = stats[0]
        assert s.count == 2
        assert s.completed == 1
        assert s.failed == 1
        assert s.avg_stability == 0.75  # Only from successful

    def test_compute_aggregated_stats_action_frequencies(self) -> None:
        """Aggregation computes correct action frequency distribution."""
        records = [
            SweepRecord(
                sweep_id=0,
                run_id=1,
                strategy="balanced",
                difficulty="normal",
                seed=42,
                world="default",
                tick_budget=100,
                final_stability=0.75,
                actions_taken=10,
                ticks_run=100,
                action_counts={"INSPECT": 6, "NEGOTIATE": 4},
            ),
            SweepRecord(
                sweep_id=1,
                run_id=1,
                strategy="balanced",
                difficulty="normal",
                seed=123,
                world="default",
                tick_budget=100,
                final_stability=0.80,
                actions_taken=10,
                ticks_run=100,
                action_counts={"INSPECT": 4, "NEGOTIATE": 6},
            ),
        ]

        stats = compute_aggregated_stats(records, group_by="strategy")

        s = stats[0]
        # Total: INSPECT=10, NEGOTIATE=10 => 50% each
        assert s.action_frequencies["INSPECT"] == pytest.approx(0.5)
        assert s.action_frequencies["NEGOTIATE"] == pytest.approx(0.5)

    def test_compute_stats_empty_records(self) -> None:
        """Aggregation handles empty record list."""
        stats = compute_aggregated_stats([], group_by="strategy")
        assert stats == []


class TestDataclasses:
    """Tests for dataclass serialization."""

    def test_sweep_record_to_dict(self) -> None:
        """SweepRecord serializes to dict correctly."""
        record = SweepRecord(
            sweep_id=1,
            run_id=1,
            strategy="balanced",
            difficulty="normal",
            seed=42,
            world="default",
            tick_budget=100,
            final_stability=0.75,
            actions_taken=10,
            ticks_run=100,
            story_seeds_activated=["seed-1"],
            action_counts={"INSPECT": 5},
            duration_seconds=2.5,
        )

        data = record.to_dict()

        assert data["sweep_id"] == 1
        assert data["strategy"] == "balanced"
        assert data["final_stability"] == 0.75
        assert data["story_seeds_activated"] == ["seed-1"]
        assert data["action_counts"] == {"INSPECT": 5}

    def test_sweep_run_metadata_to_dict(self) -> None:
        """SweepRunMetadata serializes to dict correctly."""
        metadata = SweepRunMetadata(
            run_id=1,
            timestamp="2025-01-15T10:00:00+00:00",
            git_commit="abc1234",
            total_sweeps=4,
            completed_sweeps=3,
            failed_sweeps=1,
            strategies=["balanced", "aggressive"],
            difficulties=["normal"],
            worlds=["default"],
            tick_budgets=[100],
            seeds=[42, 123],
            total_duration_seconds=10.5,
        )

        data = metadata.to_dict()

        assert data["run_id"] == 1
        assert data["git_commit"] == "abc1234"
        assert data["strategies"] == ["balanced", "aggressive"]

    def test_aggregated_stats_to_dict(self) -> None:
        """AggregatedStats serializes to dict with proper rounding."""
        stats = AggregatedStats(
            group_key="strategy",
            group_value="balanced",
            count=10,
            completed=9,
            failed=1,
            win_rate=0.777777,
            avg_stability=0.666666,
            min_stability=0.5,
            max_stability=0.9,
            avg_actions=12.333333,
            total_actions=111,
            story_seed_activation_rate=0.444444,
            action_frequencies={"INSPECT": 0.333333},
        )

        data = stats.to_dict()

        assert data["win_rate"] == 0.7778
        assert data["avg_stability"] == 0.6667
        assert data["avg_actions"] == 12.33
        assert data["action_frequencies"]["INSPECT"] == 0.3333


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_ingest_creates_database(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """CLI ingest command creates database and ingests data."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"

        exit_code = main([
            "--database", str(db_path),
            "ingest", str(sweep_dir),
        ])

        assert exit_code == 0
        assert db_path.exists()

    def test_cli_stats_json_output(
        self, tmp_path: Path, sample_sweep_summary: dict, capsys
    ) -> None:
        """CLI stats command outputs JSON when requested."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"

        # First ingest
        main([
            "--database", str(db_path),
            "ingest", str(sweep_dir),
        ])

        # Clear the capsys buffer from ingest
        _ = capsys.readouterr()

        # Then get stats as JSON
        exit_code = main([
            "--database", str(db_path),
            "stats", "--by", "strategy", "--json",
        ])

        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "stats" in data
        assert len(data["stats"]) == 2

    def test_cli_query_with_filters(
        self, tmp_path: Path, sample_sweep_summary: dict, capsys
    ) -> None:
        """CLI query command applies filters correctly."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"

        main([
            "--database", str(db_path),
            "ingest", str(sweep_dir),
        ])

        # Clear the capsys buffer from ingest
        _ = capsys.readouterr()

        exit_code = main([
            "--database", str(db_path),
            "query", "--strategy", "balanced", "--json",
        ])

        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data["results"]) == 2
        assert all(r["strategy"] == "balanced" for r in data["results"])

    def test_cli_runs_command(
        self, tmp_path: Path, sample_sweep_summary: dict, capsys
    ) -> None:
        """CLI runs command lists sweep runs."""
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(sample_sweep_summary))

        db_path = tmp_path / "test.db"

        main([
            "--database", str(db_path),
            "ingest", str(sweep_dir),
        ])

        # Clear the capsys buffer from ingest
        _ = capsys.readouterr()

        exit_code = main([
            "--database", str(db_path),
            "runs", "--json",
        ])

        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data["runs"]) == 1
        assert data["runs"][0]["git_commit"] == "abc1234"

    def test_cli_error_missing_database(
        self, tmp_path: Path, capsys
    ) -> None:
        """CLI returns error when database doesn't exist for query."""
        db_path = tmp_path / "nonexistent.db"

        exit_code = main([
            "--database", str(db_path),
            "query",
        ])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestHistoricalTracking:
    """Tests for historical tracking features."""

    def test_multiple_runs_tracked_separately(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Multiple sweep runs are tracked as separate entries."""
        db_path = tmp_path / "test.db"
        conn = init_database(db_path)

        # Create and ingest two separate runs
        for i in range(2):
            sweep_dir = tmp_path / f"sweeps_{i}"
            sweep_dir.mkdir()
            summary = sample_sweep_summary.copy()
            summary["metadata"] = {
                "timestamp": f"2025-01-{10 + i}T10:00:00+00:00",
                "git_commit": f"commit{i}",
            }
            summary_path = sweep_dir / "batch_sweep_summary.json"
            summary_path.write_text(json.dumps(summary))
            ingest_sweep_summary(conn, summary_path)

        # Verify both runs exist
        runs = query_sweep_runs(conn)
        assert len(runs) == 2

        # Each has its own git commit
        commits = {r.git_commit for r in runs}
        assert commits == {"commit0", "commit1"}

        conn.close()

    def test_query_by_date_range(
        self, tmp_path: Path, sample_sweep_summary: dict
    ) -> None:
        """Results can be filtered by date range."""
        db_path = tmp_path / "test.db"
        conn = init_database(db_path)

        # Create run with recent timestamp
        sweep_dir = tmp_path / "sweeps"
        sweep_dir.mkdir()
        recent_summary = sample_sweep_summary.copy()
        now = datetime.now(timezone.utc)
        recent_summary["metadata"] = {
            "timestamp": now.isoformat(),
            "git_commit": "recent",
        }
        summary_path = sweep_dir / "batch_sweep_summary.json"
        summary_path.write_text(json.dumps(recent_summary))
        ingest_sweep_summary(conn, summary_path)

        # Create run with old timestamp
        old_dir = tmp_path / "sweeps_old"
        old_dir.mkdir()
        old_summary = sample_sweep_summary.copy()
        old_time = now - timedelta(days=60)
        old_summary["metadata"] = {
            "timestamp": old_time.isoformat(),
            "git_commit": "old",
        }
        old_path = old_dir / "batch_sweep_summary.json"
        old_path.write_text(json.dumps(old_summary))
        ingest_sweep_summary(conn, old_path)

        # Query last 30 days
        recent_results = query_sweep_results(conn, days=30)
        recent_run_ids = {r.run_id for r in recent_results}

        # Query all time
        all_results = query_sweep_results(conn)
        all_run_ids = {r.run_id for r in all_results}

        # Recent should have fewer unique runs than all
        assert len(recent_run_ids) < len(all_run_ids)

        conn.close()
