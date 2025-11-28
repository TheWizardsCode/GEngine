"""Headless tick driver for Echoes of Emergence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

from gengine.echoes.settings import SimulationConfig, load_simulation_config
from gengine.echoes.sim import SimEngine, TickReport


def run_headless_sim(
    *,
    world: str = "default",
    snapshot: Path | None = None,
    ticks: int = 100,
    seed: int | None = None,
    lod_mode: str | None = None,
    output: Path | None = None,
    config_root: Path | None = None,
) -> dict[str, Any]:
    """Advance the simulation headlessly and return a summary payload."""

    if ticks < 1:
        raise ValueError("ticks must be >= 1")

    config = _load_config(config_root, lod_mode)
    engine = SimEngine(config=config)
    if snapshot is not None:
        engine.initialize_state(snapshot=snapshot)
        world_label = f"snapshot:{snapshot}"
    else:
        engine.initialize_state(world=world)
        world_label = world

    start_tick = engine.state.tick
    start_time = perf_counter()
    reports, batches = _advance_in_batches(engine, ticks, seed)
    duration_ms = (perf_counter() - start_time) * 1000

    summary = {
        "world": world_label,
        "ticks_requested": ticks,
        "ticks_executed": len(reports),
        "start_tick": start_tick,
        "end_tick": engine.state.tick,
        "lod_mode": engine.config.lod.mode,
        "seed": seed,
        "duration_ms": round(duration_ms, 2),
        "batches": batches,
        "events_emitted": sum(len(report.events) for report in reports),
    }
    if reports:
        summary["last_environment"] = reports[-1].environment

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2, sort_keys=True))

    return summary


def _advance_in_batches(
    engine: SimEngine,
    total_ticks: int,
    seed: int | None,
) -> tuple[list[TickReport], list[dict[str, Any]]]:
    reports: list[TickReport] = []
    batches: list[dict[str, Any]] = []
    remaining = total_ticks
    batch_index = 1
    active_seed = seed
    per_call_limit = engine.config.limits.engine_max_ticks

    while remaining > 0:
        step = min(remaining, per_call_limit)
        step_reports = engine.advance_ticks(step, seed=active_seed)
        reports.extend(step_reports)
        batches.append(
            {
                "batch": batch_index,
                "ticks": len(step_reports),
                "ending_tick": step_reports[-1].tick if step_reports else engine.state.tick,
            }
        )
        _emit_batch_log(batch_index, step_reports)
        remaining -= step
        batch_index += 1
        active_seed = None

    return reports, batches


def _emit_batch_log(batch_index: int, reports: list[TickReport]) -> None:
    if not reports:
        return
    last = reports[-1]
    env = last.environment
    sys.stderr.write(
        f"[batch {batch_index}] tick={last.tick} "
        f"stb={env['stability']:.2f} unrest={env['unrest']:.2f} "
        f"poll={env['pollution']:.2f} events={len(last.events)}\n"
    )


def _load_config(config_root: Path | None, lod_mode: str | None) -> SimulationConfig:
    config = load_simulation_config(config_root=config_root)
    if lod_mode:
        lod = config.lod.model_copy(update={"mode": lod_mode})
        config = config.model_copy(update={"lod": lod})
    return config


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Headless tick driver for Echoes")
    parser.add_argument("--world", "-w", default="default", help="World bundle to load")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        help="Optional snapshot file to load instead of content",
    )
    parser.add_argument("--ticks", "-t", type=int, default=200, help="Number of ticks to advance")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed override for determinism")
    parser.add_argument(
        "--lod",
        choices=["detailed", "balanced", "coarse"],
        default=None,
        help="Override the configured level-of-detail mode",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Optional path to write the summary JSON",
    )
    parser.add_argument(
        "--config-root",
        type=Path,
        default=None,
        help="Override the simulation config root (defaults to content/config)",
    )
    args = parser.parse_args(argv)

    summary = run_headless_sim(
        world=args.world,
        snapshot=args.snapshot,
        ticks=args.ticks,
        seed=args.seed,
        lod_mode=args.lod,
        output=args.output,
        config_root=args.config_root,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
