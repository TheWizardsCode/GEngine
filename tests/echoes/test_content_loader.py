"""Smoke tests for the initial Echoes world data and loaders."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from gengine.echoes.content import load_world_bundle
from gengine.echoes.content.loader import (
    _CONTENT_ENV_VARIABLE,
    _load_yaml,
    _resolve_world_root,
)
from gengine.echoes.persistence import load_snapshot, save_snapshot


def test_load_world_bundle_default_world() -> None:
    state = load_world_bundle()

    summary = state.summary()
    assert summary["city"] == "Neo Echo"
    assert summary["districts"] >= 3
    assert summary["factions"] >= 3
    assert summary["agents"] >= 4
    assert state.city.districts[0].resources


def test_snapshot_round_trip(tmp_path: Path) -> None:
    state = load_world_bundle()
    target = tmp_path / "snapshot.json"

    saved_path = save_snapshot(state, target)
    assert saved_path.exists()

    restored = load_snapshot(saved_path)
    assert restored.summary() == state.summary()
    assert restored.city.districts[1].name == state.city.districts[1].name


def test_load_world_bundle_missing_definition(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_world_bundle("ghost", content_root=tmp_path)


def test_load_world_bundle_seed_override() -> None:
    state = load_world_bundle(seed_override=123)

    assert state.seed == 123


def test_load_yaml_requires_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text("- not-a-mapping", encoding="utf-8")

    with pytest.raises(ValueError):
        _load_yaml(bad)


def test_resolve_world_root_honors_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(_CONTENT_ENV_VARIABLE, str(tmp_path))

    resolved = _resolve_world_root()

    assert resolved == tmp_path


def test_load_world_bundle_generates_seed_when_missing(tmp_path: Path) -> None:
    world_root = tmp_path / "custom"
    world_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "city": {
            "id": "custom-city",
            "name": "Custom City",
            "districts": [
                {
                    "id": "core",
                    "name": "Core",
                    "population": 1000,
                    "resources": {},
                }
            ],
        },
        "factions": [],
        "agents": [],
    }
    (world_root / "world.yml").write_text(yaml.safe_dump(payload), encoding="utf-8")

    state = load_world_bundle("custom", content_root=tmp_path)

    assert 0 <= state.seed <= 1_000_000


def test_geometry_enrichment_derives_adjacency(tmp_path: Path) -> None:
    world_root = tmp_path / "geom"
    world_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "city": {
            "id": "geom-city",
            "name": "Geom City",
            "districts": [
                {
                    "id": "alpha",
                    "name": "Alpha",
                    "population": 10_000,
                    "coordinates": {"x": 0.0, "y": 0.0},
                },
                {
                    "id": "beta",
                    "name": "Beta",
                    "population": 8_000,
                    "coordinates": {"x": 4.0, "y": 0.0},
                },
                {
                    "id": "gamma",
                    "name": "Gamma",
                    "population": 6_000,
                    "coordinates": {"x": 0.0, "y": 4.0},
                },
            ],
        },
        "factions": [],
        "agents": [],
    }
    (world_root / "world.yml").write_text(yaml.safe_dump(payload), encoding="utf-8")

    state = load_world_bundle("geom", content_root=tmp_path)

    adjacency = {
        district.id: set(district.adjacent) for district in state.city.districts
    }
    assert adjacency["alpha"] == {"beta", "gamma"}
    assert adjacency["beta"] == {"alpha", "gamma"}
    assert adjacency["gamma"] == {"alpha", "beta"}


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"preferred_districts": ["unknown"]}, "unknown district 'unknown'"),
        (
            {
                "triggers": [
                    {
                        "scope": "environment",
                        "district_id": "unknown",
                        "min_score": 0.5,
                        "min_severity": 0.5,
                    }
                ]
            },
            "unknown district 'unknown'",
        ),
        ({"travel_hint": {"district_id": "unknown"}}, "unknown district 'unknown'"),
        (
            {"roles": {"agents": ["ghost"], "factions": ["union-of-flux"]}},
            "unknown agent 'ghost'",
        ),
        (
            {"roles": {"agents": ["aria-volt"], "factions": ["ghost"]}},
            "unknown faction 'ghost'",
        ),
    ],
)
def test_story_seed_loader_validates_entity_references(
    tmp_path: Path, overrides: dict, message: str
) -> None:
    world_root = _write_story_seed_world(tmp_path, world_name="seed-refs")
    _write_story_seeds_file(world_root, [_story_seed_payload(**overrides)])

    with pytest.raises(ValueError, match=message):
        load_world_bundle(world_root.name, content_root=tmp_path)


def test_story_seed_loader_validates_followups(tmp_path: Path) -> None:
    world_root = _write_story_seed_world(tmp_path, world_name="seed-followups")
    seeds = [_story_seed_payload(id="alpha", followups=["beta"])]
    _write_story_seeds_file(world_root, seeds)

    with pytest.raises(ValueError, match="unknown followup 'beta'"):
        load_world_bundle(world_root.name, content_root=tmp_path)


def _write_story_seed_world(tmp_path: Path, *, world_name: str) -> Path:
    world_root = tmp_path / world_name
    world_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "city": {
            "id": "test-city",
            "name": "Test City",
            "districts": [
                {
                    "id": "core",
                    "name": "Core",
                    "population": 10_000,
                },
                {
                    "id": "spire",
                    "name": "Spire",
                    "population": 8_000,
                },
            ],
        },
        "factions": [
            {
                "id": "union-of-flux",
                "name": "Union of Flux",
            }
        ],
        "agents": [
            {
                "id": "aria-volt",
                "name": "Aria Volt",
                "role": "Advocate",
            }
        ],
    }
    (world_root / "world.yml").write_text(yaml.safe_dump(payload), encoding="utf-8")
    return world_root


def _story_seed_payload(**overrides):
    seed_id = overrides.get("id", "seed-a")
    payload = {
        "id": seed_id,
        "title": "Test Seed",
        "summary": "Test summary",
        "stakes": "Citywide unrest rises",
        "scope": "environment",
        "preferred_districts": ["core"],
        "cooldown_ticks": 5,
        "tags": ["test"],
        "triggers": [
            {
                "scope": "environment",
                "district_id": "core",
                "min_score": 0.5,
                "min_severity": 0.5,
            }
        ],
        "roles": {
            "agents": ["aria-volt"],
            "factions": ["union-of-flux"],
        },
        "beats": ["Test beat"],
        "resolution_templates": {
            "success": "Stability recovered",
            "failure": "Faction unrest worsens",
        },
        "travel_hint": {"district_id": "core"},
        "followups": [],
    }
    payload.update(overrides)
    return payload


def _write_story_seeds_file(world_root: Path, seeds: list[dict]) -> None:
    (world_root / "story_seeds.yml").write_text(
        yaml.safe_dump({"story_seeds": seeds}),
        encoding="utf-8",
    )

def test_load_world_bundle_custom_content(tmp_path: Path) -> None:
    """Verify loader logic with controlled content."""
    world_dir = tmp_path / "custom_world"
    world_dir.mkdir()
    
    # Create minimal world.yml
    world_data = {
        "city": {
            "id": "test-city",
            "name": "Test City",
            "districts": [
                {
                    "id": "d1", 
                    "name": "District 1", 
                    "population": 1000,
                    "coordinates": {"x": 0.0, "y": 0.0}
                }
            ]
        },
        "factions": [
            {
                "id": "f1", 
                "name": "Faction 1", 
                "ideology": "Test", 
                "legitimacy": 0.5,
                "resources": {"capital": 10},
                "territory": ["d1"],
                "description": "Test faction"
            }
        ],
        "agents": [
            {
                "id": "a1", 
                "name": "Agent 1", 
                "role": "Tester", 
                "home_district": "d1",
                "traits": {"resolve": 0.5},
                "goals": []
            }
        ],
        "environment": {
            "stability": 0.8,
            "unrest": 0.1,
            "pollution": 0.0,
            "climate_risk": 0.0,
            "security": 0.9
        },
        "metadata": {"seed": 999}
    }
    
    with (world_dir / "world.yml").open("w") as f:
        yaml.dump(world_data, f)
        
    # Create minimal story_seeds.yml (required by loader)
    seeds_data = {"story_seeds": []}
    with (world_dir / "story_seeds.yml").open("w") as f:
        yaml.dump(seeds_data, f)

    # Load from the temp directory
    # Note: load_world_bundle expects content_root to contain the world folder
    state = load_world_bundle("custom_world", content_root=tmp_path)

    summary = state.summary()
    assert summary["city"] == "Test City"
    assert summary["districts"] == 1
    assert summary["factions"] == 1
    assert summary["agents"] == 1
    assert state.seed == 999
