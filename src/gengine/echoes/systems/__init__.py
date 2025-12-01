"""Gameplay subsystems for Echoes of Emergence."""

from .agents import AgentIntent, AgentSystem
from .economy import EconomySystem, EconomyReport
from .factions import FactionAction, FactionSystem
from .environment import EnvironmentImpact, EnvironmentSystem
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
