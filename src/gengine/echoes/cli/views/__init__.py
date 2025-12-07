"""View mode implementations for Terminal UI.

Views prepare and render different modes of the UI:
- Map view: City overview with districts
- Agent view: Agent roster and details
- Faction view: Faction overview and power dynamics
- Focus view: Focus management and budget allocation
"""

from .agent_view import (
    prepare_agent_roster_data,
    render_agent_detail,
    render_agent_roster,
)
from .faction_view import (
    prepare_faction_overview_data,
    render_faction_detail,
    render_faction_overview,
)
from .focus_view import (
    prepare_focus_data,
    render_focus_management,
    render_focus_selection,
)
from .map_view import prepare_map_view_data, render_map_view

__all__ = [
    # Map view
    "prepare_map_view_data",
    "render_map_view",
    # Agent view
    "prepare_agent_roster_data",
    "render_agent_roster",
    "render_agent_detail",
    # Faction view
    "prepare_faction_overview_data",
    "render_faction_overview",
    "render_faction_detail",
    # Focus view
    "prepare_focus_data",
    "render_focus_management",
    "render_focus_selection",
]
