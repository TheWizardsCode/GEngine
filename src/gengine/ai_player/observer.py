"""Observer AI that monitors and analyzes Echoes simulations.

The Observer connects via SimServiceClient (remote) or local SimEngine, advances
ticks, analyzes state snapshots, and generates structured commentary on game
dynamics including stability trends, faction swings, and story seed activations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from gengine.echoes.client import SimServiceClient
from gengine.echoes.sim import SimEngine

logger = logging.getLogger("gengine.ai_player.observer")

# Minimum delta threshold to detect a trend (below this is considered "stable")
_TREND_STABLE_THRESHOLD = 0.01


@dataclass
class ObserverConfig:
    """Configuration for the AI Observer."""

    tick_budget: int = 100
    analysis_interval: int = 10
    stability_alert_threshold: float = 0.5
    legitimacy_swing_threshold: float = 0.1
    log_natural_language: bool = True


@dataclass
class TrendAnalysis:
    """Analysis of a simulation metric trend over time."""

    metric_name: str
    start_value: float
    end_value: float
    delta: float
    trend: str  # "increasing", "decreasing", "stable"
    samples: list[float] = field(default_factory=list)
    alert: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "start_value": round(self.start_value, 4),
            "end_value": round(self.end_value, 4),
            "delta": round(self.delta, 4),
            "trend": self.trend,
            "samples": [round(s, 4) for s in self.samples],
            "alert": self.alert,
        }


@dataclass
class ObservationReport:
    """Structured report from an observation session."""

    ticks_observed: int
    start_tick: int
    end_tick: int
    stability_trend: TrendAnalysis
    faction_swings: dict[str, TrendAnalysis]
    story_seeds_activated: list[dict[str, Any]]
    alerts: list[str]
    commentary: list[str]
    environment_summary: dict[str, float]
    tick_reports: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        env_summary = {}
        for k, v in self.environment_summary.items():
            if isinstance(v, (int, float)):
                env_summary[k] = round(v, 4) if isinstance(v, float) else v
            else:
                env_summary[k] = v
        return {
            "ticks_observed": self.ticks_observed,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "stability_trend": self.stability_trend.to_dict(),
            "faction_swings": {
                fid: trend.to_dict() for fid, trend in self.faction_swings.items()
            },
            "story_seeds_activated": self.story_seeds_activated,
            "alerts": self.alerts,
            "commentary": self.commentary,
            "environment_summary": env_summary,
            "tick_reports_count": len(self.tick_reports),
        }


class Observer:
    """AI Observer that monitors and analyzes simulation state.

    The Observer can connect to either a local SimEngine or a remote simulation
    service via SimServiceClient. It advances ticks, collects state snapshots,
    and generates structured analysis of game dynamics.

    Examples
    --------
    Local engine observation::

        from gengine.echoes.sim import SimEngine
        from gengine.ai_player import Observer, ObserverConfig

        engine = SimEngine()
        engine.initialize_state(world="default")
        observer = Observer(engine=engine, config=ObserverConfig(tick_budget=50))
        report = observer.observe()
        print(report.to_dict())

    Remote service observation::

        from gengine.echoes.client import SimServiceClient
        from gengine.ai_player import Observer, ObserverConfig

        client = SimServiceClient("http://localhost:8000")
        observer = Observer(client=client, config=ObserverConfig(tick_budget=50))
        report = observer.observe()
        client.close()
    """

    def __init__(
        self,
        *,
        engine: SimEngine | None = None,
        client: SimServiceClient | None = None,
        config: ObserverConfig | None = None,
    ) -> None:
        if engine is None and client is None:
            raise ValueError("Must provide either engine or client")
        if engine is not None and client is not None:
            raise ValueError("Provide only one of engine or client")
        self._engine = engine
        self._client = client
        self._config = config or ObserverConfig()
        self._is_local = engine is not None

    @property
    def config(self) -> ObserverConfig:
        return self._config

    def observe(self, ticks: int | None = None) -> ObservationReport:
        """Run an observation session for the configured tick budget.

        Parameters
        ----------
        ticks
            Override the configured tick budget. If None, uses config.tick_budget.

        Returns
        -------
        ObservationReport
            Structured analysis of the simulation during the observation period.
        """
        tick_count = ticks if ticks is not None else self._config.tick_budget
        if tick_count < 1:
            raise ValueError("Tick count must be at least 1")

        initial_state = self._get_state()
        start_tick = initial_state.get("tick", 0)

        stability_samples: list[float] = [initial_state.get("stability", 1.0)]
        faction_samples: dict[str, list[float]] = {}
        for fid, leg in initial_state.get("faction_legitimacy", {}).items():
            faction_samples[fid] = [leg]

        story_seeds_activated: list[dict[str, Any]] = []
        alerts: list[str] = []
        commentary: list[str] = []
        tick_reports: list[dict[str, Any]] = []

        ticks_advanced = 0
        remaining = tick_count

        while remaining > 0:
            batch_size = min(remaining, self._config.analysis_interval)
            tick_result = self._advance_ticks(batch_size)
            ticks_advanced += tick_result.get("ticks_advanced", batch_size)
            remaining -= batch_size

            state = self._get_state()
            stability_samples.append(state.get("stability", 1.0))

            for fid, leg in state.get("faction_legitimacy", {}).items():
                if fid not in faction_samples:
                    faction_samples[fid] = []
                faction_samples[fid].append(leg)

            self._check_story_seeds(state, story_seeds_activated)
            self._check_alerts(state, alerts, commentary)

            tick_reports.append({
                "tick": state.get("tick", 0),
                "stability": state.get("stability", 1.0),
                "faction_legitimacy": dict(state.get("faction_legitimacy", {})),
                "story_seeds": list(state.get("story_seeds", [])),
            })

        final_state = self._get_state()
        end_tick = final_state.get("tick", start_tick + ticks_advanced)

        stability_trend = self._analyze_trend(
            "stability",
            stability_samples,
            alert_threshold=self._config.stability_alert_threshold,
            alert_direction="below",
        )

        faction_swings: dict[str, TrendAnalysis] = {}
        for fid, samples in faction_samples.items():
            trend = self._analyze_trend(
                f"faction_{fid}_legitimacy",
                samples,
                swing_threshold=self._config.legitimacy_swing_threshold,
            )
            faction_swings[fid] = trend

        commentary.extend(self._generate_commentary(
            stability_trend,
            faction_swings,
            story_seeds_activated,
        ))

        return ObservationReport(
            ticks_observed=ticks_advanced,
            start_tick=start_tick,
            end_tick=end_tick,
            stability_trend=stability_trend,
            faction_swings=faction_swings,
            story_seeds_activated=story_seeds_activated,
            alerts=alerts,
            commentary=commentary,
            environment_summary=self._extract_environment(final_state),
            tick_reports=tick_reports,
        )

    def _get_state(self) -> dict[str, Any]:
        """Fetch current simulation state."""
        if self._is_local:
            assert self._engine is not None
            return self._engine.query_view("summary")
        else:
            assert self._client is not None
            return self._client.state("summary")

    def _advance_ticks(self, count: int) -> dict[str, Any]:
        """Advance simulation by count ticks."""
        if self._is_local:
            assert self._engine is not None
            reports = self._engine.advance_ticks(count)
            return {"ticks_advanced": len(reports)}
        else:
            assert self._client is not None
            return self._client.tick(count)

    def _analyze_trend(
        self,
        metric_name: str,
        samples: list[float],
        *,
        alert_threshold: float | None = None,
        alert_direction: str = "below",
        swing_threshold: float | None = None,
    ) -> TrendAnalysis:
        """Analyze a sequence of metric samples for trends."""
        if not samples:
            return TrendAnalysis(
                metric_name=metric_name,
                start_value=0.0,
                end_value=0.0,
                delta=0.0,
                trend="stable",
                samples=[],
            )

        start = samples[0]
        end = samples[-1]
        delta = end - start

        if abs(delta) < _TREND_STABLE_THRESHOLD:
            trend = "stable"
        elif delta > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        alert = None
        if alert_threshold is not None:
            if alert_direction == "below" and end < alert_threshold:
                alert = (
                    f"{metric_name} dropped below {alert_threshold} "
                    f"(current: {end:.3f})"
                )
            elif alert_direction == "above" and end > alert_threshold:
                alert = f"{metric_name} exceeded {alert_threshold} (current: {end:.3f})"

        if swing_threshold is not None and abs(delta) >= swing_threshold:
            direction = "gained" if delta > 0 else "lost"
            alert = (
                f"{metric_name} {direction} {abs(delta):.3f} over observation period"
            )

        return TrendAnalysis(
            metric_name=metric_name,
            start_value=start,
            end_value=end,
            delta=delta,
            trend=trend,
            samples=samples,
            alert=alert,
        )

    def _check_story_seeds(
        self,
        state: dict[str, Any],
        activated: list[dict[str, Any]],
    ) -> None:
        """Track newly activated story seeds."""
        current_seeds = state.get("story_seeds", [])
        known_ids = {s.get("seed_id") for s in activated}
        for seed in current_seeds:
            seed_id = seed.get("seed_id") or seed.get("id")
            if seed_id and seed_id not in known_ids:
                activated.append({
                    "seed_id": seed_id,
                    "tick": state.get("tick", 0),
                    "district": seed.get("target_district") or seed.get("district"),
                })

    def _check_alerts(
        self,
        state: dict[str, Any],
        alerts: list[str],
        commentary: list[str],
    ) -> None:
        """Check state for alert conditions."""
        stability = state.get("stability", 1.0)
        tick = state.get("tick", 0)

        if stability < self._config.stability_alert_threshold:
            alert = f"[Tick {tick}] ALERT: Stability critical at {stability:.3f}"
            if alert not in alerts:
                alerts.append(alert)
                if self._config.log_natural_language:
                    logger.warning(alert)

        director_pacing = state.get("director_pacing", {})
        if director_pacing.get("active_count", 0) >= 3:
            active_count = director_pacing["active_count"]
            alert = f"[Tick {tick}] Multiple crises active ({active_count})"
            if alert not in alerts:
                alerts.append(alert)

    def _extract_environment(self, state: dict[str, Any]) -> dict[str, float]:
        """Extract environment metrics from state."""
        env = {}
        for key in ["stability", "unrest", "pollution", "biodiversity", "security"]:
            if key in state:
                env[key] = state[key]
        env_impact = state.get("environment_impact", {})
        if isinstance(env_impact, dict):
            for key in ["avg_pollution", "biodiversity", "scarcity_pressure"]:
                if key in env_impact:
                    env[f"impact_{key}"] = env_impact[key]
        return env

    def _generate_commentary(
        self,
        stability_trend: TrendAnalysis,
        faction_swings: dict[str, TrendAnalysis],
        story_seeds: list[dict[str, Any]],
    ) -> list[str]:
        """Generate natural language commentary on the observation."""
        comments: list[str] = []

        if stability_trend.trend == "decreasing" and stability_trend.delta < -0.1:
            start_val = stability_trend.start_value
            end_val = stability_trend.end_value
            comments.append(
                f"Stability declined significantly from {start_val:.2f} "
                f"to {end_val:.2f} over the observation period."
            )
        elif stability_trend.trend == "increasing" and stability_trend.delta > 0.1:
            comments.append(
                f"Stability improved from {stability_trend.start_value:.2f} "
                f"to {stability_trend.end_value:.2f}, indicating recovering governance."
            )
        elif stability_trend.trend == "stable":
            comments.append(
                f"Stability remained steady around {stability_trend.end_value:.2f}."
            )
        else:
            end_val = stability_trend.end_value
            comments.append(
                f"Stability showed minor fluctuations, ending at {end_val:.2f}."
            )

        for fid, trend in faction_swings.items():
            if trend.alert:
                faction_name = fid.replace("_", " ").title()
                if trend.delta > 0:
                    comments.append(
                        f"{faction_name} gained influence "
                        f"(+{trend.delta:.2f} legitimacy)."
                    )
                else:
                    comments.append(
                        f"{faction_name} lost influence ({trend.delta:.2f} legitimacy)."
                    )

        if story_seeds:
            seed_names = [s.get("seed_id", "unknown") for s in story_seeds]
            comments.append(
                f"Story seeds activated during observation: {', '.join(seed_names)}."
            )

        return comments


def create_observer_from_engine(
    world: str = "default",
    config: ObserverConfig | None = None,
) -> Observer:
    """Create an Observer with a fresh local SimEngine.

    Parameters
    ----------
    world
        World bundle to load.
    config
        Optional observer configuration.

    Returns
    -------
    Observer
        Configured observer ready for observation sessions.
    """
    engine = SimEngine()
    engine.initialize_state(world=world)
    return Observer(engine=engine, config=config)


def create_observer_from_service(
    base_url: str,
    config: ObserverConfig | None = None,
) -> Observer:
    """Create an Observer connected to a remote simulation service.

    Parameters
    ----------
    base_url
        URL of the simulation service (e.g., "http://localhost:8000").
    config
        Optional observer configuration.

    Returns
    -------
    Observer
        Configured observer ready for observation sessions.
    """
    client = SimServiceClient(base_url)
    return Observer(client=client, config=config)
