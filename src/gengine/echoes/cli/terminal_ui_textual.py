"""Textual-based Terminal UI controller for Echoes of Emergence.

This module provides a Windows-compatible terminal UI using the Textual framework,
replacing the Rich-based implementation to eliminate border flicker and Unicode issues.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Static

if TYPE_CHECKING:
    from .shell import ShellBackend


class StatusBarWidget(Static):
    """Widget displaying global city status."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.city_name = "Unknown City"
        self.tick = 0
        self.stability = 1.0
        self.alert_count = 0
        self.events_count = 0

    def update_status(
        self,
        city: str,
        tick: int,
        stability: float,
        alerts: int,
        events: int,
    ) -> None:
        """Update status bar data."""
        self.city_name = city
        self.tick = tick
        self.stability = stability
        self.alert_count = alerts
        self.events_count = events
        self.refresh()

    def render(self) -> str:
        """Render status bar content."""
        # Stability bar
        filled = int(self.stability * 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        # Determine color based on stability
        if self.stability >= 0.7:
            stability_color = "green"
        elif self.stability >= 0.4:
            stability_color = "yellow"
        else:
            stability_color = "red"

        # Build status line
        alert_text = (
            f"[red bold]⚠ {self.alert_count}[/]"
            if self.alert_count > 0
            else f"[dim]⚠ {self.alert_count}[/]"
        )
        events_text = (
            f"[cyan]🔔 {self.events_count}[/]"
            if self.events_count > 0
            else f"[dim]🔔 {self.events_count}[/]"
        )
        
        parts = [
            f"🏙 [bold cyan]{self.city_name}[/]",
            f"[yellow]Tick {self.tick}[/]",
            f"[{stability_color}]{bar} {self.stability:.0%}[/]",
            alert_text,
            events_text,
        ]
        
        return "  ".join(parts)


class EventFeedWidget(Static):
    """Widget displaying recent simulation events."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.events: list[dict] = []

    def update_events(self, events: list[dict]) -> None:
        """Update event feed with latest events."""
        self.events = events[-10:]  # Keep last 10 events
        self.refresh()

    def render(self) -> str:
        """Render event feed content."""
        if not self.events:
            return "[dim]No recent events[/]"

        lines = ["[bold]Recent Events[/]"]
        for event in reversed(self.events[-5:]):  # Show last 5
            tick = event.get("tick", 0)
            desc = event.get("description", str(event))
            severity = event.get("severity", "info")
            
            color_map = {
                "critical": "red bold",
                "warning": "yellow",
                "info": "cyan",
            }
            color = color_map.get(severity, "white")
            
            lines.append(f"[dim]T{tick}[/] [{color}]{desc}[/]")

        return "\n".join(lines)


class CommandBarWidget(Static):
    """Widget displaying available commands and keyboard hints."""

    def render(self) -> str:
        """Render command bar content."""
        commands = [
            "[bold cyan]m[/]ap",
            "[bold cyan]a[/]gents",
            "[bold cyan]f[/]actions",
            "[bold cyan]o[/] f[bold cyan]o[/]cus",
            "[bold cyan]n[/]ext",
            "[bold cyan]r[/]un",
            "[bold cyan]s[/]ave",
            "[bold cyan]q[/]uit",
        ]
        return " | ".join(commands)


class MainViewWidget(Static):
    """Widget displaying the main content area (map, agents, etc.)."""

    current_view = reactive("map")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.view_content = "[dim]Loading...[/]"

    def update_content(self, content: str) -> None:
        """Update main view content."""
        self.view_content = content
        self.refresh()

    def render(self) -> str:
        """Render main view content."""
        return self.view_content


class ContextPanelWidget(Static):
    """Widget displaying context/detail information."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context_content = "[dim]No selection[/]"

    def update_content(self, content: str) -> None:
        """Update context panel content."""
        self.context_content = content
        self.refresh()

    def render(self) -> str:
        """Render context panel content."""
        return self.context_content


class EchoesTerminalApp(App):
    """Textual application for Echoes of Emergence Terminal UI."""

    CSS = """
    Screen {
        layout: vertical;
    }
    
    #status {
        height: 3;
        border: solid cyan;
        padding: 0 1;
    }
    
    #body {
        height: 1fr;
    }
    
    #main {
        width: 2fr;
        border: solid white;
        padding: 1;
    }
    
    #context {
        width: 1fr;
        border: solid yellow;
        padding: 1;
    }
    
    #events {
        height: 8;
        border: solid green;
        padding: 1;
    }
    
    #commands {
        height: 3;
        border: solid magenta;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("m", "view_map", "Map"),
        ("a", "view_agents", "Agents"),
        ("f", "view_factions", "Factions"),
        ("o", "view_focus", "Focus"),
        ("n", "tick_next", "Next Tick"),
        ("r", "tick_run", "Run Ticks"),
        ("s", "save_game", "Save"),
        ("q", "quit_app", "Quit"),
        ("?", "show_help", "Help"),
    ]

    def __init__(self, backend: ShellBackend, **kwargs) -> None:
        super().__init__(**kwargs)
        self.backend = backend
        self.current_view = "map"

    def compose(self) -> ComposeResult:  # pragma: no cover - Textual wiring
        """Create child widgets."""
        yield StatusBarWidget(id="status")
        
        with Horizontal(id="body"):
            yield MainViewWidget(id="main")
            yield ContextPanelWidget(id="context")
        
        yield EventFeedWidget(id="events")
        yield CommandBarWidget(id="commands")
        yield Footer()

    def on_mount(self) -> None:  # pragma: no cover - Textual lifecycle hook
        """Initialize after mounting."""
        self.title = "Echoes of Emergence"
        self.sub_title = "Terminal UI"
        self.refresh_ui()

    def action_view_map(self) -> None:  # pragma: no cover - Textual action
        """Switch to map view."""
        self.current_view = "map"
        self.refresh_ui()

    def action_view_agents(self) -> None:  # pragma: no cover - Textual action
        """Switch to agents view."""
        self.current_view = "agents"
        self.refresh_ui()

    def action_view_factions(self) -> None:  # pragma: no cover - Textual action
        """Switch to factions view."""
        self.current_view = "factions"
        self.refresh_ui()

    def action_view_focus(self) -> None:  # pragma: no cover - Textual action
        """Switch to focus view."""
        self.current_view = "focus"
        self.refresh_ui()

    def action_tick_next(self) -> None:  # pragma: no cover - Textual action
        """Advance one tick."""
        if hasattr(self.backend, "state"):
            # Execute next tick
            from ..sim import advance_ticks
            reports = advance_ticks(self.backend.state, 1)
            self.backend.state.tick += 1
            self._record_tick_events(reports)
            self.refresh_ui()

    def action_tick_run(self) -> None:  # pragma: no cover - Textual action
        """Run multiple ticks."""
        if hasattr(self.backend, "state"):
            # Execute 5 ticks
            from ..sim import advance_ticks
            reports = advance_ticks(self.backend.state, 5)
            self.backend.state.tick += 5
            self._record_tick_events(reports)
            self.refresh_ui()

    def action_save_game(self) -> None:  # pragma: no cover - Textual action
        """Save game state."""
        # TODO: Implement save dialog
        pass

    def action_quit_app(self) -> None:  # pragma: no cover - Textual action
        """Quit the application."""
        self.exit()

    def action_show_help(self) -> None:  # pragma: no cover - Textual action
        """Show help screen."""
        # TODO: Implement help screen
        pass

    def _record_tick_events(self, reports) -> None:  # pragma: no cover - UI helper
        """Record events from tick reports."""
        events_widget = self.query_one("#events", EventFeedWidget)
        
        if not reports:
            return

        for report in reports:
            tick = getattr(report, "tick", 0)
            for event in getattr(report, "events", []) or []:
                if isinstance(event, dict):
                    event_entry = {"tick": tick, **event}
                else:
                    event_entry = {
                        "tick": tick,
                        "description": str(event),
                        "severity": "info",
                    }
                events_widget.events.append(event_entry)
        
        events_widget.refresh()

    def refresh_ui(self) -> None:  # pragma: no cover - UI helper
        """Refresh all UI components."""
        # Update status bar
        status_widget = self.query_one("#status", StatusBarWidget)
        if hasattr(self.backend, "state"):
            state = self.backend.state
            status_widget.update_status(
                city=state.city.name,
                tick=state.tick,
                stability=state.environment.stability,
                alerts=0,  # TODO: Extract alerts
                events=len(self.query_one("#events", EventFeedWidget).events),
            )

        # Update main view based on current view
        main_widget = self.query_one("#main", MainViewWidget)
        context_widget = self.query_one("#context", ContextPanelWidget)

        if self.current_view == "map":
            main_widget.update_content(self._render_map_view())
            context_widget.update_content("[dim]Map view active[/]")
        elif self.current_view == "agents":
            main_widget.update_content(self._render_agents_view())
            context_widget.update_content("[dim]Agents view active[/]")
        elif self.current_view == "factions":
            main_widget.update_content(self._render_factions_view())
            context_widget.update_content("[dim]Factions view active[/]")
        elif self.current_view == "focus":
            main_widget.update_content(self._render_focus_view())
            context_widget.update_content("[dim]Focus view active[/]")

    def _render_map_view(self) -> str:
        """Render map view content."""
        if not hasattr(self.backend, "state"):
            return "[dim]No state available[/]"

        state = self.backend.state
        lines = ["[bold cyan]City Map[/]", ""]
        
        for district in state.city.districts:
            modifiers = getattr(district, "modifiers", None)
            unrest = getattr(district, "unrest", None)
            if unrest is None and modifiers is not None:
                unrest = modifiers.unrest
            if unrest is None:
                unrest = 0.0

            pollution = getattr(district, "pollution", None)
            if pollution is None and modifiers is not None:
                pollution = modifiers.pollution
            if pollution is None:
                pollution = 0.0
            
            lines.append(
                f"[bold]{district.name}[/] "
                f"[yellow]Unrest:{unrest:.1f}[/] "
                f"[green]Pollution:{pollution:.1f}[/]"
            )

        return "\n".join(lines)

    def _render_agents_view(self) -> str:
        """Render agents view content."""
        if not hasattr(self.backend, "state"):
            return "[dim]No state available[/]"

        state = self.backend.state
        lines = ["[bold cyan]Agents[/]", ""]
        
        if not state.agents:
            return "[dim]No agents available[/]"

        for agent in state.agents.values():
            lines.append(f"[bold]{agent.name}[/] - {agent.faction_id or 'Independent'}")

        return "\n".join(lines)

    def _render_factions_view(self) -> str:
        """Render factions view content."""
        if not hasattr(self.backend, "state"):
            return "[dim]No state available[/]"

        state = self.backend.state
        lines = ["[bold cyan]Factions[/]", ""]
        
        if not state.factions:
            return "[dim]No factions available[/]"

        for faction in state.factions.values():
            legitimacy = faction.legitimacy if hasattr(faction, 'legitimacy') else 0.5
            lines.append(
                f"[bold]{faction.name}[/] "
                f"[yellow]Legitimacy:{legitimacy:.1%}[/]"
            )

        return "\n".join(lines)

    def _render_focus_view(self) -> str:
        """Render focus management view content."""
        return "[bold cyan]Focus Management[/]\n\n[dim]Focus controls coming soon[/]"


class TextualTerminalUIController:
    """Controller for Textual-based Terminal UI.
    
    This controller provides a Windows-compatible alternative to the Rich-based UI,
    eliminating border flicker and Unicode line height issues.
    """

    def __init__(self, backend: ShellBackend):
        """Initialize the Textual Terminal UI controller.
        
        Args:
            backend: Shell backend (local or service)
        """
        self.backend = backend
        self.app = EchoesTerminalApp(backend=backend)

    def run(self) -> None:
        """Run the Textual application."""
        self.app.run()
