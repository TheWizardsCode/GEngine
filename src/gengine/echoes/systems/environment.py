"""Environment subsystem that reacts to scarcity signals."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

from ..core import GameState
from ..settings import EnvironmentSettings
from .economy import EconomyReport


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


@dataclass(slots=True)
class EnvironmentImpact:
    """Summarizes how scarcity influenced environment metrics."""

    scarcity_pressure: float = 0.0
    district_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "scarcity_pressure": round(self.scarcity_pressure, 4),
            "district_deltas": self.district_deltas,
            "events": self.events,
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
    ) -> EnvironmentImpact:
        if economy_report is None or not economy_report.shortages:
            return EnvironmentImpact()

        pressure = self._scarcity_pressure(economy_report)
        if pressure <= 0:
            return EnvironmentImpact()

        env = state.environment
        env.unrest = _clamp(
            env.unrest + pressure * self._settings.scarcity_unrest_weight
        )
        env.pollution = _clamp(
            env.pollution + pressure * self._settings.scarcity_pollution_weight
        )

        district_deltas: Dict[str, Dict[str, float]] = {}
        for district in state.city.districts:
            unrest_delta = pressure * self._settings.district_unrest_weight
            pollution_delta = pressure * self._settings.district_pollution_weight
            if unrest_delta:
                district.modifiers.unrest = _clamp(district.modifiers.unrest + unrest_delta)
            if pollution_delta:
                district.modifiers.pollution = _clamp(
                    district.modifiers.pollution + pollution_delta
                )
            if unrest_delta or pollution_delta:
                district_deltas[district.id] = {
                    "unrest": unrest_delta,
                    "pollution": pollution_delta,
                }

        events = []
        if pressure >= self._settings.scarcity_event_threshold:
            stressed = ", ".join(sorted(economy_report.shortages.keys()))
            events.append(f"Scarcity in {stressed} strains the city environment")

        return EnvironmentImpact(
            scarcity_pressure=pressure,
            district_deltas=district_deltas,
            events=events,
        )

    def _scarcity_pressure(self, report: EconomyReport) -> float:
        if not report.shortages:
            return 0.0
        cap = float(self._settings.scarcity_pressure_cap)
        capped = [min(float(duration), cap) / cap for duration in report.shortages.values()]
        return sum(capped)
