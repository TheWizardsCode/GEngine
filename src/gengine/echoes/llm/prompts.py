"""Prompt templates for LLM intent parsing and narration.

This module provides prompt templates and function schemas for structured
LLM interactions using function calling (OpenAI) and structured outputs (Anthropic).
"""

from typing import Any

# OpenAI function calling schema for intent parsing
OPENAI_INTENT_FUNCTIONS = [
    {
        "name": "inspect_target",
        "description": "Examine a district, agent, or faction to gather information",
        "parameters": {
            "type": "object",
            "properties": {
                "target_type": {
                    "type": "string",
                    "enum": ["district", "agent", "faction"],
                    "description": "Type of target to inspect",
                },
                "target_id": {
                    "type": "string",
                    "description": "ID or name of the target",
                },
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific aspects to focus on (optional)",
                },
                "narrative_context": {
                    "type": "string",
                    "description": "Natural language context for this action",
                },
            },
            "required": ["target_type", "target_id"],
        },
    },
    {
        "name": "negotiate_with_faction",
        "description": "Broker deals or truces with one or more factions",
        "parameters": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Faction IDs or names to negotiate with",
                },
                "levers": {
                    "type": "object",
                    "description": "Negotiation levers "
                    "(resource offers, policy promises)",
                },
                "goal": {
                    "type": "string",
                    "description": "Desired outcome of negotiation",
                },
                "narrative_context": {
                    "type": "string",
                    "description": "Natural language context for this action",
                },
            },
            "required": ["targets"],
        },
    },
    {
        "name": "deploy_resource",
        "description": "Allocate materials or energy to a district",
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "enum": ["materials", "energy"],
                    "description": "Type of resource to deploy",
                },
                "amount": {
                    "type": "number",
                    "description": "Amount to deploy (positive number)",
                },
                "target_district": {
                    "type": "string",
                    "description": "District ID or name to deploy to",
                },
                "purpose": {
                    "type": "string",
                    "description": "Purpose of deployment (optional)",
                },
                "narrative_context": {
                    "type": "string",
                    "description": "Natural language context for this action",
                },
            },
            "required": ["resource_type", "amount", "target_district"],
        },
    },
    {
        "name": "pass_policy",
        "description": "Enact a city-wide policy",
        "parameters": {
            "type": "object",
            "properties": {
                "policy_id": {
                    "type": "string",
                    "description": "ID of the policy to enact",
                },
                "parameters": {
                    "type": "object",
                    "description": "Policy parameters",
                },
                "duration_ticks": {
                    "type": "integer",
                    "description": "Duration in ticks (omit for permanent)",
                },
                "narrative_context": {
                    "type": "string",
                    "description": "Natural language context for this action",
                },
            },
            "required": ["policy_id"],
        },
    },
    {
        "name": "covert_action",
        "description": "Execute a hidden operation",
        "parameters": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "description": "Type of covert action",
                },
                "target_district": {
                    "type": "string",
                    "description": "Target district ID (optional)",
                },
                "target_faction": {
                    "type": "string",
                    "description": "Target faction ID (optional)",
                },
                "parameters": {
                    "type": "object",
                    "description": "Action-specific parameters",
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Risk level (optional)",
                },
                "narrative_context": {
                    "type": "string",
                    "description": "Natural language context for this action",
                },
            },
            "required": ["action_type"],
        },
    },
    {
        "name": "invoke_agent",
        "description": "Direct a specific agent to take an action",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID or name to command",
                },
                "action": {
                    "type": "string",
                    "description": "Action for agent to take",
                },
                "target": {
                    "type": "string",
                    "description": "Target for the action (optional)",
                },
                "parameters": {
                    "type": "object",
                    "description": "Action-specific parameters",
                },
                "narrative_context": {
                    "type": "string",
                    "description": "Natural language context for this action",
                },
            },
            "required": ["agent_id", "action"],
        },
    },
    {
        "name": "request_report",
        "description": "Query simulation state or request a report",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": [
                        "summary",
                        "district",
                        "faction",
                        "agent",
                        "environment",
                        "director",
                    ],
                    "description": "Type of report to generate",
                },
                "filters": {
                    "type": "object",
                    "description": "Filters for the report",
                },
                "include_history": {
                    "type": "boolean",
                    "description": "Include historical data",
                },
                "narrative_context": {
                    "type": "string",
                    "description": "Natural language context for this request",
                },
            },
            "required": ["report_type"],
        },
    },
]

# System prompt for intent parsing
INTENT_PARSING_SYSTEM_PROMPT = (
    "You are an AI assistant helping players interact with "
    '"Echoes of Emergence", a city simulation game.\n\n'
    "Your role is to parse player commands into structured game intents. "
    "Players can:\n"
    "- INSPECT districts, agents, or factions to gather information\n"
    "- NEGOTIATE with factions to broker deals or resolve conflicts\n"
    "- DEPLOY resources (materials/energy) to districts\n"
    "- PASS policies that affect the entire city\n"
    "- Execute COVERT actions for hidden operations\n"
    "- INVOKE specific agents to take actions\n"
    "- REQUEST reports about simulation state\n\n"
    "Extract key details from player text:\n"
    "- Target entities (districts, agents, factions)\n"
    "- Resource types and amounts\n"
    "- Goals and purposes\n"
    "- Any relevant context\n\n"
    "Be permissive in parsing - if the player's intent is unclear but "
    "seems like one of these actions, make a reasonable guess and include "
    "context about the uncertainty."
)

# Anthropic structured output schema
ANTHROPIC_INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent_type": {
            "type": "string",
            "enum": [
                "INSPECT",
                "NEGOTIATE",
                "DEPLOY_RESOURCE",
                "PASS_POLICY",
                "COVERT_ACTION",
                "INVOKE_AGENT",
                "REQUEST_REPORT",
            ],
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "parameters": {
            "type": "object",
            "description": "Intent-specific parameters",
        },
        "narrative_context": {
            "type": "string",
            "description": "Natural language summary of the intent",
        },
    },
    "required": ["intent_type", "confidence", "parameters"],
}

# Narration system prompt
NARRATION_SYSTEM_PROMPT = (
    "You are a narrative generator for "
    '"Echoes of Emergence", a city simulation game.\n\n'
    "Your role is to transform simulation events into engaging story text. "
    "Given a list of events and context:\n"
    "- Weave events into a cohesive narrative\n"
    "- Match the tone to the context (neutral, tense, hopeful, etc.)\n"
    "- Use vivid but concise language\n"
    "- Connect events causally when possible\n"
    "- Maintain consistency with the game world\n\n"
    "The game world:\n"
    "- Near-future city dealing with resource scarcity and political tensions\n"
    "- Three main districts: Industrial Tier (production), "
    "Perimeter Hollow (volatile), Spire (elite)\n"
    "- Two factions: Union of Flux (labor/environment) and "
    "Compact Majority (order/tradition)\n"
    "- Agents act as key NPCs driving events\n\n"
    "Keep narrations brief (2-4 sentences) unless context suggests more "
    "detail is needed."
)


def build_intent_parsing_prompt(
    user_text: str,
    available_actions: list[str] | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    """Build a complete prompt for intent parsing.

    Args:
        user_text: The player's natural language command
        available_actions: Optional list of currently available actions
        context: Optional context about current game state

    Returns:
        Formatted prompt string
    """
    prompt_parts = [f"Player command: {user_text}"]

    if available_actions:
        actions_str = ", ".join(available_actions)
        prompt_parts.append(f"\nCurrently available actions: {actions_str}")

    if context:
        if "district" in context:
            prompt_parts.append(f"\nCurrent district: {context['district']}")
        if "tick" in context:
            prompt_parts.append(f"\nCurrent tick: {context['tick']}")
        if "recent_events" in context:
            events_str = "; ".join(context["recent_events"][:3])
            prompt_parts.append(f"\nRecent events: {events_str}")

    prompt_parts.append(
        "\nParse this command into the most appropriate game intent "
        "using the available functions."
    )

    return "\n".join(prompt_parts)


def build_narration_prompt(
    events: list[str], context: dict[str, Any] | None = None
) -> str:
    """Build a complete prompt for narration generation.

    Args:
        events: List of event descriptions to narrate
        context: Optional context (district, faction, sentiment, etc.)

    Returns:
        Formatted prompt string
    """
    if not events:
        return (
            "Generate a brief observation that nothing significant "
            "has occurred recently."
        )

    prompt_parts = ["Generate a narrative for these simulation events:"]

    for i, event in enumerate(events, 1):
        prompt_parts.append(f"{i}. {event}")

    if context:
        prompt_parts.append("\nContext:")
        if "district" in context:
            prompt_parts.append(f"- Location: {context['district']}")
        if "faction" in context:
            prompt_parts.append(f"- Involved faction: {context['faction']}")
        if "sentiment" in context:
            prompt_parts.append(f"- Sentiment: {context['sentiment']}")
        if "tick" in context:
            prompt_parts.append(f"- Tick: {context['tick']}")

    prompt_parts.append(
        "\nGenerate a cohesive 2-4 sentence narrative that connects these events."
    )

    return "\n".join(prompt_parts)
