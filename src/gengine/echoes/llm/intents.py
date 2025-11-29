"""Intent schema definitions for LLM-to-simulation communication.

This module defines the structured intent types that the LLM service can parse
from natural language and send to the simulation service for execution.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class IntentType(str, Enum):
    """Supported intent types."""

    INSPECT = "INSPECT"
    NEGOTIATE = "NEGOTIATE"
    DEPLOY_RESOURCE = "DEPLOY_RESOURCE"
    PASS_POLICY = "PASS_POLICY"
    COVERT_ACTION = "COVERT_ACTION"
    INVOKE_AGENT = "INVOKE_AGENT"
    REQUEST_REPORT = "REQUEST_REPORT"


class GameIntent(BaseModel):
    """Base model for all game intents."""

    intent: IntentType = Field(..., description="The type of intent")
    session_id: str = Field(..., description="Session identifier for tracking")
    narrative_context: Optional[str] = Field(
        None, description="Natural language context for this intent"
    )


class InspectIntent(GameIntent):
    """Intent to examine districts, agents, or factions."""

    intent: IntentType = Field(default=IntentType.INSPECT)
    target_type: str = Field(
        ..., description="Type of target: district, agent, or faction"
    )
    target_id: str = Field(..., description="ID of the target to inspect")
    focus_areas: Optional[list[str]] = Field(
        None, description="Specific aspects to focus on (e.g., ['pollution', 'stability'])"
    )

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, v: str) -> str:
        """Validate target type is one of the allowed values."""
        allowed = ["district", "agent", "faction"]
        if v not in allowed:
            raise ValueError(f"target_type must be one of {allowed}, got {v}")
        return v


class NegotiateIntent(GameIntent):
    """Intent to broker deals with factions."""

    intent: IntentType = Field(default=IntentType.NEGOTIATE)
    targets: list[str] = Field(..., description="Faction IDs to negotiate with")
    levers: dict[str, Any] = Field(
        default_factory=dict,
        description="Negotiation levers (e.g., resource offers, policy promises)",
    )
    goal: Optional[str] = Field(
        None, description="Desired outcome (e.g., 'increase legitimacy', 'reduce unrest')"
    )

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: list[str]) -> list[str]:
        """Validate at least one target is specified."""
        if not v:
            raise ValueError("At least one target faction is required")
        return v


class DeployResourceIntent(GameIntent):
    """Intent to allocate materials or energy to districts."""

    intent: IntentType = Field(default=IntentType.DEPLOY_RESOURCE)
    resource_type: str = Field(..., description="Type of resource: materials or energy")
    amount: float = Field(..., description="Amount to deploy", ge=0)
    target_district: str = Field(..., description="District ID to deploy to")
    purpose: Optional[str] = Field(
        None, description="Purpose of deployment (e.g., 'stabilize', 'boost production')"
    )

    @field_validator("resource_type")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        """Validate resource type is materials or energy."""
        allowed = ["materials", "energy"]
        if v not in allowed:
            raise ValueError(f"resource_type must be one of {allowed}, got {v}")
        return v


class PassPolicyIntent(GameIntent):
    """Intent to enact city-wide policies."""

    intent: IntentType = Field(default=IntentType.PASS_POLICY)
    policy_id: str = Field(..., description="ID of the policy to enact")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Policy parameters"
    )
    duration_ticks: Optional[int] = Field(
        None, description="Duration in ticks (None for permanent)", ge=1
    )


class CovertActionIntent(GameIntent):
    """Intent for hidden operations."""

    intent: IntentType = Field(default=IntentType.COVERT_ACTION)
    action_type: str = Field(..., description="Type of covert action")
    target_district: Optional[str] = Field(None, description="Target district ID")
    target_faction: Optional[str] = Field(None, description="Target faction ID")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Action-specific parameters"
    )
    risk_level: Optional[str] = Field(
        None, description="Risk level: low, medium, high"
    )

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate risk level if specified."""
        if v is not None:
            allowed = ["low", "medium", "high"]
            if v not in allowed:
                raise ValueError(f"risk_level must be one of {allowed}, got {v}")
        return v


class InvokeAgentIntent(GameIntent):
    """Intent to direct agent actions."""

    intent: IntentType = Field(default=IntentType.INVOKE_AGENT)
    agent_id: str = Field(..., description="Agent ID to command")
    action: str = Field(..., description="Action for agent to take")
    target: Optional[str] = Field(None, description="Target for the action")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Action-specific parameters"
    )


class RequestReportIntent(GameIntent):
    """Intent to query simulation state."""

    intent: IntentType = Field(default=IntentType.REQUEST_REPORT)
    report_type: str = Field(..., description="Type of report to generate")
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Filters for the report"
    )
    include_history: bool = Field(
        default=False, description="Include historical data"
    )

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, v: str) -> str:
        """Validate report type."""
        allowed = ["summary", "district", "faction", "agent", "environment", "director"]
        if v not in allowed:
            raise ValueError(f"report_type must be one of {allowed}, got {v}")
        return v


# Type mapping for intent parsing
INTENT_TYPE_MAP: dict[IntentType, type[GameIntent]] = {
    IntentType.INSPECT: InspectIntent,
    IntentType.NEGOTIATE: NegotiateIntent,
    IntentType.DEPLOY_RESOURCE: DeployResourceIntent,
    IntentType.PASS_POLICY: PassPolicyIntent,
    IntentType.COVERT_ACTION: CovertActionIntent,
    IntentType.INVOKE_AGENT: InvokeAgentIntent,
    IntentType.REQUEST_REPORT: RequestReportIntent,
}


def parse_intent(data: dict[str, Any]) -> GameIntent:
    """Parse a raw intent dictionary into a typed intent object.

    Args:
        data: Raw intent data with at least an "intent" field

    Returns:
        Typed GameIntent subclass instance

    Raises:
        ValueError: If intent type is unknown or validation fails
    """
    if "intent" not in data:
        raise ValueError("Intent data must include 'intent' field")

    try:
        intent_type = IntentType(data["intent"])
    except ValueError as e:
        raise ValueError(f"Unknown intent type: {data['intent']}") from e

    intent_class = INTENT_TYPE_MAP[intent_type]
    return intent_class(**data)
