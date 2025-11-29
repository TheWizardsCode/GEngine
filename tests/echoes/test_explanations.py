"""Tests for the explanation tracking system (M7.2)."""

from __future__ import annotations

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.sim import ExplanationTracker
from gengine.echoes.sim.engine import SimEngine


class TestExplanationTracker:
    """Unit tests for ExplanationTracker."""

    def test_record_event_creates_unique_ids(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        event1 = tracker.record_event(
            state,
            tick=1,
            message="Event A",
            scope="agent",
        )
        event2 = tracker.record_event(
            state,
            tick=1,
            message="Event B",
            scope="agent",
        )

        assert event1.event_id != event2.event_id
        assert event1.tick == 1
        assert event1.message == "Event A"

    def test_record_event_captures_metrics(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        event = tracker.record_event(
            state,
            tick=5,
            message="Test event",
            scope="environment",
        )

        assert "stability" in event.metrics_snapshot
        assert "unrest" in event.metrics_snapshot
        assert "pollution" in event.metrics_snapshot

    def test_record_agent_reasoning(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()
        options = [("OPTION_A", 0.5), ("OPTION_B", 0.8), ("OPTION_C", 0.3)]

        reasoning = tracker.record_agent_reasoning(
            state,
            tick=10,
            agent_id="agent-1",
            agent_name="Agent One",
            decision="OPTION_B",
            options=options,
            chosen="OPTION_B",
            score=0.8,
            context={"district": "industrial-tier"},
        )

        assert reasoning.actor_id == "agent-1"
        assert reasoning.actor_type == "agent"
        assert reasoning.decision == "OPTION_B"
        assert len(reasoning.options_considered) == 3

    def test_record_faction_reasoning(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        reasoning = tracker.record_faction_reasoning(
            state,
            tick=15,
            faction_id="faction-1",
            faction_name="Test Faction",
            decision="INVEST_DISTRICT",
            score=0.65,
        )

        assert reasoning.actor_type == "faction"
        assert reasoning.decision == "INVEST_DISTRICT"

    def test_get_timeline_returns_events(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        tracker.record_event(state, tick=1, message="Event 1", scope="agent")
        tracker.record_event(state, tick=2, message="Event 2", scope="faction")
        tracker.record_event(state, tick=3, message="Event 3", scope="agent")

        timeline = tracker.get_timeline(state)

        assert len(timeline) == 3
        assert timeline[0].tick == 1
        assert timeline[2].tick == 3

    def test_get_timeline_filters_by_scope(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        tracker.record_event(state, tick=1, message="Agent event", scope="agent")
        tracker.record_event(state, tick=2, message="Faction event", scope="faction")

        agent_events = tracker.get_timeline(state, scope="agent")
        faction_events = tracker.get_timeline(state, scope="faction")

        assert len(agent_events) == 1
        assert len(faction_events) == 1

    def test_get_timeline_respects_limit(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        for i in range(10):
            tracker.record_event(state, tick=i, message=f"Event {i}", scope="agent")

        limited = tracker.get_timeline(state, limit=3)

        assert len(limited) == 3
        # Should return the last 3 events
        assert limited[0].tick == 7
        assert limited[2].tick == 9

    def test_get_event_by_id(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        recorded = tracker.record_event(
            state,
            tick=5,
            message="Specific event",
            scope="environment",
        )

        retrieved = tracker.get_event(state, recorded.event_id)

        assert retrieved is not None
        assert retrieved.message == "Specific event"

    def test_get_event_returns_none_for_unknown(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        result = tracker.get_event(state, "nonexistent-id")

        assert result is None

    def test_get_causal_chain(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        event1 = tracker.record_event(
            state, tick=1, message="Root cause", scope="environment"
        )
        event2 = tracker.record_event(
            state,
            tick=2,
            message="Effect 1",
            scope="agent",
            causes=[event1.event_id],
        )
        event3 = tracker.record_event(
            state,
            tick=3,
            message="Effect 2",
            scope="faction",
            causes=[event2.event_id],
        )

        chain = tracker.get_causal_chain(state, event3.event_id)

        assert len(chain) == 3
        assert chain[0].event_id == event3.event_id
        assert chain[2].event_id == event1.event_id

    def test_get_actor_reasoning(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        tracker.record_agent_reasoning(
            state, tick=1, agent_id="agent-1", agent_name="A1", decision="X"
        )
        tracker.record_agent_reasoning(
            state, tick=2, agent_id="agent-2", agent_name="A2", decision="Y"
        )
        tracker.record_agent_reasoning(
            state, tick=3, agent_id="agent-1", agent_name="A1", decision="Z"
        )

        reasoning = tracker.get_actor_reasoning(state, "agent-1")

        assert len(reasoning) == 2
        assert reasoning[0].decision == "X"
        assert reasoning[1].decision == "Z"

    def test_explain_event(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        event = tracker.record_event(
            state,
            tick=5,
            message="Test event",
            scope="agent",
            actor_id="agent-1",
            reasoning="Test reasoning",
        )

        explanation = tracker.explain_event(state, event.event_id)

        assert "event" in explanation
        assert "causal_chain" in explanation
        assert explanation["event"]["message"] == "Test event"

    def test_explain_event_not_found(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        explanation = tracker.explain_event(state, "nonexistent")

        assert "error" in explanation

    def test_summarize_causality(self) -> None:
        tracker = ExplanationTracker()
        state = load_world_bundle()

        tracker.record_event(
            state, tick=1, message="E1", scope="agent", actor_id="a1", actor_type="agent"
        )
        tracker.record_event(
            state, tick=2, message="E2", scope="faction", actor_id="f1", actor_type="faction"
        )
        tracker.record_event(
            state, tick=3, message="E3", scope="agent", actor_id="a1", actor_type="agent"
        )

        summary = tracker.summarize_causality(state)

        assert summary["events"] == 3
        assert summary["scopes"]["agent"] == 2
        assert summary["scopes"]["faction"] == 1

    def test_history_limit_enforced(self) -> None:
        tracker = ExplanationTracker(history_limit=5)
        state = load_world_bundle()

        for i in range(10):
            tracker.record_event(state, tick=i, message=f"Event {i}", scope="agent")

        timeline = tracker.get_timeline(state)

        assert len(timeline) == 5
        assert timeline[0].tick == 5  # First event should be tick 5 (oldest kept)


class TestExplanationCLI:
    """Tests for CLI commands related to explanations."""

    def test_timeline_command(self) -> None:
        from gengine.echoes.cli.shell import EchoesShell, LocalBackend

        engine = SimEngine()
        engine.initialize_state(world="default")
        backend = LocalBackend(engine)
        shell = EchoesShell(backend)

        # Run some ticks to generate events
        engine.advance_ticks(5)

        result = shell.execute("timeline 5")

        # Timeline may be empty if no events were recorded to the tracker
        assert result.output

    def test_explain_command_not_found(self) -> None:
        from gengine.echoes.cli.shell import EchoesShell, LocalBackend

        engine = SimEngine()
        engine.initialize_state(world="default")
        backend = LocalBackend(engine)
        shell = EchoesShell(backend)

        result = shell.execute("explain nonexistent-event")

        assert "not found" in result.output.lower()

    def test_why_command_no_reasoning(self) -> None:
        from gengine.echoes.cli.shell import EchoesShell, LocalBackend

        engine = SimEngine()
        engine.initialize_state(world="default")
        backend = LocalBackend(engine)
        shell = EchoesShell(backend)

        result = shell.execute("why unknown-actor")

        assert "no reasoning found" in result.output.lower()

    def test_explain_requires_argument(self) -> None:
        from gengine.echoes.cli.shell import EchoesShell, LocalBackend

        engine = SimEngine()
        engine.initialize_state(world="default")
        backend = LocalBackend(engine)
        shell = EchoesShell(backend)

        result = shell.execute("explain")

        assert "usage" in result.output.lower()

    def test_why_requires_argument(self) -> None:
        from gengine.echoes.cli.shell import EchoesShell, LocalBackend

        engine = SimEngine()
        engine.initialize_state(world="default")
        backend = LocalBackend(engine)
        shell = EchoesShell(backend)

        result = shell.execute("why")

        assert "usage" in result.output.lower()


class TestAgentReasoningCapture:
    """Tests for agent reasoning capture."""

    def test_agent_intent_includes_reasoning(self) -> None:
        from gengine.echoes.systems.agents import AgentSystem

        state = load_world_bundle()
        import random
        rng = random.Random(42)
        system = AgentSystem()

        intents = system.tick(state, rng=rng)

        assert intents
        intent = intents[0]
        assert intent.reasoning
        assert intent.options_considered

    def test_agent_intent_report_includes_reasoning(self) -> None:
        from gengine.echoes.systems.agents import AgentSystem

        state = load_world_bundle()
        import random
        rng = random.Random(42)
        system = AgentSystem()

        intents = system.tick(state, rng=rng)

        assert intents
        report = intents[0].to_report()
        assert "reasoning" in report
        assert "options_considered" in report


class TestFactionReasoningCapture:
    """Tests for faction reasoning capture."""

    def test_faction_action_includes_reasoning(self) -> None:
        from gengine.echoes.systems.factions import FactionSystem

        state = load_world_bundle()
        import random
        rng = random.Random(42)
        system = FactionSystem(cooldown_ticks=0)

        # May need multiple ticks to get an action
        actions = []
        for _ in range(5):
            actions.extend(system.tick(state, rng=rng))
            if actions:
                break

        if actions:
            action = actions[0]
            assert action.reasoning
            report = action.to_report()
            assert "reasoning" in report


class TestEngineExplanationMethods:
    """Tests for SimEngine explanation methods."""

    def test_engine_get_timeline(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        timeline = engine.get_timeline()

        assert isinstance(timeline, list)

    def test_engine_explain_event(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        result = engine.explain_event("nonexistent")

        assert "error" in result

    def test_engine_get_actor_reasoning(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        reasoning = engine.get_actor_reasoning("unknown-actor")

        assert isinstance(reasoning, list)

    def test_engine_get_causality_summary(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        summary = engine.get_causality_summary()

        assert "events" in summary
