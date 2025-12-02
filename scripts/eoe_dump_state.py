"""Utility to load a world bundle and show a quick summary or export a snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path

from gengine.echoes.content import load_world_bundle
from gengine.echoes.persistence import save_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--world",
        "-w",
        default="default",
        help="World folder name under content/worlds",
    )
    parser.add_argument(
        "--export",
        "-e",
        type=Path,
        default=None,
        help="Optional file path to write the snapshot JSON",
    )
    args = parser.parse_args()

    state = load_world_bundle(world_name=args.world)
    print("Echoes of Emergence :: World Summary")
    for key, value in state.summary().items():
        print(f"{key:>12}: {value}")
    if args.export is not None:
        path = save_snapshot(state, args.export)
        print(f"Snapshot written to {path}")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
