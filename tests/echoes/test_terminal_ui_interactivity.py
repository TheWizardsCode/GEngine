
from __future__ import annotations
import sys
import pytest
if sys.platform == "win32":
    pytest.skip("POSIX-only test file", allow_module_level=True)
"""Tests for Terminal UI interactivity and UI-to-engine integration."""

from unittest.mock import Mock, patch

import pytest

from gengine.echoes.cli.input_handler import InputAction, InputEvent, InputHandler
from gengine.echoes.cli.layout import UIState
from gengine.echoes.cli.terminal_ui import TerminalUIController
from gengine.echoes.core import GameState


class TestInputHandler:
    """Tests for input handling system."""

    def test_input_handler_initialization(self):
        """Test input handler initializes with default mappings."""
        handler = InputHandler()
        assert handler.mappings is not None
        assert "m" in handler.mappings
        assert handler.mappings["m"] == InputAction.VIEW_MAP

    def test_input_handler_custom_mappings(self):
        """Test input handler accepts custom key mappings."""
        custom = {"x": InputAction.QUIT}
        handler = InputHandler(custom_mappings=custom)
        assert handler.mappings["x"] == InputAction.QUIT

    def test_handle_key_mapped(self):
        """Test handling a mapped key returns InputEvent."""
        handler = InputHandler()
        event = handler.handle_key("m")
        assert event is not None
        assert isinstance(event, InputEvent)
        assert event.action == InputAction.VIEW_MAP

    def test_handle_key_unmapped(self):
        """Test handling an unmapped key returns None."""
        handler = InputHandler()
        event = handler.handle_key("z")
        assert event is None

    def test_handle_key_case_insensitive(self):
        """Test key handling is case insensitive."""
        handler = InputHandler()
        event_lower = handler.handle_key("m")
        event_upper = handler.handle_key("M")
        assert event_lower.action == event_upper.action

    def test_get_key_hints(self):
        """Test getting user-friendly key hints."""
        handler = InputHandler()
        hints = handler.get_key_hints()
        assert isinstance(hints, dict)
        assert "Navigate" in hints
        assert "Views" in hints


class TestTerminalUIController:
    """Tests for Terminal UI controller."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock shell backend."""
        backend = Mock()
        # Create proper mock structure matching GameState
        backend.state = Mock(spec=GameState)
        backend.state.city = Mock()
        backend.state.city.name = "Test City"
        backend.state.city.districts = []
        backend.state.tick = 42
        backend.state.environment = Mock()
        backend.state.environment.stability = 0.75
        backend.state.metadata = {"focus": {"district_id": None, "adjacent": []}}
        backend.advance_ticks = Mock(return_value=[])
        backend.set_focus = Mock()
        return backend

    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = Mock()
        console.width = 100
        console.height = 30
        return console

    def test_controller_initialization(self, mock_backend, mock_console):
        """Test Terminal UI controller initializes correctly."""
        controller = TerminalUIController(mock_backend, mock_console)
        assert controller.backend == mock_backend
        assert controller.console == mock_console
        assert isinstance(controller.ui_state, UIState)
        assert isinstance(controller.input_handler, InputHandler)
        assert controller.running is False

    def test_prepare_status_data(self, mock_backend, mock_console):
        """Test preparing status bar data from game state."""
        controller = TerminalUIController(mock_backend, mock_console)
        status_data = controller._prepare_status_data()
        assert status_data["city"] == "Test City"
        assert status_data["tick"] == 42
        assert status_data["stability"] == 0.75

    def test_handle_view_switching(self, mock_backend, mock_console):
        """Test handling view switching input events."""
        controller = TerminalUIController(mock_backend, mock_console)

        # Switch to agents view
        event = InputEvent(action=InputAction.VIEW_AGENTS)
        controller._handle_input_event(event)
        assert controller.ui_state.current_view == "agents"

        # Switch to factions view
        event = InputEvent(action=InputAction.VIEW_FACTIONS)
        controller._handle_input_event(event)
        assert controller.ui_state.current_view == "factions"

        # Switch to map view
        event = InputEvent(action=InputAction.VIEW_MAP)
        controller._handle_input_event(event)
        assert controller.ui_state.current_view == "map"

    def test_handle_overlay_toggling(self, mock_backend, mock_console):
        """Test handling overlay toggle events."""
        controller = TerminalUIController(mock_backend, mock_console)

        # Toggle unrest overlay on
        event = InputEvent(action=InputAction.TOGGLE_OVERLAY_UNREST)
        controller._handle_input_event(event)
        assert controller.ui_state.show_overlay == "unrest"

        # Toggle unrest overlay off
        event = InputEvent(action=InputAction.TOGGLE_OVERLAY_UNREST)
        controller._handle_input_event(event)
        assert controller.ui_state.show_overlay is None

        # Toggle pollution overlay
        event = InputEvent(action=InputAction.TOGGLE_OVERLAY_POLLUTION)
        controller._handle_input_event(event)
        assert controller.ui_state.show_overlay == "pollution"

        # Turn all overlays off
        event = InputEvent(action=InputAction.TOGGLE_OVERLAY_OFF)
        controller._handle_input_event(event)
        assert controller.ui_state.show_overlay is None

    def test_handle_tick_next_updates_state(self, mock_backend, mock_console):
        """Test tick advancement updates engine state."""
        mock_report = Mock()
        mock_report.tick = 43
        mock_report.events = ["Event 1", "Event 2"]
        mock_backend.advance_ticks.return_value = [mock_report]

        controller = TerminalUIController(mock_backend, mock_console)
        event = InputEvent(action=InputAction.TICK_NEXT)
        controller._handle_input_event(event)

        # Verify backend was called
        mock_backend.advance_ticks.assert_called_once_with(1)

        # Verify events were added to buffer
        assert len(controller.ui_state.event_buffer) == 2
        assert controller.ui_state.event_buffer[0]["description"] == "Event 1"

    def test_handle_tick_run_advances_batch(self, mock_backend, mock_console):
        """Test run command advances multiple ticks and records events."""
        report_one = Mock()
        report_one.tick = 44
        report_one.events = ["Event A"]

        report_two = Mock()
        report_two.tick = 45
        report_two.events = [
            {"description": "Event B", "severity": "warning"},
        ]

        mock_backend.advance_ticks.return_value = [report_one, report_two]

        controller = TerminalUIController(mock_backend, mock_console)
        event = InputEvent(action=InputAction.TICK_RUN)
        controller._handle_input_event(event)

        mock_backend.advance_ticks.assert_called_once_with(
            controller.RUN_TICK_BATCH
        )
        descriptions = [e["description"] for e in controller.ui_state.event_buffer]
        assert descriptions == ["Event A", "Event B"]

    def test_handle_focus_clear(self, mock_backend, mock_console):
        """Test clearing focus updates backend and UI state."""
        controller = TerminalUIController(mock_backend, mock_console)
        controller.ui_state.focus_district = "some-district"

        event = InputEvent(action=InputAction.FOCUS_CLEAR)
        controller._handle_input_event(event)

        # Verify backend was called
        mock_backend.set_focus.assert_called_once_with(None)

        # Verify UI state was updated
        assert controller.ui_state.focus_district is None

    def test_handle_quit_returns_true(self, mock_backend, mock_console):
        """Test quit action returns True to stop event loop."""
        controller = TerminalUIController(mock_backend, mock_console)
        event = InputEvent(action=InputAction.QUIT)
        should_quit = controller._handle_input_event(event)
        assert should_quit is True

    def test_update_components_renders_all_regions(self, mock_backend, mock_console):
        """Test updating components renders all layout regions."""
        controller = TerminalUIController(mock_backend, mock_console)

        with patch.object(controller.layout, "update_region") as mock_update:
            controller._update_components()

            # Verify all regions were updated
            region_names = [call[0][0] for call in mock_update.call_args_list]
            assert "header" in region_names
            assert "main" in region_names
            assert "context" in region_names
            assert "events" in region_names
            assert "commands" in region_names


class TestUIEngineIntegration:
    """Integration tests for UI-to-engine interactions."""

    @pytest.fixture
    def real_backend(self):
        """Create a real LocalBackend with minimal state."""
        from gengine.echoes.cli.shell import LocalBackend
        from gengine.echoes.sim import SimEngine

        engine = SimEngine()
        engine.initialize_state(world="default")
        return LocalBackend(engine)

    @pytest.fixture
    def real_console(self):
        """Create a real Rich console for integration testing."""
        from io import StringIO

        from rich.console import Console

        return Console(file=StringIO(), force_terminal=True, width=100, height=30)

    def test_ui_state_changes_trigger_rerender(self, real_backend, real_console):
        """Test UI state changes trigger component re-rendering."""
        controller = TerminalUIController(real_backend, real_console)

        # Change view and verify it's reflected
        controller.ui_state.current_view = "agents"
        with patch.object(controller, "_update_agents_view") as mock_update:
            controller._update_components()
            mock_update.assert_called_once()

    def test_tick_advancement_updates_ui(self, real_backend, real_console):
        """Test tick advancement updates all UI components."""
        controller = TerminalUIController(real_backend, real_console)

        initial_tick = controller._get_game_state().tick
        event = InputEvent(action=InputAction.TICK_NEXT)
        controller._handle_input_event(event)

        new_tick = controller._get_game_state().tick
        assert new_tick == initial_tick + 1

    def test_focus_change_updates_map_display(self, real_backend, real_console):
        """Test changing focus updates map display."""
        controller = TerminalUIController(real_backend, real_console)
        state = controller._get_game_state()

        # Get first district
        if state.city.districts:
            district_id = state.city.districts[0].id

            # Set focus via backend (simulating UI action)
            real_backend.set_focus(district_id)

            # Verify focus is stored in metadata under 'focus_state' key
            focus_data = state.metadata.get("focus_state", {})
            assert focus_data.get("district_id") == district_id

    def test_overlay_toggle_updates_map_colors(self, real_backend, real_console):
        """Test overlay toggle changes map visualization."""
        controller = TerminalUIController(real_backend, real_console)

        # Toggle overlay on
        event = InputEvent(action=InputAction.TOGGLE_OVERLAY_UNREST)
        controller._handle_input_event(event)
        assert controller.ui_state.show_overlay == "unrest"

        # Verify map view uses overlay
        state = controller._get_game_state()
        view_data = controller.ui_state
        from gengine.echoes.cli.views import prepare_map_view_data

        map_data = prepare_map_view_data(state, view_data)
        assert map_data["overlay"] == "unrest"

    def test_view_switching_shows_correct_components(self, real_backend, real_console):
        """Test switching views updates displayed components."""
        controller = TerminalUIController(real_backend, real_console)

        # Switch to agents view
        controller.ui_state.current_view = "agents"
        with patch.object(controller, "_update_agents_view") as mock_agents:
            controller._update_components()
            mock_agents.assert_called_once()

        # Switch to factions view
        controller.ui_state.current_view = "factions"
        with patch.object(controller, "_update_factions_view") as mock_factions:
            controller._update_components()
            mock_factions.assert_called_once()


class TestInputEvent:
    """Tests for InputEvent dataclass."""

    def test_input_event_creation(self):
        """Test creating an InputEvent."""
        event = InputEvent(action=InputAction.TICK_NEXT)
        assert event.action == InputAction.TICK_NEXT
        assert event.data is None

    def test_input_event_with_data(self):
        """Test creating an InputEvent with data."""
        event = InputEvent(action=InputAction.SELECT, data={"entity_id": "test"})
        assert event.action == InputAction.SELECT
        assert event.data["entity_id"] == "test"
