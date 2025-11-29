"""Tests for the Echoes CLI shell helpers."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from gengine.echoes.cli import run_commands
from gengine.echoes.cli.shell import (
    EchoesShell,
    LocalBackend,
    ServiceBackend,
    _render_focus_state,
    _render_director_feed,
    _render_history,
    _render_summary,
    main as cli_main,
)
from gengine.echoes.client import SimServiceClient
from gengine.echoes.content import load_world_bundle
from gengine.echoes.service import create_app
from gengine.echoes.settings import SimulationConfig, SimulationLimits
from gengine.echoes.sim import SimEngine


def test_run_commands_executes_sequence(tmp_path: Path) -> None:
    out = run_commands(
        [
            "summary",
            "next",
            "run 2",
            "map",
            f"save {tmp_path / 'state.json'}",
            "exit",
        ]
    )

    assert "Current world summary" in out[0]
    assert "Tick" in out[1]
    assert (tmp_path / "state.json").exists()
    assert "City overview" in out[3]
    assert "Geometry overlay" in out[3]
    assert "industrial-tier" in out[3]
    assert out[-1] == "Exiting shell."


def test_shell_load_switches_world(tmp_path: Path) -> None:
    state = load_world_bundle()
    engine = SimEngine(state=state)
    backend = LocalBackend(engine)
    shell = EchoesShell(backend)
    other_snapshot = tmp_path / "snap.json"
    shell.execute(f"save {other_snapshot}")

    response = shell.execute(f"load snapshot {other_snapshot}")

    assert "Loaded snapshot" in response.output
    assert engine.state.tick == 0


def test_shell_service_backend_reports_summary() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    test_client = TestClient(app)
    client = SimServiceClient(base_url="http://testserver", client=test_client)
    backend = ServiceBackend(client)
    shell = EchoesShell(backend)

    summary = shell.execute("summary")
    assert "Current world summary" in summary.output

    map_output = shell.execute("map")
    assert "City overview" in map_output.output

    load_result = shell.execute("load world default")
    assert "requires local backend" in load_result.output

    client.close()


def test_local_backend_save_and_load(tmp_path: Path) -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    backend = LocalBackend(engine)
    snapshot_path = tmp_path / "local.json"

    save_msg = backend.save_snapshot(snapshot_path)
    assert snapshot_path.exists()
    assert "Saved snapshot" in save_msg

    world_msg = backend.load_world("default")
    assert "Loaded world" in world_msg

    snap_msg = backend.load_snapshot(snapshot_path)
    assert "Loaded snapshot" in snap_msg


def test_service_backend_map_and_save(tmp_path: Path) -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    test_client = TestClient(app)
    client = SimServiceClient(base_url="http://testserver", client=test_client)
    backend = ServiceBackend(client)

    city_view = backend.render_map(None)
    assert "City overview" in city_view
    assert "Geometry overlay" in city_view

    first_id = engine.state.city.districts[0].id
    district_view = backend.render_map(first_id)
    assert engine.state.city.districts[0].name in district_view
    assert "coordinates" in district_view

    snapshot_path = tmp_path / "remote.json"
    backend.save_snapshot(snapshot_path)
    payload = json.loads(snapshot_path.read_text())
    assert payload["tick"] == 0

    with pytest.raises(NotImplementedError):
        backend.load_world("default")
    with pytest.raises(NotImplementedError):
        backend.load_snapshot(snapshot_path)

    client.close()


def test_map_command_surfaces_geometry() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    backend = LocalBackend(engine)

    city_view = backend.render_map(None)
    assert "Geometry overlay" in city_view
    assert "coords" in city_view

    detail_view = backend.render_map(engine.state.city.districts[0].id)
    assert "coordinates" in detail_view
    assert "adjacent" in detail_view


def test_cli_main_script_local(capsys) -> None:
    exit_code = cli_main(["--world", "default", "--script", "summary;exit"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Current world summary" in captured.out


def test_cli_main_script_service(monkeypatch, capsys) -> None:
    base_state = load_world_bundle()
    summary = base_state.summary()
    snapshot = base_state.snapshot()
    district = base_state.city.districts[0]
    district_panel = {
        "id": district.id,
        "name": district.name,
        "population": district.population,
        "modifiers": district.modifiers.model_dump(),
    }

    class FakeClient:
        close_called = False

        def __init__(self, url: str) -> None:  # pragma: no cover - simple stub
            self._tick = base_state.tick

        def state(self, detail: str = "summary", district_id: str | None = None):
            if detail == "summary":
                return {"data": summary}
            if detail == "snapshot":
                return {"data": snapshot}
            if detail == "district":
                return {"data": district_panel}
            raise ValueError(detail)

        def tick(self, count: int) -> dict[str, object]:
            self._tick += count
            report = {
                "tick": self._tick,
                "events": [],
                "environment": {
                    "stability": 0.5,
                    "unrest": 0.5,
                    "pollution": 0.5,
                    "climate_risk": 0.5,
                    "security": 0.5,
                },
                "districts": [],
                "agent_actions": [],
                "faction_actions": [],
                "faction_legitimacy": {},
                "faction_legitimacy_delta": {},
                "economy": {"prices": {}, "shortages": {}},
                "timings": {"tick_total_ms": 1.0},
            }
            return {"reports": [report]}

        def close(self) -> None:
            FakeClient.close_called = True

    monkeypatch.setattr("gengine.echoes.cli.shell.SimServiceClient", FakeClient)

    exit_code = cli_main(["--service-url", "http://fake", "--script", "summary;run 1;exit"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Current world summary" in captured.out
    assert FakeClient.close_called


def test_shell_help_and_error_paths() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    shell = EchoesShell(LocalBackend(engine))

    assert "Available commands" in shell.execute("help").output
    assert "Usage: next" in shell.execute("next 2").output
    assert "Usage: run <count>" in shell.execute("run").output
    assert "Unknown district" in shell.execute("map nowhere").output
    assert "Usage: save" in shell.execute("save").output
    assert "Usage" in shell.execute("load").output
    assert "Unknown command" in shell.execute("foobar").output
    assert "Unknown district" in shell.execute("focus nowhere").output


def test_run_commands_with_service_backend() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    app = create_app(engine=engine)
    client = SimServiceClient(base_url="http://testserver", client=TestClient(app))
    backend = ServiceBackend(client)

    outputs = run_commands(["summary", "exit"], backend=backend)

    assert "Current world summary" in outputs[0]
    client.close()


def test_shell_run_command_is_clamped() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    limits = SimulationLimits(
        engine_max_ticks=10,
        cli_run_cap=2,
        cli_script_command_cap=5,
        service_tick_cap=10,
    )
    shell = EchoesShell(LocalBackend(engine), limits=limits)

    result = shell.execute("run 5")

    assert "Safeguard" in result.output
    assert result.output.count("Tick") == 2


def test_run_commands_respects_script_cap() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    limits = SimulationLimits(
        engine_max_ticks=10,
        cli_run_cap=5,
        cli_script_command_cap=2,
        service_tick_cap=10,
    )
    config = SimulationConfig(limits=limits)

    outputs = run_commands(["summary", "summary", "summary"], engine=engine, config=config)

    assert outputs[-1].startswith("Safeguard: script exceeded 2 commands")


def test_cli_main_interactive(monkeypatch, capsys) -> None:
    inputs = iter(["help", "exit"])

    def fake_input(_: str) -> str:
        try:
            return next(inputs)
        except StopIteration:  # pragma: no cover - defensive
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)

    exit_code = cli_main(["--world", "default"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Available commands" in captured.out


def test_render_summary_surfaces_environment_impact() -> None:
    summary = {
        "city": "Test",
        "tick": 10,
        "districts": 3,
        "factions": 2,
        "agents": 5,
        "stability": 0.9,
        "environment_impact": {
            "scarcity_pressure": 1.25,
            "diffusion_applied": True,
            "district_deltas": {"industrial-tier": {"pollution": -0.02}},
            "faction_effects": [
                {
                    "faction": "Union of Flux",
                    "district": "industrial-tier",
                    "pollution_delta": -0.02,
                }
            ],
            "biodiversity": {"value": 0.62, "delta": -0.01},
            "stability_effects": {"biodiversity_delta": -0.002},
        },
        "focus": {
            "district_id": "industrial-tier",
            "neighbors": ["research-spire"],
            "ring": ["industrial-tier", "research-spire"],
        },
        "focus_digest": {
            "visible": ["Agent A inspects Industrial Tier"],
            "suppressed_count": 2,
            "ranked_archive": [
                {
                    "message": "Industrial Tier protests intensify",
                    "scope": "district",
                    "score": 0.92,
                    "severity": 1.0,
                    "focus_distance": 0,
                    "in_focus_ring": True,
                    "district_id": "industrial-tier",
                }
            ],
        },
    }

    rendered = _render_summary(summary)

    assert "env impact" in rendered
    assert "faction effects" in rendered
    assert "biodiversity" in rendered
    assert "focus -> industrial-tier" in rendered
    assert "focus digest" in rendered
    assert "ranked:" in rendered


def test_render_summary_surfaces_director_feed() -> None:
    summary = {
        "city": "Test",
        "tick": 12,
        "districts": 3,
        "factions": 2,
        "agents": 5,
        "stability": 0.9,
        "director_feed": {
            "focus_center": "industrial-tier",
            "suppressed_count": 2,
            "top_ranked": [
                {"message": "Event A", "score": 0.8, "district_id": "industrial-tier"},
                {"message": "Event B", "score": 0.6, "district_id": "research-spire"},
            ],
            "spatial_weights": [
                {"district_id": "industrial-tier", "score": 1.0},
                {"district_id": "research-spire", "score": 0.8},
            ],
        },
    }

    rendered = _render_summary(summary)

    assert "director feed" in rendered
    assert "ranked" in rendered
    assert "spatial" in rendered


def test_render_summary_surfaces_director_analysis() -> None:
    summary = {
        "city": "Test",
        "tick": 5,
        "districts": 3,
        "factions": 2,
        "agents": 5,
        "stability": 0.9,
        "director_analysis": {
            "hotspots": [
                {
                    "district_id": "research-spire",
                    "travel": {"travel_time": 2.5, "reachable": True},
                }
            ],
            "recommended_focus": {
                "district_id": "research-spire",
                "travel_time": 2.5,
            },
        },
    }

    rendered = _render_summary(summary)

    assert "director analysis" in rendered
    assert "travel" in rendered
    assert "recommend focus" in rendered


def test_render_summary_surfaces_story_seeds() -> None:
    summary = {
        "city": "Test",
        "tick": 7,
        "districts": 3,
        "factions": 2,
        "agents": 4,
        "stability": 0.88,
        "story_seeds": [
            {
                "seed_id": "energy-quota-crisis",
                "title": "Energy Quota Fallout",
                "district_id": "industrial-tier",
                "reason": "Scarcity in energy, materials strains the city environment",
                "score": 0.71,
            }
        ],
    }

    rendered = _render_summary(summary)

    assert "story seeds" in rendered
    assert "Energy Quota Fallout" in rendered
    assert "industrial-tier" in rendered


def test_focus_command_reports_state() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    shell = EchoesShell(LocalBackend(engine))

    default_output = shell.execute("focus").output

    assert "Focus configuration" in default_output
    assert "coords" in default_output
    assert "adjacent" in default_output

    current_focus = engine.focus_state()
    neighbor = (current_focus.get("neighbors") or [None])[0]
    if neighbor:
        updated = shell.execute(f"focus {neighbor}").output
        assert neighbor in updated

    cleared = shell.execute("focus clear").output
    assert "Focus configuration" in cleared


def test_render_focus_state_formats_output() -> None:
    panel = {
        "district_id": "industrial-tier",
        "neighbors": ["research-spire"],
        "ring": ["industrial-tier", "research-spire"],
        "adjacent": ["perimeter-hollow"],
        "coordinates": {"x": 0.0, "y": 0.0},
    }

    rendered = _render_focus_state(panel)

    assert "industrial-tier" in rendered
    assert "research-spire" in rendered
    assert "coords" in rendered
    assert "adjacent" in rendered


def test_game_state_summary_includes_environment_metadata() -> None:
    state = load_world_bundle()
    state.metadata["environment_impact"] = {"scarcity_pressure": 0.5}

    summary = state.summary()

    assert "environment_impact" in summary


def test_render_summary_surfaces_profiling() -> None:
    summary = {
        "city": "Test",
        "tick": 5,
        "districts": 3,
        "factions": 2,
        "agents": 5,
        "stability": 0.8,
        "profiling": {
            "tick_ms_p50": 1.2,
            "tick_ms_p95": 2.1,
            "tick_ms_max": 2.5,
            "last_subsystem_ms": {"agent_ms": 0.5, "economy_ms": 0.6},
            "slowest_subsystem": {"name": "economy_ms", "ms": 0.6},
            "anomalies": ["agent_error"],
        },
    }

    rendered = _render_summary(summary)

    assert "profiling" in rendered
    assert "tick ms" in rendered
    assert "slowest" in rendered
    assert "anomalies" in rendered


def test_game_state_summary_includes_profiling_metadata() -> None:
    state = load_world_bundle()
    state.metadata["profiling"] = {"tick_ms_p50": 1.0}

    summary = state.summary()

    assert "profiling" in summary


def test_history_command_reports_entries() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    engine.advance_ticks(2)
    shell = EchoesShell(LocalBackend(engine))

    rendered = shell.execute("history").output

    assert "tick" in rendered
    assert "focus=" in rendered


def test_director_command_reports_feed() -> None:
    engine = SimEngine()
    engine.initialize_state(world="default")
    engine.advance_ticks(1)
    shell = EchoesShell(LocalBackend(engine))

    rendered = shell.execute("director").output

    assert "Director feed" in rendered
    assert "focus=" in rendered


def test_render_director_feed_includes_analysis() -> None:
    feed = {
        "tick": 10,
        "focus_center": "industrial-tier",
        "suppressed_count": 3,
    }
    history = [
        {"tick": 8, "focus_center": "industrial-tier", "suppressed_count": 2},
        {"tick": 9, "focus_center": "industrial-tier", "suppressed_count": 1},
    ]
    analysis = {
        "hotspots": [
            {
                "district_id": "research-spire",
                "travel": {"reachable": True, "hops": 1, "travel_time": 1.5},
            }
        ],
        "recommended_focus": {
            "district_id": "research-spire",
            "travel_time": 1.5,
        },
    }

    rendered = _render_director_feed(feed, history, analysis)

    assert "travel planning" in rendered
    assert "recommendation" in rendered


def test_render_director_feed_includes_story_seed_matches() -> None:
    feed = {"tick": 15, "focus_center": "industrial-tier", "suppressed_count": 4}
    analysis = {
        "story_seeds": [
            {
                "seed_id": "hollow-supply-chain",
                "title": "Smuggling Lanes Exposed",
                "district_id": "perimeter-hollow",
                "reason": "Cassian Mire inspects Perimeter Hollow",
                "score": 0.6,
            }
        ]
    }

    rendered = _render_director_feed(feed, None, analysis)

    assert "seed matches" in rendered
    assert "Smuggling Lanes Exposed" in rendered
    assert "perimeter-hollow" in rendered


def test_render_history_formats_output() -> None:
    entries = [
        {
            "tick": 10,
            "focus_center": "industrial-tier",
            "suppressed_count": 3,
            "suppressed_preview": ["Event A", "Event B"],
            "top_ranked": [
                {"message": "Event A", "score": 0.8},
                {"message": "Event B", "score": 0.6},
            ],
        }
    ]

    rendered = _render_history(entries)

    assert "tick 10" in rendered
    assert "Event A" in rendered