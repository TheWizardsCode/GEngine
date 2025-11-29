"""Lightweight agent AI subsystem for early-phase simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

from ..core import GameState
from ..core.models import Agent, District, Faction


@dataclass(slots=True)
class AgentIntent:
    """Represents a single agent decision within a tick."""

    agent_id: str
    agent_name: str
    intent: str
    target: str
    target_name: str
    detail: str
    reasoning: str = ""
    options_considered: List[tuple[str, float]] = field(default_factory=list)
    chosen_score: float = 0.0

    def to_report(self) -> Dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "intent": self.intent,
            "target": self.target,
            "target_name": self.target_name,
            "detail": self.detail,
            "reasoning": self.reasoning,
            "options_considered": [
                {"option": opt, "score": round(score, 4)}
                for opt, score in self.options_considered
            ],
            "chosen_score": round(self.chosen_score, 4),
        }


class AgentSystem:
    """Utility-based agent decision module.

    This early subsystem keeps decisions lightweight by selecting from
    a small set of deterministic intents while still reacting to district
    modifiers, faction legitimacy, and global unrest.
    """

    _STRATEGIC_INTENTS = {"INSPECT_DISTRICT", "NEGOTIATE_FACTION"}

    def __init__(self, *, action_limit: int = 8) -> None:
        self._action_limit = action_limit

    def tick(self, state: GameState, *, rng: random.Random) -> List[AgentIntent]:
        districts = {district.id: district for district in state.city.districts}
        factions = state.factions
        intents: List[AgentIntent] = []
        strategic_pending = True
        for agent in state.agents.values():
            if self._action_limit and len(intents) >= self._action_limit:
                break
            intent = self._decide(
                agent,
                districts,
                factions,
                state,
                rng,
                force_strategic=strategic_pending,
            )
            if intent:
                intents.append(intent)
                if intent.intent in self._STRATEGIC_INTENTS:
                    strategic_pending = False
        return intents

    # ------------------------------------------------------------------
    def _decide(
        self,
        agent: Agent,
        districts: Dict[str, District],
        factions: Dict[str, Faction],
        state: GameState,
        rng: random.Random,
        *,
        force_strategic: bool = False,
    ) -> AgentIntent | None:
        district = districts.get(agent.home_district or "")
        faction = factions.get(agent.faction_id or "") if agent.faction_id else None

        options: List[tuple[str, float]] = []
        if district:
            unrest_pressure = district.modifiers.unrest
            security_gap = 1.0 - district.modifiers.security
            pollution_pressure = district.modifiers.pollution
            options.append(("INSPECT_DISTRICT", 0.4 + pollution_pressure))
            options.append(("STABILIZE_UNREST", 0.3 + unrest_pressure))
            options.append(("SUPPORT_SECURITY", 0.2 + security_gap))
        if faction:
            legitimacy_gap = max(0.0, 0.8 - faction.legitimacy)
            options.append(("NEGOTIATE_FACTION", 0.3 + legitimacy_gap))
        options.append(("REQUEST_REPORT", 0.1 + (1.0 - state.environment.stability)))

        traits = agent.traits or {}
        empathy = traits.get("empathy", 0.5)
        cunning = traits.get("cunning", 0.5)
        resolve = traits.get("resolve", 0.5)
        for index, (intent_name, base_score) in enumerate(options):
            if intent_name == "STABILIZE_UNREST":
                options[index] = (intent_name, base_score + empathy * 0.3)
            elif intent_name == "NEGOTIATE_FACTION":
                options[index] = (intent_name, base_score + cunning * 0.3)
            elif intent_name == "SUPPORT_SECURITY":
                options[index] = (intent_name, base_score + resolve * 0.2)

        # Store all options for reasoning
        all_options = list(options)

        if force_strategic:
            strategic_options = [option for option in options if option[0] in self._STRATEGIC_INTENTS]
            if strategic_options:
                options = strategic_options

        total = sum(max(score, 0.0) for _, score in options)
        if total <= 0:
            return None

        pick = rng.uniform(0, total)
        cumulative = 0.0
        intent_name = options[-1][0]
        chosen_score = options[-1][1]
        for name, score in options:
            score = max(score, 0.0)
            cumulative += score
            if pick <= cumulative:
                intent_name = name
                chosen_score = score
                break

        return self._build_intent(
            intent_name, agent, district, faction,
            options=all_options,
            chosen_score=chosen_score,
        )

    # ------------------------------------------------------------------
    def _build_intent(
        self,
        intent_name: str,
        agent: Agent,
        district: District | None,
        faction: Faction | None,
        *,
        options: List[tuple[str, float]] | None = None,
        chosen_score: float = 0.0,
    ) -> AgentIntent:
        if intent_name == "NEGOTIATE_FACTION" and faction is not None:
            detail = f"realigns faction strategy for {faction.name}"
            target = faction.id
            target_name = faction.name
            reasoning = f"faction legitimacy gap detected ({faction.name})"
        elif intent_name == "SUPPORT_SECURITY" and district is not None:
            detail = f"coordinates volunteer watch in {district.name}"
            target = district.id
            target_name = district.name
            reasoning = f"security gap in {district.name} (security={district.modifiers.security:.2f})"
        elif intent_name == "STABILIZE_UNREST" and district is not None:
            detail = f"mediates tensions in {district.name}"
            target = district.id
            target_name = district.name
            reasoning = f"high unrest in {district.name} (unrest={district.modifiers.unrest:.2f})"
        elif intent_name == "INSPECT_DISTRICT" and district is not None:
            detail = f"surveys conditions in {district.name}"
            target = district.id
            target_name = district.name
            reasoning = f"pollution concern in {district.name} (pollution={district.modifiers.pollution:.2f})"
        elif intent_name == "REQUEST_REPORT" and district is not None:
            detail = f"files situational report on {district.name}"
            target = district.id
            target_name = district.name
            reasoning = "monitoring city stability"
        else:
            target = district.id if district else (faction.id if faction else "city")
            target_name = district.name if district else (faction.name if faction else "city")
            detail = "gathers intelligence on city status"
            reasoning = "general situation assessment"
        return AgentIntent(
            agent_id=agent.id,
            agent_name=agent.name,
            intent=intent_name,
            target=target,
            target_name=target_name,
            detail=detail,
            reasoning=reasoning,
            options_considered=list(options) if options else [],
            chosen_score=chosen_score,
        )