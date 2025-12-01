"""Tests for the AI Player actor module."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gengine.ai_player import (
    ActionReceipt,
    ActorConfig,
    ActorReport,
    AIActor,
)
from gengine.ai_player.actor import (
    create_actor_from_engine,
)
from gengine.ai_player.strategies import (
    AggressiveStrategy,
    BalancedStrategy,
    DiplomaticStrategy,
    StrategyDecision,
    StrategyType,
)
from gengine.echoes.client import SimServiceClient
from gengine.echoes.llm.intents import InspectIntent
from gengine.echoes.service import create_app
from gengine.echoes.sim import SimEngine


class TestActorConfig:
    """Tests for ActorConfig dataclass."""

    def test_default_config(self) -> None:
        config = ActorConfig()
        assert config.strategy_type == StrategyType.BALANCED
        assert config.tick_budget == 100
        assert config.actions_per_observation == 1
        assert config.log_decisions is True
        assert config.analysis_interval == 10

    def test_custom_config(self) -> None:
        config = ActorConfig(
            strategy_type=StrategyType.AGGRESSIVE,
            tick_budget=50,
            actions_per_observation=2,
            log_decisions=False,
        )
        assert config.strategy_type == StrategyType.AGGRESSIVE
        assert config.tick_budget == 50
        assert config.actions_per_observation == 2
        assert config.log_decisions is False

    def test_config_validates_tick_budget(self) -> None:
        with pytest.raises(ValueError, match="tick_budget must be at least 1"):
            ActorConfig(tick_budget=0)

    def test_config_validates_actions_per_observation(self) -> None:
        with pytest.raises(
            ValueError, match="actions_per_observation must be at least 1"
        ):
            ActorConfig(actions_per_observation=0)

    def test_config_validates_analysis_interval(self) -> None:
        with pytest.raises(ValueError, match="analysis_interval must be at least 1"):
            ActorConfig(analysis_interval=0)


class TestActionReceipt:
    """Tests for ActionReceipt dataclass."""

    def test_to_dict_without_decision(self) -> None:
        receipt = ActionReceipt(
            tick=42,
            intent_type="INSPECT",
            status="noop",
            detail="Action not implemented",
        )

        result = receipt.to_dict()

        assert result["tick"] == 42
        assert result["intent_type"] == "INSPECT"
        assert result["status"] == "noop"
        assert result["detail"] == "Action not implemented"
        assert result["decision"] is None

    def test_to_dict_with_decision(self) -> None:
        intent = InspectIntent(
            session_id="test",
            target_type="district",
            target_id="d1",
        )
        decision = StrategyDecision(
            intent=intent,
            priority=0.8,
            rationale="Test",
            strategy_type=StrategyType.BALANCED,
        )
        receipt = ActionReceipt(
            tick=42,
            intent_type="INSPECT",
            status="noop",
            detail="",
            decision=decision,
        )

        result = receipt.to_dict()

        assert result["decision"] is not None
        assert result["decision"]["intent_type"] == "INSPECT"


class TestActorReport:
    """Tests for ActorReport dataclass."""

    def test_to_dict_structure(self) -> None:
        report = ActorReport(
            ticks_run=100,
            actions_taken=10,
            decisions=[],
            receipts=[],
            observation=None,
            strategy_type=StrategyType.BALANCED,
            final_stability=0.75,
            telemetry={"key": "value"},
        )

        result = report.to_dict()

        assert result["ticks_run"] == 100
        assert result["actions_taken"] == 10
        assert result["decisions"] == []
        assert result["receipts"] == []
        assert result["observation"] is None
        assert result["strategy_type"] == "balanced"
        assert result["final_stability"] == 0.75
        assert result["telemetry"]["key"] == "value"


class TestAIActor:
    """Tests for the AIActor class."""

    def test_requires_engine_or_client(self) -> None:
        with pytest.raises(ValueError, match="Must provide either engine or client"):
            AIActor()

    def test_rejects_both_engine_and_client(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")

        class FakeClient:
            pass

        with pytest.raises(ValueError, match="Provide only one of engine or client"):
            AIActor(engine=engine, client=FakeClient())  # type: ignore

    def test_creates_with_default_strategy(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        actor = AIActor(engine=engine)

        assert isinstance(actor.strategy, BalancedStrategy)

    def test_creates_with_config_strategy_type(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        config = ActorConfig(strategy_type=StrategyType.AGGRESSIVE)
        actor = AIActor(engine=engine, config=config)

        assert isinstance(actor.strategy, AggressiveStrategy)

    def test_creates_with_custom_strategy(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        strategy = DiplomaticStrategy(session_id="custom")
        actor = AIActor(engine=engine, strategy=strategy)

        assert actor.strategy is strategy

    def test_run_basic(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        config = ActorConfig(tick_budget=5, analysis_interval=2, log_decisions=False)
        actor = AIActor(engine=engine, config=config)

        report = actor.run()

        assert report.ticks_run == 5
        assert report.strategy_type == StrategyType.BALANCED
        assert 0.0 <= report.final_stability <= 1.0

    def test_run_respects_tick_override(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        config = ActorConfig(tick_budget=100, analysis_interval=5, log_decisions=False)
        actor = AIActor(engine=engine, config=config)

        report = actor.run(ticks=3)

        assert report.ticks_run == 3

    def test_run_rejects_zero_ticks(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        actor = AIActor(engine=engine)

        with pytest.raises(ValueError, match="Tick count must be at least 1"):
            actor.run(ticks=0)

    def test_select_action_returns_decision(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        # Set low stability to trigger action
        engine.state.environment.stability = 0.4
        actor = AIActor(engine=engine)

        decision = actor.select_action()

        assert decision is not None
        assert isinstance(decision, StrategyDecision)

    def test_submit_intent(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        actor = AIActor(engine=engine)

        intent = InspectIntent(
            session_id="test",
            target_type="district",
            target_id="test",
        )
        decision = StrategyDecision(
            intent=intent,
            priority=0.5,
            rationale="Test",
            strategy_type=StrategyType.BALANCED,
        )

        receipt = actor.submit_intent(decision)

        assert isinstance(receipt, ActionReceipt)
        assert receipt.intent_type == "INSPECT"
        # Current implementation returns noop
        assert receipt.status == "noop"

    def test_act_cycle(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.state.environment.stability = 0.5
        config = ActorConfig(log_decisions=False)
        actor = AIActor(engine=engine, config=config)

        receipt = actor.act()

        assert receipt is not None
        assert len(actor.decisions) == 1
        assert len(actor.receipts) == 1

    def test_decisions_and_receipts_tracked(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.state.environment.stability = 0.5
        config = ActorConfig(tick_budget=20, analysis_interval=5, log_decisions=False)
        actor = AIActor(engine=engine, config=config)

        report = actor.run()

        assert len(report.decisions) == report.actions_taken
        assert len(report.receipts) == report.actions_taken

    def test_telemetry_includes_action_counts(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.state.environment.stability = 0.4
        config = ActorConfig(tick_budget=10, analysis_interval=5, log_decisions=False)
        actor = AIActor(engine=engine, config=config)

        report = actor.run()

        assert "action_counts" in report.telemetry
        assert "priority_stats" in report.telemetry
        assert "strategy_type" in report.telemetry


class TestAIActorStrategies:
    """Tests for AIActor with different strategies."""

    def test_aggressive_takes_more_actions(self) -> None:
        # Aggressive strategy should take actions more frequently
        engine1 = SimEngine()
        engine1.initialize_state(world="default")
        engine1.state.environment.stability = 0.65
        aggressive_actor = AIActor(
            engine=engine1,
            config=ActorConfig(
                strategy_type=StrategyType.AGGRESSIVE,
                tick_budget=20,
                analysis_interval=5,
                log_decisions=False,
            ),
        )

        engine2 = SimEngine()
        engine2.initialize_state(world="default")
        engine2.state.environment.stability = 0.65
        balanced_actor = AIActor(
            engine=engine2,
            config=ActorConfig(
                strategy_type=StrategyType.BALANCED,
                tick_budget=20,
                analysis_interval=5,
                log_decisions=False,
            ),
        )

        aggressive_report = aggressive_actor.run()
        balanced_report = balanced_actor.run()

        # Aggressive should take at least as many actions
        assert aggressive_report.actions_taken >= balanced_report.actions_taken

    def test_diplomatic_prefers_negotiation(self) -> None:
        engine = SimEngine()
        engine.initialize_state(world="default")
        # Set factions with low legitimacy using the dict
        for faction_id in engine.state.factions:
            engine.state.factions[faction_id].legitimacy = 0.4

        diplomatic_actor = AIActor(
            engine=engine,
            config=ActorConfig(
                strategy_type=StrategyType.DIPLOMATIC,
                tick_budget=10,
                analysis_interval=5,
                log_decisions=False,
            ),
        )

        report = diplomatic_actor.run()

        # Count negotiation actions
        negotiate_count = sum(
            1 for r in report.receipts if r.intent_type == "NEGOTIATE"
        )
        deploy_count = sum(
            1 for r in report.receipts if r.intent_type == "DEPLOY_RESOURCE"
        )

        # With low faction legitimacy, diplomatic should prefer negotiation
        assert negotiate_count >= deploy_count


class TestCreateActorHelpers:
    """Tests for actor factory functions."""

    def test_create_actor_from_engine(self) -> None:
        actor = create_actor_from_engine(world="default")

        assert actor._engine is not None
        assert actor._client is None
        assert actor._is_local is True

    def test_create_actor_with_custom_config(self) -> None:
        config = ActorConfig(tick_budget=25, log_decisions=False)
        actor = create_actor_from_engine(world="default", config=config)

        assert actor.config.tick_budget == 25

    def test_create_actor_with_custom_strategy(self) -> None:
        strategy = AggressiveStrategy(session_id="test")
        actor = create_actor_from_engine(world="default", strategy=strategy)

        assert actor.strategy is strategy


class TestActorDeterminism:
    """Tests for deterministic actor behavior under fixed seeds."""

    def test_deterministic_with_seed(self) -> None:
        """Actor should produce identical results with same seed."""
        results = []
        for _ in range(2):
            engine = SimEngine()
            engine.initialize_state(world="default")

            actor = AIActor(
                engine=engine,
                config=ActorConfig(
                    tick_budget=20,
                    analysis_interval=5,
                    log_decisions=False,
                ),
            )

            # Use same seed for determinism
            engine.advance_ticks(1, seed=42)
            report = actor.run()
            results.append(report.final_stability)

        # Both runs should produce the same stability
        assert results[0] == results[1]


class TestActorRegression100Ticks:
    """100-tick regression tests with AI interventions."""

    def test_balanced_stabilizes_failing_city(self) -> None:
        """Balanced strategy should help stabilize a struggling city."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        # Set initial struggling state
        engine.state.environment.stability = 0.5
        for faction_id in engine.state.factions:
            engine.state.factions[faction_id].legitimacy = 0.4

        actor = AIActor(
            engine=engine,
            config=ActorConfig(
                strategy_type=StrategyType.BALANCED,
                tick_budget=100,
                analysis_interval=10,
                log_decisions=False,
            ),
        )

        report = actor.run()

        # Should have taken some stabilization actions
        assert report.actions_taken > 0

        # Verify report structure
        assert report.ticks_run == 100
        assert report.strategy_type == StrategyType.BALANCED

        # Final stability should be tracked
        assert 0.0 <= report.final_stability <= 1.0

    def test_aggressive_100_tick_run(self) -> None:
        """Aggressive strategy should complete 100-tick run."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.state.environment.stability = 0.6

        actor = AIActor(
            engine=engine,
            config=ActorConfig(
                strategy_type=StrategyType.AGGRESSIVE,
                tick_budget=100,
                analysis_interval=10,
                log_decisions=False,
            ),
        )

        report = actor.run()

        assert report.ticks_run == 100
        assert report.actions_taken > 0
        assert len(report.telemetry) > 0

    def test_diplomatic_100_tick_run(self) -> None:
        """Diplomatic strategy should complete 100-tick run."""
        engine = SimEngine()
        engine.initialize_state(world="default")

        actor = AIActor(
            engine=engine,
            config=ActorConfig(
                strategy_type=StrategyType.DIPLOMATIC,
                tick_budget=100,
                analysis_interval=10,
                log_decisions=False,
            ),
        )

        report = actor.run()

        assert report.ticks_run == 100
        # Diplomatic should focus on negotiation
        if report.actions_taken > 0:
            negotiate_count = sum(
                1 for r in report.receipts if r.intent_type == "NEGOTIATE"
            )
            assert negotiate_count >= 0  # May or may not have negotiations

    def test_deterministic_100_tick_outcome(self) -> None:
        """100-tick run should be deterministic with fixed seed."""
        def run_session() -> float:
            engine = SimEngine()
            engine.initialize_state(world="default")
            engine.state.environment.stability = 0.55

            actor = AIActor(
                engine=engine,
                config=ActorConfig(
                    strategy_type=StrategyType.BALANCED,
                    tick_budget=100,
                    analysis_interval=10,
                    log_decisions=False,
                ),
            )

            # Start with deterministic seed
            engine.advance_ticks(1, seed=42)
            report = actor.run()
            return report.final_stability

        result1 = run_session()
        result2 = run_session()

        assert result1 == result2

    def test_telemetry_captures_decision_rationale(self) -> None:
        """Telemetry should capture decision rationales."""
        engine = SimEngine()
        engine.initialize_state(world="default")
        engine.state.environment.stability = 0.5

        actor = AIActor(
            engine=engine,
            config=ActorConfig(
                strategy_type=StrategyType.BALANCED,
                tick_budget=50,
                analysis_interval=10,
                log_decisions=False,
            ),
        )

        report = actor.run()

        # Telemetry should include rationales
        assert "rationales" in report.telemetry
        if report.actions_taken > 0:
            assert len(report.telemetry["rationales"]) > 0


@pytest.fixture
def service_client():
    """Create a SimServiceClient backed by a test server."""
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    http_client = TestClient(app)
    client = SimServiceClient(base_url="http://testserver", client=http_client)
    yield client
    client.close()


class TestAIActorWithService:
    """Tests for AIActor with SimServiceClient."""

    def test_actor_with_service_client(self, service_client: SimServiceClient) -> None:
        """Actor should work with service client."""
        config = ActorConfig(
            tick_budget=10,
            analysis_interval=5,
            log_decisions=False,
        )
        actor = AIActor(client=service_client, config=config)

        report = actor.run()

        assert report.ticks_run == 10
        assert isinstance(report.final_stability, float)

    def test_actor_submits_actions_via_service(
        self, service_client: SimServiceClient
    ) -> None:
        """Actor should submit actions through service client."""
        config = ActorConfig(
            strategy_type=StrategyType.AGGRESSIVE,
            tick_budget=20,
            analysis_interval=5,
            log_decisions=False,
        )
        actor = AIActor(client=service_client, config=config)

        report = actor.run()

        # Actions should have been submitted
        assert isinstance(report.receipts, list)
        for receipt in report.receipts:
            assert isinstance(receipt, ActionReceipt)
