"""Tests for the progression system (M7.1)."""

from __future__ import annotations

import random
from typing import Dict, List

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.core import GameState
from gengine.echoes.core.progression import (
    AccessTier,
    ProgressionState,
    ReputationState,
    SkillDomain,
    SkillState,
    calculate_success_modifier,
)
from gengine.echoes.sim import SimEngine
from gengine.echoes.systems.progression import (
    ProgressionEvent,
    ProgressionSettings,
    ProgressionSystem,
)


class TestSkillState:
    """Tests for SkillState model."""

    def test_default_values(self) -> None:
        skill = SkillState()
        assert skill.level == 1
        assert skill.experience == 0.0

    def test_add_experience_no_levelup(self) -> None:
        skill = SkillState(level=1)
        levels = skill.add_experience(5.0)  # Need 10 for level 2
        assert levels == 0
        assert skill.level == 1
        assert skill.experience == 5.0

    def test_add_experience_levelup(self) -> None:
        skill = SkillState(level=1)
        levels = skill.add_experience(15.0)  # 10 needed for level 2
        assert levels == 1
        assert skill.level == 2
        assert skill.experience == 5.0  # 15 - 10 = 5 leftover

    def test_add_experience_multiple_levels(self) -> None:
        skill = SkillState(level=1)
        levels = skill.add_experience(35.0)  # 10 + 20 = 30 for levels 2 and 3
        assert levels == 2
        assert skill.level == 3
        assert skill.experience == 5.0

    def test_add_experience_respects_cap(self) -> None:
        skill = SkillState(level=99)
        levels = skill.add_experience(1000.0)  # Need 990 for level 100
        assert levels == 1  # Only one level up to 100
        assert skill.level == 100

    def test_add_experience_with_rate(self) -> None:
        skill = SkillState(level=1)
        levels = skill.add_experience(10.0, rate=0.5)  # Only 5 effective exp
        assert levels == 0
        assert skill.experience == 5.0

    def test_add_experience_negative_amount(self) -> None:
        skill = SkillState(level=1, experience=5.0)
        levels = skill.add_experience(-5.0)
        assert levels == 0
        assert skill.experience == 5.0  # Unchanged


class TestReputationState:
    """Tests for ReputationState model."""

    def test_default_neutral(self) -> None:
        rep = ReputationState()
        assert rep.value == 0.0
        assert rep.relationship() == "neutral"

    def test_modify_positive(self) -> None:
        rep = ReputationState()
        rep.modify(0.3)
        assert rep.value == 0.3
        assert rep.relationship() == "friendly"

    def test_modify_negative(self) -> None:
        rep = ReputationState()
        rep.modify(-0.5)
        assert rep.value == -0.5
        assert rep.relationship() == "unfriendly"

    def test_modify_clamps_high(self) -> None:
        rep = ReputationState(value=0.8)
        rep.modify(0.5)
        assert rep.value == 1.0

    def test_modify_clamps_low(self) -> None:
        rep = ReputationState(value=-0.8)
        rep.modify(-0.5)
        assert rep.value == -1.0

    def test_relationships(self) -> None:
        assert ReputationState(value=1.0).relationship() == "allied"
        assert ReputationState(value=0.8).relationship() == "allied"
        assert ReputationState(value=0.5).relationship() == "friendly"
        assert ReputationState(value=0.0).relationship() == "neutral"
        assert ReputationState(value=-0.5).relationship() == "unfriendly"
        assert ReputationState(value=-1.0).relationship() == "hostile"


class TestProgressionState:
    """Tests for ProgressionState model."""

    def test_default_initializes_all_skills(self) -> None:
        prog = ProgressionState()
        assert len(prog.skills) == 5
        for domain in SkillDomain:
            assert domain.value in prog.skills
            assert prog.skills[domain.value].level == 1

    def test_get_skill_level(self) -> None:
        prog = ProgressionState()
        prog.skills[SkillDomain.DIPLOMACY.value].level = 10
        assert prog.get_skill_level(SkillDomain.DIPLOMACY) == 10
        assert prog.get_skill_level("diplomacy") == 10

    def test_get_skill_modifier(self) -> None:
        prog = ProgressionState()
        assert prog.get_skill_modifier(SkillDomain.DIPLOMACY) == 0.0  # Level 1
        prog.skills[SkillDomain.DIPLOMACY.value].level = 100
        assert prog.get_skill_modifier(SkillDomain.DIPLOMACY) == 1.0  # Level 100

    def test_add_skill_experience(self) -> None:
        prog = ProgressionState()
        levels = prog.add_skill_experience(SkillDomain.INVESTIGATION, 15.0)
        assert levels == 1
        assert prog.skills[SkillDomain.INVESTIGATION.value].level == 2
        assert prog.total_experience == 15.0

    def test_reputation_operations(self) -> None:
        prog = ProgressionState()
        assert prog.get_reputation("faction-1") == 0.0
        prog.modify_reputation("faction-1", 0.3)
        assert prog.get_reputation("faction-1") == 0.3
        assert prog.get_relationship("faction-1") == "friendly"

    def test_reputation_modifier(self) -> None:
        prog = ProgressionState()
        # Neutral (0.0) -> 0.5 modifier
        assert prog.get_reputation_modifier("faction-1") == 0.5
        prog.modify_reputation("faction-1", 1.0)
        # Allied (1.0) -> 1.0 modifier
        assert prog.get_reputation_modifier("faction-1") == 1.0
        prog.modify_reputation("faction-1", -2.0)  # Clamps to -1.0
        # Hostile (-1.0) -> 0.0 modifier
        assert prog.get_reputation_modifier("faction-1") == 0.0

    def test_tier_promotion(self) -> None:
        prog = ProgressionState()
        assert prog.access_tier == AccessTier.NOVICE

        # Raise all skills to level 50 average
        for domain in prog.skills.values():
            domain.level = 50
        prog._check_tier_promotion()
        assert prog.access_tier == AccessTier.ESTABLISHED

        # Raise all skills to level 100 average
        for domain in prog.skills.values():
            domain.level = 100
        prog._check_tier_promotion()
        assert prog.access_tier == AccessTier.ELITE

    def test_can_access_tier(self) -> None:
        prog = ProgressionState()
        assert prog.can_access_tier(AccessTier.NOVICE)
        assert not prog.can_access_tier(AccessTier.ESTABLISHED)
        assert not prog.can_access_tier(AccessTier.ELITE)

        prog.access_tier = AccessTier.ESTABLISHED
        assert prog.can_access_tier(AccessTier.NOVICE)
        assert prog.can_access_tier(AccessTier.ESTABLISHED)
        assert not prog.can_access_tier(AccessTier.ELITE)

    def test_average_skill_level(self) -> None:
        prog = ProgressionState()
        assert prog.average_skill_level() == 1.0

        prog.skills[SkillDomain.DIPLOMACY.value].level = 11
        # Average = (1+1+1+1+11)/5 = 3.0
        assert prog.average_skill_level() == 3.0

    def test_summary(self) -> None:
        prog = ProgressionState()
        prog.modify_reputation("union-of-flux", 0.5)
        summary = prog.summary()

        assert summary["access_tier"] == "novice"
        assert summary["average_level"] == 1.0
        assert summary["actions_taken"] == 0
        assert "diplomacy" in summary["skills"]
        assert "union-of-flux" in summary["reputation"]
        assert summary["reputation"]["union-of-flux"]["relationship"] == "friendly"


class TestCalculateSuccessModifier:
    """Tests for the success modifier calculation."""

    def test_no_modifiers(self) -> None:
        prog = ProgressionState()
        mod = calculate_success_modifier(prog)
        assert mod == 1.0

    def test_skill_only(self) -> None:
        prog = ProgressionState()
        prog.skills[SkillDomain.DIPLOMACY.value].level = 100  # Max skill
        mod = calculate_success_modifier(prog, skill_domain=SkillDomain.DIPLOMACY)
        assert mod == 1.25  # Base 1.0 + 0.25 from max skill

    def test_reputation_only(self) -> None:
        prog = ProgressionState()
        prog.modify_reputation("faction-1", 1.0)  # Allied
        mod = calculate_success_modifier(prog, faction_id="faction-1")
        assert mod == 1.25  # Base 1.0 + 0.25 from allied

    def test_both_modifiers(self) -> None:
        prog = ProgressionState()
        prog.skills[SkillDomain.DIPLOMACY.value].level = 100
        prog.modify_reputation("faction-1", 1.0)
        mod = calculate_success_modifier(
            prog, skill_domain=SkillDomain.DIPLOMACY, faction_id="faction-1"
        )
        assert mod == 1.5  # Base 1.0 + 0.25 + 0.25

    def test_negative_modifiers(self) -> None:
        prog = ProgressionState()
        prog.modify_reputation("faction-1", -1.0)  # Hostile
        mod = calculate_success_modifier(prog, faction_id="faction-1")
        assert mod == 0.75  # Base 1.0 - 0.25 from hostile


class TestProgressionSystem:
    """Tests for ProgressionSystem."""

    def test_default_settings(self) -> None:
        system = ProgressionSystem()
        assert system.settings.base_experience_rate == 1.0
        assert system.settings.experience_per_action == 10.0

    def test_custom_settings(self) -> None:
        settings = ProgressionSettings(base_experience_rate=2.0)
        system = ProgressionSystem(settings=settings)
        assert system.settings.base_experience_rate == 2.0

    def test_tick_with_agent_actions(self) -> None:
        state = load_world_bundle()
        system = ProgressionSystem()

        agent_actions = [
            {"intent": "INSPECT_DISTRICT", "agent_id": "agent-1"},
            {"intent": "NEGOTIATE_FACTION", "agent_id": "agent-2"},
        ]

        events = system.tick(state, agent_actions=agent_actions)

        # Progression should be initialized
        assert state.progression is not None
        assert state.progression.actions_taken == 2

    def test_tick_with_faction_actions(self) -> None:
        state = load_world_bundle()
        system = ProgressionSystem()

        faction_actions = [
            {"faction_id": "union-of-flux", "action": "LOBBY_COUNCIL"},
            {"faction_id": "cartel-of-mist", "action": "INVEST_DISTRICT"},
        ]

        events = system.tick(state, faction_actions=faction_actions)

        assert state.progression is not None
        # Should have reputation changes
        assert "union-of-flux" in state.progression.reputation
        assert "cartel-of-mist" in state.progression.reputation

    def test_tick_records_history(self) -> None:
        state = load_world_bundle()
        system = ProgressionSystem()

        # Grant enough experience to level up
        state.ensure_progression().skills[SkillDomain.INVESTIGATION.value].experience = 9.0

        agent_actions = [
            {"intent": "INSPECT_DISTRICT", "agent_id": "agent-1"},
        ]

        events = system.tick(state, agent_actions=agent_actions)

        # Should have recorded the level up event
        history = state.metadata.get("progression_history", [])
        assert any(e.get("event_type") == "skill_gain" for e in history)

    def test_calculate_action_success_chance(self) -> None:
        state = load_world_bundle()
        system = ProgressionSystem()
        progression = state.ensure_progression()

        # Default chance should be around 0.75
        chance = system.calculate_action_success_chance(
            progression, "INSPECT_DISTRICT"
        )
        assert 0.5 <= chance <= 1.0

    def test_sabotage_affects_both_factions(self) -> None:
        state = load_world_bundle()
        system = ProgressionSystem()
        
        faction_actions = [
            {
                "faction_id": "cartel-of-mist",
                "action": "SABOTAGE_RIVAL",
                "target": "union-of-flux",
            },
        ]

        events = system.tick(state, faction_actions=faction_actions)

        # Both factions should have reputation changes
        assert "union-of-flux" in state.progression.reputation
        assert "cartel-of-mist" in state.progression.reputation
        # Sabotage target should have negative reputation
        assert state.progression.get_reputation("union-of-flux") < 0


class TestGameStateProgression:
    """Tests for progression integration with GameState."""

    def test_ensure_progression(self) -> None:
        state = load_world_bundle()
        assert state.progression is None

        prog = state.ensure_progression()
        assert prog is not None
        assert state.progression is prog

        # Second call returns same instance
        prog2 = state.ensure_progression()
        assert prog is prog2

    def test_summary_includes_progression(self) -> None:
        state = load_world_bundle()
        state.ensure_progression()
        state.progression.modify_reputation("union-of-flux", 0.3)

        summary = state.summary()
        assert "progression" in summary
        assert summary["progression"]["access_tier"] == "novice"

    def test_snapshot_includes_progression(self) -> None:
        state = load_world_bundle()
        state.ensure_progression()
        state.progression.skills[SkillDomain.DIPLOMACY.value].level = 25

        snapshot = state.snapshot()
        assert "progression" in snapshot
        assert snapshot["progression"]["skills"]["diplomacy"]["level"] == 25

    def test_from_snapshot_restores_progression(self) -> None:
        state = load_world_bundle()
        state.ensure_progression()
        state.progression.modify_reputation("union-of-flux", 0.5)
        state.progression.skills[SkillDomain.TACTICAL.value].level = 30

        snapshot = state.snapshot()
        restored = GameState.from_snapshot(snapshot)

        assert restored.progression is not None
        assert restored.progression.get_reputation("union-of-flux") == 0.5
        assert restored.progression.get_skill_level(SkillDomain.TACTICAL) == 30


class TestSimEngineProgression:
    """Tests for progression integration with SimEngine."""

    def test_engine_creates_progression_system(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        assert engine._progression_system is not None

    def test_engine_updates_progression_on_tick(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        reports = engine.advance_ticks(5)

        # Progression should be updated after ticks
        assert engine.state.progression is not None
        assert engine.state.progression.actions_taken > 0

    def test_progression_summary_api(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(1)

        summary = engine.progression_summary()
        assert "access_tier" in summary
        assert "skills" in summary
        assert "reputation" in summary

    def test_calculate_success_chance_api(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        chance = engine.calculate_success_chance("INSPECT_DISTRICT")
        assert 0.5 <= chance <= 1.0


class TestProgressionScenarios:
    """Scenario tests for progression over time."""

    def test_skill_progression_over_ticks(self) -> None:
        """Test that skills improve over multiple ticks."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        initial_total_exp = 0.0

        # Run for 20 ticks
        engine.advance_ticks(20)

        prog = engine.state.progression
        assert prog is not None
        assert prog.total_experience > initial_total_exp
        assert prog.actions_taken > 0

    def test_reputation_changes_with_faction_actions(self) -> None:
        """Test that reputation changes as factions take actions."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        # Run for 10 ticks - factions should take actions
        engine.advance_ticks(10)

        prog = engine.state.progression
        assert prog is not None
        # Some factions should have reputation changes
        assert len(prog.reputation) > 0

    def test_progression_persists_across_snapshots(self) -> None:
        """Test that progression survives save/load cycles."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.advance_ticks(5)

        # Save snapshot
        snapshot = engine.state.snapshot()
        original_exp = engine.state.progression.total_experience

        # Restore to new state
        new_engine = SimEngine()
        new_engine.initialize_state(state=GameState.from_snapshot(snapshot))

        assert new_engine.state.progression is not None
        assert new_engine.state.progression.total_experience == original_exp


class TestProgressionSettings:
    """Tests for ProgressionSettings dataclass."""

    def test_default_values(self) -> None:
        settings = ProgressionSettings()
        assert settings.base_experience_rate == 1.0
        assert settings.skill_cap == 100
        assert settings.established_threshold == 50
        assert settings.elite_threshold == 100

    def test_domain_multipliers(self) -> None:
        settings = ProgressionSettings(diplomacy_multiplier=1.5)
        assert settings.get_domain_multiplier(SkillDomain.DIPLOMACY) == 1.5
        assert settings.get_domain_multiplier(SkillDomain.INVESTIGATION) == 1.0
        assert settings.get_domain_multiplier("unknown") == 1.0
