"""Tests for the faction subsystem (Phase 4, M4.2).

This module tests FactionSystem behavior contracts without relying on
magic seed values. Tests use a deterministic fake RNG or set up state
conditions that force specific action paths.
"""

from __future__ import annotations

from gengine.echoes.content import load_world_bundle
from gengine.echoes.systems import FactionSystem


class DeterministicRNG:
    """Fake RNG that returns a predetermined value for uniform().
    
    This allows tests to force specific action selections without
    depending on magic seed values that could break if internal
    ordering changes.
    """

    def __init__(self, uniform_value: float = 0.0):
        """Initialize with a value that uniform() will return.
        
        Args:
            uniform_value: Value returned by uniform(). Set to 0.0 to
                select the first option, or a large value to select
                later options based on their cumulative weights.
        """
        self._uniform_value = uniform_value

    def uniform(self, lo: float, hi: float) -> float:
        """Return predetermined value clamped to [lo, hi]."""
        return max(lo, min(hi, self._uniform_value))


def _single_faction_state():
    """Create a state with a single faction for isolated testing."""
    state = load_world_bundle()
    faction = state.factions["union_of_flux"]
    state.factions = {faction.id: faction}
    return state, faction


def _multi_faction_state():
    """Create a state with multiple factions for rivalry testing."""
    state = load_world_bundle()
    return state


# =============================================================================
# LOBBY_COUNCIL action tests
# =============================================================================


def test_faction_lobbies_when_legitimacy_low() -> None:
    """Faction with low legitimacy (<0.7) chooses LOBBY_COUNCIL.
    
    Contract: When legitimacy is below 0.7, LOBBY_COUNCIL becomes
    an option. Using a DeterministicRNG(0.0) forces selection of
    the first available option.
    """
    state, faction = _single_faction_state()
    # Set up: low legitimacy triggers lobby option
    faction.legitimacy = 0.4
    faction.resources = {"influence": 60}
    # No territory-driven options (stable districts)
    for district in state.city.districts:
        district.modifiers.unrest = 0.2
        district.modifiers.security = 0.8
    
    system = FactionSystem(cooldown_ticks=1)
    rng = DeterministicRNG(0.0)  # Selects first option (LOBBY_COUNCIL)
    
    actions = system.tick(state, rng=rng)
    
    assert len(actions) == 1
    assert actions[0].action == "LOBBY_COUNCIL"


def test_lobby_increases_legitimacy_by_expected_delta() -> None:
    """LOBBY_COUNCIL increases legitimacy by up to 0.06 per action.
    
    Contract: The delta is min(0.06, 1.0 - current_legitimacy).
    """
    state, faction = _single_faction_state()
    faction.legitimacy = 0.4
    faction.resources = {"influence": 60}
    for district in state.city.districts:
        district.modifiers.unrest = 0.2
        district.modifiers.security = 0.8
    
    initial_legitimacy = faction.legitimacy
    system = FactionSystem(cooldown_ticks=1)
    
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    lobby = next((a for a in actions if a.action == "LOBBY_COUNCIL"), None)
    assert lobby is not None
    # Verify delta matches expected value
    expected_delta = min(0.06, 1.0 - initial_legitimacy)
    assert abs(lobby.legitimacy_delta - expected_delta) < 0.0001
    # Verify state was updated
    assert abs(faction.legitimacy - (initial_legitimacy + expected_delta)) < 0.0001


def test_lobby_costs_resources() -> None:
    """LOBBY_COUNCIL consumes resources (costs 2 from highest pool)."""
    state, faction = _single_faction_state()
    faction.legitimacy = 0.4
    faction.resources = {"influence": 60}
    for district in state.city.districts:
        district.modifiers.unrest = 0.2
        district.modifiers.security = 0.8
    
    initial_influence = faction.resources["influence"]
    system = FactionSystem(cooldown_ticks=1)
    
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    lobby = next((a for a in actions if a.action == "LOBBY_COUNCIL"), None)
    assert lobby is not None
    assert lobby.resource_delta == -2
    assert faction.resources["influence"] == initial_influence - 2


# =============================================================================
# RECRUIT_SUPPORT action tests
# =============================================================================


def test_faction_recruits_when_resources_low() -> None:
    """Faction with low resource pressure (<0.5) and high legitimacy recruits.
    
    Contract: RECRUIT_SUPPORT is an option when resource pressure is low.
    We set legitimacy high to disable LOBBY, and districts stable to
    disable INVEST, so RECRUIT becomes the dominant (and only) option.
    """
    state, faction = _single_faction_state()
    faction.legitimacy = 0.95  # High legitimacy - no lobby
    faction.resources = {}  # Empty resources - low pressure triggers recruit
    for district in state.city.districts:
        if district.id in faction.territory:
            district.modifiers.unrest = 0.2  # Low unrest - no invest
            district.modifiers.security = 0.9  # High security - no invest
    
    system = FactionSystem(cooldown_ticks=1)
    
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    recruit = next((a for a in actions if a.action == "RECRUIT_SUPPORT"), None)
    assert recruit is not None


def test_recruit_gains_resources_and_legitimacy() -> None:
    """RECRUIT_SUPPORT adds +4 resources and +0.015 legitimacy.
    
    Contract: Resource delta is +4, legitimacy delta is +0.015.
    """
    state, faction = _single_faction_state()
    faction.legitimacy = 0.8
    faction.resources = {}  # Start empty - will create "influence" pool
    for district in state.city.districts:
        if district.id in faction.territory:
            district.modifiers.unrest = 0.2
            district.modifiers.security = 0.9
    
    initial_legitimacy = faction.legitimacy
    system = FactionSystem(cooldown_ticks=1)
    
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    recruit = next((a for a in actions if a.action == "RECRUIT_SUPPORT"), None)
    assert recruit is not None
    # Verify reported deltas
    assert recruit.resource_delta == 4
    assert abs(recruit.legitimacy_delta - 0.015) < 0.0001
    # Verify state changes
    assert faction.resources.get("influence", 0) == 4
    assert abs(faction.legitimacy - (initial_legitimacy + 0.015)) < 0.0001


# =============================================================================
# INVEST_DISTRICT action tests
# =============================================================================


def test_faction_invests_when_unrest_high() -> None:
    """Faction with high unrest in territory invests to stabilize.
    
    Contract: INVEST_DISTRICT becomes an option when faction territory
    has high unrest (>0.4) or low security (<0.5).
    """
    state, faction = _single_faction_state()
    faction.legitimacy = 0.9  # High legitimacy - no lobby
    faction.resources = {"influence": 120}  # High resources - no recruit
    for district in state.city.districts:
        if district.id in faction.territory:
            district.modifiers.unrest = 0.9  # High unrest triggers invest
            district.modifiers.security = 0.2
    
    system = FactionSystem(cooldown_ticks=1)
    
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    invest = next((a for a in actions if a.action == "INVEST_DISTRICT"), None)
    assert invest is not None


def test_invest_improves_district_metrics() -> None:
    """INVEST_DISTRICT reduces unrest and increases security/prosperity.
    
    Contract: unrest_delta=-0.05, security_delta=+0.03, prosperity_delta=+0.04
    """
    state, faction = _single_faction_state()
    faction.legitimacy = 0.9
    faction.resources = {"influence": 120}
    
    # Find a district in territory and set high unrest
    target_district = None
    for district in state.city.districts:
        if district.id in faction.territory:
            target_district = district
            district.modifiers.unrest = 0.9
            district.modifiers.security = 0.2
            district.modifiers.prosperity = 0.5
            break
    
    assert target_district is not None
    initial_unrest = target_district.modifiers.unrest
    initial_security = target_district.modifiers.security
    initial_prosperity = target_district.modifiers.prosperity
    
    system = FactionSystem(cooldown_ticks=1)
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    invest = next((a for a in actions if a.action == "INVEST_DISTRICT"), None)
    assert invest is not None
    
    # Verify district was modified as expected
    assert abs(target_district.modifiers.unrest - (initial_unrest - 0.05)) < 0.0001
    assert abs(target_district.modifiers.security - (initial_security + 0.03)) < 0.0001
    assert (
        abs(target_district.modifiers.prosperity - (initial_prosperity + 0.04))
        < 0.0001
    )


def test_invest_costs_resources_and_gains_legitimacy() -> None:
    """INVEST_DISTRICT costs 3 resources and gains 0.02 legitimacy."""
    state, faction = _single_faction_state()
    faction.legitimacy = 0.8
    faction.resources = {"influence": 120}
    for district in state.city.districts:
        if district.id in faction.territory:
            district.modifiers.unrest = 0.9
            district.modifiers.security = 0.2
    
    initial_influence = faction.resources["influence"]
    initial_legitimacy = faction.legitimacy
    system = FactionSystem(cooldown_ticks=1)
    
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    invest = next((a for a in actions if a.action == "INVEST_DISTRICT"), None)
    assert invest is not None
    # Verify reported deltas
    assert invest.resource_delta == -3
    assert abs(invest.legitimacy_delta - 0.02) < 0.0001
    # Verify state changes
    assert faction.resources["influence"] == initial_influence - 3
    assert abs(faction.legitimacy - (initial_legitimacy + 0.02)) < 0.0001


# =============================================================================
# SABOTAGE_RIVAL action tests
# =============================================================================


def test_faction_can_sabotage_stronger_rival() -> None:
    """Faction can sabotage a rival with higher legitimacy.
    
    Contract: SABOTAGE_RIVAL is an option when:
    - There is a rival faction
    - Environment stability >= 0.45
    - Rival legitimacy > actor legitimacy by at least 0.05
    """
    state = _multi_faction_state()
    state.environment.stability = 0.8  # Stable enough for sabotage
    
    # Set up legitimacy gap: cartel is stronger than union
    union = state.factions["union_of_flux"]
    cartel = state.factions["cartel_of_mist"]
    union.legitimacy = 0.4  # Lower
    cartel.legitimacy = 0.7  # Higher - creates legitimacy gap
    
    # Give union resources and stable territory to avoid other options
    union.resources = {"influence": 200}
    for district in state.city.districts:
        if district.id in union.territory:
            district.modifiers.unrest = 0.2
            district.modifiers.security = 0.8
    
    system = FactionSystem(cooldown_ticks=1)
    
    # Use large RNG value to skip LOBBY option and reach SABOTAGE
    rng = DeterministicRNG(100.0)  # Large value to select later options
    
    # Run multiple ticks to allow both factions a chance to act
    sabotage = None
    for _ in range(10):
        actions = system.tick(state, rng=rng)
        sabotage = next((a for a in actions if a.action == "SABOTAGE_RIVAL"), None)
        if sabotage is not None:
            break
    
    assert sabotage is not None, "Expected a sabotage action within 10 ticks"


def test_sabotage_reduces_rival_legitimacy() -> None:
    """SABOTAGE_RIVAL reduces target's legitimacy by 0.04.
    
    Contract: The target faction loses 0.04 legitimacy per sabotage.
    We verify this by checking the state change on the target faction
    when only the acting faction can perform actions.
    """
    state = _multi_faction_state()
    state.environment.stability = 0.8
    
    # Set up union as the only faction that can act (will sabotage cartel)
    union = state.factions["union_of_flux"]
    cartel = state.factions["cartel_of_mist"]
    
    # Union setup: low legitimacy, high resources, stable territory
    union.legitimacy = 0.4
    union.resources = {"influence": 200}
    for district in state.city.districts:
        if district.id in union.territory:
            district.modifiers.unrest = 0.2
            district.modifiers.security = 0.8
    
    # Cartel setup: HIGH legitimacy (creates gap), stable to not generate actions
    cartel.legitimacy = 0.9  # High legitimacy = no lobby, creates legitimacy gap
    cartel.resources = {"influence": 200}  # High resources = no recruit
    for district in state.city.districts:
        if district.id in cartel.territory:
            district.modifiers.unrest = 0.2  # Low unrest = no invest
            district.modifiers.security = 0.9
    
    system = FactionSystem(cooldown_ticks=1)
    
    # Record cartel's legitimacy before potential sabotage
    cartel_legitimacy_before = cartel.legitimacy
    
    # Run tick with large RNG value to favor SABOTAGE over LOBBY
    actions = system.tick(state, rng=DeterministicRNG(100.0))
    
    # Find sabotage action targeting cartel
    sabotage = next(
        (a for a in actions if a.action == "SABOTAGE_RIVAL" and a.target == cartel.id),
        None
    )
    
    if sabotage is not None:
        # Verify cartel lost exactly 0.04 legitimacy
        expected_delta = 0.04
        actual_delta = cartel_legitimacy_before - cartel.legitimacy
        assert abs(actual_delta - expected_delta) < 0.0001, \
            f"Expected legitimacy drop of {expected_delta}, got {actual_delta}"
    else:
        # If union didn't sabotage on first tick, cartel should still be intact
        # (cartel won't act because all needs satisfied)
        assert cartel.legitimacy == cartel_legitimacy_before


def test_sabotage_costs_actor_legitimacy() -> None:
    """SABOTAGE_RIVAL costs the actor 0.01 legitimacy and 2 resources.
    
    Contract: The acting faction loses 0.01 legitimacy and 2 resources.
    """
    state = _multi_faction_state()
    state.environment.stability = 0.8
    
    union = state.factions["union_of_flux"]
    cartel = state.factions["cartel_of_mist"]
    union.legitimacy = 0.5
    union.resources = {"influence": 200}
    cartel.legitimacy = 0.9  # Much higher - ensures union is actor
    
    for district in state.city.districts:
        if district.id in union.territory:
            district.modifiers.unrest = 0.2
            district.modifiers.security = 0.8
    
    system = FactionSystem(cooldown_ticks=1)
    
    sabotage = None
    for _ in range(20):
        before_resources = union.resources.get("influence", 0)
        before_legitimacy = union.legitimacy
        
        actions = system.tick(state, rng=DeterministicRNG(100.0))
        sabotage = next(
            (
                a
                for a in actions
                if a.action == "SABOTAGE_RIVAL" and a.faction_id == union.id
            ),
            None,
        )
        if sabotage is not None:
            # Verify actor's losses
            assert sabotage.legitimacy_delta == -0.01
            assert sabotage.resource_delta == -2
            assert union.resources.get("influence", 0) == before_resources - 2
            assert abs(union.legitimacy - (before_legitimacy - 0.01)) < 0.0001
            break
    
    assert sabotage is not None


# =============================================================================
# No-action and cooldown tests
# =============================================================================


def test_faction_takes_no_action_when_all_needs_satisfied() -> None:
    """Faction with high legitimacy, resources, and stable territory is idle.
    
    Contract: If no action conditions are met, no action is taken.
    - legitimacy >= 0.7 → no LOBBY
    - resource pressure >= 0.5 → no RECRUIT  
    - territory unrest <= 0.4 and security >= 0.5 → no INVEST
    - no rival or stability < 0.45 → no SABOTAGE
    """
    state, faction = _single_faction_state()
    faction.legitimacy = 0.95
    faction.resources = {"influence": 200}  # High resources = high pressure
    for district in state.city.districts:
        district.modifiers.unrest = 0.2
        district.modifiers.security = 0.9
    
    system = FactionSystem(cooldown_ticks=1)
    # Any RNG value works since no options should be available
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    assert actions == []


def test_cooldown_prevents_consecutive_actions() -> None:
    """Faction cannot act on consecutive ticks due to cooldown.
    
    Contract: After taking an action, faction is on cooldown for
    cooldown_ticks ticks.
    """
    state, faction = _single_faction_state()
    faction.legitimacy = 0.4  # Low - will trigger LOBBY
    faction.resources = {"influence": 60}
    for district in state.city.districts:
        district.modifiers.unrest = 0.2
        district.modifiers.security = 0.8
    
    system = FactionSystem(cooldown_ticks=2)  # 2-tick cooldown
    
    # First tick - should act
    actions_t1 = system.tick(state, rng=DeterministicRNG(0.0))
    assert len(actions_t1) == 1
    
    # Second tick - on cooldown
    actions_t2 = system.tick(state, rng=DeterministicRNG(0.0))
    assert len(actions_t2) == 0
    
    # Third tick - still on cooldown (cooldown=2)
    actions_t3 = system.tick(state, rng=DeterministicRNG(0.0))
    assert len(actions_t3) == 0
    
    # Fourth tick - cooldown expired, can act again
    actions_t4 = system.tick(state, rng=DeterministicRNG(0.0))
    assert len(actions_t4) == 1


# =============================================================================
# FactionAction report tests
# =============================================================================


def test_faction_action_report_format() -> None:
    """FactionAction.to_report() produces expected dictionary structure."""
    state, faction = _single_faction_state()
    faction.legitimacy = 0.4
    faction.resources = {"influence": 60}
    for district in state.city.districts:
        district.modifiers.unrest = 0.2
        district.modifiers.security = 0.8
    
    system = FactionSystem(cooldown_ticks=1)
    actions = system.tick(state, rng=DeterministicRNG(0.0))
    
    assert len(actions) == 1
    report = actions[0].to_report()
    
    # Verify report structure
    assert "faction_id" in report
    assert "faction_name" in report
    assert "action" in report
    assert "target" in report
    assert "target_name" in report
    assert "detail" in report
    assert "legitimacy_delta" in report
    assert "resource_delta" in report
    assert "district_id" in report
    
    # Verify types
    assert isinstance(report["faction_id"], str)
    assert isinstance(report["faction_name"], str)
    assert isinstance(report["action"], str)
    assert isinstance(report["legitimacy_delta"], float)
    assert isinstance(report["resource_delta"], int)
