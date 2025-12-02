"""Rule-based decision strategies for AI player actions.

This module provides heuristic-based strategies that evaluate simulation state
and generate prioritized lists of intents. Each strategy represents a different
playstyle approach for automated game testing and validation.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from gengine.echoes.llm.intents import (
    DeployResourceIntent,
    GameIntent,
    InspectIntent,
    IntentType,
    NegotiateIntent,
    RequestReportIntent,
)

logger = logging.getLogger("gengine.ai_player.strategies")


class StrategyType(str, Enum):
    """Available AI player strategy types."""

    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    DIPLOMATIC = "diplomatic"
    HYBRID = "hybrid"


@dataclass
class StrategyConfig:
    """Configuration for AI strategy behavior."""

    # Stability thresholds
    stability_critical: float = 0.4
    stability_low: float = 0.6
    stability_target: float = 0.8

    # Faction support thresholds
    faction_low_legitimacy: float = 0.4
    faction_critical_legitimacy: float = 0.2

    # Resource thresholds
    resource_low_capacity: float = 0.3
    resource_deploy_amount: float = 50.0

    # Action frequency (ticks between actions)
    action_interval: int = 5
    inspect_interval: int = 10

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 0.0 <= self.stability_critical <= 1.0:
            raise ValueError("stability_critical must be between 0.0 and 1.0")
        if not 0.0 <= self.stability_low <= 1.0:
            raise ValueError("stability_low must be between 0.0 and 1.0")
        if self.stability_critical >= self.stability_low:
            raise ValueError("stability_critical must be less than stability_low")
        if self.action_interval < 1:
            raise ValueError("action_interval must be at least 1")


@dataclass
class StrategyDecision:
    """Represents a decision made by a strategy."""

    intent: GameIntent
    priority: float
    rationale: str
    strategy_type: StrategyType
    tick: int = 0
    state_snapshot: dict[str, Any] = field(default_factory=dict)
    decision_source: str = "rule"  # "rule" or "llm"
    llm_confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert decision to dictionary for telemetry."""
        result = {
            "intent_type": self.intent.intent.value,
            "priority": round(self.priority, 4),
            "rationale": self.rationale,
            "strategy_type": self.strategy_type.value,
            "tick": self.tick,
            "decision_source": self.decision_source,
            "state_summary": {
                k: round(v, 4) if isinstance(v, float) else v
                for k, v in self.state_snapshot.items()
            },
        }
        if self.llm_confidence is not None:
            result["llm_confidence"] = round(self.llm_confidence, 4)
        return result


class BaseStrategy(ABC):
    """Abstract base class for AI player strategies.

    Strategies evaluate the current game state and return prioritized lists
    of intents that the AI actor can execute.
    """

    strategy_type: StrategyType

    def __init__(
        self,
        session_id: str = "ai-player",
        config: StrategyConfig | None = None,
    ) -> None:
        self._session_id = session_id
        self._config = config or StrategyConfig()
        self._last_action_tick = 0
        self._last_inspect_tick = 0

    @property
    def config(self) -> StrategyConfig:
        return self._config

    @abstractmethod
    def evaluate(
        self,
        state: dict[str, Any],
        tick: int,
    ) -> list[StrategyDecision]:
        """Evaluate state and return prioritized decisions.

        Parameters
        ----------
        state
            Current simulation state summary.
        tick
            Current tick number.

        Returns
        -------
        list[StrategyDecision]
            Decisions sorted by priority (highest first).
        """
        pass

    def _create_intent(
        self,
        intent_type: IntentType,
        **kwargs: Any,
    ) -> GameIntent:
        """Create an intent with the session ID."""
        kwargs["session_id"] = self._session_id
        if intent_type == IntentType.INSPECT:
            return InspectIntent(**kwargs)
        elif intent_type == IntentType.NEGOTIATE:
            return NegotiateIntent(**kwargs)
        elif intent_type == IntentType.DEPLOY_RESOURCE:
            return DeployResourceIntent(**kwargs)
        elif intent_type == IntentType.REQUEST_REPORT:
            return RequestReportIntent(**kwargs)
        else:
            raise ValueError(f"Unsupported intent type: {intent_type}")

    def _should_act(self, tick: int) -> bool:
        """Check if enough time has passed since last action."""
        # Allow action on first tick or after interval
        if self._last_action_tick == 0 and tick == 0:
            return True
        return tick - self._last_action_tick >= self._config.action_interval

    def _should_inspect(self, tick: int) -> bool:
        """Check if enough time has passed since last inspection."""
        # Allow inspection on first opportunity or after interval
        if self._last_inspect_tick == 0 and tick == 0:
            return True
        return tick - self._last_inspect_tick >= self._config.inspect_interval

    def _extract_state_metrics(self, state: dict[str, Any]) -> dict[str, Any]:
        """Extract key metrics from state for decision making."""
        return {
            "stability": state.get("stability", 1.0),
            "tick": state.get("tick", 0),
            "faction_count": len(state.get("faction_legitimacy", {})),
            "district_count": state.get("district_count", 0),
            "agent_count": state.get("agent_count", 0),
        }

    def _find_lowest_legitimacy_faction(
        self,
        state: dict[str, Any],
    ) -> tuple[str | None, float]:
        """Find faction with lowest legitimacy."""
        faction_legitimacy = state.get("faction_legitimacy", {})
        if not faction_legitimacy:
            return None, 1.0
        min_faction = min(faction_legitimacy.items(), key=lambda x: x[1])
        return min_faction[0], min_faction[1]

    def _find_district_needing_resources(
        self,
        state: dict[str, Any],
    ) -> str | None:
        """Find a district that needs resource deployment.

        Note: The summary API returns district count, not district list.
        This method returns a placeholder district ID when no detailed
        district data is available.
        """
        districts = state.get("districts", [])
        # If districts is an int (count), we can't iterate
        if isinstance(districts, int):
            # Return a generic target - focus district if available
            focus = state.get("focus", {})
            if isinstance(focus, dict) and focus.get("district"):
                return focus["district"]
            return None
        # If it's a list of dicts, search for one needing resources
        for district in districts:
            if isinstance(district, dict):
                capacity = district.get("resource_capacity", 1.0)
                if capacity < self._config.resource_low_capacity:
                    return district.get("id")
        return None

    def _get_first_district(self, state: dict[str, Any]) -> str:
        """Get a default district ID for targeting."""
        focus = state.get("focus", {})
        if isinstance(focus, dict) and focus.get("district"):
            return focus["district"]
        # Use city name as fallback hint
        city = state.get("city", "default")
        return f"{city}-district"

    def record_action(self, tick: int) -> None:
        """Record that an action was taken at this tick."""
        self._last_action_tick = tick

    def record_inspect(self, tick: int) -> None:
        """Record that an inspection was done at this tick."""
        self._last_inspect_tick = tick


class BalancedStrategy(BaseStrategy):
    """Balanced strategy that maintains moderate intervention levels.

    This strategy:
    - Stabilizes when stability drops below 0.6
    - Supports factions when legitimacy drops below 0.4
    - Deploys resources when capacity is low
    - Inspects periodically for situational awareness
    """

    strategy_type = StrategyType.BALANCED

    def __init__(
        self,
        session_id: str = "ai-player",
        config: StrategyConfig | None = None,
    ) -> None:
        if config is None:
            config = StrategyConfig(
                stability_low=0.6,
                stability_critical=0.4,
                faction_low_legitimacy=0.4,
                action_interval=5,
                inspect_interval=10,
            )
        super().__init__(session_id=session_id, config=config)

    def evaluate(
        self,
        state: dict[str, Any],
        tick: int,
    ) -> list[StrategyDecision]:
        """Evaluate state with balanced decision making."""
        decisions: list[StrategyDecision] = []
        state_metrics = self._extract_state_metrics(state)
        stability = state_metrics["stability"]

        # Critical stability emergency
        if stability < self._config.stability_critical:
            intent = self._create_intent(
                IntentType.DEPLOY_RESOURCE,
                resource_type="materials",
                amount=self._config.resource_deploy_amount * 2,
                target_district=self._get_most_unstable_district(state),
                purpose="emergency_stabilization",
            )
            decisions.append(
                StrategyDecision(
                    intent=intent,
                    priority=1.0,
                    rationale=(
                        f"Critical stability at {stability:.2f}, "
                        "emergency resource deployment"
                    ),
                    strategy_type=self.strategy_type,
                    tick=tick,
                    state_snapshot=state_metrics,
                )
            )

        # Low stability intervention
        elif stability < self._config.stability_low and self._should_act(tick):
            faction_id, legitimacy = self._find_lowest_legitimacy_faction(state)
            if faction_id and legitimacy < self._config.faction_low_legitimacy:
                intent = self._create_intent(
                    IntentType.NEGOTIATE,
                    targets=[faction_id],
                    goal="stabilize",
                )
                decisions.append(
                    StrategyDecision(
                        intent=intent,
                        priority=0.8,
                        rationale=(
                            f"Stability at {stability:.2f}, "
                            f"negotiating with {faction_id}"
                        ),
                        strategy_type=self.strategy_type,
                        tick=tick,
                        state_snapshot=state_metrics,
                    )
                )
            else:
                district = self._find_district_needing_resources(state)
                if district:
                    intent = self._create_intent(
                        IntentType.DEPLOY_RESOURCE,
                        resource_type="materials",
                        amount=self._config.resource_deploy_amount,
                        target_district=district,
                        purpose="stabilization",
                    )
                    decisions.append(
                        StrategyDecision(
                            intent=intent,
                            priority=0.7,
                            rationale=(
                                f"Deploying resources to {district} for stabilization"
                            ),
                            strategy_type=self.strategy_type,
                            tick=tick,
                            state_snapshot=state_metrics,
                        )
                    )

        # Faction support
        faction_id, legitimacy = self._find_lowest_legitimacy_faction(state)
        if (
            faction_id
            and legitimacy < self._config.faction_low_legitimacy
            and self._should_act(tick)
        ):
            intent = self._create_intent(
                IntentType.NEGOTIATE,
                targets=[faction_id],
                goal="increase_legitimacy",
            )
            decisions.append(
                StrategyDecision(
                    intent=intent,
                    priority=0.6,
                    rationale=(
                        f"Supporting faction {faction_id} "
                        f"with legitimacy {legitimacy:.2f}"
                    ),
                    strategy_type=self.strategy_type,
                    tick=tick,
                    state_snapshot=state_metrics,
                )
            )

        # Periodic inspection
        if self._should_inspect(tick):
            intent = self._create_intent(
                IntentType.INSPECT,
                target_type="district",
                target_id=self._get_focus_district(state),
                focus_areas=["stability", "resources"],
            )
            decisions.append(
                StrategyDecision(
                    intent=intent,
                    priority=0.3,
                    rationale="Periodic situational awareness inspection",
                    strategy_type=self.strategy_type,
                    tick=tick,
                    state_snapshot=state_metrics,
                )
            )

        # Sort by priority
        decisions.sort(key=lambda d: d.priority, reverse=True)
        return decisions

    def _get_most_unstable_district(self, state: dict[str, Any]) -> str:
        """Get the district with highest instability."""
        districts = state.get("districts", [])
        # If districts is a count (int), use focus or default
        if isinstance(districts, int) or not districts:
            focus = state.get("focus", {})
            if isinstance(focus, dict) and focus.get("district"):
                return focus["district"]
            return "default-district"
        # Find district with highest unrest or lowest stability
        worst = None
        worst_score = -1.0
        for d in districts:
            if isinstance(d, dict):
                unrest = d.get("unrest", 0.0)
                if unrest > worst_score:
                    worst_score = unrest
                    worst = d.get("id", "default-district")
        return worst or "default-district"

    def _get_focus_district(self, state: dict[str, Any]) -> str:
        """Get the current focus district or first available."""
        focus = state.get("focus", {})
        if isinstance(focus, dict) and focus.get("district"):
            return focus["district"]
        districts = state.get("districts", [])
        # If districts is a count, can't iterate
        if isinstance(districts, int):
            return "default-district"
        if districts and isinstance(districts[0], dict):
            return districts[0].get("id", "default-district")
        return "default-district"


class AggressiveStrategy(BaseStrategy):
    """Aggressive strategy focused on direct intervention.

    This strategy:
    - Acts more frequently than balanced
    - Uses higher thresholds for intervention
    - Prefers resource deployment and policy actions
    - Takes proactive stabilization measures
    """

    strategy_type = StrategyType.AGGRESSIVE

    def __init__(
        self,
        session_id: str = "ai-player",
        config: StrategyConfig | None = None,
    ) -> None:
        if config is None:
            config = StrategyConfig(
                stability_low=0.7,  # Higher threshold
                stability_critical=0.5,
                faction_low_legitimacy=0.5,  # Higher threshold
                action_interval=3,  # More frequent
                inspect_interval=8,
                resource_deploy_amount=75.0,  # Larger deployments
            )
        super().__init__(session_id=session_id, config=config)

    def evaluate(
        self,
        state: dict[str, Any],
        tick: int,
    ) -> list[StrategyDecision]:
        """Evaluate state with aggressive decision making."""
        decisions: list[StrategyDecision] = []
        state_metrics = self._extract_state_metrics(state)
        stability = state_metrics["stability"]

        # Always prioritize direct action when stability is low
        if stability < self._config.stability_low:
            # Deploy resources aggressively
            district = self._get_most_critical_district(state)
            intent = self._create_intent(
                IntentType.DEPLOY_RESOURCE,
                resource_type="energy",
                amount=self._config.resource_deploy_amount,
                target_district=district,
                purpose="aggressive_stabilization",
            )
            decisions.append(
                StrategyDecision(
                    intent=intent,
                    priority=0.95,
                    rationale=f"Aggressive intervention at stability {stability:.2f}",
                    strategy_type=self.strategy_type,
                    tick=tick,
                    state_snapshot=state_metrics,
                )
            )

        # Critical stability - double down
        if stability < self._config.stability_critical:
            districts = self._get_multiple_districts(state, 2)
            for i, district in enumerate(districts):
                intent = self._create_intent(
                    IntentType.DEPLOY_RESOURCE,
                    resource_type="materials",
                    amount=self._config.resource_deploy_amount * 1.5,
                    target_district=district,
                    purpose="critical_intervention",
                )
                decisions.append(
                    StrategyDecision(
                        intent=intent,
                        priority=1.0 - (i * 0.05),
                        rationale=(
                            f"Critical stability {stability:.2f}, "
                            "multi-district intervention"
                        ),
                        strategy_type=self.strategy_type,
                        tick=tick,
                        state_snapshot=state_metrics,
                    )
                )

        # Proactive faction management
        if self._should_act(tick):
            faction_id, legitimacy = self._find_lowest_legitimacy_faction(state)
            if faction_id and legitimacy < self._config.faction_low_legitimacy:
                intent = self._create_intent(
                    IntentType.NEGOTIATE,
                    targets=[faction_id],
                    levers={"pressure": True},
                    goal="force_compliance",
                )
                decisions.append(
                    StrategyDecision(
                        intent=intent,
                        priority=0.7,
                        rationale=(
                            f"Pressuring faction {faction_id} at {legitimacy:.2f}"
                        ),
                        strategy_type=self.strategy_type,
                        tick=tick,
                        state_snapshot=state_metrics,
                    )
                )

        # Regular inspection
        if self._should_inspect(tick):
            intent = self._create_intent(
                IntentType.INSPECT,
                target_type="district",
                target_id=self._get_most_critical_district(state),
                focus_areas=["threats", "resources", "stability"],
            )
            decisions.append(
                StrategyDecision(
                    intent=intent,
                    priority=0.4,
                    rationale="Aggressive reconnaissance",
                    strategy_type=self.strategy_type,
                    tick=tick,
                    state_snapshot=state_metrics,
                )
            )

        decisions.sort(key=lambda d: d.priority, reverse=True)
        return decisions

    def _get_most_critical_district(self, state: dict[str, Any]) -> str:
        """Get the district in most critical condition."""
        districts = state.get("districts", [])
        # If districts is a count (int), use focus or default
        if isinstance(districts, int) or not districts:
            focus = state.get("focus", {})
            if isinstance(focus, dict) and focus.get("district"):
                return focus["district"]
            return "default-district"
        # Sort by criticality
        critical = None
        worst_score = -1.0
        for d in districts:
            if isinstance(d, dict):
                unrest = d.get("unrest", 0.0)
                pollution = d.get("pollution", 0.0)
                score = unrest + pollution * 0.5
                if score > worst_score:
                    worst_score = score
                    critical = d.get("id", "default-district")
        return critical or "default-district"

    def _get_multiple_districts(
        self,
        state: dict[str, Any],
        count: int,
    ) -> list[str]:
        """Get multiple districts for simultaneous intervention."""
        districts = state.get("districts", [])
        # If districts is a count (int), return default
        if isinstance(districts, int) or not districts:
            return ["default-district"]
        result = []
        for d in districts[:count]:
            if isinstance(d, dict):
                result.append(d.get("id", "default-district"))
        return result or ["default-district"]


class DiplomaticStrategy(BaseStrategy):
    """Diplomatic strategy focused on negotiation and relationships.

    This strategy:
    - Prefers negotiation over resource deployment
    - Builds faction relationships proactively
    - Uses lower thresholds for faction support
    - Emphasizes long-term stability through diplomacy
    """

    strategy_type = StrategyType.DIPLOMATIC

    def __init__(
        self,
        session_id: str = "ai-player",
        config: StrategyConfig | None = None,
    ) -> None:
        if config is None:
            config = StrategyConfig(
                stability_low=0.55,  # Lower threshold
                stability_critical=0.35,
                faction_low_legitimacy=0.5,  # Higher threshold for support
                faction_critical_legitimacy=0.3,
                action_interval=4,
                inspect_interval=8,
                resource_deploy_amount=30.0,  # Smaller, targeted deployments
            )
        super().__init__(session_id=session_id, config=config)

    def evaluate(
        self,
        state: dict[str, Any],
        tick: int,
    ) -> list[StrategyDecision]:
        """Evaluate state with diplomatic decision making."""
        decisions: list[StrategyDecision] = []
        state_metrics = self._extract_state_metrics(state)
        stability = state_metrics["stability"]

        # Primary focus: faction relationships
        factions = state.get("faction_legitimacy", {})
        for faction_id, legitimacy in factions.items():
            is_low_legitimacy = legitimacy < self._config.faction_low_legitimacy
            if is_low_legitimacy and self._should_act(tick):
                intent = self._create_intent(
                    IntentType.NEGOTIATE,
                    targets=[faction_id],
                    levers={"cooperation": True, "mutual_benefit": True},
                    goal="build_relationship",
                )
                is_critical = legitimacy < self._config.faction_critical_legitimacy
                priority = 0.9 if is_critical else 0.7
                decisions.append(
                    StrategyDecision(
                        intent=intent,
                        priority=priority,
                        rationale=(
                            f"Building relationship with {faction_id} "
                            f"({legitimacy:.2f})"
                        ),
                        strategy_type=self.strategy_type,
                        tick=tick,
                        state_snapshot=state_metrics,
                    )
                )

        # Stability through diplomacy first
        if stability < self._config.stability_low:
            faction_id, legitimacy = self._find_lowest_legitimacy_faction(state)
            if faction_id:
                intent = self._create_intent(
                    IntentType.NEGOTIATE,
                    targets=[faction_id],
                    levers={"stability_pact": True},
                    goal="stabilize_through_cooperation",
                )
                decisions.append(
                    StrategyDecision(
                        intent=intent,
                        priority=0.85,
                        rationale=f"Diplomatic stabilization at {stability:.2f}",
                        strategy_type=self.strategy_type,
                        tick=tick,
                        state_snapshot=state_metrics,
                    )
                )

        # Only deploy resources as last resort
        if stability < self._config.stability_critical:
            district = (
                self._find_district_needing_resources(state) or "default-district"
            )
            intent = self._create_intent(
                IntentType.DEPLOY_RESOURCE,
                resource_type="materials",
                amount=self._config.resource_deploy_amount,
                target_district=district,
                purpose="critical_support",
            )
            decisions.append(
                StrategyDecision(
                    intent=intent,
                    priority=0.95,
                    rationale=(
                        f"Critical stability {stability:.2f}, "
                        "minimal resource intervention"
                    ),
                    strategy_type=self.strategy_type,
                    tick=tick,
                    state_snapshot=state_metrics,
                )
            )

        # Regular faction status check
        if self._should_inspect(tick):
            faction_id, _ = self._find_lowest_legitimacy_faction(state)
            if faction_id:
                intent = self._create_intent(
                    IntentType.INSPECT,
                    target_type="faction",
                    target_id=faction_id,
                    focus_areas=["legitimacy", "relationships", "goals"],
                )
                decisions.append(
                    StrategyDecision(
                        intent=intent,
                        priority=0.5,
                        rationale=f"Diplomatic intelligence on {faction_id}",
                        strategy_type=self.strategy_type,
                        tick=tick,
                        state_snapshot=state_metrics,
                    )
                )

        decisions.sort(key=lambda d: d.priority, reverse=True)
        return decisions


class HybridStrategy(BaseStrategy):
    """Hybrid strategy that combines rule-based and LLM-enhanced decisions.

    This strategy:
    - Routes routine decisions (inspections, simple thresholds) to rules
    - Delegates complex decisions to the LLM service
    - Enforces budget limits on LLM calls
    - Falls back to rules when budget exhausted or LLM unavailable

    Complex situations that trigger LLM evaluation:
    - Multiple factions with low legitimacy
    - Critical stability crisis
    - Multiple active story seeds
    - Large legitimacy spread between factions

    Examples
    --------
    Basic usage::

        from gengine.ai_player.strategies import HybridStrategy
        from gengine.ai_player.llm_strategy import LLMStrategyConfig

        strategy = HybridStrategy(
            session_id="test",
            llm_config=LLMStrategyConfig(llm_call_budget=10),
        )
        decisions = strategy.evaluate(state, tick)
    """

    strategy_type = StrategyType.HYBRID

    def __init__(
        self,
        session_id: str = "ai-player",
        config: StrategyConfig | None = None,
        fallback_strategy: BaseStrategy | None = None,
        llm_config: Any | None = None,
        llm_provider: Any | None = None,
    ) -> None:
        """Initialize the hybrid strategy.

        Parameters
        ----------
        session_id
            Session identifier for tracking.
        config
            Base strategy configuration.
        fallback_strategy
            Rule-based strategy to use as fallback. Defaults to BalancedStrategy.
        llm_config
            LLM strategy configuration. If None, uses defaults.
        llm_provider
            LLM provider for complex decisions. If None, uses stub provider.
        """
        if config is None:
            config = StrategyConfig(
                stability_low=0.6,
                stability_critical=0.4,
                faction_low_legitimacy=0.4,
                action_interval=5,
                inspect_interval=10,
            )
        super().__init__(session_id=session_id, config=config)

        # Set up fallback strategy
        if fallback_strategy is not None:
            self._fallback = fallback_strategy
        else:
            self._fallback = BalancedStrategy(session_id=session_id, config=config)

        # Import here to avoid circular dependency
        from .llm_strategy import (
            LLMStrategyConfig,
            create_llm_decision_layer,
        )

        # Set up LLM layer
        self._llm_config = llm_config or LLMStrategyConfig()
        self._llm_layer = create_llm_decision_layer(
            provider=llm_provider,
            config=self._llm_config,
            session_id=session_id,
        )

        # Telemetry tracking
        self._rule_decisions: int = 0
        self._llm_decisions: int = 0

    @property
    def llm_config(self) -> Any:
        """Get the LLM configuration."""
        return self._llm_config

    @property
    def llm_budget(self) -> Any:
        """Get the current LLM budget state."""
        return self._llm_layer.budget

    @property
    def telemetry(self) -> dict[str, Any]:
        """Get telemetry for hybrid strategy decisions."""
        return {
            "rule_decisions": self._rule_decisions,
            "llm_decisions": self._llm_decisions,
            "llm_budget": self._llm_layer.budget.to_dict(),
            "total_decisions": self._rule_decisions + self._llm_decisions,
        }

    def evaluate(
        self,
        state: dict[str, Any],
        tick: int,
    ) -> list[StrategyDecision]:
        """Evaluate state with hybrid rule/LLM decision making.

        Parameters
        ----------
        state
            Current simulation state summary.
        tick
            Current tick number.

        Returns
        -------
        list[StrategyDecision]
            Decisions sorted by priority (highest first).
        """
        from .llm_strategy import LLMDecisionRequest, evaluate_complexity

        state_metrics = self._extract_state_metrics(state)

        # Check if situation is complex enough for LLM
        is_complex, complexity_factors = evaluate_complexity(state, self._llm_config)

        # If not complex or budget exhausted, use rules
        if not is_complex or self._llm_layer.is_budget_exhausted():
            decisions = self._fallback.evaluate(state, tick)
            self._rule_decisions += len(decisions)
            return decisions

        # Try LLM decision
        request = LLMDecisionRequest(
            state=state,
            tick=tick,
            session_id=self._session_id,
            complexity_factors=complexity_factors,
        )

        llm_response = self._llm_layer.request_decision(request)

        if llm_response is not None:
            # LLM succeeded, create decision
            decision = StrategyDecision(
                intent=llm_response.intent,
                priority=llm_response.confidence,
                rationale=llm_response.rationale,
                strategy_type=self.strategy_type,
                tick=tick,
                state_snapshot=state_metrics,
                decision_source="llm",
                llm_confidence=llm_response.confidence,
            )
            self._llm_decisions += 1

            # Also get low-priority rule decisions for backup
            rule_decisions = self._fallback.evaluate(state, tick)
            # Lower the priority of rule decisions when LLM is primary
            for rd in rule_decisions:
                rd.priority = rd.priority * self._llm_config.rule_priority_scaling

            self._rule_decisions += len(rule_decisions)
            return [decision] + rule_decisions

        # LLM failed, fall back to rules
        decisions = self._fallback.evaluate(state, tick)
        self._rule_decisions += len(decisions)
        return decisions

    def record_action(self, tick: int) -> None:
        """Record that an action was taken at this tick."""
        super().record_action(tick)
        self._fallback.record_action(tick)

    def record_inspect(self, tick: int) -> None:
        """Record that an inspection was done at this tick."""
        super().record_inspect(tick)
        self._fallback.record_inspect(tick)


def create_strategy(
    strategy_type: StrategyType,
    session_id: str = "ai-player",
    config: StrategyConfig | None = None,
    **kwargs: Any,
) -> BaseStrategy:
    """Factory function to create a strategy instance.

    Parameters
    ----------
    strategy_type
        Type of strategy to create.
    session_id
        Session identifier for tracking.
    config
        Optional custom configuration.
    **kwargs
        Additional arguments passed to strategy constructors.
        For HYBRID: llm_config, llm_provider, fallback_strategy.

    Returns
    -------
    BaseStrategy
        Configured strategy instance.

    Raises
    ------
    ValueError
        If strategy type is unknown.
    """
    strategies: dict[StrategyType, type[BaseStrategy]] = {
        StrategyType.BALANCED: BalancedStrategy,
        StrategyType.AGGRESSIVE: AggressiveStrategy,
        StrategyType.DIPLOMATIC: DiplomaticStrategy,
        StrategyType.HYBRID: HybridStrategy,
    }

    if strategy_type not in strategies:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    if strategy_type == StrategyType.HYBRID:
        return HybridStrategy(
            session_id=session_id,
            config=config,
            llm_config=kwargs.get("llm_config"),
            llm_provider=kwargs.get("llm_provider"),
            fallback_strategy=kwargs.get("fallback_strategy"),
        )

    return strategies[strategy_type](session_id=session_id, config=config)
