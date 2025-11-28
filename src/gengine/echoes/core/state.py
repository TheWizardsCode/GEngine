"""Game state container and serialization helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field

from .models import Agent, City, EnvironmentState, Faction


class GameState(BaseModel):
    """Represents the full simulation state at a point in time."""

    city: City
    factions: Dict[str, Faction] = Field(default_factory=dict)
    agents: Dict[str, Agent] = Field(default_factory=dict)
    environment: EnvironmentState = Field(default_factory=EnvironmentState)
    tick: int = Field(default=0, ge=0)
    seed: int = Field(default=0, ge=0)
    version: str = Field(default="0.1.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": False,
    }

    def advance_ticks(self, count: int = 1) -> int:
        """Advance simulation time by ``count`` ticks and return the new tick."""

        if count < 0:
            raise ValueError("tick count must be non-negative")
        self.tick += count
        return self.tick

    def summary(self) -> Dict[str, Any]:
        """Return a lightweight summary useful for CLI/debug output."""

        summary = {
            "city": self.city.name,
            "tick": self.tick,
            "districts": len(self.city.districts),
            "factions": len(self.factions),
            "agents": len(self.agents),
            "stability": self.environment.stability,
        }
        summary["faction_legitimacy"] = {
            faction_id: round(faction.legitimacy, 3)
            for faction_id, faction in self.factions.items()
        }
        return summary

    def snapshot(self) -> Dict[str, Any]:
        """Serialize the entire game state into a JSON-friendly dict."""

        return self.model_dump()

    @classmethod
    def from_snapshot(cls, payload: Dict[str, Any]) -> "GameState":
        """Rehydrate a :class:`GameState` from ``snapshot()`` output."""

        return cls.model_validate(payload)
