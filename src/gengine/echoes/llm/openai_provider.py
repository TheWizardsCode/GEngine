"""OpenAI LLM provider implementation using function calling."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from . import parse_intent
from .prompts import (
    INTENT_PARSING_SYSTEM_PROMPT,
    NARRATION_SYSTEM_PROMPT,
    OPENAI_INTENT_FUNCTIONS,
    build_intent_parsing_prompt,
    build_narration_prompt,
)
from .providers import IntentParseResult, LLMProvider, NarrateResult
from .settings import LLMSettings

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider using function calling for structured outputs."""

    def __init__(self, settings: LLMSettings) -> None:
        """Initialize OpenAI provider.

        Parameters
        ----------
        settings
            LLM configuration settings
        """
        super().__init__(settings)
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_retries,
        )
        self.model = settings.model or "gpt-4-turbo-preview"

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        """Parse user input into structured intents using function calling.

        Parameters
        ----------
        user_input
            Natural language input from user
        context
            Game state context for intent parsing

        Returns
        -------
        IntentParseResult
            Parsed intents with metadata
        """
        try:
            prompt = build_intent_parsing_prompt(user_input, context=context)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTENT_PARSING_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                functions=OPENAI_INTENT_FUNCTIONS,
                function_call="auto",
                temperature=0.3,
            )

            raw_response = response.model_dump_json()
            message = response.choices[0].message

            # Extract function call if present
            intents = []
            if message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                # Convert function call to GameIntent
                intent_dict = self._function_call_to_intent(
                    function_name, function_args, context
                )
                if intent_dict:
                    intents.append(intent_dict)

            # Calculate confidence based on response
            confidence = 0.9 if intents else 0.3

            logger.info(
                f"OpenAI parsed intent: {len(intents)} intent(s) from '{user_input[:50]}...'"
            )

            return IntentParseResult(
                intents=intents,
                raw_response=raw_response,
                confidence=confidence,
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API error during intent parsing: {e}")
            return IntentParseResult(
                intents=[],
                raw_response=str(e),
                confidence=0.0,
            )

    async def narrate(
        self,
        events: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> NarrateResult:
        """Generate narrative description using chat completions.

        Parameters
        ----------
        events
            List of game events to narrate
        context
            Game state context for narrative generation

        Returns
        -------
        NarrateResult
            Generated narrative with metadata
        """
        try:
            # Convert event dicts to strings
            event_strings = [
                e.get("description", str(e)) for e in events
            ]
            prompt = build_narration_prompt(event_strings, context=context)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": NARRATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            raw_response = response.model_dump_json()
            narrative = response.choices[0].message.content or ""

            metadata = {
                "model": self.model,
                "event_count": len(events),
                "tokens_used": response.usage.total_tokens if response.usage else 0,
            }

            logger.info(f"OpenAI narrated {len(events)} events")

            return NarrateResult(
                narrative=narrative,
                raw_response=raw_response,
                metadata=metadata,
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API error during narration: {e}")
            return NarrateResult(
                narrative="",
                raw_response=str(e),
                metadata={"error": str(e)},
            )

    def _function_call_to_intent(
        self,
        function_name: str,
        args: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Convert OpenAI function call to GameIntent dict.

        Parameters
        ----------
        function_name
            Name of the called function
        args
            Function arguments
        context
            Game context (includes session_id)

        Returns
        -------
        dict | None
            Intent dictionary suitable for parse_intent(), or None if conversion fails
        """
        # Map function names to intent types
        function_to_intent = {
            "inspect_target": "INSPECT",
            "negotiate_with_faction": "NEGOTIATE",
            "deploy_resource": "DEPLOY_RESOURCE",
            "pass_policy": "PASS_POLICY",
            "covert_action": "COVERT_ACTION",
            "invoke_agent": "INVOKE_AGENT",
            "request_report": "REQUEST_REPORT",
        }

        intent_type = function_to_intent.get(function_name)
        if not intent_type:
            logger.warning(f"Unknown function name: {function_name}")
            return None

        # Build intent dict with session_id from context
        intent_dict = {
            "intent": intent_type,
            "session_id": context.get("session_id", "unknown"),
        }

        # Map function args to intent fields based on type
        if intent_type == "INSPECT":
            intent_dict.update({
                "target_type": args.get("target_type"),
                "target_id": args.get("target_id"),
                "focus_areas": args.get("focus_areas", []),
            })
        elif intent_type == "NEGOTIATE":
            intent_dict.update({
                "targets": args.get("targets", []),
                "levers": args.get("levers", {}),
                "goal": args.get("goal", ""),
            })
        elif intent_type == "DEPLOY_RESOURCE":
            intent_dict.update({
                "resource_type": args.get("resource_type"),
                "amount": args.get("amount"),
                "target_district": args.get("target_district"),
                "purpose": args.get("purpose"),
            })
        elif intent_type == "PASS_POLICY":
            intent_dict.update({
                "policy_id": args.get("policy_id"),
                "parameters": args.get("parameters", {}),
                "duration_ticks": args.get("duration_ticks"),
            })
        elif intent_type == "COVERT_ACTION":
            intent_dict.update({
                "action_type": args.get("action_type"),
                "target_district": args.get("target_district"),
                "target_faction": args.get("target_faction"),
                "parameters": args.get("parameters", {}),
                "risk_level": args.get("risk_level"),
            })
        elif intent_type == "INVOKE_AGENT":
            intent_dict.update({
                "agent_id": args.get("agent_id"),
                "action": args.get("action"),
                "target": args.get("target"),
                "parameters": args.get("parameters", {}),
            })
        elif intent_type == "REQUEST_REPORT":
            intent_dict.update({
                "report_type": args.get("report_type"),
                "filters": args.get("filters", {}),
                "include_history": args.get("include_history", False),
            })

        return intent_dict
