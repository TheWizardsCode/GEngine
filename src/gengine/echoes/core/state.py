"""Game state container and serialization helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .models import Agent, City, EnvironmentState, Faction, StorySeed
from .progression import AgentProgressionState, AgentSpecialization, ProgressionState


class GameState(BaseModel):
    """Represents the full simulation state at a point in time."""

    city: City
    factions: Dict[str, Faction] = Field(default_factory=dict)
    agents: Dict[str, Agent] = Field(default_factory=dict)
    story_seeds: Dict[str, StorySeed] = Field(default_factory=dict)
    environment: EnvironmentState = Field(default_factory=EnvironmentState)
    progression: Optional[ProgressionState] = Field(default=None)
    agent_progression: Dict[str, AgentProgressionState] = Field(default_factory=dict)
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

    def ensure_progression(self) -> ProgressionState:
        """Ensure progression state exists and return it."""
        if self.progression is None:
            self.progression = ProgressionState()
        return self.progression

    def ensure_agent_progression(
        self,
        agent_id: str,
        specialization: AgentSpecialization | None = None,
    ) -> AgentProgressionState:
        """Ensure per-agent progression state exists and return it.

        If no specialization is provided and a new state needs to be created,
        defaults to INVESTIGATOR.
        """
        if agent_id not in self.agent_progression:
            spec = specialization or AgentSpecialization.INVESTIGATOR
            self.agent_progression[agent_id] = AgentProgressionState(
                agent_id=agent_id,
                specialization=spec,
            )
        return self.agent_progression[agent_id]

    def get_agent_progression(
        self, agent_id: str
    ) -> Optional[AgentProgressionState]:
        """Get per-agent progression state if it exists, otherwise None."""
        return self.agent_progression.get(agent_id)

    def agent_progression_summary(self) -> Dict[str, object]:
        """Return a summary of all agent progression states."""
        return {
            agent_id: state.summary()
            for agent_id, state in self.agent_progression.items()
        }

    def summary(self) -> Dict[str, Any]:
        """Return a lightweight summary useful for CLI/debug output."""

        summary: Dict[str, Any] = {
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
        # Include progression summary if it exists
        if self.progression is not None:
            summary["progression"] = self.progression.summary()
        # Include agent progression summaries if any exist
        if self.agent_progression:
            summary["agent_progression"] = self.agent_progression_summary()
        market = self.metadata.get("market_prices") or {}
        if market:
            summary["market_prices"] = {
                resource: round(price, 3) for resource, price in market.items()
            }
        env_impact = self.metadata.get("environment_impact") or {}
        if env_impact:
            summary["environment_impact"] = env_impact
        profiling = self.metadata.get("profiling") or {}
        if profiling:
            summary["profiling"] = profiling
        focus_state = self.metadata.get("focus_state") or {}
        if focus_state:
            summary["focus"] = focus_state
        focus_digest = self.metadata.get("focus_digest") or {}
        if focus_digest:
            summary["focus_digest"] = focus_digest
        focus_history = self.metadata.get("focus_history") or []
        if focus_history:
            summary["focus_history"] = focus_history
        director_feed = self.metadata.get("director_feed") or {}
        if director_feed:
            summary["director_feed"] = director_feed
        director_history = self.metadata.get("director_history") or []
        if director_history:
            summary["director_history"] = director_history
        director_analysis = self.metadata.get("director_analysis") or {}
        if director_analysis:
            summary["director_analysis"] = director_analysis
        director_events = self.metadata.get("director_events") or []
        if director_events:
            summary["director_events"] = director_events
        director_pacing = self.metadata.get("director_pacing") or {}
        if director_pacing:
            summary["director_pacing"] = director_pacing
        quiet_until = self.metadata.get("director_quiet_until")
        if isinstance(quiet_until, (int, float)) and quiet_until > self.tick:
            summary["director_quiet_until"] = int(quiet_until)
        story_seeds = self.metadata.get("story_seeds_active") or []
        if story_seeds:
            summary["story_seeds"] = story_seeds
        lifecycle = self.metadata.get("story_seed_lifecycle") or {}
        if lifecycle:
            summary["story_seed_lifecycle"] = lifecycle
        lifecycle_history = self.metadata.get("story_seed_lifecycle_history") or []
        if lifecycle_history:
            summary["story_seed_lifecycle_history"] = lifecycle_history
        post_mortem = self.metadata.get("post_mortem") or {}
        if post_mortem:
            summary["post_mortem"] = post_mortem
        # M7.2 Explanations data
        explanation_timeline = self.metadata.get("explanation_timeline_history") or []
        if explanation_timeline:
            summary["explanation_timeline_history"] = explanation_timeline[-10:]
        agent_reasoning = self.metadata.get("explanation_agent_reasoning") or []
        if agent_reasoning:
            summary["explanation_agent_reasoning"] = agent_reasoning
        return summary

    def snapshot(self) -> Dict[str, Any]:
        """Serialize the entire game state into a JSON-friendly dict."""

        return self.model_dump()

    @classmethod
    def from_snapshot(cls, payload: Dict[str, Any]) -> "GameState":
        """Rehydrate a :class:`GameState` from ``snapshot()`` output."""

        return cls.model_validate(payload)
