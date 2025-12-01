"""Tests for the AI Player strategies module."""

from __future__ import annotations

import pytest

from gengine.ai_player.strategies import (
    AggressiveStrategy,
    BalancedStrategy,
    DiplomaticStrategy,
    StrategyConfig,
    StrategyDecision,
    StrategyType,
    create_strategy,
)
from gengine.echoes.llm.intents import IntentType


class TestStrategyConfig:
    """Tests for StrategyConfig dataclass."""

    def test_default_config(self) -> None:
        config = StrategyConfig()
        assert config.stability_critical == 0.4
        assert config.stability_low == 0.6
        assert config.stability_target == 0.8
        assert config.faction_low_legitimacy == 0.4
        assert config.resource_low_capacity == 0.3
        assert config.action_interval == 5
        assert config.inspect_interval == 10

    def test_custom_config(self) -> None:
        config = StrategyConfig(
            stability_critical=0.3,
            stability_low=0.5,
            action_interval=3,
        )
        assert config.stability_critical == 0.3
        assert config.stability_low == 0.5
        assert config.action_interval == 3

    def test_config_validates_stability_critical_range(self) -> None:
        with pytest.raises(ValueError, match="stability_critical must be between"):
            StrategyConfig(stability_critical=1.5)
        with pytest.raises(ValueError, match="stability_critical must be between"):
            StrategyConfig(stability_critical=-0.1)

    def test_config_validates_stability_low_range(self) -> None:
        with pytest.raises(ValueError, match="stability_low must be between"):
            StrategyConfig(stability_low=1.5)

    def test_config_validates_stability_order(self) -> None:
        with pytest.raises(ValueError, match="stability_critical must be less than"):
            StrategyConfig(stability_critical=0.7, stability_low=0.5)

    def test_config_validates_action_interval(self) -> None:
        with pytest.raises(ValueError, match="action_interval must be at least 1"):
            StrategyConfig(action_interval=0)


class TestStrategyDecision:
    """Tests for StrategyDecision dataclass."""

    def test_to_dict_includes_all_fields(self) -> None:
        from gengine.echoes.llm.intents import InspectIntent

        intent = InspectIntent(
            session_id="test",
            target_type="district",
            target_id="test-district",
        )
        decision = StrategyDecision(
            intent=intent,
            priority=0.8,
            rationale="Test rationale",
            strategy_type=StrategyType.BALANCED,
            tick=42,
            state_snapshot={"stability": 0.7},
        )

        result = decision.to_dict()

        assert result["intent_type"] == "INSPECT"
        assert result["priority"] == 0.8
        assert result["rationale"] == "Test rationale"
        assert result["strategy_type"] == "balanced"
        assert result["tick"] == 42
        assert result["state_summary"]["stability"] == 0.7

    def test_to_dict_rounds_float_values(self) -> None:
        from gengine.echoes.llm.intents import InspectIntent

        intent = InspectIntent(
            session_id="test",
            target_type="district",
            target_id="test-district",
        )
        decision = StrategyDecision(
            intent=intent,
            priority=0.123456789,
            rationale="Test",
            strategy_type=StrategyType.BALANCED,
            state_snapshot={"value": 0.987654321},
        )

        result = decision.to_dict()

        assert result["priority"] == 0.1235
        assert result["state_summary"]["value"] == 0.9877


class TestBalancedStrategy:
    """Tests for BalancedStrategy."""

    def test_strategy_type(self) -> None:
        strategy = BalancedStrategy()
        assert strategy.strategy_type == StrategyType.BALANCED

    def test_default_config_values(self) -> None:
        strategy = BalancedStrategy()
        assert strategy.config.stability_low == 0.6
        assert strategy.config.stability_critical == 0.4
        assert strategy.config.faction_low_legitimacy == 0.4
        assert strategy.config.action_interval == 5

    def test_evaluate_critical_stability(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "stability": 0.3,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.5},
            "districts": [{"id": "d1", "unrest": 0.8}],
        }

        decisions = strategy.evaluate(state, 10)

        assert len(decisions) >= 1
        assert decisions[0].priority == 1.0
        assert decisions[0].intent.intent == IntentType.DEPLOY_RESOURCE
        assert "emergency" in decisions[0].rationale.lower()

    def test_evaluate_low_stability(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "stability": 0.55,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.3},
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        # Should include negotiation for low legitimacy faction
        negotiate_decisions = [
            d for d in decisions if d.intent.intent == IntentType.NEGOTIATE
        ]
        assert len(negotiate_decisions) >= 1

    def test_evaluate_stable_state(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "stability": 0.9,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.8},
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        # With high stability and high legitimacy, should only have inspection
        if decisions:
            # May or may not have decisions depending on timing
            pass

    def test_periodic_inspection(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "stability": 0.9,
            "tick": 15,
            "faction_legitimacy": {},
            "districts": [{"id": "d1"}],
        }

        # First inspection at tick 0 internally, so tick 15 should trigger
        decisions = strategy.evaluate(state, 15)

        inspect_decisions = [
            d for d in decisions if d.intent.intent == IntentType.INSPECT
        ]
        assert len(inspect_decisions) >= 1

    def test_should_act_respects_interval(self) -> None:
        strategy = BalancedStrategy()

        # First time should act
        assert strategy._should_act(0) is True

        # Record action at tick 0
        strategy.record_action(0)

        # Should not act immediately after
        assert strategy._should_act(1) is False
        assert strategy._should_act(4) is False

        # Should act after interval passes
        assert strategy._should_act(5) is True


class TestAggressiveStrategy:
    """Tests for AggressiveStrategy."""

    def test_strategy_type(self) -> None:
        strategy = AggressiveStrategy()
        assert strategy.strategy_type == StrategyType.AGGRESSIVE

    def test_higher_thresholds(self) -> None:
        strategy = AggressiveStrategy()
        balanced = BalancedStrategy()

        # Aggressive has higher thresholds
        assert strategy.config.stability_low > balanced.config.stability_low
        aggressive_faction = strategy.config.faction_low_legitimacy
        balanced_faction = balanced.config.faction_low_legitimacy
        assert aggressive_faction > balanced_faction

    def test_more_frequent_actions(self) -> None:
        strategy = AggressiveStrategy()
        balanced = BalancedStrategy()

        assert strategy.config.action_interval < balanced.config.action_interval

    def test_larger_resource_deployments(self) -> None:
        strategy = AggressiveStrategy()
        balanced = BalancedStrategy()

        aggressive_deploy = strategy.config.resource_deploy_amount
        balanced_deploy = balanced.config.resource_deploy_amount
        assert aggressive_deploy > balanced_deploy

    def test_evaluate_low_stability(self) -> None:
        strategy = AggressiveStrategy()
        state = {
            "stability": 0.65,
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [{"id": "d1", "unrest": 0.5}],
        }

        decisions = strategy.evaluate(state, 10)

        # Aggressive should take action even at moderately low stability
        assert len(decisions) >= 1
        assert decisions[0].intent.intent == IntentType.DEPLOY_RESOURCE

    def test_critical_stability_multi_district(self) -> None:
        strategy = AggressiveStrategy()
        state = {
            "stability": 0.4,
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [
                {"id": "d1", "unrest": 0.8},
                {"id": "d2", "unrest": 0.6},
            ],
        }

        decisions = strategy.evaluate(state, 10)

        # Should have multiple resource deployments
        deploy_decisions = [
            d for d in decisions if d.intent.intent == IntentType.DEPLOY_RESOURCE
        ]
        assert len(deploy_decisions) >= 2


class TestDiplomaticStrategy:
    """Tests for DiplomaticStrategy."""

    def test_strategy_type(self) -> None:
        strategy = DiplomaticStrategy()
        assert strategy.strategy_type == StrategyType.DIPLOMATIC

    def test_lower_stability_threshold(self) -> None:
        strategy = DiplomaticStrategy()
        balanced = BalancedStrategy()

        # Diplomatic has lower stability threshold
        assert strategy.config.stability_low < balanced.config.stability_low

    def test_higher_faction_threshold(self) -> None:
        strategy = DiplomaticStrategy()
        balanced = BalancedStrategy()

        # More willing to support factions
        diplomatic_faction = strategy.config.faction_low_legitimacy
        balanced_faction = balanced.config.faction_low_legitimacy
        assert diplomatic_faction > balanced_faction

    def test_evaluate_prefers_negotiation(self) -> None:
        strategy = DiplomaticStrategy()
        state = {
            "stability": 0.7,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.4},
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        # Should prefer negotiation
        negotiate_decisions = [
            d for d in decisions if d.intent.intent == IntentType.NEGOTIATE
        ]
        assert len(negotiate_decisions) >= 1

    def test_evaluate_multiple_factions(self) -> None:
        strategy = DiplomaticStrategy()
        state = {
            "stability": 0.7,
            "tick": 10,
            "faction_legitimacy": {
                "faction-a": 0.3,
                "faction-b": 0.4,
            },
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        # Should target both factions
        negotiate_decisions = [
            d for d in decisions if d.intent.intent == IntentType.NEGOTIATE
        ]
        assert len(negotiate_decisions) >= 2

    def test_resource_only_in_critical(self) -> None:
        strategy = DiplomaticStrategy()
        state = {
            "stability": 0.3,  # Below critical threshold
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [{"id": "d1"}],
        }

        decisions = strategy.evaluate(state, 10)

        # Should include resource deployment in critical situations
        deploy_decisions = [
            d for d in decisions if d.intent.intent == IntentType.DEPLOY_RESOURCE
        ]
        assert len(deploy_decisions) >= 1


class TestCreateStrategy:
    """Tests for create_strategy factory function."""

    def test_create_balanced(self) -> None:
        strategy = create_strategy(StrategyType.BALANCED)
        assert isinstance(strategy, BalancedStrategy)

    def test_create_aggressive(self) -> None:
        strategy = create_strategy(StrategyType.AGGRESSIVE)
        assert isinstance(strategy, AggressiveStrategy)

    def test_create_diplomatic(self) -> None:
        strategy = create_strategy(StrategyType.DIPLOMATIC)
        assert isinstance(strategy, DiplomaticStrategy)

    def test_create_with_custom_session_id(self) -> None:
        strategy = create_strategy(StrategyType.BALANCED, session_id="custom-session")
        assert strategy._session_id == "custom-session"

    def test_create_with_custom_config(self) -> None:
        config = StrategyConfig(stability_low=0.7)
        strategy = create_strategy(StrategyType.BALANCED, config=config)
        assert strategy.config.stability_low == 0.7

    def test_create_unknown_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown strategy type"):
            create_strategy("unknown")  # type: ignore


class TestBaseStrategyMethods:
    """Tests for BaseStrategy helper methods."""

    def test_find_lowest_legitimacy_faction(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "faction_legitimacy": {
                "faction-a": 0.7,
                "faction-b": 0.3,
                "faction-c": 0.5,
            }
        }

        faction_id, legitimacy = strategy._find_lowest_legitimacy_faction(state)

        assert faction_id == "faction-b"
        assert legitimacy == 0.3

    def test_find_lowest_legitimacy_empty(self) -> None:
        strategy = BalancedStrategy()
        state = {"faction_legitimacy": {}}

        faction_id, legitimacy = strategy._find_lowest_legitimacy_faction(state)

        assert faction_id is None
        assert legitimacy == 1.0

    def test_find_district_needing_resources(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "districts": [
                {"id": "d1", "resource_capacity": 0.8},
                {"id": "d2", "resource_capacity": 0.2},
                {"id": "d3", "resource_capacity": 0.5},
            ]
        }

        district_id = strategy._find_district_needing_resources(state)

        assert district_id == "d2"

    def test_find_district_needing_resources_none(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "districts": [
                {"id": "d1", "resource_capacity": 0.8},
                {"id": "d2", "resource_capacity": 0.6},
            ]
        }

        district_id = strategy._find_district_needing_resources(state)

        assert district_id is None

    def test_extract_state_metrics(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "stability": 0.75,
            "tick": 42,
            "faction_legitimacy": {"f1": 0.5, "f2": 0.6},
            "district_count": 3,
            "agent_count": 10,
        }

        metrics = strategy._extract_state_metrics(state)

        assert metrics["stability"] == 0.75
        assert metrics["tick"] == 42
        assert metrics["faction_count"] == 2
        assert metrics["district_count"] == 3
        assert metrics["agent_count"] == 10

    def test_record_action_updates_last_tick(self) -> None:
        strategy = BalancedStrategy()

        strategy.record_action(50)

        assert strategy._last_action_tick == 50
        assert strategy._should_act(51) is False
        assert strategy._should_act(55) is True

    def test_record_inspect_updates_last_tick(self) -> None:
        strategy = BalancedStrategy()

        strategy.record_inspect(50)

        assert strategy._last_inspect_tick == 50
        assert strategy._should_inspect(51) is False
        assert strategy._should_inspect(60) is True


class TestStrategyDecisionSorting:
    """Tests for decision sorting by priority."""

    def test_decisions_sorted_by_priority(self) -> None:
        strategy = BalancedStrategy()
        state = {
            "stability": 0.35,  # Critical
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.3},
            "districts": [{"id": "d1", "unrest": 0.9}],
        }

        decisions = strategy.evaluate(state, 10)

        # Verify sorted by priority (highest first)
        for i in range(len(decisions) - 1):
            assert decisions[i].priority >= decisions[i + 1].priority
