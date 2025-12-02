"""Tests for the explanations system (M7.2 causal queries)."""

import pytest

from gengine.echoes.core import GameState
from gengine.echoes.core.models import (
    Agent,
    City,
    District,
    DistrictCoordinates,
    DistrictModifiers,
    EnvironmentState,
    Faction,
)
from gengine.echoes.sim.explanations import (
    AgentReasoningSummary,
    CausalCategory,
    CausalEvent,
    ExplanationsManager,
    TimelineEntry,
)


@pytest.fixture
def sample_state() -> GameState:
    """Create a minimal game state for testing."""
    districts = [
        District(
            id="industrial-tier",
            name="Industrial Tier",
            population=120000,
            modifiers=DistrictModifiers(unrest=0.7, pollution=0.6),
            coordinates=DistrictCoordinates(x=0, y=0),
            adjacent=["civic-core"],
        ),
        District(
            id="civic-core",
            name="Civic Core",
            population=80000,
            modifiers=DistrictModifiers(unrest=0.4, pollution=0.3),
            coordinates=DistrictCoordinates(x=1, y=0),
            adjacent=["industrial-tier"],
        ),
    ]
    city = City(id="test-city", name="Test City", districts=districts)
    factions = {
        "union-of-flux": Faction(
            id="union-of-flux",
            name="Union of Flux",
            legitimacy=0.6,
            ideology="labor",
        ),
        "cartel-of-mist": Faction(
            id="cartel-of-mist",
            name="Cartel of Mist",
            legitimacy=0.4,
            ideology="corporate",
        ),
    }
    agents = {
        "agent-1": Agent(
            id="agent-1",
            name="Test Agent",
            role="organizer",
            faction_id="union-of-flux",
            home_district="industrial-tier",
            needs={"safety": 0.3, "belonging": 0.8},
            traits={"risk_tolerance": 0.7, "empathy": 0.6},
            goals=["increase stability", "support workers"],
        ),
    }
    return GameState(
        city=city,
        factions=factions,
        agents=agents,
        environment=EnvironmentState(stability=0.7, unrest=0.5, pollution=0.4),
        tick=10,
    )


class TestCausalEvent:
    def test_to_dict_basic(self):
        event = CausalEvent(
            tick=5,
            category=CausalCategory.ENVIRONMENT,
            description="stability increased by 0.05",
            metric="stability",
            delta=0.05,
        )
        result = event.to_dict()
        assert result["tick"] == 5
        assert result["category"] == "environment"
        assert result["description"] == "stability increased by 0.05"
        assert result["metric"] == "stability"
        assert result["delta"] == 0.05

    def test_to_dict_with_causes_and_effects(self):
        event = CausalEvent(
            tick=10,
            category=CausalCategory.FACTION,
            description="Union gained legitimacy",
            entity_id="union-of-flux",
            entity_name="Union of Flux",
            causes=["investment", "support"],
            effects=["stability boost", "influence gain"],
        )
        result = event.to_dict()
        assert result["entity_id"] == "union-of-flux"
        assert result["entity_name"] == "Union of Flux"
        assert "investment" in result["causes"]
        assert "stability boost" in result["effects"]


class TestAgentReasoningSummary:
    def test_to_dict(self):
        summary = AgentReasoningSummary(
            agent_id="agent-1",
            agent_name="Test Agent",
            tick=5,
            action="STABILIZE_UNREST",
            target="industrial-tier",
            reasoning_factors=["high unrest", "low safety"],
            needs_snapshot={"safety": 0.3},
        )
        result = summary.to_dict()
        assert result["agent_id"] == "agent-1"
        assert result["agent_name"] == "Test Agent"
        assert result["action"] == "STABILIZE_UNREST"
        assert "high unrest" in result["reasoning_factors"]

    def test_to_summary_text(self):
        summary = AgentReasoningSummary(
            agent_id="agent-1",
            agent_name="Test Agent",
            tick=5,
            action="inspected",
            target="Industrial Tier",
            reasoning_factors=["high unrest", "low safety needs"],
        )
        text = summary.to_summary_text()
        assert "Test Agent" in text
        assert "inspected" in text
        assert "Industrial Tier" in text
        assert "because" in text

    def test_to_summary_text_no_factors(self):
        summary = AgentReasoningSummary(
            agent_id="agent-1",
            agent_name="Test Agent",
            tick=5,
            action="waited",
        )
        text = summary.to_summary_text()
        assert "Test Agent waited" in text
        assert "because" not in text


class TestTimelineEntry:
    def test_to_dict(self):
        event = CausalEvent(
            tick=5,
            category=CausalCategory.ENVIRONMENT,
            description="test event",
        )
        reasoning = AgentReasoningSummary(
            agent_id="agent-1",
            agent_name="Test",
            tick=5,
            action="acted",
        )
        entry = TimelineEntry(
            tick=5,
            events=[event],
            agent_reasoning=[reasoning],
            environment_snapshot={"stability": 0.5},
            key_changes=["stability changed"],
        )
        result = entry.to_dict()
        assert result["tick"] == 5
        assert len(result["events"]) == 1
        assert len(result["agent_reasoning"]) == 1
        assert "stability changed" in result["key_changes"]


class TestExplanationsManager:
    def test_record_tick_captures_environment_delta(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        entry = manager.record_tick(
            sample_state,
            tick=11,
            environment_delta={"stability": -0.02, "unrest": 0.03},
        )
        assert entry.tick == 11
        assert len(entry.events) >= 2
        # Should have events for stability and unrest changes
        categories = [e.category for e in entry.events]
        assert CausalCategory.ENVIRONMENT in categories

    def test_record_tick_captures_faction_deltas(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        entry = manager.record_tick(
            sample_state,
            tick=11,
            faction_deltas={"union-of-flux": 0.05, "cartel-of-mist": -0.03},
        )
        # Should have events for faction legitimacy changes
        faction_events = [
            e for e in entry.events if e.category == CausalCategory.FACTION
        ]
        assert len(faction_events) >= 2

    def test_record_tick_captures_agent_actions(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        agent_actions = [
            {
                "agent_id": "agent-1",
                "agent_name": "Test Agent",
                "intent": "STABILIZE_UNREST",
                "target": "industrial-tier",
                "target_name": "Industrial Tier",
            }
        ]
        entry = manager.record_tick(
            sample_state,
            tick=11,
            agent_actions=agent_actions,
        )
        assert len(entry.agent_reasoning) == 1
        assert entry.agent_reasoning[0].agent_id == "agent-1"
        assert entry.agent_reasoning[0].action == "STABILIZE_UNREST"
        # Should also have agent event
        agent_events = [e for e in entry.events if e.category == CausalCategory.AGENT]
        assert len(agent_events) >= 1

    def test_record_tick_captures_faction_actions(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        faction_actions = [
            {
                "faction_id": "union-of-flux",
                "faction_name": "Union of Flux",
                "action": "INVEST_DISTRICT",
                "target": "industrial-tier",
                "target_name": "Industrial Tier",
            }
        ]
        entry = manager.record_tick(
            sample_state,
            tick=11,
            faction_actions=faction_actions,
        )
        faction_events = [
            e for e in entry.events if e.category == CausalCategory.FACTION
        ]
        assert len(faction_events) >= 1
        # Should have effects for investment
        invest_event = next(
            (e for e in faction_events if "INVEST_DISTRICT" in str(e.metadata)),
            None,
        )
        assert invest_event is not None
        assert "pollution relief" in invest_event.effects

    def test_record_tick_persists_to_metadata(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        manager.record_tick(sample_state, tick=11)
        assert "explanation_timeline_latest" in sample_state.metadata
        assert "explanation_timeline_history" in sample_state.metadata
        history = sample_state.metadata["explanation_timeline_history"]
        assert len(history) == 1
        assert history[0]["tick"] == 11

    def test_query_timeline(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        # Record multiple ticks
        for i in range(5):
            manager.record_tick(sample_state, tick=10 + i)
        entries = manager.query_timeline(count=3)
        assert len(entries) == 3
        # Should return most recent
        assert entries[-1].tick == 14

    def test_explain_metric_stability(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        manager.record_tick(
            sample_state,
            tick=11,
            environment_delta={"stability": -0.05},
        )
        result = manager.explain_metric(sample_state, "stability")
        assert result["metric"] == "stability"
        assert result["current_value"] == pytest.approx(0.7, rel=0.1)
        assert "causes" in result

    def test_explain_faction(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        faction_actions = [
            {
                "faction_id": "union-of-flux",
                "action": "LOBBY_COUNCIL",
            }
        ]
        manager.record_tick(
            sample_state,
            tick=11,
            faction_deltas={"union-of-flux": 0.05},
            faction_actions=faction_actions,
        )
        result = manager.explain_faction(sample_state, "union-of-flux")
        assert result["faction_name"] == "Union of Flux"
        assert result["current_legitimacy"] == pytest.approx(0.6, rel=0.1)
        assert "recent_actions" in result

    def test_explain_faction_unknown(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        result = manager.explain_faction(sample_state, "unknown-faction")
        assert "error" in result

    def test_explain_agent(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        agent_actions = [
            {
                "agent_id": "agent-1",
                "intent": "STABILIZE_UNREST",
                "target": "industrial-tier",
            }
        ]
        manager.record_tick(
            sample_state,
            tick=11,
            agent_actions=agent_actions,
        )
        result = manager.explain_agent(sample_state, "agent-1")
        assert result["agent_name"] == "Test Agent"
        assert result["role"] == "organizer"
        assert "reasoning_summary" in result
        assert "recent_actions" in result

    def test_explain_agent_unknown(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        result = manager.explain_agent(sample_state, "unknown-agent")
        assert "error" in result

    def test_explain_district(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        faction_actions = [
            {
                "faction_id": "union-of-flux",
                "action": "INVEST_DISTRICT",
                "target": "industrial-tier",
            }
        ]
        manager.record_tick(
            sample_state,
            tick=11,
            faction_actions=faction_actions,
        )
        result = manager.explain_district(sample_state, "industrial-tier")
        assert result["district_name"] == "Industrial Tier"
        assert result["population"] == 120000
        assert "modifiers" in result
        assert "faction_activity" in result

    def test_explain_district_unknown(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        result = manager.explain_district(sample_state, "unknown-district")
        assert "error" in result

    def test_get_why_summary_stability(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        manager.record_tick(
            sample_state,
            tick=11,
            environment_delta={"stability": -0.05},
        )
        result = manager.get_why_summary(sample_state, "why did stability drop?")
        assert result["metric"] == "stability"
        assert "causes" in result

    def test_get_why_summary_faction(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        manager.record_tick(sample_state, tick=11)
        result = manager.get_why_summary(sample_state, "why union-of-flux")
        assert result["faction_name"] == "Union of Flux"

    def test_get_why_summary_agent(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        manager.record_tick(sample_state, tick=11)
        result = manager.get_why_summary(sample_state, "why Test Agent")
        assert result["agent_name"] == "Test Agent"

    def test_get_why_summary_district(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        manager.record_tick(sample_state, tick=11)
        result = manager.get_why_summary(sample_state, "what about Industrial Tier")
        assert result["district_name"] == "Industrial Tier"

    def test_get_why_summary_unknown_query(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=50)
        manager.record_tick(sample_state, tick=11)
        result = manager.get_why_summary(sample_state, "random nonsense query")
        assert result["matched"] is False
        assert "suggestion" in result

    def test_history_limit_enforced(self, sample_state: GameState):
        manager = ExplanationsManager(history_limit=5)
        # Record more than limit
        for i in range(10):
            manager.record_tick(sample_state, tick=i)
        entries = manager.query_timeline(count=100)
        assert len(entries) == 5
        # Should have most recent
        assert entries[-1].tick == 9

    def test_infer_stability_causes(self, sample_state: GameState):
        # Set up state with issues
        sample_state.environment.unrest = 0.8
        sample_state.environment.pollution = 0.75
        sample_state.factions["union-of-flux"].legitimacy = 0.2
        manager = ExplanationsManager(history_limit=50)
        causes = manager._infer_stability_causes(sample_state)
        assert any("unrest" in c.lower() for c in causes)
        assert any("pollution" in c.lower() for c in causes)
        assert any("legitimacy" in c.lower() for c in causes)
