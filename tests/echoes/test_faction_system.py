"""Tests for the faction subsystem (Phase 4, M4.2)."""

from __future__ import annotations

import random

from gengine.echoes.content import load_world_bundle
from gengine.echoes.systems import FactionSystem


def _prepare_state(single_faction: bool = False):
    state = load_world_bundle()
    if single_faction:
        union = state.factions["union_of_flux"]
        state.factions = {union.id: union}
        for district in state.city.districts:
            district.modifiers.unrest = 0.2
            district.modifiers.security = 0.8
        union.legitimacy = 0.4
        union.resources = {"influence": 60}
    else:
        for district in state.city.districts:
            if district.id in ("industrial-tier", "perimeter-hollow"):
                district.modifiers.unrest = 0.2
                district.modifiers.security = 0.8
        state.factions["union_of_flux"].legitimacy = 0.8
        state.factions["union_of_flux"].resources = {"influence": 80}
        state.factions["cartel_of_mist"].legitimacy = 0.45
    return state


def test_faction_system_lobbies_when_legitimacy_low() -> None:
    state = _prepare_state(single_faction=True)
    system = FactionSystem(cooldown_ticks=1)
    rng = random.Random(0)

    actions = system.tick(state, rng=rng)

    assert any(action.action == "LOBBY_COUNCIL" for action in actions)
    assert state.factions["union_of_flux"].legitimacy > 0.4


def test_faction_system_can_sabotage_rivals() -> None:
    state = _prepare_state(single_faction=False)
    system = FactionSystem(cooldown_ticks=1)
    rng = random.Random(1)

    actions = system.tick(state, rng=rng)

    sabotage = next((action for action in actions if action.action == "SABOTAGE_RIVAL"), None)
    assert sabotage is not None
    assert state.factions["cartel_of_mist"].legitimacy < 0.45