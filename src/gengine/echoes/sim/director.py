"""Bridges narrator digest data and evaluates travel-aware director insights."""

from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Iterable, List, Mapping, Sequence

from ..core import GameState
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

        analysis = {
            "tick": feed.get("tick"),
            "focus_center": focus_center,
            "suppressed_pressure": feed.get("suppressed_count", 0),
            "hotspots": travel_reports[: self._settings.travel_max_routes],
            "recommended_focus": recommended,
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


__all__ = ["DirectorBridge", "NarrativeDirector"]
