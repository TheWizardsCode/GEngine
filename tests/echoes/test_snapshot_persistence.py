"""Additional coverage for snapshot persistence helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.core.models import (
    Agent,
    City,
    District,
    DistrictCoordinates,
    DistrictModifiers,
    EnvironmentState,
    Faction,
    ResourceStock,
    StorySeed,
    StorySeedResolutionTemplates,
    StorySeedTrigger,
)
from gengine.echoes.core.progression import (
    AccessTier,
    AgentProgressionState,
    AgentSpecialization,
    ProgressionState,
    ReputationState,
    SkillDomain,
    SkillState,
)
from gengine.echoes.core.state import GameState
from gengine.echoes.persistence.snapshot import (
    _json_default,
    load_snapshot,
    save_snapshot,
)


def test_json_default_rejects_unknown_type() -> None:
    with pytest.raises(TypeError):
        _json_default(object())


def test_load_snapshot_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "missing.json")


def test_load_snapshot_requires_mapping(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        load_snapshot(source)


def test_save_snapshot_creates_parent(tmp_path: Path) -> None:
    state = load_world_bundle()
    target = tmp_path / "nested" / "state.json"

    path = save_snapshot(state, target)

    assert path.exists()
    assert path.parent.name == "nested"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _create_minimal_city() -> City:
    """Create a minimal city with one district for testing."""
    return City(
        id="test-city",
        name="Test City",
        description="A test city",
        districts=[
            District(
                id="district-1",
                name="District One",
                population=10000,
                resources={
                    "energy": ResourceStock(
                        type="energy", capacity=100, current=50, regen=2.0
                    ),
                    "materials": ResourceStock(
                        type="materials", capacity=80, current=40, regen=1.5
                    ),
                },
                modifiers=DistrictModifiers(
                    pollution=0.3,
                    unrest=0.2,
                    prosperity=0.6,
                    security=0.5,
                ),
                coordinates=DistrictCoordinates(x=1.0, y=2.0, z=3.0),
                adjacent=["district-2"],
            ),
            District(
                id="district-2",
                name="District Two",
                population=20000,
                resources={
                    "food": ResourceStock(
                        type="food", capacity=60, current=30, regen=3.0
                    ),
                },
                modifiers=DistrictModifiers(
                    pollution=0.5,
                    unrest=0.4,
                    prosperity=0.4,
                    security=0.6,
                ),
                coordinates=DistrictCoordinates(x=5.0, y=6.0),
                adjacent=["district-1"],
            ),
        ],
    )


def _create_rich_game_state() -> GameState:
    """Create a GameState with all fields populated for comprehensive testing."""
    city = _create_minimal_city()

    factions = {
        "faction-alpha": Faction(
            id="faction-alpha",
            name="Alpha Faction",
            ideology="Progressive technology",
            legitimacy=0.75,
            resources={"capital": 100, "influence": 50},
            territory=["district-1"],
            description="A technological faction",
        ),
        "faction-beta": Faction(
            id="faction-beta",
            name="Beta Faction",
            ideology="Traditional values",
            legitimacy=0.55,
            resources={"labor": 80},
            territory=["district-2"],
            description="A traditional faction",
        ),
    }

    agents = {
        "agent-1": Agent(
            id="agent-1",
            name="Agent One",
            role="investigator",
            faction_id="faction-alpha",
            home_district="district-1",
            traits={"empathy": 0.8, "cunning": 0.3, "resolve": 0.6},
            needs={"safety": 0.5, "belonging": 0.7},
            goals=["investigate", "report"],
            notes="A key informant",
        ),
        "agent-2": Agent(
            id="agent-2",
            name="Agent Two",
            role="diplomat",
            faction_id="faction-beta",
            home_district="district-2",
            traits={"empathy": 0.6, "cunning": 0.5},
            needs={"power": 0.8},
            goals=["negotiate"],
        ),
    }

    story_seeds = {
        "seed-1": StorySeed(
            id="seed-1",
            title="Test Story",
            summary="A test story seed",
            stakes="High stakes test",
            scope="district",
            tags=["test", "drama"],
            preferred_districts=["district-1"],
            cooldown_ticks=20,
            triggers=[StorySeedTrigger(district_id="district-1", min_score=0.5)],
            beats=["beat1", "beat2"],
            resolution_templates=StorySeedResolutionTemplates(
                success="Success!",
                failure="Failure!",
                partial="Partial success",
            ),
            followups=[],
        ),
    }

    environment = EnvironmentState(
        stability=0.65,
        unrest=0.35,
        pollution=0.4,
        biodiversity=0.55,
        climate_risk=0.45,
        security=0.6,
    )

    # Create progression state with skills and reputation
    progression = ProgressionState(access_tier=AccessTier.ESTABLISHED)
    progression.skills[SkillDomain.DIPLOMACY.value] = SkillState(
        level=5, experience=25.0
    )
    progression.skills[SkillDomain.INVESTIGATION.value] = SkillState(
        level=3, experience=15.0
    )
    progression.reputation["faction-alpha"] = ReputationState(value=0.5)
    progression.reputation["faction-beta"] = ReputationState(value=-0.3)
    progression.total_experience = 150.0
    progression.actions_taken = 20

    # Create per-agent progression states
    agent_progression = {
        "agent-1": AgentProgressionState(
            agent_id="agent-1",
            specialization=AgentSpecialization.INVESTIGATOR,
            expertise={
                SkillDomain.INVESTIGATION.value: 3,
                SkillDomain.TACTICAL.value: 1,
            },
            reliability=0.75,
            stress=0.2,
            missions_completed=10,
            missions_failed=2,
        ),
        "agent-2": AgentProgressionState(
            agent_id="agent-2",
            specialization=AgentSpecialization.NEGOTIATOR,
            expertise={SkillDomain.DIPLOMACY.value: 4},
            reliability=0.6,
            stress=0.5,
            missions_completed=8,
            missions_failed=4,
        ),
    }

    created = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)

    return GameState(
        city=city,
        factions=factions,
        agents=agents,
        story_seeds=story_seeds,
        environment=environment,
        progression=progression,
        agent_progression=agent_progression,
        tick=42,
        seed=123456,
        version="1.0.0",
        created_at=created,
        metadata={
            "test_key": "test_value",
            "nested": {"inner": 42},
            "market_prices": {"energy": 1.5, "food": 2.0},
        },
    )


# ---------------------------------------------------------------------------
# Round-trip Tests: save → load → save
# ---------------------------------------------------------------------------


def test_round_trip_structural_equivalence(tmp_path: Path) -> None:
    """Save -> Load -> Save produces structurally equivalent state."""
    original = _create_rich_game_state()
    path1 = tmp_path / "snapshot1.json"
    path2 = tmp_path / "snapshot2.json"

    # First save
    save_snapshot(original, path1)
    # Load
    restored = load_snapshot(path1)
    # Second save
    save_snapshot(restored, path2)

    # Compare the two snapshot files semantically (model_dump equality)
    original_dump = original.model_dump()
    restored_dump = restored.model_dump()

    assert original_dump == restored_dump


def test_round_trip_double_cycle(tmp_path: Path) -> None:
    """Double round-trip: save → load → save → load → save produces same output."""
    original = _create_rich_game_state()

    path1 = tmp_path / "cycle1.json"
    path2 = tmp_path / "cycle2.json"
    path3 = tmp_path / "cycle3.json"

    save_snapshot(original, path1)
    state1 = load_snapshot(path1)
    save_snapshot(state1, path2)
    state2 = load_snapshot(path2)
    save_snapshot(state2, path3)

    # All three should be semantically identical
    assert state1.model_dump() == state2.model_dump()
    assert original.model_dump() == state2.model_dump()


# ---------------------------------------------------------------------------
# City and Districts Fidelity
# ---------------------------------------------------------------------------


def test_city_districts_fidelity(tmp_path: Path) -> None:
    """City and district data survives round-trip without loss."""
    original = _create_rich_game_state()
    path = tmp_path / "city_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    # City-level fields
    assert restored.city.id == original.city.id
    assert restored.city.name == original.city.name
    assert restored.city.description == original.city.description
    assert len(restored.city.districts) == len(original.city.districts)

    # District-level fields
    for orig_district, rest_district in zip(
        original.city.districts, restored.city.districts, strict=True
    ):
        assert rest_district.id == orig_district.id
        assert rest_district.name == orig_district.name
        assert rest_district.population == orig_district.population
        assert rest_district.adjacent == orig_district.adjacent

        # Resources
        assert (
            set(rest_district.resources.keys())
            == set(orig_district.resources.keys())
        )
        for res_key in orig_district.resources:
            orig_res = orig_district.resources[res_key]
            rest_res = rest_district.resources[res_key]
            assert rest_res.type == orig_res.type
            assert rest_res.capacity == orig_res.capacity
            assert rest_res.current == orig_res.current
            assert rest_res.regen == orig_res.regen

        # Modifiers
        assert rest_district.modifiers.pollution == orig_district.modifiers.pollution
        assert rest_district.modifiers.unrest == orig_district.modifiers.unrest
        assert rest_district.modifiers.prosperity == orig_district.modifiers.prosperity
        assert rest_district.modifiers.security == orig_district.modifiers.security

        # Coordinates (including None z-value case)
        if orig_district.coordinates is not None:
            assert rest_district.coordinates is not None
            assert rest_district.coordinates.x == orig_district.coordinates.x
            assert rest_district.coordinates.y == orig_district.coordinates.y
            assert rest_district.coordinates.z == orig_district.coordinates.z


# ---------------------------------------------------------------------------
# Factions Fidelity
# ---------------------------------------------------------------------------


def test_factions_fidelity(tmp_path: Path) -> None:
    """Faction data survives round-trip without loss."""
    original = _create_rich_game_state()
    path = tmp_path / "factions_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    assert set(restored.factions.keys()) == set(original.factions.keys())

    for faction_id in original.factions:
        orig_faction = original.factions[faction_id]
        rest_faction = restored.factions[faction_id]

        assert rest_faction.id == orig_faction.id
        assert rest_faction.name == orig_faction.name
        assert rest_faction.ideology == orig_faction.ideology
        assert rest_faction.legitimacy == orig_faction.legitimacy
        assert rest_faction.resources == orig_faction.resources
        assert rest_faction.territory == orig_faction.territory
        assert rest_faction.description == orig_faction.description


# ---------------------------------------------------------------------------
# Agents Fidelity
# ---------------------------------------------------------------------------


def test_agents_fidelity(tmp_path: Path) -> None:
    """Agent data survives round-trip without loss."""
    original = _create_rich_game_state()
    path = tmp_path / "agents_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    assert set(restored.agents.keys()) == set(original.agents.keys())

    for agent_id in original.agents:
        orig_agent = original.agents[agent_id]
        rest_agent = restored.agents[agent_id]

        assert rest_agent.id == orig_agent.id
        assert rest_agent.name == orig_agent.name
        assert rest_agent.role == orig_agent.role
        assert rest_agent.faction_id == orig_agent.faction_id
        assert rest_agent.home_district == orig_agent.home_district
        assert rest_agent.traits == orig_agent.traits
        assert rest_agent.needs == orig_agent.needs
        assert rest_agent.goals == orig_agent.goals
        assert rest_agent.notes == orig_agent.notes


# ---------------------------------------------------------------------------
# Environment State Fidelity
# ---------------------------------------------------------------------------


def test_environment_fidelity(tmp_path: Path) -> None:
    """Environment state survives round-trip without loss."""
    original = _create_rich_game_state()
    path = tmp_path / "environment_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    assert restored.environment.stability == original.environment.stability
    assert restored.environment.unrest == original.environment.unrest
    assert restored.environment.pollution == original.environment.pollution
    assert restored.environment.biodiversity == original.environment.biodiversity
    assert restored.environment.climate_risk == original.environment.climate_risk
    assert restored.environment.security == original.environment.security


# ---------------------------------------------------------------------------
# Progression State Fidelity
# ---------------------------------------------------------------------------


def test_progression_state_fidelity(tmp_path: Path) -> None:
    """Global progression state survives round-trip without loss."""
    original = _create_rich_game_state()
    path = tmp_path / "progression_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    assert restored.progression is not None
    orig_prog = original.progression
    rest_prog = restored.progression

    assert rest_prog.access_tier == orig_prog.access_tier
    assert rest_prog.total_experience == orig_prog.total_experience
    assert rest_prog.actions_taken == orig_prog.actions_taken

    # Skills
    assert set(rest_prog.skills.keys()) == set(orig_prog.skills.keys())
    for skill_key in orig_prog.skills:
        orig_skill = orig_prog.skills[skill_key]
        rest_skill = rest_prog.skills[skill_key]
        assert rest_skill.level == orig_skill.level
        assert rest_skill.experience == orig_skill.experience

    # Reputation
    assert set(rest_prog.reputation.keys()) == set(orig_prog.reputation.keys())
    for rep_key in orig_prog.reputation:
        assert (
            rest_prog.reputation[rep_key].value
            == orig_prog.reputation[rep_key].value
        )


def test_agent_progression_fidelity(tmp_path: Path) -> None:
    """Per-agent progression state survives round-trip without loss."""
    original = _create_rich_game_state()
    path = tmp_path / "agent_progression_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    assert (
        set(restored.agent_progression.keys())
        == set(original.agent_progression.keys())
    )

    for agent_id in original.agent_progression:
        orig_ap = original.agent_progression[agent_id]
        rest_ap = restored.agent_progression[agent_id]

        assert rest_ap.agent_id == orig_ap.agent_id
        assert rest_ap.specialization == orig_ap.specialization
        assert rest_ap.expertise == orig_ap.expertise
        assert rest_ap.reliability == orig_ap.reliability
        assert rest_ap.stress == orig_ap.stress
        assert rest_ap.missions_completed == orig_ap.missions_completed
        assert rest_ap.missions_failed == orig_ap.missions_failed


# ---------------------------------------------------------------------------
# Metadata Fidelity
# ---------------------------------------------------------------------------


def test_metadata_fidelity(tmp_path: Path) -> None:
    """Metadata fields survive round-trip, including tick, seed, version, timestamps."""
    original = _create_rich_game_state()
    path = tmp_path / "metadata_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    # Core metadata
    assert restored.tick == original.tick
    assert restored.seed == original.seed
    assert restored.version == original.version
    assert restored.created_at == original.created_at

    # Custom metadata dict
    assert restored.metadata == original.metadata
    assert restored.metadata["test_key"] == "test_value"
    assert restored.metadata["nested"]["inner"] == 42
    assert restored.metadata["market_prices"]["energy"] == 1.5


# ---------------------------------------------------------------------------
# Story Seeds Fidelity
# ---------------------------------------------------------------------------


def test_story_seeds_fidelity(tmp_path: Path) -> None:
    """Story seeds survive round-trip without loss."""
    original = _create_rich_game_state()
    path = tmp_path / "story_seeds_test.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    assert set(restored.story_seeds.keys()) == set(original.story_seeds.keys())

    for seed_id in original.story_seeds:
        orig_seed = original.story_seeds[seed_id]
        rest_seed = restored.story_seeds[seed_id]

        assert rest_seed.id == orig_seed.id
        assert rest_seed.title == orig_seed.title
        assert rest_seed.summary == orig_seed.summary
        assert rest_seed.stakes == orig_seed.stakes
        assert rest_seed.scope == orig_seed.scope
        assert rest_seed.tags == orig_seed.tags
        assert rest_seed.preferred_districts == orig_seed.preferred_districts
        assert rest_seed.cooldown_ticks == orig_seed.cooldown_ticks
        assert rest_seed.beats == orig_seed.beats
        assert rest_seed.followups == orig_seed.followups

        # Resolution templates
        assert (
            rest_seed.resolution_templates.success
            == orig_seed.resolution_templates.success
        )
        assert (
            rest_seed.resolution_templates.failure
            == orig_seed.resolution_templates.failure
        )
        assert (
            rest_seed.resolution_templates.partial
            == orig_seed.resolution_templates.partial
        )

        # Triggers
        assert len(rest_seed.triggers) == len(orig_seed.triggers)
        for orig_trig, rest_trig in zip(
            orig_seed.triggers, rest_seed.triggers, strict=True
        ):
            assert rest_trig.district_id == orig_trig.district_id
            assert rest_trig.min_score == orig_trig.min_score


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


def test_empty_collections_fidelity(tmp_path: Path) -> None:
    """Empty collections (no factions, agents, etc.) survive round-trip."""
    city = City(
        id="minimal",
        name="Minimal City",
        districts=[District(id="d1", name="D1", population=100)],
    )
    state = GameState(
        city=city,
        factions={},
        agents={},
        story_seeds={},
        agent_progression={},
    )
    path = tmp_path / "empty_collections.json"

    save_snapshot(state, path)
    restored = load_snapshot(path)

    assert restored.factions == {}
    assert restored.agents == {}
    assert restored.story_seeds == {}
    assert restored.agent_progression == {}
    assert restored.progression is None


def test_none_optional_fields_fidelity(tmp_path: Path) -> None:
    """None/null optional fields survive round-trip correctly."""
    city = City(
        id="test",
        name="Test City",
        districts=[
            District(
                id="d1",
                name="D1",
                population=100,
                coordinates=None,  # None coordinates
            ),
        ],
    )
    agent = Agent(
        id="a1",
        name="Agent",
        role="test",
        faction_id=None,  # None faction
        home_district=None,  # None home
        notes=None,  # None notes
    )
    state = GameState(
        city=city,
        agents={"a1": agent},
        progression=None,  # None progression
    )
    path = tmp_path / "none_fields.json"

    save_snapshot(state, path)
    restored = load_snapshot(path)

    assert restored.city.districts[0].coordinates is None
    assert restored.agents["a1"].faction_id is None
    assert restored.agents["a1"].home_district is None
    assert restored.agents["a1"].notes is None
    assert restored.progression is None


def test_world_bundle_round_trip(tmp_path: Path) -> None:
    """Loaded world bundle survives round-trip without data loss."""
    original = load_world_bundle()
    path = tmp_path / "world_bundle.json"

    save_snapshot(original, path)
    restored = load_snapshot(path)

    # Critical fields
    assert restored.city.id == original.city.id
    assert restored.city.name == original.city.name
    assert len(restored.city.districts) == len(original.city.districts)
    assert set(restored.factions.keys()) == set(original.factions.keys())
    assert set(restored.agents.keys()) == set(original.agents.keys())
    assert set(restored.story_seeds.keys()) == set(original.story_seeds.keys())
    assert restored.seed == original.seed

    # Full model equality
    assert restored.model_dump() == original.model_dump()


def test_modified_state_round_trip(tmp_path: Path) -> None:
    """State modified after loading survives subsequent round-trip."""
    original = load_world_bundle()

    # Modify state
    original.tick = 100
    original.environment.stability = 0.25
    original.metadata["custom_field"] = "custom_value"

    # Add progression
    original.progression = ProgressionState(access_tier=AccessTier.ELITE)
    original.progression.total_experience = 500.0

    path = tmp_path / "modified.json"
    save_snapshot(original, path)
    restored = load_snapshot(path)

    # Verify modifications persisted
    assert restored.tick == 100
    assert restored.environment.stability == 0.25
    assert restored.metadata["custom_field"] == "custom_value"
    assert restored.progression is not None
    assert restored.progression.access_tier == AccessTier.ELITE
    assert restored.progression.total_experience == 500.0


# ---------------------------------------------------------------------------
# Backwards Compatibility
# ---------------------------------------------------------------------------


def test_backwards_compat_missing_optional_fields(tmp_path: Path) -> None:
    """Snapshots from older versions without new optional fields can still be loaded.

    This simulates loading a snapshot that was created before certain optional
    fields were added (e.g., agent_progression, progression).
    """
    # Create a minimal snapshot without newer fields
    minimal_snapshot: Dict[str, Any] = {
        "city": {
            "id": "old-city",
            "name": "Old City",
            "districts": [
                {"id": "d1", "name": "D1", "population": 1000},
            ],
        },
        "factions": {},
        "agents": {},
        "story_seeds": {},
        "environment": {},
        "tick": 10,
        "seed": 42,
        "version": "0.0.1",
        # Note: no progression, no agent_progression, no created_at, no metadata
    }

    path = tmp_path / "old_snapshot.json"
    import json

    path.write_text(json.dumps(minimal_snapshot), encoding="utf-8")

    # Load should succeed with defaults for missing fields
    restored = load_snapshot(path)

    assert restored.city.id == "old-city"
    assert restored.tick == 10
    assert restored.seed == 42
    assert restored.version == "0.0.1"

    # New optional fields should have defaults
    assert restored.progression is None
    assert restored.agent_progression == {}
    assert restored.metadata == {}
    assert restored.created_at is not None  # Should have a default


def test_backwards_compat_extra_unknown_fields(tmp_path: Path) -> None:
    """Snapshots with unknown fields (future versions) can still be loaded.

    Pydantic models should ignore extra fields by default or handle gracefully.
    """
    future_snapshot: Dict[str, Any] = {
        "city": {
            "id": "future-city",
            "name": "Future City",
            "districts": [
                {"id": "d1", "name": "D1", "population": 1000},
            ],
            "future_field": "should be ignored",  # Unknown field
        },
        "factions": {},
        "agents": {},
        "story_seeds": {},
        "environment": {"future_metric": 0.5},  # Unknown field
        "tick": 50,
        "seed": 99,
        "version": "99.0.0",
        "future_top_level_field": True,  # Unknown field
    }

    path = tmp_path / "future_snapshot.json"
    import json

    path.write_text(json.dumps(future_snapshot), encoding="utf-8")

    # Load should succeed, ignoring unknown fields
    restored = load_snapshot(path)

    assert restored.city.id == "future-city"
    assert restored.tick == 50
    assert restored.version == "99.0.0"


def test_datetime_serialization_round_trip(tmp_path: Path) -> None:
    """Datetime fields serialize to ISO format and deserialize correctly."""
    original = _create_rich_game_state()
    path = tmp_path / "datetime_test.json"

    save_snapshot(original, path)

    # Check raw JSON contains ISO format
    content = path.read_text(encoding="utf-8")
    assert "2025-01-15T12:30:45" in content  # ISO format

    restored = load_snapshot(path)
    assert restored.created_at == original.created_at
    assert restored.created_at.tzinfo is not None  # Timezone preserved
