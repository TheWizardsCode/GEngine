"""Gateway session helpers."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Iterable

from ..cli.shell import CommandResult, EchoesShell, ShellBackend, _render_summary
from ..settings import SimulationLimits
from .intent_mapper import IntentMapper
from .llm_client import LLMClient

LOGGER = logging.getLogger("gengine.echoes.gateway")


class GatewaySession:
    """Wraps an ``EchoesShell`` for use over the gateway's WebSocket."""

    def __init__(
        self,
        backend: ShellBackend,
        *,
        limits: SimulationLimits,
        session_id: str | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.backend = backend
        self.shell = EchoesShell(backend, limits=limits)
        self.session_id = session_id or uuid.uuid4().hex[:8]
        self.llm_client = llm_client
        self.intent_mapper = IntentMapper()
        self.conversation_history: list[dict[str, str]] = []

    # Session lifecycle -------------------------------------------------
    def welcome(self) -> str:
        summary = self.backend.summary()
        self._log_focus(summary, label="welcome")
        return _render_summary(summary)

    def execute(self, command: str) -> CommandResult:
        result = self.shell.execute(command)
        keyword = _first_token(command)
        if keyword in {"summary", "focus", "history", "director"}:
            history_snapshot = None
            if keyword == "history":
                history_snapshot = self.backend.focus_history()
            summary = self.backend.summary()
            self._log_focus(summary, label=keyword, history_snapshot=history_snapshot)
        return result

    def execute_natural_language(self, text: str) -> CommandResult:
        """Execute a natural language command using LLM intent parsing.
        
        Args:
            text: Natural language text from user
            
        Returns:
            CommandResult with output or error
        """
        if not self.llm_client:
            return CommandResult(
                output="Natural language commands require LLM service",
                should_exit=False,
            )

        # Build context for intent parsing
        summary = self.backend.summary()
        context = self._build_intent_context(summary)
        
        # Parse intent with LLM
        LOGGER.info("Parsing NL command: %s", text[:100])
        intent = self.llm_client.parse_intent(text, context=context)
        
        if not intent:
            LOGGER.warning("Failed to parse intent from: %s", text)
            fallback = self._fallback_command(text)
            if fallback:
                LOGGER.info("Using fallback command: %s", fallback)
                result = self.shell.execute(fallback)
            else:
                result = CommandResult(
                    output="I couldn't understand that command. Try: summary, map, next, run <n>",
                    should_exit=False,
                )
            self.conversation_history.append({"user": text, "result": "fallback"})
            return result

        # Map intent to command
        try:
            command = self.intent_mapper.map_intent_to_command(intent)
            LOGGER.info("Mapped intent %s -> command: %s", type(intent).__name__, command)
        except ValueError as exc:
            LOGGER.error("Failed to map intent: %s", exc)
            result = CommandResult(
                output=f"Intent mapping failed: {exc}",
                should_exit=False,
            )
            self.conversation_history.append({"user": text, "result": "error"})
            return result

        # Execute the mapped command
        result = self.shell.execute(command)
        
        # Try to narrate the result if we have events
        if result.output and self.llm_client:
            narration = self._try_narrate(result.output, context)
            if narration:
                result = CommandResult(
                    output=f"{narration}\n\n{result.output}",
                    should_exit=result.should_exit,
                )
        
        self.conversation_history.append({
            "user": text,
            "intent": type(intent).__name__,
            "command": command,
        })
        
        return result

    def close(self) -> None:
        self.backend.close()
        if self.llm_client:
            self.llm_client.close()

    # Internal helpers --------------------------------------------------
    def _build_intent_context(self, summary: dict[str, Any]) -> dict[str, Any]:
        """Build context dictionary for LLM intent parsing."""
        context: dict[str, Any] = {}
        
        if "tick" in summary:
            context["tick"] = summary["tick"]
        
        if "focus" in summary and isinstance(summary["focus"], dict):
            focus_center = summary["focus"].get("district_id") or summary["focus"].get("focus_center")
            if focus_center:
                context["district"] = focus_center
        
        # Add recent events from digest if available
        if "focus_digest" in summary and isinstance(summary["focus_digest"], dict):
            events = summary["focus_digest"].get("events", [])
            if events:
                context["recent_events"] = events[:3]  # Limit to 3 most recent
        
        return context

    def _fallback_command(self, text: str) -> str | None:
        """Attempt keyword-based fallback when LLM parsing fails."""
        text_lower = text.lower()
        
        # Simple keyword matching for common commands
        if "summary" in text_lower or "status" in text_lower:
            return "summary"
        elif "map" in text_lower:
            return "map"
        elif "next" in text_lower or "advance" in text_lower:
            return "next"
        elif "history" in text_lower:
            return "history"
        elif "director" in text_lower:
            return "director"
        
        return None

    def _try_narrate(self, output: str, context: dict[str, Any]) -> str | None:
        """Try to generate narrative from command output."""
        if not self.llm_client:
            return None
        
        # Extract events from output for narration
        # For now, just pass the first few lines as events
        lines = output.strip().split("\n")
        events = [line.strip() for line in lines[:5] if line.strip()]
        
        if not events:
            return None
        
        narration = self.llm_client.narrate(events, context=context)
        return narration

    def _log_focus(
        self,
        summary: dict[str, object],
        *,
        label: str,
        history_snapshot: list[dict[str, object]] | None = None,
    ) -> None:
        focus = summary.get("focus") if isinstance(summary, dict) else None
        digest = summary.get("focus_digest") if isinstance(summary, dict) else None
        history = summary.get("focus_history") if isinstance(summary, dict) else None
        director_history = summary.get("director_history") if isinstance(summary, dict) else None
        focus_center = None
        if isinstance(focus, dict):
            focus_center = focus.get("district_id") or focus.get("focus_center")
        suppressed = 0
        if isinstance(digest, dict):
            suppressed = int(digest.get("suppressed_count") or 0)
        if history_snapshot is not None:
            history_len = len(history_snapshot)
        else:
            history_len = len(history or []) if isinstance(history, Iterable) else 0
        director_history_len = len(director_history or []) if isinstance(director_history, Iterable) else 0
        tick = summary.get("tick") if isinstance(summary, dict) else None
        LOGGER.info(
            "gateway session=%s label=%s tick=%s focus=%s suppressed=%s history=%s director_history=%s",
            self.session_id,
            label,
            tick,
            focus_center or "unset",
            suppressed,
            history_len,
            director_history_len,
        )


def _first_token(command: str) -> str:
    command = (command or "").strip()
    if not command:
        return ""
    return command.split()[0].lower()
