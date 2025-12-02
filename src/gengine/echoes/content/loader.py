"""Utilities for loading authored world content into a :class:`GameState`."""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Dict, Optional, Set

import yaml
from pydantic import ValidationError

from ..core.models import (
    Agent,
    City,
    DistrictCoordinates,
    EnvironmentState,
    Faction,
    StorySeed,
)
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
    _enrich_district_geometry(city)

    factions_raw = raw.get("factions", []) or []
    agents_raw = raw.get("agents", []) or []
    env_raw = raw.get("environment", {}) or {}
    metadata = raw.get("metadata", {}) or {}

    factions = {
        faction.id: faction
        for faction in (
            Faction.model_validate(entry)
            for entry in factions_raw  # type: ignore[arg-type]
        )
    }
    agents = {
        agent.id: agent
        for agent in (
            Agent.model_validate(entry)
            for entry in agents_raw  # type: ignore[arg-type]
        )
    }
    environment = EnvironmentState.model_validate(env_raw)

    seed_path = root / world_name / "story_seeds.yml"
    story_seeds = _load_story_seeds(
        seed_path,
        city=city,
        agent_ids=set(agents),
        faction_ids=set(factions),
    )

    seed = seed_override if seed_override is not None else metadata.get("seed")
    if seed is None:
        seed = random.randint(0, 1_000_000)

    return GameState(
        city=city,
        factions=factions,
        agents=agents,
        story_seeds=story_seeds,
        environment=environment,
        seed=int(seed),
        metadata=dict(metadata),
    )


def _enrich_district_geometry(city: City, *, max_neighbors: int = 3) -> None:
    """Ensure adjacency lists exist and stay consistent with coordinates."""

    coords = {
        district.id: district.coordinates
        for district in city.districts
        if district.coordinates is not None
    }
    if not coords:
        return
    for district in city.districts:
        geometry = coords.get(district.id)
        if geometry is None:
            continue
        existing = list(district.adjacent)
        needed = max(0, max_neighbors - len(existing))
        if needed <= 0:
            continue
        candidates = [
            other
            for other in city.districts
            if other.id != district.id and other.coordinates
        ]
        candidates.sort(key=lambda other: _distance(geometry, other.coordinates))  # type: ignore[arg-type]
        for candidate in candidates:
            if candidate.id in existing:
                continue
            existing.append(candidate.id)
            if len(existing) >= max_neighbors:
                break
        district.adjacent = existing

    adjacency: Dict[str, set[str]] = {
        district.id: set(district.adjacent) for district in city.districts
    }
    for district in city.districts:
        for neighbor in list(adjacency[district.id]):
            adjacency.setdefault(neighbor, set()).add(district.id)
    for district in city.districts:
        ordered = list(dict.fromkeys(district.adjacent))
        for neighbor in sorted(adjacency[district.id]):
            if neighbor not in ordered:
                ordered.append(neighbor)
        district.adjacent = ordered


def _distance(a: DistrictCoordinates, b: DistrictCoordinates) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    dz = (a.z or 0.0) - (b.z or 0.0)
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def _load_story_seeds(
    path: Path,
    *,
    city: City,
    agent_ids: Set[str],
    faction_ids: Set[str],
) -> Dict[str, StorySeed]:
    if not path.exists():
        return {}
    raw = _load_yaml(path)
    entries = raw.get("story_seeds") if isinstance(raw, dict) else raw
    if entries is None and isinstance(raw, dict):
        entries = raw.get("seeds")
    if entries is None:
        entries = []
    if not isinstance(entries, list):
        raise ValueError("story seeds file must contain a list under 'story_seeds'")
    seeds: Dict[str, StorySeed] = {}
    known_districts = {district.id for district in city.districts}
    for entry in entries:
        seed = StorySeed.model_validate(entry)
        _validate_story_seed_references(
            seed,
            districts=known_districts,
            agent_ids=agent_ids,
            faction_ids=faction_ids,
        )
        seeds[seed.id] = seed
    _validate_story_seed_followups(seeds)
    return seeds


def _validate_story_seed_references(
    seed: StorySeed,
    *,
    districts: Set[str],
    agent_ids: Set[str],
    faction_ids: Set[str],
) -> None:
    errors: list[str] = []
    for district_id in seed.preferred_districts:
        if district_id not in districts:
            errors.append(f"unknown district '{district_id}' in preferred_districts")
    for trigger in seed.triggers:
        if trigger.district_id and trigger.district_id not in districts:
            errors.append(f"unknown district '{trigger.district_id}' in trigger")
    if seed.travel_hint and seed.travel_hint.district_id:
        if seed.travel_hint.district_id not in districts:
            errors.append(
                f"unknown district '{seed.travel_hint.district_id}' in travel_hint"
            )
    for agent_id in seed.roles.agents:
        if agent_id not in agent_ids:
            errors.append(f"unknown agent '{agent_id}' in roles")
    for faction_id in seed.roles.factions:
        if faction_id not in faction_ids:
            errors.append(f"unknown faction '{faction_id}' in roles")
    if errors:
        raise ValueError(f"Invalid story seed '{seed.id}': " + "; ".join(errors))


def _validate_story_seed_followups(seeds: Dict[str, StorySeed]) -> None:
    errors: list[str] = []
    for seed in seeds.values():
        for followup_id in seed.followups:
            if followup_id not in seeds:
                errors.append(f"{seed.id} references unknown followup '{followup_id}'")
    if errors:
        raise ValueError("Invalid story seed followups: " + "; ".join(errors))
