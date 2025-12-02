#!/usr/bin/env python3
"""Run difficulty sweeps across all presets and capture telemetry."""

from __future__ import annotations

import argparse
import json
import sys
from importlib import util
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

# Difficulty presets in order of increasing challenge
DIFFICULTY_PRESETS = ["tutorial", "easy", "normal", "hard", "brutal"]

# Load headless sim module dynamically to avoid import issues
_HEADLESS_PATH = Path(__file__).resolve().parent / "run_headless_sim.py"


def _load_headless_module():
    """Dynamically load the headless simulation driver module."""
    spec = util.spec_from_file_location("headless_driver", _HEADLESS_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("headless_driver", module)
    spec.loader.exec_module(module)
    return module


def run_difficulty_sweeps(
    *,
    ticks: int = 200,
    seed: int | None = 42,
    lod_mode: str = "balanced",
    output_dir: Path | None = None,
    presets: Sequence[str] | None = None,
    verbose: bool = False,
) -> dict[str, dict[str, Any]]:
    """Run simulations for each difficulty preset and return summaries.

    Args:
        ticks: Number of ticks to run for each preset.
        seed: RNG seed for deterministic comparisons (default: 42).
        lod_mode: Level-of-detail mode override.
        output_dir: Directory to write telemetry JSON files.
        presets: Specific presets to run (defaults to all).
        verbose: Print progress to stderr.

    Returns:
        Dictionary mapping preset names to their telemetry summaries.
    """
    _headless = _load_headless_module()
    run_headless_sim = _headless.run_headless_sim

    selected = list(presets) if presets else DIFFICULTY_PRESETS
    results: dict[str, dict[str, Any]] = {}
    config_base = Path("content/config/sweeps")

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    start_total = perf_counter()

    for preset in selected:
        config_root = config_base / f"difficulty-{preset}"
        if not config_root.exists():
            if verbose:
                sys.stderr.write(f"[SKIP] Config not found: {config_root}\n")
            continue

        output_path = (
            output_dir / f"difficulty-{preset}-sweep.json" if output_dir else None
        )

        if verbose:
            sys.stderr.write(
                f"\n[START] {preset.upper()} difficulty ({ticks} ticks, seed={seed})\n"
            )

        start = perf_counter()
        summary = run_headless_sim(
            ticks=ticks,
            seed=seed,
            lod_mode=lod_mode,
            output=output_path,
            config_root=config_root,
        )
        elapsed = perf_counter() - start

        summary["sweep_metadata"] = {
            "preset": preset,
            "config_root": str(config_root),
            "elapsed_seconds": round(elapsed, 2),
        }
        results[preset] = summary

        if verbose:
            env = summary.get("last_environment", {})
            stability = env.get("stability", 0)
            unrest = env.get("unrest", 0)
            pollution = env.get("pollution", 0)
            anomalies = summary.get("anomalies", 0)
            suppressed = summary.get("suppressed_events", 0)
            sys.stderr.write(
                f"[DONE] {preset}: stb={stability:.2f} unrest={unrest:.2f} "
                f"poll={pollution:.2f} anomalies={anomalies} suppressed={suppressed} "
                f"({elapsed:.1f}s)\n"
            )

    total_elapsed = perf_counter() - start_total
    if verbose:
        sys.stderr.write(
            f"\n[COMPLETE] {len(results)} presets in {total_elapsed:.1f}s\n"
        )

    return results


def print_summary_table(results: dict[str, dict[str, Any]]) -> None:
    """Print a comparison table of difficulty results."""
    print("\n" + "=" * 80)
    print("DIFFICULTY SWEEP COMPARISON")
    print("=" * 80)
    print(
        f"{'Preset':<10} {'Stability':>10} {'Unrest':>10} {'Pollution':>10} "
        f"{'Anomalies':>10} {'Suppressed':>12}"
    )
    print("-" * 80)

    for preset in DIFFICULTY_PRESETS:
        if preset not in results:
            continue
        summary = results[preset]
        env = summary.get("last_environment", {})
        stability = env.get("stability", 0)
        unrest = env.get("unrest", 0)
        pollution = env.get("pollution", 0)
        anomalies = summary.get("anomalies", 0)
        suppressed = summary.get("suppressed_events", 0)

        print(
            f"{preset:<10} {stability:>10.3f} {unrest:>10.3f} {pollution:>10.3f} "
            f"{anomalies:>10} {suppressed:>12}"
        )

    print("=" * 80)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for running difficulty sweeps."""
    parser = argparse.ArgumentParser(
        description="Run simulations across difficulty presets and capture telemetry."
    )
    parser.add_argument(
        "--ticks",
        "-t",
        type=int,
        default=200,
        help="Number of ticks to run for each preset (default: 200)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for deterministic comparisons (default: 42)",
    )
    parser.add_argument(
        "--lod",
        choices=["detailed", "balanced", "coarse"],
        default="balanced",
        help="Override the level-of-detail mode",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("build"),
        help="Directory to write telemetry JSON files (default: build)",
    )
    parser.add_argument(
        "--preset",
        "-p",
        action="append",
        choices=DIFFICULTY_PRESETS,
        help="Specific preset(s) to run (can be repeated; default: all)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of table",
    )

    args = parser.parse_args(argv)

    results = run_difficulty_sweeps(
        ticks=args.ticks,
        seed=args.seed,
        lod_mode=args.lod,
        output_dir=args.output_dir,
        presets=args.preset,
        verbose=not args.quiet,
    )

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_summary_table(results)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
