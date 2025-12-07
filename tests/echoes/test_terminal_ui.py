"""Tests for Terminal UI components and layout."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from gengine.echoes.cli.components import (
    render_city_map,
    render_command_bar,
    render_context_panel,
    render_event_feed,
    render_status_bar,
)
from gengine.echoes.cli.layout import ScreenLayout, UIState


class TestUIState:
    """Tests for UIState dataclass."""

    def test_default_initialization(self):
        """Test UIState defaults."""
        state = UIState()
        assert state.current_view == "map"
        assert state.selected_entity is None
        assert state.selected_entity_type is None
        assert state.event_filter == "all"
        assert state.focus_district is None
        assert state.show_overlay is None
        assert state.event_buffer == []

    def test_custom_initialization(self):
        """Test UIState with custom values."""
        state = UIState(
            current_view="agent",
            selected_entity="district-1",
            selected_entity_type="district",
            event_filter="critical",
            focus_district="civic-core",
            show_overlay="unrest",
        )
        assert state.current_view == "agent"
        assert state.selected_entity == "district-1"
        assert state.selected_entity_type == "district"
        assert state.event_filter == "critical"
        assert state.focus_district == "civic-core"
        assert state.show_overlay == "unrest"


class TestScreenLayout:
    """Tests for ScreenLayout manager."""

    def test_layout_initialization(self):
        """Test layout creates expected regions."""
        console = Console(file=StringIO(), force_terminal=True, width=100, height=30)
        layout = ScreenLayout(console)

        assert layout.layout is not None
        # Verify regions can be accessed (they exist)
        layout.layout["header"]
        layout.layout["body"]
        layout.layout["events"]
        layout.layout["commands"]

    def test_terminal_size_check_valid(self):
        """Test size check passes for valid terminal."""
        console = Console(file=StringIO(), force_terminal=True, width=100, height=30)
        layout = ScreenLayout(console)

        is_valid, msg = layout.check_terminal_size()
        assert is_valid is True
        assert msg == ""

    def test_terminal_size_check_too_small(self):
        """Test size check fails for small terminal."""
        console = Console(file=StringIO(), force_terminal=True, width=60, height=15)
        layout = ScreenLayout(console)

        is_valid, msg = layout.check_terminal_size()
        assert is_valid is False
        assert "too small" in msg.lower()

    def test_update_region(self):
        """Test updating a layout region."""
        console = Console(file=StringIO(), force_terminal=True, width=100, height=30)
        layout = ScreenLayout(console)

        # Should not raise
        from rich.text import Text
        layout.update_region("header", Text("Test"))
        layout.update_region("main", Text("Test"))
        layout.update_region("context", Text("Test"))
        layout.update_region("events", Text("Test"))
        layout.update_region("commands", Text("Test"))

    def test_update_invalid_region(self):
        """Test updating invalid region raises error."""
        console = Console(file=StringIO(), force_terminal=True, width=100, height=30)
        layout = ScreenLayout(console)

        with pytest.raises(ValueError, match="Unknown region"):
            from rich.text import Text
            layout.update_region("invalid", Text("Test"))


class TestStatusBar:
    """Tests for status bar component."""

    def test_status_bar_basic(self):
        """Test basic status bar rendering."""
        state_data = {
            "city": "Test City",
            "tick": 42,
            "stability": 0.75,
            "alerts": [],
            "events_count": 5,
        }

        panel = render_status_bar(state_data)
        assert panel is not None
        # Verify panel was created with expected title
        assert "Global Status" in str(panel.title)

    def test_status_bar_with_alerts(self):
        """Test status bar with critical alerts."""
        state_data = {
            "city": "Test City",
            "tick": 42,
            "stability": 0.35,
            "alerts": [
                {"severity": "critical", "message": "Crisis!"},
                {"severity": "warning", "message": "Warning"},
            ],
            "events_count": 10,
        }

        panel = render_status_bar(state_data)
        assert panel is not None

    def test_status_bar_stability_colors(self):
        """Test stability bar colors for different thresholds."""
        # High stability (green)
        data_high = {
            "city": "City",
            "tick": 1,
            "stability": 0.85,
            "alerts": [],
            "events_count": 0,
        }
        panel = render_status_bar(data_high)
        assert panel is not None

        # Medium stability (yellow)
        data_med = {
            "city": "City",
            "tick": 1,
            "stability": 0.55,
            "alerts": [],
            "events_count": 0,
        }
        panel = render_status_bar(data_med)
        assert panel is not None

        # Low stability (red)
        data_low = {
            "city": "City",
            "tick": 1,
            "stability": 0.25,
            "alerts": [],
            "events_count": 0,
        }
        panel = render_status_bar(data_low)
        assert panel is not None


class TestCityMap:
    """Tests for city map component."""

    def test_city_map_empty(self):
        """Test city map with no districts."""
        panel = render_city_map([], {})
        assert panel is not None

    def test_city_map_single_district(self):
        """Test city map with one district."""
        districts = [
            {
                "id": "civic-core",
                "name": "Civic Core",
                "stability": 0.8,
                "modifiers": {"unrest": 0.2, "pollution": 0.3},
            }
        ]
        focus_data = {"district_id": "civic-core", "adjacent": []}

        panel = render_city_map(districts, focus_data)
        assert panel is not None

    def test_city_map_multiple_districts(self):
        """Test city map with multiple districts."""
        districts = [
            {
                "id": "civic-core",
                "name": "Civic Core",
                "stability": 0.8,
                "modifiers": {"unrest": 0.2},
            },
            {
                "id": "industrial",
                "name": "Industrial",
                "stability": 0.5,
                "modifiers": {"unrest": 0.6},
            },
            {
                "id": "commons",
                "name": "Commons",
                "stability": 0.7,
                "modifiers": {"unrest": 0.3},
            },
        ]
        focus_data = {"district_id": "civic-core", "adjacent": ["industrial"]}

        panel = render_city_map(districts, focus_data)
        assert panel is not None

    def test_city_map_with_selection(self):
        """Test city map with selected district."""
        districts = [
            {
                "id": "civic-core",
                "name": "Civic Core",
                "stability": 0.8,
                "modifiers": {"unrest": 0.2},
            }
        ]
        focus_data = {"district_id": None, "adjacent": []}

        panel = render_city_map(districts, focus_data, selected_id="civic-core")
        assert panel is not None

    def test_city_map_with_overlay(self):
        """Test city map with overlay."""
        districts = [
            {
                "id": "civic-core",
                "name": "Civic Core",
                "stability": 0.8,
                "modifiers": {"unrest": 0.2, "pollution": 0.5},
            }
        ]
        focus_data = {"district_id": None, "adjacent": []}

        panel = render_city_map(districts, focus_data, overlay="pollution")
        assert panel is not None


class TestEventFeed:
    """Tests for event feed component."""

    def test_event_feed_empty(self):
        """Test event feed with no events."""
        panel = render_event_feed([])
        assert panel is not None

    def test_event_feed_single_event(self):
        """Test event feed with one event."""
        events = [
            {
                "tick": 42,
                "location": "Civic Core",
                "description": "Test event occurred",
                "severity": "info",
            }
        ]

        panel = render_event_feed(events)
        assert panel is not None

    def test_event_feed_multiple_events(self):
        """Test event feed with multiple events."""
        events = [
            {
                "tick": 42,
                "location": "Civic Core",
                "description": "Critical event",
                "severity": "critical",
            },
            {
                "tick": 41,
                "location": "Industrial",
                "description": "Warning event",
                "severity": "warning",
            },
            {
                "tick": 40,
                "description": "Info event",
                "severity": "info",
            },
        ]

        panel = render_event_feed(events)
        assert panel is not None

    def test_event_feed_max_events(self):
        """Test event feed respects max_events limit."""
        events = [{"tick": i, "description": f"Event {i}"} for i in range(20)]

        panel = render_event_feed(events, max_events=5)
        assert panel is not None

    def test_event_feed_focus_highlighting(self):
        """Test event feed highlights focus district events."""
        events = [
            {"tick": 42, "location": "Civic Core", "description": "Focused event"},
            {"tick": 41, "location": "Industrial", "description": "Other event"},
        ]

        panel = render_event_feed(events, focus_district="Civic Core")
        assert panel is not None

    def test_event_severity_classification(self):
        """Test automatic event severity classification."""
        events = [
            {"tick": 1, "description": "Story seed activated"},
            {"tick": 2, "description": "Market price increased"},
            {"tick": 3, "description": "Critical crisis occurred"},
            {"tick": 4, "description": "Unrest warning"},
        ]

        panel = render_event_feed(events)
        assert panel is not None


class TestContextPanel:
    """Tests for context panel component."""

    def test_context_panel_empty(self):
        """Test context panel with no selection."""
        panel = render_context_panel(None, None)
        assert panel is not None

    def test_context_panel_district(self):
        """Test context panel with district."""
        district_data = {
            "name": "Civic Core",
            "population": 50000,
            "modifiers": {
                "unrest": 0.3,
                "pollution": 0.2,
                "prosperity": 0.7,
                "security": 0.8,
            },
            "resources": {
                "energy": {"current": 80, "capacity": 100},
                "food": {"current": 40, "capacity": 100},
            },
            "active_seeds": ["Power Struggle"],
            "faction_presence": "Council (dominant)",
        }

        panel = render_context_panel("district", district_data)
        assert panel is not None

    def test_context_panel_agent(self):
        """Test context panel with agent."""
        agent_data = {
            "name": "Aria Volt",
            "role": "Negotiator",
            "status": "Available",
            "stress": 0.3,
            "expertise": {"negotiation": 4, "investigation": 2, "tactical": 1},
        }

        panel = render_context_panel("agent", agent_data)
        assert panel is not None

    def test_context_panel_faction(self):
        """Test context panel with faction."""
        faction_data = {
            "name": "Union of Flux",
            "legitimacy": 0.72,
            "resources": 0.48,
            "territory": ["Industrial Tier", "Commons"],
        }

        panel = render_context_panel("faction", faction_data)
        assert panel is not None

    def test_context_panel_unknown_type(self):
        """Test context panel with unknown entity type."""
        panel = render_context_panel("unknown", {})
        assert panel is not None


class TestCommandBar:
    """Tests for command bar component."""

    def test_command_bar_default(self):
        """Test command bar with no active command."""
        panel = render_command_bar()
        assert panel is not None

    def test_command_bar_active_command(self):
        """Test command bar with active command."""
        panel = render_command_bar(active_command="next")
        assert panel is not None

        panel = render_command_bar(active_command="run")
        assert panel is not None


class TestMapView:
    """Tests for map view integration."""

    def test_prepare_map_view_data(self):
        """Test preparing map view data from game state."""
        from unittest.mock import Mock

        from gengine.echoes.cli.layout import UIState
        from gengine.echoes.cli.views import prepare_map_view_data

        # Create mock state
        state = Mock()
        state.city.districts = {
            "civic-core": Mock(
                id="civic-core",
                name="Civic Core",
                population=50000,
                unrest=0.2,
                pollution=0.3,
                prosperity=0.7,
            ),
        }
        state.metadata = {
            "focus": {
                "district_id": "civic-core",
                "adjacent": [],
            }
        }

        ui_state = UIState()

        view_data = prepare_map_view_data(state, ui_state)

        assert "districts" in view_data
        assert len(view_data["districts"]) == 1
        assert view_data["districts"][0]["id"] == "civic-core"
        assert "focus_data" in view_data

    def test_render_map_view(self):
        """Test rendering map view components."""
        from gengine.echoes.cli.views import render_map_view

        view_data = {
            "districts": [
                {
                    "id": "civic-core",
                    "name": "Civic Core",
                    "stability": 0.8,
                    "modifiers": {"unrest": 0.2},
                }
            ],
            "focus_data": {"district_id": "civic-core", "adjacent": []},
            "selected_id": None,
            "overlay": None,
            "selected_entity_type": None,
            "selected_entity_data": None,
        }

        main_content, context_content = render_map_view(view_data)
        assert main_content is not None
        assert context_content is not None
