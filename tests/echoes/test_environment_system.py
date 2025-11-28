"""Tests for the environment subsystem plumbing."""

from __future__ import annotations

import random

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.settings import EnvironmentSettings
from gengine.echoes.systems import EnvironmentSystem, FactionAction
from gengine.echoes.systems.economy import EconomyReport


def test_environment_system_applies_scarcity_pressure() -> None:
    state = load_world_bundle()
    settings = EnvironmentSettings(
        scarcity_unrest_weight=0.02,
        scarcity_pollution_weight=0.01,
        district_unrest_weight=0.01,
        district_pollution_weight=0.005,
        scarcity_event_threshold=0.5,
        diffusion_rate=0.0,
    )
    system = EnvironmentSystem(settings=settings)
    report = EconomyReport(prices={}, shortages={"energy": 4, "water": 2})
    baseline_unrest = state.environment.unrest
    baseline_pollution = state.environment.pollution
    target_district = state.city.districts[0]
    district_unrest = target_district.modifiers.unrest

    impact = system.tick(state, rng=random.Random(0), economy_report=report)

    assert impact.scarcity_pressure == pytest.approx(1.0)
    assert state.environment.unrest > baseline_unrest
    assert state.environment.pollution > baseline_pollution
    assert target_district.modifiers.unrest > district_unrest
    assert impact.events and "Scarcity" in impact.events[0]
    assert impact.diffusion_applied is False


def test_environment_system_noop_without_shortages() -> None:
    state = load_world_bundle()
    system = EnvironmentSystem(
        settings=EnvironmentSettings(
            diffusion_rate=0.0,
            scarcity_unrest_weight=0.0,
            scarcity_pollution_weight=0.0,
            district_unrest_weight=0.0,
            district_pollution_weight=0.0,
        )
    )
    report = EconomyReport(prices={}, shortages={})
    baseline_unrest = state.environment.unrest

    impact = system.tick(state, rng=random.Random(1), economy_report=report)

    assert impact.scarcity_pressure == 0
    assert state.environment.unrest == baseline_unrest
    assert not impact.events
    assert impact.diffusion_applied is False


def test_environment_system_reacts_to_faction_actions() -> None:
    state = load_world_bundle()
    district = state.city.districts[0]
    action = FactionAction(
        faction_id="union_of_flux",
        faction_name="Union of Flux",
        action="INVEST_DISTRICT",
        target=district.id,
        target_name=district.name,
        detail="",
        legitimacy_delta=0.0,
        resource_delta=0,
        district_id=district.id,
    )
    sabotage = FactionAction(
        faction_id="cartel_of_mist",
        faction_name="Cartel of Mist",
        action="SABOTAGE_RIVAL",
        target="union_of_flux",
        target_name="Union of Flux",
        detail="",
        legitimacy_delta=0.0,
        resource_delta=0,
        district_id=district.id,
    )
    system = EnvironmentSystem()

    impact = system.tick(
        state,
        rng=random.Random(2),
        economy_report=EconomyReport(prices={}, shortages={}),
        faction_actions=[action, sabotage],
    )

    assert impact.faction_effects
    assert any(effect["action"] == "SABOTAGE_RIVAL" for effect in impact.faction_effects)
    assert any("pollution" in event for event in impact.events)


def test_environment_system_runs_diffusion_cycle() -> None:
    state = load_world_bundle()
    if len(state.city.districts) < 2:
        pytest.skip("requires at least two districts")
    state.city.districts[0].modifiers.pollution = 1.0
    state.city.districts[1].modifiers.pollution = 0.1
    system = EnvironmentSystem(
        settings=EnvironmentSettings(
            diffusion_rate=0.5,
            scarcity_unrest_weight=0.0,
            scarcity_pollution_weight=0.0,
            district_unrest_weight=0.0,
            district_pollution_weight=0.0,
        )
    )

    impact = system.tick(
        state,
        rng=random.Random(7),
        economy_report=EconomyReport(prices={}, shortages={}),
    )

    assert impact.diffusion_applied is True
    assert impact.district_deltas


def test_environment_diffusion_reports_extremes_and_samples() -> None:
    state = load_world_bundle()
    if len(state.city.districts) < 2:
        pytest.skip("requires at least two districts")
    first, second = state.city.districts[:2]
    first.modifiers.pollution = 1.0
    second.modifiers.pollution = 0.0
    first.adjacent = [second.id]
    second.adjacent = [first.id]
    system = EnvironmentSystem(
        settings=EnvironmentSettings(
            diffusion_rate=0.5,
            diffusion_neighbor_bias=1.0,
            diffusion_min_delta=0.0001,
            diffusion_max_delta=0.01,
            scarcity_unrest_weight=0.0,
            scarcity_pollution_weight=0.0,
            district_unrest_weight=0.0,
            district_pollution_weight=0.0,
        )
    )

    impact = system.tick(
        state,
        rng=random.Random(11),
        economy_report=EconomyReport(prices={}, shortages={}),
    )

    assert impact.diffusion_applied is True
    assert impact.diffusion_samples
    assert impact.extremes
    assert impact.average_pollution == pytest.approx(
        sum(d.modifiers.pollution for d in state.city.districts) / len(state.city.districts)
    )
    assert all(abs(sample["delta"]) <= 0.01 for sample in impact.diffusion_samples)
    assert any(sample.get("neighbor_avg") is not None for sample in impact.diffusion_samples)
