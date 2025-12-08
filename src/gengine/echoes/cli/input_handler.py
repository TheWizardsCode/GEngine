"""Input handling for Terminal UI keyboard and mouse events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class InputAction(Enum):
    """Actions that can be triggered by input events."""

    # Navigation
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"

    # Selection
    SELECT = "select"
    DESELECT = "deselect"

    # View switching
    VIEW_MAP = "view_map"
    VIEW_AGENTS = "view_agents"
    VIEW_FACTIONS = "view_factions"
    VIEW_FOCUS = "view_focus"

    # Overlay toggling
    TOGGLE_OVERLAY_UNREST = "toggle_overlay_unrest"
    TOGGLE_OVERLAY_POLLUTION = "toggle_overlay_pollution"
    TOGGLE_OVERLAY_SECURITY = "toggle_overlay_security"
    TOGGLE_OVERLAY_PROSPERITY = "toggle_overlay_prosperity"
    TOGGLE_OVERLAY_OFF = "toggle_overlay_off"

    # Simulation commands
    TICK_NEXT = "tick_next"
    TICK_RUN = "tick_run"
    FOCUS_CLEAR = "focus_clear"
    FOCUS_SET = "focus_set"

    # UI commands
    HELP = "help"
    QUIT = "quit"
    SAVE = "save"


@dataclass
class InputEvent:
    """Represents a processed input event."""

    action: InputAction
    data: Optional[dict] = None


class InputHandler:
    """Handles keyboard input and maps to UI actions."""

    # Default key mappings
    KEY_MAPPINGS = {
        # Navigation
        "up": InputAction.MOVE_UP,
        "down": InputAction.MOVE_DOWN,
        "left": InputAction.MOVE_LEFT,
        "right": InputAction.MOVE_RIGHT,
        "k": InputAction.MOVE_UP,
        "j": InputAction.MOVE_DOWN,
        "h": InputAction.MOVE_LEFT,
        "l": InputAction.MOVE_RIGHT,
        # Selection
        "enter": InputAction.SELECT,
        "escape": InputAction.DESELECT,
        # View switching
        "m": InputAction.VIEW_MAP,
        "a": InputAction.VIEW_AGENTS,
        "f": InputAction.VIEW_FACTIONS,
        "o": InputAction.VIEW_FOCUS,
        # Overlay toggling
        "1": InputAction.TOGGLE_OVERLAY_UNREST,
        "2": InputAction.TOGGLE_OVERLAY_POLLUTION,
        "3": InputAction.TOGGLE_OVERLAY_SECURITY,
        "4": InputAction.TOGGLE_OVERLAY_PROSPERITY,
        "0": InputAction.TOGGLE_OVERLAY_OFF,
        # Simulation commands
        "n": InputAction.TICK_NEXT,
        "r": InputAction.TICK_RUN,
        "c": InputAction.FOCUS_CLEAR,
        # UI commands
        "?": InputAction.HELP,
        "q": InputAction.QUIT,
        "s": InputAction.SAVE,
    }

    def __init__(self, custom_mappings: Optional[dict[str, InputAction]] = None):
        """Initialize input handler with optional custom key mappings.

        Args:
            custom_mappings: Optional dictionary to override default key mappings
        """
        self.mappings = self.KEY_MAPPINGS.copy()
        if custom_mappings:
            self.mappings.update(custom_mappings)

    def handle_key(self, key: str) -> Optional[InputEvent]:
        """Process a key press and return an InputEvent if mapped.

        Args:
            key: The key that was pressed (normalized to lowercase)

        Returns:
            InputEvent if key is mapped, None otherwise
        """
        key_lower = key.lower()
        if key_lower in self.mappings:
            return InputEvent(action=self.mappings[key_lower])
        return None

    def get_key_hints(self) -> dict[str, str]:
        """Get user-friendly key hints for display.

        Returns:
            Dictionary mapping action descriptions to key combinations
        """
        return {
            "Navigate": "↑↓←→ or hjkl",
            "Select": "Enter",
            "Views": "m=Map a=Agents f=Factions o=Focus",
            "Overlays": "1=Unrest 2=Pollution 3=Security 4=Prosperity 0=Off",
            "Actions": "n=Next r=Run c=Clear s=Save",
            "Help": "? q=Quit",
        }
