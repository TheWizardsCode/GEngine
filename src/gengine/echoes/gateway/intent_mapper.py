"""Maps LLM intents to simulation actions."""

from __future__ import annotations

import logging
from typing import Any

from ..llm import (
    CovertActionIntent,
    DeployResourceIntent,
    GameIntent,
    InspectIntent,
    IntentType,
    InvokeAgentIntent,
    NegotiateIntent,
    PassPolicyIntent,
    RequestReportIntent,
)

LOGGER = logging.getLogger("gengine.echoes.gateway.intent")


class IntentMapper:
    """Converts GameIntent objects to simulation commands.
    
    This mapper translates structured intents from the LLM into
    commands that can be executed through the shell backend.
    """

    def map_intent_to_command(self, intent: GameIntent) -> str:
        """Convert a GameIntent to a shell command string.
        
        Args:
            intent: The parsed game intent
            
        Returns:
            Shell command string that implements the intent
            
        Raises:
            ValueError: If intent type is not supported
        """
        if isinstance(intent, InspectIntent):
            return self._map_inspect(intent)
        elif isinstance(intent, NegotiateIntent):
            return self._map_negotiate(intent)
        elif isinstance(intent, DeployResourceIntent):
            return self._map_deploy_resource(intent)
        elif isinstance(intent, PassPolicyIntent):
            return self._map_pass_policy(intent)
        elif isinstance(intent, CovertActionIntent):
            return self._map_covert_action(intent)
        elif isinstance(intent, InvokeAgentIntent):
            return self._map_invoke_agent(intent)
        elif isinstance(intent, RequestReportIntent):
            return self._map_request_report(intent)
        else:
            raise ValueError(f"Unknown intent type: {type(intent).__name__}")

    def _map_inspect(self, intent: InspectIntent) -> str:
        """Map INSPECT intent to shell command."""
        target_type = intent.target_type
        target_id = intent.target_id
        
        if target_type == "district":
            # Map to 'map <district_id>' command
            return f"map {target_id}"
        elif target_type in ("agent", "faction"):
            # For now, use summary to show agent/faction info
            # Future: add dedicated agent/faction detail commands
            LOGGER.info("INSPECT %s '%s' - using summary (no dedicated command yet)", target_type, target_id)
            return "summary"
        else:
            LOGGER.warning("Unknown INSPECT target_type: %s", target_type)
            return "summary"

    def _map_negotiate(self, intent: NegotiateIntent) -> str:
        """Map NEGOTIATE intent to shell command."""
        # Negotiation requires game mechanics not yet exposed via CLI
        # For now, log the intent and return a summary
        LOGGER.info(
            "NEGOTIATE intent: targets=%s levers=%s goal=%s (not yet implemented)",
            intent.targets,
            intent.levers,
            intent.goal,
        )
        return "summary"

    def _map_deploy_resource(self, intent: DeployResourceIntent) -> str:
        """Map DEPLOY_RESOURCE intent to shell command."""
        # Resource deployment requires action API not yet exposed via CLI
        # For now, log the intent and return a summary
        LOGGER.info(
            "DEPLOY_RESOURCE intent: type=%s amount=%d district=%s (not yet implemented)",
            intent.resource_type,
            intent.amount,
            intent.target_district,
        )
        return "summary"

    def _map_pass_policy(self, intent: PassPolicyIntent) -> str:
        """Map PASS_POLICY intent to shell command."""
        # Policy system requires action API not yet exposed via CLI
        # For now, log the intent and return a summary
        LOGGER.info(
            "PASS_POLICY intent: policy=%s duration=%s (not yet implemented)",
            intent.policy_id,
            intent.duration_ticks,
        )
        return "summary"

    def _map_covert_action(self, intent: CovertActionIntent) -> str:
        """Map COVERT_ACTION intent to shell command."""
        # Covert actions require game mechanics not yet exposed via CLI
        # For now, log the intent and return a summary
        target = intent.target_district or intent.target_faction or "unknown"
        LOGGER.info(
            "COVERT_ACTION intent: action=%s target=%s risk=%s (not yet implemented)",
            intent.action_type,
            target,
            intent.risk_level,
        )
        return "summary"

    def _map_invoke_agent(self, intent: InvokeAgentIntent) -> str:
        """Map INVOKE_AGENT intent to shell command."""
        # Agent commands require action API not yet exposed via CLI
        # For now, log the intent and return a summary
        LOGGER.info(
            "INVOKE_AGENT intent: agent=%s action=%s (not yet implemented)",
            intent.agent_id,
            intent.action,
        )
        return "summary"

    def _map_request_report(self, intent: RequestReportIntent) -> str:
        """Map REQUEST_REPORT intent to shell command."""
        report_type = intent.report_type
        
        if report_type == "summary":
            return "summary"
        elif report_type == "district":
            # Use map command to show district details
            if intent.filters and "district_id" in intent.filters:
                district_id = intent.filters["district_id"]
                return f"map {district_id}"
            else:
                return "map"
        elif report_type == "director":
            # Use director command
            count = 5  # Default count
            if intent.filters and "count" in intent.filters:
                try:
                    count = int(intent.filters["count"])
                except (ValueError, TypeError):
                    pass
            return f"director {count}"
        else:
            LOGGER.warning("Unknown report_type: %s", report_type)
            return "summary"
