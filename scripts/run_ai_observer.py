"""CLI runner for the AI Observer.

Executes AI-observed sessions with configurable tick budgets and output formats.
Supports both JSON summaries and optional natural language logs.

Examples
--------
Basic observation with JSON output::

    uv run python scripts/run_ai_observer.py \\
        --world default --ticks 100 --output build/observation.json

Verbose mode with natural language commentary::

    uv run python scripts/run_ai_observer.py --world default --ticks 50 --verbose

Service mode (connect to running simulation)::

    uv run python scripts/run_ai_observer.py \\
        --service-url http://localhost:8000 --ticks 50
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from gengine.ai_player import ObserverConfig
from gengine.ai_player.observer import (
    create_observer_from_engine,
    create_observer_from_service,
)


def run_ai_observer(
    *,
    world: str = "default",
    service_url: str | None = None,
    ticks: int = 100,
    analysis_interval: int = 10,
    stability_threshold: float = 0.5,
    legitimacy_threshold: float = 0.1,
    output: Path | None = None,
    verbose: bool = False,
) -> dict:
    """Run an AI observation session and return the report.

    Parameters
    ----------
    world
        World bundle to load (ignored if service_url is provided).
    service_url
        URL of simulation service to connect to. If None, runs locally.
    ticks
        Number of ticks to observe.
    analysis_interval
        Ticks between state analysis snapshots.
    stability_threshold
        Alert when stability drops below this value.
    legitimacy_threshold
        Alert when faction legitimacy swings exceed this value.
    output
        Optional path to write JSON report.
    verbose
        If True, print natural language commentary during observation.

    Returns
    -------
    dict
        Observation report as a dictionary.
    """
    config = ObserverConfig(
        tick_budget=ticks,
        analysis_interval=analysis_interval,
        stability_alert_threshold=stability_threshold,
        legitimacy_swing_threshold=legitimacy_threshold,
        log_natural_language=verbose,
    )

    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.getLogger("gengine.ai_player.observer").setLevel(logging.INFO)

    if service_url:
        observer = create_observer_from_service(service_url, config=config)
        mode = f"service:{service_url}"
    else:
        observer = create_observer_from_engine(world=world, config=config)
        mode = f"local:{world}"

    try:
        report = observer.observe()
    finally:
        if service_url and hasattr(observer, "_client") and observer._client:
            observer._client.close()

    result = report.to_dict()
    result["mode"] = mode
    result["config"] = {
        "tick_budget": config.tick_budget,
        "analysis_interval": config.analysis_interval,
        "stability_alert_threshold": config.stability_alert_threshold,
        "legitimacy_swing_threshold": config.legitimacy_swing_threshold,
    }

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True))
        if verbose:
            print(f"\nReport written to {output}")

    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI Observer for Echoes simulations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic local observation
  uv run python scripts/run_ai_observer.py --world default --ticks 100

  # Save JSON report
  uv run python scripts/run_ai_observer.py --ticks 50 -o build/observation.json

  # Verbose mode with commentary
  uv run python scripts/run_ai_observer.py --ticks 50 --verbose

  # Connect to running service
  uv run python scripts/run_ai_observer.py --service-url localhost:8000 --ticks 50
""",
    )
    parser.add_argument(
        "--world",
        "-w",
        default="default",
        help="World bundle to load (default: default)",
    )
    parser.add_argument(
        "--service-url",
        default=None,
        help="URL of simulation service to connect to (e.g., http://localhost:8000)",
    )
    parser.add_argument(
        "--ticks",
        "-t",
        type=int,
        default=100,
        help="Number of ticks to observe (default: 100)",
    )
    parser.add_argument(
        "--analysis-interval",
        type=int,
        default=10,
        help="Ticks between analysis snapshots (default: 10)",
    )
    parser.add_argument(
        "--stability-threshold",
        type=float,
        default=0.5,
        help="Alert when stability drops below this (default: 0.5)",
    )
    parser.add_argument(
        "--legitimacy-threshold",
        type=float,
        default=0.1,
        help="Alert when faction swings exceed this (default: 0.1)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Path to write JSON report",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print natural language commentary",
    )

    args = parser.parse_args(argv)

    result = run_ai_observer(
        world=args.world,
        service_url=args.service_url,
        ticks=args.ticks,
        analysis_interval=args.analysis_interval,
        stability_threshold=args.stability_threshold,
        legitimacy_threshold=args.legitimacy_threshold,
        output=args.output,
        verbose=args.verbose,
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
