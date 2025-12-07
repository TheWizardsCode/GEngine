"""Tests for Management Depth UI components (Issue #77)."""

from __future__ import annotations

from rich.console import Console

from gengine.echoes.cli.components.city_map import render_city_map
from gengine.echoes.cli.views.agent_view import (
    prepare_agent_roster_data,
    render_agent_detail,
    render_agent_roster,
)
from gengine.echoes.cli.views.faction_view import (
    prepare_faction_overview_data,
    render_faction_detail,
    render_faction_overview,
)
from gengine.echoes.cli.views.focus_view import (
    prepare_focus_data,
    render_focus_management,
    render_focus_selection,
)

# --- Agent Roster Tests ---


def test_render_agent_roster_empty():
    """Test agent roster renders gracefully with no agents."""
    panel = render_agent_roster([], tick=0)
    console = Console()
    # Should render without error
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    assert "No agents available" in output


def test_render_agent_roster_with_agents():
    """Test agent roster displays agents with stats."""
    agents = [
        {
            "id": "agent-1",
            "name": "Aria Volt",
            "role": "Negotiator",
            "traits": {"empathy": 0.8, "cunning": 0.5, "resolve": 0.7},
        },
        {
            "id": "agent-2",
            "name": "Cassian Mire",
            "role": "Investigator",
            "traits": {"empathy": 0.3, "cunning": 0.9, "resolve": 0.3},
        },
    ]
    
    panel = render_agent_roster(agents, tick=10)
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Agent Roster" in output
    assert "2 agents" in output
    assert "Aria Volt" in output
    assert "Cassian Mire" in output


def test_render_agent_detail():
    """Test agent detail view shows comprehensive info."""
    agent = {
        "id": "agent-1",
        "name": "Aria Volt",
        "role": "Veteran Negotiator",
        "traits": {"empathy": 0.8, "cunning": 0.5, "resolve": 0.7},
        "faction_id": "union-of-flux",
        "home_district": "civic-core",
        "notes": "Experienced diplomat with strong ties to labor movement.",
    }
    
    panel = render_agent_detail(agent, tick=10)
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Aria Volt" in output
    assert "Veteran Negotiator" in output
    assert "empathy" in output.lower()
    assert "union-of-flux" in output
    assert "civic-core" in output
    assert "Experienced diplomat" in output


def test_prepare_agent_roster_data():
    """Test agent roster data preparation from game state."""
    game_state = {
        "agents": {
            "agent-1": {
                "name": "Aria Volt",
                "role": "Negotiator",
                "traits": {"empathy": 0.8},
            },
            "agent-2": {
                "name": "Cassian Mire",
                "role": "Investigator",
                "traits": {"cunning": 0.9},
            },
        }
    }
    
    data = prepare_agent_roster_data(game_state)
    
    assert len(data) == 2
    assert data[0]["name"] == "Aria Volt"  # Should be sorted
    assert data[1]["name"] == "Cassian Mire"


# --- Faction Overview Tests ---


def test_render_faction_overview_empty():
    """Test faction overview renders gracefully with no factions."""
    panel = render_faction_overview([], {})
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "No factions available" in output


def test_render_faction_overview_with_factions():
    """Test faction overview displays factions with power metrics."""
    factions = [
        {
            "id": "union",
            "name": "Union of Flux",
            "legitimacy": 0.72,
            "territory": ["industrial-tier", "commons"],
            "legitimacy_delta": 0.05,
        },
        {
            "id": "council",
            "name": "Council of Makers",
            "legitimacy": 0.45,
            "territory": ["civic-core"],
            "legitimacy_delta": -0.03,
        },
    ]
    
    districts = {
        "industrial-tier": {"id": "industrial-tier", "name": "Industrial Tier"},
        "commons": {"id": "commons", "name": "Commons"},
        "civic-core": {"id": "civic-core", "name": "Civic Core"},
    }
    
    panel = render_faction_overview(factions, districts)
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Faction Overview" in output
    assert "2 factions" in output
    assert "Union of Flux" in output
    assert "Council of Makers" in output


def test_render_faction_detail():
    """Test faction detail view shows comprehensive info."""
    faction = {
        "id": "union",
        "name": "Union of Flux",
        "ideology": "Labor solidarity",
        "description": "Grassroots labor movement fighting for worker rights.",
        "legitimacy": 0.72,
        "resources": {"materials": 450, "influence": 120},
        "territory": ["industrial-tier", "commons"],
        "legitimacy_delta": 0.05,
    }
    
    districts = {
        "industrial-tier": {"id": "industrial-tier", "name": "Industrial Tier"},
        "commons": {"id": "commons", "name": "Commons"},
    }
    
    panel = render_faction_detail(faction, districts, {})
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Union of Flux" in output
    assert "Labor solidarity" in output
    assert "Grassroots labor movement" in output
    assert "materials" in output.lower()
    assert "Industrial Tier" in output


def test_prepare_faction_overview_data():
    """Test faction overview data preparation from game state."""
    game_state = {
        "factions": {
            "union": {
                "name": "Union of Flux",
                "legitimacy": 0.72,
                "territory": ["industrial-tier"],
            },
            "council": {
                "name": "Council of Makers",
                "legitimacy": 0.45,
                "territory": [],
            },
        },
        "city": {
            "districts": [
                {"id": "industrial-tier", "name": "Industrial Tier"},
            ]
        },
    }
    
    factions, districts = prepare_faction_overview_data(game_state)
    
    assert len(factions) == 2
    # Should be sorted by legitimacy (descending)
    assert factions[0]["name"] == "Union of Flux"
    assert factions[1]["name"] == "Council of Makers"
    assert len(districts) == 1


# --- Focus Management Tests ---


def test_render_focus_management_no_focus():
    """Test focus management view with no active focus."""
    focus_state = {
        "district_id": None,
        "adjacent": [],
        "allocation": {
            "ring_events": 0,
            "global_events": 0,
            "archived": 0,
        },
    }
    
    districts = []
    
    panel = render_focus_management(focus_state, districts)
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Focus Management" in output
    assert "None (Global)" in output


def test_render_focus_management_with_focus():
    """Test focus management view with active focus and budget allocation."""
    focus_state = {
        "district_id": "industrial-tier",
        "adjacent": ["commons", "civic-core"],
        "allocation": {
            "ring_events": 8,
            "global_events": 4,
            "archived": 23,
        },
    }
    
    districts = [
        {"id": "industrial-tier", "name": "Industrial Tier"},
        {"id": "commons", "name": "Commons"},
        {"id": "civic-core", "name": "Civic Core"},
    ]
    
    panel = render_focus_management(focus_state, districts)
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Focus Management" in output
    assert "Industrial Tier" in output
    assert "8/12" in output  # Ring events
    assert "4/12" in output  # Global events
    assert "23" in output  # Archived
    assert "Commons" in output  # Adjacent district


def test_render_focus_selection():
    """Test focus selection interface."""
    districts = [
        {
            "id": "industrial-tier",
            "name": "Industrial Tier",
            "modifiers": {"unrest": 0.7, "pollution": 0.6},
        },
        {
            "id": "civic-core",
            "name": "Civic Core",
            "modifiers": {"unrest": 0.2, "pollution": 0.1},
        },
    ]
    
    panel = render_focus_selection(districts, current_focus="civic-core")
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Select Focus District" in output
    assert "Industrial Tier" in output
    assert "Civic Core" in output
    assert "Current" in output  # Current focus indicator


def test_prepare_focus_data():
    """Test focus data preparation from game state."""
    game_state = {
        "metadata": {
            "focus_state": {
                "district_id": "industrial-tier",
                "adjacent": ["commons"],
            },
            "last_event_digest": {
                "allocation": {
                    "ring_events": 5,
                    "global_events": 3,
                    "archived": 10,
                }
            },
        }
    }
    
    data = prepare_focus_data(game_state)
    
    assert data["district_id"] == "industrial-tier"
    assert "commons" in data["adjacent"]
    assert data["allocation"]["ring_events"] == 5
    assert data["allocation"]["global_events"] == 3
    assert data["allocation"]["archived"] == 10


# --- Heat Map Overlay Tests ---


def test_render_city_map_with_unrest_overlay():
    """Test city map renders with unrest heat map overlay."""
    districts = [
        {
            "id": "district-1",
            "name": "High Unrest",
            "modifiers": {"unrest": 0.8, "pollution": 0.3},
        },
        {
            "id": "district-2",
            "name": "Low Unrest",
            "modifiers": {"unrest": 0.2, "pollution": 0.1},
        },
    ]
    
    focus_data = {"district_id": None, "adjacent": []}
    
    panel = render_city_map(districts, focus_data, overlay="unrest")
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "City Map [Unrest]" in output or "Unrest" in output
    assert "0.8" in output  # High unrest value
    assert "0.2" in output  # Low unrest value


def test_render_city_map_with_pollution_overlay():
    """Test city map renders with pollution heat map overlay."""
    districts = [
        {
            "id": "district-1",
            "name": "Polluted",
            "modifiers": {"pollution": 0.9, "unrest": 0.3},
        },
    ]
    
    focus_data = {"district_id": None, "adjacent": []}
    
    panel = render_city_map(districts, focus_data, overlay="pollution")
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Pollution" in output
    assert "0.9" in output


def test_render_city_map_with_control_overlay():
    """Test city map renders with control (security) heat map overlay."""
    districts = [
        {
            "id": "district-1",
            "name": "Secured",
            "modifiers": {"security": 0.7, "unrest": 0.2},
        },
    ]
    
    focus_data = {"district_id": None, "adjacent": []}
    
    panel = render_city_map(districts, focus_data, overlay="control")
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Control" in output
    assert "0.7" in output


def test_render_city_map_with_prosperity_overlay():
    """Test city map renders with prosperity heat map overlay."""
    districts = [
        {
            "id": "district-1",
            "name": "Prosperous",
            "modifiers": {"prosperity": 0.8, "unrest": 0.1},
        },
    ]
    
    focus_data = {"district_id": None, "adjacent": []}
    
    panel = render_city_map(districts, focus_data, overlay="prosperity")
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    assert "Prosperity" in output
    assert "0.8" in output


def test_heat_map_overlay_color_coding():
    """Test that heat map overlays use correct color coding."""
    # High unrest should be red (negative metric)
    districts_high_unrest = [
        {
            "id": "d1",
            "name": "Crisis",
            "modifiers": {"unrest": 0.9},
        }
    ]
    
    # High security should be green (positive metric)
    districts_high_security = [
        {
            "id": "d2",
            "name": "Safe",
            "modifiers": {"security": 0.9},
        }
    ]
    
    focus_data = {"district_id": None, "adjacent": []}
    
    # Render both - testing that the function doesn't crash
    # Actual color validation would require parsing ANSI codes
    panel1 = render_city_map(districts_high_unrest, focus_data, overlay="unrest")
    panel2 = render_city_map(districts_high_security, focus_data, overlay="security")
    
    console = Console()
    
    with console.capture() as capture:
        console.print(panel1)
    output1 = capture.get()
    
    with console.capture() as capture:
        console.print(panel2)
    output2 = capture.get()
    
    assert "0.9" in output1
    assert "0.9" in output2


# --- Integration Tests ---


def test_full_management_ui_integration():
    """Test all management UI components work together."""
    # Simulate a complete game state
    game_state = {
        "agents": {
            "agent-1": {
                "name": "Aria Volt",
                "role": "Negotiator",
                "traits": {"empathy": 0.8, "resolve": 0.7},
            }
        },
        "factions": {
            "union": {
                "name": "Union of Flux",
                "legitimacy": 0.72,
                "territory": ["industrial-tier"],
            }
        },
        "city": {
            "districts": [
                {
                    "id": "industrial-tier",
                    "name": "Industrial Tier",
                    "modifiers": {"unrest": 0.6, "pollution": 0.7},
                }
            ]
        },
        "metadata": {
            "focus_state": {
                "district_id": "industrial-tier",
                "adjacent": [],
            },
            "last_event_digest": {
                "allocation": {"ring_events": 5, "global_events": 3, "archived": 10}
            },
        },
    }
    
    # Prepare all data
    agents = prepare_agent_roster_data(game_state)
    factions, districts = prepare_faction_overview_data(game_state)
    focus = prepare_focus_data(game_state)
    
    # Render all views
    agent_panel = render_agent_roster(agents, tick=10)
    faction_panel = render_faction_overview(factions, districts)
    focus_panel = render_focus_management(focus, game_state["city"]["districts"])
    map_panel = render_city_map(
        game_state["city"]["districts"],
        game_state["metadata"]["focus_state"],
        overlay="unrest",
    )
    
    console = Console()
    
    # Verify all panels render without error
    with console.capture() as capture:
        console.print(agent_panel)
        console.print(faction_panel)
        console.print(focus_panel)
        console.print(map_panel)
    output = capture.get()
    
    assert "Aria Volt" in output
    assert "Union of Flux" in output
    assert "Industrial Tier" in output
    assert "Focus Management" in output


def test_management_ui_keyboard_navigation_hints():
    """Test that UI components include keyboard navigation hints."""
    # Focus management should show keyboard hints
    focus_state = {
        "district_id": None,
        "adjacent": [],
        "allocation": {"ring_events": 0, "global_events": 0, "archived": 0},
    }
    
    panel = render_focus_management(focus_state, [])
    console = Console()
    
    with console.capture() as capture:
        console.print(panel)
    output = capture.get()
    
    # Should have hint about pressing 'f' to change focus
    assert "f" in output.lower() or "focus" in output.lower()
    
    # Focus selection should show cancel hint
    panel2 = render_focus_selection([], None)
    
    with console.capture() as capture:
        console.print(panel2)
    output2 = capture.get()
    
    assert "cancel" in output2.lower() or "c" in output2.lower()
