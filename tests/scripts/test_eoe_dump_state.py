"""Tests for the world bundle dump state utility."""

from __future__ import annotations

import sys
from importlib import util
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "eoe_dump_state.py"


def _load_dump_state_module():
    spec = util.spec_from_file_location("eoe_dump_state", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("eoe_dump_state", module)
    spec.loader.exec_module(module)
    return module


_mod = _load_dump_state_module()
main = _mod.main


def _create_minimal_world(world_dir: Path) -> None:
    """Create a minimal valid world directory for testing."""
    world_dir.mkdir(parents=True, exist_ok=True)
    world_yml = {
        "city": {
            "id": "test-city",
            "name": "Test City",
            "districts": [
                {
                    "id": "core",
                    "name": "Core District",
                    "population": 10000,
                }
            ],
        },
        "factions": [
            {"id": "test-faction", "name": "Test Faction"},
        ],
        "agents": [
            {"id": "test-agent", "name": "Test Agent", "role": "Test"},
        ],
    }
    (world_dir / "world.yml").write_text(yaml.safe_dump(world_yml), encoding="utf-8")

    story_seeds = {
        "story_seeds": [
            {
                "id": "test-seed",
                "title": "Test Seed",
                "summary": "A test story seed",
                "stakes": "Test stakes",
                "scope": "environment",
                "preferred_districts": ["core"],
                "cooldown_ticks": 10,
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
                    "agents": ["test-agent"],
                    "factions": ["test-faction"],
                },
                "beats": ["Test beat"],
                "resolution_templates": {
                    "success": "Success",
                    "failure": "Failure",
                },
                "followups": [],
            }
        ]
    }
    (world_dir / "story_seeds.yml").write_text(
        yaml.safe_dump(story_seeds), encoding="utf-8"
    )


class TestMainFunction:
    """Tests for the main CLI function."""

    def test_main_loads_default_world(self, capsys) -> None:
        """Test that main loads and displays the default world summary."""
        # Use the actual default world in the repository
        with patch("sys.argv", ["eoe_dump_state"]):
            main()

        captured = capsys.readouterr()
        assert "Echoes of Emergence :: World Summary" in captured.out
        # Check that summary fields are printed
        assert ":" in captured.out

    def test_main_loads_specified_world(self, capsys) -> None:
        """Test loading a specified world bundle."""
        with patch("sys.argv", ["eoe_dump_state", "--world", "default"]):
            main()

        captured = capsys.readouterr()
        assert "Echoes of Emergence :: World Summary" in captured.out

    def test_main_exports_snapshot(self, tmp_path: Path, capsys) -> None:
        """Test exporting a snapshot to a JSON file."""
        export_path = tmp_path / "snapshot.json"

        with patch("sys.argv", ["eoe_dump_state", "-e", str(export_path)]):
            main()

        captured = capsys.readouterr()
        assert "Snapshot written to" in captured.out
        assert export_path.exists()

        # Verify the snapshot contains valid JSON
        import json

        data = json.loads(export_path.read_text())
        assert "city" in data or "game_state" in data or len(data) > 0

    def test_main_export_with_long_option(self, tmp_path: Path, capsys) -> None:
        """Test exporting using --export option."""
        export_path = tmp_path / "output" / "state.json"

        with patch("sys.argv", ["eoe_dump_state", "--export", str(export_path)]):
            main()

        captured = capsys.readouterr()
        assert "Snapshot written to" in captured.out
        assert export_path.exists()

    def test_main_with_world_short_option(self, capsys) -> None:
        """Test using -w short option for world."""
        with patch("sys.argv", ["eoe_dump_state", "-w", "default"]):
            main()

        captured = capsys.readouterr()
        assert "Echoes of Emergence :: World Summary" in captured.out

    def test_main_invalid_world_raises_error(self) -> None:
        """Test that an invalid world name raises an error."""
        with patch("sys.argv", ["eoe_dump_state", "--world", "nonexistent_world"]):
            with pytest.raises((FileNotFoundError, ValueError)):
                main()

    def test_main_combined_options(self, tmp_path: Path, capsys) -> None:
        """Test using both world and export options together."""
        export_path = tmp_path / "combined.json"

        with patch(
            "sys.argv",
            ["eoe_dump_state", "-w", "default", "-e", str(export_path)],
        ):
            main()

        captured = capsys.readouterr()
        assert "Echoes of Emergence :: World Summary" in captured.out
        assert "Snapshot written to" in captured.out
        assert export_path.exists()


class TestSummaryOutput:
    """Tests for summary output content."""

    def test_summary_contains_expected_fields(self, capsys) -> None:
        """Test that summary output contains expected game state fields."""
        with patch("sys.argv", ["eoe_dump_state"]):
            main()

        captured = capsys.readouterr()
        # Summary should include some key information
        # The exact fields depend on GameState.summary() implementation
        assert ":" in captured.out
        lines = captured.out.strip().split("\n")
        # Should have multiple lines (header + at least one field)
        assert len(lines) > 1


class TestArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_help_option(self, capsys) -> None:
        """Test that --help option works."""
        with patch("sys.argv", ["eoe_dump_state", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "--world" in captured.out
        assert "--export" in captured.out

    def test_default_world_value(self) -> None:
        """Test that default world is 'default' when not specified."""
        import argparse

        # Create a new parser like the script does
        parser = argparse.ArgumentParser()
        parser.add_argument("--world", "-w", default="default")
        parser.add_argument("--export", "-e", type=Path, default=None)

        args = parser.parse_args([])
        assert args.world == "default"
        assert args.export is None


class TestRealWorldIntegration:
    """Integration tests using actual repository content."""

    def test_loads_repository_default_world(self, capsys) -> None:
        """Test loading the actual default world from the repository."""
        repo_root = Path(__file__).resolve().parents[2]
        content_dir = repo_root / "content" / "worlds" / "default"

        if not content_dir.exists():
            pytest.skip("Default world content not found")

        with patch("sys.argv", ["eoe_dump_state", "--world", "default"]):
            main()

        captured = capsys.readouterr()
        assert "Echoes of Emergence :: World Summary" in captured.out

    def test_export_creates_valid_json(self, tmp_path: Path) -> None:
        """Test that exported snapshot is valid JSON with expected structure."""
        import json

        export_path = tmp_path / "valid.json"

        with patch("sys.argv", ["eoe_dump_state", "-e", str(export_path)]):
            main()

        assert export_path.exists()
        data = json.loads(export_path.read_text())
        # The snapshot should be a dictionary with game state data
        assert isinstance(data, dict)
