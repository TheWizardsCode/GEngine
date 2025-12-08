"""Screen layout manager for Terminal UI mode.

This module provides the foundational layout system that organizes
the terminal screen into regions for the game's UI components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.layout import Layout


@dataclass
class UIState:
    """Tracks the current state of the UI across components."""

    current_view: str = "map"
    selected_entity: Optional[str] = None
    selected_entity_type: Optional[str] = None  # "district", "agent", "faction"
    event_filter: str = "all"
    focus_district: Optional[str] = None
    show_overlay: Optional[str] = None  # None, "unrest", "pollution", "prosperity"
    event_buffer: list[dict] = field(default_factory=list)


class ScreenLayout:
    """Manages the screen layout for the Terminal UI.

    Organizes the screen into regions:
    - Header: Global status bar
    - Main: Primary view area (map, district detail, etc.)
    - Context: Entity detail panel
    - Events: Event feed
    - Commands: Command bar
    """

    MIN_WIDTH = 80
    MIN_HEIGHT = 24

    def __init__(self, console: Console):
        self.console = console
        self.layout = Layout()
        self._locked_size: tuple[int, int] | None = None
        self._configure_regions()

    def _configure_regions(self) -> None:
        """Set up the layout regions with appropriate sizing."""
        # Split vertically: header, body, events, commands
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="events", size=8),
            Layout(name="commands", size=3),
        )

        # Split body horizontally: main view (larger) and context panel
        self.layout["body"].split_row(
            Layout(name="main", ratio=2),
            Layout(name="context", ratio=1),
        )

    def check_terminal_size(self) -> tuple[bool, str]:
        """Check if terminal meets minimum size requirements.

        Returns:
            Tuple of (is_valid, message)
        """
        width = self.console.width
        height = self.console.height

        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            msg = (
                f"Terminal too small. Need at least "
                f"{self.MIN_WIDTH}x{self.MIN_HEIGHT}, "
                f"got {width}x{height}. Please resize your terminal."
            )
            return False, msg

        return True, ""

    def lock_dimensions(self, width: int, height: int) -> None:
        """Lock the layout to a fixed terminal size.

        Args:
            width: Terminal width in characters
            height: Terminal height in rows
        """

        self._locked_size = (height, width)
        self.layout.size = (height, width)

    def sync_dimensions(self) -> None:
        """Ensure the layout matches the locked or current console size."""
        if self._locked_size is not None:
            height, width = self._locked_size
        else:
            height = self.console.height
            width = self.console.width

        self.layout.size = (height, width)

    def update_region(self, region_name: str, content: object) -> None:
        """Update a specific layout region with new content.

        Args:
            region_name: Name of the region
                        ("header", "main", "context", "events", "commands")
            content: Rich renderable content to display
        """
        if region_name in ["header", "main", "context", "events", "commands"]:
            self.layout[region_name].update(content)
        else:
            raise ValueError(f"Unknown region: {region_name}")

    def render(self) -> None:
        """Render the entire layout to the console."""
        self.console.print(self.layout)

    def clear(self) -> None:
        """Clear the console."""
        self.console.clear()
