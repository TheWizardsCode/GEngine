"""AI Player module for testing and validation of Echoes simulations.

The AI player is a testing and validation tool that exercises the game APIs
programmatically, enabling automated balance tuning, edge case discovery, and
playthrough validation. It uses the same public APIs as human players.
"""

from .observer import (
    ObservationReport,
    Observer,
    ObserverConfig,
    TrendAnalysis,
)

__all__ = [
    "Observer",
    "ObserverConfig",
    "ObservationReport",
    "TrendAnalysis",
]
