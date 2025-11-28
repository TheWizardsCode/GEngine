"""Tests for the agent subsystem (Phase 4, M4.1)."""

from __future__ import annotations

import random

from gengine.echoes.content import load_world_bundle
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