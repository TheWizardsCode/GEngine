"""Additional coverage for snapshot persistence helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.persistence.snapshot import (
    _json_default,
    load_snapshot,
    save_snapshot,
)


def test_json_default_rejects_unknown_type() -> None:
    with pytest.raises(TypeError):
        _json_default(object())


def test_load_snapshot_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "missing.json")


def test_load_snapshot_requires_mapping(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        load_snapshot(source)


def test_save_snapshot_creates_parent(tmp_path: Path) -> None:
    state = load_world_bundle()
    target = tmp_path / "nested" / "state.json"

    path = save_snapshot(state, target)

    assert path.exists()
    assert path.parent.name == "nested"
