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


def _single_faction_state():
    state = load_world_bundle()
    faction = state.factions["union_of_flux"]
    state.factions = {faction.id: faction}
    return state, faction


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


def test_faction_system_invests_to_calm_unrest() -> None:
    state, faction = _single_faction_state()
    faction.legitimacy = 0.9
    faction.resources = {"influence": 120}
    for district in state.city.districts:
        if district.id in faction.territory:
            district.modifiers.unrest = 0.9
            district.modifiers.security = 0.2
    system = FactionSystem(cooldown_ticks=1)

    actions = system.tick(state, rng=random.Random(2))

    invest = next((action for action in actions if action.action == "INVEST_DISTRICT"), None)
    assert invest is not None
    target = next(d for d in state.city.districts if d.id == invest.target)
    assert target.modifiers.unrest < 0.9


def test_faction_system_recruits_when_resources_low() -> None:
    state, faction = _single_faction_state()
    faction.legitimacy = 0.95
    faction.resources = {}
    for district in state.city.districts:
        if district.id in faction.territory:
            district.modifiers.unrest = 0.2
            district.modifiers.security = 0.9
    system = FactionSystem(cooldown_ticks=1)

    actions = system.tick(state, rng=random.Random(3))

    recruit = next((action for action in actions if action.action == "RECRUIT_SUPPORT"), None)
    assert recruit is not None
    assert recruit.resource_delta > 0


def test_faction_system_takes_no_action_when_stable() -> None:
    state, faction = _single_faction_state()
    faction.legitimacy = 0.95
    faction.resources = {"influence": 200}
    for district in state.city.districts:
        district.modifiers.unrest = 0.2
        district.modifiers.security = 0.9
    system = FactionSystem(cooldown_ticks=1)

    actions = system.tick(state, rng=random.Random(4))

    assert actions == []