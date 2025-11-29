"""Bridges narrator digest data and evaluates travel-aware director insights."""

from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Iterable, List, Mapping, Sequence

from ..core import GameState
from ..core.models import StorySeed, StorySeedTrigger
from ..settings import DirectorSettings
from .focus import FocusBudgetResult
from .spatial import euclidean_distance


class DirectorBridge:
    """Captures per-tick payloads for the upcoming narrative director."""

    def __init__(self, *, settings: DirectorSettings | None = None) -> None:
        self._settings = settings or DirectorSettings()

    def record(
        self,
        state: GameState,
        *,
        tick: int,
        focus_result: FocusBudgetResult,
    ) -> Dict[str, Any]:
        """Build and persist a director-friendly snapshot for ``tick``."""

        focus_state = focus_result.focus_state
        spatial_weights = self._spatial_preview(focus_state.get("spatial_weights") or [])
        top_ranked = self._ranked_preview(focus_result)
        payload = {
            "tick": tick,
            "focus_center": focus_state.get("district_id"),
            "focus_ring": list(focus_state.get("ring") or []),
            "focus_coordinates": focus_state.get("coordinates"),
            "spatial_weights": spatial_weights,
            "spatial_metrics": focus_state.get("spatial_metrics") or {},
            "allocation": self._clone_allocation(focus_result.allocation),
            "suppressed_count": len(focus_result.suppressed),
            "top_ranked": top_ranked,
            "environment": self._environment_snapshot(state),
            "faction_legitimacy": self._legitimacy_snapshot(state),
            "market_prices": self._market_prices(state),
        }
        state.metadata["director_feed"] = payload
        history = list(state.metadata.get("director_history") or [])
        history.append(payload)
        if len(history) > self._settings.history_limit:
            history = history[-self._settings.history_limit :]
        state.metadata["director_history"] = history
        return payload

    def _ranked_preview(self, result: FocusBudgetResult) -> List[Dict[str, Any]]:
        limit = max(1, self._settings.ranked_limit)
        preview: List[Dict[str, Any]] = []
        for ranked in result.ranked_archive[:limit]:
            preview.append(ranked.to_payload())
        return preview

    def _spatial_preview(self, weights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        limit = max(1, self._settings.spatial_preview)
        preview: List[Dict[str, Any]] = []
        for entry in weights[:limit]:
            preview.append(dict(entry))
        return preview

    @staticmethod
    def _clone_allocation(allocation: Dict[str, Any]) -> Dict[str, Any]:
        cloned: Dict[str, Any] = {}
        for key, value in allocation.items():
            if isinstance(value, list):
                cloned[key] = list(value)
            else:
                cloned[key] = value
        return cloned

    @staticmethod
    def _environment_snapshot(state: GameState) -> Dict[str, float]:
        env = state.environment
        return {
            "stability": env.stability,
            "unrest": env.unrest,
            "pollution": env.pollution,
        }

    @staticmethod
    def _legitimacy_snapshot(state: GameState) -> Dict[str, float]:
        return {
            faction_id: round(faction.legitimacy, 4)
            for faction_id, faction in state.factions.items()
        }

    @staticmethod
    def _market_prices(state: GameState) -> Dict[str, float]:
        prices = state.metadata.get("market_prices") or {}
        return {resource: round(price, 3) for resource, price in prices.items()}


class NarrativeDirector:
    """Consumes ``director_feed`` snapshots and derives travel-aware insights."""

    def __init__(self, *, settings: DirectorSettings | None = None) -> None:
        self._settings = settings or DirectorSettings()

    def evaluate(
        self,
        state: GameState,
        snapshot: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        feed = dict(snapshot or state.metadata.get("director_feed") or {})
        if not feed:
            state.metadata.pop("director_analysis", None)
            return {}

        focus_center = feed.get("focus_center")
        hotspots = self._select_hotspots(feed)
        adjacency = self._adjacency_index(state)
        coords = {district.id: district.coordinates for district in state.city.districts}
        travel_reports: List[Dict[str, Any]] = []
        recommended: Dict[str, Any] | None = None

        for hotspot in hotspots:
            target = hotspot.get("district_id")
            if not target:
                continue
            travel = self._plan_route(
                focus_center,
                target,
                adjacency,
                coords,
            )
            payload = {
                "district_id": target,
                "message": hotspot.get("message"),
                "scope": hotspot.get("scope"),
                "score": round(float(hotspot.get("score", 0.0)), 3),
                "severity": round(float(hotspot.get("severity", 0.0)), 3),
                "focus_distance": hotspot.get("focus_distance"),
                "in_focus_ring": hotspot.get("in_focus_ring"),
                "travel": travel,
            }
            travel_reports.append(payload)
            if (
                recommended is None
                and focus_center
                and target != focus_center
                and travel.get("reachable")
            ):
                recommended = {
                    "district_id": target,
                    "score": payload["score"],
                    "travel_time": travel.get("travel_time"),
                    "path": list(travel.get("path") or []),
                }

        # Fall back to the closest hotspot even if the score threshold filtered all entries.
        if not travel_reports:
            fallback = self._select_hotspots(feed, enforce_threshold=False)
            for hotspot in fallback:
                target = hotspot.get("district_id")
                if not target:
                    continue
                travel_reports.append(
                    {
                        "district_id": target,
                        "message": hotspot.get("message"),
                        "scope": hotspot.get("scope"),
                        "score": round(float(hotspot.get("score", 0.0)), 3),
                        "severity": round(float(hotspot.get("severity", 0.0)), 3),
                        "focus_distance": hotspot.get("focus_distance"),
                        "in_focus_ring": hotspot.get("in_focus_ring"),
                        "travel": self._plan_route(focus_center, target, adjacency, coords),
                    }
                )
                break

        story_seed_matches, director_events = self._match_story_seeds(
            state,
            feed=feed,
            hotspots=travel_reports,
        )

        analysis = {
            "tick": feed.get("tick"),
            "focus_center": focus_center,
            "suppressed_pressure": feed.get("suppressed_count", 0),
            "hotspots": travel_reports[: self._settings.travel_max_routes],
            "recommended_focus": recommended,
            "story_seeds": story_seed_matches,
            "director_events": director_events,
        }
        state.metadata["director_analysis"] = analysis
        return analysis

    # ------------------------------------------------------------------
    def _select_hotspots(
        self,
        feed: Mapping[str, Any],
        *,
        enforce_threshold: bool = True,
    ) -> List[Dict[str, Any]]:
        ranked = list(feed.get("top_ranked") or [])
        hotspots: List[Dict[str, Any]] = []
        for entry in ranked:
            district_id = entry.get("district_id")
            if not district_id:
                continue
            if enforce_threshold and float(entry.get("score", 0.0)) < self._settings.hotspot_score_threshold:
                continue
            hotspots.append(entry)
            if len(hotspots) >= self._settings.hotspot_limit:
                break
        return hotspots

    def _adjacency_index(self, state: GameState) -> Dict[str, List[str]]:
        adjacency: Dict[str, List[str]] = {}
        for district in state.city.districts:
            adjacency[district.id] = list(district.adjacent)
        return adjacency

    def _plan_route(
        self,
        origin: str | None,
        target: str,
        adjacency: Mapping[str, Iterable[str]],
        coords: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not origin or origin not in adjacency:
            return {
                "origin": origin,
                "target": target,
                "reachable": False,
                "path": [],
                "reason": "no_focus",
            }
        if origin == target:
            return {
                "origin": origin,
                "target": target,
                "reachable": True,
                "adjacent": True,
                "path": [origin],
                "hops": 0,
                "distance": 0.0,
                "travel_time": 0.0,
            }
        path = self._shortest_path(origin, target, adjacency)
        adjacent = target in set(adjacency.get(origin, []))
        if path:
            distance = self._path_distance(path, coords)
            hops = len(path) - 1
            travel_time = hops * self._settings.travel_time_per_hop
            if distance is not None:
                travel_time += distance * self._settings.travel_time_per_distance
            return {
                "origin": origin,
                "target": target,
                "reachable": True,
                "adjacent": adjacent,
                "path": path,
                "hops": hops,
                "distance": None if distance is None else round(distance, 3),
                "travel_time": round(travel_time, 3),
            }

        fallback_distance = euclidean_distance(coords.get(origin), coords.get(target))
        if fallback_distance is None:
            fallback_distance = self._settings.travel_default_distance
        return {
            "origin": origin,
            "target": target,
            "reachable": False,
            "adjacent": adjacent,
            "path": [],
            "reason": "disconnected",
            "fallback_distance": round(float(fallback_distance), 3),
        }

    def _shortest_path(
        self,
        origin: str,
        target: str,
        adjacency: Mapping[str, Iterable[str]],
    ) -> List[str] | None:
        if origin == target:
            return [origin]
        visited = {origin: None}
        queue: Deque[str] = deque([origin])
        while queue:
            node = queue.popleft()
            for neighbor in adjacency.get(node, []):
                if neighbor in visited:
                    continue
                visited[neighbor] = node
                if neighbor == target:
                    return self._reconstruct_path(visited, target)
                queue.append(neighbor)
        return None

    @staticmethod
    def _reconstruct_path(parents: Mapping[str, str | None], target: str) -> List[str]:
        chain: List[str] = [target]
        current = parents.get(target)
        while current is not None:
            chain.append(current)
            current = parents.get(current)
        return list(reversed(chain))

    def _path_distance(
        self,
        path: Sequence[str],
        coords: Mapping[str, Any],
    ) -> float | None:
        total = 0.0
        missing = False
        for left, right in zip(path, path[1:]):
            distance = euclidean_distance(coords.get(left), coords.get(right))
            if distance is None:
                missing = True
                break
            total += distance
        if missing:
            return None
        return total

    def _load_lifecycle(self, state: GameState) -> Dict[str, Dict[str, Any]]:
        raw = state.metadata.get("story_seed_lifecycle") or {}
        lifecycle: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw, dict):
            for seed_id, payload in raw.items():
                if isinstance(payload, dict):
                    entry = dict(payload)
                    entry["seed_id"] = seed_id
                    lifecycle[seed_id] = entry
        return lifecycle

    def _save_lifecycle(self, state: GameState, lifecycle: Dict[str, Dict[str, Any]]) -> None:
        if lifecycle:
            state.metadata["story_seed_lifecycle"] = {
                seed_id: dict(entry) for seed_id, entry in lifecycle.items()
            }
        else:
            state.metadata.pop("story_seed_lifecycle", None)

    def _transition_state(
        self,
        state: GameState,
        lifecycle: Dict[str, Dict[str, Any]],
        seed_id: str,
        new_state: str,
        tick: int,
        *,
        updates: Dict[str, Any] | None = None,
        record: bool = True,
    ) -> Dict[str, Any]:
        entry = lifecycle.setdefault(
            seed_id,
            {"seed_id": seed_id, "state": "primed", "entered_tick": tick},
        )
        prev_state = entry.get("state", "primed")
        if record and prev_state != new_state:
            self._record_lifecycle_history(state, seed_id, prev_state, new_state, tick)
        entry["state"] = new_state
        entry["entered_tick"] = tick
        if updates:
            for key, value in updates.items():
                if value is None:
                    entry.pop(key, None)
                else:
                    entry[key] = value
        return entry

    def _record_lifecycle_history(
        self,
        state: GameState,
        seed_id: str,
        previous: str,
        new_state: str,
        tick: int,
    ) -> None:
        history = list(state.metadata.get("story_seed_lifecycle_history") or [])
        history.append({"tick": tick, "seed_id": seed_id, "from": previous, "to": new_state})
        limit = getattr(self._settings, "lifecycle_history_limit", 10)
        if len(history) > limit:
            history = history[-limit:]
        state.metadata["story_seed_lifecycle_history"] = history

    def _advance_lifecycle_states(
        self,
        state: GameState,
        lifecycle: Dict[str, Dict[str, Any]],
        tick: int,
    ) -> None:
        for seed_id in list(lifecycle.keys()):
            entry = lifecycle[seed_id]
            current = entry.get("state", "primed")
            if current == "active":
                expires = entry.get("state_expires")
                duration = max(0, getattr(self._settings, "seed_active_ticks", 0))
                if duration == 0 or (isinstance(expires, (int, float)) and tick >= int(expires)):
                    resolve_duration = max(0, getattr(self._settings, "seed_resolve_ticks", 0))
                    resolve_expires = tick + resolve_duration if resolve_duration else None
                    self._transition_state(
                        state,
                        lifecycle,
                        seed_id,
                        "resolving",
                        tick,
                        updates={"state_expires": resolve_expires},
                    )
            elif current == "resolving":
                expires = entry.get("state_expires")
                duration = max(0, getattr(self._settings, "seed_resolve_ticks", 0))
                if duration == 0 or (isinstance(expires, (int, float)) and tick >= int(expires)):
                    quiet_span = max(0, getattr(self._settings, "seed_quiet_ticks", 0))
                    quiet_until = tick + quiet_span if quiet_span else None
                    self._transition_state(
                        state,
                        lifecycle,
                        seed_id,
                        "archived",
                        tick,
                        updates={"state_expires": None, "quiet_until": quiet_until},
                    )
            elif current == "archived":
                quiet_until = entry.get("quiet_until")
                cooldown_until = entry.get("cooldown_until")
                ready_tick = tick
                if isinstance(quiet_until, (int, float)):
                    ready_tick = max(ready_tick, int(quiet_until))
                if isinstance(cooldown_until, (int, float)):
                    ready_tick = max(ready_tick, int(cooldown_until))
                if tick >= ready_tick:
                    self._transition_state(
                        state,
                        lifecycle,
                        seed_id,
                        "primed",
                        tick,
                        updates={"state_expires": None, "quiet_until": None, "cooldown_until": None},
                    )

        for seed_id in list(lifecycle.keys()):
            if seed_id not in state.story_seeds:
                lifecycle.pop(seed_id, None)

    @staticmethod
    def _state_remaining(entry: Mapping[str, Any], tick: int) -> int | None:
        expires = entry.get("state_expires")
        if not isinstance(expires, (int, float)):
            return None
        return max(int(expires) - tick, 0)

    @staticmethod
    def _sync_contexts_with_lifecycle(
        contexts: Dict[str, Dict[str, Any]],
        lifecycle: Mapping[str, Mapping[str, Any]],
    ) -> None:
        for seed_id in list(contexts.keys()):
            state_name = lifecycle.get(seed_id, {}).get("state")
            if state_name not in {"active", "resolving"}:
                contexts.pop(seed_id, None)

    def _normalize_quiet_timer(self, state: GameState, tick: int) -> int:
        quiet_until = state.metadata.get("director_quiet_until")
        if isinstance(quiet_until, (int, float)):
            quiet_value = int(quiet_until)
        else:
            quiet_value = 0
        if quiet_value and tick >= quiet_value:
            state.metadata.pop("director_quiet_until", None)
            return 0
        return quiet_value

    def _store_pacing_summary(
        self,
        state: GameState,
        *,
        tick: int,
        lifecycle: Mapping[str, Mapping[str, Any]],
        quiet_until: int,
        blocked: Sequence[str],
    ) -> None:
        active = 0
        resolving = 0
        for entry in lifecycle.values():
            current = entry.get("state")
            if current == "active":
                active += 1
            elif current == "resolving":
                resolving += 1
        summary = {
            "tick": tick,
            "active": active,
            "resolving": resolving,
            "max_active": getattr(self._settings, "max_active_seeds", 1),
            "global_quiet_until": quiet_until,
            "global_quiet_remaining": max(quiet_until - tick, 0) if quiet_until else 0,
        }
        if blocked:
            summary["blocked_reasons"] = sorted(set(blocked))
        if any(
            (
                summary["active"],
                summary["resolving"],
                summary["global_quiet_until"],
                summary.get("blocked_reasons"),
            )
        ):
            state.metadata["director_pacing"] = summary
        else:
            state.metadata.pop("director_pacing", None)

    # ------------------------------------------------------------------
    def _match_story_seeds(
        self,
        state: GameState,
        *,
        feed: Mapping[str, Any],
        hotspots: Sequence[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if not state.story_seeds:
            state.metadata.pop("story_seeds_active", None)
            state.metadata.pop("story_seed_cooldowns", None)
            state.metadata.pop("story_seed_context", None)
            state.metadata.pop("story_seed_lifecycle", None)
            state.metadata.pop("story_seed_lifecycle_history", None)
            state.metadata.pop("director_pacing", None)
            state.metadata.pop("director_events", None)
            state.metadata.pop("director_quiet_until", None)
            return [], []

        ranked = list(feed.get("top_ranked") or [])
        suppressed = int(feed.get("suppressed_count", 0))
        tick = int(feed.get("tick") or state.tick)
        lifecycle = self._load_lifecycle(state)
        self._advance_lifecycle_states(state, lifecycle, tick)
        cooldowns = dict(state.metadata.get("story_seed_cooldowns") or {})
        raw_contexts = state.metadata.get("story_seed_context") or {}
        contexts: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw_contexts, dict):
            for seed_id, payload in raw_contexts.items():
                if isinstance(payload, dict):
                    contexts[seed_id] = dict(payload)
        travel_lookup = {
            entry.get("district_id"): entry.get("travel")
            for entry in hotspots
            if entry.get("district_id")
        }
        district_lookup = {district.id: district.name for district in state.city.districts}
        new_events: List[Dict[str, Any]] = []
        quiet_until = self._normalize_quiet_timer(state, tick)
        blocked_reasons: List[str] = []
        max_active = max(1, getattr(self._settings, "max_active_seeds", 1))
        active_count = sum(
            1 for entry in lifecycle.values() if entry.get("state") in {"active", "resolving"}
        )
        self._sync_contexts_with_lifecycle(contexts, lifecycle)

        for seed in state.story_seeds.values():
            if not seed.triggers:
                continue
            entry = lifecycle.setdefault(
                seed.id,
                {"seed_id": seed.id, "state": "primed", "entered_tick": tick},
            )
            if entry.get("state") != "primed":
                continue
            if quiet_until and tick < quiet_until:
                blocked_reasons.append("global_quiet")
                break
            if active_count >= max_active:
                blocked_reasons.append("max_active")
                break
            seed_quiet_until = entry.get("quiet_until")
            if isinstance(seed_quiet_until, (int, float)) and tick < int(seed_quiet_until):
                blocked_reasons.append("seed_quiet")
                continue
            last_tick = cooldowns.get(seed.id)
            cooldown_window = max(1, seed.cooldown_ticks or 0)
            if last_tick is not None and tick - last_tick < cooldown_window:
                continue
            trigger_match = self._match_seed_trigger(seed.triggers, ranked, suppressed)
            if trigger_match is None:
                continue
            target = trigger_match.get("district_id")
            if not target:
                if seed.travel_hint and seed.travel_hint.district_id:
                    target = seed.travel_hint.district_id
                elif seed.preferred_districts:
                    target = seed.preferred_districts[0]
                else:
                    target = feed.get("focus_center")
            travel = travel_lookup.get(target)
            travel_hint = seed.travel_hint.model_dump() if seed.travel_hint else None
            contexts[seed.id] = {
                "seed_id": seed.id,
                "title": seed.title,
                "summary": seed.summary,
                "stakes": seed.stakes,
                "district_id": target,
                "scope": seed.scope,
                "tags": list(seed.tags),
                "roles": seed.roles.model_dump(),
                "resolution_templates": seed.resolution_templates.model_dump(),
                "followups": list(seed.followups),
                "beats": list(seed.beats[:2]),
                "reason": trigger_match.get("reason"),
                "score": trigger_match.get("score"),
                "travel": dict(travel) if isinstance(travel, dict) else travel,
                "last_trigger_tick": tick,
            }
            if travel_hint:
                contexts[seed.id]["travel_hint"] = travel_hint
            cooldowns[seed.id] = tick
            event_payload = self._build_director_event(
                state,
                seed=seed,
                tick=tick,
                district_id=target,
                trigger_match=trigger_match,
                travel=travel,
                district_lookup=district_lookup,
            )
            if event_payload:
                new_events.append(event_payload)
            active_duration = max(0, getattr(self._settings, "seed_active_ticks", 0))
            active_expires = tick + active_duration if active_duration else None
            entry = self._transition_state(
                state,
                lifecycle,
                seed.id,
                "active",
                tick,
                updates={"state_expires": active_expires, "quiet_until": None},
            )
            entry["cooldown_until"] = tick + cooldown_window
            active_count += 1
            quiet_span = max(0, getattr(self._settings, "global_quiet_ticks", 0))
            if quiet_span:
                quiet_until = tick + quiet_span
                state.metadata["director_quiet_until"] = quiet_until
            else:
                quiet_until = 0
                state.metadata.pop("director_quiet_until", None)

        active_matches: List[Dict[str, Any]] = []
        for seed in state.story_seeds.values():
            entry = lifecycle.get(seed.id)
            if not entry or entry.get("state") not in {"active", "resolving"}:
                continue
            payload = contexts.get(seed.id)
            if not payload:
                continue
            enriched = dict(payload)
            enriched["state"] = entry.get("state")
            remaining = self._state_remaining(entry, tick)
            if remaining is not None:
                enriched["state_remaining"] = remaining
            cooldown_until = entry.get("cooldown_until")
            if isinstance(cooldown_until, (int, float)):
                enriched["cooldown_remaining"] = max(int(cooldown_until) - tick, 0)
            else:
                enriched["cooldown_remaining"] = 0
            active_matches.append(enriched)

        active_matches.sort(
            key=lambda entry: (
                float(entry.get("score", 0.0)),
                int(entry.get("last_trigger_tick") or 0),
            ),
            reverse=True,
        )
        if len(active_matches) > self._settings.story_seed_limit:
            active_matches = active_matches[: self._settings.story_seed_limit]

        cooldowns = {seed_id: value for seed_id, value in cooldowns.items() if seed_id in state.story_seeds}
        contexts = {seed_id: payload for seed_id, payload in contexts.items() if seed_id in state.story_seeds}

        if active_matches:
            state.metadata["story_seeds_active"] = active_matches
        else:
            state.metadata.pop("story_seeds_active", None)
        if cooldowns:
            state.metadata["story_seed_cooldowns"] = cooldowns
        else:
            state.metadata.pop("story_seed_cooldowns", None)
        if contexts:
            state.metadata["story_seed_context"] = contexts
        else:
            state.metadata.pop("story_seed_context", None)
        self._save_lifecycle(state, lifecycle)

        if new_events:
            history = list(state.metadata.get("director_events") or [])
            history.extend(new_events)
            limit = getattr(self._settings, "event_history_limit", len(history) or 1)
            limit = max(1, limit)
            if len(history) > limit:
                history = history[-limit:]
            state.metadata["director_events"] = history

        self._store_pacing_summary(
            state,
            tick=tick,
            lifecycle=lifecycle,
            quiet_until=quiet_until,
            blocked=blocked_reasons,
        )

        return active_matches, new_events

    def _match_seed_trigger(
        self,
        triggers: Sequence[StorySeedTrigger],
        ranked: Sequence[Mapping[str, Any]],
        suppressed: int,
    ) -> Dict[str, Any] | None:
        for trigger in triggers:
            if suppressed < trigger.min_suppressed:
                continue
            match = self._match_hotspot(trigger, ranked)
            if match is not None:
                return match
        return None

    def _match_hotspot(
        self,
        trigger: StorySeedTrigger,
        ranked: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any] | None:
        for entry in ranked:
            district_id = entry.get("district_id")
            if trigger.district_id and trigger.district_id != district_id:
                continue
            scope = entry.get("scope")
            if trigger.scope and trigger.scope != scope:
                continue
            score = float(entry.get("score", 0.0))
            if score < trigger.min_score:
                continue
            severity = float(entry.get("severity", 0.0))
            if severity < trigger.min_severity:
                continue
            focus_distance = entry.get("focus_distance")
            if (
                trigger.max_focus_distance is not None
                and (focus_distance is None or focus_distance > trigger.max_focus_distance)
            ):
                continue
            return {
                "district_id": district_id,
                "reason": entry.get("message"),
                "score": round(score, 3),
                "severity": round(severity, 3),
            }
        return None

    def _build_director_event(
        self,
        state: GameState,
        *,
        seed: StorySeed,
        tick: int,
        district_id: str | None,
        trigger_match: Mapping[str, Any],
        travel: Mapping[str, Any] | None,
        district_lookup: Mapping[str, str],
    ) -> Dict[str, Any]:
        travel_payload = dict(travel) if isinstance(travel, dict) else None
        event = {
            "tick": tick,
            "seed_id": seed.id,
            "title": seed.title,
            "summary": seed.summary,
            "stakes": seed.stakes,
            "scope": seed.scope,
            "district_id": district_id,
            "district_name": district_lookup.get(district_id, district_id) if district_id else None,
            "reason": trigger_match.get("reason"),
            "score": trigger_match.get("score"),
            "severity": trigger_match.get("severity"),
            "cooldown_ticks": seed.cooldown_ticks,
            "beats": list(seed.beats[:2]),
            "followups": list(seed.followups),
            "resolution_templates": seed.resolution_templates.model_dump(),
            "roles": seed.roles.model_dump(),
            "agents": self._resolve_agents(state, seed.roles.agents),
            "factions": self._resolve_factions(state, seed.roles.factions),
        }
        if travel_payload:
            event["travel"] = travel_payload
        if seed.travel_hint:
            event["travel_hint"] = seed.travel_hint.model_dump()
        return event

    def _resolve_agents(self, state: GameState, agent_ids: Sequence[str]) -> List[Dict[str, Any]]:
        resolved: List[Dict[str, Any]] = []
        for agent_id in agent_ids[:3]:
            agent = state.agents.get(agent_id)
            if agent is None:
                resolved.append({"id": agent_id})
                continue
            resolved.append(
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role,
                    "faction_id": agent.faction_id,
                    "home_district": agent.home_district,
                }
            )
        return resolved

    def _resolve_factions(self, state: GameState, faction_ids: Sequence[str]) -> List[Dict[str, Any]]:
        resolved: List[Dict[str, Any]] = []
        for faction_id in faction_ids[:3]:
            faction = state.factions.get(faction_id)
            if faction is None:
                resolved.append({"id": faction_id})
                continue
            resolved.append(
                {
                    "id": faction.id,
                    "name": faction.name,
                    "ideology": faction.ideology,
                }
            )
        return resolved


__all__ = ["DirectorBridge", "NarrativeDirector"]
