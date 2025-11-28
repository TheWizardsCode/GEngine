"""FastAPI application for the Echoes simulation service."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..core import GameState
from ..sim import SimEngine, TickReport
from ..sim.engine import EngineNotInitializedError

DetailName = Literal["summary", "snapshot", "district"]


class TickRequest(BaseModel):
    ticks: int = Field(1, ge=1, le=100)


class TickResponse(BaseModel):
    ticks_advanced: int
    reports: list[dict[str, Any]]


class ActionsRequest(BaseModel):
    actions: list[dict[str, Any]] = Field(default_factory=list)


class ActionsResponse(BaseModel):
    results: list[dict[str, Any]]


def create_app(
    engine: SimEngine | None = None,
    *,
    auto_world: str = "default",
) -> FastAPI:
    """Instantiate the FastAPI app backed by a ``SimEngine``."""

    sim = engine or SimEngine()
    _ensure_state(sim, auto_world)

    app = FastAPI(title="Echoes Simulation Service", version="0.1.0")

    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    @app.post("/tick", response_model=TickResponse)
    def post_tick(payload: TickRequest) -> TickResponse:
        reports = sim.advance_ticks(payload.ticks)
        return TickResponse(
            ticks_advanced=len(reports),
            reports=[_serialize_report(report) for report in reports],
        )

    @app.get("/state")
    def get_state(
        detail: DetailName = "summary",
        district_id: str | None = None,
    ) -> dict[str, Any]:
        if detail == "district" and not district_id:
            raise HTTPException(status_code=400, detail="district_id is required")
        kwargs: dict[str, Any] = {}
        if district_id:
            kwargs["district_id"] = district_id
        return {"detail": detail, "data": sim.query_view(detail, **kwargs)}

    @app.get("/metrics")
    def get_metrics() -> dict[str, Any]:
        env = sim.state.environment.model_dump()
        return {"tick": sim.state.tick, "environment": env}

    @app.post("/actions", response_model=ActionsResponse)
    def post_actions(payload: ActionsRequest) -> ActionsResponse:
        receipts = [sim.apply_action(action) for action in payload.actions]
        return ActionsResponse(results=receipts)

    return app


def _ensure_state(engine: SimEngine, world: str) -> None:
    try:
        _ = engine.state
    except EngineNotInitializedError:
        engine.initialize_state(world=world)


def _serialize_report(report: TickReport) -> dict[str, Any]:
    return {
        "tick": report.tick,
        "events": list(report.events),
        "environment": dict(report.environment),
        "districts": [dict(district) for district in report.districts],
    }
