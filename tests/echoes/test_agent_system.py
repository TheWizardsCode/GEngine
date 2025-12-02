"""Tests for the agent subsystem (Phase 4, M4.1)."""

from __future__ import annotations

import random

from gengine.echoes.content import load_world_bundle
from gengine.echoes.core.models import Agent
from gengine.echoes.sim import SimEngine
from gengine.echoes.systems import AgentSystem


def test_agent_system_produces_deterministic_intents() -> None:
    state = load_world_bundle()
    system = AgentSystem(action_limit=4)
    rng = random.Random(42)

    intents_first = system.tick(state, rng=rng)
    rng = random.Random(42)
    intents_second = system.tick(state, rng=rng)

    assert [intent.intent for intent in intents_first] == [intent.intent for intent in intents_second]
    assert intents_first


def test_sim_engine_emits_agent_actions() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    reports = engine.advance_ticks(1)

    assert reports[0].agent_actions
    assert any("inspects" in event or "negotiates" in event for event in reports[0].events)


def test_agent_scoring_logic_traits() -> None:
    """Verify that agent traits influence option scoring."""
    state = load_world_bundle()
    system = AgentSystem()

    # Create a test agent with high empathy
    agent = Agent(
        id="test_agent",
        name="Test Agent",
        role="Operative",
        home_district="district_1",
        faction_id="faction_1",
        traits={"empathy": 1.0, "cunning": 0.0, "resolve": 0.0},
    )

    # Get district and faction from state
    district = state.city.districts[0]
    faction = list(state.factions.values())[0]

    # Calculate scores
    scores = system._calculate_scores(agent, district, faction, state)
    score_map = dict(scores)

    # Base score for STABILIZE_UNREST is 0.3 + unrest_pressure
    # With empathy 1.0, it should add 0.3
    # Let's compare with a low empathy agent

    agent_low = Agent(
        id="test_agent_low",
        name="Test Agent Low",
        role="Operative",
        home_district="district_1",
        faction_id="faction_1",
        traits={"empathy": 0.0, "cunning": 0.0, "resolve": 0.0},
    )

    scores_low = system._calculate_scores(agent_low, district, faction, state)
    score_map_low = dict(scores_low)

    assert score_map["STABILIZE_UNREST"] > score_map_low["STABILIZE_UNREST"]
    assert abs(score_map["STABILIZE_UNREST"] - score_map_low["STABILIZE_UNREST"] - 0.3) < 0.0001


def test_agent_scoring_logic_environment() -> None:
    """Verify that environment modifiers influence option scoring."""
    state = load_world_bundle()
    system = AgentSystem()

    agent = list(state.agents.values())[0]
    district = state.city.districts[0]
    faction = list(state.factions.values())[0]

    # Case 1: High Unrest
    district.modifiers.unrest = 1.0
    scores_high = system._calculate_scores(agent, district, faction, state)
    score_map_high = dict(scores_high)

    # Case 2: Low Unrest
    district.modifiers.unrest = 0.0
    scores_low = system._calculate_scores(agent, district, faction, state)
    score_map_low = dict(scores_low)

    assert score_map_high["STABILIZE_UNREST"] > score_map_low["STABILIZE_UNREST"]
    # Difference should be exactly 1.0 (the difference in unrest)
    assert abs(score_map_high["STABILIZE_UNREST"] - score_map_low["STABILIZE_UNREST"] - 1.0) < 0.0001


def test_agent_decision_edge_cases() -> None:
    """Verify behavior when agent has no district or faction."""
    state = load_world_bundle()
    system = AgentSystem()
    rng = random.Random(42)

    # Agent with no district or faction
    agent = Agent(
        id="loner",
        name="Loner",
        role="Drifter",
        home_district=None,
        faction_id=None,
        traits={},
    )

    # Should only have REQUEST_REPORT option
    scores = system._calculate_scores(agent, None, None, state)
    assert len(scores) == 1
    assert scores[0][0] == "REQUEST_REPORT"

    # _decide should still work
    intent = system._decide(agent, {}, {}, state, rng)
    assert intent is not None
    assert intent.intent == "REQUEST_REPORT"


def test_agent_decision_no_options() -> None:
    """Verify behavior when no options are available (simulated by mocking _calculate_scores)."""
    state = load_world_bundle()
    system = AgentSystem()
    rng = random.Random(42)

    agent = Agent(id="test", name="Test", role="Tester", home_district=None, faction_id=None)

    # Mock _calculate_scores to return empty list
    # We can just assign a lambda to the instance method
    system._calculate_scores = lambda *args: []  # type: ignore

    intent = system._decide(agent, {}, {}, state, rng)
    assert intent is None