"""Tests for the environment subsystem plumbing."""

from __future__ import annotations

import random

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.settings import EnvironmentSettings
from gengine.echoes.systems import EnvironmentSystem
from gengine.echoes.systems.economy import EconomyReport


def test_environment_system_applies_scarcity_pressure() -> None:
    state = load_world_bundle()
    settings = EnvironmentSettings(
        scarcity_unrest_weight=0.02,
        scarcity_pollution_weight=0.01,
        district_unrest_weight=0.01,
        district_pollution_weight=0.005,
        scarcity_event_threshold=0.5,
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


def test_environment_system_noop_without_shortages() -> None:
    state = load_world_bundle()
    system = EnvironmentSystem()
    report = EconomyReport(prices={}, shortages={})
    baseline_unrest = state.environment.unrest

    impact = system.tick(state, rng=random.Random(1), economy_report=report)

    assert impact.scarcity_pressure == 0
    assert state.environment.unrest == baseline_unrest
    assert not impact.events
