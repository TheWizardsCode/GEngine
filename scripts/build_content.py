"""Content build and validation tool for Echoes of Emergence.

Validates all content under the `content/` directory including:
- World definitions (world.yml) and story seeds (story_seeds.yml)
- Simulation configuration (simulation.yml)
- Difficulty sweep configurations

Exit codes:
- 0: All content validated successfully
- 1: Validation errors found
- 2: File or configuration errors
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import yaml
from pydantic import ValidationError

from gengine.echoes.content.loader import load_world_bundle
from gengine.echoes.settings import SimulationConfig


@dataclass
class ValidationResult:
    """Result of validating a single content file."""

    path: Path
    success: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class BuildManifest:
    """Manifest of all validated content files."""

    validated_files: list[str] = field(default_factory=list)
    failed_files: list[str] = field(default_factory=list)
    total_errors: int = 0
    validation_results: list[ValidationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "validated_files": self.validated_files,
            "failed_files": self.failed_files,
            "total_errors": self.total_errors,
            "success": self.total_errors == 0 and len(self.failed_files) == 0,
        }


def _default_content_root() -> Path:
    """Return the default content directory relative to this script."""
    return Path(__file__).resolve().parents[1] / "content"


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at root of {path}")
    return data


def validate_world(
    world_path: Path,
    *,
    content_root: Path,
) -> ValidationResult:
    """Validate a world directory containing world.yml and story_seeds.yml."""
    world_name = world_path.name
    world_yml = world_path / "world.yml"
    errors: list[str] = []

    if not world_yml.exists():
        errors.append(f"Missing world.yml in {world_path}")
        return ValidationResult(path=world_path, success=False, errors=errors)

    try:
        # Use the existing load_world_bundle which validates both world.yml
        # and story_seeds.yml, including entity reference validation
        load_world_bundle(world_name, content_root=content_root)
    except FileNotFoundError as exc:
        errors.append(f"File not found: {exc}")
    except ValidationError as exc:
        for error in exc.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"Schema validation error at {loc}: {msg}")
    except (KeyError, ValueError) as exc:
        errors.append(str(exc))

    return ValidationResult(
        path=world_path,
        success=len(errors) == 0,
        errors=errors,
    )


def validate_simulation_config(config_path: Path) -> ValidationResult:
    """Validate a simulation configuration file."""
    errors: list[str] = []

    if not config_path.exists():
        errors.append(f"Missing configuration file: {config_path}")
        return ValidationResult(path=config_path, success=False, errors=errors)

    try:
        data = _load_yaml_file(config_path)
        SimulationConfig.model_validate(data)
    except FileNotFoundError as exc:
        errors.append(f"File not found: {exc}")
    except ValidationError as exc:
        for error in exc.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"Schema validation error at {loc}: {msg}")
    except (yaml.YAMLError, ValueError) as exc:
        errors.append(f"YAML parsing error: {exc}")

    return ValidationResult(
        path=config_path,
        success=len(errors) == 0,
        errors=errors,
    )


def validate_sweep_config(sweep_path: Path) -> ValidationResult:
    """Validate a sweep configuration directory."""
    config_file = sweep_path / "simulation.yml"
    errors: list[str] = []

    if not config_file.exists():
        errors.append(f"Missing simulation.yml in sweep directory: {sweep_path}")
        return ValidationResult(path=sweep_path, success=False, errors=errors)

    result = validate_simulation_config(config_file)
    return ValidationResult(
        path=sweep_path,
        success=result.success,
        errors=result.errors,
    )


def validate_all_content(
    content_root: Path,
    *,
    verbose: bool = False,
) -> BuildManifest:
    """Validate all content in the content directory."""
    manifest = BuildManifest()

    # Validate worlds
    worlds_dir = content_root / "worlds"
    if worlds_dir.exists():
        for world_path in sorted(worlds_dir.iterdir()):
            if world_path.is_dir():
                if verbose:
                    sys.stderr.write(f"Validating world: {world_path.name}\n")
                result = validate_world(world_path, content_root=worlds_dir)
                manifest.validation_results.append(result)
                if result.success:
                    manifest.validated_files.append(str(result.path))
                else:
                    manifest.failed_files.append(str(result.path))
                    manifest.total_errors += len(result.errors)

    # Validate simulation config
    config_dir = content_root / "config"
    if config_dir.exists():
        sim_config = config_dir / "simulation.yml"
        if sim_config.exists():
            if verbose:
                sys.stderr.write(f"Validating config: {sim_config}\n")
            result = validate_simulation_config(sim_config)
            manifest.validation_results.append(result)
            if result.success:
                manifest.validated_files.append(str(result.path))
            else:
                manifest.failed_files.append(str(result.path))
                manifest.total_errors += len(result.errors)

        # Validate sweep configs
        sweeps_dir = config_dir / "sweeps"
        if sweeps_dir.exists():
            for sweep_path in sorted(sweeps_dir.iterdir()):
                if sweep_path.is_dir():
                    if verbose:
                        sys.stderr.write(f"Validating sweep: {sweep_path.name}\n")
                    result = validate_sweep_config(sweep_path)
                    manifest.validation_results.append(result)
                    if result.success:
                        manifest.validated_files.append(str(result.path))
                    else:
                        manifest.failed_files.append(str(result.path))
                        manifest.total_errors += len(result.errors)

    return manifest


def print_validation_errors(manifest: BuildManifest) -> None:
    """Print validation errors to stderr with clear formatting."""
    for result in manifest.validation_results:
        if not result.success:
            sys.stderr.write(f"\n❌ Validation failed: {result.path}\n")
            for error in result.errors:
                sys.stderr.write(f"   • {error}\n")


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the content build script."""
    parser = argparse.ArgumentParser(
        description="Validate all Echoes content files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/build_content.py                    # Validate all content
  python scripts/build_content.py --verbose          # Verbose output
  python scripts/build_content.py -o manifest.json   # Write manifest file
  python scripts/build_content.py --content /path    # Custom content root
""",
    )
    parser.add_argument(
        "--content",
        "-c",
        type=Path,
        default=None,
        help="Content directory root (default: content/)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Optional path to write the build manifest JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args(argv)

    content_root = args.content or _default_content_root()

    if not content_root.exists():
        sys.stderr.write(f"Error: Content directory not found: {content_root}\n")
        return 2

    if args.verbose:
        sys.stderr.write(f"Validating content in: {content_root}\n")

    manifest = validate_all_content(content_root, verbose=args.verbose)

    # Print errors if any
    if manifest.total_errors > 0:
        print_validation_errors(manifest)

    # Write manifest if requested
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest.to_dict(), indent=2))
        if args.verbose:
            sys.stderr.write(f"Manifest written to: {args.output}\n")

    # Print summary
    total_files = len(manifest.validated_files) + len(manifest.failed_files)
    if manifest.total_errors == 0:
        sys.stdout.write(
            f"✓ All content validated successfully ({total_files} files)\n"
        )
        return 0
    else:
        sys.stderr.write(
            f"\n✗ Validation failed: {manifest.total_errors} error(s) in "
            f"{len(manifest.failed_files)} file(s)\n"
        )
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
