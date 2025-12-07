# Agent Roster Panel & Management UI

**Last Updated:** 2025-12-07

## Overview
The Agent Roster Panel is a new interactive component in the Echoes of Emergence Terminal UI. It displays a live roster of agents, their stats, and supports keyboard navigation for selection and detail viewing. This feature enables rapid monitoring and management of agent states during simulation runs.

## Accessing the Agent Roster Panel
To launch the Terminal UI with the Agent Roster Panel:

```bash
./start.sh --ui
```

Once the UI is running, the Agent Roster Panel appears in the management dashboard. It updates in real time as the simulation progresses.

## Features
- **Keyboard Navigation:**
  - `↑` / `↓`: Move selection up/down the agent list
  - `Enter`: Open detailed view for the selected agent
  - `Escape`: Close detail view or exit panel
- **Live Updates:**
  - The panel refreshes automatically to reflect the latest simulation state
  - Selection is clamped to available agents
- **Agent Stats Displayed:**
  - Missions
  - Reliability (%)
  - Expertise (●●●●○)
  - Stress levels
  - Selection highlighting
- **Detail View:**
  - Shows mission statistics and deeper agent data

## Example Usage
```python
from gengine.echoes.cli.components import AgentRosterPanel, AgentRosterState

# Create panel with initial state
state = AgentRosterState(show_detail=False, selected_index=0)
panel = AgentRosterPanel(game_state, state)

# Keyboard navigation
panel.on_key("down")   # Move selection down
panel.on_key("enter")  # Toggle detail view

# Real-time updates
panel.update(game_state)  # Refresh with latest simulation data
```

## Testing & Coverage
- 6 new tests cover keyboard selection, real-time updates, rendering, boundary conditions, and detail view
- See `tests/echoes/test_management_ui.py` for examples

## See Also
- [How to Play Echoes](how_to_play_echoes.md)
- [Testing Guide](testing_guide.md)

---
