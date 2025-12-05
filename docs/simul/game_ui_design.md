# Echoes of Emergence – Game UI Design
#
**Last Updated:** 2025-12-05

## 1. Introduction

This document defines the user interface design for Echoes of Emergence, a story-driven simulation game where players act as subtle catalysts in a living city-state. The UI must surface deep systemic complexity while remaining immediately legible and enjoyable to play.

**Design Philosophy:**
The UI should feel like operating a sophisticated but intuitive dashboard for a living world—not a spreadsheet. Every screen should answer "what's happening?" and "what can I do?" within seconds, while offering deeper inspection for players who want to understand the "why."

**Target Emotions:**
- Curiosity (what's brewing in the city?)
- Agency (my choices ripple outward)
- Clarity (I understand why this happened)
- Tension (something is at stake)

---

## 2. Three-Ring Loop Support

The UI must explicitly support the three-ring game loop described in the GDD. Each ring requires different information density, update frequency, and interaction patterns.

### 2.1 Moment-to-Moment Ring (Tactical Choices This Tick/Session)

**Player Questions:**
- What just happened?
- Who needs my attention right now?
- Which agent should I send on this task?
- What's the immediate risk?

**UI Requirements:**
- Event feed with severity-coded entries (critical/warning/info)
- Quick-glance agent status (availability, stress, specialization)
- Action shortcuts for common operations (inspect, negotiate, intervene)
- Clear feedback when actions resolve (success/partial/failure)
- Focus ring indicator showing current narrative spotlight

**Update Cadence:** Every tick, with visual emphasis on changes.

### 2.2 Mid-Term Management Ring (Districts, Factions, Resources)

**Player Questions:**
- Which districts are trending toward crisis?
- How are faction power balances shifting?
- Are shortages developing? Where?
- Should I reposition my focus?

**UI Requirements:**
- District overview with trend indicators (↑↓→)
- Faction legitimacy bars with recent delta highlights
- Resource/economy dashboard with shortage warnings
- Map with heat overlays (unrest, pollution, prosperity)
- Focus management controls

**Update Cadence:** Summarized after action batches or on-demand.

### 2.3 Long-Term Campaign Ring (Progression, Story Arcs, Outcomes)

**Player Questions:**
- Am I making progress toward my goals?
- What major story threads are active?
- How has the city transformed since I started?
- What ending am I steering toward?

**UI Requirements:**
- Campaign progress tracker
- Active story seeds with lifecycle indicators
- Historical timeline with major events
- Skill/reputation/access progression display
- Post-mortem and recap screens

**Update Cadence:** On significant milestones or player request.

---

## 3. Screen Layout & Information Architecture

### 3.1 Primary Play Screen

The main interface uses a persistent layout with contextual panels:

```
┌────────────────────────────────────────────────────────────────────┐
│  HEADER: City Name | Tick # | Global Stability Gauge | Alert Icons │
├──────────────────────────────┬─────────────────────────────────────┤
│                              │                                     │
│      MAIN VIEW AREA          │         CONTEXT PANEL               │
│                              │                                     │
│   (Map / District Detail /   │   (Selected Entity Info /           │
│    Agent Roster / Timeline)  │    Action Options / Explanations)   │
│                              │                                     │
├──────────────────────────────┴─────────────────────────────────────┤
│  EVENT FEED: Latest narrative beats, alerts, faction actions       │
├────────────────────────────────────────────────────────────────────┤
│  COMMAND BAR: Quick actions | Time controls | Menu access          │
└────────────────────────────────────────────────────────────────────┘
```

**Responsive Behavior:**
- Main View Area fills 60-70% of horizontal space
- Context Panel collapses to overlay on narrow screens
- Event Feed can expand/collapse for more detail
- Command Bar remains persistent and accessible

**Console Implementation Note:**
This layout is designed for Rich/ANSI rendering in terminal mode. All panels use box-drawing characters, ASCII progress bars (`████░░`), and ANSI color codes. The `--rich` flag on `echoes-shell` already provides styled tables and color-coded output. The same information architecture ports to a future graphical UI, but the primary implementation target is the console.

### 3.2 View Modes

The Main View Area cycles through several modes via tabs or hotkeys:

| View | Purpose | Key Information |
|------|---------|-----------------|
| **City Map** | Spatial overview of all districts | Heat overlays, faction territories, focus ring |
| **District Detail** | Deep dive on selected district | Population, modifiers, resources, local events |
| **Agent Roster** | Manage field agents | Status, specialization, stress, availability |
| **Faction Overview** | Track power dynamics | Legitimacy, resources, recent actions, relationships |
| **Timeline** | Historical causality | Event chain, why things happened, key turning points |
| **Campaign** | Long-term progress | Story seeds, progression, campaign goals |

---

## 4. Core UI Components

### 4.1 Global Status Bar (Header)

Always visible. Provides at-a-glance city health.

```
┌────────────────────────────────────────────────────────────────────┐
│ 🏙 FRONTIER CITY  │  Tick 247  │  ████████░░ 78%  │  ⚠ 2  │  🔔 5  │
│                   │            │   Stability      │ Alerts │ Events│
└────────────────────────────────────────────────────────────────────┘
```

**Elements:**
- **City Name:** Grounds the player in the scenario
- **Tick Counter:** Current simulation time
- **Stability Gauge:** Primary health metric with color coding (green/yellow/red)
- **Alert Count:** Critical issues requiring attention (clickable to expand)
- **Event Count:** Unread narrative beats since last check

**Behavior:**
- Stability gauge pulses when dropping rapidly
- Alert badge flashes for critical thresholds
- Clicking any element navigates to relevant detail view

### 4.2 City Map View

The spatial hub for mid-term management.

```
┌──────────────────────────────────────┐
│          CITY MAP                    │
│                                      │
│     [Civic]────[Spires]              │
│        │    ╲    │                   │
│        │     ╲   │                   │
│   [Commons]───[Industrial]           │
│        │         │                   │
│     [Wilds]──────┘                   │
│                                      │
│  Legend: ● Focus  ◐ Adjacent  ○ Other│
│  Overlay: [Unrest▼] [Pollution] [Econ]│
└──────────────────────────────────────┘
```

**Features:**



- Green: Healthy (0.0–0.3)



The narrative heartbeat. Shows what's happening in the city.



└────────────────────────────────────────────────────────────────────┘

- Suppressed count links to full archive for deep analysis
- Events within focus ring receive visual emphasis (bold or highlight)

**Scrolling Behavior:**
- New events appear at top
- Auto-scroll pauses when user is reading older entries
- "Jump to latest" button appears when scrolled back

### 4.4 Context Panel

Dynamic detail view for selected entities.

**District Context:**
```
┌─────────────────────────────────┐
│ INDUSTRIAL TIER          [Pin] │
├─────────────────────────────────┤
│ Population: 45,000              │
│                                 │
│ Modifiers:                      │
│   Unrest:     ████░░░░ 0.52 ↑   │
│   Pollution:  █████░░░ 0.68 →   │
│   Prosperity: ███░░░░░ 0.35 ↓   │
│   Security:   ████░░░░ 0.48 →   │
│                                 │
│ Resources:                      │
│   Energy:  120/200 (shortage!)  │
│   Food:    180/200              │
│   Water:   95/150               │
│                                 │
│ Active Seeds: Power Struggle    │
│ Faction Presence: Union (dom.)  │
├─────────────────────────────────┤
│ [Set Focus] [View History]      │
└─────────────────────────────────┘
```

**Agent Context:**
```
┌─────────────────────────────────┐
│ ARIA VOLT                [Pin] │
│ Veteran Negotiator              │
├─────────────────────────────────┤
│ Status: Available               │
│ Stress: ██░░░░░░ Calm           │
│                                 │
│ Expertise:                      │
│   Negotiation: ●●●●○            │
│   Investigation: ●●○○○          │
│   Tactical: ●○○○○               │
│                                 │
│ Recent Actions:                 │
│   T246: Negotiated with Union   │
│   T241: Inspected Civic Core    │
│                                 │
│ Reliability: High (0.85)        │
│ Missions: 12 complete, 1 failed │
├─────────────────────────────────┤
│ [Assign Task] [Rest Agent]      │
└─────────────────────────────────┘
```

**Faction Context:**
```
┌─────────────────────────────────┐
│ UNION OF FLUX            [Pin] │
│ Grassroots Labor Movement       │
├─────────────────────────────────┤
│ Legitimacy: ██████░░ 0.72 ↑     │
│ Resources:  ████░░░░ 0.48       │
│                                 │
│ Territory:                      │
│   Industrial Tier (dominant)    │
│   Commons (contested)           │
│                                 │
│ Recent Actions:                 │
│   T246: Lobbied council         │
│   T240: Invested in Industrial  │
│                                 │
│ Relations:                      │
│   Council: Neutral              │
│   Cartel: Hostile               │
├─────────────────────────────────┤
│ [View Members] [Reputation]     │
└─────────────────────────────────┘
```

### 4.5 Command Bar

Persistent action interface at screen bottom.

```
┌────────────────────────────────────────────────────────────────────┐
│ ▶ Next │ ▶▶ Run 5 │ 🎯 Focus │ 💾 Save │ ❓ Why │ ☰ Menu          │
└────────────────────────────────────────────────────────────────────┘
```

**Primary Actions:**
- **Next (▶):** Advance exactly 1 tick with full feedback
- **Run N (▶▶):** Batch advance with aggregate report (configurable N)
- **Focus (🎯):** Quick-change focus district (dropdown or map click)
- **Save (💾):** Persist current state
- **Why (❓):** Context-sensitive explanation query
- **Menu (☰):** Campaign management, settings, help

**Keyboard Shortcuts:**
- `Space` or `N`: Next tick
- `R`: Run batch
- `F`: Focus mode
- `S`: Quick save
- `?`: Why/explain
- `M`: Map view
- `A`: Agents view
- `T`: Timeline view

---

## 5. Interaction Patterns

### 5.1 Focus Management

The focus system controls narrative budget allocation. UI must make this tangible.

**Setting Focus:**
1. Click district on map → Context Panel shows "Set Focus" button
2. Or use Command Bar focus dropdown
3. Or keyboard shortcut F + district number

**Visual Feedback:**
- Focused district glows/pulses subtly
- Adjacent districts in focus ring show lighter highlight
- Event feed emphasizes focus-ring events
- Header shows current focus district name

**Budget Indicator:**
```
Focus Budget: Industrial Tier
  Ring events: 8/12 (67%)
  Global events: 4/12 (33%)
  Archived: 23 events
```

### 5.2 Time Control & Pacing

Players need control over simulation speed without losing track of events.

**Single Tick (Next):**
- Full event detail
- Animation/transitions for changes
- Automatic scroll to new events
- Pause for player review

**Batch Run:**
- Progress indicator during execution
- Aggregate summary on completion
- Highlight significant events that occurred
- "Review Details" option to step through tick-by-tick

**Batch Summary Panel:**
```
┌─────────────────────────────────────────┐
│ RAN 5 TICKS (T247 → T252)               │
├─────────────────────────────────────────┤
│ Stability: 0.78 → 0.71 (↓ 0.07)         │
│ Critical Events: 2                      │
│   • Energy crisis deepened (Industrial) │
│   • Story seed "Power Struggle" active  │
│ Faction Shifts:                         │
│   Union +0.05, Council -0.03            │
│ Market: Energy spiked to 1.42           │
├─────────────────────────────────────────┤
│ [Review Tick-by-Tick] [Continue]        │
└─────────────────────────────────────────┘
```

### 5.3 Explanation & Causality ("Why?")

The "Why" system is critical for legible complexity.

**Context-Sensitive Queries:**
- Click "Why" with nothing selected → "Why did stability change?"
- Click "Why" with district selected → "Why is Industrial Tier in crisis?"
- Click "Why" with agent selected → "Why did Aria's negotiation fail?"
- Click "Why" on event feed item → Causal chain for that specific event

**Explanation Display:**
```
┌─────────────────────────────────────────────────────────────────┐
│ WHY: Stability dropped from 0.78 to 0.71                        │
├─────────────────────────────────────────────────────────────────┤
│ Primary Causes:                                                 │
│   1. Unrest rose in Industrial Tier (+0.08)                     │
│      ← Energy shortage persisted 3+ ticks                       │
│      ← Production fell below consumption                        │
│                                                                 │
│   2. Pollution diffused from Industrial to Commons              │
│      ← Cartel sabotage in Industrial (T244)                     │
│                                                                 │
│ Contributing Factors:                                           │
│   • Biodiversity below midpoint (recovery stalled)              │
│   • No faction investment actions this window                   │
│                                                                 │
│ Suggested Actions:                                              │
│   → Send agent to stabilize Industrial unrest                   │
│   → Encourage faction investment in affected districts          │
├─────────────────────────────────────────────────────────────────┤
│ [View Full Timeline] [Close]                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Agent Assignment

Selecting and sending agents should feel quick and informed.

**Assignment Flow:**
1. Select task type (Inspect, Negotiate, Stabilize, Covert Op)
2. Select target (district, faction, agent)
3. System shows recommended agents with suitability scores
4. Player confirms assignment
5. Immediate feedback on dispatch, outcome next tick(s)

**Agent Recommendation Panel:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ASSIGN: Negotiate with Union of Flux                            │
├─────────────────────────────────────────────────────────────────┤
│ Recommended Agents:                                             │
│                                                                 │
│ ★ Aria Volt          Negotiation ●●●●○  Calm      → 78% est.   │
│   Cassian Mire       Negotiation ●●○○○  Strained  → 52% est.   │
│   Ilya Chen          Negotiation ●○○○○  Calm      → 45% est.   │
│                                                                 │
│ Note: Aria's expertise and reliability boost success odds.      │
│ Cassian is strained; consider resting before high-stakes tasks. │
├─────────────────────────────────────────────────────────────────┤
│ [Confirm: Aria] [Back]                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Campaign & Progression Screens

### 6.1 Campaign Hub

Accessed via Menu or dedicated tab for long-term planning.

```
┌─────────────────────────────────────────────────────────────────────┐
│ CAMPAIGN: "Industrial Renaissance"                                  │
│ World: Frontier City  │  Started: T0  │  Current: T247              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ACTIVE STORY SEEDS                                                  │
│ ┌─────────────────┬───────────┬────────────┬───────────────────┐    │
│ │ Seed            │ State     │ Location   │ Time Remaining    │    │
│ ├─────────────────┼───────────┼────────────┼───────────────────┤    │
│ │ Power Struggle  │ 🟢 Active │ Civic Core │ 8 ticks resolving │    │
│ │ Plague Cluster  │ 🟡 Primed │ Commons    │ Cooldown: 15      │    │
│ │ Rogue Terraformer│ ⚪ Archived│ Wilds     │ --                │    │
│ └─────────────────┴───────────┴────────────┴───────────────────┘    │
│                                                                     │
│ PLAYER PROGRESSION                                                  │
│   Access Tier: Established                                          │
│   Skills: Diplomacy ●●●○○  Investigation ●●○○○  Economics ●○○○○    │
│   Reputation: Union (Friendly), Council (Neutral), Cartel (Wary)    │
│                                                                     │
│ CAMPAIGN MILESTONES                                                 │
│   ✓ First crisis resolved (T45)                                     │
│   ✓ Faction alliance formed (T120)                                  │
│   ○ Achieve district stability across 3+ zones                      │
│   ○ Resolve "Power Struggle" seed                                   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ [View Timeline] [Post-Mortem Preview] [End Campaign]                │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Timeline View

Causal history for understanding "how did we get here?"

```
┌─────────────────────────────────────────────────────────────────────┐
│ TIMELINE                                         [Filter ▼] [Zoom] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ T247 ──●── Energy crisis deepens (Industrial)                       │
│        │     └─ Caused by: T244 sabotage, T240 underinvestment      │
│        │                                                            │
│ T244 ──●── Cartel sabotages Industrial Tier                         │
│        │     └─ Triggered: Pollution spike, unrest rise             │
│        │                                                            │
│ T240 ──●── Union invests in Industrial (partial success)            │
│        │                                                            │
│ T235 ──●── Story Seed "Power Struggle" primed                       │
│        │     └─ Preconditions met: faction tension, resource stress │
│        │                                                            │
│ T220 ──○── Player set focus to Industrial Tier                      │
│                                                                     │
│ [← Earlier]                                         [Later →]       │
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Major events shown as nodes on timeline
- Causal links indicated with connecting lines
- Filter by: Story seeds, Faction actions, Player actions, Crises
- Zoom to adjust time granularity
- Click event to see full explanation

### 6.3 Post-Mortem Screen

End-of-campaign or "what happened" recap.

```
┌─────────────────────────────────────────────────────────────────────┐
│ POST-MORTEM: "Industrial Renaissance"                               │
│ Duration: 247 ticks  │  Outcome: Stabilizing Technocracy            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ CITY STATE                                                          │
│   Stability: 0.71 (Recovering)                                      │
│   Governance: Council-Corporate Alliance                            │
│   Environment: Moderate pollution, biodiversity stressed            │
│                                                                     │
│ MAJOR STORY ARCS                                                    │
│   ✓ "Power Struggle" - Resolved: Council retained control           │
│   ✓ "Plague Cluster" - Resolved: Contained with Union aid           │
│   ○ "Rogue Terraformer" - Never triggered                           │
│                                                                     │
│ FACTION OUTCOMES                                                    │
│   Council: Dominant (0.75)  ↑ from 0.60                             │
│   Union: Allied (0.68)  ↑ from 0.55                                 │
│   Cartel: Marginalized (0.32)  ↓ from 0.50                          │
│                                                                     │
│ KEY TURNING POINTS                                                  │
│   T120: Player brokered Union-Council alliance                      │
│   T180: Cartel overreached with sabotage, lost legitimacy           │
│   T220: Industrial crisis averted through coordinated investment    │
│                                                                     │
│ WHAT COULD HAVE BEEN                                                │
│   • Cartel dominance if sabotage had succeeded at T180              │
│   • Collapse scenario if energy crisis persisted past T260          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ [Export Report] [New Campaign] [Return to Menu]                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Visual Design Principles

### 7.1 Color Language

Consistent color coding across all UI elements:

| Color | Meaning | Usage |
|-------|---------|-------|
| **Green** | Healthy/Positive | Good metrics, successful actions, recovery |
| **Yellow** | Caution/Neutral | Moderate levels, ongoing processes |
| **Red** | Critical/Negative | Crises, failures, dangerous thresholds |
| **Blue** | Information/Player | Selections, player actions, focus |
| **Purple** | Story/Narrative | Story seeds, major events |
| **Orange** | Economy/Resources | Market prices, shortages, trade |
| **Gray** | Inactive/Archived | Unavailable options, past events |

### 7.2 Typography Hierarchy

- **Headers:** Bold, larger size for section titles
- **Labels:** Medium weight for field names and categories
- **Values:** Regular weight, potentially monospace for numbers
- **Body:** Regular weight for descriptions and explanations
- **Alerts:** Bold with color coding for urgency

### 7.3 Iconography

Consistent icons for quick recognition:

| Icon | Meaning |
|------|---------|
| 🏙️ | City/District |
| 👤 | Agent |
| 🏛️ | Faction |
| 📊 | Metrics/Stats |
| 📖 | Story/Narrative |
| ⚠️ | Warning/Alert |
| ⚡ | Economy/Energy |
| 🌿 | Environment/Biodiversity |
| 🎯 | Focus |
| ❓ | Explanation/Why |

### 7.4 Motion & Feedback

- **State Changes:** Subtle animations when values update (number ticker, bar fill)
- **Selections:** Immediate highlight feedback on click
- **Transitions:** Smooth panel slides when switching views
- **Alerts:** Pulse animation for critical notifications
- **Loading:** Progress indicators for batch operations

---

## 8. Accessibility Considerations

### 8.1 Color Independence

- All color-coded information has secondary indicators (icons, text labels, patterns)
- High contrast mode available for visual impairment
- Avoid conveying critical information through color alone

### 8.2 Keyboard Navigation

- Full keyboard navigation for all interactions
- Visible focus indicators
- Logical tab order through UI elements
- Shortcut keys for common actions (documented in help)

### 8.3 Screen Reader Support

- Semantic structure with proper headings
- Alt text for visual elements
- Live regions for dynamic updates (event feed)
- Descriptive button labels

### 8.4 Adjustable Pacing

- Configurable batch sizes for time advancement
- Pause functionality during batch runs
- Event feed scroll-lock for reading
- Optional confirmation dialogs for major actions

---

## 9. Progressive Disclosure

### 9.1 Onboarding Layers

**Layer 1 - First Session:**
- Highlight core loop: Observe → Decide → Simulate
- Focus on single district, limited actions
- Tooltips explain each UI element on first encounter
- Simplified event feed (critical events only)

**Layer 2 - Early Campaigns:**
- Introduce focus management
- Unlock agent assignment complexity
- Show faction dynamics
- Full event feed with filters

**Layer 3 - Experienced Play:**
- Full timeline and causality tools
- Advanced batch sweeps
- Custom focus strategies
- Post-mortem analysis depth

### 9.2 Tooltip Strategy

- **Hover tooltips:** Brief explanation of UI element purpose
- **Extended tooltips:** Deeper explanation on sustained hover
- **Contextual help:** "?" icon opens detailed help panel
- **Tutorial triggers:** First-time actions prompt optional walkthrough

---

## 10. Implementation Priorities

### Phase 1: Core Playability
1. Global status bar with stability gauge
2. Basic city map with district selection
3. Event feed with severity coding
4. Simple context panel (district info)
5. Command bar with Next/Run/Save

### Phase 2: Management Depth
1. Agent roster view with assignment flow
2. Faction overview panel
3. Focus management UI
4. Heat map overlays
5. Batch run summary panel

### Phase 3: Understanding & Reflection
1. Why/Explanation system
2. Timeline view with causality
3. Campaign hub
4. Post-mortem screen
5. Progressive disclosure system

### Phase 4: Polish & Accessibility
1. Animation and feedback polish
2. Keyboard navigation complete
3. Accessibility audit and fixes
4. Onboarding refinement
5. Help system integration

---

## 11. Success Metrics

The UI should be evaluated against these player experience goals:

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to First Action** | < 30 seconds | New player can advance time within 30s |
| **Crisis Detection** | < 5 seconds | Critical alerts noticed within 5s of appearing |
| **Causality Understanding** | 80%+ accuracy | Players can explain why stability changed |
| **Focus Comprehension** | 90%+ awareness | Players know which district is focused |
| **Agent Selection Confidence** | Informed choice | Players use agent info when assigning |
| **Session Satisfaction** | 4+/5 rating | Post-session player survey |

---

## 12. Open Questions

- Should the event feed auto-pause on critical events, or just highlight?
- How much automation is desirable for routine agent assignments?
- What's the right balance between map-centric and list-centric views?
- Should explanations be generated on-demand (LLM) or pre-computed?
- How to visualize faction relationships without overwhelming the map?

---

## See Also

- [Game Design Document](./emergent_story_game_gdd.md) – Core game systems and philosophy
- [How to Play Echoes](../gengine/how_to_play_echoes.md) – Current CLI interface documentation
- [Implementation Plan](./emergent_story_game_implementation_plan.md) – Technical roadmap
