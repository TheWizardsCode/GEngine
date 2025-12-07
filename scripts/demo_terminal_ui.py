#!/usr/bin/env python3
"""Demo script showing the Terminal UI in action.

This script demonstrates the Terminal UI components rendering game state.
Run with: python3 scripts/demo_terminal_ui.py
"""


from rich.console import Console

from gengine.echoes.cli.components import (
    render_city_map,
    render_command_bar,
    render_context_panel,
    render_event_feed,
    render_status_bar,
)
from gengine.echoes.cli.layout import ScreenLayout, UIState


def create_sample_state():
    """Create sample game state for demo."""
    return {
        "city": "Frontier City",
        "tick": 247,
        "stability": 0.68,
        "alerts": [
            {"severity": "critical", "message": "Energy shortage in Industrial Tier"},
            {"severity": "warning", "message": "Unrest rising in Commons"},
        ],
        "events_count": 12,
    }


def create_sample_districts():
    """Create sample districts for demo."""
    return [
        {
            "id": "civic-core",
            "name": "Civic",
            "stability": 0.85,
            "population": 45000,
            "modifiers": {
                "unrest": 0.15,
                "pollution": 0.25,
                "prosperity": 0.75,
                "security": 0.80,
            },
            "resources": {
                "energy": {"current": 180, "capacity": 200},
                "food": {"current": 190, "capacity": 200},
            },
            "active_seeds": [],
            "faction_presence": "Council (dominant)",
        },
        {
            "id": "industrial-tier",
            "name": "Industrial",
            "stability": 0.45,
            "population": 60000,
            "modifiers": {
                "unrest": 0.68,
                "pollution": 0.82,
                "prosperity": 0.38,
                "security": 0.42,
            },
            "resources": {
                "energy": {"current": 30, "capacity": 250},
                "food": {"current": 140, "capacity": 250},
            },
            "active_seeds": ["Power Struggle"],
            "faction_presence": "Union of Flux (dominant)",
        },
        {
            "id": "commons",
            "name": "Commons",
            "stability": 0.62,
            "population": 55000,
            "modifiers": {
                "unrest": 0.52,
                "pollution": 0.35,
                "prosperity": 0.55,
                "security": 0.58,
            },
            "resources": {
                "energy": {"current": 120, "capacity": 180},
                "food": {"current": 160, "capacity": 180},
            },
            "active_seeds": [],
            "faction_presence": "Contested",
        },
        {
            "id": "perimeter-hollow",
            "name": "Perimeter",
            "stability": 0.72,
            "population": 30000,
            "modifiers": {
                "unrest": 0.28,
                "pollution": 0.15,
                "prosperity": 0.68,
                "security": 0.75,
            },
            "resources": {
                "energy": {"current": 90, "capacity": 120},
                "food": {"current": 110, "capacity": 120},
            },
            "active_seeds": [],
            "faction_presence": "",
        },
        {
            "id": "spires",
            "name": "Spires",
            "stability": 0.88,
            "population": 25000,
            "modifiers": {
                "unrest": 0.12,
                "pollution": 0.08,
                "prosperity": 0.92,
                "security": 0.90,
            },
            "resources": {
                "energy": {"current": 100, "capacity": 100},
                "food": {"current": 95, "capacity": 100},
            },
            "active_seeds": [],
            "faction_presence": "Elite Council",
        },
        {
            "id": "wilds",
            "name": "Wilds",
            "stability": 0.55,
            "population": 15000,
            "modifiers": {
                "unrest": 0.45,
                "pollution": 0.60,
                "prosperity": 0.35,
                "security": 0.40,
            },
            "resources": {
                "energy": {"current": 40, "capacity": 80},
                "food": {"current": 70, "capacity": 80},
            },
            "active_seeds": [],
            "faction_presence": "Fringe groups",
        },
    ]


def create_sample_events():
    """Create sample events for demo."""
    return [
        {
            "tick": 247,
            "location": "Industrial Tier",
            "description": "Energy shortage persists (3 ticks)",
            "severity": "critical",
        },
        {
            "tick": 247,
            "location": "Commons",
            "description": "Unrest rising due to spillover from Industrial",
            "severity": "warning",
        },
        {
            "tick": 246,
            "location": "Industrial Tier",
            "description": "Union of Flux invested resources",
            "severity": "economy",
        },
        {
            "tick": 246,
            "description": "Story seed 'Power Struggle' activated",
            "severity": "story",
        },
        {
            "tick": 245,
            "location": "Civic Core",
            "description": "Agent Aria Volt inspected district",
            "severity": "info",
        },
        {
            "tick": 244,
            "location": "Industrial Tier",
            "description": "Pollution diffused to neighboring districts",
            "severity": "warning",
        },
        {
            "tick": 243,
            "description": "Market prices adjusted: energy +0.15",
            "severity": "economy",
        },
    ]


def create_sample_focus():
    """Create sample focus data for demo."""
    return {
        "district_id": "industrial-tier",
        "adjacent": ["commons", "wilds"],
    }


def main():
    """Run the Terminal UI demo."""
    print("Terminal UI Demo - Echoes of Emergence")
    print("=" * 80)
    print()
    print("This demo shows the Terminal UI components in action.")
    print("Press Ctrl+C to exit.\n")

    # Create console
    console = Console()

    # Create layout
    layout = ScreenLayout(console)

    # Check terminal size
    is_valid, msg = layout.check_terminal_size()
    if not is_valid:
        console.print(f"[red]Error: {msg}[/red]")
        return

    # Create UI state
    ui_state = UIState(
        current_view="map",
        selected_entity="industrial-tier",
        selected_entity_type="district",
        focus_district="industrial-tier",
    )

    # Get sample data
    state_data = create_sample_state()
    districts = create_sample_districts()
    events = create_sample_events()
    focus_data = create_sample_focus()

    # Find selected district data
    selected_district = None
    for dist in districts:
        if dist["id"] == ui_state.selected_entity:
            selected_district = dist
            break

    # Render components
    try:
        # Status bar
        status_bar = render_status_bar(state_data)

        # City map
        city_map = render_city_map(
            districts, focus_data, selected_id=ui_state.selected_entity
        )

        # Context panel
        context = render_context_panel(
            ui_state.selected_entity_type, selected_district
        )

        # Event feed
        event_feed = render_event_feed(events, focus_district="Industrial Tier")

        # Command bar
        command_bar = render_command_bar()

        # Update layout
        layout.update_region("header", status_bar)
        layout.update_region("main", city_map)
        layout.update_region("context", context)
        layout.update_region("events", event_feed)
        layout.update_region("commands", command_bar)

        # Render the layout
        console.clear()
        layout.render()

        # Print instructions
        console.print()
        console.print(
            "[dim]This is a static demo. The full UI will support "
            "keyboard navigation and real-time updates.[/dim]"
        )
        console.print(
            "[dim]See the implementation in src/gengine/echoes/cli/components/[/dim]"
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted.[/yellow]")


if __name__ == "__main__":
    main()
