"""Tests for the lightweight tick loop."""

from __future__ import annotations

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.settings import EconomySettings, SimulationConfig, SimulationLimits
from gengine.echoes.sim import SimEngine, TickReport, advance_ticks
from gengine.echoes.sim.director import NarrativeDirector


def test_advance_ticks_updates_environment_and_tick_math() -> None:
    state = load_world_bundle()

    reports = advance_ticks(state, count=3, seed=1234)

    assert state.tick == 3
    assert isinstance(reports[-1], TickReport)
    assert reports[-1].tick == 3
    for report in reports:
        env = report.environment
        assert 0.0 <= env["stability"] <= 1.0
        assert 0.0 <= env["unrest"] <= 1.0
        assert 0.0 <= env["pollution"] <= 1.0
        # District snapshots should match city layout
        assert len(report.districts) == len(state.city.districts)


def test_advance_ticks_requires_positive_count() -> None:
    state = load_world_bundle()
    try:
        advance_ticks(state, count=0)
    except ValueError as exc:  # pragma: no cover - explicit branch
        assert "count" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError when count < 1")


def test_engine_reports_include_economy_snapshot() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    report = engine.advance_ticks(1)[0]

    assert "prices" in report.economy
    assert "shortages" in report.economy
    assert isinstance(engine.state.metadata.get("market_prices"), dict)


def test_environment_impact_metadata_tracks_scarcity() -> None:
    config = SimulationConfig(
        economy=EconomySettings(shortage_threshold=0.9, shortage_warning_ticks=1)
    )
    engine = SimEngine(config=config)
    state = load_world_bundle()
    for district in state.city.districts:
        for stock in district.resources.values():
            stock.current = 0
            if stock.capacity == 0:
                stock.capacity = 10
    engine.initialize_state(state=state)

    engine.advance_ticks(1)

    impact = engine.state.metadata.get("environment_impact")
    assert impact
    assert impact["scarcity_pressure"] > 0
    assert "diffusion_applied" in impact


def test_tick_reports_include_timings() -> None:
    state = load_world_bundle()

    report = advance_ticks(state, count=1)[0]

    assert "tick_total_ms" in report.timings
    assert report.timings["tick_total_ms"] >= 0


def test_profiling_metadata_tracks_percentiles() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    engine.advance_ticks(5)

    profiling = engine.state.metadata.get("profiling")
    assert profiling
    assert profiling["tick_ms_p50"] > 0
    assert profiling["history_len"] >= 1
    assert profiling["last_subsystem_ms"]
    assert "slowest_subsystem" in profiling
    assert "anomalies" in profiling


def test_engine_enforces_tick_limit() -> None:
    limits = SimulationLimits(
        engine_max_ticks=2,
        cli_run_cap=2,
        cli_script_command_cap=5,
        service_tick_cap=2,
    )
    config = SimulationConfig(limits=limits)
    engine = SimEngine(config=config)
    engine.initialize_state(world="default")

    with pytest.raises(ValueError):
        engine.advance_ticks(5)


def test_focus_budget_populates_metadata() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")

    report = engine.advance_ticks(1)[0]

    assert report.focus_budget
    assert report.focus_budget.get("spatial_weights")
    assert report.event_archive
    assert report.director_snapshot
    digest = engine.state.metadata.get("focus_digest")
    assert digest
    assert digest["visible"] == report.events
    assert digest["ranked_archive"]
    history = engine.state.metadata.get("focus_history")
    assert history
    assert history[-1]["top_ranked"]
    assert report.districts and report.districts[0].get("coordinates") is not None
    director_feed = engine.state.metadata.get("director_feed")
    assert director_feed
    assert director_feed["tick"] == report.tick
    assert "top_ranked" in director_feed
    assert director_feed["top_ranked"][0].get("district_id") is not None
    director_history = engine.state.metadata.get("director_history")
    assert director_history
    assert director_history[-1]["tick"] == report.tick
    analysis = engine.state.metadata.get("director_analysis")
    assert analysis
    assert report.director_analysis
    assert analysis.get("hotspots") is not None
    assert isinstance(report.director_events, list)


def test_narrative_director_builds_travel_routes() -> None:
    state = load_world_bundle()
    assert len(state.city.districts) >= 2
    origin = state.city.districts[0].id
    target = state.city.districts[1].id
    director = NarrativeDirector()
    snapshot = {
        "tick": 42,
        "focus_center": origin,
        "suppressed_count": 1,
        "top_ranked": [
            {
                "message": "Spike",
                "scope": "district",
                "score": 1.1,
                "severity": 1.0,
                "focus_distance": 1,
                "in_focus_ring": False,
                "district_id": target,
            }
        ],
    }

    analysis = director.evaluate(state, snapshot=snapshot)

    assert analysis["hotspots"]
    travel = analysis["hotspots"][0]["travel"]
    assert travel["origin"] == origin
    assert travel["target"] == target
