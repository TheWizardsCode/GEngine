"""Explanation system for tracking causal chains and actor reasoning.

This module provides tools to answer "why did this happen?" questions by:
- Tracking causal relationships between events
- Recording agent/faction decision reasoning
- Building queryable timelines with causality links
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..core import GameState


@dataclass(slots=True)
class CausalEvent:
    """An event with tracked causality information."""

    tick: int
    event_id: str
    message: str
    scope: str
    actor_id: str | None = None
    actor_name: str | None = None
    actor_type: str | None = None  # "agent", "faction", "system"
    target_id: str | None = None
    target_name: str | None = None
    district_id: str | None = None
    causes: List[str] = field(default_factory=list)  # event_ids that caused this
    reasoning: str | None = None
    outcome: str | None = None
    metrics_snapshot: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary for storage/display."""
        return {
            "tick": self.tick,
            "event_id": self.event_id,
            "message": self.message,
            "scope": self.scope,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "actor_type": self.actor_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "district_id": self.district_id,
            "causes": list(self.causes),
            "reasoning": self.reasoning,
            "outcome": self.outcome,
            "metrics_snapshot": dict(self.metrics_snapshot),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CausalEvent":
        """Rehydrate from dictionary."""
        return cls(
            tick=int(data.get("tick", 0)),
            event_id=str(data.get("event_id", "")),
            message=str(data.get("message", "")),
            scope=str(data.get("scope", "system")),
            actor_id=data.get("actor_id"),
            actor_name=data.get("actor_name"),
            actor_type=data.get("actor_type"),
            target_id=data.get("target_id"),
            target_name=data.get("target_name"),
            district_id=data.get("district_id"),
            causes=list(data.get("causes") or []),
            reasoning=data.get("reasoning"),
            outcome=data.get("outcome"),
            metrics_snapshot=dict(data.get("metrics_snapshot") or {}),
        )


@dataclass(slots=True)
class ActorReasoning:
    """Captures decision-making rationale for an actor."""

    tick: int
    actor_id: str
    actor_name: str
    actor_type: str  # "agent" or "faction"
    decision: str
    options_considered: List[Dict[str, Any]] = field(default_factory=list)
    chosen_option: str | None = None
    score: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tick": self.tick,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "actor_type": self.actor_type,
            "decision": self.decision,
            "options_considered": list(self.options_considered),
            "chosen_option": self.chosen_option,
            "score": round(self.score, 4),
            "context": dict(self.context),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActorReasoning":
        """Rehydrate from dictionary."""
        return cls(
            tick=int(data.get("tick", 0)),
            actor_id=str(data.get("actor_id", "")),
            actor_name=str(data.get("actor_name", "")),
            actor_type=str(data.get("actor_type", "agent")),
            decision=str(data.get("decision", "")),
            options_considered=list(data.get("options_considered") or []),
            chosen_option=data.get("chosen_option"),
            score=float(data.get("score", 0.0)),
            context=dict(data.get("context") or {}),
        )


class ExplanationTracker:
    """Tracks causal events and reasoning for queryable explanations."""

    def __init__(self, *, history_limit: int = 100) -> None:
        self._history_limit = max(1, history_limit)
        self._event_counter = 0

    def _generate_event_id(self, tick: int, scope: str) -> str:
        """Generate a unique event ID."""
        self._event_counter += 1
        return f"{scope}-{tick}-{self._event_counter}"

    def record_event(
        self,
        state: GameState,
        *,
        tick: int,
        message: str,
        scope: str,
        actor_id: str | None = None,
        actor_name: str | None = None,
        actor_type: str | None = None,
        target_id: str | None = None,
        target_name: str | None = None,
        district_id: str | None = None,
        causes: Sequence[str] | None = None,
        reasoning: str | None = None,
        outcome: str | None = None,
    ) -> CausalEvent:
        """Record a causal event in the timeline."""
        event_id = self._generate_event_id(tick, scope)
        env = state.environment
        metrics = {
            "stability": round(env.stability, 3),
            "unrest": round(env.unrest, 3),
            "pollution": round(env.pollution, 3),
        }
        event = CausalEvent(
            tick=tick,
            event_id=event_id,
            message=message,
            scope=scope,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_type=actor_type,
            target_id=target_id,
            target_name=target_name,
            district_id=district_id,
            causes=list(causes) if causes else [],
            reasoning=reasoning,
            outcome=outcome,
            metrics_snapshot=metrics,
        )
        self._append_event(state, event)
        return event

    def record_agent_reasoning(
        self,
        state: GameState,
        *,
        tick: int,
        agent_id: str,
        agent_name: str,
        decision: str,
        options: Sequence[tuple[str, float]] | None = None,
        chosen: str | None = None,
        score: float = 0.0,
        context: Mapping[str, Any] | None = None,
    ) -> ActorReasoning:
        """Record agent decision reasoning."""
        options_data = [{"option": opt, "score": round(sc, 4)} for opt, sc in (options or [])]
        reasoning = ActorReasoning(
            tick=tick,
            actor_id=agent_id,
            actor_name=agent_name,
            actor_type="agent",
            decision=decision,
            options_considered=options_data,
            chosen_option=chosen,
            score=score,
            context=dict(context) if context else {},
        )
        self._append_reasoning(state, reasoning)
        return reasoning

    def record_faction_reasoning(
        self,
        state: GameState,
        *,
        tick: int,
        faction_id: str,
        faction_name: str,
        decision: str,
        options: Sequence[tuple[str, float]] | None = None,
        chosen: str | None = None,
        score: float = 0.0,
        context: Mapping[str, Any] | None = None,
    ) -> ActorReasoning:
        """Record faction decision reasoning."""
        options_data = [{"option": opt, "score": round(sc, 4)} for opt, sc in (options or [])]
        reasoning = ActorReasoning(
            tick=tick,
            actor_id=faction_id,
            actor_name=faction_name,
            actor_type="faction",
            decision=decision,
            options_considered=options_data,
            chosen_option=chosen,
            score=score,
            context=dict(context) if context else {},
        )
        self._append_reasoning(state, reasoning)
        return reasoning

    def get_timeline(
        self,
        state: GameState,
        *,
        limit: int | None = None,
        scope: str | None = None,
        actor_id: str | None = None,
    ) -> List[CausalEvent]:
        """Query the event timeline with optional filters."""
        raw = state.metadata.get("explanation_timeline") or []
        events = [CausalEvent.from_dict(entry) for entry in raw]
        if scope:
            events = [e for e in events if e.scope == scope]
        if actor_id:
            events = [e for e in events if e.actor_id == actor_id]
        if limit and limit > 0:
            events = events[-limit:]
        return events

    def get_event(self, state: GameState, event_id: str) -> CausalEvent | None:
        """Retrieve a specific event by ID."""
        raw = state.metadata.get("explanation_timeline") or []
        for entry in raw:
            if entry.get("event_id") == event_id:
                return CausalEvent.from_dict(entry)
        return None

    def get_causal_chain(
        self,
        state: GameState,
        event_id: str,
        *,
        max_depth: int = 5,
    ) -> List[CausalEvent]:
        """Trace the causal chain back from an event."""
        chain: List[CausalEvent] = []
        visited: set[str] = set()
        queue = [event_id]
        depth = 0

        while queue and depth < max_depth:
            next_queue: List[str] = []
            for eid in queue:
                if eid in visited:
                    continue
                visited.add(eid)
                event = self.get_event(state, eid)
                if event:
                    chain.append(event)
                    next_queue.extend(event.causes)
            queue = next_queue
            depth += 1

        return chain

    def get_actor_reasoning(
        self,
        state: GameState,
        actor_id: str,
        *,
        limit: int | None = None,
    ) -> List[ActorReasoning]:
        """Get reasoning history for a specific actor."""
        raw = state.metadata.get("explanation_reasoning") or []
        reasoning = [
            ActorReasoning.from_dict(entry)
            for entry in raw
            if entry.get("actor_id") == actor_id
        ]
        if limit and limit > 0:
            reasoning = reasoning[-limit:]
        return reasoning

    def get_recent_reasoning(
        self,
        state: GameState,
        *,
        actor_type: str | None = None,
        limit: int | None = None,
    ) -> List[ActorReasoning]:
        """Get recent reasoning entries with optional type filter."""
        raw = state.metadata.get("explanation_reasoning") or []
        reasoning = [ActorReasoning.from_dict(entry) for entry in raw]
        if actor_type:
            reasoning = [r for r in reasoning if r.actor_type == actor_type]
        if limit and limit > 0:
            reasoning = reasoning[-limit:]
        return reasoning

    def explain_event(
        self,
        state: GameState,
        event_id: str,
    ) -> Dict[str, Any]:
        """Generate a causal explanation for an event."""
        event = self.get_event(state, event_id)
        if not event:
            return {"error": f"Event '{event_id}' not found"}

        chain = self.get_causal_chain(state, event_id)

        # Build explanation
        explanation: Dict[str, Any] = {
            "event": event.to_dict(),
            "causal_chain": [e.to_dict() for e in chain],
            "chain_length": len(chain),
        }

        # Add actor reasoning if available
        if event.actor_id:
            reasoning = self.get_actor_reasoning(state, event.actor_id, limit=1)
            if reasoning:
                latest = reasoning[-1]
                if latest.tick == event.tick:
                    explanation["actor_reasoning"] = latest.to_dict()

        return explanation

    def summarize_causality(
        self,
        state: GameState,
        *,
        tick_range: tuple[int, int] | None = None,
    ) -> Dict[str, Any]:
        """Generate a causal summary for the simulation."""
        timeline = self.get_timeline(state)
        if tick_range:
            timeline = [e for e in timeline if tick_range[0] <= e.tick <= tick_range[1]]

        if not timeline:
            return {"events": 0, "actors": [], "scopes": {}}

        # Aggregate by scope
        scope_counts: Dict[str, int] = {}
        actor_events: Dict[str, int] = {}
        for event in timeline:
            scope_counts[event.scope] = scope_counts.get(event.scope, 0) + 1
            if event.actor_id:
                key = f"{event.actor_type or 'unknown'}:{event.actor_id}"
                actor_events[key] = actor_events.get(key, 0) + 1

        # Get top actors
        top_actors = sorted(actor_events.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "events": len(timeline),
            "tick_range": (timeline[0].tick, timeline[-1].tick) if timeline else None,
            "scopes": scope_counts,
            "top_actors": [{"actor": a, "events": c} for a, c in top_actors],
        }

    def _append_event(self, state: GameState, event: CausalEvent) -> None:
        """Append an event to the timeline, respecting history limit."""
        timeline = list(state.metadata.get("explanation_timeline") or [])
        timeline.append(event.to_dict())
        if len(timeline) > self._history_limit:
            timeline = timeline[-self._history_limit:]
        state.metadata["explanation_timeline"] = timeline

    def _append_reasoning(self, state: GameState, reasoning: ActorReasoning) -> None:
        """Append reasoning to history, respecting limit."""
        history = list(state.metadata.get("explanation_reasoning") or [])
        history.append(reasoning.to_dict())
        if len(history) > self._history_limit:
            history = history[-self._history_limit:]
        state.metadata["explanation_reasoning"] = history


__all__ = [
    "ActorReasoning",
    "CausalEvent",
    "ExplanationTracker",
]
