"""LLM service module for natural language intent parsing and narration.

Provides provider abstraction layer supporting multiple LLM backends
(OpenAI, Anthropic, stub mode) with a unified interface.
"""

from __future__ import annotations

from .intents import (
    CovertActionIntent,
    DeployResourceIntent,
    GameIntent,
    InspectIntent,
    IntentType,
    InvokeAgentIntent,
    NegotiateIntent,
    PassPolicyIntent,
    RequestReportIntent,
    parse_intent,
)
from .providers import LLMProvider, create_provider
from .settings import LLMSettings

__all__ = [
    "LLMProvider",
    "LLMSettings",
    "create_provider",
    "GameIntent",
    "IntentType",
    "InspectIntent",
    "NegotiateIntent",
    "DeployResourceIntent",
    "PassPolicyIntent",
    "CovertActionIntent",
    "InvokeAgentIntent",
    "RequestReportIntent",
    "parse_intent",
]
