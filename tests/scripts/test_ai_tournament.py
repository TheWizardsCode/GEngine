"""Tests for AI tournament infrastructure."""

from __future__ import annotations

import json
import sys
import tempfile
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "run_ai_tournament.py"
)


def _load_tournament_module():
    spec = util.spec_from_file_location("tournament_driver", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("tournament_driver", module)
    spec.loader.exec_module(module)
    return module


_driver = _load_tournament_module()
GameResult = _driver.GameResult
TournamentConfig = _driver.TournamentConfig
TournamentReport = _driver.TournamentReport
run_single_game = _driver.run_single_game
run_tournament = _driver.run_tournament
main = _driver.main


class TestGameResult:
    """Tests for the GameResult dataclass."""

    def test_game_result_default_values(self) -> None:
        result = GameResult(
            game_id=1,
            strategy="balanced",
            seed=42,
            ticks_run=100,
            final_stability=0.75,
            actions_taken=10,
        )
        assert result.story_seeds_activated == []
        assert result.action_counts == {}
        assert result.duration_seconds == 0.0
        assert result.error is None

    def test_game_result_to_dict(self) -> None:
        result = GameResult(
            game_id=1,
            strategy="balanced",
            seed=42,
            ticks_run=100,
            final_stability=0.7567,
            actions_taken=10,
            story_seeds_activated=["seed-1", "seed-2"],
            action_counts={"INSPECT": 5, "NEGOTIATE": 5},
            duration_seconds=1.234,
        )

        data = result.to_dict()

        assert data["game_id"] == 1
        assert data["strategy"] == "balanced"
        assert data["seed"] == 42
        assert data["ticks_run"] == 100
        assert data["final_stability"] == 0.7567
        assert data["actions_taken"] == 10
        assert data["story_seeds_activated"] == ["seed-1", "seed-2"]
        assert data["action_counts"] == {"INSPECT": 5, "NEGOTIATE": 5}
        assert data["duration_seconds"] == 1.234
        assert data["error"] is None

    def test_game_result_with_error(self) -> None:
        result = GameResult(
            game_id=1,
            strategy="balanced",
            seed=42,
            ticks_run=0,
            final_stability=0.0,
            actions_taken=0,
            error="Connection failed",
        )

        data = result.to_dict()
        assert data["error"] == "Connection failed"


class TestTournamentConfig:
    """Tests for the TournamentConfig dataclass."""

    def test_default_config(self) -> None:
        config = TournamentConfig()
        assert config.num_games == 100
        assert config.ticks_per_game == 100
        assert config.strategies == ["balanced", "aggressive", "diplomatic"]
        assert config.base_seed == 42
        assert config.world == "default"
        assert config.max_workers is None
        assert config.stability_win_threshold == 0.5

    def test_custom_config(self) -> None:
        config = TournamentConfig(
            num_games=50,
            ticks_per_game=200,
            strategies=["balanced", "hybrid"],
            base_seed=123,
            world="test",
            max_workers=2,
            stability_win_threshold=0.6,
        )
        assert config.num_games == 50
        assert config.ticks_per_game == 200
        assert config.strategies == ["balanced", "hybrid"]
        assert config.base_seed == 123
        assert config.world == "test"
        assert config.max_workers == 2
        assert config.stability_win_threshold == 0.6


class TestTournamentReport:
    """Tests for the TournamentReport dataclass."""

    def test_report_to_dict(self) -> None:
        game1 = GameResult(
            game_id=1,
            strategy="balanced",
            seed=42,
            ticks_run=100,
            final_stability=0.8,
            actions_taken=5,
        )
        game2 = GameResult(
            game_id=2,
            strategy="aggressive",
            seed=43,
            ticks_run=100,
            final_stability=0.6,
            actions_taken=10,
        )

        report = TournamentReport(
            config={"num_games": 2, "strategies": ["balanced", "aggressive"]},
            total_games=2,
            completed_games=2,
            failed_games=0,
            games_by_strategy={
                "balanced": [game1],
                "aggressive": [game2],
            },
            strategy_stats={
                "balanced": {"win_rate": 1.0, "avg_stability": 0.8},
                "aggressive": {"win_rate": 0.5, "avg_stability": 0.6},
            },
            all_story_seeds={"seed-1"},
            unused_story_seeds=[],
            total_duration_seconds=5.5,
        )

        data = report.to_dict()

        assert data["total_games"] == 2
        assert data["completed_games"] == 2
        assert data["failed_games"] == 0
        assert "balanced" in data["strategy_stats"]
        assert "aggressive" in data["strategy_stats"]
        assert data["all_story_seeds_seen"] == ["seed-1"]
        assert data["total_duration_seconds"] == 5.5
        assert len(data["games"]["balanced"]) == 1
        assert len(data["games"]["aggressive"]) == 1


class TestRunSingleGame:
    """Tests for the run_single_game function."""

    def test_run_single_game_balanced(self) -> None:
        result = run_single_game(
            game_id=1,
            strategy_name="balanced",
            seed=42,
            ticks=10,
            world="default",
        )

        assert result.game_id == 1
        assert result.strategy == "balanced"
        assert result.seed == 42
        assert result.ticks_run == 10
        assert result.error is None
        assert 0.0 <= result.final_stability <= 1.0
        assert result.duration_seconds > 0

    def test_run_single_game_aggressive(self) -> None:
        result = run_single_game(
            game_id=2,
            strategy_name="aggressive",
            seed=43,
            ticks=10,
            world="default",
        )

        assert result.game_id == 2
        assert result.strategy == "aggressive"
        assert result.error is None

    def test_run_single_game_diplomatic(self) -> None:
        result = run_single_game(
            game_id=3,
            strategy_name="diplomatic",
            seed=44,
            ticks=10,
            world="default",
        )

        assert result.game_id == 3
        assert result.strategy == "diplomatic"
        assert result.error is None

    def test_run_single_game_invalid_world(self) -> None:
        result = run_single_game(
            game_id=1,
            strategy_name="balanced",
            seed=42,
            ticks=10,
            world="nonexistent_world",
        )

        assert result.error is not None
        assert result.ticks_run == 0


class TestRunTournament:
    """Tests for the run_tournament function."""

    def test_run_tournament_small(self) -> None:
        """Run a small tournament to verify basic functionality."""
        config = TournamentConfig(
            num_games=6,
            ticks_per_game=10,
            strategies=["balanced", "aggressive"],
            base_seed=42,
            max_workers=2,
        )

        report = run_tournament(config, verbose=False)

        assert report.total_games == 6
        assert report.completed_games == 6
        assert report.failed_games == 0
        assert "balanced" in report.games_by_strategy
        assert "aggressive" in report.games_by_strategy
        assert len(report.games_by_strategy["balanced"]) == 3
        assert len(report.games_by_strategy["aggressive"]) == 3

    def test_run_tournament_calculates_stats(self) -> None:
        """Verify that tournament calculates strategy statistics."""
        config = TournamentConfig(
            num_games=4,
            ticks_per_game=10,
            strategies=["balanced", "diplomatic"],
            base_seed=42,
            max_workers=1,
        )

        report = run_tournament(config, verbose=False)

        assert "balanced" in report.strategy_stats
        assert "diplomatic" in report.strategy_stats

        for _strategy, stats in report.strategy_stats.items():
            assert "games_played" in stats
            assert "win_rate" in stats
            assert "avg_stability" in stats
            assert "total_actions" in stats
            assert "avg_actions" in stats

    def test_run_tournament_with_single_strategy(self) -> None:
        """Test tournament with only one strategy."""
        config = TournamentConfig(
            num_games=3,
            ticks_per_game=10,
            strategies=["balanced"],
            base_seed=42,
            max_workers=1,
        )

        report = run_tournament(config, verbose=False)

        assert report.total_games == 3
        assert len(report.games_by_strategy["balanced"]) == 3

    def test_run_tournament_collects_story_seeds(self) -> None:
        """Test that tournament collects story seed information."""
        config = TournamentConfig(
            num_games=2,
            ticks_per_game=50,  # More ticks to potentially trigger seeds
            strategies=["balanced"],
            base_seed=42,
            max_workers=1,
        )

        report = run_tournament(config, verbose=False)

        # Story seeds may or may not be activated, just verify the field exists
        assert isinstance(report.all_story_seeds, set)


class TestTournamentDeterminism:
    """Tests for tournament determinism with fixed seeds."""

    def test_same_seed_produces_same_result(self) -> None:
        """Running the same game twice with same seed should produce same result."""
        result1 = run_single_game(
            game_id=1,
            strategy_name="balanced",
            seed=42,
            ticks=20,
            world="default",
        )
        result2 = run_single_game(
            game_id=1,
            strategy_name="balanced",
            seed=42,
            ticks=20,
            world="default",
        )

        assert result1.final_stability == result2.final_stability
        assert result1.actions_taken == result2.actions_taken

    def test_different_seeds_may_differ(self) -> None:
        """Different seeds may produce different outcomes."""
        result1 = run_single_game(
            game_id=1,
            strategy_name="balanced",
            seed=42,
            ticks=20,
            world="default",
        )
        result2 = run_single_game(
            game_id=2,
            strategy_name="balanced",
            seed=12345,
            ticks=20,
            world="default",
        )

        # Results may or may not differ, but both should complete successfully
        assert result1.error is None
        assert result2.error is None


class TestTournamentOutputFile:
    """Tests for tournament JSON output."""

    def test_tournament_writes_json_output(self) -> None:
        """Test that tournament can write results to JSON file."""
        config = TournamentConfig(
            num_games=2,
            ticks_per_game=10,
            strategies=["balanced"],
            max_workers=1,
        )

        report = run_tournament(config, verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            output_path.write_text(json.dumps(report.to_dict(), indent=2))

            # Verify file was written and can be read back
            assert output_path.exists()
            loaded = json.loads(output_path.read_text())
            assert loaded["total_games"] == 2
            assert "balanced" in loaded["games"]


class TestTournamentCLI:
    """Tests for the tournament CLI."""

    def test_cli_basic_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test CLI with minimal arguments."""
        output_path = tmp_path / "results.json"

        exit_code = main([
            "--games", "2",
            "--ticks", "5",
            "--strategies", "balanced",
            "--output", str(output_path),
        ])

        assert exit_code == 0
        assert output_path.exists()

        captured = capsys.readouterr()
        assert "AI TOURNAMENT RESULTS" in captured.out

    def test_cli_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test CLI with JSON output format."""
        exit_code = main([
            "--games", "2",
            "--ticks", "5",
            "--strategies", "balanced",
            "--json",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "total_games" in data
