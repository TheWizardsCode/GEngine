"""Interactive Terminal UI controller for Echoes of Emergence.

This module provides the main controller for the interactive terminal UI,
handling real-time rendering, input processing, and state management.
"""

from __future__ import annotations

import sys
import termios
import time
import tty
from typing import TYPE_CHECKING, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .components import (
    render_command_bar,
    render_event_feed,
    render_status_bar,
)
from .input_handler import InputAction, InputHandler
from .layout import ScreenLayout, UIState
from .views import (
    prepare_agent_roster_data,
    prepare_faction_overview_data,
    prepare_focus_data,
    prepare_map_view_data,
    render_agent_roster,
    render_faction_overview,
    render_focus_management,
    render_map_view,
)

if TYPE_CHECKING:
    from ..core import GameState
    from .shell import ShellBackend


class TerminalUIController:
    """Main controller for the interactive terminal UI.

    Manages the event loop, input handling, and real-time rendering of
    the game simulation UI.
    """

    REFRESH_RATE = 0.1  # 10 FPS refresh rate

    def __init__(
        self,
        backend: ShellBackend,
        console: Optional[Console] = None,
    ):
        """Initialize the Terminal UI controller.

        Args:
            backend: Shell backend (local or service)
            console: Rich console instance (creates one if not provided)
        """
        self.backend = backend
        self.console = console or Console()
        self.layout = ScreenLayout(self.console)
        self.ui_state = UIState()
        self.input_handler = InputHandler()
        self.running = False
        self._last_update = 0.0

    def _get_game_state(self) -> GameState:
        """Get the current game state from backend."""
        # For LocalBackend, we can access state directly
        if hasattr(self.backend, "state"):
            return self.backend.state
        # For ServiceBackend, we'd need to fetch it
        # This is a simplified version - real impl would need API call
        raise NotImplementedError("ServiceBackend state access not yet implemented")

    def _prepare_status_data(self) -> dict:
        """Prepare data for status bar component."""
        state = self._get_game_state()
        return {
            "city": state.city.name,
            "tick": state.tick,
            "stability": state.environment.stability,
            "alerts": [],  # TODO: Extract alerts from state
            "events_count": len(self.ui_state.event_buffer),
        }

    def _prepare_event_feed_data(self) -> list[dict]:
        """Prepare data for event feed component."""
        # Use the event buffer from UI state
        return self.ui_state.event_buffer[-10:]  # Show last 10 events

    def _update_components(self) -> None:
        """Update all UI components with latest game state."""
        # Update status bar
        status_data = self._prepare_status_data()
        self.layout.update_region("header", render_status_bar(status_data))

        # Update main view based on current view mode
        if self.ui_state.current_view == "map":
            self._update_map_view()
        elif self.ui_state.current_view == "agents":
            self._update_agents_view()
        elif self.ui_state.current_view == "factions":
            self._update_factions_view()
        elif self.ui_state.current_view == "focus":
            self._update_focus_view()

        # Update event feed
        event_data = self._prepare_event_feed_data()
        self.layout.update_region(
            "events",
            render_event_feed(
                event_data, focus_district=self.ui_state.focus_district
            ),
        )

        # Update command bar
        self.layout.update_region("commands", render_command_bar())

    def _update_map_view(self) -> None:
        """Update the map view components."""
        state = self._get_game_state()
        view_data = prepare_map_view_data(state, self.ui_state)
        main_content, context_content = render_map_view(view_data)
        self.layout.update_region("main", main_content)
        self.layout.update_region("context", context_content)

    def _update_agents_view(self) -> None:
        """Update the agents view components."""
        state = self._get_game_state()
        roster_data = prepare_agent_roster_data(state)
        roster_panel = render_agent_roster(roster_data)
        self.layout.update_region("main", roster_panel)

        # Show agent detail in context if one is selected
        if self.ui_state.selected_entity_type == "agent":
            # TODO: Render agent detail
            self.layout.update_region(
                "context",
                Panel(Text("Agent detail coming soon")),
            )
        else:
            self.layout.update_region(
                "context",
                Panel(Text("Select an agent for details")),
            )

    def _update_factions_view(self) -> None:
        """Update the factions view components."""
        state = self._get_game_state()
        faction_data = prepare_faction_overview_data(state)
        faction_panel = render_faction_overview(faction_data)
        self.layout.update_region("main", faction_panel)

        # Show faction detail in context if one is selected
        if self.ui_state.selected_entity_type == "faction":
            # TODO: Render faction detail
            self.layout.update_region(
                "context",
                Panel(Text("Faction detail coming soon")),
            )
        else:
            self.layout.update_region(
                "context",
                Panel(Text("Select a faction for details")),
            )

    def _update_focus_view(self) -> None:
        """Update the focus management view."""
        state = self._get_game_state()
        focus_data = prepare_focus_data(state)
        focus_panel = render_focus_management(focus_data)
        self.layout.update_region("main", focus_panel)
        self.layout.update_region(
            "context",
            Panel(Text("Press 'c' to clear focus or select a district")),
        )

    def _handle_input_event(self, event) -> bool:
        """Handle a processed input event.

        Args:
            event: The InputEvent to handle

        Returns:
            True if UI should quit, False otherwise
        """
        action = event.action

        # Navigation
        if action == InputAction.MOVE_UP:
            # TODO: Navigate up in current view
            pass
        elif action == InputAction.MOVE_DOWN:
            # TODO: Navigate down in current view
            pass

        # View switching
        elif action == InputAction.VIEW_MAP:
            self.ui_state.current_view = "map"
        elif action == InputAction.VIEW_AGENTS:
            self.ui_state.current_view = "agents"
        elif action == InputAction.VIEW_FACTIONS:
            self.ui_state.current_view = "factions"
        elif action == InputAction.VIEW_FOCUS:
            self.ui_state.current_view = "focus"

        # Overlay toggling
        elif action == InputAction.TOGGLE_OVERLAY_UNREST:
            self.ui_state.show_overlay = (
                None if self.ui_state.show_overlay == "unrest" else "unrest"
            )
        elif action == InputAction.TOGGLE_OVERLAY_POLLUTION:
            self.ui_state.show_overlay = (
                None if self.ui_state.show_overlay == "pollution" else "pollution"
            )
        elif action == InputAction.TOGGLE_OVERLAY_SECURITY:
            self.ui_state.show_overlay = (
                None if self.ui_state.show_overlay == "security" else "security"
            )
        elif action == InputAction.TOGGLE_OVERLAY_PROSPERITY:
            self.ui_state.show_overlay = (
                None if self.ui_state.show_overlay == "prosperity" else "prosperity"
            )
        elif action == InputAction.TOGGLE_OVERLAY_OFF:
            self.ui_state.show_overlay = None

        # Simulation commands
        elif action == InputAction.TICK_NEXT:
            reports = self.backend.advance_ticks(1)
            # Add events from report to event buffer
            if reports:
                for event in reports[0].events:
                    self.ui_state.event_buffer.append(
                        {
                            "tick": reports[0].tick,
                            "description": event,
                            "severity": "info",
                        }
                    )

        elif action == InputAction.FOCUS_CLEAR:
            self.backend.set_focus(None)
            self.ui_state.focus_district = None

        # UI commands
        elif action == InputAction.QUIT:
            return True
        elif action == InputAction.SAVE:
            # TODO: Implement save dialog
            pass

        return False

    def _read_key(self) -> Optional[str]:
        """Read a single key press without blocking.

        Returns:
            The key pressed, or None if no key available
        """
        # This is a simplified version - real implementation would need
        # platform-specific non-blocking keyboard input
        # For now, we'll use a timeout-based approach with input()
        import select

        # Check if input is available
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

    def run(self) -> None:
        """Run the interactive terminal UI event loop."""
        # Check terminal size
        is_valid, msg = self.layout.check_terminal_size()
        if not is_valid:
            self.console.print(f"[red]Error:[/red] {msg}")
            return

        self.running = True

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())

            with Live(
                self.layout.layout,
                console=self.console,
                screen=True,
                refresh_per_second=1 / self.REFRESH_RATE,
            ):
                # Initial render
                self._update_components()

                while self.running:
                    # Check for input
                    key = self._read_key()
                    if key:
                        event = self.input_handler.handle_key(key)
                        if event:
                            should_quit = self._handle_input_event(event)
                            if should_quit:
                                break

                    # Periodic refresh
                    current_time = time.time()
                    if current_time - self._last_update >= self.REFRESH_RATE:
                        self._update_components()
                        self._last_update = current_time

                    # Small sleep to prevent CPU spinning
                    time.sleep(0.01)

        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def run_terminal_ui(backend: ShellBackend) -> None:
    """Run the interactive terminal UI.

    Args:
        backend: Shell backend to use (local or service)
    """
    controller = TerminalUIController(backend)
    controller.run()
