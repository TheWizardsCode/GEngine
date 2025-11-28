"""Environment subsystem that reacts to scarcity signals."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from ..core import District, GameState
from ..settings import EnvironmentSettings
from .economy import EconomyReport
from .factions import FactionAction


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass(slots=True)
class EnvironmentImpact:
    """Summarizes how scarcity influenced environment metrics."""

    scarcity_pressure: float = 0.0
    district_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    diffusion_applied: bool = False
    faction_effects: List[Dict[str, object]] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    average_pollution: float = 0.0
    extremes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    diffusion_samples: List[Dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "scarcity_pressure": round(self.scarcity_pressure, 4),
            "district_deltas": self.district_deltas,
            "diffusion_applied": self.diffusion_applied,
            "faction_effects": self.faction_effects,
            "events": self.events,
            "average_pollution": round(self.average_pollution, 4),
            "extremes": self.extremes,
            "diffusion_samples": self.diffusion_samples,
        }


class EnvironmentSystem:
    """Couples resource scarcity back into unrest/pollution loops."""

    def __init__(self, settings: EnvironmentSettings | None = None) -> None:
        self._settings = settings or EnvironmentSettings()

    def tick(
        self,
        state: GameState,
        *,
        rng: random.Random,
        economy_report: EconomyReport | None = None,
        faction_actions: Sequence[FactionAction] | None = None,
    ) -> EnvironmentImpact:
        pressure = self._scarcity_pressure(economy_report) if economy_report else 0.0
        district_deltas: Dict[str, Dict[str, float]] = {}
        events: List[str] = []

        if pressure > 0:
            self._apply_scarcity_pressure(state, pressure, district_deltas)
            if (
                economy_report
                and pressure >= self._settings.scarcity_event_threshold
                and economy_report.shortages
            ):
                stressed = ", ".join(sorted(economy_report.shortages.keys()))
                events.append(f"Scarcity in {stressed} strains the city environment")

        (
            diffusion_applied,
            average_pollution,
            extremes,
            diffusion_samples,
        ) = self._apply_diffusion(state, district_deltas)
        if diffusion_applied:
            events.append("Pollution diffuses toward the citywide baseline")

        faction_events, faction_effects = self._apply_faction_effects(
            faction_actions or [],
            state,
            district_deltas,
        )
        events.extend(faction_events)

        return EnvironmentImpact(
            scarcity_pressure=pressure,
            district_deltas=district_deltas,
            diffusion_applied=diffusion_applied,
            average_pollution=average_pollution,
            extremes=extremes,
            diffusion_samples=diffusion_samples,
            faction_effects=faction_effects,
            events=events,
        )

    def _scarcity_pressure(self, report: EconomyReport) -> float:
        if not report.shortages:
            return 0.0
        cap = float(self._settings.scarcity_pressure_cap)
        capped = [min(float(duration), cap) / cap for duration in report.shortages.values()]
        return sum(capped)

    def _apply_scarcity_pressure(
        self,
        state: GameState,
        pressure: float,
        district_deltas: Dict[str, Dict[str, float]],
    ) -> None:
        env = state.environment
        env.unrest = _clamp(
            env.unrest + pressure * self._settings.scarcity_unrest_weight
        )
        env.pollution = _clamp(
            env.pollution + pressure * self._settings.scarcity_pollution_weight
        )

        for district in state.city.districts:
            unrest_delta = pressure * self._settings.district_unrest_weight
            pollution_delta = pressure * self._settings.district_pollution_weight
            if unrest_delta:
                district.modifiers.unrest = _clamp(district.modifiers.unrest + unrest_delta)
                _record_delta(district_deltas, district.id, "unrest", unrest_delta)
            if pollution_delta:
                district.modifiers.pollution = _clamp(
                    district.modifiers.pollution + pollution_delta
                )
                _record_delta(district_deltas, district.id, "pollution", pollution_delta)

    def _apply_diffusion(
        self,
        state: GameState,
        district_deltas: Dict[str, Dict[str, float]],
    ) -> Tuple[bool, float, Dict[str, Dict[str, float]], List[Dict[str, object]]]:
        districts = state.city.districts
        if not districts:
            return False, 0.0, {}, []

        avg_pollution = sum(d.modifiers.pollution for d in districts) / len(districts)
        rate = self._settings.diffusion_rate
        if rate <= 0:
            return False, avg_pollution, _pollution_extremes(districts), []

        neighbor_bias = _clamp(self._settings.diffusion_neighbor_bias, 0.0, 1.0)
        min_delta = max(self._settings.diffusion_min_delta, 0.0)
        max_delta = max(self._settings.diffusion_max_delta, 0.0)
        lookup = {district.id: district for district in districts}
        applied = False
        top_deltas: List[Tuple[float, Dict[str, object]]] = []

        for district in districts:
            neighbor_avg = _neighbor_average(district, lookup)
            target = avg_pollution
            if neighbor_avg is not None:
                target = (neighbor_bias * neighbor_avg) + ((1.0 - neighbor_bias) * avg_pollution)
            delta = (target - district.modifiers.pollution) * rate
            if abs(delta) < min_delta:
                continue
            applied = True
            if max_delta > 0:
                capped = min(abs(delta), max_delta)
                delta = capped if delta >= 0 else -capped
            district.modifiers.pollution = _clamp(district.modifiers.pollution + delta)
            _record_delta(district_deltas, district.id, "pollution", delta)
            top_deltas.append(
                (
                    abs(delta),
                    {
                        "district_id": district.id,
                        "delta": round(delta, 6),
                        "target": round(target, 4),
                        "neighbor_avg": None
                        if neighbor_avg is None
                        else round(neighbor_avg, 4),
                    },
                )
            )

        samples = [entry for _, entry in sorted(top_deltas, key=lambda item: item[0], reverse=True)[:3]]
        avg_pollution = sum(d.modifiers.pollution for d in districts) / len(districts)
        extremes = _pollution_extremes(districts)
        return applied, avg_pollution, extremes, samples

    def _apply_faction_effects(
        self,
        faction_actions: Sequence[FactionAction],
        state: GameState,
        district_deltas: Dict[str, Dict[str, float]],
    ) -> Tuple[List[str], List[Dict[str, object]]]:
        if not faction_actions:
            return [], []
        districts = {district.id: district for district in state.city.districts}
        events: List[str] = []
        effects: List[Dict[str, object]] = []
        for action in faction_actions:
            district_id = getattr(action, "district_id", None)
            if not district_id:
                continue
            district = districts.get(district_id)
            if district is None:
                continue
            if action.action == "INVEST_DISTRICT":
                delta = -self._settings.faction_invest_pollution_relief
                descriptor = "mitigates"
            elif action.action == "SABOTAGE_RIVAL":
                delta = self._settings.faction_sabotage_pollution_spike
                descriptor = "exacerbates"
            else:
                continue
            district.modifiers.pollution = _clamp(district.modifiers.pollution + delta)
            _record_delta(district_deltas, district.id, "pollution", delta)
            effects.append(
                {
                    "faction": action.faction_name,
                    "action": action.action,
                    "district": district.id,
                    "pollution_delta": round(delta, 4),
                }
            )
            verb = "relief" if delta < 0 else "surge"
            events.append(
                f"{action.faction_name} {descriptor} pollution in {district.name} ({verb})"
            )
        return events, effects


def _record_delta(
    container: Dict[str, Dict[str, float]],
    district_id: str,
    metric: str,
    delta: float,
) -> None:
    if abs(delta) < 1e-6:
        return
    entry = container.setdefault(district_id, {})
    entry[metric] = round(entry.get(metric, 0.0) + delta, 6)


def _neighbor_average(district: District, lookup: Dict[str, District]) -> float | None:
    neighbors = [lookup[neighbor] for neighbor in district.adjacent if neighbor in lookup]
    if not neighbors:
        return None
    return sum(neighbor.modifiers.pollution for neighbor in neighbors) / len(neighbors)


def _pollution_extremes(districts: Sequence[District]) -> Dict[str, Dict[str, float]]:
    if not districts:
        return {}
    max_district = max(districts, key=lambda d: d.modifiers.pollution)
    min_district = min(districts, key=lambda d: d.modifiers.pollution)
    return {
        "max": {
            "district": max_district.id,
            "pollution": round(max_district.modifiers.pollution, 4),
        },
        "min": {
            "district": min_district.id,
            "pollution": round(min_district.modifiers.pollution, 4),
        },
    }
