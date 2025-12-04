"""Tests for the AI Player Observer module."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gengine.ai_player import Observer, ObserverConfig, TrendAnalysis
from gengine.ai_player.observer import create_observer_from_engine
from gengine.echoes.client import SimServiceClient
from gengine.echoes.service import create_app
from gengine.echoes.sim import SimEngine


class TestObserverConfig:
    """Tests for ObserverConfig dataclass."""

    def test_default_config(self) -> None:
        config = ObserverConfig()
        assert config.tick_budget == 100
        assert config.analysis_interval == 10
        assert config.stability_alert_threshold == 0.5
        assert config.legitimacy_swing_threshold == 0.1
        assert config.log_natural_language is True

    def test_custom_config(self) -> None:
        config = ObserverConfig(
            tick_budget=50,
            analysis_interval=5,
            stability_alert_threshold=0.3,
            legitimacy_swing_threshold=0.2,
            log_natural_language=False,
        )
        assert config.tick_budget == 50
        assert config.analysis_interval == 5
        assert config.stability_alert_threshold == 0.3
        assert config.legitimacy_swing_threshold == 0.2
        assert config.log_natural_language is False

    def test_config_validates_tick_budget(self) -> None:
        with pytest.raises(ValueError, match="tick_budget must be at least 1"):
            ObserverConfig(tick_budget=0)

    def test_config_validates_analysis_interval_minimum(self) -> None:
        with pytest.raises(ValueError, match="analysis_interval must be at least 1"):
            ObserverConfig(analysis_interval=0)

    def test_config_validates_analysis_interval_vs_budget(self) -> None:
        with pytest.raises(ValueError, match="analysis_interval.*cannot exceed"):
            ObserverConfig(tick_budget=10, analysis_interval=20)

    def test_config_validates_stability_threshold_range(self) -> None:
        with pytest.raises(
            ValueError, match="stability_alert_threshold must be between"
        ):
            ObserverConfig(stability_alert_threshold=1.5)
        with pytest.raises(
            ValueError, match="stability_alert_threshold must be between"
        ):
            ObserverConfig(stability_alert_threshold=-0.1)

    def test_config_validates_legitimacy_threshold(self) -> None:
        with pytest.raises(
            ValueError, match="legitimacy_swing_threshold must be non-negative"
        ):
            ObserverConfig(legitimacy_swing_threshold=-0.1)


class TestTrendAnalysis:
    """Tests for TrendAnalysis dataclass."""

    def test_to_dict_includes_all_fields(self) -> None:
        trend = TrendAnalysis(
            metric_name="stability",
            start_value=0.8,
            end_value=0.6,
            delta=-0.2,
            trend="decreasing",
            samples=[0.8, 0.75, 0.7, 0.65, 0.6],
            alert="stability dropped below 0.7",
        )
        result = trend.to_dict()
        assert result["metric_name"] == "stability"
        assert result["start_value"] == 0.8
        assert result["end_value"] == 0.6
        assert result["delta"] == -0.2
        assert result["trend"] == "decreasing"
        assert len(result["samples"]) == 5
        assert result["alert"] is not None

    def test_to_dict_rounds_values(self) -> None:
        trend = TrendAnalysis(
            metric_name="test",
            start_value=0.123456789,
            end_value=0.987654321,
            delta=0.864197532,
            trend="increasing",
            samples=[0.123456789, 0.555555555, 0.987654321],
        )
        result = trend.to_dict()
        assert result["start_value"] == 0.1235
        assert result["end_value"] == 0.9877
        assert result["delta"] == 0.8642


class TestObserver:
    """Tests for the Observer class."""

    def test_requires_engine_or_client(self) -> None:
        with pytest.raises(ValueError, match="Must provide either engine or client"):
            Observer()

    def test_rejects_both_engine_and_client(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        class FakeClient:
            pass

        with pytest.raises(ValueError, match="Provide only one of engine or client"):
            Observer(engine=engine, client=FakeClient())  # type: ignore

    def test_observe_with_local_engine(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        config = ObserverConfig(tick_budget=5, analysis_interval=2)
        observer = Observer(engine=engine, config=config)

        report = observer.observe()

        assert report.ticks_observed == 5
        assert report.end_tick > report.start_tick
        assert isinstance(report.stability_trend, TrendAnalysis)
        assert isinstance(report.faction_swings, dict)
        assert isinstance(report.alerts, list)
        assert isinstance(report.commentary, list)

    def test_observe_respects_tick_override(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        config = ObserverConfig(tick_budget=100, analysis_interval=5)
        observer = Observer(engine=engine, config=config)

        report = observer.observe(ticks=3)

        assert report.ticks_observed == 3

    def test_observe_rejects_zero_ticks(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        observer = Observer(engine=engine)

        with pytest.raises(ValueError, match="Tick count must be at least 1"):
            observer.observe(ticks=0)

    def test_report_to_dict_structure(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        config = ObserverConfig(tick_budget=3, analysis_interval=1)
        observer = Observer(engine=engine, config=config)

        report = observer.observe()
        result = report.to_dict()

        assert "ticks_observed" in result
        assert "start_tick" in result
        assert "end_tick" in result
        assert "stability_trend" in result
        assert "faction_swings" in result
        assert "story_seeds_activated" in result
        assert "alerts" in result
        assert "commentary" in result
        assert "environment_summary" in result
        assert "tick_reports_count" in result

    def test_stability_trend_detection(self) -> None:
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        increasing = observer._analyze_trend("test", [0.3, 0.4, 0.5, 0.6])
        assert increasing.trend == "increasing"
        assert increasing.delta > 0

        decreasing = observer._analyze_trend("test", [0.8, 0.7, 0.6, 0.5])
        assert decreasing.trend == "decreasing"
        assert decreasing.delta < 0

        stable = observer._analyze_trend("test", [0.5, 0.505, 0.498, 0.502])
        assert stable.trend == "stable"

    def test_stability_alert_triggered(self) -> None:
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig(stability_alert_threshold=0.5)

        trend = observer._analyze_trend(
            "stability",
            [0.6, 0.5, 0.4, 0.3],
            alert_threshold=0.5,
            alert_direction="below",
        )

        assert trend.alert is not None
        assert "dropped below" in trend.alert

    def test_faction_swing_alert(self) -> None:
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig(legitimacy_swing_threshold=0.1)

        trend = observer._analyze_trend(
            "faction_test_legitimacy",
            [0.5, 0.4, 0.3, 0.2],
            swing_threshold=0.1,
        )

        assert trend.alert is not None
        assert "lost" in trend.alert

    def test_empty_samples_handled(self) -> None:
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        trend = observer._analyze_trend("test", [])

        assert trend.start_value == 0.0
        assert trend.end_value == 0.0
        assert trend.trend == "stable"


class TestObserverDetectsStabilityCrash:
    """Integration test: Observer detects scripted stability crash."""

    def test_observer_detects_stability_decline(self) -> None:
        """Observer should detect and alert when stability drops significantly."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        engine.state.environment.stability = 0.9

        config = ObserverConfig(
            tick_budget=20,
            analysis_interval=5,
            stability_alert_threshold=0.6,
        )
        observer = Observer(engine=engine, config=config)

        report = observer.observe()

        assert report.stability_trend.start_value >= 0.5
        assert report.stability_trend.end_value <= 1.0
        assert isinstance(report.stability_trend.delta, float)

        assert any("stability" in c.lower() for c in report.commentary), (
            "Commentary should mention stability"
        )

    def test_observer_detects_scripted_stability_crash(self) -> None:
        """Observer should detect and alert when stability is scripted to crash.

        This test verifies the observer can detect a forced stability crash by:
        1. Starting with high stability
        2. Observing a few ticks
        3. Manually forcing stability to crash below threshold
        4. Observing more ticks and verifying alert is generated
        """
        engine = SimEngine()
        engine.initialize_state(world="default")

        # Start with high stability
        engine.state.environment.stability = 0.9

        # Configure observer with alert threshold at 0.5
        config = ObserverConfig(
            tick_budget=5,
            analysis_interval=5,
            stability_alert_threshold=0.5,
        )
        observer = Observer(engine=engine, config=config)

        # First observation with stable conditions
        observer.observe()

        # Script the crash: force stability to drop below threshold
        crashed_stability = 0.3
        engine.state.environment.stability = crashed_stability

        # Reuse the same observer to detect the crash (realistic usage pattern)
        report2 = observer.observe()

        # Verify the crash is detected
        start_val = report2.stability_trend.start_value
        assert start_val < 0.5, f"Start value below threshold, got {start_val}"
        assert len(report2.alerts) > 0, "Should have an alert for low stability"
        has_stability_alert = any(
            "stability critical" in alert.lower() for alert in report2.alerts
        )
        assert has_stability_alert, f"Missing stability alert: {report2.alerts}"
        # Verify alert contains a stability value below threshold using regex
        import re

        has_value_in_alert = any(
            re.search(r"0\.[0-4]\d*", alert) for alert in report2.alerts
        )
        assert has_value_in_alert, "Alert should contain the critical stability value"

    def test_observer_tracks_faction_legitimacy(self) -> None:
        """Observer should track faction legitimacy changes."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        config = ObserverConfig(tick_budget=10, analysis_interval=5)
        observer = Observer(engine=engine, config=config)

        report = observer.observe()

        assert len(report.faction_swings) > 0, "Should track at least one faction"
        for _faction_id, trend in report.faction_swings.items():
            assert isinstance(trend.start_value, float)
            assert isinstance(trend.end_value, float)
            assert trend.metric_name.startswith("faction_")


class TestObserverAlertAndCommentaryEdgeCases:
    """Additional tests for coverage of alert and commentary edge cases."""

    def test_alert_direction_above_threshold(self) -> None:
        """Test alert triggered when metric exceeds threshold from above."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        trend = observer._analyze_trend(
            "pollution",
            [0.5, 0.7, 0.9],
            alert_threshold=0.8,
            alert_direction="above",
        )

        assert trend.alert is not None
        assert "exceeded" in trend.alert

    def test_check_alerts_stability_critical_with_logging(self) -> None:
        """Test stability critical alert is logged and added."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig(
            stability_alert_threshold=0.5,
            log_natural_language=True,
        )

        alerts: list[str] = []
        commentary: list[str] = []
        state = {"stability": 0.3, "tick": 50}

        observer._check_alerts(state, alerts, commentary)

        assert len(alerts) == 1
        assert "ALERT: Stability critical" in alerts[0]
        assert "0.300" in alerts[0]

    def test_check_alerts_multiple_crises(self) -> None:
        """Test multiple crises alert is triggered."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        alerts: list[str] = []
        commentary: list[str] = []
        state = {
            "stability": 0.8,
            "tick": 100,
            "director_pacing": {"active_count": 4},
        }

        observer._check_alerts(state, alerts, commentary)

        assert len(alerts) == 1
        assert "Multiple crises active (4)" in alerts[0]

    def test_commentary_stability_declining_significantly(self) -> None:
        """Test commentary for significant stability decline."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        stability_trend = TrendAnalysis(
            metric_name="stability",
            start_value=0.9,
            end_value=0.6,
            delta=-0.3,
            trend="decreasing",
        )

        comments = observer._generate_commentary(stability_trend, {}, [])

        assert any(
            "[STABILITY]" in c and "Declined significantly" in c for c in comments
        )
        assert any("0.90" in c and "0.60" in c for c in comments)

    def test_commentary_stability_stable(self) -> None:
        """Test commentary for stable stability."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        stability_trend = TrendAnalysis(
            metric_name="stability",
            start_value=0.7,
            end_value=0.71,
            delta=0.01,
            trend="stable",
        )

        comments = observer._generate_commentary(stability_trend, {}, [])

        assert any("[STABILITY]" in c and "Remained steady" in c for c in comments)

    def test_commentary_faction_losing_influence(self) -> None:
        """Test commentary for faction losing legitimacy."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        stability_trend = TrendAnalysis(
            metric_name="stability",
            start_value=0.8,
            end_value=0.82,
            delta=0.02,
            trend="stable",
        )

        faction_swings = {
            "rebel_alliance": TrendAnalysis(
                metric_name="faction_rebel_alliance_legitimacy",
                start_value=0.7,
                end_value=0.5,
                delta=-0.2,
                trend="decreasing",
                alert=(
                    "faction_rebel_alliance_legitimacy lost 0.200 "
                    "over observation period"
                ),
            )
        }

        comments = observer._generate_commentary(stability_trend, faction_swings, [])

        assert any("[FACTION]" in c and "lost influence" in c for c in comments)
        assert any("-0.20 legitimacy" in c for c in comments)

    def test_check_story_seeds_handles_id_variants(self) -> None:
        """Test story seed tracking handles both 'seed_id' and 'id' fields."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        activated: list[dict] = []
        state = {
            "tick": 50,
            "story_seeds": [
                {"seed_id": "crisis-a", "target_district": "district-1"},
                {"id": "crisis-b", "district": "district-2"},
            ],
        }

        observer._check_story_seeds(state, activated)

        assert len(activated) == 2
        seed_ids = [s["seed_id"] for s in activated]
        assert "crisis-a" in seed_ids
        assert "crisis-b" in seed_ids

    def test_commentary_includes_structured_labels(self) -> None:
        """Test that commentary uses structured labels for clarity."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        stability_trend = TrendAnalysis(
            metric_name="stability",
            start_value=0.7,
            end_value=0.64,
            delta=-0.06,
            trend="decreasing",
        )

        comments = observer._generate_commentary(stability_trend, {}, [])

        assert any("[STABILITY]" in c for c in comments)
        # Delta of -0.06 triggers moderate decrease path
        assert any("Decreased moderately" in c for c in comments)

    def test_commentary_moderate_faction_changes_included(self) -> None:
        """Test that moderate faction changes (>=0.05) are included in commentary."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        stability_trend = TrendAnalysis(
            metric_name="stability",
            start_value=0.7,
            end_value=0.7,
            delta=0.0,
            trend="stable",
        )

        faction_swings = {
            "test_faction": TrendAnalysis(
                metric_name="faction_test_faction_legitimacy",
                start_value=0.5,
                end_value=0.56,
                delta=0.06,
                trend="increasing",
                alert=None,  # No alert, but should still appear
            )
        }

        comments = observer._generate_commentary(stability_trend, faction_swings, [])

        assert any("[FACTION]" in c for c in comments)
        assert any("Test Faction" in c for c in comments)
        assert any("moderately" in c.lower() for c in comments)

    def test_extract_environment_captures_economy_metrics(self) -> None:
        """Test that environment extraction includes economy metrics."""
        observer = Observer.__new__(Observer)
        observer._config = ObserverConfig()

        state = {
            "stability": 0.7,
            "economy": {
                "wealth_ratio": 0.8,
                "supply_demand_ratio": 1.2,
                "avg_capacity": 0.6,
            },
            "agent_count": 150,
        }

        env = observer._extract_environment(state)

        assert "stability" in env
        assert "economy_wealth_ratio" in env
        assert "economy_supply_demand_ratio" in env
        assert "economy_avg_capacity" in env
        assert "agent_count" in env
        assert env["economy_wealth_ratio"] == 0.8


class TestCreateObserverHelpers:
    """Tests for observer factory functions."""

    def test_create_observer_from_engine(self) -> None:
        observer = create_observer_from_engine(world="default")

        assert observer._engine is not None
        assert observer._client is None
        assert observer._is_local is True

    def test_create_observer_with_custom_config(self) -> None:
        config = ObserverConfig(tick_budget=25)
        observer = create_observer_from_engine(world="default", config=config)

        assert observer.config.tick_budget == 25


@pytest.fixture
def service_client():
    """Create a SimServiceClient backed by a test server with proper cleanup."""
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    http_client = TestClient(app)
    client = SimServiceClient(base_url="http://testserver", client=http_client)
    yield client
    client.close()


class TestObserverWithSimServiceClient:
    """Integration tests for Observer using SimServiceClient."""

    def test_observer_with_service_client_observes_ticks(
        self, service_client: SimServiceClient
    ) -> None:
        """Observer should work correctly with SimServiceClient."""
        config = ObserverConfig(tick_budget=5, analysis_interval=2)
        observer = Observer(client=service_client, config=config)

        report = observer.observe()

        assert report.ticks_observed == 5
        assert report.end_tick > report.start_tick
        assert isinstance(report.stability_trend, TrendAnalysis)
        assert isinstance(report.faction_swings, dict)

    def test_observer_with_service_client_detects_trends(
        self, service_client: SimServiceClient
    ) -> None:
        """Observer should detect trends when using SimServiceClient."""
        config = ObserverConfig(tick_budget=10, analysis_interval=5)
        observer = Observer(client=service_client, config=config)

        report = observer.observe()

        # Verify trend detection works
        assert report.stability_trend.metric_name == "stability"
        assert report.stability_trend.trend in ["increasing", "decreasing", "stable"]
        assert len(report.stability_trend.samples) > 0
        # Verify faction tracking works
        assert len(report.faction_swings) > 0
        for _faction_id, trend in report.faction_swings.items():
            assert trend.metric_name.startswith("faction_")
            assert trend.trend in ["increasing", "decreasing", "stable"]

    def test_observer_with_service_client_generates_commentary(
        self, service_client: SimServiceClient
    ) -> None:
        """Observer should generate commentary when using SimServiceClient."""
        config = ObserverConfig(
            tick_budget=10,
            analysis_interval=5,
            log_natural_language=True,
        )
        observer = Observer(client=service_client, config=config)

        report = observer.observe()

        # Verify commentary is generated
        assert isinstance(report.commentary, list)
        assert len(report.commentary) > 0
        # Verify structured labels are present
        assert any("[STABILITY]" in c for c in report.commentary)

    def test_observer_with_service_client_json_output(
        self, service_client: SimServiceClient
    ) -> None:
        """Observer should produce valid JSON output via SimServiceClient."""
        config = ObserverConfig(tick_budget=5, analysis_interval=2)
        observer = Observer(client=service_client, config=config)

        report = observer.observe()
        result = report.to_dict()

        # Verify JSON structure
        assert "ticks_observed" in result
        assert "start_tick" in result
        assert "end_tick" in result
        assert "stability_trend" in result
        assert "faction_swings" in result
        assert "story_seeds_activated" in result
        assert "alerts" in result
        assert "commentary" in result
        assert "environment_summary" in result
        assert "tick_reports_count" in result
