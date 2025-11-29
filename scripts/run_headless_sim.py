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
        "agent_actions": sum(len(report.agent_actions) for report in reports),
        "agent_intent_breakdown": _intent_breakdown(reports),
        "faction_actions": sum(len(report.faction_actions) for report in reports),
        "faction_action_breakdown": _faction_breakdown(reports),
    }
    summary["suppressed_events"] = sum(len(report.suppressed_events) for report in reports)
    summary["director_feed"] = dict(engine.state.metadata.get("director_feed", {}))
    summary["director_history"] = list(engine.state.metadata.get("director_history") or [])
    summary["director_analysis"] = dict(engine.state.metadata.get("director_analysis") or {})
    summary["director_events"] = list(engine.state.metadata.get("director_events") or [])
    summary["director_pacing"] = dict(engine.state.metadata.get("director_pacing") or {})
    summary["story_seeds"] = list(engine.state.metadata.get("story_seeds_active") or [])
    summary["story_seed_lifecycle"] = dict(engine.state.metadata.get("story_seed_lifecycle") or {})
    summary["story_seed_lifecycle_history"] = list(
        engine.state.metadata.get("story_seed_lifecycle_history") or []
    )
    quiet_until = engine.state.metadata.get("director_quiet_until")
    if isinstance(quiet_until, (int, float)):
        summary["director_quiet_until"] = int(quiet_until)
    summary["post_mortem"] = engine.query_view("post-mortem")
    if reports:
        summary["anomalies"] = sum(len(report.anomalies) for report in reports)
        summary["anomaly_examples"] = sorted(
            {anomaly for report in reports for anomaly in report.anomalies}
        )[:5]
    if reports:
        summary["last_environment"] = reports[-1].environment
        summary["faction_legitimacy"] = reports[-1].faction_legitimacy
        summary["last_economy"] = reports[-1].economy
        digest = engine.state.metadata.get("focus_digest", {})
        summary["last_event_digest"] = {
            "visible": list(reports[-1].events),
            "archive": list(reports[-1].event_archive),
            "suppressed": list(reports[-1].suppressed_events),
            "focus_budget": dict(reports[-1].focus_budget),
            "ranked_archive": list(digest.get("ranked_archive", [])),
        }
        summary["last_director_snapshot"] = dict(reports[-1].director_snapshot)
        summary["last_director_analysis"] = dict(reports[-1].director_analysis)
        summary["last_director_events"] = list(reports[-1].director_events)
    profiling = engine.state.metadata.get("profiling")
    if profiling:
        summary["profiling"] = profiling

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
        last_report = step_reports[-1] if step_reports else None
        batch_payload = {
            "batch": batch_index,
            "ticks": len(step_reports),
            "ending_tick": last_report.tick if last_report else engine.state.tick,
            "agent_actions": sum(len(report.agent_actions) for report in step_reports),
            "faction_actions": sum(len(report.faction_actions) for report in step_reports),
        }
        if last_report is not None:
            batch_payload["tick_ms"] = round(
                last_report.timings.get("tick_total_ms", 0.0), 2
            )
            batch_payload["slowest_subsystem"] = _slowest_subsystem(last_report)
            batch_payload["anomalies"] = list(last_report.anomalies)
        else:
            batch_payload["tick_ms"] = 0.0
            batch_payload["slowest_subsystem"] = None
            batch_payload["anomalies"] = []
        batches.append(batch_payload)
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
        f"poll={env['pollution']:.2f} events={len(last.events)} "
        f"agent_actions={len(last.agent_actions)} factions={len(last.faction_actions)} "
        f"prices={len(last.economy.get('prices', {}))}\n"
    )


def _intent_breakdown(reports: Sequence[TickReport]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for report in reports:
        for action in report.agent_actions:
            intent = action.get("intent", "unknown")
            counts[intent] = counts.get(intent, 0) + 1
    return counts


def _faction_breakdown(reports: Sequence[TickReport]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for report in reports:
        for action in report.faction_actions:
            name = action.get("action", "unknown")
            counts[name] = counts.get(name, 0) + 1
    return counts


def _load_config(config_root: Path | None, lod_mode: str | None) -> SimulationConfig:
    config = load_simulation_config(config_root=config_root)
    if lod_mode:
        lod = config.lod.model_copy(update={"mode": lod_mode})
        config = config.model_copy(update={"lod": lod})
    return config


def _slowest_subsystem(report: TickReport) -> dict[str, float] | None:
    candidates = {
        name: value
        for name, value in report.timings.items()
        if name.endswith("_ms") and name != "tick_total_ms"
    }
    if not candidates:
        return None
    name, value = max(candidates.items(), key=lambda item: item[1])
    return {"name": name, "ms": round(value, 2)}


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
