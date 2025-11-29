"""Tests covering authored story seeds and director integration."""

from __future__ import annotations

from gengine.echoes.content import load_world_bundle
from gengine.echoes.sim.director import NarrativeDirector


def test_world_loader_populates_story_seeds() -> None:
    state = load_world_bundle()

    assert state.story_seeds
    assert "energy-quota-crisis" in state.story_seeds
    assert state.story_seeds["energy-quota-crisis"].triggers


def test_story_seed_schema_fields_are_loaded() -> None:
    state = load_world_bundle()

    seed = state.story_seeds["energy-quota-crisis"]

    assert seed.stakes
    assert seed.resolution_templates.success
    assert seed.resolution_templates.failure
    assert seed.travel_hint is not None
    assert seed.followups == ["hollow-supply-chain"]


def test_summary_includes_active_story_seeds() -> None:
    state = load_world_bundle()
    active = {
        "seed_id": "energy-quota-crisis",
        "title": "Energy Quota Fallout",
        "district_id": "industrial-tier",
        "reason": "test",
        "score": 0.9,
    }
    state.metadata["story_seeds_active"] = [active]

    summary = state.summary()

    assert summary["story_seeds"] == [active]


def test_summary_includes_director_events_history() -> None:
    state = load_world_bundle()
    event = {
        "seed_id": "energy-quota-crisis",
        "title": "Energy Quota Fallout",
        "district_id": "industrial-tier",
        "reason": "Power rationing hits workshops",
    }
    state.metadata["director_events"] = [event]

    summary = state.summary()

    assert summary["director_events"] == [event]


def test_narrative_director_matches_story_seed() -> None:
    state = load_world_bundle()
    director = NarrativeDirector()
    snapshot = {
        "tick": 12,
        "focus_center": "industrial-tier",
        "suppressed_count": 6,
        "top_ranked": [
            {
                "message": "Power rationing hits workshops",
                "scope": "environment",
                "score": 0.9,
                "severity": 0.85,
                "focus_distance": 1,
                "in_focus_ring": True,
                "district_id": "industrial-tier",
            }
        ],
    }

    analysis = director.evaluate(state, snapshot=snapshot)

    seeds = analysis.get("story_seeds") or []
    assert seeds
    assert any(seed["seed_id"] == "energy-quota-crisis" for seed in seeds)
    assert state.metadata.get("story_seeds_active")
    assert state.metadata.get("story_seed_cooldowns")
    events = analysis.get("director_events") or []
    assert events
    assert events[0]["seed_id"] == "energy-quota-crisis"
    assert events[0]["agents"]
    assert state.metadata.get("director_events")


def test_story_seed_persists_during_cooldown_window() -> None:
    state = load_world_bundle()
    director = NarrativeDirector()
    first_tick = 20
    first_snapshot = {
        "tick": first_tick,
        "focus_center": "industrial-tier",
        "suppressed_count": 2,
        "top_ranked": [
            {
                "message": "Scarcity in energy, materials strains the city environment",
                "scope": "environment",
                "score": 0.8,
                "severity": 0.9,
                "focus_distance": 1,
                "in_focus_ring": True,
                "district_id": None,
            }
        ],
    }
    director.evaluate(state, snapshot=first_snapshot)

    followup_tick = first_tick + 5
    followup_snapshot = {
        "tick": followup_tick,
        "focus_center": "industrial-tier",
        "suppressed_count": 0,
        "top_ranked": [
            {
                "message": "Cassian Mire inspects Perimeter Hollow",
                "scope": "agent",
                "score": 0.4,
                "severity": 0.5,
                "focus_distance": 1,
                "in_focus_ring": True,
                "district_id": "perimeter-hollow",
            }
        ],
    }

    analysis = director.evaluate(state, snapshot=followup_snapshot)
    seeds = analysis.get("story_seeds") or []

    assert seeds
    energy_seed = next(seed for seed in seeds if seed["seed_id"] == "energy-quota-crisis")
    cooldown = state.story_seeds["energy-quota-crisis"].cooldown_ticks
    assert energy_seed["last_trigger_tick"] == first_tick
    assert energy_seed["cooldown_remaining"] == cooldown - (followup_tick - first_tick)
    assert state.metadata.get("story_seed_context")
