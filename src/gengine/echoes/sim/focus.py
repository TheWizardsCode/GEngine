"""Focus-aware narrative budgeting utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from ..core import GameState
from ..core.models import District
from ..settings import FocusSettings


@dataclass(slots=True)
class NarrativeEvent:
    """Structured narrative entry emitted during a tick."""

    message: str
    district_id: str | None = None
    scope: str = "global"

    def to_display(self) -> str:
        return self.message


@dataclass(slots=True)
class FocusBudgetResult:
    """Result of curating narrative events with focus-aware budgets."""

    visible: List[NarrativeEvent] = field(default_factory=list)
    archive: List[NarrativeEvent] = field(default_factory=list)
    suppressed: List[NarrativeEvent] = field(default_factory=list)
    allocation: Dict[str, object] = field(default_factory=dict)
    focus_state: Dict[str, object] = field(default_factory=dict)
    ranked_archive: List["RankedEvent"] = field(default_factory=list)


@dataclass(slots=True)
class RankedEvent:
    """Narrative entry metadata ranked for narrator history views."""

    message: str
    scope: str
    score: float
    severity: float
    focus_distance: int
    in_focus_ring: bool

    def to_payload(self) -> Dict[str, object]:
        return {
            "message": self.message,
            "scope": self.scope,
            "score": round(self.score, 3),
            "severity": round(self.severity, 3),
            "focus_distance": self.focus_distance,
            "in_focus_ring": self.in_focus_ring,
        }


class FocusManager:
    """Allocates per-tick narrative budgets around a focused district."""

    def __init__(self, *, settings: FocusSettings | None = None) -> None:
        self._settings = settings or FocusSettings()

    # ------------------------------------------------------------------
    def describe(self, state: GameState) -> Dict[str, object]:
        return dict(self._ensure_focus_state(state))

    def set_focus(self, state: GameState, district_id: str | None) -> Dict[str, object]:
        focus_payload = self._build_focus_payload(state, district_id)
        state.metadata["focus_state"] = focus_payload
        return dict(focus_payload)

    def clear_focus(self, state: GameState) -> Dict[str, object]:
        state.metadata.pop("focus_state", None)
        return self.describe(state)

    # ------------------------------------------------------------------
    def curate(
        self,
        state: GameState,
        events: Sequence[NarrativeEvent],
        *,
        event_budget: int | None,
    ) -> FocusBudgetResult:
        focus_state = self._ensure_focus_state(state)
        archive = list(events)
        total_budget = self._resolve_total_budget(len(events), event_budget)
        focus_reserved, global_reserved = self._resolve_allocations(total_budget)
        ring_ids = set(focus_state.get("ring") or [])

        visible: List[NarrativeEvent] = []
        suppressed: List[NarrativeEvent] = []
        focus_used = 0
        global_used = 0
        for entry in archive:
            in_focus = bool(entry.district_id and entry.district_id in ring_ids)
            if in_focus and focus_used < focus_reserved:
                visible.append(entry)
                focus_used += 1
                continue
            if not in_focus and global_used < global_reserved:
                visible.append(entry)
                global_used += 1
                continue
            if len(visible) < total_budget:
                visible.append(entry)
                if in_focus:
                    focus_used += 1
                else:
                    global_used += 1
                continue
            suppressed.append(entry)

        allocation = {
            "focus_center": focus_state.get("district_id"),
            "focus_ring": focus_state.get("ring", []),
            "focus_reserved": focus_reserved,
            "focus_used": focus_used,
            "global_reserved": global_reserved,
            "global_used": global_used,
            "total_budget": total_budget,
            "suppressed": len(suppressed),
        }
        ranked_archive = self._rank_events(archive, focus_state)
        return FocusBudgetResult(
            visible=visible,
            archive=archive,
            suppressed=suppressed,
            allocation=allocation,
            focus_state=dict(focus_state),
            ranked_archive=ranked_archive,
        )

    def record_digest(
        self,
        state: GameState,
        *,
        tick: int,
        result: FocusBudgetResult,
    ) -> None:
        preview_limit = self._settings.suppressed_preview
        digest_payload = {
            "tick": tick,
            "visible": [entry.to_display() for entry in result.visible],
            "suppressed_count": len(result.suppressed),
            "suppressed_preview": [
                entry.to_display() for entry in result.suppressed[:preview_limit]
            ],
            "archive": [
                entry.to_display() for entry in result.archive[: self._settings.history_limit]
            ],
            "ranked_archive": [
                ranked.to_payload()
                for ranked in result.ranked_archive[: self._settings.history_limit]
            ],
        }
        state.metadata["focus_digest"] = digest_payload
        self._append_history(
            state,
            {
                "tick": tick,
                "focus_center": result.focus_state.get("district_id"),
                "suppressed_count": len(result.suppressed),
                "suppressed_preview": digest_payload["suppressed_preview"],
                "visible_highlights": digest_payload["visible"][:preview_limit],
                "top_ranked": digest_payload["ranked_archive"][: max(1, preview_limit)],
            },
        )
        state.metadata["focus_state"] = result.focus_state

    # ------------------------------------------------------------------
    def _ensure_focus_state(self, state: GameState) -> Dict[str, object]:
        payload = state.metadata.get("focus_state")
        districts = list(state.city.districts)
        if not districts:
            empty = {"district_id": None, "neighbors": [], "ring": []}
            state.metadata["focus_state"] = empty
            return empty
        if payload:
            center_id = payload.get("district_id")
            if center_id and not any(d.id == center_id for d in districts):
                payload = None
        if not payload:
            payload = self._build_focus_payload(state, self._settings.default_district)
            state.metadata["focus_state"] = payload
        return payload

    def _build_focus_payload(
        self,
        state: GameState,
        district_id: str | None,
    ) -> Dict[str, object]:
        districts = list(state.city.districts)
        if not districts:
            return {"district_id": None, "neighbors": [], "ring": []}
        center = self._resolve_center(districts, district_id)
        ring = self._build_ring(center, districts)
        neighbors = [did for did in ring if did != center.id]
        return {
            "district_id": center.id,
            "neighbors": neighbors,
            "ring": ring,
        }

    def _resolve_center(self, districts: Sequence[District], district_id: str | None) -> District:
        lookup = {district.id: district for district in districts}
        if district_id and district_id in lookup:
            return lookup[district_id]
        if district_id and district_id not in lookup:
            raise ValueError(f"Unknown district '{district_id}'")
        default_id = self._settings.default_district
        if default_id and default_id in lookup:
            return lookup[default_id]
        return max(districts, key=lambda district: (district.population, district.id))

    def _build_ring(self, center: District, districts: Sequence[District]) -> List[str]:
        ring = [center.id]
        if self._settings.neighborhood_size <= 0:
            return ring
        candidates = [d for d in districts if d.id != center.id]
        candidates.sort(key=lambda district: (-district.population, district.id))
        for district in candidates[: self._settings.neighborhood_size]:
            ring.append(district.id)
        return ring

    def _resolve_total_budget(self, event_count: int, event_budget: int | None) -> int:
        if event_count <= 0:
            baseline = event_budget if event_budget is not None else 1
            return max(1, min(baseline, self._settings.digest_size))
        total = event_budget if event_budget is not None else event_count
        total = min(total, self._settings.digest_size)
        total = min(total, event_count)
        return max(1, total)

    def _resolve_allocations(self, total_budget: int) -> tuple[int, int]:
        if total_budget <= 1:
            return 1, 0
        focus_reserved = int(round(total_budget * self._settings.focus_budget_ratio))
        focus_reserved = min(total_budget, max(0, focus_reserved))
        global_reserved = total_budget - focus_reserved
        floor = min(self._settings.global_floor, total_budget)
        if global_reserved < floor:
            global_reserved = floor
            focus_reserved = max(0, total_budget - global_reserved)
        if focus_reserved == 0 and total_budget > global_reserved:
            focus_reserved = total_budget - global_reserved
        return focus_reserved, global_reserved

    def _rank_events(
        self,
        events: Sequence[NarrativeEvent],
        focus_state: Dict[str, object],
    ) -> List[RankedEvent]:
        ring = focus_state.get("ring") or []
        ranked: List[RankedEvent] = []
        for entry in events:
            severity = self._scope_severity(entry.scope) + self._message_bonus(entry.message)
            severity = max(0.1, min(1.5, severity))
            distance = self._focus_distance(entry.district_id, ring)
            distance_penalty = max(0.2, 1.0 - 0.15 * min(distance, 5))
            score = severity * distance_penalty
            ranked.append(
                RankedEvent(
                    message=entry.to_display(),
                    scope=entry.scope,
                    score=score,
                    severity=severity,
                    focus_distance=distance,
                    in_focus_ring=bool(entry.district_id and entry.district_id in ring),
                )
            )
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked

    def _scope_severity(self, scope: str) -> float:
        weights = {
            "environment": 1.0,
            "district": 0.9,
            "economy": 0.8,
            "faction": 0.7,
            "agent": 0.6,
            "resources": 0.5,
        }
        return weights.get(scope, 0.6)

    def _message_bonus(self, message: str) -> float:
        lowered = message.lower()
        bonus = 0.0
        triggers = {
            "spike": 0.1,
            "critical": 0.12,
            "collapse": 0.15,
            "unrest": 0.08,
            "stability": 0.08,
            "shortage": 0.07,
            "sabotage": 0.09,
            "invest": 0.05,
        }
        for keyword, value in triggers.items():
            if keyword in lowered:
                bonus += value
        return bonus

    def _focus_distance(self, district_id: str | None, ring: Sequence[str]) -> int:
        if not district_id:
            return max(2, len(ring))
        try:
            position = ring.index(district_id)
            return max(0, position)
        except ValueError:
            return max(2, len(ring))

    def _append_history(self, state: GameState, entry: Dict[str, object]) -> None:
        limit = max(1, self._settings.history_limit)
        history = list(state.metadata.get("focus_history") or [])
        history.append(entry)
        if len(history) > limit:
            history = history[-limit:]
        state.metadata["focus_history"] = history


__all__ = [
    "FocusBudgetResult",
    "FocusManager",
    "NarrativeEvent",
    "RankedEvent",
]
