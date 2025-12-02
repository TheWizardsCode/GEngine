#!/usr/bin/env python3
"""Plot pollution and unrest trajectories from headless telemetry JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib.pyplot as plt

DEFAULT_RUNS: Dict[str, Path] = {
    "cushioned": Path("build/feature-m4-7-biodiversity-cushioned.json"),
    "high-pressure": Path("build/feature-m4-7-biodiversity-high-pressure.json"),
    "profiling-history": Path("build/feature-m4-7-biodiversity-profiling-history.json"),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plot pollution/unrest trajectories from telemetry JSON files. "
            "By default the script looks for the cushioned, high-pressure, and "
            "profiling-history captures under build/."
        )
    )
    parser.add_argument(
        "--run",
        action="append",
        metavar="LABEL=PATH",
        help="Telemetry file to plot (can be provided multiple times).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save the figure instead of displaying it.",
    )
    parser.add_argument(
        "--title",
        default="Environment trajectories",
        help="Figure title to display across the subplots.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    runs = _collect_runs(args.run)
    if not runs:
        raise SystemExit(
            "No telemetry files found. Provide --run LABEL=PATH "
            "or rerun the sweeps to generate JSON."
        )

    fig, (ax_pollution, ax_unrest) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
    for label, path in runs.items():
        ticks, pollution, unrest = _extract_series(path)
        if len(ticks) < 2:
            print(
                f"Warning: {label} only provided {len(ticks)} sample(s); "
                "increase focus.history_length before capturing telemetry."
            )
        ax_pollution.plot(ticks, pollution, label=label)
        ax_unrest.plot(ticks, unrest, label=label)

    fig.suptitle(args.title)
    ax_pollution.set_ylabel("Average pollution")
    ax_unrest.set_ylabel("Average unrest")
    ax_unrest.set_xlabel("Tick")
    ax_pollution.legend(loc="best")
    ax_unrest.legend(loc="best")
    fig.tight_layout()

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=200)
        print(f"Saved plot to {args.output}")
    else:
        plt.show()
    return 0


def _collect_runs(run_args: Sequence[str] | None) -> Dict[str, Path]:
    runs: Dict[str, Path] = {}
    if run_args:
        for spec in run_args:
            label, path = _parse_run_spec(spec)
            runs[label] = path
    else:
        for label, path in DEFAULT_RUNS.items():
            if path.exists():
                runs[label] = path
    return runs


def _parse_run_spec(spec: str) -> Tuple[str, Path]:
    if "=" not in spec:
        path = Path(spec)
        return (path.stem, path)
    label, raw_path = spec.split("=", 1)
    return label.strip(), Path(raw_path.strip())


def _extract_series(path: Path) -> Tuple[List[int], List[float], List[float]]:
    data = json.loads(path.read_text())
    entries = list(data.get("director_history", []))
    entries.sort(key=lambda entry: entry.get("tick", 0))

    ticks: List[int] = []
    pollution: List[float] = []
    unrest: List[float] = []

    for entry in entries:
        env = entry.get("environment")
        tick = entry.get("tick")
        if not env or tick is None:
            continue
        ticks.append(int(tick))
        pollution.append(float(env.get("pollution", 0.0)))
        unrest.append(float(env.get("unrest", 0.0)))

    if not ticks and "last_environment" in data:
        env = data["last_environment"]
        ticks = [int(data.get("end_tick", 0))]
        pollution = [float(env.get("pollution", 0.0))]
        unrest = [float(env.get("unrest", 0.0))]

    return ticks, pollution, unrest


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
