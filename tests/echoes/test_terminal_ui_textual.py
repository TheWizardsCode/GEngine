"""Tests for Textual-based Terminal UI implementation."""

from __future__ import annotations

from gengine.echoes.cli.terminal_ui_textual import (
    CommandBarWidget,
    ContextPanelWidget,
    EchoesTerminalApp,
    EventFeedWidget,
    MainViewWidget,
    StatusBarWidget,
    TextualTerminalUIController,
)
from gengine.echoes.sim import SimEngine


class MockBackend:
    """Mock backend for testing."""

    def __init__(self):
        engine = SimEngine()
        engine.initialize_state(world="default")
        self.state = engine.state


class TestStatusBarWidget:
    """Tests for StatusBarWidget."""

    def test_initialization(self):
        """Test widget can be created."""
        widget = StatusBarWidget()
        assert widget.city_name == "Unknown City"
        assert widget.tick == 0
        assert widget.stability == 1.0

    def test_update_status(self):
        """Test status can be updated."""
        widget = StatusBarWidget()
        widget.update_status(
            city="Test City",
            tick=42,
            stability=0.75,
            alerts=2,
            events=5,
        )
        assert widget.city_name == "Test City"
        assert widget.tick == 42
        assert widget.stability == 0.75
        assert widget.alert_count == 2
        assert widget.events_count == 5

    def test_render_returns_string(self):
        """Test render produces a string."""
        widget = StatusBarWidget()
        widget.update_status(
            city="Test City",
            tick=10,
            stability=0.8,
            alerts=0,
            events=3,
        )
        result = widget.render()
        assert isinstance(result, str)
        assert "Test City" in result
        assert "10" in result


class TestEventFeedWidget:
    """Tests for EventFeedWidget."""

    def test_initialization(self):
        """Test widget can be created."""
        widget = EventFeedWidget()
        assert widget.events == []

    def test_update_events(self):
        """Test events can be updated."""
        widget = EventFeedWidget()
        events = [
            {"tick": 1, "description": "Event 1", "severity": "info"},
            {"tick": 2, "description": "Event 2", "severity": "warning"},
        ]
        widget.update_events(events)
        assert len(widget.events) == 2

    def test_render_empty(self):
        """Test render with no events."""
        widget = EventFeedWidget()
        result = widget.render()
        assert isinstance(result, str)
        assert "No recent events" in result

    def test_render_with_events(self):
        """Test render with events."""
        widget = EventFeedWidget()
        events = [
            {"tick": 1, "description": "Test event", "severity": "info"},
        ]
        widget.update_events(events)
        result = widget.render()
        assert isinstance(result, str)
        assert "Test event" in result


class TestCommandBarWidget:
    """Tests for CommandBarWidget."""

    def test_initialization(self):
        """Test widget can be created."""
        widget = CommandBarWidget()
        assert widget is not None

    def test_render_returns_string(self):
        """Test render produces a string with commands."""
        widget = CommandBarWidget()
        result = widget.render()
        assert isinstance(result, str)
        # Check for command text (accounting for Rich markup)
        assert "ap" in result  # "m[/]ap"
        assert "gents" in result.lower()
        assert "uit" in result.lower()  # "q[/]uit"


class TestMainViewWidget:
    """Tests for MainViewWidget."""

    def test_initialization(self):
        """Test widget can be created."""
        widget = MainViewWidget()
        assert widget.current_view == "map"

    def test_update_content(self):
        """Test content can be updated."""
        widget = MainViewWidget()
        widget.update_content("Test content")
        assert widget.view_content == "Test content"

    def test_render_returns_string(self):
        """Test render produces a string."""
        widget = MainViewWidget()
        widget.update_content("Custom view")
        result = widget.render()
        assert isinstance(result, str)
        assert "Custom view" in result


class TestContextPanelWidget:
    """Tests for ContextPanelWidget."""

    def test_initialization(self):
        """Test widget can be created."""
        widget = ContextPanelWidget()
        assert widget.context_content == "[dim]No selection[/]"

    def test_update_content(self):
        """Test content can be updated."""
        widget = ContextPanelWidget()
        widget.update_content("District details")
        assert widget.context_content == "District details"

    def test_render_returns_string(self):
        """Test render produces a string."""
        widget = ContextPanelWidget()
        result = widget.render()
        assert isinstance(result, str)


class TestEchoesTerminalApp:
    """Tests for EchoesTerminalApp."""

    def test_initialization(self):
        """Test app can be created with backend."""
        backend = MockBackend()
        app = EchoesTerminalApp(backend=backend)
        assert app.backend is backend
        assert app.current_view == "map"

    def test_has_required_bindings(self):
        """Test app has required keyboard bindings."""
        backend = MockBackend()
        app = EchoesTerminalApp(backend=backend)
        
        # Check that bindings are defined
        assert len(app.BINDINGS) > 0
        
        # Extract just the keys from bindings
        binding_keys = [b[0] for b in app.BINDINGS]
        
        # Verify essential keys are present
        assert "m" in binding_keys  # Map
        assert "a" in binding_keys  # Agents
        assert "f" in binding_keys  # Factions
        assert "q" in binding_keys  # Quit


class TestTextualTerminalUIController:
    """Tests for TextualTerminalUIController."""

    def test_initialization(self):
        """Test controller can be created."""
        backend = MockBackend()
        controller = TextualTerminalUIController(backend)
        assert controller.backend is backend
        assert controller.app is not None
        assert isinstance(controller.app, EchoesTerminalApp)
