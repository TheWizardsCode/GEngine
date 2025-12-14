"""Foundry Local LLM provider implementation."""

from __future__ import annotations

import json
import logging
import socket
from typing import Any

import httpx

from .prompts import (
    INTENT_PARSING_SYSTEM_PROMPT,
    NARRATION_SYSTEM_PROMPT,
    OPENAI_INTENT_FUNCTIONS,
    build_intent_parsing_prompt,
    build_narration_prompt,
)
from .providers import IntentParseResult, LLMProvider, NarrateResult
from .settings import LLMSettings

LOGGER = logging.getLogger(__name__)


def _format_foundry_error(exc: httpx.HTTPError, base_url: str) -> str:
    """Convert HTTP errors into actionable troubleshooting hints."""
    if isinstance(exc, httpx.ConnectError):
        cause = exc.__cause__
        if isinstance(cause, socket.gaierror):
            return (
                f"Failed to resolve Foundry Local host in '{base_url}'. "
                "Ensure the service is running on Windows and that "
                "ECHOES_LLM_BASE_URL points to a reachable host/port."
            )
        return (
            f"Could not connect to Foundry Local at '{base_url}': {exc}. "
            "Verify the service is running and the port is open."
        )
    if isinstance(exc, httpx.HTTPStatusError):
        body = exc.response.text[:200] if exc.response else ""
        return (
            f"Foundry Local responded with HTTP {exc.response.status_code}: {body}"
        )
    return str(exc)


class FoundryLocalProvider(LLMProvider):
    """Provider that talks to the Foundry Local OpenAI-compatible API."""

    def __init__(
        self,
        settings: LLMSettings,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        super().__init__(settings)
        self.base_url = (settings.base_url or "http://localhost:5272").rstrip("/")
        self.model = settings.model or "qwen2.5-0.5b-instruct-generic-cpu"
        self._transport = transport

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        """Parse user input into structured intents via Foundry Local."""
        prompt = build_intent_parsing_prompt(user_input, context=context)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": INTENT_PARSING_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.3,
            "functions": OPENAI_INTENT_FUNCTIONS,
            "function_call": "auto",
        }
        LOGGER.info("FoundryLocalProvider.parse_intent prompt: %s", prompt)
        LOGGER.info("FoundryLocalProvider.parse_intent payload: %s", json.dumps(payload, indent=2))
        try:
            data, raw_text = await self._chat_completion(payload)
            try:
                import json as _json
                pretty = _json.dumps(data, indent=2, ensure_ascii=False)
                LOGGER.info("FoundryLocalProvider.parse_intent response (pretty):\n%s", pretty)
            except Exception:
                LOGGER.info("FoundryLocalProvider.parse_intent response (raw): %s", raw_text)
            intents = []
            choices = data.get("choices") or []
            if choices:
                message = choices[0].get("message", {})
                function_call = message.get("function_call")
                if function_call:
                    try:
                        args = json.loads(function_call.get("arguments") or "{}")
                    except json.JSONDecodeError as exc:
                        LOGGER.warning("Foundry function args not JSON: %s", exc)
                        args = {}
                    intent_dict = self._function_call_to_intent(
                        function_call.get("name", ""),
                        args,
                        context,
                    )
                    if intent_dict:
                        intents.append(intent_dict)
                else:
                    # Fallback: try to extract intent from message content (code block or plain text)
                    content = message.get("content", "")
                    # Try to extract code block
                    import re
                    code_block = None
                    code_block_match = re.search(r"```(?:json)?\n(.*?)```", content, re.DOTALL)
                    if code_block_match:
                        code_block = code_block_match.group(1).strip()
                    if code_block:
                        try:
                            intent_dict = json.loads(code_block)
                            if isinstance(intent_dict, dict):
                                intents.append(intent_dict)
                        except Exception as exc:
                            LOGGER.info("Failed to parse code block as JSON: %s", exc)
                    else:
                        # Try to parse intent from plain text (very basic fallback)
                        # Example: look for lines like 'Action: INSPECT', 'Target: districts', etc.
                        lines = content.splitlines()
                        intent_dict = {}
                        for line in lines:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                key = key.strip().lower()
                                value = value.strip()
                                if key and value:
                                    intent_dict[key] = value
                        if intent_dict:
                            intents.append(intent_dict)

            confidence = 0.9 if intents else 0.3
            LOGGER.info(
                "Foundry Local parsed %d intent(s) from '%s...'",
                len(intents),
                user_input[:50],
            )
            return IntentParseResult(
                intents=intents,
                raw_response=raw_text,
                confidence=confidence,
            )
        except httpx.HTTPError as exc:
            message = _format_foundry_error(exc, self.base_url)
            LOGGER.error("Foundry Local intent parsing failed: %s", message)
            return IntentParseResult(intents=[], raw_response=message, confidence=0.0)

    async def narrate(
        self,
        events: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> NarrateResult:
        """Generate narration via Foundry Local."""
        event_strings = [event.get("description", str(event)) for event in events]
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": NARRATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_narration_prompt(event_strings, context=context),
                },
            ],
            "temperature": self.settings.temperature,
            "max_tokens": min(self.settings.max_tokens, 1000),
        }
        try:
            data, raw_text = await self._chat_completion(payload)
            choices = data.get("choices") or []
            message = choices[0].get("message", {}) if choices else {}
            narrative = message.get("content", "") or ""
            usage = data.get("usage") or {}
            metadata = {
                "model": self.model,
                "event_count": len(events),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            }
            LOGGER.info("Foundry Local narrated %d events", len(events))
            return NarrateResult(
                narrative=narrative,
                raw_response=raw_text,
                metadata=metadata,
            )
        except httpx.HTTPError as exc:
            message = _format_foundry_error(exc, self.base_url)
            LOGGER.error("Foundry Local narration failed: %s", message)
            return NarrateResult(
                narrative="",
                raw_response=message,
                metadata={"error": message},
            )

    async def _chat_completion(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], str]:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.settings.timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            return response.json(), response.text

    def _function_call_to_intent(
        self,
        function_name: str,
        args: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
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
            LOGGER.warning("Unknown Foundry function: %s", function_name)
            return None

        intent_dict = {
            "intent": intent_type,
            "session_id": context.get("session_id", "unknown"),
        }
        if intent_type == "INSPECT":
            intent_dict.update(
                {
                    "target_type": args.get("target_type"),
                    "target_id": args.get("target_id"),
                    "focus_areas": args.get("focus_areas", []),
                }
            )
        elif intent_type == "NEGOTIATE":
            intent_dict.update(
                {
                    "targets": args.get("targets", []),
                    "levers": args.get("levers", {}),
                    "goal": args.get("goal", ""),
                }
            )
        elif intent_type == "DEPLOY_RESOURCE":
            intent_dict.update(
                {
                    "resource_type": args.get("resource_type"),
                    "amount": args.get("amount"),
                    "target_district": args.get("target_district"),
                    "purpose": args.get("purpose"),
                }
            )
        elif intent_type == "PASS_POLICY":
            intent_dict.update(
                {
                    "policy_id": args.get("policy_id"),
                    "parameters": args.get("parameters", {}),
                    "duration_ticks": args.get("duration_ticks"),
                }
            )
        elif intent_type == "COVERT_ACTION":
            intent_dict.update(
                {
                    "action_type": args.get("action_type"),
                    "target_district": args.get("target_district"),
                    "target_faction": args.get("target_faction"),
                    "parameters": args.get("parameters", {}),
                    "risk_level": args.get("risk_level"),
                }
            )
        elif intent_type == "INVOKE_AGENT":
            intent_dict.update(
                {
                    "agent_id": args.get("agent_id"),
                    "action": args.get("action"),
                    "target": args.get("target"),
                    "parameters": args.get("parameters", {}),
                }
            )
        elif intent_type == "REQUEST_REPORT":
            intent_dict.update(
                {
                    "report_type": args.get("report_type"),
                    "filters": args.get("filters", {}),
                    "include_history": args.get("include_history", False),
                }
            )

        return intent_dict
