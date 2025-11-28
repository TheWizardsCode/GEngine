"""Simulation engine abstraction for Echoes of Emergence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

from ..content import load_world_bundle
from ..core import GameState
from ..persistence import load_snapshot
from .tick import TickReport, advance_ticks as _advance_ticks

ViewName = Literal["summary", "snapshot", "district"]


class EngineNotInitializedError(RuntimeError):
    """Raised when engine operations run without initialized state."""


class SimEngine:
    """Thin façade that will back both in-process and service deployments."""

    def __init__(self, state: GameState | None = None) -> None:
        self._state = state

    # ------------------------------------------------------------------
    @property
    def state(self) -> GameState:
        if self._state is None:
            raise EngineNotInitializedError("SimEngine state is not initialized")
        return self._state

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

        return _advance_ticks(self.state, count, seed=seed)

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