"""Tests covering authored story seeds and director integration."""

from __future__ import annotations

from gengine.echoes.content import load_world_bundle
from gengine.echoes.core.models import (
    StorySeed,
    StorySeedResolutionTemplates,
    StorySeedTrigger,
)
from gengine.echoes.core.state import GameState
from gengine.echoes.settings import DirectorSettings
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
    assert seed.followups == ["supply-chain-collapse"]


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
    energy_seed = next(
        seed for seed in seeds if seed["seed_id"] == "energy-quota-crisis"
    )
    cooldown = state.story_seeds["energy-quota-crisis"].cooldown_ticks
    assert energy_seed["last_trigger_tick"] == first_tick
    assert energy_seed["cooldown_remaining"] == cooldown - (followup_tick - first_tick)
    assert state.metadata.get("story_seed_context")


def test_summary_includes_pacing_and_lifecycle_metadata() -> None:
    state = load_world_bundle()
    state.metadata["director_pacing"] = {"active": 1, "resolving": 0}
    state.metadata["story_seed_lifecycle"] = {
        "seed-1": {"state": "active", "entered_tick": 4}
    }
    state.metadata["story_seed_lifecycle_history"] = [
        {"tick": 4, "seed_id": "seed-1", "from": "primed", "to": "active"}
    ]
    state.metadata["story_seeds_active"] = [
        {"seed_id": "seed-1", "title": "Test Seed", "score": 0.9}
    ]
    state.metadata["director_quiet_until"] = state.tick + 5

    summary = state.summary()

    assert summary["director_pacing"]["active"] == 1
    assert summary["story_seed_lifecycle"]["seed-1"]["state"] == "active"
    assert summary["story_seed_lifecycle_history"]
    assert summary["director_quiet_until"] == state.tick + 5


def test_story_seed_lifecycle_transitions_and_persists() -> None:
    state = load_world_bundle()
    state.story_seeds["energy-quota-crisis"].cooldown_ticks = 1
    settings = DirectorSettings(
        seed_active_ticks=1,
        seed_resolve_ticks=1,
        seed_quiet_ticks=1,
        global_quiet_ticks=0,
    )
    director = NarrativeDirector(settings=settings)

    def snapshot(tick: int, include_hotspot: bool) -> dict[str, object]:
        entry = {
            "message": "Power rationing hits workshops",
            "scope": "environment",
            "score": 0.9,
            "severity": 0.85,
            "focus_distance": 1,
            "in_focus_ring": True,
            "district_id": "industrial-tier",
        }
        return {
            "tick": tick,
            "focus_center": "industrial-tier",
            "suppressed_count": 0,
            "top_ranked": [entry] if include_hotspot else [],
        }

    director.evaluate(state, snapshot=snapshot(10, True))
    lifecycle = state.metadata["story_seed_lifecycle"]["energy-quota-crisis"]
    assert lifecycle["state"] == "active"

    director.evaluate(state, snapshot=snapshot(11, False))
    lifecycle = state.metadata["story_seed_lifecycle"]["energy-quota-crisis"]
    assert lifecycle["state"] == "resolving"

    director.evaluate(state, snapshot=snapshot(12, False))
    lifecycle = state.metadata["story_seed_lifecycle"]["energy-quota-crisis"]
    assert lifecycle["state"] == "archived"

    payload = state.snapshot()
    restored = GameState.from_snapshot(payload)
    restored.story_seeds["energy-quota-crisis"].cooldown_ticks = 1
    director = NarrativeDirector(settings=settings)

    director.evaluate(restored, snapshot=snapshot(14, False))
    lifecycle = restored.metadata["story_seed_lifecycle"]["energy-quota-crisis"]
    assert lifecycle["state"] == "primed"
    history = restored.metadata.get("story_seed_lifecycle_history") or []
    assert any(entry["to"] == "archived" for entry in history)


def _build_seed(seed_id: str) -> StorySeed:
    resolution = StorySeedResolutionTemplates(success="ok", failure="fail")
    trigger = StorySeedTrigger(scope="environment", min_score=0.1, min_severity=0.1)
    return StorySeed(
        id=seed_id,
        title=f"Seed {seed_id}",
        summary="Test storyline",
        stakes="High stakes",
        scope="environment",
        cooldown_ticks=1,
        triggers=[trigger],
        resolution_templates=resolution,
    )


def _feed_payload(tick: int) -> dict[str, object]:
    entry = {
        "district_id": "industrial-tier",
        "message": "Scarcity spike",
        "scope": "environment",
        "score": 0.95,
        "severity": 0.9,
        "focus_distance": 0,
        "in_focus_ring": True,
    }
    return {
        "tick": tick,
        "focus_center": "industrial-tier",
        "suppressed_count": 0,
        "top_ranked": [entry],
    }


def test_director_pacing_flags_max_active_block() -> None:
    state = load_world_bundle()
    state.story_seeds = {
        "seed-alpha": _build_seed("seed-alpha"),
        "seed-beta": _build_seed("seed-beta"),
    }
    settings = DirectorSettings(
        max_active_seeds=1,
        seed_active_ticks=1,
        seed_resolve_ticks=0,
        seed_quiet_ticks=0,
        global_quiet_ticks=0,
        lifecycle_history_limit=4,
    )
    director = NarrativeDirector(settings=settings)

    director.evaluate(state, snapshot=_feed_payload(30))

    pacing = state.metadata["director_pacing"]
    assert pacing["active"] == 1
    assert "max_active" in pacing.get("blocked_reasons", [])
    assert pacing.get("global_quiet_until", 0) == 0


def test_director_pacing_applies_global_quiet_timer() -> None:
    state = load_world_bundle()
    state.story_seeds = {
        "seed-alpha": _build_seed("seed-alpha"),
        "seed-beta": _build_seed("seed-beta"),
    }
    settings = DirectorSettings(
        max_active_seeds=1,
        seed_active_ticks=1,
        seed_resolve_ticks=0,
        seed_quiet_ticks=2,
        global_quiet_ticks=2,
        lifecycle_history_limit=6,
    )
    director = NarrativeDirector(settings=settings)

    director.evaluate(state, snapshot=_feed_payload(40))
    pacing = state.metadata["director_pacing"]
    assert pacing["active"] == 1
    assert pacing["global_quiet_until"] > 40
    assert "global_quiet" in pacing.get("blocked_reasons", [])
    assert pacing["global_quiet_remaining"] > 0

    director.evaluate(state, snapshot=_feed_payload(41))
    director.evaluate(state, snapshot=_feed_payload(42))

    director.evaluate(state, snapshot=_feed_payload(44))
    lifecycle = state.metadata["story_seed_lifecycle"]["seed-alpha"]
    assert lifecycle["state"] in {"archived", "primed"}
    history = state.metadata.get("story_seed_lifecycle_history") or []
    assert history
    assert len(history) <= settings.lifecycle_history_limit
