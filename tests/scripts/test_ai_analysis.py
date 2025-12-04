"""Tests for AI tournament analysis module."""

from __future__ import annotations

import json
import sys
import tempfile
from importlib import util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "analyze_ai_games.py"
)


def _load_analysis_module():
    spec = util.spec_from_file_location("analysis_driver", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("analysis_driver", module)
    spec.loader.exec_module(module)
    return module


_driver = _load_analysis_module()
AnalysisReport = _driver.AnalysisReport
BalanceAnomaly = _driver.BalanceAnomaly
analyze_actions = _driver.analyze_actions
analyze_story_seeds = _driver.analyze_story_seeds
analyze_tournament = _driver.analyze_tournament
analyze_win_rates = _driver.analyze_win_rates
detect_anomalies = _driver.detect_anomalies
generate_recommendations = _driver.generate_recommendations
load_tournament_results = _driver.load_tournament_results
main = _driver.main


class TestBalanceAnomaly:
    """Tests for the BalanceAnomaly dataclass."""

    def test_anomaly_to_dict(self) -> None:
        anomaly = BalanceAnomaly(
            anomaly_type="dominant_strategy",
            severity="high",
            description="Strategy 'aggressive' dominates",
            data={"strategy": "aggressive", "win_rate": 0.95},
        )

        result = anomaly.to_dict()

        assert result["type"] == "dominant_strategy"
        assert result["severity"] == "high"
        assert result["description"] == "Strategy 'aggressive' dominates"
        assert result["data"]["strategy"] == "aggressive"


class TestAnalysisReport:
    """Tests for the AnalysisReport dataclass."""

    def test_report_to_dict(self) -> None:
        anomaly = BalanceAnomaly(
            anomaly_type="test", severity="low", description="Test anomaly"
        )
        report = AnalysisReport(
            tournament_config={"num_games": 100},
            strategy_comparison={"balanced": {"win_rate": 0.5}},
            win_rate_analysis={"is_balanced": True},
            action_analysis={"most_used_action": "INSPECT"},
            story_seed_analysis={"seeds_seen": ["seed-1"]},
            anomalies=[anomaly],
            recommendations=["Test recommendation"],
        )

        result = report.to_dict()

        assert result["tournament_config"] == {"num_games": 100}
        assert "balanced" in result["strategy_comparison"]
        assert len(result["anomalies"]) == 1
        assert result["recommendations"] == ["Test recommendation"]


class TestAnalyzeWinRates:
    """Tests for the analyze_win_rates function."""

    def test_analyze_balanced_strategies(self) -> None:
        strategy_stats = {
            "balanced": {"win_rate": 0.50},
            "aggressive": {"win_rate": 0.55},
            "diplomatic": {"win_rate": 0.52},
        }

        result = analyze_win_rates(strategy_stats)

        assert result["best_strategy"] == "aggressive"
        assert result["best_win_rate"] == 0.55
        assert result["worst_strategy"] == "balanced"
        assert result["worst_win_rate"] == 0.50
        assert result["win_rate_delta"] == 0.05
        assert result["is_balanced"] is True

    def test_analyze_imbalanced_strategies(self) -> None:
        strategy_stats = {
            "balanced": {"win_rate": 0.30},
            "aggressive": {"win_rate": 0.80},
        }

        result = analyze_win_rates(strategy_stats)

        assert result["win_rate_delta"] == 0.50
        assert result["is_balanced"] is False

    def test_analyze_empty_stats(self) -> None:
        result = analyze_win_rates({})
        assert "error" in result

    def test_analyze_single_strategy(self) -> None:
        strategy_stats = {"balanced": {"win_rate": 0.75}}

        result = analyze_win_rates(strategy_stats)

        assert result["best_strategy"] == "balanced"
        assert result["worst_strategy"] == "balanced"
        assert result["win_rate_delta"] == 0.0
        assert result["is_balanced"] is True


class TestAnalyzeActions:
    """Tests for the analyze_actions function."""

    def test_analyze_action_distribution(self) -> None:
        strategy_stats = {
            "balanced": {"action_breakdown": {"INSPECT": 20, "NEGOTIATE": 15}},
            "aggressive": {"action_breakdown": {"INSPECT": 10, "DEPLOY_RESOURCE": 25}},
        }

        result = analyze_actions(strategy_stats)

        assert result["total_actions"]["INSPECT"] == 30
        assert result["total_actions"]["NEGOTIATE"] == 15
        assert result["total_actions"]["DEPLOY_RESOURCE"] == 25
        assert result["most_used_action"] == "INSPECT"
        assert result["most_used_count"] == 30
        assert result["least_used_action"] == "NEGOTIATE"
        assert result["least_used_count"] == 15

    def test_analyze_dominant_action(self) -> None:
        strategy_stats = {
            "balanced": {"action_breakdown": {"INSPECT": 100}},
            "aggressive": {"action_breakdown": {"INSPECT": 100, "NEGOTIATE": 10}},
        }

        result = analyze_actions(strategy_stats)

        # INSPECT is over 50% of total actions
        assert result["dominant_action"] == "INSPECT"

    def test_analyze_no_dominant_action(self) -> None:
        strategy_stats = {
            "balanced": {"action_breakdown": {"INSPECT": 30, "NEGOTIATE": 30}},
        }

        result = analyze_actions(strategy_stats)

        assert result["dominant_action"] is None

    def test_analyze_empty_actions(self) -> None:
        result = analyze_actions({})
        assert "error" in result


class TestAnalyzeStorySeeds:
    """Tests for the analyze_story_seeds function."""

    def test_analyze_seed_coverage(self) -> None:
        results = {
            "all_story_seeds_seen": ["seed-1", "seed-2"],
            "games": {
                "balanced": [
                    {"story_seeds_activated": ["seed-1"], "error": None},
                    {"story_seeds_activated": ["seed-1", "seed-2"], "error": None},
                ]
            },
        }

        analysis = analyze_story_seeds(results)

        assert "seed-1" in analysis["seeds_seen"]
        assert "seed-2" in analysis["seeds_seen"]
        assert analysis["seed_counts"]["seed-1"] == 2
        assert analysis["seed_counts"]["seed-2"] == 1
        assert analysis["total_games_analyzed"] == 2

    def test_analyze_with_authored_seeds(self) -> None:
        results = {
            "all_story_seeds_seen": ["seed-1"],
            "games": {
                "balanced": [
                    {"story_seeds_activated": ["seed-1"], "error": None},
                ]
            },
        }
        authored = ["seed-1", "seed-2", "seed-3"]

        analysis = analyze_story_seeds(results, authored)

        assert analysis["unused_seeds"] == ["seed-2", "seed-3"]
        assert analysis["coverage_rate"] == pytest.approx(1 / 3)

    def test_analyze_full_coverage(self) -> None:
        results = {
            "all_story_seeds_seen": ["seed-1", "seed-2"],
            "games": {},
        }
        authored = ["seed-1", "seed-2"]

        analysis = analyze_story_seeds(results, authored)

        assert analysis["unused_seeds"] == []
        assert analysis["coverage_rate"] == 1.0


class TestDetectAnomalies:
    """Tests for the detect_anomalies function."""

    def test_detect_dominant_strategy(self) -> None:
        win_rate = {
            "win_rate_delta": 0.25,
            "best_strategy": "aggressive",
            "best_win_rate": 0.85,
            "worst_strategy": "diplomatic",
            "worst_win_rate": 0.60,
        }

        anomalies = detect_anomalies(win_rate, {}, {}, {})

        assert len(anomalies) >= 1
        dominant = [a for a in anomalies if a.anomaly_type == "dominant_strategy"]
        assert len(dominant) == 1
        assert dominant[0].severity == "high"

    def test_detect_strategy_imbalance(self) -> None:
        win_rate = {
            "win_rate_delta": 0.18,  # Between 0.15 and 0.2
            "best_strategy": "aggressive",
            "best_win_rate": 0.75,
            "worst_strategy": "diplomatic",
            "worst_win_rate": 0.57,
        }

        anomalies = detect_anomalies(win_rate, {}, {}, {})

        imbalance = [a for a in anomalies if a.anomaly_type == "strategy_imbalance"]
        assert len(imbalance) == 1
        assert imbalance[0].severity == "medium"

    def test_detect_dominant_action(self) -> None:
        action_analysis = {
            "dominant_action": "INSPECT",
            "action_percentages": {"INSPECT": 0.75},
        }

        anomalies = detect_anomalies({}, action_analysis, {}, {})

        dominant = [a for a in anomalies if a.anomaly_type == "dominant_action"]
        assert len(dominant) == 1

    def test_detect_unused_story_seeds(self) -> None:
        story_seed_analysis = {
            "unused_seeds": ["seed-1", "seed-2", "seed-3"],
            "authored_seeds": ["seed-1", "seed-2", "seed-3", "seed-4"],
        }

        anomalies = detect_anomalies({}, {}, story_seed_analysis, {})

        unused = [a for a in anomalies if a.anomaly_type == "unused_story_seeds"]
        assert len(unused) == 1
        assert unused[0].severity == "high"

    def test_detect_low_activity_strategy(self) -> None:
        strategy_stats = {
            "balanced": {"avg_actions": 0.5},
        }

        anomalies = detect_anomalies({}, {}, {}, strategy_stats)

        low_activity = [
            a for a in anomalies if a.anomaly_type == "low_activity_strategy"
        ]
        assert len(low_activity) == 1

    def test_no_anomalies_when_balanced(self) -> None:
        win_rate = {
            "win_rate_delta": 0.05,
            "is_balanced": True,
        }
        action_analysis = {"dominant_action": None}
        story_seed_analysis = {"unused_seeds": [], "coverage_rate": 1.0}
        strategy_stats = {"balanced": {"avg_actions": 5.0}}

        anomalies = detect_anomalies(
            win_rate, action_analysis, story_seed_analysis, strategy_stats
        )

        assert len(anomalies) == 0


class TestGenerateRecommendations:
    """Tests for the generate_recommendations function."""

    def test_recommends_for_imbalanced(self) -> None:
        anomalies = [
            BalanceAnomaly(
                "dominant_strategy", "high", "Strategy imbalanced"
            )
        ]
        win_rate = {
            "is_balanced": False,
            "best_strategy": "aggressive",
            "worst_strategy": "diplomatic",
        }

        recs = generate_recommendations(anomalies, win_rate, {}, {})

        assert len(recs) >= 1
        assert any("diplomatic" in r.lower() or "aggressive" in r.lower() for r in recs)

    def test_recommends_for_dominant_action(self) -> None:
        action_analysis = {"dominant_action": "INSPECT"}

        recs = generate_recommendations([], {}, action_analysis, {})

        assert any("INSPECT" in r for r in recs)

    def test_recommends_for_unused_seeds(self) -> None:
        story_seed_analysis = {
            "unused_seeds": ["seed-1", "seed-2"],
            "coverage_rate": 0.5,
        }

        recs = generate_recommendations([], {}, {}, story_seed_analysis)

        assert any("seed" in r.lower() for r in recs)

    def test_default_recommendation_when_balanced(self) -> None:
        recs = generate_recommendations(
            [], {"is_balanced": True}, {"dominant_action": None}, {}
        )

        assert len(recs) >= 1
        assert any("no significant" in r.lower() for r in recs)


class TestAnalyzeTournament:
    """Tests for the full analyze_tournament function."""

    def test_full_analysis(self) -> None:
        results = {
            "config": {"num_games": 10, "strategies": ["balanced", "aggressive"]},
            "strategy_stats": {
                "balanced": {
                    "win_rate": 0.6,
                    "avg_stability": 0.7,
                    "avg_actions": 5.0,
                    "games_completed": 5,
                    "action_breakdown": {"INSPECT": 20},
                },
                "aggressive": {
                    "win_rate": 0.5,
                    "avg_stability": 0.65,
                    "avg_actions": 8.0,
                    "games_completed": 5,
                    "action_breakdown": {"INSPECT": 10, "DEPLOY_RESOURCE": 30},
                },
            },
            "all_story_seeds_seen": ["seed-1"],
            "games": {
                "balanced": [
                    {"story_seeds_activated": ["seed-1"], "error": None},
                ],
                "aggressive": [
                    {"story_seeds_activated": [], "error": None},
                ],
            },
        }

        report = analyze_tournament(results)

        assert report.tournament_config["num_games"] == 10
        assert "balanced" in report.strategy_comparison
        assert "aggressive" in report.strategy_comparison
        assert report.win_rate_analysis["is_balanced"] is True
        assert len(report.recommendations) >= 1

    def test_analysis_with_authored_seeds(self) -> None:
        results = {
            "config": {},
            "strategy_stats": {
                "balanced": {
                    "win_rate": 0.5,
                    "avg_stability": 0.5,
                    "avg_actions": 5.0,
                    "games_completed": 1,
                    "action_breakdown": {},
                },
            },
            "all_story_seeds_seen": ["seed-1"],
            "games": {},
        }
        authored = ["seed-1", "seed-2", "seed-3"]

        report = analyze_tournament(results, authored)

        assert report.story_seed_analysis["unused_seeds"] == ["seed-2", "seed-3"]


class TestLoadTournamentResults:
    """Tests for loading tournament results from files."""

    def test_load_valid_json(self) -> None:
        results = {
            "config": {"num_games": 10},
            "total_games": 10,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.json"
            path.write_text(json.dumps(results))

            loaded = load_tournament_results(path)

            assert loaded["config"]["num_games"] == 10
            assert loaded["total_games"] == 10


class TestAnalysisCLI:
    """Tests for the analysis CLI."""

    def test_cli_basic_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test CLI with minimal arguments."""
        results = {
            "config": {"num_games": 10},
            "strategy_stats": {
                "balanced": {
                    "win_rate": 0.5,
                    "avg_stability": 0.5,
                    "avg_actions": 5.0,
                    "games_completed": 10,
                    "action_breakdown": {"INSPECT": 50},
                },
            },
            "all_story_seeds_seen": [],
            "games": {},
        }
        input_path = tmp_path / "results.json"
        input_path.write_text(json.dumps(results))

        exit_code = main(["--input", str(input_path)])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "AI TOURNAMENT ANALYSIS REPORT" in captured.out

    def test_cli_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test CLI with JSON output format."""
        results = {
            "config": {"num_games": 10},
            "strategy_stats": {
                "balanced": {
                    "win_rate": 0.5,
                    "avg_stability": 0.5,
                    "avg_actions": 5.0,
                    "games_completed": 10,
                    "action_breakdown": {},
                },
            },
            "all_story_seeds_seen": [],
            "games": {},
        }
        input_path = tmp_path / "results.json"
        input_path.write_text(json.dumps(results))

        exit_code = main(["--input", str(input_path), "--json"])

        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "tournament_config" in data
        assert "anomalies" in data

    def test_cli_missing_input_file(self, capsys: pytest.CaptureFixture) -> None:
        """Test CLI with missing input file."""
        exit_code = main(["--input", "/nonexistent/path/results.json"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
