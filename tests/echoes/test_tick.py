"""Tests for the lightweight tick loop."""

from __future__ import annotations

from gengine.echoes.content import load_world_bundle
from gengine.echoes.settings import EconomySettings, SimulationConfig
from gengine.echoes.sim import SimEngine, TickReport, advance_ticks


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
