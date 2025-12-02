"""Tests for the content build and validation script."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

import pytest
import yaml

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "build_content.py"


def _load_build_content_module():
    spec = util.spec_from_file_location("build_content", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("build_content", module)
    spec.loader.exec_module(module)
    return module


_mod = _load_build_content_module()
main = _mod.main
validate_all_content = _mod.validate_all_content
validate_world = _mod.validate_world
validate_simulation_config = _mod.validate_simulation_config
validate_sweep_config = _mod.validate_sweep_config


def _create_valid_world(world_dir: Path) -> None:
    """Create a minimal valid world directory."""
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


def _create_valid_simulation_config(config_path: Path) -> None:
    """Create a minimal valid simulation configuration."""
    config = {
        "limits": {
            "engine_max_ticks": 100,
            "cli_run_cap": 50,
            "cli_script_command_cap": 200,
            "service_tick_cap": 100,
        },
        "lod": {
            "mode": "balanced",
            "volatility_scale": {
                "detailed": 0.9,
                "balanced": 0.5,
                "coarse": 0.3,
            },
            "max_events_per_tick": 6,
        },
        "profiling": {
            "log_ticks": True,
            "history_window": 60,
            "capture_subsystems": True,
        },
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")


class TestValidateWorld:
    """Tests for world validation."""

    def test_valid_world(self, tmp_path: Path) -> None:
        worlds_dir = tmp_path / "worlds"
        world_dir = worlds_dir / "test-world"
        _create_valid_world(world_dir)

        result = validate_world(world_dir, content_root=worlds_dir)

        assert result.success
        assert len(result.errors) == 0

    def test_missing_world_yml(self, tmp_path: Path) -> None:
        worlds_dir = tmp_path / "worlds"
        world_dir = worlds_dir / "empty-world"
        world_dir.mkdir(parents=True)

        result = validate_world(world_dir, content_root=worlds_dir)

        assert not result.success
        assert any("Missing world.yml" in e for e in result.errors)

    def test_invalid_schema(self, tmp_path: Path) -> None:
        worlds_dir = tmp_path / "worlds"
        world_dir = worlds_dir / "invalid-world"
        world_dir.mkdir(parents=True)
        # Missing required 'city' field
        (world_dir / "world.yml").write_text(
            yaml.safe_dump({"factions": []}), encoding="utf-8"
        )

        result = validate_world(world_dir, content_root=worlds_dir)

        assert not result.success
        assert len(result.errors) > 0

    def test_invalid_entity_reference(self, tmp_path: Path) -> None:
        worlds_dir = tmp_path / "worlds"
        world_dir = worlds_dir / "bad-refs"
        world_dir.mkdir(parents=True)
        world_yml = {
            "city": {
                "id": "test-city",
                "name": "Test City",
                "districts": [{"id": "core", "name": "Core", "population": 1000}],
            },
            "factions": [],
            "agents": [],
        }
        (world_dir / "world.yml").write_text(
            yaml.safe_dump(world_yml), encoding="utf-8"
        )
        story_seeds = {
            "story_seeds": [
                {
                    "id": "bad-seed",
                    "title": "Bad Seed",
                    "summary": "References unknown entities",
                    "stakes": "Test",
                    "scope": "environment",
                    "preferred_districts": ["unknown-district"],  # Bad reference
                    "cooldown_ticks": 10,
                    "tags": [],
                    "triggers": [
                        {
                            "scope": "environment",
                            "district_id": "core",
                            "min_score": 0.5,
                            "min_severity": 0.5,
                        }
                    ],
                    "roles": {"agents": [], "factions": []},
                    "beats": [],
                    "resolution_templates": {"success": "OK", "failure": "Fail"},
                    "followups": [],
                }
            ]
        }
        (world_dir / "story_seeds.yml").write_text(
            yaml.safe_dump(story_seeds), encoding="utf-8"
        )

        result = validate_world(world_dir, content_root=worlds_dir)

        assert not result.success
        assert any("unknown district" in e for e in result.errors)


class TestValidateSimulationConfig:
    """Tests for simulation config validation."""

    def test_valid_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / "simulation.yml"
        _create_valid_simulation_config(config_path)

        result = validate_simulation_config(config_path)

        assert result.success
        assert len(result.errors) == 0

    def test_missing_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / "missing.yml"

        result = validate_simulation_config(config_path)

        assert not result.success
        assert any("Missing configuration" in e for e in result.errors)

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        config_path = tmp_path / "bad.yml"
        config_path.write_text("not: valid: yaml: here", encoding="utf-8")

        result = validate_simulation_config(config_path)

        assert not result.success


class TestValidateSweepConfig:
    """Tests for sweep config validation."""

    def test_valid_sweep(self, tmp_path: Path) -> None:
        sweep_dir = tmp_path / "sweep-test"
        config_path = sweep_dir / "simulation.yml"
        _create_valid_simulation_config(config_path)

        result = validate_sweep_config(sweep_dir)

        assert result.success
        assert len(result.errors) == 0

    def test_missing_simulation_yml(self, tmp_path: Path) -> None:
        sweep_dir = tmp_path / "empty-sweep"
        sweep_dir.mkdir()

        result = validate_sweep_config(sweep_dir)

        assert not result.success
        assert any("Missing simulation.yml" in e for e in result.errors)


class TestValidateAllContent:
    """Tests for full content validation."""

    def test_validates_all_content_types(self, tmp_path: Path) -> None:
        content_root = tmp_path / "content"

        # Create worlds
        worlds_dir = content_root / "worlds"
        _create_valid_world(worlds_dir / "world1")
        _create_valid_world(worlds_dir / "world2")

        # Create config
        config_dir = content_root / "config"
        _create_valid_simulation_config(config_dir / "simulation.yml")

        # Create sweeps
        sweeps_dir = config_dir / "sweeps"
        _create_valid_simulation_config(sweeps_dir / "easy" / "simulation.yml")
        _create_valid_simulation_config(sweeps_dir / "hard" / "simulation.yml")

        manifest = validate_all_content(content_root)

        assert manifest.total_errors == 0
        assert len(manifest.failed_files) == 0
        assert len(manifest.validated_files) == 5  # 2 worlds + 1 config + 2 sweeps

    def test_reports_errors_correctly(self, tmp_path: Path) -> None:
        content_root = tmp_path / "content"
        worlds_dir = content_root / "worlds"

        # Create valid world
        _create_valid_world(worlds_dir / "valid-world")

        # Create invalid world
        invalid_world = worlds_dir / "invalid-world"
        invalid_world.mkdir(parents=True)
        (invalid_world / "world.yml").write_text("not-a-mapping", encoding="utf-8")

        manifest = validate_all_content(content_root)

        assert manifest.total_errors > 0
        assert len(manifest.failed_files) == 1
        assert len(manifest.validated_files) == 1


class TestMain:
    """Tests for the CLI entry point."""

    def test_main_success(self, tmp_path: Path, capsys) -> None:
        content_root = tmp_path / "content"
        worlds_dir = content_root / "worlds"
        _create_valid_world(worlds_dir / "test-world")

        exit_code = main(["--content", str(content_root)])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "validated successfully" in captured.out

    def test_main_failure(self, tmp_path: Path, capsys) -> None:
        content_root = tmp_path / "content"
        worlds_dir = content_root / "worlds"
        invalid_world = worlds_dir / "invalid"
        invalid_world.mkdir(parents=True)
        # Invalid: missing city
        (invalid_world / "world.yml").write_text(
            yaml.safe_dump({"factions": []}), encoding="utf-8"
        )

        exit_code = main(["--content", str(content_root)])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Validation failed" in captured.err

    def test_main_writes_manifest(self, tmp_path: Path) -> None:
        content_root = tmp_path / "content"
        worlds_dir = content_root / "worlds"
        _create_valid_world(worlds_dir / "test-world")
        manifest_path = tmp_path / "manifest.json"

        exit_code = main(
            ["--content", str(content_root), "--output", str(manifest_path)]
        )

        assert exit_code == 0
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert manifest["success"] is True
        assert len(manifest["validated_files"]) == 1

    def test_main_missing_content_dir(self, tmp_path: Path) -> None:
        missing_path = tmp_path / "nonexistent"

        exit_code = main(["--content", str(missing_path)])

        assert exit_code == 2


class TestRealContent:
    """Integration tests using the actual repository content."""

    def test_validates_default_world(self) -> None:
        """Validate that the default world in the repository is valid."""
        repo_root = Path(__file__).resolve().parents[2]
        content_root = repo_root / "content"

        if not content_root.exists():
            pytest.skip("Content directory not found")

        manifest = validate_all_content(content_root)

        # The real content should validate successfully
        assert manifest.total_errors == 0, f"Errors: {manifest.failed_files}"
        assert len(manifest.validated_files) > 0

    def test_cli_validates_real_content(self, capsys) -> None:
        """Test the CLI with real repository content."""
        repo_root = Path(__file__).resolve().parents[2]
        content_root = repo_root / "content"

        if not content_root.exists():
            pytest.skip("Content directory not found")

        exit_code = main(["--content", str(content_root), "--verbose"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "validated successfully" in captured.out
