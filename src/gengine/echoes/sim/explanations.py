"""Explanations system for queryable timelines and causal summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Sequence

from ..core import GameState


class CausalCategory(str, Enum):
    """Categories for causal events."""

    ENVIRONMENT = "environment"
    ECONOMY = "economy"
    FACTION = "faction"
    AGENT = "agent"
    DISTRICT = "district"
    STORY_SEED = "story_seed"
    POLICY = "policy"


@dataclass
class CausalEvent:
    """Represents an event in the causal chain with links to causes/effects."""

    tick: int
    category: CausalCategory
    description: str
    entity_id: str | None = None
    entity_name: str | None = None
    metric: str | None = None
    delta: float | None = None
    causes: List[str] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: Dict[str, Any] = {
            "tick": self.tick,
            "category": self.category.value,
            "description": self.description,
        }
        if self.entity_id:
            result["entity_id"] = self.entity_id
        if self.entity_name:
            result["entity_name"] = self.entity_name
        if self.metric:
            result["metric"] = self.metric
        if self.delta is not None:
            result["delta"] = round(self.delta, 4)
        if self.causes:
            result["causes"] = list(self.causes)
        if self.effects:
            result["effects"] = list(self.effects)
        if self.metadata:
            result["metadata"] = dict(self.metadata)
        return result


@dataclass
class AgentReasoningSummary:
    """Summarizes an agent's reasoning for their actions."""

    agent_id: str
    agent_name: str
    tick: int
    action: str
    target: str | None = None
    reasoning_factors: List[str] = field(default_factory=list)
    trust_changes: Dict[str, float] = field(default_factory=dict)
    needs_snapshot: Dict[str, float] = field(default_factory=dict)
    goals_active: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: Dict[str, Any] = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "tick": self.tick,
            "action": self.action,
        }
        if self.target:
            result["target"] = self.target
        if self.reasoning_factors:
            result["reasoning_factors"] = list(self.reasoning_factors)
        if self.trust_changes:
            result["trust_changes"] = {
                k: round(v, 3) for k, v in self.trust_changes.items()
            }
        if self.needs_snapshot:
            result["needs_snapshot"] = {
                k: round(v, 3) for k, v in self.needs_snapshot.items()
            }
        if self.goals_active:
            result["goals_active"] = list(self.goals_active)
        return result

    def to_summary_text(self) -> str:
        """Generate human-readable reasoning summary."""
        parts = [f"{self.agent_name} {self.action}"]
        if self.target:
            parts[0] = f"{parts[0]} targeting {self.target}"
        if self.reasoning_factors:
            factors = ", ".join(self.reasoning_factors[:3])
            parts.append(f"because {factors}")
        return " ".join(parts)


@dataclass
class TimelineEntry:
    """A single entry in the queryable timeline."""

    tick: int
    events: List[CausalEvent] = field(default_factory=list)
    agent_reasoning: List[AgentReasoningSummary] = field(default_factory=list)
    environment_snapshot: Dict[str, float] = field(default_factory=dict)
    key_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tick": self.tick,
            "events": [e.to_dict() for e in self.events],
            "agent_reasoning": [r.to_dict() for r in self.agent_reasoning],
            "environment_snapshot": dict(self.environment_snapshot),
            "key_changes": list(self.key_changes),
        }


class ExplanationsManager:
    """Tracks and queries causal relationships in the simulation."""

    def __init__(self, *, history_limit: int = 100) -> None:
        self._history_limit = max(1, history_limit)
        self._timeline: List[TimelineEntry] = []
        self._causal_index: Dict[str, List[CausalEvent]] = {}

    def record_tick(
        self,
        state: GameState,
        *,
        tick: int,
        environment_delta: Dict[str, float] | None = None,
        faction_deltas: Dict[str, float] | None = None,
        agent_actions: Sequence[Mapping[str, Any]] | None = None,
        faction_actions: Sequence[Mapping[str, Any]] | None = None,
        economy_report: Mapping[str, Any] | None = None,
        environment_impact: Mapping[str, Any] | None = None,
        director_events: Sequence[Mapping[str, Any]] | None = None,
    ) -> TimelineEntry:
        """Record a tick's events and build causal links."""
        events: List[CausalEvent] = []
        agent_reasoning: List[AgentReasoningSummary] = []
        key_changes: List[str] = []

        # Track environment changes
        env_causes: List[str] = []
        if environment_delta:
            for metric, delta in environment_delta.items():
                if abs(delta) >= 0.01:
                    direction = "increased" if delta > 0 else "decreased"
                    events.append(
                        CausalEvent(
                            tick=tick,
                            category=CausalCategory.ENVIRONMENT,
                            description=f"{metric} {direction} by {abs(delta):.3f}",
                            metric=metric,
                            delta=delta,
                        )
                    )
                    key_changes.append(f"{metric} {direction}")

        # Track economy changes
        if economy_report:
            shortages = economy_report.get("shortages") or {}
            for resource, shortage_ticks in shortages.items():
                if shortage_ticks > 0:
                    events.append(
                        CausalEvent(
                            tick=tick,
                            category=CausalCategory.ECONOMY,
                            description=f"{resource} shortage (tick {shortage_ticks})",
                            metric=resource,
                            metadata={"shortage_ticks": shortage_ticks},
                        )
                    )
                    env_causes.append(f"{resource} shortage")
            prices = economy_report.get("prices") or {}
            for resource, price in prices.items():
                if price > 1.2:
                    events.append(
                        CausalEvent(
                            tick=tick,
                            category=CausalCategory.ECONOMY,
                            description=f"{resource} price elevated ({price:.2f})",
                            metric=f"{resource}_price",
                            metadata={"price": price},
                        )
                    )

        # Track faction changes
        if faction_deltas:
            for faction_id, delta in faction_deltas.items():
                if abs(delta) >= 0.01:
                    direction = "gained" if delta > 0 else "lost"
                    faction = state.factions.get(faction_id)
                    name = faction.name if faction else faction_id
                    causes = []
                    # Link faction changes to their actions
                    if faction_actions:
                        for action in faction_actions:
                            if action.get("faction_id") == faction_id:
                                causes.append(action.get("action", "action"))
                    events.append(
                        CausalEvent(
                            tick=tick,
                            category=CausalCategory.FACTION,
                            description=f"{name} {direction} {abs(delta):.3f} legitimacy",
                            entity_id=faction_id,
                            entity_name=name,
                            metric="legitimacy",
                            delta=delta,
                            causes=causes,
                        )
                    )
                    key_changes.append(f"{name} legitimacy {direction}")

        # Track agent actions and build reasoning summaries
        if agent_actions:
            for action in agent_actions:
                agent_id = action.get("agent_id")
                agent = state.agents.get(agent_id) if agent_id else None
                agent_name = action.get("agent_name") or (agent.name if agent else agent_id)
                intent = action.get("intent", "acted")
                target = action.get("target_name") or action.get("target")

                # Build reasoning factors
                reasoning_factors = []
                if agent:
                    # Check needs that might motivate action
                    for need, value in agent.needs.items():
                        if value < 0.4:
                            reasoning_factors.append(f"low {need}")
                        elif value > 0.7:
                            reasoning_factors.append(f"high {need}")
                    # Check traits that might influence action
                    for trait, value in agent.traits.items():
                        if abs(value - 0.5) > 0.3:
                            direction = "high" if value > 0.5 else "low"
                            reasoning_factors.append(f"{direction} {trait}")

                # District context
                district_id = action.get("target")
                if district_id:
                    district = next(
                        (d for d in state.city.districts if d.id == district_id),
                        None,
                    )
                    if district:
                        if district.modifiers.unrest > 0.6:
                            reasoning_factors.append(f"unrest in {district.name}")
                        if district.modifiers.pollution > 0.6:
                            reasoning_factors.append(f"pollution in {district.name}")

                summary = AgentReasoningSummary(
                    agent_id=agent_id or "unknown",
                    agent_name=agent_name or "Agent",
                    tick=tick,
                    action=intent,
                    target=target,
                    reasoning_factors=reasoning_factors[:5],
                    needs_snapshot=dict(agent.needs) if agent else {},
                    goals_active=list(agent.goals[:3]) if agent else [],
                )
                agent_reasoning.append(summary)

                events.append(
                    CausalEvent(
                        tick=tick,
                        category=CausalCategory.AGENT,
                        description=summary.to_summary_text(),
                        entity_id=agent_id,
                        entity_name=agent_name,
                        metadata={"intent": intent, "target": target},
                    )
                )

        # Track faction actions
        if faction_actions:
            for action in faction_actions:
                faction_id = action.get("faction_id")
                faction = state.factions.get(faction_id) if faction_id else None
                faction_name = action.get("faction_name") or (faction.name if faction else faction_id)
                action_type = action.get("action", "acted")
                target = action.get("target_name") or action.get("target")

                desc = f"{faction_name} {action_type}"
                if target:
                    desc = f"{desc} targeting {target}"

                effects = []
                if action_type == "INVEST_DISTRICT":
                    effects.append("pollution relief")
                    effects.append("legitimacy gain")
                elif action_type == "SABOTAGE_RIVAL":
                    effects.append("rival legitimacy loss")
                    effects.append("pollution spike")
                elif action_type == "RECRUIT_SUPPORT":
                    effects.append("legitimacy gain")
                elif action_type == "LOBBY_COUNCIL":
                    effects.append("policy influence")

                events.append(
                    CausalEvent(
                        tick=tick,
                        category=CausalCategory.FACTION,
                        description=desc,
                        entity_id=faction_id,
                        entity_name=faction_name,
                        effects=effects,
                        metadata={"action": action_type, "target": target},
                    )
                )

        # Track environment impact (from EnvironmentSystem)
        if environment_impact:
            scarcity = environment_impact.get("scarcity_pressure", 0.0)
            if scarcity > 0.1:
                events.append(
                    CausalEvent(
                        tick=tick,
                        category=CausalCategory.ENVIRONMENT,
                        description=f"scarcity pressure at {scarcity:.2f}",
                        metric="scarcity_pressure",
                        delta=scarcity,
                        effects=["unrest increase", "pollution increase"],
                    )
                )
                env_causes.append("scarcity pressure")

            biodiversity = environment_impact.get("biodiversity") or {}
            bio_delta = biodiversity.get("delta")
            if bio_delta is not None and abs(bio_delta) >= 0.01:
                direction = "recovered" if bio_delta > 0 else "declined"
                events.append(
                    CausalEvent(
                        tick=tick,
                        category=CausalCategory.ENVIRONMENT,
                        description=f"biodiversity {direction} by {abs(bio_delta):.3f}",
                        metric="biodiversity",
                        delta=bio_delta,
                        causes=env_causes if bio_delta < 0 else [],
                    )
                )

        # Track story seed activations
        if director_events:
            for event in director_events:
                seed_id = event.get("seed_id")
                title = event.get("title") or seed_id
                district = event.get("district_id")
                stakes = event.get("stakes")
                reason = event.get("reason")

                causes = []
                if reason:
                    causes.append(reason)

                events.append(
                    CausalEvent(
                        tick=tick,
                        category=CausalCategory.STORY_SEED,
                        description=f"Story seed '{title}' activated",
                        entity_id=seed_id,
                        entity_name=title,
                        causes=causes,
                        metadata={
                            "district": district,
                            "stakes": stakes,
                            "agents": [a.get("name") for a in event.get("agents", [])],
                            "factions": [f.get("name") for f in event.get("factions", [])],
                        },
                    )
                )
                key_changes.append(f"'{title}' story activated")

        # Build environment snapshot
        env_snapshot = {
            "stability": state.environment.stability,
            "unrest": state.environment.unrest,
            "pollution": state.environment.pollution,
            "biodiversity": state.environment.biodiversity,
        }

        entry = TimelineEntry(
            tick=tick,
            events=events,
            agent_reasoning=agent_reasoning,
            environment_snapshot=env_snapshot,
            key_changes=key_changes,
        )

        # Add to timeline
        self._timeline.append(entry)
        if len(self._timeline) > self._history_limit:
            self._timeline = self._timeline[-self._history_limit:]

        # Index events by entity
        for event in events:
            if event.entity_id:
                if event.entity_id not in self._causal_index:
                    self._causal_index[event.entity_id] = []
                self._causal_index[event.entity_id].append(event)

        # Persist to state metadata
        self._persist_to_metadata(state, entry)

        return entry

    def _persist_to_metadata(self, state: GameState, entry: TimelineEntry) -> None:
        """Store explanation data in game state metadata."""
        # Store latest timeline entry
        state.metadata["explanation_timeline_latest"] = entry.to_dict()

        # Store rolling history
        history = list(state.metadata.get("explanation_timeline_history") or [])
        history.append(entry.to_dict())
        if len(history) > self._history_limit:
            history = history[-self._history_limit:]
        state.metadata["explanation_timeline_history"] = history

        # Store agent reasoning summaries
        if entry.agent_reasoning:
            summaries = [r.to_dict() for r in entry.agent_reasoning]
            state.metadata["explanation_agent_reasoning"] = summaries

    def query_timeline(self, count: int = 10) -> List[TimelineEntry]:
        """Get the most recent timeline entries."""
        return list(self._timeline[-count:])

    def query_entity(self, entity_id: str) -> List[CausalEvent]:
        """Get all events related to a specific entity."""
        return list(self._causal_index.get(entity_id, []))

    def explain_metric(
        self,
        state: GameState,
        metric: str,
        *,
        lookback: int = 10,
    ) -> Dict[str, Any]:
        """Explain why a metric changed by analyzing recent causal chains."""
        relevant_events: List[CausalEvent] = []
        metric_deltas: List[float] = []

        # Search recent timeline for related events
        for entry in self._timeline[-lookback:]:
            for event in entry.events:
                if event.metric == metric:
                    relevant_events.append(event)
                    if event.delta is not None:
                        metric_deltas.append(event.delta)
                # Also check for events that might cause this metric to change
                if metric in event.effects:
                    relevant_events.append(event)

        # Build causal chain
        causes: List[str] = []
        for event in relevant_events:
            if event.causes:
                causes.extend(event.causes)
            if event.category == CausalCategory.ECONOMY and metric in ("unrest", "stability"):
                causes.append(event.description)
            if event.category == CausalCategory.FACTION and event.delta:
                causes.append(event.description)

        # Get current value
        current_value: float | None = None
        if hasattr(state.environment, metric):
            current_value = getattr(state.environment, metric)

        total_delta = sum(metric_deltas) if metric_deltas else 0.0

        return {
            "metric": metric,
            "current_value": round(current_value, 3) if current_value is not None else None,
            "total_delta": round(total_delta, 4),
            "event_count": len(relevant_events),
            "causes": list(set(causes))[:10],
            "events": [e.to_dict() for e in relevant_events[-5:]],
        }

    def explain_faction(
        self,
        state: GameState,
        faction_id: str,
        *,
        lookback: int = 10,
    ) -> Dict[str, Any]:
        """Explain a faction's recent changes and actions."""
        faction = state.factions.get(faction_id)
        if not faction:
            return {"error": f"Unknown faction '{faction_id}'"}

        # Get faction events
        faction_events = self.query_entity(faction_id)[-lookback:]

        # Calculate legitimacy trend
        legitimacy_deltas = [
            e.delta for e in faction_events
            if e.delta is not None and e.metric == "legitimacy"
        ]
        trend = sum(legitimacy_deltas) if legitimacy_deltas else 0.0

        # Get actions
        actions = [
            e for e in faction_events
            if e.metadata.get("action")
        ]

        return {
            "faction_id": faction_id,
            "faction_name": faction.name,
            "current_legitimacy": round(faction.legitimacy, 3),
            "legitimacy_trend": round(trend, 4),
            "recent_actions": [
                {
                    "tick": e.tick,
                    "action": e.metadata.get("action"),
                    "target": e.metadata.get("target"),
                    "effects": e.effects,
                }
                for e in actions[-5:]
            ],
            "events": [e.to_dict() for e in faction_events[-5:]],
        }

    def explain_agent(
        self,
        state: GameState,
        agent_id: str,
        *,
        lookback: int = 10,
    ) -> Dict[str, Any]:
        """Explain an agent's recent actions and reasoning."""
        agent = state.agents.get(agent_id)
        if not agent:
            return {"error": f"Unknown agent '{agent_id}'"}

        # Find agent reasoning entries
        reasoning_history: List[AgentReasoningSummary] = []
        for entry in self._timeline[-lookback:]:
            for reasoning in entry.agent_reasoning:
                if reasoning.agent_id == agent_id:
                    reasoning_history.append(reasoning)

        # Build reasoning summary text
        if reasoning_history:
            latest = reasoning_history[-1]
            reasoning_text = latest.to_summary_text()
        else:
            reasoning_text = f"{agent.name} has been quiet recently"

        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "role": agent.role,
            "faction_id": agent.faction_id,
            "home_district": agent.home_district,
            "current_needs": {k: round(v, 2) for k, v in agent.needs.items()},
            "traits": {k: round(v, 2) for k, v in agent.traits.items()},
            "goals": list(agent.goals[:5]),
            "reasoning_summary": reasoning_text,
            "recent_actions": [
                {
                    "tick": r.tick,
                    "action": r.action,
                    "target": r.target,
                    "reasoning": r.reasoning_factors,
                }
                for r in reasoning_history[-5:]
            ],
        }

    def explain_district(
        self,
        state: GameState,
        district_id: str,
        *,
        lookback: int = 10,
    ) -> Dict[str, Any]:
        """Explain changes in a district."""
        district = next(
            (d for d in state.city.districts if d.id == district_id),
            None,
        )
        if not district:
            return {"error": f"Unknown district '{district_id}'"}

        # Find district-related events
        district_events: List[CausalEvent] = []
        for entry in self._timeline[-lookback:]:
            for event in entry.events:
                # Check metadata for district references
                if event.metadata.get("target") == district_id:
                    district_events.append(event)
                elif event.metadata.get("district") == district_id:
                    district_events.append(event)

        # Get story seeds affecting this district
        story_seeds = [
            e for e in district_events
            if e.category == CausalCategory.STORY_SEED
        ]

        # Get faction activities in this district
        faction_activity = [
            e for e in district_events
            if e.category == CausalCategory.FACTION
        ]

        return {
            "district_id": district_id,
            "district_name": district.name,
            "population": district.population,
            "modifiers": {
                "unrest": round(district.modifiers.unrest, 3),
                "pollution": round(district.modifiers.pollution, 3),
                "prosperity": round(district.modifiers.prosperity, 3),
                "security": round(district.modifiers.security, 3),
            },
            "story_seeds": [e.to_dict() for e in story_seeds[-3:]],
            "faction_activity": [e.to_dict() for e in faction_activity[-5:]],
            "event_count": len(district_events),
        }

    def get_why_summary(
        self,
        state: GameState,
        query: str,
    ) -> Dict[str, Any]:
        """Answer a 'why' query about the simulation state."""
        query_lower = query.lower()

        # Check for stability queries
        if "stability" in query_lower:
            explanation = self.explain_metric(state, "stability")
            causes = explanation.get("causes", [])
            if not causes:
                causes = self._infer_stability_causes(state)
            explanation["causes"] = causes
            return explanation

        # Check for unrest queries
        if "unrest" in query_lower:
            return self.explain_metric(state, "unrest")

        # Check for pollution queries
        if "pollution" in query_lower:
            return self.explain_metric(state, "pollution")

        # Check for faction queries
        for faction_id, faction in state.factions.items():
            if faction_id.lower() in query_lower or faction.name.lower() in query_lower:
                return self.explain_faction(state, faction_id)

        # Check for agent queries
        for agent_id, agent in state.agents.items():
            if agent_id.lower() in query_lower or agent.name.lower() in query_lower:
                return self.explain_agent(state, agent_id)

        # Check for district queries
        for district in state.city.districts:
            if district.id.lower() in query_lower or district.name.lower() in query_lower:
                return self.explain_district(state, district.id)

        # Default: return recent key changes
        recent_changes: List[str] = []
        for entry in self._timeline[-5:]:
            recent_changes.extend(entry.key_changes)

        return {
            "query": query,
            "matched": False,
            "suggestion": "Try asking about stability, unrest, pollution, a faction name, agent name, or district name",
            "recent_changes": recent_changes[-10:],
        }

    def _infer_stability_causes(self, state: GameState) -> List[str]:
        """Infer likely causes of stability changes from current state."""
        causes = []
        env = state.environment

        if env.unrest > 0.6:
            causes.append(f"high citywide unrest ({env.unrest:.2f})")
        if env.pollution > 0.7:
            causes.append(f"elevated pollution ({env.pollution:.2f})")
        if env.biodiversity < 0.4:
            causes.append(f"low biodiversity ({env.biodiversity:.2f})")

        # Check district conditions
        high_unrest_districts = [
            d.name for d in state.city.districts if d.modifiers.unrest > 0.7
        ]
        if high_unrest_districts:
            causes.append(f"unrest in {', '.join(high_unrest_districts[:2])}")

        # Check faction legitimacy
        for faction_id, faction in state.factions.items():
            if faction.legitimacy < 0.3:
                causes.append(f"{faction.name} legitimacy crisis ({faction.legitimacy:.2f})")
            elif faction.legitimacy > 0.8:
                causes.append(f"{faction.name} dominance ({faction.legitimacy:.2f})")

        return causes


__all__ = [
    "CausalCategory",
    "CausalEvent",
    "AgentReasoningSummary",
    "TimelineEntry",
    "ExplanationsManager",
]
