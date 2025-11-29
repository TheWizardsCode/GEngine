"""Domain models for the Echoes of Emergence simulation."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ResourceStock(BaseModel):
    """Represents the availability of a single resource inside a district."""

    type: str = Field(..., min_length=1)
    capacity: int = Field(..., ge=0)
    current: int = Field(..., ge=0)
    regen: float = Field(0.0, ge=0.0)

    model_config = {"validate_assignment": True}

    @field_validator("current")
    @classmethod
    def _current_not_above_capacity(cls, value: int, info):  # type: ignore[override]
        capacity = info.data.get("capacity")
        if capacity is not None and value > capacity:
            raise ValueError("current stock cannot exceed capacity")
        return value


class DistrictModifiers(BaseModel):
    """Continuous modifiers that influence subsystem behavior per district."""

    pollution: float = Field(0.5, ge=0.0, le=1.0)
    unrest: float = Field(0.5, ge=0.0, le=1.0)
    prosperity: float = Field(0.5, ge=0.0, le=1.0)
    security: float = Field(0.5, ge=0.0, le=1.0)

    model_config = {"validate_assignment": True}

class DistrictCoordinates(BaseModel):
    """Planar or 3D coordinates for a district."""

    x: float
    y: float
    z: float | None = None

    model_config = {"validate_assignment": True}


class District(BaseModel):
    """A single district within the city."""

    id: str = Field(..., min_length=1)
    name: str
    population: int = Field(..., ge=0)
    resources: Dict[str, ResourceStock] = Field(default_factory=dict)
    modifiers: DistrictModifiers = Field(default_factory=DistrictModifiers)
    coordinates: DistrictCoordinates | None = None
    adjacent: List[str] = Field(default_factory=list)

    model_config = {"validate_assignment": True}

    @field_validator("adjacent")
    @classmethod
    def _dedupe_adjacent(cls, values: List[str]) -> List[str]:  # type: ignore[override]
        ordered: List[str] = []
        for neighbor in values:
            if neighbor not in ordered:
                ordered.append(neighbor)
        return ordered


class StorySeedTrigger(BaseModel):
    """Activation criteria for an authored story seed."""

    district_id: str | None = None
    scope: str | None = None
    min_score: float = Field(0.5, ge=0.0)
    min_severity: float = Field(0.5, ge=0.0)
    max_focus_distance: int | None = Field(default=None, ge=0)
    min_suppressed: int = Field(0, ge=0)

    model_config = {"validate_assignment": True}


class StorySeedRoles(BaseModel):
    """Lists of authored participants a seed prefers to attach to."""

    agents: List[str] = Field(default_factory=list)
    factions: List[str] = Field(default_factory=list)

    model_config = {"validate_assignment": True}


class StorySeedResolutionTemplates(BaseModel):
    """Text snippets describing possible outcomes for a seed."""

    success: str
    failure: str
    partial: str | None = None

    model_config = {"validate_assignment": True}


class StorySeedTravelHint(BaseModel):
    """Optional pointer that helps the director bias travel costs."""

    district_id: str | None = None
    max_focus_distance: int | None = Field(default=None, ge=0)

    model_config = {"validate_assignment": True}

    @model_validator(mode="after")
    def _ensure_target(self) -> "StorySeedTravelHint":
        if self.district_id is None and self.max_focus_distance is None:
            raise ValueError("travel hint must set district_id or max_focus_distance")
        return self


class StorySeed(BaseModel):
    """Authored narrative seed triggered by hotspot conditions."""

    id: str = Field(..., min_length=1)
    title: str
    summary: str
    stakes: str
    scope: str = "district"
    tags: List[str] = Field(default_factory=list)
    preferred_districts: List[str] = Field(default_factory=list)
    cooldown_ticks: int = Field(30, ge=0)
    triggers: List[StorySeedTrigger] = Field(default_factory=list)
    roles: StorySeedRoles = Field(default_factory=StorySeedRoles)
    beats: List[str] = Field(default_factory=list)
    resolution_templates: StorySeedResolutionTemplates
    travel_hint: StorySeedTravelHint | None = None
    followups: List[str] = Field(default_factory=list)

    model_config = {"validate_assignment": True}

    @field_validator("triggers")
    @classmethod
    def _validate_triggers(cls, value: List[StorySeedTrigger]) -> List[StorySeedTrigger]:  # type: ignore[override]
        if not value:
            raise ValueError("story seed must define at least one trigger")
        return value


class Faction(BaseModel):
    """Political or social group that acts across multiple districts."""

    id: str = Field(..., min_length=1)
    name: str
    ideology: Optional[str] = None
    legitimacy: float = Field(0.5, ge=0.0, le=1.0)
    resources: Dict[str, int] = Field(default_factory=dict)
    territory: List[str] = Field(default_factory=list)
    description: Optional[str] = None

    model_config = {"validate_assignment": True}


class Agent(BaseModel):
    """An individual character operating inside the simulation."""

    id: str = Field(..., min_length=1)
    name: str
    role: str
    faction_id: Optional[str] = None
    home_district: Optional[str] = None
    traits: Dict[str, float] = Field(default_factory=dict)
    needs: Dict[str, float] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    model_config = {"validate_assignment": True}


class EnvironmentState(BaseModel):
    """City-wide environment and stability metrics."""

    stability: float = Field(0.5, ge=0.0, le=1.0)
    unrest: float = Field(0.5, ge=0.0, le=1.0)
    pollution: float = Field(0.5, ge=0.0, le=1.0)
    biodiversity: float = Field(0.6, ge=0.0, le=1.0)
    climate_risk: float = Field(0.5, ge=0.0, le=1.0)
    security: float = Field(0.5, ge=0.0, le=1.0)

    model_config = {"validate_assignment": True}


class City(BaseModel):
    """Top-level container for the playable area."""

    id: str = Field(..., min_length=1)
    name: str
    description: Optional[str] = None
    districts: List[District]

    model_config = {"validate_assignment": True}

    @model_validator(mode="after")
    def _normalize_adjacency(self) -> "City":
        lookup = {district.id for district in self.districts}
        for district in self.districts:
            filtered: List[str] = []
            for neighbor in district.adjacent:
                if neighbor == district.id or neighbor not in lookup:
                    continue
                if neighbor not in filtered:
                    filtered.append(neighbor)
            district.adjacent = filtered
        return self
