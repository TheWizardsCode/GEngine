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
    history_window: int = Field(50, ge=1)
    capture_subsystems: bool = True


class FocusSettings(BaseModel):
    """Configuration for focus-aware narrative budgeting."""

    default_district: str | None = None
    neighborhood_size: int = Field(2, ge=0)
    focus_budget_ratio: float = Field(0.65, ge=0.0, le=1.0)
    global_floor: int = Field(2, ge=0)
    digest_size: int = Field(6, ge=1)
    history_limit: int = Field(30, ge=1)
    suppressed_preview: int = Field(5, ge=0)
    spatial_population_weight: float = Field(0.6, ge=0.0, le=1.0)
    spatial_distance_weight: float = Field(0.4, ge=0.0, le=1.0)
    adjacency_bonus: float = Field(0.1, ge=0.0)
    spatial_falloff: float = Field(10.0, ge=0.1)


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
    diffusion_rate: float = Field(0.1, ge=0.0)
    diffusion_neighbor_bias: float = Field(0.6, ge=0.0, le=1.0)
    diffusion_min_delta: float = Field(0.0005, ge=0.0)
    diffusion_max_delta: float = Field(0.02, ge=0.0)
    faction_invest_pollution_relief: float = Field(0.02, ge=0.0)
    faction_sabotage_pollution_spike: float = Field(0.025, ge=0.0)
    biodiversity_baseline: float = Field(0.65, ge=0.0, le=1.0)
    biodiversity_recovery_rate: float = Field(0.02, ge=0.0, le=1.0)
    scarcity_biodiversity_weight: float = Field(0.0004, ge=0.0)
    biodiversity_stability_weight: float = Field(0.0015, ge=0.0)
    biodiversity_stability_midpoint: float = Field(0.6, ge=0.0, le=1.0)
    biodiversity_alert_threshold: float = Field(0.35, ge=0.0, le=1.0)


class DirectorSettings(BaseModel):
    """Lightweight knobs for bridging narrator output into the director."""

    history_limit: int = Field(20, ge=1)
    ranked_limit: int = Field(5, ge=1)
    spatial_preview: int = Field(4, ge=1)
    hotspot_limit: int = Field(3, ge=1)
    hotspot_score_threshold: float = Field(0.75, ge=0.0)
    travel_time_per_hop: float = Field(1.5, ge=0.0)
    travel_time_per_distance: float = Field(0.25, ge=0.0)
    travel_default_distance: float = Field(2.0, ge=0.0)
    travel_max_routes: int = Field(4, ge=1)
    story_seed_limit: int = Field(2, ge=1)
    event_history_limit: int = Field(6, ge=1)
    max_active_seeds: int = Field(1, ge=1)
    global_quiet_ticks: int = Field(4, ge=0)
    seed_active_ticks: int = Field(6, ge=0)
    seed_resolve_ticks: int = Field(4, ge=0)
    seed_quiet_ticks: int = Field(6, ge=0)
    lifecycle_history_limit: int = Field(12, ge=1)


class ProgressionSettings(BaseModel):
    """Tunable parameters for player progression systems."""

    # Base experience rates
    base_experience_rate: float = Field(1.0, ge=0.0)
    experience_per_action: float = Field(10.0, ge=0.0)
    experience_per_inspection: float = Field(5.0, ge=0.0)
    experience_per_negotiation: float = Field(15.0, ge=0.0)

    # Skill domain multipliers
    diplomacy_multiplier: float = Field(1.0, ge=0.0)
    investigation_multiplier: float = Field(1.0, ge=0.0)
    economics_multiplier: float = Field(1.0, ge=0.0)
    tactical_multiplier: float = Field(1.0, ge=0.0)
    influence_multiplier: float = Field(1.0, ge=0.0)

    # Reputation change rates
    reputation_gain_rate: float = Field(0.05, ge=0.0)
    reputation_loss_rate: float = Field(0.03, ge=0.0)

    # Level and tier thresholds
    skill_cap: int = Field(100, ge=1)
    established_threshold: int = Field(50, ge=1)
    elite_threshold: int = Field(100, ge=1)


class PerAgentProgressionSettings(BaseModel):
    """Settings for per-agent progression (layered on global progression)."""

    # Feature toggle
    enable_per_agent_modifiers: bool = Field(False)

    # Expertise settings
    expertise_max_pips: int = Field(5, ge=1, le=10)
    expertise_gain_per_success: int = Field(1, ge=0, le=5)

    # Reliability settings
    reliability_gain_per_success: float = Field(0.05, ge=0.0, le=0.5)
    reliability_loss_per_failure: float = Field(0.08, ge=0.0, le=0.5)

    # Stress settings
    stress_gain_per_failure: float = Field(0.1, ge=0.0, le=0.5)
    stress_gain_per_hazardous: float = Field(0.05, ge=0.0, le=0.3)
    stress_recovery_per_tick: float = Field(0.02, ge=0.0, le=0.2)

    # Success modifier bounds (keep small to avoid destabilizing difficulty)
    max_expertise_bonus: float = Field(0.1, ge=0.0, le=0.25)
    max_stress_penalty: float = Field(0.1, ge=0.0, le=0.25)


class CampaignSettings(BaseModel):
    """Settings for campaign management and autosave."""

    campaigns_dir: str = Field("campaigns")
    autosave_interval: int = Field(50, ge=0)
    max_autosaves: int = Field(3, ge=1)
    generate_postmortem_on_end: bool = Field(True)


class SimulationConfig(BaseModel):
    limits: SimulationLimits = Field(default_factory=SimulationLimits)
    lod: LodSettings = Field(default_factory=LodSettings)
    profiling: ProfilingSettings = Field(default_factory=ProfilingSettings)
    focus: FocusSettings = Field(default_factory=FocusSettings)
    director: DirectorSettings = Field(default_factory=DirectorSettings)
    economy: EconomySettings = Field(default_factory=EconomySettings)
    environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings)
    progression: ProgressionSettings = Field(default_factory=ProgressionSettings)
    per_agent_progression: PerAgentProgressionSettings = Field(
        default_factory=PerAgentProgressionSettings
    )
    campaign: CampaignSettings = Field(default_factory=CampaignSettings)


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
    "DirectorSettings",
    "EconomySettings",
    "FocusSettings",
    "EnvironmentSettings",
    "ProgressionSettings",
    "PerAgentProgressionSettings",
    "CampaignSettings",
    "load_simulation_config",
]
