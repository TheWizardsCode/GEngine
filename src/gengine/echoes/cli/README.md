# Terminal UI Components

This directory contains the Terminal UI implementation for Echoes of Emergence, providing a rich, visual terminal interface that transitions the game from CLI-only to a dashboard-style experience.

## Architecture

The Terminal UI is built on the Rich library and uses a component-based architecture:

```
cli/
├── layout.py          # Screen layout manager and UI state
├── components/        # Reusable UI components
│   ├── status_bar.py      # Global status bar with stability gauge
│   ├── city_map.py        # ASCII city map with district visualization
│   ├── event_feed.py      # Event feed with severity indicators
│   ├── context_panel.py   # Entity detail panel (districts/agents/factions)
│   └── command_bar.py     # Command bar with action buttons
└── views/            # View mode implementations
    └── map_view.py        # Map view data preparation and rendering
```

## Components

### Layout Manager (`layout.py`)

- **ScreenLayout**: Organizes the screen into regions (header, main, context, events, commands)
- **UIState**: Tracks UI state (current view, selections, filters, event buffer)
- Handles terminal size validation (minimum 80x24)
- Provides region update and rendering methods

### Status Bar (`components/status_bar.py`)

Global status bar displaying:
- City name
- Current tick number
- Stability gauge with color coding (green/yellow/red)
- Alert count (critical issues)
- Event count (unread events)

Color thresholds:
- Green: stability ≥ 0.7
- Yellow: stability 0.4-0.7
- Red: stability < 0.4

### City Map (`components/city_map.py`)

ASCII district map featuring:
- District nodes with boundaries
- Focus indicators (● focused, ◐ adjacent, ○ other)
- Color-coded overlays (unrest, pollution, prosperity)
- Selection highlighting
- Legend with focus ring indicators

### Event Feed (`components/event_feed.py`)

Chronological event feed with:
- Severity icons (🔴 critical, 🟡 warning, 🟢 info, 📖 story, ⚡ economy)
- Tick numbers and locations
- Automatic severity classification
- Focus district highlighting
- Suppressed event count

Event classification rules:
- **Critical**: crises, persistent shortages (3+ ticks)
- **Warning**: unrest, sabotage events
- **Story**: story seed activations
- **Economy**: market prices, shortages
- **Info**: agent actions, routine updates

### Context Panel (`components/context_panel.py`)

Entity detail panel supporting:

**Districts:**
- Population
- Modifier bars (unrest, pollution, prosperity, security) with trend arrows
- Resource levels with shortage warnings
- Active story seeds
- Faction presence

**Agents:**
- Status (Available/Assigned/Resting)
- Stress level
- Expertise ratings (pips: ●●●○○)
- Recent actions
- Mission statistics

**Factions:**
- Legitimacy bar
- Resource levels
- Territory control
- Relationships

### Command Bar (`components/command_bar.py`)

Persistent action interface with:
- Next (n): Advance one tick
- Run (r): Batch advance
- Focus (f): Change focus district
- Save (s): Save snapshot
- Why (?): Query explanations
- Menu (m): Access menu

## Usage

### Basic Example

```python
from rich.console import Console
from gengine.echoes.cli.layout import ScreenLayout, UIState
from gengine.echoes.cli.components import (
    render_status_bar,
    render_city_map,
    render_event_feed,
    render_context_panel,
    render_command_bar,
)

# Create console and layout
console = Console()
layout = ScreenLayout(console)

# Check terminal size
is_valid, msg = layout.check_terminal_size()
if not is_valid:
    console.print(f"[red]Error: {msg}[/red]")
    return

# Create UI state
ui_state = UIState(current_view="map")

# Render components (see demo script for data preparation)
status_bar = render_status_bar(state_data)
city_map = render_city_map(districts, focus_data)
event_feed = render_event_feed(events)
context = render_context_panel(entity_type, entity_data)
command_bar = render_command_bar()

# Update layout
layout.update_region("header", status_bar)
layout.update_region("main", city_map)
layout.update_region("context", context)
layout.update_region("events", event_feed)
layout.update_region("commands", command_bar)

# Render
console.clear()
layout.render()
```

### Demo Script

Run the demo to see the Terminal UI in action:

```bash
python scripts/demo_terminal_ui.py
```

## Data Formats

### State Data (Status Bar)

```python
{
    "city": "Frontier City",
    "tick": 247,
    "stability": 0.68,
    "alerts": [
        {"severity": "critical", "message": "Energy shortage"},
    ],
    "events_count": 12,
}
```

### Districts (City Map)

```python
{
    "id": "civic-core",
    "name": "Civic Core",
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
    },
    "active_seeds": ["Power Struggle"],
    "faction_presence": "Council (dominant)",
}
```

### Events (Event Feed)

```python
{
    "tick": 247,
    "location": "Industrial Tier",
    "description": "Energy shortage persists (3 ticks)",
    "severity": "critical",  # or auto-classified
}
```

### Focus Data (Map)

```python
{
    "district_id": "industrial-tier",
    "adjacent": ["commons", "wilds"],
}
```

## Testing

Comprehensive test suite in `tests/echoes/test_terminal_ui.py`:

- 30 tests covering all components
- Layout initialization and size validation
- Component rendering with various data states
- Event severity classification
- Focus indicators and selection highlighting
- Coverage: 95%+ for all components

Run tests:

```bash
pytest tests/echoes/test_terminal_ui.py -v
```

## Next Steps

Future enhancements (Phase UI-2 and beyond):

1. **Real-time Updates**: Live display support for batch tick execution
2. **Keyboard Navigation**: Arrow keys, tab order, focus indicators
3. **Additional Views**: Agent roster, faction overview, timeline
4. **Overlays**: Heat maps for different metrics
5. **Batch Summary Panel**: Aggregate reporting after run commands
6. **Integration with EchoesShell**: `--ui` flag for Terminal UI mode

See `docs/simul/game_ui_implementation_plan.md` for the full roadmap.

## Design References

- [Game UI Design](../../docs/simul/game_ui_design.md) - Visual design specification
- [Game UI Implementation Plan](../../docs/simul/game_ui_implementation_plan.md) - Technical roadmap
- [How to Play Echoes](../../docs/gengine/how_to_play_echoes.md) - Gameplay guide

## Dependencies

- Rich (already integrated): Terminal rendering, styling, layout
- Standard library: dataclasses, typing

No additional dependencies required.

## Phase 12.2.1: Management Depth UI (Issue #77)

New views for advanced management features:

### Agent Roster View (`views/agent_view.py`)

Displays all agents with key stats:
- Name, role, and specialization (Negotiator/Investigator/Operative)
- Expertise visualization with pips (●●●○○)
- Stress level with color coding (Calm/Steady/Strained/Stressed)
- Availability status (Available/Assigned/Resting)

**Functions:**
```python
render_agent_roster(agents_data, tick) -> Panel
render_agent_detail(agent_data, tick) -> Panel
prepare_agent_roster_data(game_state) -> list[dict]
```

### Faction Overview View (`views/faction_view.py`)

Displays all factions with power dynamics:
- Legitimacy bars with trend indicators (↑↓→)
- Territory claims with district names
- Resource levels
- Faction relations (coming soon)

**Functions:**
```python
render_faction_overview(factions_data, districts_data) -> Panel
render_faction_detail(faction_data, districts_data, all_factions) -> Panel
prepare_faction_overview_data(game_state) -> tuple[list[dict], dict]
```

### Focus Management View (`views/focus_view.py`)

Displays narrative budget allocation:
- Current focus district
- Budget breakdown (ring events vs global events)
- Focus ring district listing
- Archive count
- District selection interface

**Functions:**
```python
render_focus_management(focus_state, districts_data) -> Panel
render_focus_selection(districts_data, current_focus) -> Panel
prepare_focus_data(game_state) -> dict
```

### Heat Map Overlays (enhanced `components/city_map.py`)

Enhanced city map with metric overlays:
- **unrest**: Negative metric (high=red, low=green)
- **pollution**: Negative metric (high=red, low=green)
- **security**: Positive metric (high=green, low=red)
- **prosperity**: Positive metric (high=green, low=red)
- **control**: Alias for security

Color coding automatically adjusts based on metric type:
- Positive metrics: green=good, red=bad
- Negative metrics: green=good (low), red=bad (high)

**Usage:**
```python
render_city_map(districts, focus_data, overlay="unrest")
render_city_map(districts, focus_data, overlay="pollution")
render_city_map(districts, focus_data, overlay="security")
```

## Test Coverage

Comprehensive test suite in `tests/echoes/test_management_ui.py`:
- 19 tests covering all management UI components
- Agent roster: 4 tests
- Faction overview: 4 tests
- Focus management: 4 tests
- Heat map overlays: 5 tests
- Integration: 2 tests

Coverage metrics:
- agent_view.py: 87%
- faction_view.py: 97%
- focus_view.py: 97%
- city_map.py: 78% (enhanced from baseline)

## Future Enhancements

Planned for future phases:
- Agent assignment workflow (select agent, choose task, confirm)
- Faction relationship visualization
- Action history tracking for agents and factions
- Real-time stress tracking for agents
- District selection via keyboard navigation
