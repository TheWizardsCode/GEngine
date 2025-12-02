"""Anthropic LLM provider implementation using structured outputs."""

from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import Anthropic, AnthropicError

from .prompts import (
    ANTHROPIC_INTENT_SCHEMA,
    INTENT_PARSING_SYSTEM_PROMPT,
    NARRATION_SYSTEM_PROMPT,
    build_intent_parsing_prompt,
    build_narration_prompt,
)
from .providers import IntentParseResult, LLMProvider, NarrateResult
from .settings import LLMSettings

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider using structured outputs."""

    def __init__(self, settings: LLMSettings) -> None:
        """Initialize Anthropic provider.

        Parameters
        ----------
        settings
            LLM configuration settings
        """
        super().__init__(settings)
        self.client = Anthropic(
            api_key=settings.api_key,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_retries,
        )
        self.model = settings.model or "claude-3-5-sonnet-20241022"

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        """Parse user input into structured intents using structured outputs.

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

            # Build prompt with schema instructions
            full_prompt = f"""{prompt}

Respond with a JSON object matching this schema:
{json.dumps(ANTHROPIC_INTENT_SCHEMA, indent=2)}

Ensure the response is valid JSON that can be parsed."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system=INTENT_PARSING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": full_prompt}],
            )

            raw_response = response.model_dump_json()

            # Extract JSON from response
            content = response.content[0].text if response.content else ""

            # Try to parse JSON from content
            intents = []
            confidence = 0.0

            try:
                # Look for JSON in the response
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    parsed = json.loads(json_str)

                    # Convert to intent dict with session_id
                    intent_dict = self._structured_output_to_intent(parsed, context)
                    if intent_dict:
                        intents.append(intent_dict)
                        confidence = parsed.get("confidence", 0.8)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Anthropic response: {e}")

            logger.info(
                f"Anthropic parsed intent: {len(intents)} intent(s) "
                f"from '{user_input[:50]}...'"
            )

            return IntentParseResult(
                intents=intents,
                raw_response=raw_response,
                confidence=confidence,
            )

        except AnthropicError as e:
            logger.error(f"Anthropic API error during intent parsing: {e}")
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
        """Generate narrative description using messages API.

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
            event_strings = [e.get("description", str(e)) for e in events]
            prompt = build_narration_prompt(event_strings, context=context)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                system=NARRATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_response = response.model_dump_json()
            narrative = response.content[0].text if response.content else ""

            metadata = {
                "model": self.model,
                "event_count": len(events),
                "tokens_used": response.usage.input_tokens
                + response.usage.output_tokens
                if response.usage
                else 0,
            }

            logger.info(f"Anthropic narrated {len(events)} events")

            return NarrateResult(
                narrative=narrative,
                raw_response=raw_response,
                metadata=metadata,
            )

        except AnthropicError as e:
            logger.error(f"Anthropic API error during narration: {e}")
            return NarrateResult(
                narrative="",
                raw_response=str(e),
                metadata={"error": str(e)},
            )

    def _structured_output_to_intent(
        self,
        structured_output: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Convert Anthropic structured output to GameIntent dict.

        Parameters
        ----------
        structured_output
            Parsed JSON from Anthropic response
        context
            Game context (includes session_id)

        Returns
        -------
        dict | None
            Intent dictionary suitable for parse_intent(), or None if conversion fails
        """
        intent_type = structured_output.get("intent_type")
        if not intent_type:
            logger.warning("No intent_type in structured output")
            return None

        parameters = structured_output.get("parameters", {})

        # Build intent dict with session_id from context
        intent_dict = {
            "intent": intent_type,
            "session_id": context.get("session_id", "unknown"),
        }

        # Copy parameters directly - they should match intent field names
        intent_dict.update(parameters)

        return intent_dict
