"""Gateway session helpers."""

from __future__ import annotations

import logging
import uuid
from typing import Iterable

from ..cli.shell import CommandResult, EchoesShell, ShellBackend, _render_summary
from ..settings import SimulationLimits

LOGGER = logging.getLogger("gengine.echoes.gateway")


class GatewaySession:
    """Wraps an ``EchoesShell`` for use over the gateway's WebSocket."""

    def __init__(
        self,
        backend: ShellBackend,
        *,
        limits: SimulationLimits,
        session_id: str | None = None,
    ) -> None:
        self.backend = backend
        self.shell = EchoesShell(backend, limits=limits)
        self.session_id = session_id or uuid.uuid4().hex[:8]

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

    def close(self) -> None:
        self.backend.close()

    # Internal helpers --------------------------------------------------
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
