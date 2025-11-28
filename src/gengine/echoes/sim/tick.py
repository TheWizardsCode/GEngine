"""Simple tick loop and environment updates for the Echoes prototype."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Sequence

from ..core import GameState
from ..settings import LodSettings


@dataclass(slots=True)
class TickReport:
    """Structured information about a single tick advancement."""

    tick: int
    events: List[str] = field(default_factory=list)
    environment: dict[str, float] = field(default_factory=dict)
    districts: List[dict[str, float]] = field(default_factory=list)


def advance_ticks(
    state: GameState,
    count: int = 1,
    *,
    seed: int | None = None,
    lod: LodSettings | None = None,
) -> List[TickReport]:
    """Advance ``state`` by ``count`` ticks, returning per-tick reports."""

    if count < 1:
        raise ValueError("count must be >= 1")

    rng_seed = seed if seed is not None else state.seed + state.tick
    rng = random.Random(rng_seed)
    reports: List[TickReport] = []

    scale = lod.scale if lod else 1.0
    event_budget = lod.max_events_per_tick if lod else None

    for _ in range(count):
        events: List[str] = []
        _update_resources(state, rng, events, scale)
        _update_district_modifiers(state, rng, events, scale)
        _update_environment(state, rng, events, scale)
        tick_value = state.advance_ticks(1)
        _enforce_event_budget(events, event_budget)
        reports.append(
            TickReport(
                tick=tick_value,
                events=events,
                environment=_environment_snapshot(state),
                districts=_district_snapshot(state),
            )
        )

    return reports


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _update_resources(
    state: GameState,
    rng: random.Random,
    events: List[str],
    scale: float,
) -> None:
    for district in state.city.districts:
        for stock in district.resources.values():
            midpoint = stock.capacity * 0.5
            drift = (midpoint - stock.current) * 0.05
            fluctuation = rng.uniform(-1.5, 1.5) * scale
            new_value = _clamp(stock.current + drift + fluctuation, 0, stock.capacity)
            if abs(new_value - stock.current) > 3:
                events.append(
                    f"{district.name} {stock.type} adjusted to {int(new_value)} units"
                )
            stock.current = int(new_value)


def _update_district_modifiers(
    state: GameState,
    rng: random.Random,
    events: List[str],
    scale: float,
) -> None:
    for district in state.city.districts:
        unrest_shift = rng.uniform(-0.02, 0.02) * scale
        pollution_shift = rng.uniform(-0.015, 0.015) * scale
        prosperity_shift = rng.uniform(-0.02, 0.02) * scale
        security_shift = rng.uniform(-0.02, 0.02) * scale

        district.modifiers.unrest = _clamp(district.modifiers.unrest + unrest_shift)
        district.modifiers.pollution = _clamp(
            district.modifiers.pollution + pollution_shift
        )
        district.modifiers.prosperity = _clamp(
            district.modifiers.prosperity + prosperity_shift
        )
        district.modifiers.security = _clamp(
            district.modifiers.security + security_shift
        )

        if district.modifiers.unrest > 0.75:
            events.append(f"{district.name} protests intensify")
        if district.modifiers.pollution > 0.75:
            events.append(f"{district.name} pollution spike detected")


def _update_environment(
    state: GameState,
    rng: random.Random,
    events: List[str],
    scale: float,
) -> None:
    env = state.environment
    avg_unrest = _average(d.modifiers.unrest for d in state.city.districts)
    avg_pollution = _average(d.modifiers.pollution for d in state.city.districts)

    env.unrest = _clamp(
        env.unrest + 0.05 * (avg_unrest - 0.5) + rng.uniform(-0.01, 0.01) * scale
    )
    env.pollution = _clamp(
        env.pollution
        + 0.04 * (avg_pollution - 0.5)
        + rng.uniform(-0.015, 0.015) * scale
    )
    env.stability = _clamp(env.stability - (env.unrest - 0.5) * 0.04)
    env.security = _clamp(env.security - (env.pollution - 0.5) * 0.02)

    if env.unrest > 0.7:
        events.append("Civic tension is rising across the city")
    if env.pollution > 0.7:
        events.append("Pollution breaches critical thresholds")
    if env.stability < 0.4:
        events.append("Governance stability wanes")


def _environment_snapshot(state: GameState) -> dict[str, float]:
    env = state.environment
    return {
        "stability": env.stability,
        "unrest": env.unrest,
        "pollution": env.pollution,
        "climate_risk": env.climate_risk,
        "security": env.security,
    }


def _district_snapshot(state: GameState) -> List[dict[str, float]]:
    entries: List[dict[str, float]] = []
    for district in state.city.districts:
        entries.append(
            {
                "id": district.id,
                "pollution": district.modifiers.pollution,
                "unrest": district.modifiers.unrest,
                "prosperity": district.modifiers.prosperity,
                "security": district.modifiers.security,
            }
        )
    return entries


def _average(values: Sequence[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _enforce_event_budget(events: List[str], budget: int | None) -> None:
    if budget is None or len(events) <= budget:
        return
    del events[budget:]
    events.append("Additional events suppressed by LOD budget")
