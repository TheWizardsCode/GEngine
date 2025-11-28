"""Tick orchestration and subsystem telemetry for the Echoes prototype."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, List, Sequence

from ..core import GameState
from ..settings import LodSettings, ProfilingSettings
from .director import DirectorBridge, NarrativeDirector
from .focus import FocusBudgetResult, FocusManager, NarrativeEvent


logger = logging.getLogger("gengine.echoes.sim.tick")


@dataclass(slots=True)
class TickReport:
    """Structured information about a single tick advancement."""

    tick: int
    events: List[str] = field(default_factory=list)
    event_archive: List[str] = field(default_factory=list)
    suppressed_events: List[str] = field(default_factory=list)
    environment: dict[str, float] = field(default_factory=dict)
    districts: List[dict[str, float]] = field(default_factory=list)
    agent_actions: List[dict[str, Any]] = field(default_factory=list)
    faction_actions: List[dict[str, Any]] = field(default_factory=list)
    faction_legitimacy: Dict[str, float] = field(default_factory=dict)
    faction_legitimacy_delta: Dict[str, float] = field(default_factory=dict)
    economy: Dict[str, Any] = field(default_factory=dict)
    environment_impact: Dict[str, Any] = field(default_factory=dict)
    timings: Dict[str, float] = field(default_factory=dict)
    focus_budget: Dict[str, Any] = field(default_factory=dict)
    director_snapshot: Dict[str, Any] = field(default_factory=dict)
    director_analysis: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[str] = field(default_factory=list)


class TickCoordinator:
    """Coordinates subsystem execution order and diagnostics per tick."""

    def __init__(
        self,
        *,
        agent_system: object | None = None,
        faction_system: object | None = None,
        economy_system: object | None = None,
        environment_system: object | None = None,
        focus_manager: FocusManager | None = None,
        director_bridge: DirectorBridge | None = None,
        narrative_director: NarrativeDirector | None = None,
    ) -> None:
        self._agent_system = agent_system
        self._faction_system = faction_system
        self._economy_system = economy_system
        self._environment_system = environment_system
        self._focus_manager = focus_manager or FocusManager()
        self._director_bridge = director_bridge
        self._narrative_director = narrative_director

    def run(
        self,
        state: GameState,
        count: int = 1,
        *,
        seed: int | None = None,
        lod: LodSettings | None = None,
        profiling: ProfilingSettings | None = None,
    ) -> List[TickReport]:
        if count < 1:
            raise ValueError("count must be >= 1")

        rng_seed = seed if seed is not None else state.seed + state.tick
        rng = random.Random(rng_seed)
        scale = lod.scale if lod else 1.0
        event_budget = lod.max_events_per_tick if lod else None
        capture_timings = profiling.capture_subsystems if profiling is not None else True

        reports: List[TickReport] = []
        for _ in range(count):
            reports.append(
                self._execute_tick(
                    state,
                    rng,
                    scale=scale,
                    event_budget=event_budget,
                    capture_timings=capture_timings,
                    focus_manager=self._focus_manager,
                    director_bridge=self._director_bridge,
                    narrative_director=self._narrative_director,
                )
            )
        return reports

    def _execute_tick(
        self,
        state: GameState,
        rng: random.Random,
        *,
        scale: float,
        event_budget: int | None,
        capture_timings: bool,
        focus_manager: FocusManager,
        director_bridge: DirectorBridge | None,
        narrative_director: NarrativeDirector | None,
    ) -> TickReport:
        tick_start = perf_counter()
        timings: Dict[str, float] = {}
        event_entries: List[NarrativeEvent] = []
        anomalies: List[str] = []
        prev_legitimacy = {
            faction_id: faction.legitimacy for faction_id, faction in state.factions.items()
        }

        agent_intents = self._invoke_subsystem(
            "agent",
            self._agent_system,
            default=[],
            timings=timings,
            capture_timings=capture_timings,
            anomalies=anomalies,
            state=state,
            rng=rng,
        )
        district_ids = {district.id for district in state.city.districts}
        event_entries.extend(_summarize_agent_actions(agent_intents, district_ids))

        faction_decisions = self._invoke_subsystem(
            "faction",
            self._faction_system,
            default=[],
            timings=timings,
            capture_timings=capture_timings,
            anomalies=anomalies,
            state=state,
            rng=rng,
        )
        event_entries.extend(_summarize_faction_actions(faction_decisions))

        economy_report = self._invoke_subsystem(
            "economy",
            self._economy_system,
            default=None,
            timings=timings,
            capture_timings=capture_timings,
            anomalies=anomalies,
            state=state,
            rng=rng,
        )
        event_entries.extend(_summarize_economy(economy_report))

        segment_start = perf_counter()
        _update_resources(state, rng, event_entries, scale)
        if capture_timings:
            timings["resources_ms"] = (perf_counter() - segment_start) * 1000

        segment_start = perf_counter()
        _update_district_modifiers(state, rng, event_entries, scale)
        if capture_timings:
            timings["district_ms"] = (perf_counter() - segment_start) * 1000

        env_result = self._invoke_subsystem(
            "environment_system",
            self._environment_system,
            default=None,
            timings=timings,
            capture_timings=capture_timings,
            anomalies=anomalies,
            state=state,
            rng=rng,
            economy_report=economy_report,
            faction_actions=faction_decisions,
        )
        impact_payload: Dict[str, Any] = {}
        if env_result is not None:
            if getattr(env_result, "events", None):
                event_entries.extend(
                    NarrativeEvent(message, None, "environment") for message in env_result.events
                )
            if hasattr(env_result, "to_dict"):
                impact_payload = env_result.to_dict()
                state.metadata["environment_impact"] = impact_payload
        elif "environment_impact" in state.metadata:
            impact_payload = state.metadata["environment_impact"]

        segment_start = perf_counter()
        _update_environment(state, rng, event_entries, scale)
        if capture_timings:
            timings["environment_ms"] = (perf_counter() - segment_start) * 1000

        focus_result = focus_manager.curate(state, event_entries, event_budget=event_budget)
        visible_events = [entry.to_display() for entry in focus_result.visible]
        archive_events = [entry.to_display() for entry in focus_result.archive]
        suppressed_events = [entry.to_display() for entry in focus_result.suppressed]

        tick_value = state.advance_ticks(1)
        focus_manager.record_digest(state, tick=tick_value, result=focus_result)
        director_snapshot: Dict[str, Any] = {}
        if director_bridge is not None:
            director_snapshot = director_bridge.record(
                state,
                tick=tick_value,
                focus_result=focus_result,
            )
        director_analysis: Dict[str, Any] = {}
        if narrative_director is not None:
            director_analysis = narrative_director.evaluate(state, director_snapshot)

        timings["tick_total_ms"] = (perf_counter() - tick_start) * 1000
        return TickReport(
            tick=tick_value,
            events=visible_events,
            event_archive=archive_events,
            suppressed_events=suppressed_events,
            environment=_environment_snapshot(state),
            districts=_district_snapshot(state),
            agent_actions=[action.to_report() for action in agent_intents],
            faction_actions=[action.to_report() for action in faction_decisions],
            faction_legitimacy=_legitimacy_snapshot(state),
            faction_legitimacy_delta=_legitimacy_delta(prev_legitimacy, state),
            economy=economy_report.to_dict() if economy_report else {},
            environment_impact=impact_payload,
            timings=timings,
            focus_budget=focus_result.allocation,
            director_snapshot=director_snapshot,
            director_analysis=director_analysis,
            anomalies=anomalies,
        )

    def _invoke_subsystem(
        self,
        label: str,
        system: object | None,
        *,
        default: Any,
        timings: Dict[str, float],
        capture_timings: bool,
        anomalies: List[str],
        **kwargs: Any,
    ) -> Any:
        if system is None:
            return default
        segment_start = perf_counter()
        try:
            return system.tick(**kwargs)
        except Exception as exc:  # pragma: no cover - defensive safeguard
            anomalies.append(f"{label}_error")
            logger.exception("%s system failed", label)
            return default
        finally:
            if capture_timings:
                timings[f"{label}_ms"] = (perf_counter() - segment_start) * 1000


def advance_ticks(
    state: GameState,
    count: int = 1,
    *,
    seed: int | None = None,
    lod: LodSettings | None = None,
    agent_system: object | None = None,
    faction_system: object | None = None,
    economy_system: object | None = None,
    environment_system: object | None = None,
    profiling: ProfilingSettings | None = None,
    focus_manager: FocusManager | None = None,
    director_bridge: DirectorBridge | None = None,
    narrative_director: NarrativeDirector | None = None,
) -> List[TickReport]:
    """Advance ``state`` by ``count`` ticks, returning per-tick reports."""

    coordinator = TickCoordinator(
        agent_system=agent_system,
        faction_system=faction_system,
        economy_system=economy_system,
        environment_system=environment_system,
        focus_manager=focus_manager,
        director_bridge=director_bridge,
        narrative_director=narrative_director,
    )
    return coordinator.run(
        state,
        count=count,
        seed=seed,
        lod=lod,
        profiling=profiling,
    )


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _update_resources(
    state: GameState,
    rng: random.Random,
    events: List[NarrativeEvent],
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
                    NarrativeEvent(
                        f"{district.name} {stock.type} adjusted to {int(new_value)} units",
                        district_id=district.id,
                        scope="resources",
                    )
                )
            stock.current = int(new_value)


def _update_district_modifiers(
    state: GameState,
    rng: random.Random,
    events: List[NarrativeEvent],
    scale: float,
) -> None:
    for district in state.city.districts:
        district.modifiers.unrest = _mean_revert(
            district.modifiers.unrest,
            rng.uniform(-0.02, 0.02),
            scale,
            drift=0.2,
        )
        district.modifiers.pollution = _mean_revert(
            district.modifiers.pollution,
            rng.uniform(-0.015, 0.015),
            scale,
            drift=0.18,
        )
        district.modifiers.prosperity = _mean_revert(
            district.modifiers.prosperity,
            rng.uniform(-0.02, 0.02),
            scale,
            drift=0.12,
        )
        district.modifiers.security = _mean_revert(
            district.modifiers.security,
            rng.uniform(-0.02, 0.02),
            scale,
            drift=0.12,
        )

        if district.modifiers.unrest > 0.75:
            events.append(
                NarrativeEvent(
                    f"{district.name} protests intensify",
                    district_id=district.id,
                    scope="district",
                )
            )
        if district.modifiers.pollution > 0.75:
            events.append(
                NarrativeEvent(
                    f"{district.name} pollution spike detected",
                    district_id=district.id,
                    scope="district",
                )
            )


def _update_environment(
    state: GameState,
    rng: random.Random,
    events: List[NarrativeEvent],
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
    env.stability = _clamp(env.stability - (env.unrest - 0.5) * 0.02)
    env.security = _clamp(env.security - (env.pollution - 0.5) * 0.02)

    if env.unrest > 0.7:
        events.append(
            NarrativeEvent("Civic tension is rising across the city", scope="environment")
        )
    if env.pollution > 0.7:
        events.append(
            NarrativeEvent("Pollution breaches critical thresholds", scope="environment")
        )
    if env.stability < 0.4:
        events.append(NarrativeEvent("Governance stability wanes", scope="environment"))


def _environment_snapshot(state: GameState) -> dict[str, float]:
    env = state.environment
    return {
        "stability": env.stability,
        "unrest": env.unrest,
        "pollution": env.pollution,
        "climate_risk": env.climate_risk,
        "security": env.security,
    }


def _district_snapshot(state: GameState) -> List[dict[str, object]]:
    entries: List[dict[str, object]] = []
    for district in state.city.districts:
        entries.append(
            {
                "id": district.id,
                "pollution": district.modifiers.pollution,
                "unrest": district.modifiers.unrest,
                "prosperity": district.modifiers.prosperity,
                "security": district.modifiers.security,
                "adjacent": list(district.adjacent),
                "coordinates": district.coordinates.model_dump() if district.coordinates else None,
            }
        )
    return entries


def _average(values: Sequence[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _mean_revert(value: float, noise: float, scale: float, *, drift: float) -> float:
    """Noise plus drift back toward the neutral 0.5 midpoint."""

    return _clamp(value + (0.5 - value) * drift + noise * scale)


def _summarize_agent_actions(actions: Sequence, district_ids: set[str]) -> List[NarrativeEvent]:
    summaries: List[NarrativeEvent] = []
    for action in actions:
        agent_name = getattr(action, "agent_name", getattr(action, "agent_id", "Agent"))
        intent = getattr(action, "intent", "")
        target = getattr(action, "target_name", getattr(action, "target", ""))
        district_id = getattr(action, "target", None)
        if district_id not in district_ids:
            district_id = None
        if intent == "STABILIZE_UNREST":
            message = f"{agent_name} eases unrest in {target}"
        elif intent == "SUPPORT_SECURITY":
            message = f"{agent_name} reinforces security in {target}"
        elif intent == "NEGOTIATE_FACTION":
            message = f"{agent_name} negotiates with {target}"
        elif intent == "INSPECT_DISTRICT":
            message = f"{agent_name} inspects {target}"
        elif intent == "REQUEST_REPORT":
            message = f"{agent_name} files a report on {target}"
        else:
            message = f"{agent_name} acts in {target}"
        summaries.append(NarrativeEvent(message, district_id=district_id, scope="agent"))
    return summaries


def _summarize_faction_actions(actions: Sequence) -> List[NarrativeEvent]:
    summaries: List[NarrativeEvent] = []
    for action in actions:
        name = getattr(action, "faction_name", getattr(action, "faction_id", "Faction"))
        intent = getattr(action, "action", "")
        target = getattr(action, "target_name", getattr(action, "target", "city"))
        district_id = getattr(action, "district_id", None)
        if intent == "LOBBY_COUNCIL":
            message = f"{name} lobbies city leadership"
        elif intent == "RECRUIT_SUPPORT":
            message = f"{name} recruits new supporters"
        elif intent == "INVEST_DISTRICT":
            message = f"{name} invests in {target}"
        elif intent == "SABOTAGE_RIVAL":
            message = f"{name} undermines {target}"
        else:
            message = f"{name} acts strategically"
        summaries.append(NarrativeEvent(message, district_id=district_id, scope="faction"))
    return summaries


def _summarize_economy(report) -> List[NarrativeEvent]:
    if report is None:
        return []
    lines: List[NarrativeEvent] = []
    for resource, ticks in report.shortages.items():
        lines.append(
            NarrativeEvent(
                f"Economy alert: {resource} shortage persists for {ticks} ticks",
                scope="economy",
            )
        )
    return lines


def _legitimacy_snapshot(state: GameState) -> Dict[str, float]:
    return {faction_id: round(faction.legitimacy, 4) for faction_id, faction in state.factions.items()}


def _legitimacy_delta(previous: Dict[str, float], state: GameState) -> Dict[str, float]:
    deltas: Dict[str, float] = {}
    for faction_id, faction in state.factions.items():
        before = previous.get(faction_id, faction.legitimacy)
        change = round(faction.legitimacy - before, 4)
        if change:
            deltas[faction_id] = change
    return deltas
