"""Snapshot persistence helpers for Echoes of Emergence."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.state import GameState


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def save_snapshot(state: GameState, path: Path | str, *, indent: int = 2) -> Path:
    """Save ``state`` to ``path`` as JSON and return the resolved path."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = state.snapshot()
    target.write_text(
        json.dumps(payload, indent=indent, default=_json_default), encoding="utf-8"
    )
    return target


def load_snapshot(path: Path | str) -> GameState:
    """Load a :class:`GameState` snapshot from disk."""

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Snapshot file not found at {source}")
    data: Any = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Snapshot root must be a mapping")
    return GameState.from_snapshot(data)
