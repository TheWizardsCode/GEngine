"""Smoke tests for the initial Echoes world data and loaders."""

from __future__ import annotations

import os
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
    assert summary["districts"] == 3
    assert summary["factions"] == 2
    assert summary["agents"] == 3
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
