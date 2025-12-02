"""Tests for the hybrid LLM-enhanced AI player strategy."""

from __future__ import annotations

import pytest

from gengine.ai_player.llm_strategy import (
    LLMBudgetState,
    LLMDecisionLayer,
    LLMDecisionRequest,
    LLMStrategyConfig,
    create_llm_decision_layer,
    evaluate_complexity,
)
from gengine.ai_player.strategies import (
    BalancedStrategy,
    HybridStrategy,
    StrategyConfig,
    StrategyType,
    create_strategy,
)
from gengine.echoes.llm.providers import StubProvider
from gengine.echoes.llm.settings import LLMSettings


class TestLLMStrategyConfig:
    """Tests for LLMStrategyConfig dataclass."""

    def test_default_config(self) -> None:
        config = LLMStrategyConfig()
        assert config.llm_call_budget == 10
        assert config.complexity_threshold_factions == 2
        assert config.complexity_threshold_legitimacy == 0.4
        assert config.complexity_threshold_stability == 0.5
        assert config.complexity_threshold_seeds == 2
        assert config.cost_per_call_estimate == 0.01
        assert config.llm_timeout_seconds == 10.0
        assert config.fallback_on_error is True

    def test_custom_config(self) -> None:
        config = LLMStrategyConfig(
            llm_call_budget=5,
            complexity_threshold_stability=0.3,
            cost_per_call_estimate=0.02,
        )
        assert config.llm_call_budget == 5
        assert config.complexity_threshold_stability == 0.3
        assert config.cost_per_call_estimate == 0.02

    def test_validates_negative_budget(self) -> None:
        with pytest.raises(ValueError, match="llm_call_budget cannot be negative"):
            LLMStrategyConfig(llm_call_budget=-1)

    def test_validates_legitimacy_range(self) -> None:
        with pytest.raises(ValueError, match="complexity_threshold_legitimacy"):
            LLMStrategyConfig(complexity_threshold_legitimacy=1.5)
        with pytest.raises(ValueError, match="complexity_threshold_legitimacy"):
            LLMStrategyConfig(complexity_threshold_legitimacy=-0.1)

    def test_validates_stability_range(self) -> None:
        with pytest.raises(ValueError, match="complexity_threshold_stability"):
            LLMStrategyConfig(complexity_threshold_stability=1.5)

    def test_validates_timeout(self) -> None:
        with pytest.raises(ValueError, match="llm_timeout_seconds must be positive"):
            LLMStrategyConfig(llm_timeout_seconds=0)


class TestLLMBudgetState:
    """Tests for LLMBudgetState tracking."""

    def test_default_state(self) -> None:
        budget = LLMBudgetState()
        assert budget.calls_used == 0
        assert budget.estimated_cost == 0.0
        assert budget.fallback_count == 0
        assert budget.last_call_latency_ms == 0.0

    def test_to_dict(self) -> None:
        budget = LLMBudgetState(
            calls_used=5,
            estimated_cost=0.05,
            fallback_count=2,
            last_call_latency_ms=150.5,
        )
        result = budget.to_dict()
        assert result["calls_used"] == 5
        assert result["estimated_cost"] == 0.05
        assert result["fallback_count"] == 2
        assert result["last_call_latency_ms"] == 150.5


class TestLLMDecisionRequest:
    """Tests for LLMDecisionRequest dataclass."""

    def test_to_prompt_context(self) -> None:
        state = {
            "stability": 0.6,
            "tick": 42,
            "faction_legitimacy": {"faction-a": 0.5},
            "district_count": 3,
            "story_seeds": [{"seed_id": "crisis-1"}],
        }
        request = LLMDecisionRequest(
            state=state,
            tick=42,
            session_id="test",
            complexity_factors=["critical_stability"],
        )

        context = request.to_prompt_context()

        assert context["stability"] == 0.6
        assert context["tick"] == 42
        assert context["faction_legitimacy"] == {"faction-a": 0.5}
        assert context["complexity_factors"] == ["critical_stability"]

    def test_recent_decisions_limited(self) -> None:
        request = LLMDecisionRequest(
            state={"stability": 0.8},
            tick=10,
            session_id="test",
            context_history=["d1", "d2", "d3", "d4", "d5", "d6", "d7"],
        )

        context = request.to_prompt_context()

        # Should only include last 5 decisions
        assert len(context["recent_decisions"]) == 5


class TestEvaluateComplexity:
    """Tests for the complexity evaluation function."""

    def test_low_stability_is_complex(self) -> None:
        config = LLMStrategyConfig(complexity_threshold_stability=0.5)
        state = {"stability": 0.4}

        is_complex, factors = evaluate_complexity(state, config)

        assert is_complex is True
        assert "critical_stability" in factors

    def test_high_stability_not_complex(self) -> None:
        config = LLMStrategyConfig(complexity_threshold_stability=0.5)
        state = {"stability": 0.8}

        is_complex, factors = evaluate_complexity(state, config)

        assert "critical_stability" not in factors

    def test_multiple_stressed_factions_is_complex(self) -> None:
        config = LLMStrategyConfig(
            complexity_threshold_factions=2,
            complexity_threshold_legitimacy=0.4,
        )
        state = {
            "stability": 0.8,
            "faction_legitimacy": {
                "faction-a": 0.3,
                "faction-b": 0.2,
                "faction-c": 0.8,
            },
        }

        is_complex, factors = evaluate_complexity(state, config)

        assert is_complex is True
        assert "multiple_stressed_factions" in factors

    def test_single_stressed_faction_not_complex(self) -> None:
        config = LLMStrategyConfig(
            complexity_threshold_factions=2,
            complexity_threshold_legitimacy=0.4,
        )
        state = {
            "stability": 0.8,
            "faction_legitimacy": {
                "faction-a": 0.3,
                "faction-b": 0.8,
            },
        }

        is_complex, factors = evaluate_complexity(state, config)

        assert "multiple_stressed_factions" not in factors

    def test_multiple_story_seeds_is_complex(self) -> None:
        config = LLMStrategyConfig(complexity_threshold_seeds=2)
        state = {
            "stability": 0.8,
            "story_seeds": [
                {"seed_id": "crisis-1"},
                {"seed_id": "crisis-2"},
            ],
        }

        is_complex, factors = evaluate_complexity(state, config)

        assert is_complex is True
        assert "multiple_story_seeds" in factors

    def test_faction_legitimacy_spread_is_complex(self) -> None:
        config = LLMStrategyConfig()
        state = {
            "stability": 0.8,
            "faction_legitimacy": {
                "faction-a": 0.9,
                "faction-b": 0.5,  # 0.4 spread
            },
        }

        is_complex, factors = evaluate_complexity(state, config)

        assert is_complex is True
        assert "faction_legitimacy_spread" in factors

    def test_no_complexity_factors_not_complex(self) -> None:
        config = LLMStrategyConfig()
        state = {
            "stability": 0.9,
            "faction_legitimacy": {"faction-a": 0.8},
            "story_seeds": [],
        }

        is_complex, factors = evaluate_complexity(state, config)

        assert is_complex is False
        assert len(factors) == 0


class TestLLMDecisionLayer:
    """Tests for the LLM decision layer."""

    def test_create_with_stub_provider(self) -> None:
        layer = create_llm_decision_layer()
        assert layer is not None
        assert layer.budget.calls_used == 0

    def test_budget_not_exhausted_initially(self) -> None:
        config = LLMStrategyConfig(llm_call_budget=5)
        layer = create_llm_decision_layer(config=config)
        assert layer.is_budget_exhausted() is False

    def test_budget_exhausted_at_limit(self) -> None:
        config = LLMStrategyConfig(llm_call_budget=2)
        layer = create_llm_decision_layer(config=config)

        # Simulate budget exhaustion
        layer._budget.calls_used = 2

        assert layer.is_budget_exhausted() is True

    def test_unlimited_budget_never_exhausted(self) -> None:
        config = LLMStrategyConfig(llm_call_budget=0)  # 0 = unlimited
        layer = create_llm_decision_layer(config=config)

        layer._budget.calls_used = 1000

        assert layer.is_budget_exhausted() is False

    def test_request_decision_with_stub_provider(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)
        config = LLMStrategyConfig(llm_call_budget=5)
        layer = LLMDecisionLayer(provider, config, session_id="test")

        request = LLMDecisionRequest(
            state={"stability": 0.4},
            tick=10,
            session_id="test",
            complexity_factors=["critical_stability"],
        )

        response = layer.request_decision(request)

        assert response is not None
        assert response.intent is not None
        assert response.confidence > 0
        assert layer.budget.calls_used == 1

    def test_request_decision_returns_none_when_budget_exhausted(self) -> None:
        config = LLMStrategyConfig(llm_call_budget=1)
        layer = create_llm_decision_layer(config=config)
        layer._budget.calls_used = 1

        request = LLMDecisionRequest(
            state={"stability": 0.4},
            tick=10,
            session_id="test",
        )

        response = layer.request_decision(request)

        assert response is None

    def test_budget_tracks_cost(self) -> None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)
        config = LLMStrategyConfig(
            llm_call_budget=5,
            cost_per_call_estimate=0.02,
        )
        layer = LLMDecisionLayer(provider, config, session_id="test")

        request = LLMDecisionRequest(
            state={"stability": 0.4},
            tick=10,
            session_id="test",
        )

        layer.request_decision(request)
        layer.request_decision(request)

        assert layer.budget.calls_used == 2
        assert layer.budget.estimated_cost == pytest.approx(0.04)


class TestHybridStrategy:
    """Tests for the hybrid LLM-enhanced strategy."""

    def test_strategy_type(self) -> None:
        strategy = HybridStrategy()
        assert strategy.strategy_type == StrategyType.HYBRID

    def test_default_fallback_is_balanced(self) -> None:
        strategy = HybridStrategy()
        assert isinstance(strategy._fallback, BalancedStrategy)

    def test_custom_fallback_strategy(self) -> None:
        from gengine.ai_player.strategies import AggressiveStrategy

        fallback = AggressiveStrategy(session_id="custom")
        strategy = HybridStrategy(fallback_strategy=fallback)
        assert strategy._fallback is fallback

    def test_evaluate_uses_rules_for_simple_state(self) -> None:
        strategy = HybridStrategy()
        state = {
            "stability": 0.9,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.8},
            "districts": [],
            "story_seeds": [],
        }

        decisions = strategy.evaluate(state, 10)

        # Should use rule-based decisions for simple state
        assert strategy._rule_decisions > 0
        # All decisions should be from rules
        for decision in decisions:
            assert decision.decision_source == "rule"

    def test_evaluate_uses_llm_for_complex_state(self) -> None:
        strategy = HybridStrategy(
            llm_config=LLMStrategyConfig(
                complexity_threshold_stability=0.5,
                llm_call_budget=5,
            ),
        )
        state = {
            "stability": 0.3,  # Critical - should trigger LLM
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.5},
            "districts": [],
            "story_seeds": [],
        }

        decisions = strategy.evaluate(state, 10)

        # Should have at least one LLM decision
        assert strategy._llm_decisions > 0
        # First decision should be from LLM
        assert decisions[0].decision_source == "llm"

    def test_evaluate_falls_back_when_budget_exhausted(self) -> None:
        strategy = HybridStrategy(
            llm_config=LLMStrategyConfig(llm_call_budget=0),  # Already exhausted
        )
        # Manually exhaust budget
        strategy._llm_layer._budget.calls_used = 1
        strategy._llm_layer._config.llm_call_budget = 1

        state = {
            "stability": 0.3,  # Would trigger LLM, but budget exhausted
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        # Should fall back to rules
        assert strategy._llm_decisions == 0
        for decision in decisions:
            assert decision.decision_source == "rule"

    def test_llm_decision_includes_confidence(self) -> None:
        strategy = HybridStrategy(
            llm_config=LLMStrategyConfig(
                complexity_threshold_stability=0.5,
                llm_call_budget=5,
            ),
        )
        state = {
            "stability": 0.3,
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        llm_decision = decisions[0]
        assert llm_decision.decision_source == "llm"
        assert llm_decision.llm_confidence is not None
        assert 0.0 <= llm_decision.llm_confidence <= 1.0

    def test_telemetry_tracks_decisions(self) -> None:
        strategy = HybridStrategy()

        # Evaluate simple state (rules only)
        simple_state = {
            "stability": 0.9,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.8},
            "districts": [],
            "story_seeds": [],
        }
        strategy.evaluate(simple_state, 10)

        telemetry = strategy.telemetry
        assert "rule_decisions" in telemetry
        assert "llm_decisions" in telemetry
        assert "llm_budget" in telemetry
        assert telemetry["rule_decisions"] > 0

    def test_record_action_updates_both_strategies(self) -> None:
        strategy = HybridStrategy()

        strategy.record_action(50)

        assert strategy._last_action_tick == 50
        assert strategy._fallback._last_action_tick == 50

    def test_record_inspect_updates_both_strategies(self) -> None:
        strategy = HybridStrategy()

        strategy.record_inspect(50)

        assert strategy._last_inspect_tick == 50
        assert strategy._fallback._last_inspect_tick == 50


class TestCreateStrategyWithHybrid:
    """Tests for create_strategy factory with hybrid type."""

    def test_create_hybrid(self) -> None:
        strategy = create_strategy(StrategyType.HYBRID)
        assert isinstance(strategy, HybridStrategy)

    def test_create_hybrid_with_session_id(self) -> None:
        strategy = create_strategy(StrategyType.HYBRID, session_id="custom-session")
        assert strategy._session_id == "custom-session"

    def test_create_hybrid_with_config(self) -> None:
        config = StrategyConfig(stability_low=0.7)
        strategy = create_strategy(StrategyType.HYBRID, config=config)
        assert strategy.config.stability_low == 0.7

    def test_create_hybrid_with_llm_config(self) -> None:
        llm_config = LLMStrategyConfig(llm_call_budget=20)
        strategy = create_strategy(
            StrategyType.HYBRID,
            llm_config=llm_config,
        )
        assert isinstance(strategy, HybridStrategy)
        assert strategy.llm_config.llm_call_budget == 20


class TestHybridStrategyScenarios:
    """Scenario tests comparing rule-only vs hybrid strategies."""

    def test_rule_vs_hybrid_on_stable_state(self) -> None:
        """Both should behave similarly on stable states."""
        rule_strategy = BalancedStrategy()
        hybrid_strategy = HybridStrategy()

        state = {
            "stability": 0.9,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.8},
            "districts": [],
            "story_seeds": [],
        }

        rule_decisions = rule_strategy.evaluate(state, 10)
        hybrid_decisions = hybrid_strategy.evaluate(state, 10)

        # Hybrid should use rules for stable state, so similar count
        # (might differ slightly due to decision source field)
        assert len(hybrid_decisions) == len(rule_decisions)

    def test_hybrid_prioritizes_llm_on_complex_state(self) -> None:
        """Hybrid should put LLM decision first on complex states."""
        hybrid_strategy = HybridStrategy(
            llm_config=LLMStrategyConfig(
                complexity_threshold_stability=0.5,
                llm_call_budget=5,
            ),
        )

        state = {
            "stability": 0.3,
            "tick": 10,
            "faction_legitimacy": {
                "faction-a": 0.2,
                "faction-b": 0.2,
            },
            "districts": [{"id": "d1", "unrest": 0.8}],
            "story_seeds": [],
        }

        decisions = hybrid_strategy.evaluate(state, 10)

        # First decision should be LLM-based
        assert decisions[0].decision_source == "llm"
        # Subsequent decisions should be rule-based with lower priority
        if len(decisions) > 1:
            assert decisions[1].priority < decisions[0].priority

    def test_multiple_evaluations_track_budget(self) -> None:
        """Budget should accumulate across evaluations."""
        hybrid_strategy = HybridStrategy(
            llm_config=LLMStrategyConfig(
                complexity_threshold_stability=0.5,
                llm_call_budget=3,
            ),
        )

        complex_state = {
            "stability": 0.3,
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [],
        }

        # First evaluation - uses LLM
        hybrid_strategy.evaluate(complex_state, 10)
        assert hybrid_strategy.llm_budget.calls_used == 1

        # Second evaluation - uses LLM
        hybrid_strategy.evaluate(complex_state, 20)
        assert hybrid_strategy.llm_budget.calls_used == 2

        # Third evaluation - uses LLM
        hybrid_strategy.evaluate(complex_state, 30)
        assert hybrid_strategy.llm_budget.calls_used == 3

        # Fourth evaluation - budget exhausted, falls back to rules
        hybrid_strategy.evaluate(complex_state, 40)
        assert hybrid_strategy.llm_budget.calls_used == 3  # No increase

    def test_decision_source_in_telemetry(self) -> None:
        """Decision source should be tracked in telemetry."""
        hybrid_strategy = HybridStrategy(
            llm_config=LLMStrategyConfig(
                complexity_threshold_stability=0.5,
                llm_call_budget=5,
            ),
        )

        # Evaluate complex state
        complex_state = {
            "stability": 0.3,
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [],
        }
        decisions = hybrid_strategy.evaluate(complex_state, 10)

        # Check decision telemetry
        decision_dict = decisions[0].to_dict()
        assert "decision_source" in decision_dict
        assert decision_dict["decision_source"] == "llm"

    def test_rule_decision_source_in_telemetry(self) -> None:
        """Rule decisions should have source='rule' in telemetry."""
        rule_strategy = BalancedStrategy()

        state = {
            "stability": 0.5,
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.3},
            "districts": [],
        }

        decisions = rule_strategy.evaluate(state, 10)

        if decisions:
            decision_dict = decisions[0].to_dict()
            assert "decision_source" in decision_dict
            assert decision_dict["decision_source"] == "rule"


class TestHybridWith100TickRun:
    """Regression tests with 100-tick simulation runs."""

    def test_hybrid_100_tick_run_local(self) -> None:
        """Hybrid strategy should work over 100 ticks with local engine."""
        from gengine.ai_player import ActorConfig, AIActor
        from gengine.echoes.sim import SimEngine

        engine = SimEngine()
        engine.initialize_state(world="default")

        config = ActorConfig(
            strategy_type=StrategyType.HYBRID,
            tick_budget=100,
            analysis_interval=10,
        )
        # Create custom hybrid strategy with budget
        hybrid = HybridStrategy(
            session_id="test",
            llm_config=LLMStrategyConfig(llm_call_budget=10),
        )

        actor = AIActor(engine=engine, config=config, strategy=hybrid)
        report = actor.run()

        assert report.ticks_run == 100
        assert report.strategy_type == StrategyType.HYBRID
        assert report.final_stability >= 0.0

    def test_hybrid_maintains_stability(self) -> None:
        """Hybrid strategy should maintain or improve stability."""
        from gengine.ai_player import ActorConfig, AIActor
        from gengine.echoes.sim import SimEngine

        engine = SimEngine()
        engine.initialize_state(world="default")

        hybrid = HybridStrategy(
            session_id="test",
            llm_config=LLMStrategyConfig(llm_call_budget=20),
        )

        config = ActorConfig(
            strategy_type=StrategyType.HYBRID,
            tick_budget=50,
            analysis_interval=10,
        )

        actor = AIActor(engine=engine, config=config, strategy=hybrid)
        report = actor.run()

        # Stability should not crash
        assert report.final_stability >= 0.0
        # Hybrid telemetry should be captured
        assert "llm_budget" in hybrid.telemetry

    def test_hybrid_telemetry_comprehensive(self) -> None:
        """Hybrid strategy telemetry should track all decisions."""
        from gengine.ai_player import ActorConfig, AIActor
        from gengine.echoes.sim import SimEngine

        engine = SimEngine()
        engine.initialize_state(world="default")

        hybrid = HybridStrategy(
            session_id="test",
            llm_config=LLMStrategyConfig(llm_call_budget=5),
        )

        config = ActorConfig(
            strategy_type=StrategyType.HYBRID,
            tick_budget=30,
            analysis_interval=5,
        )

        actor = AIActor(engine=engine, config=config, strategy=hybrid)
        actor.run()

        telemetry = hybrid.telemetry

        # Should have tracked some decisions
        assert telemetry["total_decisions"] >= 0
        assert telemetry["rule_decisions"] >= 0
        assert telemetry["llm_decisions"] >= 0
        assert "llm_budget" in telemetry
        assert "calls_used" in telemetry["llm_budget"]
