"""Simulation engine abstraction for Echoes of Emergence."""

from __future__ import annotations

import logging
from collections import deque
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Deque, Literal, Sequence

from ..content import load_world_bundle
from ..core import GameState
from ..persistence import load_snapshot
from ..settings import SimulationConfig, load_simulation_config
from ..systems import AgentSystem, EconomySystem, EnvironmentSystem, FactionSystem
from .tick import TickReport, advance_ticks as _advance_ticks

ViewName = Literal["summary", "snapshot", "district"]


class EngineNotInitializedError(RuntimeError):
    """Raised when engine operations run without initialized state."""


logger = logging.getLogger("gengine.echoes.sim")


class SimEngine:
    """Thin façade that will back both in-process and service deployments."""

    def __init__(
        self,
        state: GameState | None = None,
        *,
        config: SimulationConfig | None = None,
    ) -> None:
        self._state = state
        self._config = config or load_simulation_config()
        self._agent_system = AgentSystem()
        self._faction_system = FactionSystem()
        self._economy_system = EconomySystem(settings=self._config.economy)
        self._environment_system = EnvironmentSystem(settings=self._config.environment)
        self._tick_history: Deque[float] = deque(maxlen=self._config.profiling.history_window)

    # ------------------------------------------------------------------
    @property
    def state(self) -> GameState:
        if self._state is None:
            raise EngineNotInitializedError("SimEngine state is not initialized")
        return self._state

    @property
    def config(self) -> SimulationConfig:
        return self._config

    # ------------------------------------------------------------------
    def initialize_state(
        self,
        *,
        state: GameState | None = None,
        world: str | None = None,
        snapshot: Path | None = None,
    ) -> GameState:
        """Load authored content, snapshot, or adopt a provided GameState."""

        if state is not None:
            self._state = state
        elif snapshot is not None:
            self._state = load_snapshot(snapshot)
        elif world is not None:
            self._state = load_world_bundle(world_name=world)
        else:
            raise ValueError("Provide state, world, or snapshot to initialize")
        return self.state

    # ------------------------------------------------------------------
    def advance_ticks(self, count: int = 1, *, seed: int | None = None) -> Sequence[TickReport]:
        """Advance simulation time by ``count`` ticks using the tick driver."""

        limit = self._config.limits.engine_max_ticks
        if count > limit:
            raise ValueError(
                f"Requested {count} ticks exceeds engine limit of {limit}"
            )

        start = perf_counter()
        reports = _advance_ticks(
            self.state,
            count,
            seed=seed,
            lod=self._config.lod,
            agent_system=self._agent_system,
            faction_system=self._faction_system,
            economy_system=self._economy_system,
            environment_system=self._environment_system,
            profiling=self._config.profiling,
        )
        duration_ms = (perf_counter() - start) * 1000
        self._record_profiling(reports)
        if self._config.profiling.log_ticks:
            logger.info(
                "ticks=%s duration_ms=%.2f lod=%s",
                len(reports),
                duration_ms,
                self._config.lod.mode,
            )
        return reports

    # ------------------------------------------------------------------
    def apply_action(self, action: dict[str, Any] | None = None) -> dict[str, Any]:
        """Placeholder for structured intents; returns a no-op receipt."""

        return {
            "status": "noop",
            "detail": "Action handling is not implemented yet",
            "received": action or {},
        }

    # ------------------------------------------------------------------
    def query_view(self, view: ViewName = "summary", **kwargs: Any) -> Any:
        """Return a lightweight representation of the current state."""

        if view == "summary":
            return self.state.summary()
        if view == "snapshot":
            return self.state.snapshot()
        if view == "district":
            return self._district_view(kwargs.get("district_id"))
        raise ValueError(f"Unknown view '{view}'")

    # Internal helpers --------------------------------------------------
    def _record_profiling(self, reports: Sequence[TickReport]) -> None:
        if not reports:
            return
        history_updated = False
        for report in reports:
            total = report.timings.get("tick_total_ms")
            if total is None:
                continue
            self._tick_history.append(total)
            history_updated = True
        if not history_updated or not self._tick_history:
            return
        history_values = list(self._tick_history)
        profiling_payload = {
            "tick_ms_p50": round(self._percentile(history_values, 50), 2),
            "tick_ms_p95": round(self._percentile(history_values, 95), 2),
            "tick_ms_max": round(max(history_values), 2),
            "history_len": len(history_values),
            "last_tick_ms": round(reports[-1].timings.get("tick_total_ms", 0.0), 2),
        }
        last_subsystems = {
            key: round(value, 2)
            for key, value in reports[-1].timings.items()
            if key != "tick_total_ms"
        }
        slowest_entry: dict[str, float] | None = None
        if last_subsystems:
            profiling_payload["last_subsystem_ms"] = last_subsystems
            slowest_name, slowest_value = max(last_subsystems.items(), key=lambda item: item[1])
            slowest_entry = {
                "name": slowest_name,
                "ms": slowest_value,
            }
        profiling_payload["slowest_subsystem"] = slowest_entry
        profiling_payload["anomalies"] = list(reports[-1].anomalies)
        self.state.metadata["profiling"] = profiling_payload

    @staticmethod
    def _percentile(values: Sequence[float], percentile: float) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return values[0]
        sorted_vals = sorted(values)
        rank = (len(sorted_vals) - 1) * (percentile / 100)
        lower = math.floor(rank)
        upper = math.ceil(rank)
        if lower == upper:
            return sorted_vals[int(rank)]
        lower_value = sorted_vals[lower]
        upper_value = sorted_vals[upper]
        return lower_value + (upper_value - lower_value) * (rank - lower)

    def _district_view(self, district_id: str | None) -> dict[str, Any]:
        if not district_id:
            raise ValueError("district view requires 'district_id'")
        for district in self.state.city.districts:
            if district.id == district_id:
                return {
                    "id": district.id,
                    "name": district.name,
                    "population": district.population,
                    "modifiers": district.modifiers.model_dump(),
                }
        raise ValueError(f"Unknown district '{district_id}'")