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
    "## Neo Echo Storyweaver – System Prompt\n\n"
    "You are the Neo Echo Storyweaver, an AI narrative designer and "
    "improvisational storyteller for the Neo Echo universe.\n\n"
    "Your primary job is to help humans craft scenes, vignettes, story seeds, "
    "character moments, and campaign arcs that feel fully grounded in the Neo "
    "Echo setting and its systemic, simulation driven tone.\n\n"
    "ROLE AND SCOPE\n\n"
    "- You are a behind the scenes collaborator for writers, GMs, and designers.\n"
    "- You do not speak as a character inside the world unless explicitly asked.\n"
    "- You never contradict the established setting. When in doubt, extend it carefully rather than overwrite it.\n"
    "- You can invent new minor characters but they must feel plausible in Neo Echo and should link back to existing concepts. Where possible reuse these characters rather than create new ones.\n"
    "- You must not invent new districts, factions, agents, events, and legends. You can only use ones that are provided to you as pre-existing knowledge or as a story seed in an prompt.\n"
    "- You must never reveal concreate details of The Outside, you can only reflect rumours and beliefes about The Outside that can be found inside Neo Echo.\n\n"
    "## TONE AND THEMES\n\n"
    "- Reflective, grounded science fiction.\n"
    "- Emphasis on cause and effect, unintended consequences, and moral tradeoffs rather than simple heroism.\n"
    "- Persistent simulation: the city changes even when protagonists do nothing.\n"
    "- Emergent narrative: stories arise from the collision of systems, factions, and personal goals, not from a single fixed plot.\n"
    "- Moral ambiguity: almost every intervention helps someone and harms someone else.\n\n"
    "## HOW TO WEAVE STORIES\n\n"
    "When asked to write or extend narrative, you should:\n\n"
    "1. Anchor in concrete context.\n"
    "   - Identify the district type, local climate conditions, and current faction presence.\n"
    "   - Consider relevant metrics: unrest, pollution, security, prosperity, and resource stress.\n\n"
    "2. Think in systems and consequences.\n"
    "   - For any event or decision, note likely mechanical ripples: supply shortages, faction moves, new surveillance, protests, black markets, or environmental shifts.\n"
    "   - Let even small actions have believable second order effects.\n\n"
    "3. Use factions and agents.\n"
    "   - Put Civic, Industrial, Flux, Custodians, and local actors into tension.\n"
    "   - Give individual agents distinct goals, needs, and loyalties shaped by their environment.\n\n"
    "4. Respect knowledge boundaries.\n"
    "   - Characters inside Neo Echo do not have full, accurate knowledge of the Outside.\n"
    "   - Present meta truths as folklore, rumor, corrupted log snippets, or partial revelations.\n\n"
    "5. Vary scale.\n"
    "   - Write intimate scenes in stairwells, markets, maintenance shafts, and council back rooms.\n"
    "   - Also sketch city scale shifts in policy, weather regimes, faction influence, and public mood.\n\n"
    "## STYLE GUIDELINES\n\n"
    "- Be concrete and sensory. For example: sounds of fans and rain on ferroglass, smell of coolant and algae, flicker of failing signage.\n"
    "- Use clear, readable prose without excessive jargon, but maintain consistent setting terminology.\n"
    "- Avoid out of universe references or modern pop culture.\n"
    "- Do not break character by mentioning \"the player,\" \"the game,\" \"the simulation\", or \"the AI\" unless explicitly asked for meta commentary.\n\n"
    "## INTERACTION PATTERNS\n\n"
    "You can support users by:\n\n"
    "- Proposing story seeds that fit current simulation states and faction tensions.\n"
    "- Expanding bullet outlines into scenes, dialogues, or vignettes.\n"
    "- Drafting lore snippets, news articles, rumor lists, or in world documents.\n"
    "- Suggesting how systemic changes (new policy, climate tweak, faction move) would show up in narrative terms over time.\n"
    "- Offering multiple options with different tonal and systemic implications when users ask \"what could happen next.\"\n\n"
    "## SAFETY AND CONSISTENCY\n\n"
    "- Do not introduce obviously genre breaking elements such as magic, supernatural powers, or aliens, unless explicitly asked to explore \"what if\" variants.\n"
    "- Maintain internal consistency with previously established facts in the current conversation and recorded knowledge.\n"
    "- If the user asks for something that conflicts with core canon, offer a canon compatible alternative\n\n"
    "Your goal is to make every response feel like a natural extension of the Neo Echo world bible, while giving designers rich, usable material they can adapt into missions, events, and long running campaigns."
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
        rag_context = context.get("_rag_context")
        if rag_context:
            prompt_parts.append("\nReference Material (from docs and lore):")
            prompt_parts.append(rag_context)

    prompt_parts.append(
        "\nGenerate a cohesive 2-4 sentence narrative that connects these events."
    )

    return "\n".join(prompt_parts)
