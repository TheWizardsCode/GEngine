"""Simple tick loop and environment updates for the Echoes prototype."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, List, Sequence

from ..core import GameState
from ..settings import LodSettings


@dataclass(slots=True)
class TickReport:
    """Structured information about a single tick advancement."""

    tick: int
    events: List[str] = field(default_factory=list)
    environment: dict[str, float] = field(default_factory=dict)
    districts: List[dict[str, float]] = field(default_factory=list)
    agent_actions: List[dict[str, Any]] = field(default_factory=list)
    faction_actions: List[dict[str, Any]] = field(default_factory=list)


def advance_ticks(
    state: GameState,
    count: int = 1,
    *,
    seed: int | None = None,
    lod: LodSettings | None = None,
    agent_system: object | None = None,
    faction_system: object | None = None,
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
        agent_intents = _run_agent_system(agent_system, state, rng)
        events.extend(_summarize_agent_actions(agent_intents))
        faction_decisions = _run_faction_system(faction_system, state, rng)
        events.extend(_summarize_faction_actions(faction_decisions))
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
                agent_actions=[action.to_report() for action in agent_intents],
                faction_actions=[action.to_report() for action in faction_decisions],
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


def _run_agent_system(agent_system: object | None, state: GameState, rng: random.Random):
    if agent_system is None:
        return []
    try:
        return agent_system.tick(state, rng=rng)
    except Exception:  # pragma: no cover - defensive safeguard
        return []


def _run_faction_system(faction_system: object | None, state: GameState, rng: random.Random):
    if faction_system is None:
        return []
    try:
        return faction_system.tick(state, rng=rng)
    except Exception:  # pragma: no cover - defensive safeguard
        return []


def _summarize_agent_actions(actions: Sequence) -> List[str]:
    summaries: List[str] = []
    for action in actions:
        agent_name = getattr(action, "agent_name", getattr(action, "agent_id", "Agent"))
        intent = getattr(action, "intent", "")
        target = getattr(action, "target_name", getattr(action, "target", ""))
        if intent == "STABILIZE_UNREST":
            summaries.append(f"{agent_name} eases unrest in {target}")
        elif intent == "SUPPORT_SECURITY":
            summaries.append(f"{agent_name} reinforces security in {target}")
        elif intent == "NEGOTIATE_FACTION":
            summaries.append(f"{agent_name} negotiates with {target}")
        elif intent == "INSPECT_DISTRICT":
            summaries.append(f"{agent_name} inspects {target}")
        elif intent == "REQUEST_REPORT":
            summaries.append(f"{agent_name} files a report on {target}")
        else:
            summaries.append(f"{agent_name} acts in {target}")
    return summaries


def _summarize_faction_actions(actions: Sequence) -> List[str]:
    summaries: List[str] = []
    for action in actions:
        name = getattr(action, "faction_name", getattr(action, "faction_id", "Faction"))
        intent = getattr(action, "action", "")
        target = getattr(action, "target_name", getattr(action, "target", "city"))
        if intent == "LOBBY_COUNCIL":
            summaries.append(f"{name} lobbies city leadership")
        elif intent == "RECRUIT_SUPPORT":
            summaries.append(f"{name} recruits new supporters")
        elif intent == "INVEST_DISTRICT":
            summaries.append(f"{name} invests in {target}")
        elif intent == "SABOTAGE_RIVAL":
            summaries.append(f"{name} undermines {target}")
        else:
            summaries.append(f"{name} acts strategically")
    return summaries
