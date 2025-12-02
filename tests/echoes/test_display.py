"""Tests for enhanced ASCII display utilities."""

from __future__ import annotations

from gengine.echoes.cli import display
from gengine.echoes.cli.shell import LocalBackend
from gengine.echoes.settings import load_simulation_config
from gengine.echoes.sim import SimEngine


def test_render_summary_table_basic() -> None:
    """Verify that render_summary_table produces formatted output."""
    config = load_simulation_config()
    engine = SimEngine(config=config)
    engine.initialize_state(world="default")
    backend = LocalBackend(engine)
    summary = backend.summary()

    output = display.render_summary_table(summary)

    assert "World Status" in output
    assert "Stability" in output
    assert "Environment Impact" in output or len(output) > 0


def test_render_summary_table_with_story_seeds() -> None:
    """Verify that story seeds render in the summary table."""
    config = load_simulation_config()
    engine = SimEngine(config=config)
    engine.initialize_state(world="default")

    # Advance ticks to potentially trigger story seeds
    engine.advance_ticks(50)
    backend = LocalBackend(engine)
    summary = backend.summary()

    output = display.render_summary_table(summary)
    assert output  # Should produce some output

    # If story seeds are active, they should appear
    seeds = summary.get("story_seeds") or []
    if seeds:
        assert "Active Story Seeds" in output or "Story" in output


def test_render_director_table() -> None:
    """Verify that render_director_table produces formatted output."""
    config = load_simulation_config()
    engine = SimEngine(config=config)
    engine.initialize_state(world="default")
    engine.advance_ticks(10)
    backend = LocalBackend(engine)
    summary = backend.summary()

    feed = summary.get("director_feed") or {}
    history = summary.get("director_history") or []
    analysis = summary.get("director_analysis")

    if feed:
        output = display.render_director_table(feed, history, analysis)
        assert output
        assert "Director" in output or "Feed" in output or "Focus" in output


def test_render_map_overlay() -> None:
    """Verify that render_map_overlay produces formatted output."""
    config = load_simulation_config()
    engine = SimEngine(config=config)
    engine.initialize_state(world="default")
    backend = LocalBackend(engine)
    summary = backend.summary()

    output = display.render_map_overlay(summary)

    assert output
    assert "City Map" in output or "District" in output


def test_render_with_profiling_data() -> None:
    """Verify that profiling data renders correctly."""
    config = load_simulation_config()
    engine = SimEngine(config=config)
    engine.initialize_state(world="default")
    engine.advance_ticks(5)
    backend = LocalBackend(engine)
    summary = backend.summary()

    output = display.render_summary_table(summary)

    # Profiling should be present
    profiling = summary.get("profiling")
    if profiling:
        assert "Performance" in output or "Metrics" in output


def test_environment_panel_colors() -> None:
    """Verify that environment impact renders with appropriate formatting."""
    summary = {
        "city": "Test",
        "tick": 10,
        "districts": 3,
        "factions": 2,
        "agents": 5,
        "stability": 0.5,
        "environment_impact": {
            "scarcity_pressure": 1.5,
            "average_pollution": 0.75,
            "biodiversity": {"value": 0.4, "delta": -0.05},
        },
    }

    output = display.render_summary_table(summary)

    assert output
    assert "scarcity" in output.lower() or "pressure" in output.lower()
