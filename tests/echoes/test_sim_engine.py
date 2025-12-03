"""Tests for the SimEngine abstraction (Phase 3, M3.1).

This module includes comprehensive tests for:
- All public SimEngine APIs (views, focus, director, explanations, progression)
- Error handling paths (uninitialized state, invalid inputs, tick limits)
- Integration with progression system
"""

from __future__ import annotations
import pytest
from gengine.echoes.settings import SimulationConfig, SimulationLimits
from gengine.echoes.sim import SimEngine
from gengine.echoes.sim.engine import EngineNotInitializedError

# ...existing code before TestProgressionAPI...

class TestProgressionAPI:
    def test_query_view_before_initialization_raises(self) -> None:
        """EngineNotInitializedError raised when querying view before init."""
        engine = SimEngine()
        with pytest.raises(EngineNotInitializedError):
            engine.query_view("summary")

    def test_advance_ticks_before_initialization_raises(self) -> None:
        """EngineNotInitializedError raised when advancing ticks before init."""
        engine = SimEngine()
        with pytest.raises(EngineNotInitializedError):
            engine.advance_ticks(1)

    def test_progression_summary_before_initialization_raises(self) -> None:
        """EngineNotInitializedError raised for progression_summary before init."""
        engine = SimEngine()
        with pytest.raises(EngineNotInitializedError):
            engine.progression_summary()

# ...existing code after TestProgressionAPI...
