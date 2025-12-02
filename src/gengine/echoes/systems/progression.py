"""Progression system for updating player skills, reputation, and access tiers.

This system integrates with agent actions and faction negotiations to:
- Grant skill experience based on player actions
- Modify reputation based on faction interactions
- Unlock access tiers as skills improve
- Provide success rate modifiers for skill checks
- Track per-agent progression (expertise, reliability, stress)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..core import GameState
from ..core.progression import (
    ProgressionState,
    SkillDomain,
    calculate_agent_modifier,
    calculate_success_modifier,
)


@dataclass(slots=True)
class ProgressionEvent:
    """Records a progression change during a tick."""

    tick: int
    event_type: (
        str  # "skill_gain", "reputation_change", "tier_unlock", "agent_progression"
    )
    domain: Optional[str] = None
    faction_id: Optional[str] = None
    agent_id: Optional[str] = None
    amount: float = 0.0
    new_level: Optional[int] = None
    new_tier: Optional[str] = None
    detail: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "tick": self.tick,
            "event_type": self.event_type,
            "domain": self.domain,
            "faction_id": self.faction_id,
            "agent_id": self.agent_id,
            "amount": round(self.amount, 2),
            "new_level": self.new_level,
            "new_tier": self.new_tier,
            "detail": self.detail,
        }


@dataclass
class ProgressionSettings:
    """Configuration for progression rates and thresholds."""

    # Base experience rates per action type
    base_experience_rate: float = 1.0

    # Skill domain experience multipliers
    diplomacy_multiplier: float = 1.0
    investigation_multiplier: float = 1.0
    economics_multiplier: float = 1.0
    tactical_multiplier: float = 1.0
    influence_multiplier: float = 1.0

    # Reputation change rates
    reputation_gain_rate: float = 0.05  # Per successful interaction
    reputation_loss_rate: float = 0.03  # Per failed or hostile interaction

    # Skill level caps
    skill_cap: int = 100

    # Access tier thresholds (average skill level required)
    established_threshold: int = 50
    elite_threshold: int = 100

    # Experience scaling
    experience_per_action: float = 10.0
    experience_per_inspection: float = 5.0
    experience_per_negotiation: float = 15.0

    def get_domain_multiplier(self, domain: SkillDomain | str) -> float:
        """Get the experience multiplier for a skill domain."""
        key = domain.value if isinstance(domain, SkillDomain) else domain
        multipliers = {
            SkillDomain.DIPLOMACY.value: self.diplomacy_multiplier,
            SkillDomain.INVESTIGATION.value: self.investigation_multiplier,
            SkillDomain.ECONOMICS.value: self.economics_multiplier,
            SkillDomain.TACTICAL.value: self.tactical_multiplier,
            SkillDomain.INFLUENCE.value: self.influence_multiplier,
        }
        return multipliers.get(key, 1.0)


@dataclass
class PerAgentProgressionSettings:
    """Configuration for per-agent progression (layered on global)."""

    # Feature toggle
    enable_per_agent_modifiers: bool = False

    # Expertise settings
    expertise_max_pips: int = 5
    expertise_gain_per_success: int = 1

    # Reliability settings
    reliability_gain_per_success: float = 0.05
    reliability_loss_per_failure: float = 0.08

    # Stress settings
    stress_gain_per_failure: float = 0.1
    stress_gain_per_hazardous: float = 0.05
    stress_recovery_per_tick: float = 0.02

    # Success modifier bounds
    max_expertise_bonus: float = 0.1
    max_stress_penalty: float = 0.1


# Actions considered hazardous for stress calculations.
# Hazardous actions apply higher stress gain (+0.1 instead of base stress_delta)
# because they involve dangerous or confrontational activities.
HAZARDOUS_ACTIONS = {"SABOTAGE_RIVAL", "SUPPORT_SECURITY"}


class ProgressionSystem:
    """Handles progression updates each tick based on player/agent actions."""

    # Mapping of action types to their primary skill domains
    ACTION_SKILL_MAP: Dict[str, SkillDomain] = {
        "INSPECT_DISTRICT": SkillDomain.INVESTIGATION,
        "NEGOTIATE_FACTION": SkillDomain.DIPLOMACY,
        "STABILIZE_UNREST": SkillDomain.INFLUENCE,
        "SUPPORT_SECURITY": SkillDomain.TACTICAL,
        "REQUEST_REPORT": SkillDomain.INVESTIGATION,
        "LOBBY_COUNCIL": SkillDomain.DIPLOMACY,
        "RECRUIT_SUPPORT": SkillDomain.INFLUENCE,
        "INVEST_DISTRICT": SkillDomain.ECONOMICS,
        "SABOTAGE_RIVAL": SkillDomain.TACTICAL,
    }

    def __init__(
        self,
        settings: Optional[ProgressionSettings] = None,
        per_agent_settings: Optional[PerAgentProgressionSettings] = None,
    ) -> None:
        self._settings = settings or ProgressionSettings()
        self._per_agent_settings = per_agent_settings or PerAgentProgressionSettings()
        self._events: List[ProgressionEvent] = []

    @property
    def settings(self) -> ProgressionSettings:
        return self._settings

    @property
    def per_agent_settings(self) -> PerAgentProgressionSettings:
        return self._per_agent_settings

    def tick(
        self,
        state: GameState,
        *,
        agent_actions: Optional[List[Dict[str, str]]] = None,
        faction_actions: Optional[List[Dict[str, object]]] = None,
    ) -> List[ProgressionEvent]:
        """Process progression updates for the current tick.

        Args:
            state: The current game state
            agent_actions: List of agent action reports from AgentSystem
            faction_actions: List of faction action reports from FactionSystem

        Returns:
            List of progression events that occurred
        """
        self._events = []
        progression = state.ensure_progression()
        tick = state.tick

        # Process agent actions for skill experience and per-agent progression
        if agent_actions:
            for action in agent_actions:
                self._process_agent_action(progression, action, tick)
                # Also process per-agent progression
                self._process_per_agent_action(state, action, tick)

        # Apply stress recovery per tick to all tracked agents
        self._apply_stress_recovery(state)

        # Process faction actions for reputation changes
        if faction_actions:
            for action in faction_actions:
                self._process_faction_action(progression, action, tick)

        # Record actions taken
        action_count = (len(agent_actions) if agent_actions else 0) + (
            len(faction_actions) if faction_actions else 0
        )
        for _ in range(action_count):
            progression.record_action()

        # Update metadata for telemetry
        if self._events:
            history = state.metadata.get("progression_history") or []
            for event in self._events:
                history.append(event.to_dict())
            # Keep last 50 events
            state.metadata["progression_history"] = history[-50:]

        return self._events

    def _process_agent_action(
        self,
        progression: ProgressionState,
        action: Dict[str, str],
        tick: int,
    ) -> None:
        """Grant skill experience for an agent action."""
        intent = action.get("intent", "")
        domain = self.ACTION_SKILL_MAP.get(intent)

        if domain is None:
            return

        # Calculate experience amount
        base_exp = self._settings.experience_per_action
        if "INSPECT" in intent:
            base_exp = self._settings.experience_per_inspection
        elif "NEGOTIATE" in intent:
            base_exp = self._settings.experience_per_negotiation

        multiplier = self._settings.get_domain_multiplier(domain)
        exp_amount = base_exp * multiplier * self._settings.base_experience_rate

        # Add experience
        old_tier = progression.access_tier
        levels_gained = progression.add_skill_experience(domain, exp_amount)

        # Record event if skill leveled up
        if levels_gained > 0:
            new_level = progression.get_skill_level(domain)
            self._events.append(
                ProgressionEvent(
                    tick=tick,
                    event_type="skill_gain",
                    domain=domain.value,
                    amount=exp_amount,
                    new_level=new_level,
                    detail=(
                        f"{domain.value.title()} skill increased to level "
                        f"{new_level}"
                    ),
                )
            )

        # Check for tier promotion
        if progression.access_tier != old_tier:
            self._events.append(
                ProgressionEvent(
                    tick=tick,
                    event_type="tier_unlock",
                    new_tier=progression.access_tier.value,
                    detail=f"Access tier promoted to {progression.access_tier.value}",
                )
            )

    def _process_faction_action(
        self,
        progression: ProgressionState,
        action: Dict[str, object],
        tick: int,
    ) -> None:
        """Update reputation based on faction actions."""
        faction_id = str(action.get("faction_id", ""))
        action_type = str(action.get("action", ""))

        if not faction_id:
            return

        # Determine reputation change based on action type
        delta = 0.0
        if action_type in ("LOBBY_COUNCIL", "RECRUIT_SUPPORT", "INVEST_DISTRICT"):
            # Positive actions improve reputation
            delta = self._settings.reputation_gain_rate
        elif action_type == "SABOTAGE_RIVAL":
            # Sabotage hurts reputation with both factions
            target_id = str(action.get("target", ""))
            if target_id:
                # Lose reputation with the target faction
                progression.modify_reputation(
                    target_id, -self._settings.reputation_loss_rate * 2
                )
                self._events.append(
                    ProgressionEvent(
                        tick=tick,
                        event_type="reputation_change",
                        faction_id=target_id,
                        amount=-self._settings.reputation_loss_rate * 2,
                        detail=f"Reputation with {target_id} decreased due to sabotage",
                    )
                )
            # Slight gain with the acting faction (they appreciate your help)
            delta = self._settings.reputation_gain_rate * 0.5

        if delta != 0.0:
            progression.modify_reputation(faction_id, delta)
            self._events.append(
                ProgressionEvent(
                    tick=tick,
                    event_type="reputation_change",
                    faction_id=faction_id,
                    amount=delta,
                    detail=f"Reputation with {faction_id} changed by {delta:+.2f}",
                )
            )

    def calculate_action_success_chance(
        self,
        progression: ProgressionState,
        action_type: str,
        faction_id: Optional[str] = None,
    ) -> float:
        """Calculate success chance for an action based on skills and reputation.

        Returns a value between 0.5 and 1.0 representing success probability.
        Base success is 0.75, modified by skill and reputation.
        """
        base_chance = 0.75
        domain = self.ACTION_SKILL_MAP.get(action_type)

        modifier = calculate_success_modifier(progression, domain, faction_id)
        # Modifier is 0.5 to 1.5, scale to affect base chance
        adjusted = base_chance * modifier

        # Clamp to valid probability range
        return max(0.5, min(1.0, adjusted))

    def get_accessible_districts(
        self,
        progression: ProgressionState,
        all_districts: List[str],
    ) -> List[str]:
        """Return list of districts accessible at the current access tier.

        For now, all districts are accessible at all tiers. This can be
        extended to gate districts by tier in future content updates.
        """
        # All districts accessible for now
        # Future: filter based on tier and district metadata
        return list(all_districts)

    def is_action_allowed(
        self,
        progression: ProgressionState,
        action_type: str,
    ) -> bool:
        """Check if an action is allowed at the current access tier.

        For now, all actions are allowed. This can be extended to gate
        certain actions by tier in future content updates.
        """
        # All actions allowed for now
        # Future: check action requirements against tier
        return True

    def summary(self, progression: ProgressionState) -> Dict[str, object]:
        """Generate a summary of progression state for display."""
        return progression.summary()

    def _process_per_agent_action(
        self,
        state: GameState,
        action: Dict[str, str],
        tick: int,
    ) -> None:
        """Update per-agent progression based on an agent action."""
        agent_id = action.get("agent_id", "")
        if not agent_id:
            return

        intent = action.get("intent", "")
        domain = self.ACTION_SKILL_MAP.get(intent)
        if domain is None:
            return

        # Get or create agent progression state
        agent_prog = state.ensure_agent_progression(agent_id)

        # Determine success/failure from action (default to success if not specified)
        success = action.get("success", "true").lower() in ("true", "1", "yes")

        settings = self._per_agent_settings

        if success:
            # On success: gain expertise, improve reliability
            old_expertise = agent_prog.get_expertise(domain)
            new_expertise = agent_prog.add_expertise(
                domain, settings.expertise_gain_per_success
            )
            agent_prog.modify_reliability(settings.reliability_gain_per_success)
            agent_prog.record_success()

            # Hazardous actions still add some stress even on success
            if intent in HAZARDOUS_ACTIONS:
                agent_prog.modify_stress(settings.stress_gain_per_hazardous)

            # Record event for significant expertise gain
            if new_expertise > old_expertise:
                self._events.append(
                    ProgressionEvent(
                        tick=tick,
                        event_type="agent_progression",
                        agent_id=agent_id,
                        domain=domain.value,
                        amount=float(new_expertise - old_expertise),
                        detail=f"Agent {agent_id} gained expertise in {domain.value}",
                    )
                )
        else:
            # On failure: reduce reliability, increase stress
            agent_prog.modify_reliability(-settings.reliability_loss_per_failure)
            agent_prog.modify_stress(settings.stress_gain_per_failure)
            agent_prog.record_failure()

            # Record burnout warning if stress is high
            if agent_prog.stress >= 0.75:
                self._events.append(
                    ProgressionEvent(
                        tick=tick,
                        event_type="agent_progression",
                        agent_id=agent_id,
                        amount=agent_prog.stress,
                        detail=f"Agent {agent_id} is {agent_prog.stress_label()}",
                    )
                )

    def _apply_stress_recovery(self, state: GameState) -> None:
        """Apply stress recovery to all tracked agents each tick."""
        settings = self._per_agent_settings
        if settings.stress_recovery_per_tick <= 0:
            return

        for agent_prog in state.agent_progression.values():
            if agent_prog.stress > 0:
                agent_prog.modify_stress(-settings.stress_recovery_per_tick)

    def calculate_action_success_chance_with_agent(
        self,
        state: GameState,
        action_type: str,
        agent_id: Optional[str] = None,
        faction_id: Optional[str] = None,
    ) -> float:
        """Calculate success chance including per-agent modifiers (if enabled).

        Returns a value between 0.5 and 1.0 representing success probability.
        """
        progression = state.ensure_progression()
        domain = self.ACTION_SKILL_MAP.get(action_type)

        # Get agent progression if we have an agent_id
        agent_prog = None
        if agent_id:
            agent_prog = state.get_agent_progression(agent_id)

        if self._per_agent_settings.enable_per_agent_modifiers and agent_prog:
            # Use the combined agent modifier
            modifier = calculate_agent_modifier(
                progression,
                agent_prog,
                domain,
                faction_id,
                max_expertise_bonus=self._per_agent_settings.max_expertise_bonus,
                max_stress_penalty=self._per_agent_settings.max_stress_penalty,
            )
        else:
            # Use global modifier only
            modifier = calculate_success_modifier(progression, domain, faction_id)

        base_chance = 0.75
        adjusted = base_chance * modifier
        return max(0.5, min(1.0, adjusted))

    def agent_roster_summary(self, state: GameState) -> List[Dict[str, object]]:
        """Return a list of agent progression summaries for display."""
        return [agent_prog.summary() for agent_prog in state.agent_progression.values()]
