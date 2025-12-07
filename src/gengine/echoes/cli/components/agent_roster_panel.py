"""Interactive agent roster panel with keyboard navigation and selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel

if TYPE_CHECKING:
    pass


@dataclass
class AgentRosterState:
    """State for the interactive agent roster panel."""
    
    selected_index: int = 0
    agents_data: list[dict[str, Any]] = field(default_factory=list)
    show_detail: bool = False
    
    def select_next(self) -> None:
        """Move selection to next agent."""
        if self.agents_data:
            self.selected_index = (self.selected_index + 1) % len(self.agents_data)
    
    def select_previous(self) -> None:
        """Move selection to previous agent."""
        if self.agents_data:
            self.selected_index = (self.selected_index - 1) % len(self.agents_data)
    
    def toggle_detail(self) -> None:
        """Toggle detail view on/off."""
        self.show_detail = not self.show_detail
    
    def get_selected_agent(self) -> dict[str, Any] | None:
        """Get currently selected agent data."""
        if 0 <= self.selected_index < len(self.agents_data):
            return self.agents_data[self.selected_index]
        return None
    
    def update_agents(self, game_state: dict[str, Any]) -> None:
        """Update agents data from game state."""
        # Import here to avoid circular import
        from ..views.agent_view import prepare_agent_roster_data
        
        self.agents_data = prepare_agent_roster_data(game_state)
        # Clamp selection to valid range
        if self.agents_data:
            self.selected_index = min(self.selected_index, len(self.agents_data) - 1)
        else:
            self.selected_index = 0


class AgentRosterPanel:
    """Interactive agent roster panel component.
    
    Provides keyboard navigation (arrow keys, Enter) and real-time updates
    as simulation state changes.
    """
    
    def __init__(self, console: Console | None = None):
        """Initialize the agent roster panel.
        
        Args:
            console: Rich Console instance (creates new one if None)
        """
        self.console = console or Console()
        self.state = AgentRosterState()
        self.tick = 0
    
    def update(self, game_state: dict[str, Any], tick: int = 0) -> None:
        """Update panel with current game state.
        
        Args:
            game_state: Full game state dictionary
            tick: Current simulation tick
        """
        self.state.update_agents(game_state)
        self.tick = tick
    
    def handle_key(self, key: str) -> bool:
        """Handle keyboard input.
        
        Args:
            key: Key pressed ('up', 'down', 'enter', etc.)
            
        Returns:
            True if key was handled, False otherwise
        """
        if key in ('up', 'k'):
            self.state.select_previous()
            return True
        elif key in ('down', 'j'):
            self.state.select_next()
            return True
        elif key in ('enter', 'return'):
            self.state.toggle_detail()
            return True
        elif key in ('escape', 'q') and self.state.show_detail:
            self.state.show_detail = False
            return True
        return False
    
    def render(self, tick: int = 0) -> Panel | Layout:
        """Render the agent roster panel.
        
        Args:
            tick: Current simulation tick
            
        Returns:
            Rich Panel or Layout with agent roster (and optional detail)
        """
        # Import here to avoid circular import
        from ..views.agent_view import render_agent_roster
        
        if self.state.show_detail:
            # Show split view: roster + detail
            layout = Layout()
            layout.split_row(
                Layout(
                    render_agent_roster(
                        self.state.agents_data,
                        tick=tick,
                        selected_index=self.state.selected_index
                    ),
                    name="roster",
                    ratio=2
                ),
                Layout(
                    self._render_detail_or_help(tick),
                    name="detail",
                    ratio=1
                )
            )
            return layout
        else:
            # Show just the roster
            return render_agent_roster(
                self.state.agents_data,
                tick=tick,
                selected_index=self.state.selected_index
            )
    
    def _render_detail_or_help(self, tick: int) -> Panel:
        """Render agent detail panel or help text.
        
        Args:
            tick: Current simulation tick
            
        Returns:
            Rich Panel with agent detail or help
        """
        # Import here to avoid circular import
        from rich.text import Text

        from ..views.agent_view import render_agent_detail
        
        selected = self.state.get_selected_agent()
        if selected:
            return render_agent_detail(selected, tick=tick)
        else:
            return Panel(
                Text(
                    "No agent selected.\n\n"
                    "Use ↑↓ to navigate\n"
                    "Press Enter to view details",
                    justify="center",
                    style="dim"
                ),
                title="[bold]Help[/bold]",
                border_style="dim"
            )
    
    def get_keyboard_hints(self) -> str:
        """Get keyboard shortcut hints for display.
        
        Returns:
            String with keyboard hints
        """
        if self.state.show_detail:
            return "↑↓: Navigate | Esc: Close detail | Enter: Toggle"
        else:
            return "↑↓: Navigate | Enter: View detail | q: Quit"
