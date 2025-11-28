"""Echoes of Emergence simulation package."""

from .client import SimServiceClient
from .core.state import GameState
from .service import create_app as create_service_app
from .settings import SimulationConfig, load_simulation_config
from .sim import SimEngine, TickReport, advance_ticks
from .systems import AgentSystem, EconomySystem, FactionSystem

__all__ = [
	"GameState",
	"SimEngine",
	"TickReport",
	"advance_ticks",
	"SimServiceClient",
	"create_service_app",
	"AgentSystem",
	"FactionSystem",
	"EconomySystem",
	"SimulationConfig",
	"load_simulation_config",
]
