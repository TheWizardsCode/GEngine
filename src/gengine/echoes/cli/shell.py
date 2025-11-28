"""In-process CLI shell for driving the Echoes simulation."""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from ..content import load_world_bundle
from ..core import GameState
from ..persistence import load_snapshot, save_snapshot
from ..sim import TickReport, advance_ticks

PROMPT = "(echoes) "
INTRO_TEXT = "Echoes shell ready. Type 'help' for commands."


@dataclass
class CommandResult:
    output: str
    should_exit: bool = False


class EchoesShell:
    """Minimal command processor for the early CLI shell."""

    def __init__(self, state: GameState) -> None:
        self.state = state

    # Public API ---------------------------------------------------------
    def execute(self, command_line: str) -> CommandResult:
        parts = shlex.split(command_line)
        if not parts:
            return CommandResult("")
        cmd = parts[0].lower()
        args = parts[1:]

        handler = getattr(self, f"_cmd_{cmd}", None)
        if handler is None:
            return CommandResult(f"Unknown command '{cmd}'. Type 'help' for options.")
        return handler(args)

    # Command implementations -------------------------------------------
    def _cmd_help(self, _: Sequence[str]) -> CommandResult:
        return CommandResult(
            "Available commands: summary, next [n], run <n>, map [district], "
            "save <path>, load world <name>|snapshot <path>, help, exit"
        )

    def _cmd_summary(self, _: Sequence[str]) -> CommandResult:
        return CommandResult(_render_summary(self.state))

    def _cmd_next(self, args: Sequence[str]) -> CommandResult:
        if args:
            return CommandResult("Usage: next")
        reports = advance_ticks(self.state, 1)
        return CommandResult(_render_reports(reports))

    def _cmd_run(self, args: Sequence[str]) -> CommandResult:
        if not args:
            return CommandResult("Usage: run <count>")
        try:
            count = max(1, int(args[0]))
        except ValueError:
            return CommandResult("Usage: run <count>")
        reports = advance_ticks(self.state, count)
        return CommandResult(_render_reports(reports))

    def _cmd_map(self, args: Sequence[str]) -> CommandResult:
        district_id = args[0] if args else None
        return CommandResult(_render_map(self.state, district_id))

    def _cmd_save(self, args: Sequence[str]) -> CommandResult:
        if not args:
            return CommandResult("Usage: save <path>")
        path = Path(args[0])
        save_snapshot(self.state, path)
        return CommandResult(f"Saved snapshot to {path}")

    def _cmd_load(self, args: Sequence[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult("Usage: load world <name> | load snapshot <path>")
        source = args[0]
        target = args[1]
        if source == "world":
            self.state = load_world_bundle(world_name=target)
            return CommandResult(f"Loaded world '{target}'")
        if source == "snapshot":
            self.state = load_snapshot(Path(target))
            return CommandResult(f"Loaded snapshot from {target}")
        return CommandResult("Usage: load world <name> | load snapshot <path>")

    def _cmd_exit(self, _: Sequence[str]) -> CommandResult:
        return CommandResult("Exiting shell.", should_exit=True)

    _cmd_quit = _cmd_exit


def _render_summary(state: GameState) -> str:
    summary = state.summary()
    lines = ["Current world summary:"]
    for key in ("city", "tick", "districts", "factions", "agents", "stability"):
        value = summary[key]
        lines.append(f"  {key:>10}: {value}")
    return "\n".join(lines)


def _render_reports(reports: Sequence[TickReport]) -> str:
    lines: List[str] = []
    for report in reports:
        lines.append(f"Tick {report.tick} advanced.")
        env = report.environment
        lines.append(
            "  env -> "
            f"stb {env['stability']:.2f} | unrest {env['unrest']:.2f} | poll {env['pollution']:.2f}"
        )
        if report.events:
            for event in report.events:
                lines.append(f"  - {event}")
    return "\n".join(lines)


def _render_map(state: GameState, district_id: str | None) -> str:
    if district_id:
        district = next(
            (d for d in state.city.districts if d.id == district_id),
            None,
        )
        if district is None:
            return f"Unknown district '{district_id}'"
        return (
            f"District {district.name}\n"
            f"  population : {district.population}\n"
            f"  unrest     : {district.modifiers.unrest:.2f}\n"
            f"  pollution  : {district.modifiers.pollution:.2f}\n"
            f"  prosperity : {district.modifiers.prosperity:.2f}\n"
            f"  security   : {district.modifiers.security:.2f}"
        )

    header = "| District ID      | District         |   Pop | Unrest | Poll | Prosper | Sec |"
    divider = "+------------------+-----------------+-------+--------+------+---------+-----+"
    lines = ["City overview:", divider, header, divider]
    for district in state.city.districts:
        lines.append(
            f"| {district.id:<16} | {district.name:<15} | {district.population:5d} | "
            f"{district.modifiers.unrest:0.2f} | {district.modifiers.pollution:0.2f} | "
            f"{district.modifiers.prosperity:0.2f} | {district.modifiers.security:0.2f} |"
        )
    lines.append(divider)
    return "\n".join(lines)


def run_commands(
    commands: Iterable[str],
    *,
    state: GameState | None = None,
    world: str = "default",
) -> List[str]:
    base_state = state or load_world_bundle(world_name=world)
    shell = EchoesShell(base_state)
    outputs: List[str] = []
    for command in commands:
        result = shell.execute(command)
        outputs.append(result.output)
        if result.should_exit:
            break
    return outputs


def _load_initial_state(world: str, snapshot: Path | None) -> GameState:
    if snapshot is not None:
        return load_snapshot(snapshot)
    return load_world_bundle(world_name=world)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Echoes CLI shell")
    parser.add_argument("--world", "-w", default="default", help="World name to load")
    parser.add_argument(
        "--snapshot",
        "-s",
        type=Path,
        default=None,
        help="Load state from a snapshot file instead of authored content",
    )
    parser.add_argument(
        "--script",
        type=str,
        default=None,
        help="Semicolon-separated list of commands to run non-interactively",
    )
    args = parser.parse_args(argv)

    state = _load_initial_state(args.world, args.snapshot)
    shell = EchoesShell(state)

    if args.script:
        commands = [cmd.strip() for cmd in args.script.split(";") if cmd.strip()]
        for result in run_commands(commands, state=state):
            if result:
                print(result)
        return 0

    print(INTRO_TEXT)
    print(_render_summary(state))
    while True:
        try:
            line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        result = shell.execute(line)
        if result.output:
            print(result.output)
        if result.should_exit:
            break
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
