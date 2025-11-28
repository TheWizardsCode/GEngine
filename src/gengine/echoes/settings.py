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


class EconomySettings(BaseModel):
    """Tunable parameters driving the economy subsystem."""

    regen_scale: float = Field(0.8, ge=0.0)
    demand_population_scale: int = Field(100_000, ge=1)
    demand_unrest_weight: float = Field(0.3, ge=0.0)
    demand_prosperity_weight: float = Field(0.2, ge=0.0)
    base_resource_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "energy": 4.0,
            "food": 3.5,
            "water": 3.0,
            "materials": 2.5,
            "capital": 2.4,
            "data": 2.0,
        }
    )
    base_price: float = Field(1.0, ge=0.0)
    shortage_threshold: float = Field(0.2, ge=0.0, le=1.0)
    shortage_warning_ticks: int = Field(3, ge=1)
    price_increase_step: float = Field(0.05, ge=0.0)
    price_max_boost: float = Field(0.5, ge=0.0)
    price_decay: float = Field(0.03, ge=0.0)
    price_floor: float = Field(0.5, ge=0.0)


class EnvironmentSettings(BaseModel):
    """Settings that couple scarcity pressure into environment metrics."""

    scarcity_pressure_cap: int = Field(6, ge=1)
    scarcity_unrest_weight: float = Field(0.0005, ge=0.0)
    scarcity_pollution_weight: float = Field(0.0003, ge=0.0)
    district_unrest_weight: float = Field(0.0003, ge=0.0)
    district_pollution_weight: float = Field(0.0002, ge=0.0)
    scarcity_event_threshold: float = Field(1.5, ge=0.0)


class SimulationConfig(BaseModel):
    limits: SimulationLimits = Field(default_factory=SimulationLimits)
    lod: LodSettings = Field(default_factory=LodSettings)
    profiling: ProfilingSettings = Field(default_factory=ProfilingSettings)
    economy: EconomySettings = Field(default_factory=EconomySettings)
    environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings)


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
    "EconomySettings",
    "EnvironmentSettings",
    "load_simulation_config",
]
