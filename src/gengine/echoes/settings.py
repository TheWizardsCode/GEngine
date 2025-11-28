"""Simulation configuration and safeguard settings for Echoes."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Literal

import yaml
from pydantic import BaseModel, Field

_CONFIG_ENV_VAR = "ECHOES_CONFIG_ROOT"
_DEFAULT_CONFIG_NAME = "simulation"


class SimulationLimits(BaseModel):
    """Guardrails that keep the CLI and service responsive."""

    engine_max_ticks: int = Field(200, ge=1)
    cli_run_cap: int = Field(50, ge=1)
    cli_script_command_cap: int = Field(200, ge=1)
    service_tick_cap: int = Field(100, ge=1)


class LodSettings(BaseModel):
    """Level-of-detail tuning that trades fidelity for stability when needed."""

    mode: Literal["detailed", "balanced", "coarse"] = "balanced"
    volatility_scale: Dict[str, float] = Field(
        default_factory=lambda: {"detailed": 1.0, "balanced": 0.75, "coarse": 0.45}
    )
    max_events_per_tick: int = Field(6, ge=1)

    @property
    def scale(self) -> float:
        return self.volatility_scale.get(self.mode, 0.75)


class ProfilingSettings(BaseModel):
    log_ticks: bool = True


class SimulationConfig(BaseModel):
    limits: SimulationLimits = Field(default_factory=SimulationLimits)
    lod: LodSettings = Field(default_factory=LodSettings)
    profiling: ProfilingSettings = Field(default_factory=ProfilingSettings)


def _default_config_root() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "content" / "config"


def load_simulation_config(
    config_name: str = _DEFAULT_CONFIG_NAME,
    *,
    config_root: Path | None = None,
) -> SimulationConfig:
    """Load the simulation config from ``content/config`` (or override path)."""

    root = config_root or Path(os.environ.get(_CONFIG_ENV_VAR, _default_config_root()))
    path = root / f"{config_name}.yml"
    if not path.exists():
        return SimulationConfig()
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError("Simulation config root must be a mapping")
    return SimulationConfig.model_validate(raw)


__all__ = [
    "SimulationConfig",
    "SimulationLimits",
    "LodSettings",
    "ProfilingSettings",
    "load_simulation_config",
]
