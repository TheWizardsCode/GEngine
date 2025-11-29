"""Regression tests for DirectorBridge and NarrativeDirector helpers."""

from __future__ import annotations

import pytest

from gengine.echoes.content import load_world_bundle
from gengine.echoes.core.models import DistrictCoordinates
from gengine.echoes.settings import DirectorSettings
from gengine.echoes.sim.director import DirectorBridge, NarrativeDirector
from gengine.echoes.sim.focus import FocusBudgetResult, NarrativeEvent, RankedEvent


def test_director_bridge_record_trims_history_and_clones_payloads() -> None:
    state = load_world_bundle()
    ring_ids = [district.id for district in state.city.districts[:2]]
    state.metadata["market_prices"] = {"energy": 12.3456}
    focus_state = {
        "district_id": ring_ids[0],
        "ring": ring_ids,
        "spatial_weights": [
            {"district_id": ring_ids[0], "score": 1.0},
            {"district_id": ring_ids[1], "score": 0.75},
        ],
        "spatial_metrics": {"pressure": 0.5},
    }
    allocation = {
        "focus_center": ring_ids[0],
        "focus_ring": ring_ids,
        "list_field": [1, 2, 3],
        "scalar_field": {"value": 7},
    }
    ranked_archive = [
        RankedEvent(
            message="Signal spike",
            scope="district",
            score=1.25,
            severity=0.9,
            focus_distance=1,
            in_focus_ring=True,
            district_id=ring_ids[0],
        ),
        RankedEvent(
            message="Fallback",
            scope="environment",
            score=0.9,
            severity=0.5,
            focus_distance=2,
            in_focus_ring=False,
            district_id=ring_ids[1],
        ),
    ]
    focus_result = FocusBudgetResult(
        visible=[],
        archive=[],
        suppressed=[NarrativeEvent("Suppressed beat", district_id=ring_ids[0])],
        allocation=allocation,
        focus_state=focus_state,
        ranked_archive=ranked_archive,
    )
    settings = DirectorSettings(history_limit=1, ranked_limit=1, spatial_preview=1)
    bridge = DirectorBridge(settings=settings)

    first_snapshot = bridge.record(state, tick=5, focus_result=focus_result)
    second_snapshot = bridge.record(state, tick=6, focus_result=focus_result)

    assert first_snapshot["top_ranked"][0]["district_id"] == ring_ids[0]
    assert len(second_snapshot["spatial_weights"]) == 1
    assert second_snapshot["allocation"]["list_field"] == [1, 2, 3]
    assert (
        second_snapshot["allocation"]["list_field"]
        is not allocation["list_field"]
    ), "allocation list must be cloned"
    assert state.metadata["director_history"][-1]["tick"] == 6
    assert len(state.metadata["director_history"]) == 1
    assert second_snapshot["market_prices"]["energy"] == pytest.approx(12.346, rel=1e-6)


def test_narrative_director_evaluate_clears_analysis_when_feed_missing() -> None:
    state = load_world_bundle()
    director = NarrativeDirector()
    state.metadata["director_analysis"] = {"tick": 99}

    analysis = director.evaluate(state, snapshot=None)

    assert analysis == {}
    assert "director_analysis" not in state.metadata


def test_narrative_director_plan_route_handles_disconnected_and_no_focus() -> None:
    director = NarrativeDirector()
    adjacency = {"A": ["B"], "B": []}
    coords = {
        "A": DistrictCoordinates(x=0.0, y=0.0, z=0.0),
        "C": DistrictCoordinates(x=3.0, y=4.0, z=0.0),
    }

    disconnected = director._plan_route("A", "C", adjacency, coords)
    assert disconnected["reachable"] is False
    assert disconnected["reason"] == "disconnected"
    assert disconnected["fallback_distance"] == pytest.approx(5.0, rel=1e-3)

    no_focus = director._plan_route(None, "C", adjacency, coords)
    assert no_focus["reachable"] is False
    assert no_focus["reason"] == "no_focus"


def test_narrative_director_plan_route_handles_missing_coordinates() -> None:
    settings = DirectorSettings(travel_time_per_distance=0.0, travel_time_per_hop=2.0)
    director = NarrativeDirector(settings=settings)
    adjacency = {"A": ["B"], "B": ["C"], "C": []}
    coords = {
        "A": DistrictCoordinates(x=0.0, y=0.0, z=0.0),
        "C": DistrictCoordinates(x=2.0, y=0.0, z=0.0),
    }

    route = director._plan_route("A", "C", adjacency, coords)

    assert route["reachable"] is True
    assert route["distance"] is None
    assert route["travel_time"] == pytest.approx(4.0)
