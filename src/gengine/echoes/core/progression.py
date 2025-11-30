"""Player progression models for Echoes of Emergence.

This module defines the player progression system including:
- Skill domains (diplomacy, investigation, economics, tactical, influence)
- Access tiers (novice, established, elite) that unlock districts/commands
- Reputation tracking per faction affecting AI responses and success rates
"""

from __future__ import annotations

from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field, field_validator


class SkillDomain(str, Enum):
    """Core skill domains that influence player actions."""

    DIPLOMACY = "diplomacy"  # Faction negotiations, dialogue success
    INVESTIGATION = "investigation"  # District inspections, information gathering
    ECONOMICS = "economics"  # Resource management, trade effectiveness
    TACTICAL = "tactical"  # Security operations, covert actions
    INFLUENCE = "influence"  # Story seed triggers, NPC reactions


class AccessTier(str, Enum):
    """Access tiers that unlock districts and commands."""

    NOVICE = "novice"  # Default, basic districts and commands
    ESTABLISHED = "established"  # Advanced districts, some restricted actions
    ELITE = "elite"  # Full access to all districts and commands


# Skill thresholds for tier progression
TIER_THRESHOLDS = {
    AccessTier.NOVICE: 0,
    AccessTier.ESTABLISHED: 50,
    AccessTier.ELITE: 100,
}


class SkillState(BaseModel):
    """State for a single skill domain."""

    level: int = Field(default=1, ge=1, le=100)
    experience: float = Field(default=0.0, ge=0.0)

    model_config = {"validate_assignment": True}

    def add_experience(self, amount: float, rate: float = 1.0) -> int:
        """Add experience and return any level ups gained."""
        if amount <= 0:
            return 0
        self.experience += amount * rate
        levels_gained = 0
        # Experience required per level increases linearly
        while self.level < 100:
            required = self.level * 10.0  # 10, 20, 30... per level
            if self.experience >= required:
                self.experience -= required
                self.level += 1
                levels_gained += 1
            else:
                break
        return levels_gained


class ReputationState(BaseModel):
    """Reputation with a single faction."""

    value: float = Field(default=0.0, ge=-1.0, le=1.0)

    model_config = {"validate_assignment": True}

    @field_validator("value")
    @classmethod
    def _clamp_value(cls, v: float) -> float:
        return max(-1.0, min(1.0, v))

    def modify(self, delta: float) -> None:
        """Modify reputation by delta, clamping to valid range."""
        self.value = max(-1.0, min(1.0, self.value + delta))

    def relationship(self) -> str:
        """Return human-readable relationship status."""
        if self.value >= 0.75:
            return "allied"
        elif self.value >= 0.25:
            return "friendly"
        elif self.value >= -0.25:
            return "neutral"
        elif self.value >= -0.75:
            return "unfriendly"
        else:
            return "hostile"


class ProgressionState(BaseModel):
    """Complete player progression state."""

    skills: Dict[str, SkillState] = Field(default_factory=dict)
    reputation: Dict[str, ReputationState] = Field(default_factory=dict)
    access_tier: AccessTier = Field(default=AccessTier.NOVICE)
    total_experience: float = Field(default=0.0, ge=0.0)
    actions_taken: int = Field(default=0, ge=0)

    model_config = {"validate_assignment": True}

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure all skill domains are initialized
        for domain in SkillDomain:
            if domain.value not in self.skills:
                self.skills[domain.value] = SkillState()

    def get_skill_level(self, domain: SkillDomain | str) -> int:
        """Get the level for a skill domain."""
        key = domain.value if isinstance(domain, SkillDomain) else domain
        if key not in self.skills:
            return 1
        return self.skills[key].level

    def get_skill_modifier(self, domain: SkillDomain | str) -> float:
        """Get a modifier (0.0 to 1.0) based on skill level."""
        level = self.get_skill_level(domain)
        # Linear scaling: level 1 = 0.0, level 100 = 1.0
        return (level - 1) / 99.0

    def add_skill_experience(
        self, domain: SkillDomain | str, amount: float, rate: float = 1.0
    ) -> int:
        """Add experience to a skill and return levels gained."""
        key = domain.value if isinstance(domain, SkillDomain) else domain
        if key not in self.skills:
            self.skills[key] = SkillState()
        levels_gained = self.skills[key].add_experience(amount, rate)
        self.total_experience += amount * rate
        self._check_tier_promotion()
        return levels_gained

    def get_reputation(self, faction_id: str) -> float:
        """Get reputation value for a faction (-1.0 to 1.0)."""
        if faction_id not in self.reputation:
            return 0.0
        return self.reputation[faction_id].value

    def get_reputation_modifier(self, faction_id: str) -> float:
        """Get reputation modifier (0.0 to 1.0) for success rate calculations."""
        rep = self.get_reputation(faction_id)
        # Transform from [-1, 1] to [0, 1] range
        return (rep + 1.0) / 2.0

    def modify_reputation(self, faction_id: str, delta: float) -> None:
        """Modify reputation with a faction."""
        if faction_id not in self.reputation:
            self.reputation[faction_id] = ReputationState()
        self.reputation[faction_id].modify(delta)

    def get_relationship(self, faction_id: str) -> str:
        """Get human-readable relationship status with a faction."""
        if faction_id not in self.reputation:
            return "neutral"
        return self.reputation[faction_id].relationship()

    def record_action(self) -> None:
        """Record that an action was taken."""
        self.actions_taken += 1

    def _check_tier_promotion(self) -> None:
        """Check if player qualifies for tier promotion."""
        avg_level = self.average_skill_level()
        if avg_level >= TIER_THRESHOLDS[AccessTier.ELITE]:
            self.access_tier = AccessTier.ELITE
        elif avg_level >= TIER_THRESHOLDS[AccessTier.ESTABLISHED]:
            self.access_tier = AccessTier.ESTABLISHED

    def average_skill_level(self) -> float:
        """Calculate average skill level across all domains."""
        if not self.skills:
            return 1.0
        total = sum(skill.level for skill in self.skills.values())
        return total / len(self.skills)

    def can_access_tier(self, tier: AccessTier) -> bool:
        """Check if player has access to a given tier."""
        tier_order = [AccessTier.NOVICE, AccessTier.ESTABLISHED, AccessTier.ELITE]
        player_idx = tier_order.index(self.access_tier)
        required_idx = tier_order.index(tier)
        return player_idx >= required_idx

    def summary(self) -> Dict[str, object]:
        """Return a summary of progression state for display."""
        return {
            "access_tier": self.access_tier.value,
            "average_level": round(self.average_skill_level(), 1),
            "total_experience": round(self.total_experience, 1),
            "actions_taken": self.actions_taken,
            "skills": {
                domain: {
                    "level": self.skills[domain].level,
                    "experience": round(self.skills[domain].experience, 1),
                }
                for domain in self.skills
            },
            "reputation": {
                faction_id: {
                    "value": round(state.value, 2),
                    "relationship": state.relationship(),
                }
                for faction_id, state in self.reputation.items()
            },
        }


def calculate_success_modifier(
    progression: ProgressionState,
    skill_domain: SkillDomain | str | None = None,
    faction_id: str | None = None,
) -> float:
    """Calculate a combined success modifier based on skill and reputation.

    Returns a value between 0.5 and 1.5:
    - 0.5: Minimum modifier (no skill, hostile reputation)
    - 1.0: Neutral modifier (average skill, neutral reputation)
    - 1.5: Maximum modifier (max skill, allied reputation)
    """
    base = 1.0

    # Skill contribution: -0.25 to +0.25
    if skill_domain is not None:
        skill_mod = progression.get_skill_modifier(skill_domain)
        base += (skill_mod - 0.5) * 0.5  # -0.25 to +0.25

    # Reputation contribution: -0.25 to +0.25
    if faction_id is not None:
        rep_mod = progression.get_reputation_modifier(faction_id)
        base += (rep_mod - 0.5) * 0.5  # -0.25 to +0.25

    return max(0.5, min(1.5, base))
