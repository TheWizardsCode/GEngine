"""Domain models for the Echoes of Emergence simulation."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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


class District(BaseModel):
    """A single district within the city."""

    id: str = Field(..., min_length=1)
    name: str
    population: int = Field(..., ge=0)
    resources: Dict[str, ResourceStock] = Field(default_factory=dict)
    modifiers: DistrictModifiers = Field(default_factory=DistrictModifiers)

    model_config = {"validate_assignment": True}


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
