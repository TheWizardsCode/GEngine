"""LLM-enhanced decision layer for AI player strategies.

This module provides the bridge between AI player strategies and the LLM service,
enabling complex game decisions to be delegated to language models while maintaining
budget controls and fallback mechanisms.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from gengine.echoes.llm.intents import (
    DeployResourceIntent,
    GameIntent,
    InspectIntent,
    NegotiateIntent,
    RequestReportIntent,
)
from gengine.echoes.llm.providers import LLMProvider, StubProvider
from gengine.echoes.llm.settings import LLMSettings

logger = logging.getLogger("gengine.ai_player.llm_strategy")


@dataclass
class LLMStrategyConfig:
    """Configuration for LLM-enhanced strategy behavior.

    Attributes
    ----------
    llm_call_budget
        Maximum LLM calls allowed per session. Set to 0 for unlimited.
    complexity_threshold_factions
        Number of factions with low legitimacy to trigger LLM.
    complexity_threshold_legitimacy
        Legitimacy level below which a faction is considered stressed.
    complexity_threshold_stability
        Stability level below which situation is considered critical.
    complexity_threshold_seeds
        Number of active story seeds to trigger LLM evaluation.
    complexity_threshold_legitimacy_spread
        Legitimacy spread between factions to trigger LLM evaluation.
    cost_per_call_estimate
        Estimated cost per LLM call for budget tracking.
    llm_timeout_seconds
        Timeout for LLM calls.
    fallback_on_error
        Whether to use rule-based fallback on LLM errors.
    rule_priority_scaling
        Scaling factor for rule decision priorities when LLM is primary.
    """

    llm_call_budget: int = 10
    complexity_threshold_factions: int = 2
    complexity_threshold_legitimacy: float = 0.4
    complexity_threshold_stability: float = 0.5
    complexity_threshold_seeds: int = 2
    complexity_threshold_legitimacy_spread: float = 0.3
    cost_per_call_estimate: float = 0.01
    llm_timeout_seconds: float = 10.0
    fallback_on_error: bool = True
    rule_priority_scaling: float = 0.5

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.llm_call_budget < 0:
            raise ValueError("llm_call_budget cannot be negative")
        if not 0.0 <= self.complexity_threshold_legitimacy <= 1.0:
            raise ValueError(
                "complexity_threshold_legitimacy must be between 0.0 and 1.0"
            )
        if not 0.0 <= self.complexity_threshold_stability <= 1.0:
            raise ValueError(
                "complexity_threshold_stability must be between 0.0 and 1.0"
            )
        if not 0.0 <= self.complexity_threshold_legitimacy_spread <= 1.0:
            raise ValueError(
                "complexity_threshold_legitimacy_spread must be between 0.0 and 1.0"
            )
        if self.llm_timeout_seconds <= 0:
            raise ValueError("llm_timeout_seconds must be positive")
        if not 0.0 <= self.rule_priority_scaling <= 1.0:
            raise ValueError(
                "rule_priority_scaling must be between 0.0 and 1.0"
            )


@dataclass
class LLMBudgetState:
    """Tracks LLM usage for budget enforcement.

    Attributes
    ----------
    calls_used
        Number of LLM calls made this session.
    estimated_cost
        Running estimate of API costs.
    fallback_count
        Number of times fallback was triggered.
    last_call_latency_ms
        Latency of the most recent LLM call.
    """

    calls_used: int = 0
    estimated_cost: float = 0.0
    fallback_count: int = 0
    last_call_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for telemetry."""
        return {
            "calls_used": self.calls_used,
            "estimated_cost": round(self.estimated_cost, 4),
            "fallback_count": self.fallback_count,
            "last_call_latency_ms": round(self.last_call_latency_ms, 2),
        }


@dataclass
class LLMDecisionRequest:
    """Request for LLM-based decision making.

    Attributes
    ----------
    state
        Current simulation state summary.
    tick
        Current tick number.
    session_id
        Session identifier for tracking.
    complexity_factors
        List of factors that triggered LLM evaluation.
    context_history
        Recent decisions for context.
    """

    state: dict[str, Any]
    tick: int
    session_id: str
    complexity_factors: list[str] = field(default_factory=list)
    context_history: list[str] = field(default_factory=list)

    def to_prompt_context(self) -> dict[str, Any]:
        """Convert to context dictionary for prompt building."""
        return {
            "stability": self.state.get("stability", 1.0),
            "tick": self.tick,
            "faction_legitimacy": self.state.get("faction_legitimacy", {}),
            "district_count": self.state.get("district_count", 0),
            "story_seeds": self.state.get("story_seeds", []),
            "complexity_factors": self.complexity_factors,
            "recent_decisions": self.context_history[-5:],
        }


@dataclass
class LLMDecisionResponse:
    """Response from LLM decision layer.

    Attributes
    ----------
    intent
        The game intent parsed from LLM response.
    confidence
        Confidence score from LLM (0.0-1.0).
    rationale
        Explanation of the decision.
    raw_response
        Raw LLM output for debugging.
    latency_ms
        Time taken for the LLM call.
    """

    intent: GameIntent
    confidence: float
    rationale: str
    raw_response: str
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for telemetry."""
        return {
            "intent_type": self.intent.intent.value,
            "confidence": round(self.confidence, 4),
            "rationale": self.rationale,
            "latency_ms": round(self.latency_ms, 2),
        }


class LLMDecisionLayer:
    """Bridge between AI strategies and LLM providers.

    The decision layer handles:
    - Building prompts from game state
    - Calling LLM providers with timeout/retry
    - Parsing responses into valid intents
    - Budget tracking and enforcement

    Examples
    --------
    Basic usage with stub provider::

        from gengine.ai_player.llm_strategy import LLMDecisionLayer, LLMStrategyConfig
        from gengine.echoes.llm.providers import StubProvider
        from gengine.echoes.llm.settings import LLMSettings

        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)
        config = LLMStrategyConfig(llm_call_budget=5)

        layer = LLMDecisionLayer(provider, config)
        response = layer.request_decision(request)
    """

    def __init__(
        self,
        provider: LLMProvider,
        config: LLMStrategyConfig | None = None,
        session_id: str = "ai-player",
    ) -> None:
        self._provider = provider
        self._config = config or LLMStrategyConfig()
        self._session_id = session_id
        self._budget = LLMBudgetState()

    @property
    def config(self) -> LLMStrategyConfig:
        return self._config

    @property
    def budget(self) -> LLMBudgetState:
        return self._budget

    def is_budget_exhausted(self) -> bool:
        """Check if LLM call budget has been exhausted."""
        if self._config.llm_call_budget == 0:
            return False  # Unlimited budget
        return self._budget.calls_used >= self._config.llm_call_budget

    def request_decision(
        self,
        request: LLMDecisionRequest,
    ) -> LLMDecisionResponse | None:
        """Request a decision from the LLM.

        Parameters
        ----------
        request
            The decision request containing state and context.

        Returns
        -------
        LLMDecisionResponse | None
            The LLM's decision, or None if budget exhausted or error occurred.
        """
        if self.is_budget_exhausted():
            logger.debug("LLM budget exhausted, skipping call")
            return None

        try:
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None and loop.is_running():
                # Already in async context - use thread to avoid nested loops
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    # Create a new event loop in the thread
                    future = executor.submit(self._run_in_new_loop, request)
                    return future.result(timeout=self._config.llm_timeout_seconds + 5)
            else:
                # No event loop running, create a new one
                return asyncio.run(self._call_llm(request))
        except Exception as e:
            logger.warning("Failed to run LLM call: %s", e)
            self._budget.fallback_count += 1
            if not self._config.fallback_on_error:
                raise
            return None

    def _run_in_new_loop(
        self,
        request: LLMDecisionRequest,
    ) -> LLMDecisionResponse | None:
        """Run the LLM call in a new event loop (for threading context)."""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(self._call_llm(request))
        finally:
            new_loop.close()

    async def _call_llm(
        self,
        request: LLMDecisionRequest,
    ) -> LLMDecisionResponse | None:
        """Internal async LLM call with timeout and error handling."""
        import time

        start_time = time.perf_counter()

        try:
            # Build context for the LLM
            context = request.to_prompt_context()

            # Build a command based on complexity factors
            command = self._build_command_from_context(request)

            # Call the provider
            result = await asyncio.wait_for(
                self._provider.parse_intent(command, context),
                timeout=self._config.llm_timeout_seconds,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Update budget tracking
            self._budget.calls_used += 1
            self._budget.estimated_cost += self._config.cost_per_call_estimate
            self._budget.last_call_latency_ms = latency_ms

            # Parse the response into an intent
            intent = self._parse_intent_from_result(result, request.session_id)

            if intent is None:
                self._budget.fallback_count += 1
                return None

            # Build rationale from LLM response
            rationale = self._build_rationale(result, request.complexity_factors)

            return LLMDecisionResponse(
                intent=intent,
                confidence=result.confidence or 0.8,
                rationale=rationale,
                raw_response=result.raw_response,
                latency_ms=latency_ms,
            )

        except asyncio.TimeoutError:
            logger.warning(
                "LLM call timed out after %.1f seconds",
                self._config.llm_timeout_seconds,
            )
            self._budget.fallback_count += 1
            return None

        except Exception as e:
            logger.warning("LLM call failed: %s", e)
            self._budget.fallback_count += 1
            if not self._config.fallback_on_error:
                raise
            return None

    def _build_command_from_context(
        self,
        request: LLMDecisionRequest,
    ) -> str:
        """Build a natural language command from the request context."""
        stability = request.state.get("stability", 1.0)
        factors = request.complexity_factors

        # Build command based on situation
        if stability < self._config.complexity_threshold_stability:
            return (
                f"The city stability is critical at {stability:.2f}. "
                "What action should we take to stabilize the situation?"
            )

        if "multiple_stressed_factions" in factors:
            factions = request.state.get("faction_legitimacy", {})
            low_factions = [
                f for f, leg in factions.items()
                if leg < self._config.complexity_threshold_legitimacy
            ]
            return (
                f"Multiple factions have low legitimacy: {', '.join(low_factions)}. "
                "How should we prioritize negotiations?"
            )

        if "multiple_story_seeds" in factors:
            seeds = request.state.get("story_seeds", [])
            seed_names = [s.get("seed_id", "unknown") for s in seeds[:3]]
            return (
                f"Multiple crises are active: {', '.join(seed_names)}. "
                "Which should we address first?"
            )

        # Default command
        return (
            f"Current stability is {stability:.2f}. "
            "Recommend the best action to maintain or improve the city."
        )

    def _parse_intent_from_result(
        self,
        result: Any,
        session_id: str,
    ) -> GameIntent | None:
        """Parse an LLM result into a GameIntent."""
        if not result or not result.intents:
            return None

        intent_data = result.intents[0]
        intent_type = intent_data.get("type", "").lower()

        try:
            if intent_type in ("inspect", "check", "observe"):
                return InspectIntent(
                    session_id=session_id,
                    target_type=intent_data.get("target", "district"),
                    target_id=intent_data.get("target_id", "default-district"),
                    focus_areas=intent_data.get("focus_areas"),
                )
            elif intent_type in ("negotiate", "talk", "diplomacy"):
                targets = intent_data.get("targets", [])
                if not targets:
                    targets = [intent_data.get("target", "default-faction")]
                return NegotiateIntent(
                    session_id=session_id,
                    targets=targets,
                    goal=intent_data.get("goal", "stabilize"),
                )
            elif intent_type in ("stabilize", "deploy", "resource"):
                return DeployResourceIntent(
                    session_id=session_id,
                    resource_type=intent_data.get("resource_type", "materials"),
                    amount=float(intent_data.get("amount", 50)),
                    target_district=intent_data.get(
                        "target_district",
                        intent_data.get("target", "default-district"),
                    ),
                    purpose="llm_recommended",
                )
            elif intent_type in ("report", "status", "summary"):
                return RequestReportIntent(
                    session_id=session_id,
                    report_type=intent_data.get("report_type", "summary"),
                )
            else:
                # Default to inspect
                return InspectIntent(
                    session_id=session_id,
                    target_type="district",
                    target_id="default-district",
                )
        except Exception as e:
            logger.warning("Failed to parse intent from LLM result: %s", e)
            return None

    def _build_rationale(
        self,
        result: Any,
        complexity_factors: list[str],
    ) -> str:
        """Build a human-readable rationale from the LLM response."""
        parts = ["LLM-assisted decision"]
        if complexity_factors:
            parts.append(f"triggered by: {', '.join(complexity_factors)}")
        if result.confidence:
            parts.append(f"confidence: {result.confidence:.2f}")
        return "; ".join(parts)


def evaluate_complexity(
    state: dict[str, Any],
    config: LLMStrategyConfig,
) -> tuple[bool, list[str]]:
    """Evaluate whether a state requires LLM-level decision making.

    Parameters
    ----------
    state
        Current simulation state summary.
    config
        LLM strategy configuration.

    Returns
    -------
    tuple[bool, list[str]]
        Whether LLM should be used, and list of complexity factors.
    """
    factors: list[str] = []

    # Check stability
    stability = state.get("stability", 1.0)
    if stability < config.complexity_threshold_stability:
        factors.append("critical_stability")

    # Check faction stress
    faction_legitimacy = state.get("faction_legitimacy", {})
    stressed_factions = sum(
        1 for leg in faction_legitimacy.values()
        if leg < config.complexity_threshold_legitimacy
    )
    if stressed_factions >= config.complexity_threshold_factions:
        factors.append("multiple_stressed_factions")

    # Check active story seeds
    story_seeds = state.get("story_seeds", [])
    if isinstance(story_seeds, list):
        active_seeds = len([s for s in story_seeds if isinstance(s, dict)])
        if active_seeds >= config.complexity_threshold_seeds:
            factors.append("multiple_story_seeds")

    # Check for conflicting faction goals
    if len(faction_legitimacy) >= 2:
        legitimacy_values = list(faction_legitimacy.values())
        if legitimacy_values:
            spread = max(legitimacy_values) - min(legitimacy_values)
            if spread > config.complexity_threshold_legitimacy_spread:
                factors.append("faction_legitimacy_spread")

    is_complex = len(factors) > 0
    return is_complex, factors


def create_llm_decision_layer(
    provider: LLMProvider | None = None,
    config: LLMStrategyConfig | None = None,
    session_id: str = "ai-player",
) -> LLMDecisionLayer:
    """Factory function to create an LLM decision layer.

    Parameters
    ----------
    provider
        LLM provider to use. If None, creates a StubProvider.
    config
        LLM strategy configuration.
    session_id
        Session identifier for tracking.

    Returns
    -------
    LLMDecisionLayer
        Configured decision layer.
    """
    if provider is None:
        settings = LLMSettings(provider="stub")
        provider = StubProvider(settings)

    return LLMDecisionLayer(
        provider=provider,
        config=config,
        session_id=session_id,
    )
