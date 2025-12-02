"""FastAPI application for the Echoes simulation service."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..settings import SimulationConfig, load_simulation_config
from ..sim import SimEngine, TickReport
from ..sim.engine import EngineNotInitializedError

DetailName = Literal["summary", "snapshot", "district", "post-mortem"]


class TickRequest(BaseModel):
    ticks: int = Field(1, ge=1)


class TickResponse(BaseModel):
    ticks_advanced: int
    reports: list[dict[str, Any]]


class ActionsRequest(BaseModel):
    actions: list[dict[str, Any]] = Field(default_factory=list)


class ActionsResponse(BaseModel):
    results: list[dict[str, Any]]


class FocusRequest(BaseModel):
    district_id: str | None = None


class FocusResponse(BaseModel):
    focus: dict[str, Any]
    digest: dict[str, Any] | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)


def create_app(
    engine: SimEngine | None = None,
    *,
    auto_world: str = "default",
    config: SimulationConfig | None = None,
) -> FastAPI:
    """Instantiate the FastAPI app backed by a ``SimEngine``."""

    active_config = (
        config or getattr(engine, "config", None) or load_simulation_config()
    )
    sim = engine or SimEngine(config=active_config)
    _ensure_state(sim, auto_world)

    app = FastAPI(title="Echoes Simulation Service", version="0.1.0")

    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    @app.post("/tick", response_model=TickResponse)
    def post_tick(payload: TickRequest) -> TickResponse:
        limit = active_config.limits.service_tick_cap
        if payload.ticks > limit:
            raise HTTPException(
                status_code=400,
                detail=f"Tick request exceeds service limit of {limit}",
            )
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
        profiling = sim.state.metadata.get("profiling", {})
        return {"tick": sim.state.tick, "environment": env, "profiling": profiling}

    @app.post("/actions", response_model=ActionsResponse)
    def post_actions(payload: ActionsRequest) -> ActionsResponse:
        receipts = [sim.apply_action(action) for action in payload.actions]
        return ActionsResponse(results=receipts)

    @app.get("/focus", response_model=FocusResponse)
    def get_focus() -> FocusResponse:
        digest = sim.state.metadata.get("focus_digest", {})
        history = _focus_history(sim, sim.config.focus.history_limit)
        return FocusResponse(focus=sim.focus_state(), digest=digest, history=history)

    @app.post("/focus", response_model=FocusResponse)
    def post_focus(payload: FocusRequest) -> FocusResponse:
        try:
            if payload.district_id is None:
                focus = sim.clear_focus()
            else:
                focus = sim.set_focus(payload.district_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        digest = sim.state.metadata.get("focus_digest", {})
        history = _focus_history(sim, sim.config.focus.history_limit)
        return FocusResponse(focus=focus, digest=digest, history=history)

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
        "event_archive": list(report.event_archive),
        "suppressed_events": list(report.suppressed_events),
        "environment": dict(report.environment),
        "districts": [dict(district) for district in report.districts],
        "agent_actions": list(report.agent_actions),
        "faction_actions": list(report.faction_actions),
        "faction_legitimacy": dict(report.faction_legitimacy),
        "faction_legitimacy_delta": dict(report.faction_legitimacy_delta),
        "economy": dict(report.economy),
        "environment_impact": dict(report.environment_impact),
        "focus_budget": dict(report.focus_budget),
        "director_snapshot": dict(report.director_snapshot),
        "director_analysis": dict(report.director_analysis),
        "director_events": list(report.director_events),
        "timings": dict(report.timings),
        "anomalies": list(report.anomalies),
    }


def _focus_history(sim: SimEngine, limit: int | None = None) -> list[dict[str, Any]]:
    history = list(sim.state.metadata.get("focus_history") or [])
    if limit is None or limit >= len(history):
        return history
    return history[-limit:]
