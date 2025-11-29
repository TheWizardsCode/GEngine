"""Tests for the post-mortem summary generator."""

from __future__ import annotations

from gengine.echoes.content import load_world_bundle
from gengine.echoes.sim.post_mortem import generate_post_mortem_summary


def test_generate_post_mortem_summary_builds_recap() -> None:
    state = load_world_bundle()
    state.tick = 200
    state.metadata["director_history"] = [
        {
            "environment": {"stability": 0.4, "unrest": 0.6, "pollution": 0.7},
            "faction_legitimacy": {"union_of_flux": 0.45, "cartel_of_mist": 0.55},
        },
        {
            "environment": {"stability": 0.7, "unrest": 0.4, "pollution": 0.5},
            "faction_legitimacy": {"union_of_flux": 0.6, "cartel_of_mist": 0.48},
        },
    ]
    state.metadata["director_events"] = [
        {
            "seed_id": "energy-quota-crisis",
            "title": "Energy Quota Fallout",
            "district_id": "industrial-tier",
            "reason": "Scarcity spike",
            "tick": 180,
        }
    ]
    state.metadata["story_seed_lifecycle"] = {
        "energy-quota-crisis": {"state": "archived", "entered_tick": 150, "cooldown_remaining": 2}
    }
    state.metadata["story_seed_lifecycle_history"] = [
        {"seed_id": "energy-quota-crisis", "from": "active", "to": "archived", "tick": 150},
        {"seed_id": "hollow-supply-chain", "from": "primed", "to": "active", "tick": 160},
    ]

    summary = generate_post_mortem_summary(state)

    assert summary["tick"] == 200
    assert "environment" in summary
    assert summary["environment_trend"]["delta"]["stability"] > 0
    assert summary["faction_trends"]
    assert summary["featured_events"]
    assert summary["story_seeds"]
    assert summary["notes"]
    assert state.metadata["post_mortem"] == summary
