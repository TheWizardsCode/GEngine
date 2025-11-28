"""In-process CLI shell for driving the Echoes simulation."""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Sequence

from ..core import GameState
from ..persistence import save_snapshot
from ..client import SimServiceClient
from ..settings import SimulationConfig, SimulationLimits, load_simulation_config
from ..sim import SimEngine, TickReport

PROMPT = "(echoes) "
INTRO_TEXT = "Echoes shell ready. Type 'help' for commands."


@dataclass
class CommandResult:
    output: str
    should_exit: bool = False


class ShellBackend:
    """Interface allowing the shell to target local or remote sims."""

    def summary(self) -> dict[str, object]:  # pragma: no cover - interface
        raise NotImplementedError

    def advance_ticks(self, count: int) -> Sequence[TickReport]:  # pragma: no cover
        raise NotImplementedError

    def render_map(self, district_id: str | None) -> str:  # pragma: no cover
        raise NotImplementedError

    def save_snapshot(self, path: Path) -> str:  # pragma: no cover
        raise NotImplementedError

    def load_world(self, name: str) -> str:  # pragma: no cover
        raise NotImplementedError

    def load_snapshot(self, path: Path) -> str:  # pragma: no cover
        raise NotImplementedError


class LocalBackend(ShellBackend):
    def __init__(self, engine: SimEngine) -> None:
        self.engine = engine

    @property
    def state(self) -> GameState:
        return self.engine.state

    def summary(self) -> dict[str, object]:
        return self.engine.query_view("summary")

    def advance_ticks(self, count: int) -> Sequence[TickReport]:
        return self.engine.advance_ticks(count)

    def render_map(self, district_id: str | None) -> str:
        return _render_map(self.state, district_id)

    def save_snapshot(self, path: Path) -> str:
        save_snapshot(self.state, path)
        return f"Saved snapshot to {path}"

    def load_world(self, name: str) -> str:
        self.engine.initialize_state(world=name)
        return f"Loaded world '{name}'"

    def load_snapshot(self, path: Path) -> str:
        self.engine.initialize_state(snapshot=path)
        return f"Loaded snapshot from {path}"


class ServiceBackend(ShellBackend):
    def __init__(self, client: SimServiceClient) -> None:
        self.client = client

    def summary(self) -> dict[str, object]:
        return self.client.state("summary")["data"]

    def advance_ticks(self, count: int) -> Sequence[TickReport]:
        payload = self.client.tick(count)
        return [TickReport(**report) for report in payload["reports"]]

    def render_map(self, district_id: str | None) -> str:
        if district_id:
            detail = self.client.state("district", district_id=district_id)["data"]
            return _render_remote_district(detail)
        payload = self.client.state("snapshot")["data"]
        state = GameState.model_validate(payload)
        return _render_map(state, None)

    def save_snapshot(self, path: Path) -> str:
        payload = self.client.state("snapshot")["data"]
        GameState.model_validate(payload)
        path.write_text(_jsonify(payload))
        return f"Saved snapshot to {path}"

    def load_world(self, name: str) -> str:
        raise NotImplementedError("Loading worlds requires local backend")

    def load_snapshot(self, path: Path) -> str:
        raise NotImplementedError("Loading snapshots requires local backend")


class EchoesShell:
    """Minimal command processor for the early CLI shell."""

    def __init__(
        self,
        backend: ShellBackend,
        *,
        limits: SimulationLimits | None = None,
    ) -> None:
        self.backend = backend
        self._limits = limits

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
        summary = self.backend.summary()
        return CommandResult(_render_summary(summary))

    def _cmd_next(self, args: Sequence[str]) -> CommandResult:
        if args:
            return CommandResult("Usage: next")
        reports = self.backend.advance_ticks(1)
        return CommandResult(_render_reports(reports))

    def _cmd_run(self, args: Sequence[str]) -> CommandResult:
        if not args:
            return CommandResult("Usage: run <count>")
        try:
            count = max(1, int(args[0]))
        except ValueError:
            return CommandResult("Usage: run <count>")
        limit = self._limits.cli_run_cap if self._limits else count
        capped = min(count, limit)
        reports = self.backend.advance_ticks(capped)
        output = _render_reports(reports)
        if capped < count:
            prefix = (
                f"Safeguard: run limited to {limit} ticks (requested {count})."
            )
            output = f"{prefix}\n{output}" if output else prefix
        return CommandResult(output)

    def _cmd_map(self, args: Sequence[str]) -> CommandResult:
        district_id = args[0] if args else None
        return CommandResult(self.backend.render_map(district_id))

    def _cmd_save(self, args: Sequence[str]) -> CommandResult:
        if not args:
            return CommandResult("Usage: save <path>")
        path = Path(args[0])
        try:
            message = self.backend.save_snapshot(path)
        except NotImplementedError as exc:
            return CommandResult(str(exc))
        return CommandResult(message)

    def _cmd_load(self, args: Sequence[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult("Usage: load world <name> | load snapshot <path>")
        source = args[0]
        target = args[1]
        if source == "world":
            try:
                return CommandResult(self.backend.load_world(target))
            except NotImplementedError as exc:
                return CommandResult(str(exc))
        if source == "snapshot":
            try:
                return CommandResult(self.backend.load_snapshot(Path(target)))
            except NotImplementedError as exc:
                return CommandResult(str(exc))
        return CommandResult("Usage: load world <name> | load snapshot <path>")

    def _cmd_exit(self, _: Sequence[str]) -> CommandResult:
        return CommandResult("Exiting shell.", should_exit=True)

    _cmd_quit = _cmd_exit


def _render_summary(summary: dict[str, object]) -> str:
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


def _render_remote_district(panel: dict[str, Any]) -> str:
    mods = panel["modifiers"]
    return (
        f"District {panel['name']}\n"
        f"  population : {panel['population']}\n"
        f"  unrest     : {mods['unrest']:.2f}\n"
        f"  pollution  : {mods['pollution']:.2f}\n"
        f"  prosperity : {mods['prosperity']:.2f}\n"
        f"  security   : {mods['security']:.2f}"
    )


def _jsonify(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def run_commands(
    commands: Iterable[str],
    *,
    backend: ShellBackend | None = None,
    engine: SimEngine | None = None,
    state: GameState | None = None,
    world: str = "default",
    config: SimulationConfig | None = None,
) -> List[str]:
    active_backend = backend
    active_config = config or load_simulation_config()
    if active_backend is None:
        sim_engine = engine or SimEngine(config=active_config)
        if engine is None:
            if state is not None:
                sim_engine.initialize_state(state=state)
            else:
                sim_engine.initialize_state(world=world)
        active_backend = LocalBackend(sim_engine)
    shell = EchoesShell(active_backend, limits=active_config.limits)
    outputs: List[str] = []
    max_commands = active_config.limits.cli_script_command_cap
    executed = 0
    for command in commands:
        if executed >= max_commands:
            outputs.append(
                f"Safeguard: script exceeded {max_commands} commands; halting."
            )
            break
        executed += 1
        result = shell.execute(command)
        outputs.append(result.output)
        if result.should_exit:
            break
    return outputs


def _build_engine(
    world: str,
    snapshot: Path | None,
    *,
    config: SimulationConfig,
) -> SimEngine:
    engine = SimEngine(config=config)
    if snapshot is not None:
        engine.initialize_state(snapshot=snapshot)
    else:
        engine.initialize_state(world=world)
    return engine


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
    parser.add_argument(
        "--service-url",
        type=str,
        default=None,
        help="If provided, target a running simulation service instead of local state",
    )
    args = parser.parse_args(argv)
    config = load_simulation_config()

    client: SimServiceClient | None = None
    if args.service_url:
        client = SimServiceClient(args.service_url)
        backend: ShellBackend = ServiceBackend(client)
    else:
        engine = _build_engine(args.world, args.snapshot, config=config)
        backend = LocalBackend(engine)
    shell = EchoesShell(backend, limits=config.limits)

    try:
        if args.script:
            commands = [cmd.strip() for cmd in args.script.split(";") if cmd.strip()]
            for result in run_commands(commands, backend=backend, config=config):
                if result:
                    print(result)
            return 0

        print(INTRO_TEXT)
        print(_render_summary(backend.summary()))
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
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
