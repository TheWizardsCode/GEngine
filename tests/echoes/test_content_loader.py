"""Smoke tests for the initial Echoes world data and loaders."""

from __future__ import annotations

from pathlib import Path

from gengine.echoes.content import load_world_bundle
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
