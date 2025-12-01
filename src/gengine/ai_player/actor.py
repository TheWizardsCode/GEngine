"""AI Actor that selects and submits actions based on strategy decisions.

The AIActor wraps the Observer for state analysis and uses a Strategy to
determine actions. It submits intents via the simulation API and logs all
decisions for telemetry and replay.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from gengine.echoes.client import SimServiceClient
from gengine.echoes.sim import SimEngine

from .observer import ObservationReport, Observer, ObserverConfig
from .strategies import (
    BaseStrategy,
    StrategyConfig,
    StrategyDecision,
    StrategyType,
    create_strategy,
)

logger = logging.getLogger("gengine.ai_player.actor")


@dataclass
class ActionReceipt:
    """Receipt for a submitted action."""

    tick: int
    intent_type: str
    status: str
    detail: str
    decision: StrategyDecision | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "intent_type": self.intent_type,
            "status": self.status,
            "detail": self.detail,
            "decision": self.decision.to_dict() if self.decision else None,
        }


@dataclass
class ActorConfig:
    """Configuration for the AI Actor."""

    strategy_type: StrategyType = StrategyType.BALANCED
    tick_budget: int = 100
    actions_per_observation: int = 1
    log_decisions: bool = True
    analysis_interval: int = 10
    strategy_config: StrategyConfig | None = None

    def __post_init__(self) -> None:
        if self.tick_budget < 1:
            raise ValueError("tick_budget must be at least 1")
        if self.actions_per_observation < 1:
            raise ValueError("actions_per_observation must be at least 1")
        if self.analysis_interval < 1:
            raise ValueError("analysis_interval must be at least 1")


@dataclass
class ActorReport:
    """Report from an actor session."""

    ticks_run: int
    actions_taken: int
    decisions: list[StrategyDecision]
    receipts: list[ActionReceipt]
    observation: ObservationReport | None
    strategy_type: StrategyType
    final_stability: float
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticks_run": self.ticks_run,
            "actions_taken": self.actions_taken,
            "decisions": [d.to_dict() for d in self.decisions],
            "receipts": [r.to_dict() for r in self.receipts],
            "observation": self.observation.to_dict() if self.observation else None,
            "strategy_type": self.strategy_type.value,
            "final_stability": round(self.final_stability, 4),
            "telemetry": self.telemetry,
        }


class AIActor:
    """AI Actor that observes, decides, and acts on the simulation.

    The actor combines observation analysis with strategy-based decision making
    to autonomously interact with the simulation. It logs all decisions for
    debugging, replay, and telemetry analysis.

    Examples
    --------
    Local engine mode::

        from gengine.echoes.sim import SimEngine
        from gengine.ai_player import AIActor, ActorConfig
        from gengine.ai_player.strategies import StrategyType

        engine = SimEngine()
        engine.initialize_state(world="default")
        config = ActorConfig(
            strategy_type=StrategyType.BALANCED,
            tick_budget=50,
        )
        actor = AIActor(engine=engine, config=config)
        report = actor.run()
        print(f"Actions taken: {report.actions_taken}")
        print(f"Final stability: {report.final_stability}")

    With custom strategy::

        from gengine.ai_player.strategies import AggressiveStrategy, StrategyConfig

        strategy = AggressiveStrategy(
            session_id="test-session",
            config=StrategyConfig(stability_low=0.7),
        )
        actor = AIActor(engine=engine, strategy=strategy)
        report = actor.run(ticks=100)
    """

    def __init__(
        self,
        *,
        engine: SimEngine | None = None,
        client: SimServiceClient | None = None,
        config: ActorConfig | None = None,
        strategy: BaseStrategy | None = None,
    ) -> None:
        if engine is None and client is None:
            raise ValueError("Must provide either engine or client")
        if engine is not None and client is not None:
            raise ValueError("Provide only one of engine or client")

        self._engine = engine
        self._client = client
        self._config = config or ActorConfig()
        self._is_local = engine is not None

        # Create strategy
        if strategy is not None:
            self._strategy = strategy
        else:
            self._strategy = create_strategy(
                self._config.strategy_type,
                session_id="ai-actor",
                config=self._config.strategy_config,
            )

        # Create observer
        observer_config = ObserverConfig(
            tick_budget=self._config.tick_budget,
            analysis_interval=self._config.analysis_interval,
            log_natural_language=self._config.log_decisions,
        )
        if self._is_local:
            self._observer = Observer(engine=engine, config=observer_config)
        else:
            self._observer = Observer(client=client, config=observer_config)

        # Decision tracking
        self._decisions: list[StrategyDecision] = []
        self._receipts: list[ActionReceipt] = []
        self._current_tick = 0

    @property
    def config(self) -> ActorConfig:
        return self._config

    @property
    def strategy(self) -> BaseStrategy:
        return self._strategy

    @property
    def decisions(self) -> list[StrategyDecision]:
        return list(self._decisions)

    @property
    def receipts(self) -> list[ActionReceipt]:
        return list(self._receipts)

    def run(self, ticks: int | None = None) -> ActorReport:
        """Run the actor for the specified number of ticks.

        The actor alternates between:
        1. Advancing simulation ticks
        2. Analyzing state
        3. Making decisions
        4. Submitting actions

        Parameters
        ----------
        ticks
            Number of ticks to run. If None, uses config.tick_budget.

        Returns
        -------
        ActorReport
            Summary of the actor session including decisions and outcomes.
        """
        tick_count = ticks if ticks is not None else self._config.tick_budget
        if tick_count < 1:
            raise ValueError("Tick count must be at least 1")

        self._decisions.clear()
        self._receipts.clear()

        initial_state = self._get_state()
        self._current_tick = initial_state.get("tick", 0)
        start_tick = self._current_tick

        ticks_advanced = 0
        remaining = tick_count

        while remaining > 0:
            batch_size = min(remaining, self._config.analysis_interval)

            # Advance ticks
            self._advance_ticks(batch_size)
            ticks_advanced += batch_size
            remaining -= batch_size

            # Get current state
            state = self._get_state()
            self._current_tick = state.get("tick", self._current_tick + batch_size)

            # Evaluate strategy and take actions
            decisions = self._strategy.evaluate(state, self._current_tick)

            # Take top N actions
            actions_to_take = min(len(decisions), self._config.actions_per_observation)
            for decision in decisions[:actions_to_take]:
                receipt = self._submit_action(decision)
                self._decisions.append(decision)
                self._receipts.append(receipt)

                if self._config.log_decisions:
                    logger.info(
                        "Actor decision: tick=%d intent=%s priority=%.2f "
                        "rationale='%s'",
                        self._current_tick,
                        decision.intent.intent.value,
                        decision.priority,
                        decision.rationale,
                    )

        # Final state
        final_state = self._get_state()
        final_stability = final_state.get("stability", 1.0)

        # Generate observation report for the period
        observation = None
        if self._decisions:
            # Create a summary observation
            observation = self._create_observation_summary(
                start_tick,
                self._current_tick,
                ticks_advanced,
            )

        return ActorReport(
            ticks_run=ticks_advanced,
            actions_taken=len(self._receipts),
            decisions=list(self._decisions),
            receipts=list(self._receipts),
            observation=observation,
            strategy_type=self._strategy.strategy_type,
            final_stability=final_stability,
            telemetry=self._build_telemetry(final_state),
        )

    def select_action(
        self,
        state: dict[str, Any] | None = None,
    ) -> StrategyDecision | None:
        """Select the highest priority action for the current state.

        Parameters
        ----------
        state
            Optional state to evaluate. If None, fetches current state.

        Returns
        -------
        StrategyDecision | None
            The highest priority decision, or None if no action is recommended.
        """
        if state is None:
            state = self._get_state()

        tick = state.get("tick", 0)
        decisions = self._strategy.evaluate(state, tick)

        if decisions:
            return decisions[0]
        return None

    def submit_intent(
        self,
        decision: StrategyDecision,
    ) -> ActionReceipt:
        """Submit an intent based on a strategy decision.

        Parameters
        ----------
        decision
            The decision containing the intent to submit.

        Returns
        -------
        ActionReceipt
            Receipt with status and details from the submission.
        """
        return self._submit_action(decision)

    def act(self) -> ActionReceipt | None:
        """Perform a single observe-decide-act cycle.

        Returns
        -------
        ActionReceipt | None
            Receipt from the action, or None if no action was taken.
        """
        state = self._get_state()
        tick = state.get("tick", 0)

        decision = self.select_action(state)
        if decision is None:
            return None

        receipt = self.submit_intent(decision)

        self._decisions.append(decision)
        self._receipts.append(receipt)

        if self._config.log_decisions:
            logger.info(
                "Actor act: tick=%d intent=%s status=%s",
                tick,
                decision.intent.intent.value,
                receipt.status,
            )

        return receipt

    def _get_state(self) -> dict[str, Any]:
        """Fetch current simulation state."""
        if self._is_local:
            assert self._engine is not None
            return self._engine.query_view("summary")
        else:
            assert self._client is not None
            response = self._client.state("summary")
            if "data" in response:
                return response["data"]
            return response

    def _advance_ticks(self, count: int) -> dict[str, Any]:
        """Advance simulation by count ticks."""
        if self._is_local:
            assert self._engine is not None
            reports = self._engine.advance_ticks(count)
            return {"ticks_advanced": len(reports)}
        else:
            assert self._client is not None
            return self._client.tick(count)

    def _submit_action(self, decision: StrategyDecision) -> ActionReceipt:
        """Submit an action to the simulation."""
        intent_dict = decision.intent.model_dump()

        if self._is_local:
            assert self._engine is not None
            result = self._engine.apply_action(intent_dict)
        else:
            assert self._client is not None
            result = self._client.submit_actions([intent_dict])

        # Update strategy state
        if decision.intent.intent.value == "INSPECT":
            self._strategy.record_inspect(self._current_tick)
        else:
            self._strategy.record_action(self._current_tick)

        return ActionReceipt(
            tick=self._current_tick,
            intent_type=decision.intent.intent.value,
            status=result.get("status", "unknown"),
            detail=result.get("detail", ""),
            decision=decision,
        )

    def _create_observation_summary(
        self,
        start_tick: int,
        end_tick: int,
        ticks_observed: int,
    ) -> ObservationReport | None:
        """Create a summary observation report."""
        from .observer import TrendAnalysis

        state = self._get_state()

        # Extract stability
        stability = state.get("stability", 1.0)
        stability_trend = TrendAnalysis(
            metric_name="stability",
            start_value=1.0,  # Assumed start
            end_value=stability,
            delta=stability - 1.0,
            trend="stable" if abs(stability - 1.0) < 0.01 else (
                "increasing" if stability > 1.0 else "decreasing"
            ),
        )

        # Extract faction swings
        faction_swings = {}
        for fid, leg in state.get("faction_legitimacy", {}).items():
            faction_swings[fid] = TrendAnalysis(
                metric_name=f"faction_{fid}_legitimacy",
                start_value=0.5,  # Assumed start
                end_value=leg,
                delta=leg - 0.5,
                trend="stable" if abs(leg - 0.5) < 0.05 else (
                    "increasing" if leg > 0.5 else "decreasing"
                ),
            )

        return ObservationReport(
            ticks_observed=ticks_observed,
            start_tick=start_tick,
            end_tick=end_tick,
            stability_trend=stability_trend,
            faction_swings=faction_swings,
            story_seeds_activated=[],
            alerts=[],
            commentary=[],
            environment_summary={
                "stability": stability,
                "action_count": len(self._receipts),
            },
        )

    def _build_telemetry(self, final_state: dict[str, Any]) -> dict[str, Any]:
        """Build telemetry data for the session."""
        action_counts: dict[str, int] = {}
        for receipt in self._receipts:
            intent_type = receipt.intent_type
            action_counts[intent_type] = action_counts.get(intent_type, 0) + 1

        priority_stats = {
            "avg_priority": 0.0,
            "max_priority": 0.0,
            "min_priority": 1.0,
        }
        if self._decisions:
            priorities = [d.priority for d in self._decisions]
            priority_stats["avg_priority"] = sum(priorities) / len(priorities)
            priority_stats["max_priority"] = max(priorities)
            priority_stats["min_priority"] = min(priorities)

        return {
            "action_counts": action_counts,
            "priority_stats": {
                k: round(v, 4) for k, v in priority_stats.items()
            },
            "strategy_type": self._strategy.strategy_type.value,
            "final_state": {
                "stability": final_state.get("stability", 1.0),
                "tick": final_state.get("tick", 0),
            },
            "rationales": [d.rationale for d in self._decisions[-10:]],
        }


def create_actor_from_engine(
    world: str = "default",
    config: ActorConfig | None = None,
    strategy: BaseStrategy | None = None,
) -> AIActor:
    """Create an AIActor with a fresh local SimEngine.

    Parameters
    ----------
    world
        World bundle to load.
    config
        Optional actor configuration.
    strategy
        Optional custom strategy.

    Returns
    -------
    AIActor
        Configured actor ready for sessions.
    """
    engine = SimEngine()
    engine.initialize_state(world=world)
    return AIActor(engine=engine, config=config, strategy=strategy)


def create_actor_from_service(
    base_url: str,
    config: ActorConfig | None = None,
    strategy: BaseStrategy | None = None,
) -> AIActor:
    """Create an AIActor connected to a remote simulation service.

    Parameters
    ----------
    base_url
        URL of the simulation service.
    config
        Optional actor configuration.
    strategy
        Optional custom strategy.

    Returns
    -------
    AIActor
        Configured actor ready for sessions.
    """
    client = SimServiceClient(base_url)
    return AIActor(client=client, config=config, strategy=strategy)
