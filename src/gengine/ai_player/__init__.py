"""AI Player module for testing and validation of Echoes simulations.

The AI player is a testing and validation tool that exercises the game APIs
programmatically, enabling automated balance tuning, edge case discovery, and
playthrough validation. It uses the same public APIs as human players.
"""

from .actor import (
    ActionReceipt,
    ActorConfig,
    ActorReport,
    AIActor,
    create_actor_from_engine,
    create_actor_from_service,
)
from .observer import (
    ObservationReport,
    Observer,
    ObserverConfig,
    TrendAnalysis,
)
from .strategies import (
    AggressiveStrategy,
    BalancedStrategy,
    BaseStrategy,
    DiplomaticStrategy,
    StrategyConfig,
    StrategyDecision,
    StrategyType,
    create_strategy,
)

__all__ = [
    # Observer
    "Observer",
    "ObserverConfig",
    "ObservationReport",
    "TrendAnalysis",
    # Strategies
    "StrategyType",
    "StrategyConfig",
    "StrategyDecision",
    "BaseStrategy",
    "BalancedStrategy",
    "AggressiveStrategy",
    "DiplomaticStrategy",
    "create_strategy",
    # Actor
    "AIActor",
    "ActorConfig",
    "ActorReport",
    "ActionReceipt",
    "create_actor_from_engine",
    "create_actor_from_service",
]
