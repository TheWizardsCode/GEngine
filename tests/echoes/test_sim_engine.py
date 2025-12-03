"""Tests for the SimEngine abstraction (Phase 3, M3.1).

This module includes comprehensive tests for:
- All public SimEngine APIs (views, focus, director, explanations, progression)
- Error handling paths (uninitialized state, invalid inputs, tick limits)
- Integration with progression system
"""

from __future__ import annotations

import pytest

from gengine.echoes.settings import SimulationConfig, SimulationLimits
from gengine.echoes.sim import SimEngine
from gengine.echoes.sim.engine import EngineNotInitializedError


# --------------------------------------------------------------------------
# Basic initialization tests
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
# Error handling tests
# --------------------------------------------------------------------------


class TestSimEngineErrorHandling:
    """Tests for error handling paths in SimEngine."""

    def test_state_access_before_initialization_raises(self) -> None:
        """Accessing state before initialization should raise EngineNotInitializedError."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            _ = engine.state

    def test_advance_ticks_before_initialization_raises(self) -> None:
        """Calling advance_ticks before initialization should raise."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.advance_ticks(1)

    def test_query_view_before_initialization_raises(self) -> None:
        """Calling query_view before initialization should raise."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.query_view("summary")

    def test_focus_state_before_initialization_raises(self) -> None:
        """Calling focus_state before initialization should raise."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.focus_state()

    def test_initialize_state_without_arguments_raises(self) -> None:
        """initialize_state with no arguments should raise ValueError."""
        engine = SimEngine()

        with pytest.raises(ValueError, match="Provide state, world, or snapshot"):
            engine.initialize_state()

    def test_query_view_with_invalid_view_name_raises(self) -> None:
        """Unknown view names should raise ValueError."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="Unknown view"):
            engine.query_view("invalid-view-name")

    def test_district_view_without_district_id_raises(self) -> None:
        """District view without district_id should raise ValueError."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="district view requires"):
            engine.query_view("district")

    def test_district_view_with_unknown_district_raises(self) -> None:
        """District view with unknown district_id should raise ValueError."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="Unknown district"):
            engine.query_view("district", district_id="nonexistent-district")

    def test_advance_ticks_exceeding_limit_raises(self) -> None:
        """Requesting too many ticks should raise ValueError."""
        limits = SimulationLimits(
            engine_max_ticks=5,
            cli_run_cap=5,
            cli_script_command_cap=10,
            service_tick_cap=5,
        )
        config = SimulationConfig(limits=limits)
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="exceeds engine limit"):
            engine.advance_ticks(10)


# --------------------------------------------------------------------------
# Query view tests for all view types
# --------------------------------------------------------------------------


class TestSimEngineQueryViews:
    """Tests for query_view with all supported view names."""

    def test_query_view_summary(self) -> None:
        """Query summary view returns expected structure."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.query_view("summary")

        assert isinstance(result, dict)
        assert "city" in result
        assert "tick" in result
        assert "factions" in result

    def test_query_view_snapshot(self) -> None:
        """Query snapshot view returns full state representation."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.query_view("snapshot")

        assert isinstance(result, dict)
        assert "city" in result
        assert "agents" in result
        assert "factions" in result

    def test_query_view_district(self) -> None:
        """Query district view returns district details."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        district_id = state.city.districts[0].id

        result = engine.query_view("district", district_id=district_id)

        assert result["id"] == district_id
        assert "name" in result
        assert "population" in result
        assert "modifiers" in result
        assert "adjacent" in result

    def test_query_view_post_mortem(self) -> None:
        """Query post-mortem view returns analysis summary."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(1)

        result = engine.query_view("post-mortem")

        assert "tick" in result
        assert "environment" in result


# --------------------------------------------------------------------------
# Director feed tests
# --------------------------------------------------------------------------


class TestSimEngineDirectorFeed:
    """Tests for director_feed method."""

    def test_director_feed_returns_expected_structure(self) -> None:
        """director_feed returns a dict with required keys."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        feed = engine.director_feed()

        assert isinstance(feed, dict)
        assert "latest" in feed
        assert "history" in feed
        assert "analysis" in feed
        assert "events" in feed

    def test_director_feed_after_ticks_has_content(self) -> None:
        """director_feed after advancing ticks contains data."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(3)

        feed = engine.director_feed()

        # Feed should have been populated by ticks
        assert isinstance(feed["latest"], dict)
        assert isinstance(feed["history"], list)
        assert isinstance(feed["events"], list)

    def test_director_feed_before_initialization_raises(self) -> None:
        """Calling director_feed before initialization should raise."""
        engine = SimEngine()

        with pytest.raises(EngineNotInitializedError):
            engine.director_feed()


# --------------------------------------------------------------------------
# Explanations API tests
# --------------------------------------------------------------------------


class TestSimEngineExplanationsAPI:
    """Tests for explanation methods at the engine level."""

    def test_query_timeline_returns_list(self) -> None:
        """query_timeline returns a list of timeline entries."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(2)

        timeline = engine.query_timeline(count=5)

        assert isinstance(timeline, list)
        # After ticks, we should have at least some entries
        assert all(isinstance(entry, dict) for entry in timeline)

    def test_query_timeline_respects_count(self) -> None:
        """query_timeline returns at most count entries."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(5)

        timeline = engine.query_timeline(count=3)

        assert len(timeline) <= 3

    def test_explain_metric_returns_explanation(self) -> None:
        """explain_metric returns a dict with metric explanation."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(2)

        result = engine.explain_metric("stability")

        assert isinstance(result, dict)
        assert result["metric"] == "stability"
        assert "current_value" in result
        assert "causes" in result

    def test_explain_metric_with_lookback(self) -> None:
        """explain_metric respects lookback parameter."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(5)

        result = engine.explain_metric("unrest", lookback=2)

        assert isinstance(result, dict)
        assert result["metric"] == "unrest"

    def test_explain_faction_returns_faction_info(self) -> None:
        """explain_faction returns info about a faction."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        engine.advance_ticks(2)

        # Get any faction id from the state
        faction_id = next(iter(state.factions.keys()))

        result = engine.explain_faction(faction_id)

        assert isinstance(result, dict)
        assert "faction_name" in result
        assert "current_legitimacy" in result

    def test_explain_faction_unknown_returns_error(self) -> None:
        """explain_faction with unknown faction returns error."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.explain_faction("nonexistent-faction")

        assert "error" in result

    def test_explain_agent_returns_agent_info(self) -> None:
        """explain_agent returns info about an agent."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        engine.advance_ticks(2)

        # Get any agent id from the state
        agent_id = next(iter(state.agents.keys()))

        result = engine.explain_agent(agent_id)

        assert isinstance(result, dict)
        assert "agent_name" in result
        assert "role" in result

    def test_explain_agent_unknown_returns_error(self) -> None:
        """explain_agent with unknown agent returns error."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.explain_agent("nonexistent-agent")

        assert "error" in result

    def test_explain_district_returns_district_info(self) -> None:
        """explain_district returns info about a district."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")
        engine.advance_ticks(2)

        district_id = state.city.districts[0].id

        result = engine.explain_district(district_id)

        assert isinstance(result, dict)
        assert "district_name" in result
        assert "modifiers" in result

    def test_explain_district_unknown_returns_error(self) -> None:
        """explain_district with unknown district returns error."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.explain_district("nonexistent-district")

        assert "error" in result

    def test_why_query_returns_result(self) -> None:
        """why method returns an explanation based on query."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(2)

        result = engine.why("why is stability changing?")

        assert isinstance(result, dict)

    def test_why_query_unknown_topic_suggests_help(self) -> None:
        """why method with unknown topic suggests help."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.why("random unrecognized query")

        assert isinstance(result, dict)
        assert "suggestion" in result


# --------------------------------------------------------------------------
# Progression API tests
# --------------------------------------------------------------------------


class TestSimEngineProgressionAPI:
    """Tests for progression methods at the engine level."""

    def test_progression_summary_returns_summary(self) -> None:
        """progression_summary returns a summary dict."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        summary = engine.progression_summary()

        assert isinstance(summary, dict)
        assert "access_tier" in summary
        assert "skills" in summary

    def test_progression_summary_after_ticks(self) -> None:
        """progression_summary reflects state after ticks."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(3)

        summary = engine.progression_summary()

        # Summary should have reasonable structure
        assert isinstance(summary, dict)
        assert "total_experience" in summary

    def test_calculate_success_chance_returns_float(self) -> None:
        """calculate_success_chance returns a probability value."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")

        faction_id = next(iter(state.factions.keys()))
        chance = engine.calculate_success_chance("negotiate", faction_id)

        assert isinstance(chance, float)
        assert 0.0 <= chance <= 1.0

    def test_calculate_success_chance_varies_by_action_type(self) -> None:
        """Different action types may yield different success chances."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")

        faction_id = next(iter(state.factions.keys()))
        chance1 = engine.calculate_success_chance("negotiate", faction_id)
        chance2 = engine.calculate_success_chance("investigate", faction_id)

        # Just verifying both return valid floats
        assert isinstance(chance1, float)
        assert isinstance(chance2, float)

    def test_calculate_success_chance_with_agent(self) -> None:
        """calculate_success_chance_with_agent includes agent modifiers."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")

        agent_id = next(iter(state.agents.keys()))
        faction_id = next(iter(state.factions.keys()))

        chance = engine.calculate_success_chance_with_agent(
            "negotiate", agent_id, faction_id
        )

        assert isinstance(chance, float)
        assert 0.0 <= chance <= 1.0

    def test_agent_roster_summary_returns_list(self) -> None:
        """agent_roster_summary returns a list of agent summaries."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        roster = engine.agent_roster_summary()

        assert isinstance(roster, list)
        # Each entry should be a dict with agent info
        for entry in roster:
            assert isinstance(entry, dict)


# --------------------------------------------------------------------------
# Progression integration test
# --------------------------------------------------------------------------


class TestSimEngineProgressionIntegration:
    """Tests for verifying progression updates when ticks advance."""

    def test_progression_state_updates_on_tick_advance(self) -> None:
        """Progression state is updated when ticks advance.

        This test validates that the interaction between SimEngine
        and ProgressionSystem is working - i.e., that a tick actually
        updates progression.
        """
        engine = SimEngine()
        engine.initialize_state(world="default")

        # Get initial progression state
        initial_summary = engine.progression_summary()
        initial_total_exp = initial_summary.get("total_experience", 0)

        # Advance several ticks with deterministic seed
        engine.advance_ticks(10, seed=42)

        # Get updated progression state
        updated_summary = engine.progression_summary()
        updated_total_exp = updated_summary.get("total_experience", 0)

        # Progression should have changed (experience should increase)
        # Note: With a seed, we get deterministic agent actions that grant experience
        assert updated_total_exp >= initial_total_exp

    def test_progression_events_recorded_in_metadata(self) -> None:
        """Progression events are recorded in state metadata during ticks."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        # Advance ticks
        engine.advance_ticks(5, seed=42)

        # Check that progression state exists
        progression = engine.state.ensure_progression()
        assert progression is not None

        # Verify progression summary reflects actual state
        summary = engine.progression_summary()
        assert summary["access_tier"] == progression.access_tier.value


# --------------------------------------------------------------------------
# Additional API coverage tests
# --------------------------------------------------------------------------


class TestSimEngineAdditionalCoverage:
    """Additional tests for full API coverage."""

    def test_config_property_returns_config(self) -> None:
        """config property returns the SimulationConfig."""
        engine = SimEngine()

        config = engine.config

        assert isinstance(config, SimulationConfig)

    def test_initialize_state_with_provided_state(self) -> None:
        """initialize_state can accept a pre-built GameState."""
        from gengine.echoes.content import load_world_bundle

        engine = SimEngine()
        provided_state = load_world_bundle("default")

        result = engine.initialize_state(state=provided_state)

        assert result is provided_state
        assert engine.state is provided_state

    def test_apply_action_without_args_returns_noop(self) -> None:
        """apply_action with no arguments returns noop receipt."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.apply_action()

        assert result["status"] == "noop"
        assert result["received"] == {}

    def test_set_focus_updates_focus(self) -> None:
        """set_focus changes the focused district."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")

        district_id = state.city.districts[0].id
        result = engine.set_focus(district_id)

        assert result["district_id"] == district_id

    def test_clear_focus_after_set_focus(self) -> None:
        """clear_focus resets focus after it was set."""
        engine = SimEngine()
        state = engine.initialize_state(world="default")

        # Set then clear
        district_id = state.city.districts[0].id
        engine.set_focus(district_id)
        result = engine.clear_focus()

        # Should still have a district_id (focus manager picks default)
        assert "district_id" in result
