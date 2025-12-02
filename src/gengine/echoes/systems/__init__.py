"""Gameplay subsystems for Echoes of Emergence."""

from .agents import AgentIntent, AgentSystem
from .economy import EconomyReport, EconomySystem
from .environment import EnvironmentImpact, EnvironmentSystem
from .factions import FactionAction, FactionSystem
from .progression import (
    PerAgentProgressionSettings,
    ProgressionEvent,
    ProgressionSettings,
    ProgressionSystem,
)

__all__ = [
    "AgentIntent",
    "AgentSystem",
    "FactionAction",
    "FactionSystem",
    "EconomySystem",
    "EconomyReport",
    "EnvironmentImpact",
    "EnvironmentSystem",
    "PerAgentProgressionSettings",
    "ProgressionEvent",
    "ProgressionSettings",
    "ProgressionSystem",
]
