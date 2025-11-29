"""Tests for intent mapper."""

import pytest

from gengine.echoes.gateway.intent_mapper import IntentMapper
from gengine.echoes.llm import (
    CovertActionIntent,
    DeployResourceIntent,
    InspectIntent,
    InvokeAgentIntent,
    NegotiateIntent,
    PassPolicyIntent,
    RequestReportIntent,
)

# Test session ID used for all intents
TEST_SESSION = "test-session-123"


class TestIntentMapper:
    """Test intent to command mapping."""

    def test_map_inspect_district(self):
        """Test mapping INSPECT intent for district."""
        mapper = IntentMapper()
        intent = InspectIntent(
            session_id=TEST_SESSION,
            target_type="district",
            target_id="industrial-tier",
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "map industrial-tier"

    def test_map_inspect_agent(self):
        """Test mapping INSPECT intent for agent."""
        mapper = IntentMapper()
        intent = InspectIntent(
            session_id=TEST_SESSION,
            target_type="agent",
            target_id="aria-volt",
        )
        command = mapper.map_intent_to_command(intent)
        # For now, agents map to summary
        assert command == "summary"

    def test_map_inspect_faction(self):
        """Test mapping INSPECT intent for faction."""
        mapper = IntentMapper()
        intent = InspectIntent(
            session_id=TEST_SESSION,
            target_type="faction",
            target_id="union-of-flux",
        )
        command = mapper.map_intent_to_command(intent)
        # For now, factions map to summary
        assert command == "summary"

    def test_map_inspect_with_focus_areas(self):
        """Test INSPECT intent with focus areas."""
        mapper = IntentMapper()
        intent = InspectIntent(
            session_id=TEST_SESSION,
            target_type="district",
            target_id="perimeter-hollow",
            focus_areas=["pollution", "unrest"],
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "map perimeter-hollow"

    def test_map_negotiate(self):
        """Test mapping NEGOTIATE intent."""
        mapper = IntentMapper()
        intent = NegotiateIntent(
            session_id=TEST_SESSION,
            targets=["union-of-flux"],
            levers={"policy_support": True},
            goal="reduce_unrest",
        )
        command = mapper.map_intent_to_command(intent)
        # Negotiation not yet implemented in CLI
        assert command == "summary"

    def test_map_deploy_resource_materials(self):
        """Test mapping DEPLOY_RESOURCE intent with materials."""
        mapper = IntentMapper()
        intent = DeployResourceIntent(
            session_id=TEST_SESSION,
            resource_type="materials",
            amount=100,
            target_district="industrial-tier",
        )
        command = mapper.map_intent_to_command(intent)
        # Resource deployment not yet implemented in CLI
        assert command == "summary"

    def test_map_deploy_resource_energy(self):
        """Test mapping DEPLOY_RESOURCE intent with energy."""
        mapper = IntentMapper()
        intent = DeployResourceIntent(
            session_id=TEST_SESSION,
            resource_type="energy",
            amount=50,
            target_district="perimeter-hollow",
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "summary"

    def test_map_pass_policy(self):
        """Test mapping PASS_POLICY intent."""
        mapper = IntentMapper()
        intent = PassPolicyIntent(
            session_id=TEST_SESSION,
            policy_id="emergency-rationing",
            duration_ticks=10,
        )
        command = mapper.map_intent_to_command(intent)
        # Policy system not yet implemented in CLI
        assert command == "summary"

    def test_map_pass_policy_permanent(self):
        """Test mapping permanent PASS_POLICY intent."""
        mapper = IntentMapper()
        intent = PassPolicyIntent(
            session_id=TEST_SESSION,
            policy_id="universal-basic-income",
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "summary"

    def test_map_covert_action(self):
        """Test mapping COVERT_ACTION intent."""
        mapper = IntentMapper()
        intent = CovertActionIntent(
            session_id=TEST_SESSION,
            action_type="sabotage",
            target_faction="compact-majority",
            risk_level="medium",
        )
        command = mapper.map_intent_to_command(intent)
        # Covert actions not yet implemented in CLI
        assert command == "summary"

    def test_map_invoke_agent(self):
        """Test mapping INVOKE_AGENT intent."""
        mapper = IntentMapper()
        intent = InvokeAgentIntent(
            session_id=TEST_SESSION,
            agent_id="aria-volt",
            action="investigate",
        )
        command = mapper.map_intent_to_command(intent)
        # Agent commands not yet implemented in CLI
        assert command == "summary"

    def test_map_invoke_agent_with_target(self):
        """Test mapping INVOKE_AGENT intent with target."""
        mapper = IntentMapper()
        intent = InvokeAgentIntent(
            session_id=TEST_SESSION,
            agent_id="aria-volt",
            action="negotiate",
            target="union-of-flux",
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "summary"

    def test_map_request_report_summary(self):
        """Test mapping REQUEST_REPORT intent for summary."""
        mapper = IntentMapper()
        intent = RequestReportIntent(
            session_id=TEST_SESSION,
            report_type="summary",
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "summary"

    def test_map_request_report_district_all(self):
        """Test mapping REQUEST_REPORT intent for all districts."""
        mapper = IntentMapper()
        intent = RequestReportIntent(
            session_id=TEST_SESSION,
            report_type="district",
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "map"

    def test_map_request_report_district_specific(self):
        """Test mapping REQUEST_REPORT intent for specific district."""
        mapper = IntentMapper()
        intent = RequestReportIntent(
            session_id=TEST_SESSION,
            report_type="district",
            filters={"district_id": "industrial-tier"},
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "map industrial-tier"

    def test_map_request_report_director_default(self):
        """Test mapping REQUEST_REPORT intent for director."""
        mapper = IntentMapper()
        intent = RequestReportIntent(
            session_id=TEST_SESSION,
            report_type="director",
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "director 5"

    def test_map_request_report_director_with_count(self):
        """Test mapping REQUEST_REPORT intent for director with count."""
        mapper = IntentMapper()
        intent = RequestReportIntent(
            session_id=TEST_SESSION,
            report_type="director",
            filters={"count": 10},
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "director 10"

    def test_map_request_report_invalid_count(self):
        """Test REQUEST_REPORT with invalid count falls back to default."""
        mapper = IntentMapper()
        intent = RequestReportIntent(
            session_id=TEST_SESSION,
            report_type="director",
            filters={"count": "not-a-number"},
        )
        command = mapper.map_intent_to_command(intent)
        assert command == "director 5"

    def test_map_unknown_intent_type(self):
        """Test mapping unknown intent type raises error."""
        mapper = IntentMapper()
        
        # Create a mock intent that's not a recognized type
        class UnknownIntent:
            pass
        
        with pytest.raises(ValueError, match="Unknown intent type"):
            mapper.map_intent_to_command(UnknownIntent())
