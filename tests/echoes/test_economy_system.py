"""Tests for the economy subsystem (Phase 4, M4.3)."""

from __future__ import annotations

import random

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.settings import EconomySettings
from gengine.echoes.systems import EconomySystem


def test_economy_system_tracks_shortages() -> None:
    state = load_world_bundle()
    for district in state.city.districts:
        for stock in district.resources.values():
            stock.current = 0
            stock.capacity = max(stock.capacity, 10)
    settings = EconomySettings(shortage_threshold=0.9, shortage_warning_ticks=1)
    system = EconomySystem(settings=settings)

    report = system.tick(state, rng=random.Random(0))

    assert report.shortages
    assert report.prices
    assert state.metadata["market_prices"]


def test_economy_system_rebalances_resources() -> None:
    state = load_world_bundle()
    target = state.city.districts[0]
    energy = target.resources["energy"]
    energy.current = energy.capacity
    system = EconomySystem()

    system.tick(state, rng=random.Random(1))

    assert energy.current <= energy.capacity


def test_economy_system_price_respects_configured_steps() -> None:
    state = load_world_bundle()
    for district in state.city.districts:
        for stock in district.resources.values():
            stock.current = 0
    settings = EconomySettings(
        shortage_threshold=0.9,
        shortage_warning_ticks=1,
        price_increase_step=0.2,
        price_max_boost=0.2,
    )
    system = EconomySystem(settings=settings)

    report = system.tick(state, rng=random.Random(2))

    assert report.prices
    sample_price = next(iter(report.prices.values()))
    assert sample_price == pytest.approx(1.2, rel=1e-3)


def test_economy_system_long_run_conserves_resources_and_prices() -> None:
    state = load_world_bundle()
    settings = EconomySettings(
        price_decay=0.02,
        price_floor=0.75,
        price_max_boost=0.4,
    )
    system = EconomySystem(settings=settings)
    rng = random.Random(3)

    for _ in range(30):
        report = system.tick(state, rng=rng)
        for district in state.city.districts:
            for stock in district.resources.values():
                assert 0 <= stock.current <= stock.capacity
        ceiling = settings.base_price + settings.price_max_boost
        for price in report.prices.values():
            assert settings.price_floor <= price <= ceiling
