"""Faction AI subsystem for Phase 4 (M4.2)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

from ..core import GameState
from ..core.models import District, Faction


@dataclass(slots=True)
class FactionAction:
    """Structured record of a faction-level decision."""

    faction_id: str
    faction_name: str
    action: str
    target: str
    target_name: str
    detail: str
    legitimacy_delta: float
    resource_delta: int

    def to_report(self) -> Dict[str, object]:
        return {
            "faction_id": self.faction_id,
            "faction_name": self.faction_name,
            "action": self.action,
            "target": self.target,
            "target_name": self.target_name,
            "detail": self.detail,
            "legitimacy_delta": round(self.legitimacy_delta, 4),
            "resource_delta": self.resource_delta,
        }


class FactionSystem:
    """Low-frequency strategic decision module for factions."""

    def __init__(self, *, cooldown_ticks: int = 3) -> None:
        self._cooldown_ticks = cooldown_ticks
        self._cooldowns: Dict[str, int] = {}

    def tick(self, state: GameState, *, rng: random.Random) -> List[FactionAction]:
        districts = {district.id: district for district in state.city.districts}
        factions = state.factions
        actions: List[FactionAction] = []
        for faction in factions.values():
            cooldown = self._cooldowns.get(faction.id, 0)
            if cooldown > 0:
                self._cooldowns[faction.id] = cooldown - 1
                continue
            action = self._decide_action(faction, districts, factions, state, rng)
            if action is not None:
                actions.append(action)
                self._cooldowns[faction.id] = self._cooldown_ticks
        return actions

    # ------------------------------------------------------------------
    def _decide_action(
        self,
        faction: Faction,
        districts: Dict[str, District],
        factions: Dict[str, Faction],
        state: GameState,
        rng: random.Random,
    ) -> FactionAction | None:
        metrics = self._territory_metrics(faction, districts)
        pressure = self._resource_pressure(faction)
        rival = self._strongest_rival(faction, factions)

        options: List[tuple[str, float]] = []
        if faction.legitimacy < 0.7:
            options.append(("LOBBY_COUNCIL", 0.4 + (0.7 - faction.legitimacy)))
        if metrics["unrest"] > 0.55 or metrics["security"] < 0.45:
            options.append(("INVEST_DISTRICT", 0.35 + metrics["unrest"]))
        if pressure < 0.5:
            options.append(("RECRUIT_SUPPORT", 0.3 + (0.5 - pressure)))
        if rival is not None:
            options.append(("SABOTAGE_RIVAL", 0.25 + rival.legitimacy))

        if not options:
            return None

        total = sum(max(score, 0.0) for _, score in options)
        if total <= 0:
            return None

        pick = rng.uniform(0, total)
        cumulative = 0.0
        action_name = options[-1][0]
        for name, score in options:
            score = max(score, 0.0)
            cumulative += score
            if pick <= cumulative:
                action_name = name
                break

        return self._execute_action(action_name, faction, districts, rival, state)

    # ------------------------------------------------------------------
    def _execute_action(
        self,
        action: str,
        faction: Faction,
        districts: Dict[str, District],
        rival: Faction | None,
        state: GameState,
    ) -> FactionAction | None:
        if action == "LOBBY_COUNCIL":
            delta_leg = min(0.06, 1.0 - faction.legitimacy)
            faction.legitimacy = _clamp(faction.legitimacy + delta_leg)
            resource_delta = self._shift_resource(faction, -2)
            detail = "campaigns for broader mandate"
            return FactionAction(
                faction_id=faction.id,
                faction_name=faction.name,
                action=action,
                target="city",
                target_name=state.city.name,
                detail=detail,
                legitimacy_delta=delta_leg,
                resource_delta=resource_delta,
            )

        if action == "RECRUIT_SUPPORT":
            resource_delta = self._shift_resource(faction, 4)
            delta_leg = 0.015
            faction.legitimacy = _clamp(faction.legitimacy + delta_leg)
            detail = "organizes recruitment drive across districts"
            return FactionAction(
                faction_id=faction.id,
                faction_name=faction.name,
                action=action,
                target="city",
                target_name=state.city.name,
                detail=detail,
                legitimacy_delta=delta_leg,
                resource_delta=resource_delta,
            )

        if action == "INVEST_DISTRICT":
            district = self._select_district(faction, districts)
            if district is None:
                return None
            unrest_delta = -0.05
            security_delta = 0.03
            prosperity_delta = 0.04
            district.modifiers.unrest = _clamp(
                district.modifiers.unrest + unrest_delta
            )
            district.modifiers.security = _clamp(
                district.modifiers.security + security_delta
            )
            district.modifiers.prosperity = _clamp(
                district.modifiers.prosperity + prosperity_delta
            )
            delta_leg = 0.02
            faction.legitimacy = _clamp(faction.legitimacy + delta_leg)
            resource_delta = self._shift_resource(faction, -3)
            detail = f"injects resources into {district.name}"
            return FactionAction(
                faction_id=faction.id,
                faction_name=faction.name,
                action=action,
                target=district.id,
                target_name=district.name,
                detail=detail,
                legitimacy_delta=delta_leg,
                resource_delta=resource_delta,
            )

        if action == "SABOTAGE_RIVAL" and rival is not None:
            rival_delta = -0.04
            rival.legitimacy = _clamp(rival.legitimacy + rival_delta)
            actor_leg_delta = -0.01
            faction.legitimacy = _clamp(faction.legitimacy + actor_leg_delta)
            resource_delta = self._shift_resource(faction, -2)
            target_name = rival.name
            target_id = rival.id
            detail = f"disrupts operations run by {rival.name}"
            district = self._select_district(rival, districts)
            if district is not None:
                detail = f"agitates unrest in {district.name}"
                district.modifiers.unrest = _clamp(
                    district.modifiers.unrest + 0.04
                )
            return FactionAction(
                faction_id=faction.id,
                faction_name=faction.name,
                action=action,
                target=target_id,
                target_name=target_name,
                detail=detail,
                legitimacy_delta=actor_leg_delta,
                resource_delta=resource_delta,
            )

        return None

    # ------------------------------------------------------------------
    def _territory_metrics(
        self,
        faction: Faction,
        districts: Dict[str, District],
    ) -> Dict[str, float]:
        values = [districts[did] for did in faction.territory if did in districts]
        if not values:
            return {"unrest": 0.5, "security": 0.5}
        unrest = sum(d.modifiers.unrest for d in values) / len(values)
        security = sum(d.modifiers.security for d in values) / len(values)
        return {"unrest": unrest, "security": security}

    def _resource_pressure(self, faction: Faction) -> float:
        if not faction.resources:
            return 0.0
        total = sum(max(value, 0) for value in faction.resources.values())
        cap = max(len(faction.resources) * 40, 1)
        return _clamp(total / cap)

    def _strongest_rival(
        self,
        faction: Faction,
        factions: Dict[str, Faction],
    ) -> Faction | None:
        rivals = [candidate for candidate in factions.values() if candidate.id != faction.id]
        if not rivals:
            return None
        return max(rivals, key=lambda rival: rival.legitimacy)

    def _select_district(
        self,
        faction: Faction,
        districts: Dict[str, District],
    ) -> District | None:
        owned = [districts[did] for did in faction.territory if did in districts]
        if not owned:
            return None
        return max(owned, key=lambda district: district.modifiers.unrest)

    def _shift_resource(self, faction: Faction, amount: int) -> int:
        if not faction.resources:
            if amount > 0:
                faction.resources["influence"] = amount
                return amount
            return 0
        key = max(faction.resources, key=lambda name: faction.resources[name])
        current = faction.resources[key]
        new_value = max(0, current + amount)
        faction.resources[key] = new_value
        return new_value - current


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
