"""In-process CLI shell for driving the Echoes simulation."""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Sequence

from ..core import GameState
from ..persistence import save_snapshot
from ..client import SimServiceClient
from ..settings import SimulationConfig, SimulationLimits, load_simulation_config
from ..sim import SimEngine, TickReport

try:
    from . import display
    from io import StringIO
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

PROMPT = "(echoes) "

# Cached styled prompt for Rich mode
_STYLED_PROMPT: str | None = None


def _get_prompt(enable_rich: bool) -> str:
    """Return the prompt string, optionally styled green with Rich."""
    global _STYLED_PROMPT
    if not enable_rich or not RICH_AVAILABLE:
        return PROMPT
    if _STYLED_PROMPT is None:
        console = Console(file=StringIO(), force_terminal=True)
        console.print("[green](echoes)[/green] ", end="")
        _STYLED_PROMPT = console.file.getvalue()
    return _STYLED_PROMPT


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

    def focus_state(self) -> dict[str, object]:  # pragma: no cover
        raise NotImplementedError

    def set_focus(self, district_id: str | None) -> dict[str, object]:  # pragma: no cover
        raise NotImplementedError

    def focus_history(self) -> List[dict[str, object]]:  # pragma: no cover
        raise NotImplementedError

    def post_mortem(self) -> dict[str, object]:  # pragma: no cover
        raise NotImplementedError

    def query_timeline(self, count: int = 10) -> List[dict[str, object]]:  # pragma: no cover
        raise NotImplementedError

    def explain(self, entity_type: str, entity_id: str) -> dict[str, object]:  # pragma: no cover
        raise NotImplementedError

    def why(self, query: str) -> dict[str, object]:  # pragma: no cover
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover - optional cleanup
        """Hook for releasing backend resources (network clients, etc.)."""
        return None


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

    def focus_state(self) -> dict[str, object]:
        return self.engine.focus_state()

    def set_focus(self, district_id: str | None) -> dict[str, object]:
        if district_id is None:
            return self.engine.clear_focus()
        return self.engine.set_focus(district_id)

    def focus_history(self) -> List[dict[str, object]]:
        return self.engine.focus_history()

    def post_mortem(self) -> dict[str, object]:
        return self.engine.query_view("post-mortem")

    def query_timeline(self, count: int = 10) -> List[dict[str, object]]:
        return self.engine.query_timeline(count)

    def explain(self, entity_type: str, entity_id: str) -> dict[str, object]:
        if entity_type == "faction":
            return self.engine.explain_faction(entity_id)
        if entity_type == "agent":
            return self.engine.explain_agent(entity_id)
        if entity_type == "district":
            return self.engine.explain_district(entity_id)
        if entity_type == "metric":
            return self.engine.explain_metric(entity_id)
        return {"error": f"Unknown entity type '{entity_type}'"}

    def why(self, query: str) -> dict[str, object]:
        return self.engine.why(query)

    def close(self) -> None:  # pragma: no cover - nothing to release
        return None


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

    def focus_state(self) -> dict[str, object]:
        payload = self.client.focus_state()
        return payload.get("focus", {})

    def set_focus(self, district_id: str | None) -> dict[str, object]:
        payload = self.client.set_focus(district_id)
        return payload.get("focus", {})

    def focus_history(self) -> List[dict[str, object]]:
        payload = self.client.focus_state()
        history = payload.get("history") or []
        return list(history)

    def post_mortem(self) -> dict[str, object]:
        payload = self.client.state("post-mortem")
        return payload.get("data", {})

    def query_timeline(self, count: int = 10) -> List[dict[str, object]]:
        # Timeline data is included in the summary under explanation_timeline_history
        payload = self.client.state("summary")["data"]
        history = payload.get("explanation_timeline_history") or []
        return list(history[-count:])

    def explain(self, entity_type: str, entity_id: str) -> dict[str, object]:
        # Explanations require local backend for now
        raise NotImplementedError("Explanations require local backend")

    def why(self, query: str) -> dict[str, object]:
        # Why queries require local backend for now
        raise NotImplementedError("Why queries require local backend")

    def close(self) -> None:
        self.client.close()


class EchoesShell:
    """Minimal command processor for the early CLI shell."""

    def __init__(
        self,
        backend: ShellBackend,
        *,
        limits: SimulationLimits | None = None,
        enable_rich: bool = False,
    ) -> None:
        self.backend = backend
        self._limits = limits
        self.enable_rich = enable_rich and RICH_AVAILABLE

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
            "Available commands: summary, next [n], run <n>, map [district], focus [district|clear], "
            "history [count], director [count], postmortem, timeline [count], explain <type> <id>, "
            "why <query>, save <path>, load world <name>|snapshot <path>, help, exit"
        )

    def _cmd_summary(self, _: Sequence[str]) -> CommandResult:
        summary = self.backend.summary()
        if self.enable_rich:
            return CommandResult(display.render_summary_table(summary))
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
        if self.enable_rich and not args:
            summary = self.backend.summary()
            return CommandResult(display.render_map_overlay(summary))
        district_id = args[0] if args else None
        return CommandResult(self.backend.render_map(district_id))

    def _cmd_focus(self, args: Sequence[str]) -> CommandResult:
        try:
            if not args:
                focus = self.backend.focus_state()
            else:
                target = args[0]
                if target.lower() == "clear":
                    focus = self.backend.set_focus(None)
                else:
                    focus = self.backend.set_focus(target)
        except ValueError as exc:
            return CommandResult(str(exc))
        return CommandResult(_render_focus_state(focus))

    def _cmd_history(self, args: Sequence[str]) -> CommandResult:
        limit: int | None = None
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                return CommandResult("Usage: history [count]")
        history = self.backend.focus_history()
        if not history:
            return CommandResult("No focus history recorded.")
        entries = history if limit is None else history[-limit:]
        return CommandResult(_render_history(entries))

    def _cmd_director(self, args: Sequence[str]) -> CommandResult:
        limit: int | None = None
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                return CommandResult("Usage: director [count]")
        summary = self.backend.summary()
        feed = summary.get("director_feed")
        history = summary.get("director_history") or []
        analysis = summary.get("director_analysis")
        if not feed:
            return CommandResult("No director feed recorded.")
        entries = history if limit is None else history[-limit:]
        if self.enable_rich:
            return CommandResult(display.render_director_table(feed, entries, analysis))
        return CommandResult(_render_director_feed(feed, entries, analysis))

    def _cmd_postmortem(self, args: Sequence[str]) -> CommandResult:
        if args:
            return CommandResult("Usage: postmortem")
        payload = self.backend.post_mortem()
        if not payload:
            return CommandResult("Post-mortem summary unavailable; run a few ticks first.")
        return CommandResult(_render_post_mortem(payload))

    def _cmd_timeline(self, args: Sequence[str]) -> CommandResult:
        limit: int = 10
        if args:
            try:
                limit = max(1, int(args[0]))
            except ValueError:
                return CommandResult("Usage: timeline [count]")
        try:
            entries = self.backend.query_timeline(limit)
        except NotImplementedError as exc:
            return CommandResult(str(exc))
        if not entries:
            return CommandResult("No timeline data recorded. Run some ticks first.")
        return CommandResult(_render_timeline(entries))

    def _cmd_explain(self, args: Sequence[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(
                "Usage: explain <type> <id>\n"
                "Types: faction, agent, district, metric"
            )
        entity_type = args[0].lower()
        entity_id = args[1]
        try:
            result = self.backend.explain(entity_type, entity_id)
        except NotImplementedError as exc:
            return CommandResult(str(exc))
        if "error" in result:
            return CommandResult(str(result["error"]))
        return CommandResult(_render_explanation(entity_type, result))

    def _cmd_why(self, args: Sequence[str]) -> CommandResult:
        if not args:
            return CommandResult(
                "Usage: why <query>\n"
                "Examples: why stability, why did unrest rise, why union-of-flux"
            )
        query = " ".join(args)
        try:
            result = self.backend.why(query)
        except NotImplementedError as exc:
            return CommandResult(str(exc))
        return CommandResult(_render_why_answer(result))

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
    impact = summary.get("environment_impact")
    if isinstance(impact, dict) and impact:
        pressure = impact.get("scarcity_pressure", 0.0)
        lines.append("  env impact:")
        lines.append(f"    scarcity pressure: {pressure:.2f}")
        if impact.get("diffusion_applied"):
            lines.append("    diffusion: active")
        avg_pollution = impact.get("average_pollution")
        if isinstance(avg_pollution, (int, float)):
            lines.append(f"    avg pollution: {float(avg_pollution):.3f}")
        extremes = impact.get("extremes") or {}
        if isinstance(extremes, dict) and extremes:
            max_info = extremes.get("max") or {}
            min_info = extremes.get("min") or {}
            if max_info and min_info:
                lines.append(
                    "    extremes: "
                    f"max {max_info.get('district')} {float(max_info.get('pollution', 0.0)):.3f}"
                    ", "
                    f"min {min_info.get('district')} {float(min_info.get('pollution', 0.0)):.3f}"
                )
        deltas = impact.get("district_deltas") or {}
        if deltas:
            sample_id, sample_delta = next(iter(deltas.items()))
            poll_delta = sample_delta.get("pollution", 0.0)
            lines.append(
                f"    sample delta: {sample_id} pollution {poll_delta:+.3f}"
            )
        diffusion_samples = impact.get("diffusion_samples") or []
        if diffusion_samples:
            preview = []
            for sample in diffusion_samples[:2]:
                delta = float(sample.get("delta", 0.0))
                preview.append(
                    f"{sample.get('district_id')}: {delta:+.3f}"
                )
            if preview:
                lines.append(f"    diffusion samples: {', '.join(preview)}")
        biodiversity = impact.get("biodiversity") or {}
        if isinstance(biodiversity, dict) and biodiversity.get("value") is not None:
            value = biodiversity.get("value")
            if isinstance(value, (int, float)):
                delta = biodiversity.get("delta")
                delta_text = ""
                if isinstance(delta, (int, float)) and abs(delta) >= 1e-4:
                    delta_text = f" ({delta:+.3f})"
                lines.append(f"    biodiversity: {value:.3f}{delta_text}")
                stab = impact.get("stability_effects") or {}
                stability_delta = stab.get("biodiversity_delta")
                if isinstance(stability_delta, (int, float)) and abs(stability_delta) >= 1e-4:
                    lines.append(f"    stability<-bio: {stability_delta:+.3f}")
        faction_effects = impact.get("faction_effects") or []
        if faction_effects:
            preview = []
            for effect in faction_effects[:2]:
                preview.append(
                    f"{effect['faction']}->{effect['district']} ({effect['pollution_delta']:+.3f})"
                )
            lines.append(f"    faction effects: {', '.join(preview)}")
    focus = summary.get("focus")
    if isinstance(focus, dict) and focus.get("district_id"):
        neighbors = focus.get("neighbors") or []
        neighbor_text = ", ".join(neighbors) if neighbors else "none"
        lines.append(
            f"  focus -> {focus['district_id']} (neighbors: {neighbor_text})"
        )
        coords = focus.get("coordinates")
        if coords:
            lines.append(f"    coords: {_format_coordinates(coords)}")
        adjacency = focus.get("adjacent") or []
        if adjacency:
            lines.append(f"    adjacent: {', '.join(adjacency)}")
        weights = focus.get("spatial_weights") or []
        if weights:
            preview = ", ".join(
                f"{entry['district_id']}:{float(entry.get('score', 0.0)):.2f}"
                for entry in weights[:3]
            )
            lines.append(f"    spatial weights: {preview}")
        metrics = focus.get("spatial_metrics") or {}
        ref = metrics.get("distance_reference")
        fallback = metrics.get("fallback_distance")
        if isinstance(ref, (int, float)) and ref > 0:
            lines.append(f"    distance ref: {ref:.2f}")
        elif isinstance(fallback, (int, float)) and fallback > 0:
            lines.append(f"    distance ref: fallback {fallback:.2f}")
    digest = summary.get("focus_digest")
    if isinstance(digest, dict) and digest.get("visible"):
        lines.append("  focus digest:")
        for event in digest.get("visible", [])[:3]:
            lines.append(f"    - {event}")
        suppressed = digest.get("suppressed_count", 0)
        if suppressed:
            lines.append(f"    suppressed: {suppressed} archived events")
        ranked = digest.get("ranked_archive") or []
        if ranked:
            preview = []
            for item in ranked[:2]:
                score = float(item.get("score", 0.0))
                message = item.get("message", "")
                preview.append(f"{score:.2f}:{message}")
            if preview:
                lines.append(f"    ranked: {', '.join(preview)}")
    director_feed = summary.get("director_feed")
    if isinstance(director_feed, dict) and director_feed:
        lines.append("  director feed:")
        lines.append(
            "    focus="
            f"{director_feed.get('focus_center') or 'unset'} suppressed={director_feed.get('suppressed_count', 0)}"
        )
        top_ranked = director_feed.get("top_ranked") or []
        if top_ranked:
            preview = []
            for item in top_ranked[:2]:
                score = float(item.get("score", 0.0))
                preview.append(f"{score:.2f}:{item.get('message', '')}")
            if preview:
                lines.append(f"    ranked: {', '.join(preview)}")
        weights = director_feed.get("spatial_weights") or []
        if weights:
            preview = []
            for entry in weights[:2]:
                preview.append(
                    f"{entry.get('district_id', 'n/a')}:{float(entry.get('score', 0.0)):.2f}"
                )
            if preview:
                lines.append(f"    spatial: {', '.join(preview)}")
    analysis = summary.get("director_analysis")
    if isinstance(analysis, dict) and analysis:
        lines.append("  director analysis:")
        recommended = analysis.get("recommended_focus")
        if isinstance(recommended, dict) and recommended.get("district_id"):
            travel_time = recommended.get("travel_time")
            if isinstance(travel_time, (int, float)):
                rec_text = (
                    f"    recommend focus -> {recommended['district_id']} "
                    f"({travel_time:.2f} travel time)"
                )
            else:
                rec_text = f"    recommend focus -> {recommended['district_id']}"
            lines.append(rec_text)
        hotspots = analysis.get("hotspots") or []
        if hotspots:
            preview = []
            for hotspot in hotspots[:2]:
                travel = hotspot.get("travel") or {}
                travel_time = travel.get("travel_time")
                if isinstance(travel_time, (int, float)):
                    preview.append(
                        f"{hotspot.get('district_id', 'n/a')}:{travel_time:.2f}t"
                    )
                elif travel.get("reachable") is False:
                    preview.append(f"{hotspot.get('district_id', 'n/a')}:blocked")
                else:
                    preview.append(f"{hotspot.get('district_id', 'n/a')}:pending")
            if preview:
                lines.append(f"    travel: {', '.join(preview)}")
    pacing = summary.get("director_pacing")
    if isinstance(pacing, dict) and pacing:
        lines.append("  director pacing:")
        lines.append(
            "    active/resolving -> "
            f"{pacing.get('active', 0)}/{pacing.get('resolving', 0)} (max {pacing.get('max_active', 0)})"
        )
        quiet_until = pacing.get("global_quiet_until")
        quiet_remaining = pacing.get("global_quiet_remaining")
        if isinstance(quiet_until, (int, float)) and quiet_until > 0:
            if isinstance(quiet_remaining, (int, float)) and quiet_remaining > 0:
                lines.append(
                    f"    quiet until tick {int(quiet_until)} ({int(quiet_remaining)} ticks)"
                )
            else:
                lines.append(f"    quiet until tick {int(quiet_until)}")
        blocked = pacing.get("blocked_reasons") or []
        if blocked:
            lines.append(f"    blocked: {', '.join(blocked)}")
        tick = pacing.get("tick")
        if isinstance(tick, (int, float)):
            lines.append(f"    tick: {int(tick)}")
    story_seeds = summary.get("story_seeds") or []
    if story_seeds:
        lines.append("  story seeds:")
        for seed in story_seeds[:3]:
            district = seed.get("district_id")
            score = seed.get("score")
            prefix = f"    - {seed.get('title', seed.get('seed_id', 'seed'))}"
            if district:
                prefix = f"{prefix} @ {district}"
            if isinstance(score, (int, float)):
                prefix = f"{prefix} ({score:.2f})"
            reason = seed.get("reason")
            if reason:
                prefix = f"{prefix} :: {reason}"
            lifecycle_bits: List[str] = []
            state_name = seed.get("state")
            if state_name:
                lifecycle_bits.append(state_name)
            state_remaining = seed.get("state_remaining")
            if isinstance(state_remaining, (int, float)) and state_remaining > 0:
                lifecycle_bits.append(f"{int(state_remaining)}t")
            if lifecycle_bits:
                prefix = f"{prefix} <{'|'.join(lifecycle_bits)}>"
            cooldown_bits: List[str] = []
            remaining = seed.get("cooldown_remaining")
            if isinstance(remaining, (int, float)):
                cooldown_bits.append(f"{int(remaining)}t cd")
            last_tick = seed.get("last_trigger_tick")
            if isinstance(last_tick, (int, float)):
                cooldown_bits.append(f"last {int(last_tick)}")
            if cooldown_bits:
                prefix = f"{prefix} [{' | '.join(cooldown_bits)}]"
            lines.append(prefix)
            stakes = seed.get("stakes")
            if stakes:
                lines.append(f"      stakes: {stakes}")
        if len(story_seeds) > 3:
            lines.append(f"    (+{len(story_seeds) - 3} more)")
    director_events = summary.get("director_events") or []
    if director_events:
        lines.append("  director events:")
        preview = list(reversed(director_events[-2:]))
        for event in preview:
            title = event.get("title") or event.get("seed_id", "seed")
            district = event.get("district_id") or "unset"
            reason = event.get("reason")
            line = f"    - {title} @ {district}"
            if reason:
                line = f"{line} :: {reason}"
            lines.append(line)
            stakes = event.get("stakes")
            if stakes:
                lines.append(f"      stakes: {stakes}")
            participants: List[str] = []
            agents = event.get("agents") or []
            for agent in agents:
                name = agent.get("name")
                if name:
                    participants.append(name)
                    break
            factions = event.get("factions") or []
            for faction in factions:
                name = faction.get("name")
                if name:
                    participants.append(name)
                    break
            if participants:
                lines.append(f"      roles: {', '.join(participants)}")
    profiling = summary.get("profiling")
    if isinstance(profiling, dict) and profiling:
        lines.append("  profiling:")
        lines.append(
            "    tick ms -> "
            f"p50 {profiling.get('tick_ms_p50', 0.0):.2f} | "
            f"p95 {profiling.get('tick_ms_p95', 0.0):.2f} | max {profiling.get('tick_ms_max', 0.0):.2f}"
        )
        last_subs = profiling.get("last_subsystem_ms") or {}
        if last_subs:
            preview = ", ".join(
                f"{name}:{value:.2f}ms"
                for name, value in list(last_subs.items())[:3]
            )
            lines.append(f"    last subsystems: {preview}")
        slowest = profiling.get("slowest_subsystem")
        if isinstance(slowest, dict) and slowest.get("name"):
            lines.append(
                "    slowest: "
                f"{slowest['name']} {slowest.get('ms', 0.0):.2f}ms"
            )
        anomalies = profiling.get("anomalies") or []
        if anomalies:
            lines.append(
                f"    anomalies: {', '.join(anomalies[:3])}"
            )
    return "\n".join(lines)

def _render_post_mortem(payload: Mapping[str, Any]) -> str:
    lines = ["Post-mortem recap:"]
    tick = payload.get("tick")
    if isinstance(tick, int):
        lines.append(f"  ticks analyzed: 0 → {tick}")
    environment_trend = payload.get("environment_trend") or {}
    delta = environment_trend.get("delta") or {}
    if delta:
        stability = float(delta.get("stability", 0.0))
        unrest = float(delta.get("unrest", 0.0))
        pollution = float(delta.get("pollution", 0.0))
        lines.append(
            "  environment trend: "
            f"stability {stability:+.3f}, unrest {unrest:+.3f}, pollution {pollution:+.3f}"
        )
    factions = payload.get("faction_trends") or []
    if factions:
        lines.append("  faction swings:")
        for entry in factions[:3]:
            lines.append(
                "    - "
                f"{entry['faction_id']}: {entry['start']:.3f} → {entry['end']:.3f} ({entry['delta']:+.3f})"
            )
    events = payload.get("featured_events") or []
    if events:
        lines.append("  featured events:")
        for event in events:
            title = event.get("title") or event.get("seed_id")
            district = event.get("district_id") or "n/a"
            tick_label = event.get("tick")
            tick_text = tick_label if tick_label is not None else "n/a"
            lines.append(f"    - {title} @ {district} (tick {tick_text})")
    seeds = payload.get("story_seeds") or []
    if seeds:
        lines.append("  story seeds:")
        for seed in seeds[:3]:
            title = seed.get("title") or seed.get("seed_id")
            state = seed.get("state") or "primed"
            district = seed.get("district_id") or "n/a"
            lines.append(f"    - {title} [{state}] focus={district}")
        remaining = max(0, len(seeds) - 3)
        if remaining:
            lines.append(f"    (+{remaining} more seeds tracked)")
    notes = payload.get("notes") or []
    if notes:
        lines.append("  notes:")
        for note in notes[:3]:
            lines.append(f"    - {note}")
    return "\n".join(lines)


def _render_focus_state(focus: dict[str, object] | None) -> str:
    focus = focus or {}
    center = focus.get("district_id")
    neighbors = focus.get("neighbors") or []
    ring = focus.get("ring") or []
    lines = ["Focus configuration:"]
    lines.append(f"  center   : {center or 'unset'}")
    lines.append(f"  neighbors: {', '.join(neighbors) if neighbors else 'none'}")
    if ring:
        lines.append(f"  ring     : {', '.join(ring)}")
    coords = focus.get("coordinates")
    if coords:
        lines.append(f"  coords   : {_format_coordinates(coords)}")
    adjacency = focus.get("adjacent") or []
    lines.append(f"  adjacent : {', '.join(adjacency) if adjacency else 'none'}")
    metrics = focus.get("spatial_metrics") or {}
    ref = metrics.get("distance_reference")
    fallback = metrics.get("fallback_distance")
    if isinstance(ref, (int, float)) and ref > 0:
        lines.append(f"  distance : {ref:.2f}")
    elif isinstance(fallback, (int, float)) and fallback > 0:
        lines.append(f"  distance : fallback {fallback:.2f}")
    weights = focus.get("spatial_weights") or []
    if weights:
        lines.append("  spatial weights:")
        for entry in weights[:4]:
            distance = entry.get("distance")
            distance_text = (
                f"{float(distance):.2f}" if isinstance(distance, (int, float)) else "n/a"
            )
            lines.append(
                "    "
                f"{entry['district_id']:<16} score {float(entry.get('score', 0.0)):.2f} "
                f"pop {float(entry.get('population_rank', 0.0)):.2f} dist {distance_text}"
            )
    return "\n".join(lines)


def _render_history(entries: Sequence[dict[str, object]]) -> str:
    lines = ["Focus history (latest first):"]
    for entry in reversed(entries):
        tick = entry.get("tick")
        center = entry.get("focus_center") or "unset"
        suppressed = entry.get("suppressed_count", 0)
        lines.append(f"  tick {tick}: focus={center} suppressed={suppressed}")
        top_ranked = entry.get("top_ranked") or []
        for ranked in top_ranked[:3]:
            score = ranked.get("score", 0.0)
            message = ranked.get("message", "")
            lines.append(f"    ({score:.2f}) {message}")
        preview = entry.get("suppressed_preview") or []
        if preview:
            lines.append(f"    preview: {', '.join(preview[:3])}")
    return "\n".join(lines)


def _render_director_feed(
    feed: dict[str, object],
    history: Sequence[dict[str, object]] | None = None,
    analysis: dict[str, object] | None = None,
) -> str:
    lines = ["Director feed:"]
    tick = feed.get("tick")
    focus_center = feed.get("focus_center") or "unset"
    suppressed = feed.get("suppressed_count", 0)
    lines.append(f"  tick {tick}: focus={focus_center} suppressed={suppressed}")
    ring = feed.get("focus_ring") or []
    if ring:
        lines.append(f"  ring: {', '.join(ring)}")
    allocation = feed.get("allocation") or {}
    if allocation:
        lines.append(
            "  allocation -> "
            f"focus {allocation.get('focus_used', 0)}/{allocation.get('focus_reserved', 0)} | "
            f"global {allocation.get('global_used', 0)}/{allocation.get('global_reserved', 0)}"
        )
    weights = feed.get("spatial_weights") or []
    if weights:
        preview = ", ".join(
            f"{entry.get('district_id', 'n/a')}:{float(entry.get('score', 0.0)):.2f}"
            for entry in weights[:3]
        )
        lines.append(f"  spatial preview: {preview}")
    ranked = feed.get("top_ranked") or []
    if ranked:
        lines.append("  ranked beats:")
        for item in ranked[:3]:
            score = float(item.get("score", 0.0))
            message = item.get("message", "")
            lines.append(f"    ({score:.2f}) {message}")
    env = feed.get("environment") or {}
    if env:
        lines.append(
            "  environment -> "
            f"stb {env.get('stability', 0.0):.2f} | "
            f"unrest {env.get('unrest', 0.0):.2f} | "
            f"poll {env.get('pollution', 0.0):.2f}"
        )
    history = history or []
    if history:
        lines.append("  recent snapshots:")
        for entry in reversed(history[-3:]):
            lines.append(
                f"    tick {entry.get('tick')}: focus={entry.get('focus_center') or 'unset'} "
                f"suppressed={entry.get('suppressed_count', 0)}"
            )
    if analysis:
        hotspots = analysis.get("hotspots") or []
        if hotspots:
            lines.append("  travel planning:")
            for hotspot in hotspots[:3]:
                travel = hotspot.get("travel") or {}
                prefix = hotspot.get("district_id", "n/a")
                if travel.get("reachable"):
                    hops = travel.get("hops")
                    travel_time = travel.get("travel_time")
                    detail = ""
                    if isinstance(hops, int):
                        detail += f"{hops} hops"
                    if isinstance(travel_time, (int, float)):
                        detail = f"{detail} | {travel_time:.2f}t" if detail else f"{travel_time:.2f}t"
                    lines.append(f"    {prefix}: {detail or 'reachable'}")
                else:
                    reason = travel.get("reason", "blocked")
                    lines.append(f"    {prefix}: {reason}")
        seeds = analysis.get("story_seeds") or []
        if seeds:
            lines.append("  seed matches:")
            for seed in seeds[:3]:
                reason = seed.get("reason")
                detail = seed.get("district_id") or "unset"
                score = seed.get("score")
                line = f"    - {seed.get('title', seed.get('seed_id', 'seed'))}"
                if detail:
                    line = f"{line} -> {detail}"
                if isinstance(score, (int, float)):
                    line = f"{line} ({score:.2f})"
                if reason:
                    line = f"{line} :: {reason}"
                cooldown_bits: List[str] = []
                remaining = seed.get("cooldown_remaining")
                if isinstance(remaining, (int, float)):
                    cooldown_bits.append(f"{int(remaining)}t cd")
                last_tick = seed.get("last_trigger_tick")
                if isinstance(last_tick, (int, float)):
                    cooldown_bits.append(f"last {int(last_tick)}")
                if cooldown_bits:
                    line = f"{line} [{' | '.join(cooldown_bits)}]"
                lines.append(line)
            if len(seeds) > 3:
                lines.append(f"    (+{len(seeds) - 3} more)")
        events = analysis.get("director_events") or []
        if events:
            lines.append("  director events:")
            for event in events[:3]:
                title = event.get("title") or event.get("seed_id", "seed")
                district = event.get("district_id") or "unset"
                tick = event.get("tick")
                snippet = f"    - {title} @ {district}"
                if isinstance(tick, int):
                    snippet = f"{snippet} [tick {tick}]"
                lines.append(snippet)
                agent = next((agent for agent in event.get("agents", []) if agent.get("name")), None)
                faction = next(
                    (faction for faction in event.get("factions", []) if faction.get("name")),
                    None,
                )
                participants: List[str] = []
                if agent:
                    participants.append(agent["name"])
                if faction:
                    participants.append(faction["name"])
                if participants:
                    lines.append(f"      roles: {', '.join(participants)}")
                stakes = event.get("stakes")
                if stakes:
                    lines.append(f"      stakes: {stakes}")
        recommended = analysis.get("recommended_focus")
        if isinstance(recommended, dict) and recommended.get("district_id"):
            travel_time = recommended.get("travel_time")
            if isinstance(travel_time, (int, float)):
                lines.append(
                    "  recommendation: focus -> "
                    f"{recommended['district_id']} ({travel_time:.2f}t)"
                )
            else:
                lines.append(f"  recommendation: focus -> {recommended['district_id']}")
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
        if report.faction_legitimacy_delta:
            lines.append("  faction legitimacy:")
            for faction_id, delta in sorted(
                report.faction_legitimacy_delta.items(),
                key=lambda item: abs(item[1]),
                reverse=True,
            )[:3]:
                lines.append(
                    f"    {faction_id:<18} {'+' if delta > 0 else ''}{delta:.3f}"
                )
        if report.economy:
            prices = report.economy.get("prices", {})
            if prices:
                sample = ", ".join(
                    f"{resource}:{price:.2f}" for resource, price in sorted(prices.items())[:3]
                )
                lines.append(f"  market -> {sample}")
        if report.events:
            for event in report.events:
                lines.append(f"  - {event}")
        if report.focus_budget:
            fb = report.focus_budget
            lines.append(
                "  focus budget -> "
                f"focus {fb.get('focus_used', 0)}/{fb.get('focus_reserved', 0)} | "
                f"global {fb.get('global_used', 0)}/{fb.get('global_reserved', 0)} | "
                f"suppressed {fb.get('suppressed', 0)}"
            )
        if report.suppressed_events:
            lines.append(
                f"  suppressed archive: {len(report.suppressed_events)} events held back"
            )
        if report.anomalies:
            lines.append(f"  anomalies: {', '.join(report.anomalies)}")
    return "\n".join(lines)


def _render_map(state: GameState, district_id: str | None) -> str:
    if district_id:
        district = next(
            (d for d in state.city.districts if d.id == district_id),
            None,
        )
        if district is None:
            return f"Unknown district '{district_id}'"
        detail = [
            f"District {district.name}",
            f"  population : {district.population}",
            f"  unrest     : {district.modifiers.unrest:.2f}",
            f"  pollution  : {district.modifiers.pollution:.2f}",
            f"  prosperity : {district.modifiers.prosperity:.2f}",
            f"  security   : {district.modifiers.security:.2f}",
            f"  coordinates: {_format_coordinates(district.coordinates)}",
        ]
        neighbors = ", ".join(district.adjacent) if district.adjacent else "none"
        detail.append(f"  adjacent   : {neighbors}")
        return "\n".join(detail)

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
    lines.append("Geometry overlay:")
    for district in state.city.districts:
        coord_text = _format_coordinates(district.coordinates)
        adjacency = ", ".join(district.adjacent) if district.adjacent else "none"
        lines.append(
            f"  {district.id:<16} coords {coord_text:<18} neighbors: {adjacency}"
        )
    return "\n".join(lines)


def _render_remote_district(panel: dict[str, Any]) -> str:
    mods = panel["modifiers"]
    lines = [
        f"District {panel['name']}",
        f"  population : {panel['population']}",
        f"  unrest     : {mods['unrest']:.2f}",
        f"  pollution  : {mods['pollution']:.2f}",
        f"  prosperity : {mods['prosperity']:.2f}",
        f"  security   : {mods['security']:.2f}",
        f"  coordinates: {_format_coordinates(panel.get('coordinates'))}",
    ]
    adjacency = panel.get("adjacent") or []
    lines.append(f"  adjacent   : {', '.join(adjacency) if adjacency else 'none'}")
    return "\n".join(lines)


def _format_coordinates(coords: Any | None) -> str:
    if coords is None:
        return "n/a"
    if hasattr(coords, "x") and hasattr(coords, "y"):
        x = getattr(coords, "x")
        y = getattr(coords, "y")
        z = getattr(coords, "z", None)
    elif isinstance(coords, dict):
        x = coords.get("x")
        y = coords.get("y")
        z = coords.get("z")
    else:
        return "n/a"
    if x is None or y is None:
        return "n/a"
    if isinstance(z, (int, float)):
        return f"({float(x):.1f}, {float(y):.1f}, {float(z):.1f})"
    return f"({float(x):.1f}, {float(y):.1f})"


def _render_timeline(entries: Sequence[Mapping[str, Any]]) -> str:
    lines = ["Causal timeline (recent events):"]
    for entry in reversed(entries[-10:]):
        tick = entry.get("tick", "?")
        lines.append(f"  Tick {tick}:")
        key_changes = entry.get("key_changes") or []
        if key_changes:
            for change in key_changes[:3]:
                lines.append(f"    • {change}")
        events = entry.get("events") or []
        if events:
            for event in events[:5]:
                desc = event.get("description", "event")
                category = event.get("category", "")
                lines.append(f"    [{category}] {desc}")
        agent_reasoning = entry.get("agent_reasoning") or []
        if agent_reasoning:
            for reasoning in agent_reasoning[:2]:
                name = reasoning.get("agent_name", "Agent")
                action = reasoning.get("action", "acted")
                factors = reasoning.get("reasoning_factors") or []
                text = f"    {name} {action}"
                if factors:
                    text = f"{text} (because: {', '.join(factors[:2])})"
                lines.append(text)
    if not entries:
        lines.append("  No events recorded yet.")
    return "\n".join(lines)


def _render_explanation(entity_type: str, result: Mapping[str, Any]) -> str:
    lines: List[str] = []
    if entity_type == "faction":
        name = result.get("faction_name", result.get("faction_id"))
        lines.append(f"Faction: {name}")
        lines.append(f"  Legitimacy: {result.get('current_legitimacy', 0):.3f}")
        trend = result.get("legitimacy_trend", 0)
        if trend:
            direction = "↑" if trend > 0 else "↓"
            lines.append(f"  Trend: {direction} {abs(trend):.3f}")
        actions = result.get("recent_actions") or []
        if actions:
            lines.append("  Recent actions:")
            for action in actions:
                tick = action.get("tick", "?")
                act = action.get("action", "acted")
                target = action.get("target")
                desc = f"    tick {tick}: {act}"
                if target:
                    desc = f"{desc} → {target}"
                effects = action.get("effects") or []
                if effects:
                    desc = f"{desc} ({', '.join(effects[:2])})"
                lines.append(desc)
    elif entity_type == "agent":
        name = result.get("agent_name", result.get("agent_id"))
        lines.append(f"Agent: {name}")
        lines.append(f"  Role: {result.get('role', 'unknown')}")
        faction = result.get("faction_id")
        if faction:
            lines.append(f"  Faction: {faction}")
        home = result.get("home_district")
        if home:
            lines.append(f"  Home: {home}")
        lines.append(f"  Reasoning: {result.get('reasoning_summary', 'No recent activity')}")
        needs = result.get("current_needs") or {}
        if needs:
            need_strs = [f"{k}:{v:.2f}" for k, v in list(needs.items())[:4]]
            lines.append(f"  Needs: {', '.join(need_strs)}")
        goals = result.get("goals") or []
        if goals:
            lines.append(f"  Goals: {', '.join(goals[:3])}")
        actions = result.get("recent_actions") or []
        if actions:
            lines.append("  Recent actions:")
            for action in actions:
                tick = action.get("tick", "?")
                act = action.get("action", "acted")
                target = action.get("target")
                reasoning = action.get("reasoning") or []
                desc = f"    tick {tick}: {act}"
                if target:
                    desc = f"{desc} → {target}"
                if reasoning:
                    desc = f"{desc} (because: {', '.join(reasoning[:2])})"
                lines.append(desc)
    elif entity_type == "district":
        name = result.get("district_name", result.get("district_id"))
        lines.append(f"District: {name}")
        lines.append(f"  Population: {result.get('population', 0):,}")
        mods = result.get("modifiers") or {}
        if mods:
            lines.append(
                f"  Modifiers: unrest={mods.get('unrest', 0):.2f}, "
                f"pollution={mods.get('pollution', 0):.2f}"
            )
        seeds = result.get("story_seeds") or []
        if seeds:
            lines.append("  Story seeds:")
            for seed in seeds:
                desc = seed.get("description", "event")
                lines.append(f"    • {desc}")
        activity = result.get("faction_activity") or []
        if activity:
            lines.append("  Faction activity:")
            for event in activity[:3]:
                desc = event.get("description", "activity")
                lines.append(f"    • {desc}")
    elif entity_type == "metric":
        metric = result.get("metric", "unknown")
        lines.append(f"Metric: {metric}")
        current = result.get("current_value")
        if current is not None:
            lines.append(f"  Current: {current:.3f}")
        delta = result.get("total_delta", 0)
        if delta:
            direction = "↑" if delta > 0 else "↓"
            lines.append(f"  Change: {direction} {abs(delta):.4f}")
        causes = result.get("causes") or []
        if causes:
            lines.append("  Causes:")
            for cause in causes[:5]:
                lines.append(f"    • {cause}")
        events = result.get("events") or []
        if events:
            lines.append(f"  Related events: {len(events)}")
    else:
        lines.append(f"Unknown entity type: {entity_type}")
    return "\n".join(lines)


def _render_why_answer(result: Mapping[str, Any]) -> str:
    lines: List[str] = []
    if not result.get("matched", True):
        query = result.get("query", "")
        lines.append(f"Could not find specific information for: '{query}'")
        suggestion = result.get("suggestion")
        if suggestion:
            lines.append(f"  Tip: {suggestion}")
        changes = result.get("recent_changes") or []
        if changes:
            lines.append("  Recent changes in the simulation:")
            for change in changes[:5]:
                lines.append(f"    • {change}")
        return "\n".join(lines)

    # Handle metric explanations
    metric = result.get("metric")
    if metric:
        lines.append(f"Why {metric}?")
        current = result.get("current_value")
        if current is not None:
            lines.append(f"  Current value: {current:.3f}")
        delta = result.get("total_delta", 0)
        if delta:
            direction = "increased" if delta > 0 else "decreased"
            lines.append(f"  Recently {direction} by {abs(delta):.4f}")
        causes = result.get("causes") or []
        if causes:
            lines.append("  Contributing factors:")
            for cause in causes[:5]:
                lines.append(f"    • {cause}")
        return "\n".join(lines)

    # Handle faction explanations
    faction_name = result.get("faction_name")
    if faction_name:
        lines.append(f"About {faction_name}:")
        lines.append(f"  Legitimacy: {result.get('current_legitimacy', 0):.3f}")
        trend = result.get("legitimacy_trend", 0)
        if trend:
            direction = "gaining" if trend > 0 else "losing"
            lines.append(f"  Currently {direction} influence ({abs(trend):.3f})")
        actions = result.get("recent_actions") or []
        if actions:
            lines.append("  Recent actions explain their position:")
            for action in actions[:3]:
                act = action.get("action", "acted")
                target = action.get("target")
                desc = f"    • {act}"
                if target:
                    desc = f"{desc} targeting {target}"
                lines.append(desc)
        return "\n".join(lines)

    # Handle agent explanations
    agent_name = result.get("agent_name")
    if agent_name:
        lines.append(f"About {agent_name}:")
        reasoning = result.get("reasoning_summary")
        if reasoning:
            lines.append(f"  {reasoning}")
        needs = result.get("current_needs") or {}
        if needs:
            critical = [f"{k}:{v:.2f}" for k, v in needs.items() if v < 0.4 or v > 0.7]
            if critical:
                lines.append(f"  Key needs: {', '.join(critical[:3])}")
        return "\n".join(lines)

    # Handle district explanations
    district_name = result.get("district_name")
    if district_name:
        lines.append(f"About {district_name}:")
        mods = result.get("modifiers") or {}
        if mods:
            issues = []
            if mods.get("unrest", 0) > 0.6:
                issues.append(f"high unrest ({mods['unrest']:.2f})")
            if mods.get("pollution", 0) > 0.6:
                issues.append(f"elevated pollution ({mods['pollution']:.2f})")
            if issues:
                lines.append(f"  Issues: {', '.join(issues)}")
        return "\n".join(lines)

    # Fallback
    lines.append("Analysis complete but no specific insights available.")
    return "\n".join(lines)


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
    parser.add_argument(
        "--rich",
        action="store_true",
        help="Enable enhanced ASCII views with Rich formatting (tables, colors, panels)",
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
    shell = EchoesShell(backend, limits=config.limits, enable_rich=args.rich)

    try:
        if args.script:
            commands = [cmd.strip() for cmd in args.script.split(";") if cmd.strip()]
            for result in run_commands(commands, backend=backend, config=config):
                if result:
                    print(result)
            return 0

        print(INTRO_TEXT)
        print(_render_summary(backend.summary()))
        prompt = _get_prompt(shell.enable_rich)
        while True:
            try:
                line = input(prompt)
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
