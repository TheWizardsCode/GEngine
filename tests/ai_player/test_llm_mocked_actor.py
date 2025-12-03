"""Tests for AI Player with mocked LLM integration.

This module provides comprehensive tests for the AI player actor using
mocked LLM providers to test hybrid strategy functionality without
making real API calls.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gengine.ai_player import ActorConfig, AIActor
from gengine.ai_player.actor import create_actor_from_engine
from gengine.ai_player.llm_strategy import (
    LLMBudgetState,
    LLMDecisionLayer,
    LLMDecisionRequest,
    LLMDecisionResponse,
    LLMStrategyConfig,
    create_llm_decision_layer,
    evaluate_complexity,
)
from gengine.ai_player.strategies import (
    BalancedStrategy,
    HybridStrategy,
    StrategyType,
    create_strategy,
)
from gengine.echoes.llm.intents import (
    DeployResourceIntent,
    InspectIntent,
    NegotiateIntent,
)
from gengine.echoes.llm.providers import IntentParseResult, StubProvider
from gengine.echoes.llm.settings import LLMSettings
from gengine.echoes.sim import SimEngine


# ==============================================================================
# Mock Provider for AI Player Tests
# ==============================================================================


class AIPlayerMockProvider(StubProvider):
    """Extended mock provider specifically for AI player testing.

    Provides configurable responses and tracking for AI player scenarios.
    """

    def __init__(self, settings: LLMSettings) -> None:
        super().__init__(settings)
        self._responses: list[dict[str, Any]] = []
        self._call_index = 0
        self._delay_seconds = 0.0
        self._should_timeout = False
        self._should_fail = False
        self._failure_message = "Simulated failure"

    def configure_responses(self, responses: list[dict[str, Any]]) -> None:
        """Configure a sequence of responses to return."""
        self._responses = responses
        self._call_index = 0

    def configure_delay(self, seconds: float) -> None:
        """Configure response delay."""
        self._delay_seconds = seconds

    def configure_timeout(self) -> None:
        """Configure provider to timeout."""
        self._should_timeout = True

    def configure_failure(self, message: str = "Simulated failure") -> None:
        """Configure provider to fail."""
        self._should_fail = True
        self._failure_message = message

    def reset(self) -> None:
        """Reset provider state."""
        self._responses = []
        self._call_index = 0
        self._delay_seconds = 0.0
        self._should_timeout = False
        self._should_fail = False

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)

        if self._should_timeout:
            await asyncio.sleep(1000)  # Will be cancelled by timeout

        if self._should_fail:
            raise RuntimeError(self._failure_message)

        if self._responses and self._call_index < len(self._responses):
            response = self._responses[self._call_index]
            self._call_index += 1
            return IntentParseResult(
                intents=[response],
                raw_response=f"[MOCK] Response {self._call_index}",
                confidence=response.get("confidence", 0.9),
            )

        # Default to parent stub behavior
        return await super().parse_intent(user_input, context)


# ==============================================================================
# LLM Decision Layer Tests with Mocking
# ==============================================================================


class TestLLMDecisionLayerMocked:
    """Tests for LLMDecisionLayer with mocked providers."""

    @pytest.fixture
    def mock_provider(self) -> AIPlayerMockProvider:
        settings = LLMSettings(provider="stub")
        return AIPlayerMockProvider(settings)

    @pytest.fixture
    def decision_layer(
        self, mock_provider: AIPlayerMockProvider
    ) -> LLMDecisionLayer:
        config = LLMStrategyConfig(llm_call_budget=10)
        return LLMDecisionLayer(mock_provider, config, session_id="test")

    def test_request_decision_with_custom_response(
        self, mock_provider: AIPlayerMockProvider, decision_layer: LLMDecisionLayer
    ) -> None:
        """Decision layer uses configured mock response."""
        mock_provider.configure_responses(
            [{"type": "stabilize", "target": "district", "confidence": 0.95}]
        )

        request = LLMDecisionRequest(
            state={"stability": 0.3},
            tick=10,
            session_id="test",
            complexity_factors=["critical_stability"],
        )

        response = decision_layer.request_decision(request)

        assert response is not None
        assert response.confidence == 0.95
        assert decision_layer.budget.calls_used == 1

    def test_request_decision_budget_tracking(
        self, mock_provider: AIPlayerMockProvider, decision_layer: LLMDecisionLayer
    ) -> None:
        """Budget tracks calls and cost."""
        config = LLMStrategyConfig(llm_call_budget=5, cost_per_call_estimate=0.05)
        layer = LLMDecisionLayer(mock_provider, config, session_id="test")

        request = LLMDecisionRequest(
            state={"stability": 0.4},
            tick=10,
            session_id="test",
        )

        layer.request_decision(request)
        layer.request_decision(request)
        layer.request_decision(request)

        assert layer.budget.calls_used == 3
        assert layer.budget.estimated_cost == pytest.approx(0.15)

    def test_request_decision_handles_provider_failure(
        self, mock_provider: AIPlayerMockProvider, decision_layer: LLMDecisionLayer
    ) -> None:
        """Decision layer handles provider failures gracefully."""
        mock_provider.configure_failure("API Error")

        request = LLMDecisionRequest(
            state={"stability": 0.3},
            tick=10,
            session_id="test",
        )

        response = decision_layer.request_decision(request)

        assert response is None
        assert decision_layer.budget.fallback_count == 1

    def test_request_decision_respects_budget_limit(
        self, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Decision layer respects budget limits."""
        config = LLMStrategyConfig(llm_call_budget=2)
        layer = LLMDecisionLayer(mock_provider, config, session_id="test")

        request = LLMDecisionRequest(
            state={"stability": 0.3},
            tick=10,
            session_id="test",
        )

        # First two calls succeed
        assert layer.request_decision(request) is not None
        assert layer.request_decision(request) is not None

        # Third call returns None (budget exhausted)
        assert layer.request_decision(request) is None
        assert layer.budget.calls_used == 2

    def test_unlimited_budget_never_exhausted(
        self, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Budget of 0 means unlimited."""
        config = LLMStrategyConfig(llm_call_budget=0)  # Unlimited
        layer = LLMDecisionLayer(mock_provider, config, session_id="test")

        request = LLMDecisionRequest(
            state={"stability": 0.3},
            tick=10,
            session_id="test",
        )

        # Many calls should all succeed
        for _ in range(20):
            layer.request_decision(request)

        assert layer.budget.calls_used == 20
        assert not layer.is_budget_exhausted()


# ==============================================================================
# Hybrid Strategy with Mocked LLM Tests
# ==============================================================================


class TestHybridStrategyMocked:
    """Tests for HybridStrategy with mocked LLM providers."""

    @pytest.fixture
    def mock_provider(self) -> AIPlayerMockProvider:
        settings = LLMSettings(provider="stub")
        return AIPlayerMockProvider(settings)

    def test_hybrid_uses_llm_for_complex_state(
        self, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Hybrid strategy delegates to LLM for complex states."""
        mock_provider.configure_responses(
            [{"type": "stabilize", "target": "district", "confidence": 0.9}]
        )

        config = LLMStrategyConfig(
            complexity_threshold_stability=0.5,
            llm_call_budget=5,
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        strategy = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        # Replace the internal LLM layer with our mock
        strategy._llm_layer = layer

        state = {
            "stability": 0.3,  # Below threshold - triggers LLM
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        assert len(decisions) > 0
        assert strategy._llm_decisions > 0
        # First decision should be LLM-sourced
        assert decisions[0].decision_source == "llm"

    def test_hybrid_uses_rules_for_simple_state(
        self, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Hybrid strategy uses rules for simple states."""
        config = LLMStrategyConfig(
            complexity_threshold_stability=0.5,
            llm_call_budget=5,
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        strategy = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        strategy._llm_layer = layer

        state = {
            "stability": 0.9,  # Above threshold - uses rules
            "tick": 10,
            "faction_legitimacy": {"faction-a": 0.8},
            "districts": [],
            "story_seeds": [],
        }

        decisions = strategy.evaluate(state, 10)

        assert len(decisions) > 0
        # All decisions should be rule-based
        for decision in decisions:
            assert decision.decision_source == "rule"

    def test_hybrid_falls_back_on_llm_failure(
        self, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Hybrid strategy falls back to rules when LLM fails."""
        mock_provider.configure_failure("API Error")

        config = LLMStrategyConfig(
            complexity_threshold_stability=0.5,
            llm_call_budget=5,
            fallback_on_error=True,
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        strategy = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        strategy._llm_layer = layer

        state = {
            "stability": 0.3,  # Would trigger LLM, but it fails
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [],
        }

        decisions = strategy.evaluate(state, 10)

        # Should still get decisions from fallback
        assert len(decisions) > 0
        # All should be rule-based after failure
        for decision in decisions:
            assert decision.decision_source == "rule"

    def test_hybrid_llm_decision_includes_confidence(
        self, mock_provider: AIPlayerMockProvider
    ) -> None:
        """LLM decisions include confidence scores."""
        mock_provider.configure_responses(
            [{"type": "negotiate", "target": "faction", "confidence": 0.85}]
        )

        config = LLMStrategyConfig(
            complexity_threshold_stability=0.5,
            llm_call_budget=5,
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        strategy = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        strategy._llm_layer = layer

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

    def test_hybrid_telemetry_tracks_both_sources(
        self, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Telemetry tracks both LLM and rule decisions."""
        config = LLMStrategyConfig(
            complexity_threshold_stability=0.5,
            llm_call_budget=10,
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        strategy = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        strategy._llm_layer = layer

        # Complex state - uses LLM
        complex_state = {
            "stability": 0.3,
            "tick": 10,
            "faction_legitimacy": {},
            "districts": [],
        }
        strategy.evaluate(complex_state, 10)

        # Simple state - uses rules
        simple_state = {
            "stability": 0.9,
            "tick": 20,
            "faction_legitimacy": {"faction-a": 0.8},
            "districts": [],
            "story_seeds": [],
        }
        strategy.evaluate(simple_state, 20)

        telemetry = strategy.telemetry

        assert telemetry["llm_decisions"] >= 1
        assert telemetry["rule_decisions"] >= 1
        assert "llm_budget" in telemetry


# ==============================================================================
# AI Actor with Mocked LLM Tests
# ==============================================================================


class TestAIActorMockedLLM:
    """Tests for AIActor with mocked LLM for hybrid strategy."""

    @pytest.fixture
    def sim_engine(self) -> SimEngine:
        engine = SimEngine()
        engine.initialize_state(world="default")
        return engine

    @pytest.fixture
    def mock_provider(self) -> AIPlayerMockProvider:
        settings = LLMSettings(provider="stub")
        return AIPlayerMockProvider(settings)

    def test_actor_with_hybrid_strategy_uses_llm(
        self, sim_engine: SimEngine, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Actor with hybrid strategy uses LLM for complex states."""
        mock_provider.configure_responses(
            [
                {"type": "inspect", "target": "district", "confidence": 0.9},
                {"type": "stabilize", "target": "district", "confidence": 0.85},
            ]
        )

        config = LLMStrategyConfig(
            complexity_threshold_stability=0.6,
            llm_call_budget=10,
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        hybrid = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        hybrid._llm_layer = layer

        # Set low stability to trigger LLM
        sim_engine.state.environment.stability = 0.4

        actor = AIActor(
            engine=sim_engine,
            config=ActorConfig(
                strategy_type=StrategyType.HYBRID,
                tick_budget=10,
                analysis_interval=5,
                log_decisions=False,
            ),
            strategy=hybrid,
        )

        report = actor.run()

        assert report.ticks_run == 10
        assert report.strategy_type == StrategyType.HYBRID
        assert hybrid._llm_decisions > 0

    def test_actor_hybrid_budget_exhaustion(
        self, sim_engine: SimEngine, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Actor continues with rules after LLM budget exhausted."""
        config = LLMStrategyConfig(
            complexity_threshold_stability=0.6,
            llm_call_budget=2,  # Very limited budget
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        hybrid = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        hybrid._llm_layer = layer

        # Set low stability consistently
        sim_engine.state.environment.stability = 0.4

        actor = AIActor(
            engine=sim_engine,
            config=ActorConfig(
                strategy_type=StrategyType.HYBRID,
                tick_budget=30,  # Run longer than budget
                analysis_interval=5,
                log_decisions=False,
            ),
            strategy=hybrid,
        )

        report = actor.run()

        # Should complete successfully
        assert report.ticks_run == 30
        # Budget should be exhausted
        assert hybrid._llm_layer.budget.calls_used == 2
        # Should have used rules after budget exhaustion
        assert hybrid._rule_decisions > 0

    def test_actor_hybrid_telemetry_comprehensive(
        self, sim_engine: SimEngine, mock_provider: AIPlayerMockProvider
    ) -> None:
        """Actor telemetry includes LLM usage information."""
        config = LLMStrategyConfig(
            complexity_threshold_stability=0.5,
            llm_call_budget=5,
        )
        layer = create_llm_decision_layer(provider=mock_provider, config=config)

        hybrid = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        hybrid._llm_layer = layer

        sim_engine.state.environment.stability = 0.4

        actor = AIActor(
            engine=sim_engine,
            config=ActorConfig(
                strategy_type=StrategyType.HYBRID,
                tick_budget=20,
                analysis_interval=5,
                log_decisions=False,
            ),
            strategy=hybrid,
        )

        report = actor.run()

        # Check telemetry includes hybrid-specific info
        strategy_telemetry = hybrid.telemetry
        assert "llm_budget" in strategy_telemetry
        assert "llm_decisions" in strategy_telemetry
        assert "rule_decisions" in strategy_telemetry

    def test_actor_create_helper_with_hybrid(self) -> None:
        """create_actor_from_engine works with hybrid strategy."""
        config = ActorConfig(
            strategy_type=StrategyType.HYBRID,
            tick_budget=10,
            log_decisions=False,
        )

        actor = create_actor_from_engine(world="default", config=config)

        assert actor._is_local is True
        assert isinstance(actor.strategy, HybridStrategy)


# ==============================================================================
# Complexity Evaluation Tests
# ==============================================================================


class TestComplexityEvaluationScenarios:
    """Comprehensive tests for complexity evaluation logic."""

    @pytest.fixture
    def default_config(self) -> LLMStrategyConfig:
        return LLMStrategyConfig()

    def test_multiple_complexity_factors(self, default_config: LLMStrategyConfig) -> None:
        """State can trigger multiple complexity factors."""
        state = {
            "stability": 0.3,  # Critical stability
            "faction_legitimacy": {
                "faction-a": 0.2,  # Low
                "faction-b": 0.3,  # Low
                "faction-c": 0.9,  # High (creates spread)
            },
            "story_seeds": [
                {"seed_id": "crisis-1"},
                {"seed_id": "crisis-2"},
            ],
        }

        is_complex, factors = evaluate_complexity(state, default_config)

        assert is_complex is True
        assert "critical_stability" in factors
        assert "multiple_stressed_factions" in factors
        assert "faction_legitimacy_spread" in factors
        # May or may not have story seeds depending on threshold

    def test_no_complexity_all_healthy(self, default_config: LLMStrategyConfig) -> None:
        """Healthy state has no complexity factors."""
        state = {
            "stability": 0.95,
            "faction_legitimacy": {
                "faction-a": 0.8,
                "faction-b": 0.82,
            },
            "story_seeds": [],
        }

        is_complex, factors = evaluate_complexity(state, default_config)

        assert is_complex is False
        assert len(factors) == 0

    def test_edge_case_exactly_at_threshold(self) -> None:
        """Stability exactly at threshold is not complex."""
        config = LLMStrategyConfig(complexity_threshold_stability=0.5)
        state = {"stability": 0.5}  # Exactly at threshold

        is_complex, factors = evaluate_complexity(state, config)

        # At threshold should not be complex (< not <=)
        assert "critical_stability" not in factors

    def test_edge_case_just_below_threshold(self) -> None:
        """Stability just below threshold triggers complexity."""
        config = LLMStrategyConfig(complexity_threshold_stability=0.5)
        state = {"stability": 0.49}  # Just below

        is_complex, factors = evaluate_complexity(state, config)

        assert is_complex is True
        assert "critical_stability" in factors

    def test_empty_faction_legitimacy(self, default_config: LLMStrategyConfig) -> None:
        """Empty faction legitimacy doesn't trigger faction factors."""
        state = {
            "stability": 0.3,  # Complex due to stability
            "faction_legitimacy": {},
            "story_seeds": [],
        }

        is_complex, factors = evaluate_complexity(state, default_config)

        assert is_complex is True
        assert "multiple_stressed_factions" not in factors
        assert "faction_legitimacy_spread" not in factors

    def test_single_faction_no_spread(self, default_config: LLMStrategyConfig) -> None:
        """Single faction can't have spread."""
        state = {
            "stability": 0.8,
            "faction_legitimacy": {"only-faction": 0.2},  # Low but single
        }

        is_complex, factors = evaluate_complexity(state, default_config)

        assert "faction_legitimacy_spread" not in factors
        assert "multiple_stressed_factions" not in factors

    def test_story_seeds_as_list_of_dicts(self, default_config: LLMStrategyConfig) -> None:
        """Story seeds must be list of dicts to count."""
        config = LLMStrategyConfig(complexity_threshold_seeds=2)

        # List of dicts - should count
        state1 = {
            "stability": 0.8,
            "story_seeds": [{"seed_id": "a"}, {"seed_id": "b"}],
        }
        is_complex1, factors1 = evaluate_complexity(state1, config)
        assert "multiple_story_seeds" in factors1

        # List of strings - should not count as dicts
        state2 = {
            "stability": 0.8,
            "story_seeds": ["seed-a", "seed-b"],
        }
        is_complex2, factors2 = evaluate_complexity(state2, config)
        assert "multiple_story_seeds" not in factors2


# ==============================================================================
# LLM Decision Response Tests
# ==============================================================================


class TestLLMDecisionResponse:
    """Tests for LLMDecisionResponse dataclass."""

    def test_to_dict_structure(self) -> None:
        """to_dict returns expected structure."""
        intent = InspectIntent(
            session_id="test",
            target_type="district",
            target_id="industrial-tier",
        )
        response = LLMDecisionResponse(
            intent=intent,
            confidence=0.92,
            rationale="Critical stability detected",
            raw_response='{"mock": "response"}',
            latency_ms=150.5,
        )

        data = response.to_dict()

        assert data["intent_type"] == "INSPECT"
        assert data["confidence"] == 0.92
        assert data["rationale"] == "Critical stability detected"
        assert data["latency_ms"] == 150.5

    def test_confidence_rounding(self) -> None:
        """Confidence is rounded to 4 decimal places."""
        intent = NegotiateIntent(
            session_id="test",
            targets=["faction-a"],
        )
        response = LLMDecisionResponse(
            intent=intent,
            confidence=0.123456789,
            rationale="Test",
            raw_response="",
            latency_ms=100.0,
        )

        data = response.to_dict()
        assert data["confidence"] == 0.1235  # Rounded


# ==============================================================================
# Integration Scenarios
# ==============================================================================


class TestAIPlayerLLMIntegrationScenarios:
    """End-to-end integration scenarios with mocked LLM."""

    def test_100_tick_hybrid_run_no_api_calls(self) -> None:
        """100-tick run with hybrid strategy makes no real API calls."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        # Use stub provider (no real API)
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)
        config = LLMStrategyConfig(llm_call_budget=20)
        layer = LLMDecisionLayer(provider, config, session_id="test")

        hybrid = HybridStrategy(
            session_id="test",
            llm_config=config,
        )
        hybrid._llm_layer = layer

        actor = AIActor(
            engine=engine,
            config=ActorConfig(
                strategy_type=StrategyType.HYBRID,
                tick_budget=100,
                analysis_interval=10,
                log_decisions=False,
            ),
            strategy=hybrid,
        )

        report = actor.run()

        assert report.ticks_run == 100
        assert report.strategy_type == StrategyType.HYBRID
        assert report.final_stability >= 0.0

    def test_hybrid_vs_balanced_performance(self) -> None:
        """Compare hybrid and balanced strategy performance."""
        # Run with balanced
        engine1 = SimEngine()
        engine1.initialize_state(world="default")
        engine1.state.environment.stability = 0.5

        balanced_actor = AIActor(
            engine=engine1,
            config=ActorConfig(
                strategy_type=StrategyType.BALANCED,
                tick_budget=50,
                analysis_interval=10,
                log_decisions=False,
            ),
        )
        balanced_report = balanced_actor.run()

        # Run with hybrid (stub LLM)
        engine2 = SimEngine()
        engine2.initialize_state(world="default")
        engine2.state.environment.stability = 0.5

        hybrid = HybridStrategy(
            session_id="test",
            llm_config=LLMStrategyConfig(llm_call_budget=10),
        )

        hybrid_actor = AIActor(
            engine=engine2,
            config=ActorConfig(
                strategy_type=StrategyType.HYBRID,
                tick_budget=50,
                analysis_interval=10,
                log_decisions=False,
            ),
            strategy=hybrid,
        )
        hybrid_report = hybrid_actor.run()

        # Both should complete successfully
        assert balanced_report.ticks_run == 50
        assert hybrid_report.ticks_run == 50

        # Stability should be tracked
        assert 0.0 <= balanced_report.final_stability <= 1.0
        assert 0.0 <= hybrid_report.final_stability <= 1.0

    def test_strategy_factory_creates_hybrid_with_llm(self) -> None:
        """create_strategy factory creates hybrid with LLM layer."""
        llm_config = LLMStrategyConfig(llm_call_budget=15)
        strategy = create_strategy(
            StrategyType.HYBRID,
            session_id="factory-test",
            llm_config=llm_config,
        )

        assert isinstance(strategy, HybridStrategy)
        assert strategy.llm_config.llm_call_budget == 15
        assert strategy._llm_layer is not None
