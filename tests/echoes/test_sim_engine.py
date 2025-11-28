"""Tests for the SimEngine abstraction (Phase 3, M3.1)."""

from __future__ import annotations

import pytest

from gengine.echoes.settings import SimulationConfig, SimulationLimits
from gengine.echoes.sim import SimEngine


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