# Echoes of Emergence – Game UI Implementation Plan

This plan stages the implementation of the UI design specified in
`game_ui_design.md`. It builds incrementally on the existing `echoes-shell`
CLI and Rich rendering infrastructure, delivering playable value at each
milestone. The implementation targets console/terminal rendering first,
with architectural decisions that support future graphical UI ports.

## Progress Log

- ⏳ **Phase UI-1 (Core Playability):** Not started
- ⏳ **Phase UI-2 (Management Depth):** Not started
- ⏳ **Phase UI-3 (Understanding & Reflection):** Not started
- ⏳ **Phase UI-4 (Polish & Accessibility):** Not started

## Dependencies

This plan assumes the following simulation features are available:

| Dependency | Source | Status |
|------------|--------|--------|
| SimEngine abstraction | Phase 3, M3.1 | ✅ Complete |
| Rich CLI rendering (`--rich`) | Phase 6, M6.2 | ✅ Complete |
| Focus management | Phase 4, M4.6 | ✅ Complete |
| Agent AI + progression | Phase 4, M4.1 + Phase 7, M7.1 | ✅ Complete |
| Faction AI | Phase 4, M4.2 | ✅ Complete |
| Economy subsystem | Phase 4, M4.3 | ✅ Complete |
| Explanations manager | Phase 7, M7.2 | ✅ Complete |
| Campaign management | Phase 7, M7.4 | ✅ Complete |
| Story seeds + director | Phase 5 | ✅ Complete |

## Architecture Overview

### Module Structure

```
src/gengine/echoes/
├── cli/
│   ├── shell.py          # Existing shell, extended with UI commands
│   ├── display.py        # Existing Rich rendering (M6.2)
│   ├── layout.py         # NEW: Screen layout manager
│   ├── components/       # NEW: Reusable UI components
│   │   ├── __init__.py
│   │   ├── status_bar.py
│   │   ├── city_map.py
│   │   ├── event_feed.py
│   │   ├── context_panel.py
│   │   ├── command_bar.py
│   │   └── progress_bars.py
│   └── views/            # NEW: View mode implementations
│       ├── __init__.py
│       ├── map_view.py
│       ├── district_view.py
│       ├── agent_view.py
│       ├── faction_view.py
│       ├── timeline_view.py
│       └── campaign_view.py
```

### Rendering Strategy

- **Rich library** for styled console output (already integrated)
- **Live displays** for real-time updates during batch runs
- **Panel composition** using Rich's `Layout` and `Panel` classes
- **Color themes** via Rich's `Theme` for consistent styling
- **Responsive widths** that adapt to terminal size

### State Management

- UI state (current view, selection, filters) stored in `UIState` dataclass
- Game state accessed via existing `SimEngine` / `GameState` APIs
- Event feed maintains a bounded buffer of recent events
- View transitions preserve context where meaningful

---

## Phase UI-1: Core Playability

**Goal:** Establish the fundamental play screen with essential information
and controls. A player can observe the city state, advance time, and save
their game.

**Duration:** 3–5 days

### M-UI-1.1 Screen Layout Manager (0.5–1 day)

Create the foundational layout system that organizes the screen into regions.

**Implementation:**

1. Create `src/gengine/echoes/cli/layout.py`:
   ```python
   from rich.layout import Layout
   from rich.console import Console
   from dataclasses import dataclass
   
   @dataclass
   class UIState:
       current_view: str = "map"
       selected_entity: Optional[str] = None
       event_filter: str = "all"
       focus_district: Optional[str] = None
   
   class ScreenLayout:
       def __init__(self, console: Console):
           self.console = console
           self.layout = Layout()
           self._configure_regions()
       
       def _configure_regions(self):
           self.layout.split_column(
               Layout(name="header", size=3),
               Layout(name="body"),
               Layout(name="events", size=8),
               Layout(name="commands", size=3),
           )
           self.layout["body"].split_row(
               Layout(name="main", ratio=2),
               Layout(name="context", ratio=1),
           )
   ```

2. Add responsive width detection and minimum size warnings.

3. Wire layout into `EchoesShell` when `--rich` flag is active.

**Tests:**
- Layout creates expected regions
- Handles narrow terminals gracefully
- Components can be attached to regions

**Acceptance:** Running `echoes-shell --rich` shows the basic layout skeleton.

### M-UI-1.2 Global Status Bar (0.5 day)

Implement the header component showing city health at a glance.

**Implementation:**

1. Create `src/gengine/echoes/cli/components/status_bar.py`:
   - Display city name from `GameState.city.name`
   - Show tick counter from `GameState.tick`
   - Render stability gauge using `GameState.environment.stability`
   - Count critical alerts from recent events
   - Count unread events since last summary

2. Color coding:
   - Stability ≥ 0.7: green
   - Stability 0.4–0.7: yellow
   - Stability < 0.4: red

3. Update logic:
   - Refresh after each tick
   - Pulse animation (Rich's `Spinner` or style toggle) when stability drops

**Tests:**
- Status bar reflects current game state
- Color thresholds work correctly
- Alert count updates with events

**Acceptance:** Header shows live city metrics after `next` command.

### M-UI-1.3 Basic City Map (1–1.5 days)

Render the city as connected district nodes with visual state indicators.

**Implementation:**

1. Create `src/gengine/echoes/cli/components/city_map.py`:
   - Read districts from `GameState.city.districts`
   - Read adjacency from district `adjacent` lists
   - Render as node-edge ASCII diagram using box characters

2. District node format:
   ```
   ┌─────────┐
   │ CIVIC   │ ← Name
   │ ●  0.72 │ ← Focus indicator + dominant metric
   └─────────┘
   ```

3. Focus visualization:
   - Focused district: filled marker (●) + bright style
   - Adjacent districts: half marker (◐) + dim style
   - Other districts: outline marker (○) + normal style

4. Connection rendering:
   - Draw edges based on `adjacent` lists
   - Use `─│╲╱` characters for connections

**Tests:**
- Map renders all districts
- Adjacency edges are symmetric
- Focus ring is visually distinct

**Acceptance:** `map` command shows styled district graph with focus.

### M-UI-1.4 Event Feed Component (1 day)

Display the narrative heartbeat with severity-coded events.

**Implementation:**

1. Create `src/gengine/echoes/cli/components/event_feed.py`:
   - Maintain bounded buffer (configurable, default 50 events)
   - Events sourced from tick reports + narrator digest

2. Event formatting:
   ```
   🔴 T247 Industrial Tier: Energy shortage persists (3 ticks)
   ```
   - Severity icon: 🔴 critical, 🟡 warning, 🟢 info, 📖 story, ⚡ economy
   - Tick number prefix
   - Location + description

3. Severity classification:
   - Critical: shortage > 3 ticks, stability drop > 0.1, story seed active
   - Warning: shortage 1–3 ticks, unrest > 0.5, faction sabotage
   - Info: agent actions, investments, routine updates
   - Story: story seed lifecycle changes
   - Economy: price changes, market alerts

4. Display controls:
   - Show last N events (configurable)
   - Suppressed count with link to full archive
   - Focus-ring events receive bold styling

**Tests:**
- Events categorized correctly by severity
- Buffer respects size limit
- Focus-ring events highlighted

**Acceptance:** After `run 5`, event feed shows categorized recent events.

### M-UI-1.5 Simple Context Panel (0.5–1 day)

Show details for the selected or focused district.

**Implementation:**

1. Create `src/gengine/echoes/cli/components/context_panel.py`:
   - Display district name and population
   - Show modifier bars (unrest, pollution, prosperity, security)
   - List resource levels with shortage warnings
   - Show active story seeds in district
   - Show dominant faction presence

2. Modifier bar rendering:
   ```
   Unrest:     ████░░░░ 0.52 ↑
   ```
   - 8-character bar scaled to 0.0–1.0
   - Trend arrow from delta since last tick

3. Resource display:
   ```
   Energy:  120/200 (shortage!)
   ```
   - Current/capacity format
   - Warning text when below threshold

**Tests:**
- Panel updates when focus changes
- Trend arrows calculated correctly
- Shortage warnings trigger appropriately

**Acceptance:** Clicking/selecting a district populates the context panel.

### M-UI-1.6 Command Bar and Keyboard Shortcuts (0.5 day)

Implement the persistent action interface.

**Implementation:**

1. Extend `EchoesShell` with keyboard shortcut handling:
   - `n` or `Space`: `next` command
   - `r`: prompt for tick count, then `run N`
   - `f`: `focus` command
   - `s`: `save` with auto-generated filename
   - `?`: `why` command
   - `m`: switch to map view
   - `q`: quit

2. Visual command bar at bottom:
   ```
   ▶ Next │ ▶▶ Run │ 🎯 Focus │ 💾 Save │ ❓ Why │ ☰ Menu
   ```

3. Highlight active command during execution.

**Tests:**
- Shortcuts trigger correct commands
- Command bar updates during execution
- Help text explains shortcuts

**Acceptance:** Player can navigate using keyboard shortcuts.

### M-UI-1.7 Integration and Smoke Tests (0.5 day)

Wire all Phase UI-1 components together and validate.

**Implementation:**

1. Update `--rich` mode to use new layout + components.
2. Ensure backward compatibility with non-rich mode.
3. Add integration test that runs 10 ticks and validates:
   - Status bar shows correct tick count
   - Map renders all districts
   - Event feed contains expected event types
   - Context panel populated for focused district

**Tests:**
- Full UI renders without crashes
- Performance acceptable (< 100ms render time)
- Terminal resize handled gracefully

**Acceptance:** `echoes-shell --rich --script "run 10;map;exit"` produces
expected visual output.

---

## Phase UI-2: Management Depth

**Goal:** Enable mid-term management through agent assignment, faction
tracking, and enhanced focus controls.

**Duration:** 4–6 days

### M-UI-2.1 Agent Roster View (1–1.5 days)

Display and manage field agents.

**Implementation:**

1. Create `src/gengine/echoes/cli/views/agent_view.py`:
   - List all agents with status summary
   - Show specialization, expertise pips, stress state
   - Indicate availability (available/assigned/resting)

2. Agent row format:
   ```
   Aria Volt      Negotiator   ●●●●○  Calm       Available
   Cassian Mire   Investigator ●●○○○  Strained   Assigned: Industrial
   ```

3. Selection and detail:
   - Select agent to show full context panel
   - Recent action history
   - Mission statistics

4. Keyboard navigation:
   - Arrow keys to select agent
   - Enter to view details
   - `a` to assign task

**Tests:**
- Roster shows all agents
- Stress states map to correct words
- Selection updates context panel

**Acceptance:** `agents` command shows styled roster with status.

### M-UI-2.2 Agent Assignment Flow (1 day)

Implement the task assignment interaction.

**Implementation:**

1. Add `assign` command to shell:
   - Prompt for task type (inspect/negotiate/stabilize/covert)
   - Prompt for target (district or faction)
   - Show recommended agents with suitability scores

2. Suitability calculation:
   - Use `calculate_agent_modifier()` from M7.1.2
   - Factor in expertise, stress, reliability
   - Display estimated success percentage

3. Confirmation and feedback:
   - Player selects agent
   - Show dispatch confirmation
   - Action queued for next tick

**Tests:**
- Recommendations sorted by suitability
- Stressed agents show warning
- Assignment creates valid intent

**Acceptance:** Player can assign agent to task via guided flow.

### M-UI-2.3 Faction Overview Panel (1 day)

Track faction power dynamics.

**Implementation:**

1. Create `src/gengine/echoes/cli/views/faction_view.py`:
   - List all factions with legitimacy bars
   - Show resource levels
   - Display territory claims

2. Faction row format:
   ```
   Union of Flux    ██████░░ 0.72 ↑   Industrial (dom.), Commons (contested)
   ```

3. Faction detail panel:
   - Recent actions (last 5)
   - Relations with other factions
   - Key members (agents affiliated)

4. Relationship display:
   ```
   Relations:
     Council: Neutral
     Cartel:  Hostile (-0.3)
   ```

**Tests:**
- Legitimacy bars scaled correctly
- Territory claims match game state
- Relations reflect actual values

**Acceptance:** `factions` command shows power balance overview.

### M-UI-2.4 Enhanced Focus Management UI (0.5–1 day)

Make focus selection intuitive and visual.

**Implementation:**

1. Enhance `focus` command:
   - Show current focus with budget allocation
   - List districts with distance-from-focus scores
   - Quick-select via number or name prefix

2. Focus budget display:
   ```
   Focus: Industrial Tier
     Ring events:   8/12 (67%)
     Global events: 4/12 (33%)
     Archived:      23 events
   ```

3. Map integration:
   - `f` in map view enters focus-select mode
   - Arrow keys navigate districts
   - Enter confirms selection

**Tests:**
- Budget percentages calculated correctly
- Focus change updates all components
- Navigation intuitive

**Acceptance:** Player can change focus via map navigation.

### M-UI-2.5 Heat Map Overlays (0.5–1 day)

Add visual overlays to the city map.

**Implementation:**

1. Extend city map component with overlay modes:
   - Unrest: color districts by unrest level
   - Pollution: color by pollution level
   - Prosperity: color by prosperity
   - Security: color by security

2. Overlay toggle:
   - `o` key cycles through overlays
   - Legend shows current overlay and scale

3. Color mapping:
   - Green: 0.0–0.3
   - Yellow: 0.3–0.6
   - Red: 0.6–1.0

4. Trend indicators:
   - Arrow suffix on node labels (↑↓→)

**Tests:**
- Overlay colors match metric values
- Legend updates with overlay change
- Trends calculated from recent delta

**Acceptance:** Map shows colored overlay with `map --overlay unrest`.

### M-UI-2.6 Batch Run Summary Panel (0.5 day)

Provide meaningful feedback after time batches.

**Implementation:**

1. After `run N` completes, display summary panel:
   - Tick range (T247 → T252)
   - Stability delta
   - Critical events count with list
   - Faction legitimacy changes (top 3 movers)
   - Market price changes

2. Navigation options:
   - [Review Tick-by-Tick]: step through each tick
   - [Continue]: dismiss and resume play

3. Store tick-by-tick data for review mode.

**Tests:**
- Summary captures all critical events
- Deltas calculated correctly
- Review mode steps through correctly

**Acceptance:** Batch run shows informative summary before continuing.

---

## Phase UI-3: Understanding & Reflection

**Goal:** Enable deep understanding of causality and long-term campaign
tracking.

**Duration:** 4–6 days

### M-UI-3.1 Why/Explanation System (1–1.5 days)

Surface causal reasoning through the UI.

**Implementation:**

1. Enhance `why` command with context sensitivity:
   - No selection: explain last stability change
   - District selected: explain district's current state
   - Agent selected: explain agent's last action outcome
   - Event selected: explain that specific event

2. Explanation display format:
   ```
   WHY: Stability dropped from 0.78 to 0.71
   
   Primary Causes:
     1. Unrest rose in Industrial Tier (+0.08)
        ← Energy shortage persisted 3+ ticks
        ← Production fell below consumption
   
   Contributing Factors:
     • Biodiversity below midpoint
     • No faction investment this window
   
   Suggested Actions:
     → Send agent to stabilize Industrial unrest
   ```

3. Integration with ExplanationsManager (M7.2):
   - Call `explain_metric()`, `explain_faction()`, `explain_agent()`
   - Format causal chains with indentation

**Tests:**
- Context detection works for each entity type
- Causal chains formatted correctly
- Suggestions are actionable

**Acceptance:** `why` provides meaningful causal explanation.

### M-UI-3.2 Timeline View (1–1.5 days)

Display historical causality.

**Implementation:**

1. Create `src/gengine/echoes/cli/views/timeline_view.py`:
   - Show major events as nodes
   - Draw causal connections between events
   - Filter by event type

2. Timeline format:
   ```
   T247 ──●── Energy crisis deepens (Industrial)
          │     └─ Caused by: T244 sabotage, T240 underinvestment
          │
   T244 ──●── Cartel sabotages Industrial Tier
   ```

3. Navigation:
   - Scroll through time (earlier/later)
   - Zoom to adjust granularity (show more/fewer events)
   - Select event to see full explanation

4. Event types and icons:
   - Story seeds: 📖
   - Faction actions: 🏛️
   - Player actions: 👤
   - Crises: ⚠️

**Tests:**
- Timeline shows events in order
- Causal links match event metadata
- Filters reduce displayed events

**Acceptance:** `timeline` shows causal event history.

### M-UI-3.3 Campaign Hub (1 day)

Long-term campaign tracking screen.

**Implementation:**

1. Create `src/gengine/echoes/cli/views/campaign_view.py`:
   - Show campaign name, world, duration
   - List active story seeds with lifecycle states
   - Display player progression (skills, access, reputation)
   - Track campaign milestones

2. Story seed table:
   ```
   Seed             State      Location     Time Remaining
   Power Struggle   🟢 Active  Civic Core   8 ticks resolving
   Plague Cluster   🟡 Primed  Commons      Cooldown: 15
   ```

3. Progression display:
   ```
   Access Tier: Established
   Skills: Diplomacy ●●●○○  Investigation ●●○○○  Economics ●○○○○
   Reputation: Union (Friendly), Council (Neutral)
   ```

4. Milestone tracking:
   - Define milestone conditions in config
   - Check conditions each tick
   - Display completed vs. pending

**Tests:**
- Campaign data loads correctly
- Story seed states accurate
- Milestones update on achievement

**Acceptance:** `campaign status` shows full campaign overview.

### M-UI-3.4 Post-Mortem Screen (0.5–1 day)

End-of-campaign recap and analysis.

**Implementation:**

1. Enhance existing `postmortem` command with rich formatting:
   - City final state summary
   - Story arc resolutions
   - Faction outcome comparison (start vs. end)
   - Key turning points

2. "What Could Have Been" section:
   - Identify alternative paths based on near-miss conditions
   - Highlight player-influenced decision points

3. Export options:
   - Save as JSON for analysis
   - Save as formatted text for sharing

**Tests:**
- Post-mortem generates for ended campaigns
- Faction deltas calculated correctly
- Export produces valid files

**Acceptance:** `campaign end` shows rich post-mortem screen.

### M-UI-3.5 Progressive Disclosure System (1 day)

Guide new players without overwhelming them.

**Implementation:**

1. Add onboarding state tracking:
   - Track which UI elements have been seen
   - Track which actions have been taken
   - Persist across sessions

2. Layer 1 (First Session):
   - Highlight core loop commands only
   - Show tutorial tooltips on first encounter
   - Simplified event feed (critical only)

3. Layer 2 (Early Campaigns):
   - Unlock focus management after 10 ticks
   - Unlock agent assignment after first crisis
   - Full event feed with filter hint

4. Layer 3 (Experienced):
   - All features unlocked
   - No tutorial interruptions
   - Advanced options visible

5. Configuration:
   - `content/config/simulation.yml` onboarding section
   - Skip onboarding via `--expert` flag

**Tests:**
- Onboarding state persists
- Features unlock at correct thresholds
- Expert mode bypasses all restrictions

**Acceptance:** New player sees guided introduction.

---

## Phase UI-4: Polish & Accessibility

**Goal:** Refine the experience with animations, full keyboard navigation,
and accessibility compliance.

**Duration:** 3–5 days

### M-UI-4.1 Animation and Feedback Polish (1 day)

Add subtle motion to reinforce state changes.

**Implementation:**

1. Number transitions:
   - Tick counter animates when advancing
   - Metric changes show brief highlight

2. Progress indicators:
   - Batch runs show progress bar
   - Loading states for slow operations

3. Alert animations:
   - Critical alerts pulse briefly
   - New events fade in

4. Use Rich's `Live` display for smooth updates.

**Tests:**
- Animations complete within reasonable time
- Performance not degraded
- Can be disabled via config

**Acceptance:** UI feels responsive and alive.

### M-UI-4.2 Full Keyboard Navigation (1 day)

Ensure all interactions work without mouse.

**Implementation:**

1. Tab order through all components:
   - Header → Main View → Context → Events → Commands

2. View-specific navigation:
   - Map: arrow keys select districts
   - Agent roster: arrow keys select agents
   - Timeline: arrow keys scroll events

3. Focus indicators:
   - Visible highlight on focused element
   - Consistent styling across views

4. Shortcut documentation:
   - `?` shows keyboard shortcut reference
   - Shortcuts shown in command bar tooltips

**Tests:**
- All actions reachable via keyboard
- Tab order logical
- Focus visible at all times

**Acceptance:** Full session playable with keyboard only.

### M-UI-4.3 Accessibility Audit and Fixes (1 day)

Ensure UI is usable with assistive technologies.

**Implementation:**

1. Color independence:
   - All colored elements have text/icon alternatives
   - Test with simulated color blindness

2. High contrast mode:
   - Add `--high-contrast` flag
   - Adjust color palette for visibility

3. Screen reader considerations:
   - Ensure logical heading structure
   - Add descriptive labels to all interactive elements
   - Test with terminal screen readers

4. Adjustable pacing:
   - Configurable animation speeds
   - Option to disable all motion

**Tests:**
- Color blind simulation passes
- High contrast mode readable
- Screen reader test checklist

**Acceptance:** Accessibility checklist complete.

### M-UI-4.4 Onboarding Refinement (0.5 day)

Tune the new player experience based on feedback.

**Implementation:**

1. Review onboarding flow for friction points.
2. Adjust unlock thresholds based on playtesting.
3. Add skip/reset options for onboarding state.
4. Ensure tutorial content is accurate.

**Tests:**
- Onboarding completes in under 5 minutes
- No dead ends or confusion points
- Skip option works cleanly

**Acceptance:** New player successfully completes first session.

### M-UI-4.5 Help System Integration (0.5 day)

Comprehensive in-game help.

**Implementation:**

1. `help` command shows context-sensitive topics:
   - `help map` explains map view
   - `help agents` explains agent management
   - `help shortcuts` lists all keyboard shortcuts

2. Inline help icons:
   - `?` next to complex elements
   - Brief tooltip on hover/select

3. Link to external documentation:
   - `help docs` opens browser to gameplay guide

**Tests:**
- Help topics exist for all major features
- Inline help matches feature behavior
- Links work correctly

**Acceptance:** Player can find help for any feature.

---

## Success Criteria

Each phase has acceptance criteria. Overall UI implementation succeeds when:

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Time to First Action | < 30 seconds | Playtest timing |
| Crisis Detection | < 5 seconds | Event visibility test |
| Causality Understanding | 80%+ accuracy | Player survey |
| Focus Comprehension | 90%+ awareness | Player survey |
| Keyboard-Only Playability | 100% features | Manual test |
| Accessibility Compliance | WCAG 2.1 AA | Audit checklist |

---

## Testing Strategy

### Unit Tests

- Each component has isolated tests
- Rendering output validated against snapshots
- State management tested independently

### Integration Tests

- Full session scripts (`--script`) validate component interaction
- Regression captures (`build/ui-regression-*.json`) track behavior

### Playtest Protocols

- First-time player sessions (onboarding validation)
- Experienced player sessions (efficiency validation)
- Accessibility testing with screen readers

### CI Integration

- UI tests run on every PR
- Visual regression via snapshot comparison
- Performance benchmarks for render time

---

## Open Questions

Decisions to resolve during implementation:

1. **Event feed capacity:** How many events to buffer before rotation?
2. **Animation timing:** What duration feels responsive but visible?
3. **Onboarding thresholds:** When should features unlock?
4. **Screen reader support:** Which terminal readers to prioritize?
5. **Mobile terminals:** Support narrow widths (< 80 columns)?

---

## See Also

- [Game UI Design](./game_ui_design.md) – Design specification
- [Game Design Document](./emergent_story_game_gdd.md) – Core game systems
- [Implementation Plan](./emergent_story_game_implementation_plan.md) – Overall roadmap
- [How to Play Echoes](../gengine/how_to_play_echoes.md) – Current CLI reference
