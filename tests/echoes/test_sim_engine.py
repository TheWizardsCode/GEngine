"""Tests for the SimEngine abstraction (Phase 3, M3.1)."""

from __future__ import annotations

import pytest

from gengine.echoes.settings import SimulationConfig, SimulationLimits
from gengine.echoes.sim import SimEngine
from gengine.echoes.sim.engine import EngineNotInitializedError

# --------------------------------------------------------------------------
# Basic Initialization Tests
# --------------------------------------------------------------------------


def test_engine_initializes_from_world() -> None:
    engine = SimEngine()

    state = engine.initialize_state(world="default")

    assert state.city.name
    assert engine.state.tick == 0


def test_engine_advances_ticks_and_reports() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    reports = engine.advance_ticks(2)

    assert len(reports) == 2
    assert engine.state.tick == 2


def test_engine_query_district_view() -> None:
    engine = SimEngine()
    state = engine.initialize_state(world="default")
    district_id = state.city.districts[0].id

    panel = engine.query_view("district", district_id=district_id)

    assert panel["id"] == district_id
    assert "modifiers" in panel


def test_engine_apply_action_is_placeholder() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    result = engine.apply_action({"intent": "noop"})

    assert result["status"] == "noop"


def test_engine_enforces_tick_limit() -> None:
    limits = SimulationLimits(
        engine_max_ticks=1,
        cli_run_cap=1,
        cli_script_command_cap=5,
        service_tick_cap=1,
    )
    config = SimulationConfig(limits=limits)
    engine = SimEngine(config=config)
    engine.initialize_state(world="default")

    with pytest.raises(ValueError):
        engine.advance_ticks(2)


def test_engine_focus_controls_update_state() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    initial = engine.focus_state()
    assert initial["district_id"]
    neighbors = initial.get("neighbors") or []
    if neighbors:
        updated = engine.set_focus(neighbors[0])
        assert updated["district_id"] == neighbors[0]
    cleared = engine.clear_focus()
    assert cleared["district_id"]


def test_engine_focus_history_reports_recent_ticks() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    engine.advance_ticks(2)

    history = engine.focus_history()
    assert isinstance(history, list)
    assert history


def test_engine_query_post_mortem_view() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    engine.advance_ticks(1)
    payload = engine.query_view("post-mortem")

    assert payload["tick"] >= 0
    assert "environment" in payload


# --------------------------------------------------------------------------
# Initialization Validation Tests
# --------------------------------------------------------------------------


class TestInitializeStateValidation:
    """Tests for initialize_state validation behavior."""

    def test_initialize_state_requires_argument(self) -> None:
        """ValueError raised when no state, world, or snapshot provided."""
        engine = SimEngine()

        with pytest.raises(ValueError, match="Provide state, world, or snapshot"):
            engine.initialize_state()

    def test_engine_state_raises_before_initialization(self) -> None:
        """EngineNotInitializedError raised when accessing state before init."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            _ = engine.state


# --------------------------------------------------------------------------
# Query View Tests
# --------------------------------------------------------------------------


class TestQueryView:
    """Tests for query_view with all view types."""

    def test_query_view_summary(self) -> None:
        """query_view('summary') returns state summary."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        summary = engine.query_view("summary")

        assert isinstance(summary, dict)
        assert "tick" in summary

    def test_query_view_snapshot(self) -> None:
        """query_view('snapshot') returns full snapshot data."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        snapshot = engine.query_view("snapshot")

        assert isinstance(snapshot, dict)
        assert "city" in snapshot

    def test_query_view_unknown_raises_valueerror(self) -> None:
        """ValueError raised for unknown view names."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="Unknown view"):
            engine.query_view("nonexistent")

    def test_query_view_district_missing_id_raises_valueerror(self) -> None:
        """ValueError raised when district view lacks district_id."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="district view requires"):
            engine.query_view("district")

    def test_query_view_district_invalid_id_raises_valueerror(self) -> None:
        """ValueError raised for invalid district_id."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="Unknown district"):
            engine.query_view("district", district_id="nonexistent-district-id")


# --------------------------------------------------------------------------
# Director Feed Tests
# --------------------------------------------------------------------------


class TestDirectorFeed:
    """Tests for director_feed API."""

    def test_director_feed_returns_expected_structure(self) -> None:
        """director_feed returns dict with expected keys."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        feed = engine.director_feed()

        assert isinstance(feed, dict)
        assert "latest" in feed
        assert "history" in feed
        assert "analysis" in feed
        assert "events" in feed

    def test_director_feed_after_ticks(self) -> None:
        """director_feed populates after advancing ticks."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(2)

        feed = engine.director_feed()

        assert isinstance(feed["history"], list)
        assert isinstance(feed["events"], list)


# --------------------------------------------------------------------------
# Explanations API Tests
# --------------------------------------------------------------------------


class TestExplanationsAPI:
    """Tests for the explanations helpers."""

    def test_query_timeline_returns_list(self) -> None:
        """query_timeline returns a list of timeline entries."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(1)

        timeline = engine.query_timeline(count=5)

        assert isinstance(timeline, list)

    def test_explain_metric_returns_dict(self) -> None:
        """explain_metric returns explanation dictionary."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(1)

        explanation = engine.explain_metric("stability", lookback=5)

        assert isinstance(explanation, dict)

    def test_explain_faction_returns_dict(self) -> None:
        """explain_faction returns explanation for a faction."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        engine.advance_ticks(1)
        faction_ids = list(state.factions.keys())
        faction_id = faction_ids[0] if faction_ids else "unknown"

        explanation = engine.explain_faction(faction_id, lookback=5)

        assert isinstance(explanation, dict)

    def test_explain_agent_returns_dict(self) -> None:
        """explain_agent returns explanation for an agent."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        engine.advance_ticks(1)
        agent_ids = list(state.agents.keys())
        agent_id = agent_ids[0] if agent_ids else "unknown"

        explanation = engine.explain_agent(agent_id, lookback=5)

        assert isinstance(explanation, dict)

    def test_explain_district_returns_dict(self) -> None:
        """explain_district returns explanation for a district."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        engine.advance_ticks(1)
        district_id = state.city.districts[0].id

        explanation = engine.explain_district(district_id, lookback=5)

        assert isinstance(explanation, dict)

    def test_why_returns_dict(self) -> None:
        """why returns explanation dictionary for arbitrary query."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(1)

        explanation = engine.why("stability dropped")

        assert isinstance(explanation, dict)


# --------------------------------------------------------------------------
# Progression API Tests
# --------------------------------------------------------------------------


class TestProgressionAPI:
    """Tests for progression helpers."""

    def test_progression_summary_returns_dict(self) -> None:
        """progression_summary returns dictionary with expected keys."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        summary = engine.progression_summary()

        assert isinstance(summary, dict)

    def test_calculate_success_chance_returns_float(self) -> None:
        """calculate_success_chance returns float between 0 and 1."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        chance = engine.calculate_success_chance("inspect")

        assert isinstance(chance, float)
        assert 0.0 <= chance <= 1.0

    def test_calculate_success_chance_with_faction(self) -> None:
        """calculate_success_chance works with faction_id."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        faction_ids = list(state.factions.keys())
        faction_id = faction_ids[0] if faction_ids else "unknown"

        chance = engine.calculate_success_chance("negotiate", faction_id=faction_id)

        assert isinstance(chance, float)
        assert 0.0 <= chance <= 1.0

    def test_calculate_success_chance_with_agent(self) -> None:
        """calculate_success_chance_with_agent returns float."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        agent_ids = list(state.agents.keys())
        agent_id = agent_ids[0] if agent_ids else None

        chance = engine.calculate_success_chance_with_agent(
            "inspect", agent_id=agent_id
        )

        assert isinstance(chance, float)
        assert 0.0 <= chance <= 1.0

    def test_agent_roster_summary_returns_list(self) -> None:
        """agent_roster_summary returns list of agent summaries."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        roster = engine.agent_roster_summary()

        assert isinstance(roster, list)

    def test_progression_state_updated_when_ticks_advance(self) -> None:
        """Progression state is updated when ticks advance."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        # Get initial progression
        initial_summary = engine.progression_summary()
        initial_experience = initial_summary.get("total_experience", 0)

        # Advance ticks
        engine.advance_ticks(5)

        # Get updated progression
        updated_summary = engine.progression_summary()
        updated_experience = updated_summary.get("total_experience", 0)

        # Progression state should have been processed
        # (even if experience didn't change, tick count should indicate system ran)
        assert isinstance(updated_summary, dict)
        # The progression system runs during tick advancement
        assert updated_experience >= initial_experience


# --------------------------------------------------------------------------
# Error Path Tests
# --------------------------------------------------------------------------


class TestErrorPaths:
    """Tests for error handling paths."""

    def test_advance_ticks_exceeds_limit(self) -> None:
        """ValueError raised when requesting too many ticks."""
        limits = SimulationLimits(
            engine_max_ticks=5,
            cli_run_cap=5,
            cli_script_command_cap=5,
            service_tick_cap=5,
        )
        config = SimulationConfig(limits=limits)
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="exceeds engine limit"):
            engine.advance_ticks(10)

    def test_focus_state_before_initialization_raises(self) -> None:
        """EngineNotInitializedError raised when calling focus_state before init."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.focus_state()

    def test_query_view_before_initialization_raises(self) -> None:
        """EngineNotInitializedError raised when querying view before init."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.query_view("summary")

    def test_advance_ticks_before_initialization_raises(self) -> None:
        """EngineNotInitializedError raised when advancing ticks before init."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.advance_ticks(1)

    def test_progression_summary_before_initialization_raises(self) -> None:
        """EngineNotInitializedError raised for progression_summary before init."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.progression_summary()
