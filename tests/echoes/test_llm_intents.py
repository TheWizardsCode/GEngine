"""Tests for intent schema definitions."""

import pytest
from pydantic import ValidationError

from gengine.echoes.llm.intents import (
    CovertActionIntent,
    DeployResourceIntent,
    InspectIntent,
    IntentType,
    InvokeAgentIntent,
    NegotiateIntent,
    PassPolicyIntent,
    RequestReportIntent,
    parse_intent,
)


class TestInspectIntent:
    """Tests for InspectIntent schema."""

    def test_inspect_district(self):
        """Test valid inspect intent for a district."""
        intent = InspectIntent(
            session_id="test-session",
            target_type="district",
            target_id="industrial-tier",
            narrative_context="Check pollution levels",
        )
        assert intent.intent == IntentType.INSPECT
        assert intent.target_type == "district"
        assert intent.target_id == "industrial-tier"

    def test_inspect_with_focus_areas(self):
        """Test inspect intent with specific focus areas."""
        intent = InspectIntent(
            session_id="test-session",
            target_type="district",
            target_id="perimeter-hollow",
            focus_areas=["pollution", "stability", "unrest"],
        )
        assert len(intent.focus_areas) == 3
        assert "pollution" in intent.focus_areas

    def test_inspect_invalid_target_type(self):
        """Test that invalid target types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InspectIntent(
                session_id="test-session",
                target_type="invalid",
                target_id="some-id",
            )
        assert "target_type must be one of" in str(exc_info.value)

    def test_inspect_agent(self):
        """Test inspect intent for an agent."""
        intent = InspectIntent(
            session_id="test-session",
            target_type="agent",
            target_id="jonas-vale",
        )
        assert intent.target_type == "agent"
        assert intent.target_id == "jonas-vale"

    def test_inspect_faction(self):
        """Test inspect intent for a faction."""
        intent = InspectIntent(
            session_id="test-session",
            target_type="faction",
            target_id="union-of-flux",
        )
        assert intent.target_type == "faction"


class TestNegotiateIntent:
    """Tests for NegotiateIntent schema."""

    def test_negotiate_single_faction(self):
        """Test negotiation with a single faction."""
        intent = NegotiateIntent(
            session_id="test-session",
            targets=["union-of-flux"],
            levers={"resource_offer": "materials", "amount": 50},
            goal="increase legitimacy",
        )
        assert len(intent.targets) == 1
        assert intent.levers["resource_offer"] == "materials"

    def test_negotiate_multiple_factions(self):
        """Test negotiation with multiple factions."""
        intent = NegotiateIntent(
            session_id="test-session",
            targets=["union-of-flux", "compact-majority"],
            goal="broker truce",
        )
        assert len(intent.targets) == 2

    def test_negotiate_empty_targets(self):
        """Test that empty targets list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            NegotiateIntent(
                session_id="test-session",
                targets=[],
            )
        assert "At least one target faction is required" in str(exc_info.value)

    def test_negotiate_with_narrative_context(self):
        """Test negotiation with narrative context."""
        intent = NegotiateIntent(
            session_id="test-session",
            targets=["union-of-flux"],
            narrative_context="Broker truce over refinery protest",
        )
        assert intent.narrative_context == "Broker truce over refinery protest"


class TestDeployResourceIntent:
    """Tests for DeployResourceIntent schema."""

    def test_deploy_materials(self):
        """Test deploying materials to a district."""
        intent = DeployResourceIntent(
            session_id="test-session",
            resource_type="materials",
            amount=100.5,
            target_district="industrial-tier",
            purpose="boost production",
        )
        assert intent.resource_type == "materials"
        assert intent.amount == 100.5
        assert intent.target_district == "industrial-tier"

    def test_deploy_energy(self):
        """Test deploying energy to a district."""
        intent = DeployResourceIntent(
            session_id="test-session",
            resource_type="energy",
            amount=75.0,
            target_district="perimeter-hollow",
        )
        assert intent.resource_type == "energy"
        assert intent.amount == 75.0

    def test_deploy_invalid_resource_type(self):
        """Test that invalid resource types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DeployResourceIntent(
                session_id="test-session",
                resource_type="invalid",
                amount=50,
                target_district="spire",
            )
        assert "resource_type must be one of" in str(exc_info.value)

    def test_deploy_negative_amount(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValidationError):
            DeployResourceIntent(
                session_id="test-session",
                resource_type="materials",
                amount=-10,
                target_district="spire",
            )


class TestPassPolicyIntent:
    """Tests for PassPolicyIntent schema."""

    def test_pass_permanent_policy(self):
        """Test passing a permanent policy."""
        intent = PassPolicyIntent(
            session_id="test-session",
            policy_id="emissions-cap",
            parameters={"max_pollution": 0.5},
        )
        assert intent.policy_id == "emissions-cap"
        assert intent.duration_ticks is None

    def test_pass_temporary_policy(self):
        """Test passing a temporary policy."""
        intent = PassPolicyIntent(
            session_id="test-session",
            policy_id="curfew",
            duration_ticks=20,
        )
        assert intent.duration_ticks == 20

    def test_pass_policy_with_parameters(self):
        """Test passing a policy with parameters."""
        intent = PassPolicyIntent(
            session_id="test-session",
            policy_id="resource-rationing",
            parameters={"materials_limit": 100, "energy_limit": 50},
        )
        assert len(intent.parameters) == 2


class TestCovertActionIntent:
    """Tests for CovertActionIntent schema."""

    def test_covert_action_basic(self):
        """Test basic covert action."""
        intent = CovertActionIntent(
            session_id="test-session",
            action_type="surveillance",
            target_district="perimeter-hollow",
        )
        assert intent.action_type == "surveillance"
        assert intent.target_district == "perimeter-hollow"

    def test_covert_action_with_risk(self):
        """Test covert action with risk level."""
        intent = CovertActionIntent(
            session_id="test-session",
            action_type="sabotage",
            target_faction="compact-majority",
            risk_level="high",
        )
        assert intent.risk_level == "high"

    def test_covert_action_invalid_risk(self):
        """Test that invalid risk levels are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CovertActionIntent(
                session_id="test-session",
                action_type="infiltration",
                risk_level="extreme",
            )
        assert "risk_level must be one of" in str(exc_info.value)

    def test_covert_action_with_parameters(self):
        """Test covert action with custom parameters."""
        intent = CovertActionIntent(
            session_id="test-session",
            action_type="intel-gathering",
            parameters={"duration": 10, "focus": "leadership"},
        )
        assert intent.parameters["duration"] == 10


class TestInvokeAgentIntent:
    """Tests for InvokeAgentIntent schema."""

    def test_invoke_agent_basic(self):
        """Test basic agent invocation."""
        intent = InvokeAgentIntent(
            session_id="test-session",
            agent_id="jonas-vale",
            action="investigate",
        )
        assert intent.agent_id == "jonas-vale"
        assert intent.action == "investigate"

    def test_invoke_agent_with_target(self):
        """Test agent invocation with target."""
        intent = InvokeAgentIntent(
            session_id="test-session",
            agent_id="jonas-vale",
            action="negotiate",
            target="union-of-flux",
        )
        assert intent.target == "union-of-flux"

    def test_invoke_agent_with_parameters(self):
        """Test agent invocation with parameters."""
        intent = InvokeAgentIntent(
            session_id="test-session",
            agent_id="jonas-vale",
            action="stabilize",
            target="industrial-tier",
            parameters={"priority": "high", "resources": 50},
        )
        assert intent.parameters["priority"] == "high"


class TestRequestReportIntent:
    """Tests for RequestReportIntent schema."""

    def test_request_summary_report(self):
        """Test requesting a summary report."""
        intent = RequestReportIntent(
            session_id="test-session",
            report_type="summary",
        )
        assert intent.report_type == "summary"
        assert not intent.include_history

    def test_request_district_report(self):
        """Test requesting a district report with filters."""
        intent = RequestReportIntent(
            session_id="test-session",
            report_type="district",
            filters={"district_id": "industrial-tier"},
            include_history=True,
        )
        assert intent.report_type == "district"
        assert intent.include_history

    def test_request_report_invalid_type(self):
        """Test that invalid report types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RequestReportIntent(
                session_id="test-session",
                report_type="invalid",
            )
        assert "report_type must be one of" in str(exc_info.value)

    def test_request_director_report(self):
        """Test requesting a director report."""
        intent = RequestReportIntent(
            session_id="test-session",
            report_type="director",
            filters={"count": 5},
        )
        assert intent.report_type == "director"


class TestParseIntent:
    """Tests for parse_intent function."""

    def test_parse_inspect_intent(self):
        """Test parsing an inspect intent from raw data."""
        data = {
            "intent": "INSPECT",
            "session_id": "test-session",
            "target_type": "district",
            "target_id": "industrial-tier",
        }
        intent = parse_intent(data)
        assert isinstance(intent, InspectIntent)
        assert intent.target_type == "district"

    def test_parse_negotiate_intent(self):
        """Test parsing a negotiate intent from raw data."""
        data = {
            "intent": "NEGOTIATE",
            "session_id": "test-session",
            "targets": ["union-of-flux"],
        }
        intent = parse_intent(data)
        assert isinstance(intent, NegotiateIntent)

    def test_parse_missing_intent_field(self):
        """Test that missing intent field raises error."""
        data = {"session_id": "test-session"}
        with pytest.raises(ValueError) as exc_info:
            parse_intent(data)
        assert "Intent data must include 'intent' field" in str(exc_info.value)

    def test_parse_unknown_intent_type(self):
        """Test that unknown intent types raise error."""
        data = {"intent": "UNKNOWN", "session_id": "test-session"}
        with pytest.raises(ValueError) as exc_info:
            parse_intent(data)
        assert "Unknown intent type" in str(exc_info.value)

    def test_parse_deploy_resource_intent(self):
        """Test parsing a deploy resource intent."""
        data = {
            "intent": "DEPLOY_RESOURCE",
            "session_id": "test-session",
            "resource_type": "materials",
            "amount": 50,
            "target_district": "spire",
        }
        intent = parse_intent(data)
        assert isinstance(intent, DeployResourceIntent)
        assert intent.amount == 50

    def test_parse_validation_error(self):
        """Test that validation errors are raised for invalid data."""
        data = {
            "intent": "INSPECT",
            "session_id": "test-session",
            "target_type": "invalid",
            "target_id": "some-id",
        }
        with pytest.raises(ValidationError):
            parse_intent(data)
