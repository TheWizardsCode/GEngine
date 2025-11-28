"""Utilities for loading authored world content into a :class:`GameState`."""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import ValidationError

from ..core.models import Agent, City, EnvironmentState, Faction
from ..core.state import GameState

DEFAULT_WORLD_NAME = "default"
_CONTENT_ENV_VARIABLE = "ECHOES_WORLD_ROOT"


def _default_world_root() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "content" / "worlds"


def _resolve_world_root(content_root: Optional[Path] = None) -> Path:
    if content_root is not None:
        return content_root
    env_root = os.environ.get(_CONTENT_ENV_VARIABLE)
    if env_root:
        return Path(env_root)
    return _default_world_root()


def _load_yaml(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"World definition not found at {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at root of {path}")
    return data


def load_world_bundle(
    world_name: str = DEFAULT_WORLD_NAME,
    *,
    content_root: Optional[Path] = None,
    seed_override: Optional[int] = None,
) -> GameState:
    """Load a world definition and build a :class:`GameState` instance."""

    root = _resolve_world_root(content_root)
    world_path = root / world_name / "world.yml"
    raw = _load_yaml(world_path)

    try:
        city = City.model_validate(raw["city"])
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise KeyError("World definition is missing 'city'") from exc
    except ValidationError as exc:  # pragma: no cover - validation detail
        raise ValueError(f"Invalid city definition: {exc}") from exc

    factions_raw = raw.get("factions", []) or []
    agents_raw = raw.get("agents", []) or []
    env_raw = raw.get("environment", {}) or {}
    metadata = raw.get("metadata", {}) or {}

    factions = {
        faction.id: faction
        for faction in (
            Faction.model_validate(entry) for entry in factions_raw  # type: ignore[arg-type]
        )
    }
    agents = {
        agent.id: agent
        for agent in (
            Agent.model_validate(entry) for entry in agents_raw  # type: ignore[arg-type]
        )
    }
    environment = EnvironmentState.model_validate(env_raw)

    seed = seed_override if seed_override is not None else metadata.get("seed")
    if seed is None:
        seed = random.randint(0, 1_000_000)

    return GameState(
        city=city,
        factions=factions,
        agents=agents,
        environment=environment,
        seed=int(seed),
        metadata=dict(metadata),
    )
