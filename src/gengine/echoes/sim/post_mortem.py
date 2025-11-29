"""Derives deterministic post-mortem summaries from the current game state."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Mapping, Sequence

from ..core import GameState


@dataclass
class PostMortemSummary:
    """Normalized recap of a simulation run."""

    tick: int
    environment: Dict[str, float]
    environment_trend: Dict[str, Any]
    faction_trends: List[Dict[str, Any]]
    featured_events: List[Dict[str, Any]]
    story_seeds: List[Dict[str, Any]]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_post_mortem_summary(state: GameState) -> Dict[str, Any]:
    """Build a deterministic recap that downstream tools can diff."""

    history: List[Mapping[str, Any]] = list(state.metadata.get("director_history") or [])
    events: List[Dict[str, Any]] = list(state.metadata.get("director_events") or [])
    environment = _environment_snapshot(state)
    env_trend = _environment_trend(history, environment)
    faction_trends = _faction_trends(history, state)
    seed_recap = _story_seed_recap(state, events)
    notes = _post_mortem_notes(env_trend, faction_trends, seed_recap)

    summary = PostMortemSummary(
        tick=state.tick,
        environment=environment,
        environment_trend=env_trend,
        faction_trends=faction_trends,
        featured_events=_featured_events(events),
        story_seeds=seed_recap,
        notes=notes,
    )
    payload = summary.to_dict()
    state.metadata["post_mortem"] = payload
    return payload


def _environment_snapshot(state: GameState) -> Dict[str, float]:
    env = state.environment
    return {
        "stability": round(env.stability, 3),
        "unrest": round(env.unrest, 3),
        "pollution": round(env.pollution, 3),
    }


def _environment_trend(
    history: List[Mapping[str, Any]],
    fallback: Mapping[str, float],
) -> Dict[str, Any]:
    if history:
        start_env = dict(history[0].get("environment") or {})
        end_env = dict(history[-1].get("environment") or {})
    else:
        start_env = dict(fallback)
        end_env = dict(fallback)
    trend: Dict[str, Any] = {
        "start": {
            "stability": round(float(start_env.get("stability", fallback.get("stability", 0.0))), 3),
            "unrest": round(float(start_env.get("unrest", fallback.get("unrest", 0.0))), 3),
            "pollution": round(float(start_env.get("pollution", fallback.get("pollution", 0.0))), 3),
        },
        "end": {
            "stability": round(float(end_env.get("stability", fallback.get("stability", 0.0))), 3),
            "unrest": round(float(end_env.get("unrest", fallback.get("unrest", 0.0))), 3),
            "pollution": round(float(end_env.get("pollution", fallback.get("pollution", 0.0))), 3),
        },
    }
    trend["delta"] = {
        key: round(trend["end"][key] - trend["start"][key], 3)
        for key in ("stability", "unrest", "pollution")
    }
    return trend


def _faction_trends(history: List[Mapping[str, Any]], state: GameState) -> List[Dict[str, Any]]:
    baseline: Dict[str, float] = {}
    latest: Dict[str, float] = {}
    for entry in history:
        snapshot = entry.get("faction_legitimacy") or {}
        if snapshot and not baseline:
            baseline = {k: round(float(v), 4) for k, v in snapshot.items()}
        if snapshot:
            latest = {k: round(float(v), 4) for k, v in snapshot.items()}
    if not baseline:
        baseline = {faction_id: round(faction.legitimacy, 4) for faction_id, faction in state.factions.items()}
    if not latest:
        latest = {faction_id: round(faction.legitimacy, 4) for faction_id, faction in state.factions.items()}
    entries: List[Dict[str, Any]] = []
    for faction_id in sorted(set(baseline) | set(latest)):
        start_value = baseline.get(faction_id, 0.0)
        end_value = latest.get(faction_id, start_value)
        entries.append(
            {
                "faction_id": faction_id,
                "start": round(start_value, 3),
                "end": round(end_value, 3),
                "delta": round(end_value - start_value, 3),
            }
        )
    entries.sort(key=lambda entry: abs(entry["delta"]), reverse=True)
    return entries[:3]


def _featured_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not events:
        return []
    preview = events[-3:]
    normalized: List[Dict[str, Any]] = []
    for event in reversed(preview):
        normalized.append(
            {
                "seed_id": event.get("seed_id"),
                "title": event.get("title") or event.get("seed_id"),
                "district_id": event.get("district_id"),
                "reason": event.get("reason"),
                "stakes": event.get("stakes"),
                "tick": event.get("tick"),
            }
        )
    return normalized


def _story_seed_recap(state: GameState, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lifecycle = state.metadata.get("story_seed_lifecycle") or {}
    history = list(state.metadata.get("story_seed_lifecycle_history") or [])
    history_index: Dict[str, Dict[str, Any]] = {}
    for entry in history:
        seed_id = entry.get("seed_id")
        if seed_id:
            history_index[seed_id] = entry
    event_index: Dict[str, Dict[str, Any]] = {}
    for event in events:
        seed_id = event.get("seed_id")
        if seed_id:
            event_index[seed_id] = event
    recaps: List[Dict[str, Any]] = []
    for seed_id, entry in lifecycle.items():
        recaps.append(_seed_entry(seed_id, entry, state, history_index.get(seed_id), event_index.get(seed_id)))
    # Include seeds that only live in history (e.g., archived + pruned lifecycle)
    for seed_id, entry in history_index.items():
        if any(rec["seed_id"] == seed_id for rec in recaps):
            continue
        recaps.append(_seed_entry(seed_id, entry, state, entry, event_index.get(seed_id)))
    recaps.sort(key=lambda entry: entry.get("last_activity_tick", -1), reverse=True)
    return recaps[:5]


def _seed_entry(
    seed_id: str,
    payload: Mapping[str, Any],
    state: GameState,
    last_transition: Mapping[str, Any] | None,
    last_event: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    seed = state.story_seeds.get(seed_id)
    title = seed.title if seed else seed_id
    stakes = seed.stakes if seed else None
    state_name = payload.get("state") or payload.get("to") or "primed"
    entered_tick = payload.get("entered_tick") or payload.get("tick")
    summary = {
        "seed_id": seed_id,
        "title": title,
        "state": state_name,
        "entered_tick": entered_tick,
    }
    if stakes:
        summary["stakes"] = stakes
    if last_transition:
        summary["last_transition"] = {
            "from": last_transition.get("from"),
            "to": last_transition.get("to"),
            "tick": last_transition.get("tick"),
        }
        if last_transition.get("tick") is not None:
            summary["last_activity_tick"] = last_transition["tick"]
    elif isinstance(entered_tick, int):
        summary["last_activity_tick"] = entered_tick
    event_reason = None
    district_id = None
    if last_event:
        event_reason = last_event.get("reason")
        district_id = last_event.get("district_id")
        if last_event.get("tick") is not None:
            summary["last_activity_tick"] = max(
                summary.get("last_activity_tick", -1), int(last_event["tick"])
            )
    if district_id:
        summary["district_id"] = district_id
    if event_reason:
        summary["reason"] = event_reason
    cooldown = payload.get("cooldown_remaining") or _int_or_none(payload.get("cooldown_until"))
    if isinstance(cooldown, (int, float)):
        summary["cooldown_remaining"] = int(max(cooldown, 0))
    return summary


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _post_mortem_notes(
    env_trend: Mapping[str, Any],
    faction_trends: Sequence[Mapping[str, Any]],
    seeds: Sequence[Mapping[str, Any]],
) -> List[str]:
    notes: List[str] = []
    delta = env_trend.get("delta") or {}
    stability_delta = float(delta.get("stability", 0.0))
    pollution_delta = float(delta.get("pollution", 0.0))
    if stability_delta:
        trend = "improved" if stability_delta > 0 else "fell"
        notes.append(f"Stability {trend} by {stability_delta:+.3f} across the run.")
    if pollution_delta:
        trend = "worsened" if pollution_delta > 0 else "eased"
        notes.append(f"Pollution {trend} by {pollution_delta:+.3f}.")
    if faction_trends:
        swing = faction_trends[0]
        if swing["delta"]:
            direction = "gained" if swing["delta"] > 0 else "lost"
            notes.append(
                f"Faction {swing['faction_id']} {direction} {abs(swing['delta']):.3f} legitimacy (start {swing['start']:.3f} → end {swing['end']:.3f})."
            )
    archived = [seed for seed in seeds if seed.get("state") == "archived"]
    if archived:
        names = ", ".join(seed.get("title", seed["seed_id"]) for seed in archived[:2])
        if len(archived) > 2:
            names = f"{names} (+{len(archived) - 2} more)"
        notes.append(f"Archived story seeds: {names}.")
    return notes