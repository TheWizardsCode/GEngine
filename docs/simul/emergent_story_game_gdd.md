# Echoes of Emergence – Game Design Document

## Automated Testing & Balancing Plan

### Simulation Results Summary (2025-12-07)

### Design Update: Disruptive Story Seeds & Resource Scarcity

#### Purpose
Introduce disruptive story seeds (e.g., city-wide crises, faction betrayals, resource shortages) and resource scarcity to increase tension, risk, and outcome diversity. These events force players to adapt tactics, manage resources, and recover from setbacks, making each playthrough more engaging and unpredictable.

#### Mechanics & Tuning Knobs

- New disruptive story seed added: "Supply Chain Collapse" (citywide logistics breakdown, resource shortage, faction conflict).
- Resource scarcity increased in default world: energy and materials starting values reduced, slower regeneration.
- Supply Chain Collapse triggers when resources fall below 20% in key districts, forcing emergency rationing and trade decisions.

- Disruptive seeds trigger unpredictable events (e.g., sudden supply chain collapse, faction betrayal, environmental disaster).
- Resource scarcity is tuned via config knobs (frequency, severity, recovery options) in `content/config/`.
- Director pacing controls when and how often disruptions occur, ensuring tension without overwhelming the player.

#### Game Loop Impact
- Moment-to-moment: Players must react to crises, make tough choices, and prioritize limited resources.
- Mid-term: Faction/district management becomes riskier, requiring strategic planning and mitigation.
- Long-term: Campaign arcs feature more recovery opportunities, failure modes, and divergent outcomes.

#### Balance Guidance
- Target: Tension curves with clear risk/reward, readable feedback, and recovery options.
- Safe envelope: Disruptions should challenge but not punish; configs should allow tuning for different skill levels.
- Telemetry: Use batch sweeps to validate tension, outcome diversity, and avoid grind/snowball/dead-end states.

#### Enjoyment Risks & Follow-ups
- Risks: Excessive punishment, opaque outcomes, confusion.
- Mitigation: Start with mild disruptions, increase severity gradually, and run lightweight playtests to validate fun and readability.

---


- **Proposal:** Add disruptive story seeds (e.g., city-wide crises, faction betrayals, resource shortages) and introduce resource scarcity to scenario configs.
- **Intended impact:** Create more risk, recovery opportunities, and divergent outcomes across strategies, increasing tension and replayability.
- **Balance guidance:** Tune disruptive events to occur unpredictably but not overwhelmingly; ensure recovery options exist so players can avoid dead-ends.
- **Next steps:** Prototype new seeds and scarcity configs, then run fresh batch sweeps to validate increased tension and outcome diversity.


- **Strategies tested:** balanced, aggressive, diplomatic (seed 42, normal difficulty, 100 ticks)
- **Outcomes:** All strategies activated the 'hollow-supply-chain' story seed and reached final stability 1.0 within 100 ticks.
- **Action profiles:**
  - Balanced: 10 INSPECT actions
  - Aggressive: 5 DEPLOY_RESOURCE, 5 INSPECT
  - Diplomatic: 7 INSPECT, 3 NEGOTIATE
- **Balance notes:** No grind, snowball, or dead-end states observed. All strategies converged to stable outcomes, suggesting current tuning is fair but may lack tension spikes or risk of failure.
- **Next steps:** Increase scenario variety and introduce more disruptive story seeds to test edge cases and tension curves.


1. **Automated Playtest Scenarios**
   - Scripted agents simulate player actions across all three rings (moment-to-moment, mid-term, long-term).
   - Batch simulations with varied configs from `content/config/` capture win/loss rates, resource curves, and narrative pacing.
   - Key metrics (decision density, tension spikes, recovery frequency) are logged to `build/telemetry/` for analysis.

2. **Balance Sweeps and Tuning**
   - Parameter sweeps systematically vary difficulty, resource availability, and director pacing knobs.
   - Telemetry identifies grind, snowball, and dead-end states; configs producing unfun or unreadable outcomes are flagged.
   - Auto-generated balance reports summarize safe tuning envelopes and outlier scenarios.

3. **Continuous GDD Alignment**
   - After each test sweep, GDD statements are cross-checked against observed outcomes.
   - Balance notes and tuning guidance are updated to reflect actual system behavior, with prototype divergences highlighted.

---

## 1. High-Level Concept

**Working Title:** Echoes of Emergence

**Elevator Pitch:**

A story-driven simulation game where you act as a subtle catalyst

inside a living, systemic city-state.

The overarching narrative emerges from the interactions

of autonomous factions, characters, and the environment,

with authored story "seeds" that grow

differently every playthrough.

**Core Fantasy:**

You are a wanderer in a frontier city-state on the brink of transformation or

collapse,

nudging a complex society of NPCs, institutions, ecologies, and

technologies

toward different futures.

**Design Pillars:**

- **Emergent Narrative:** Stories arise primarily from systems

  rather than fixed linear sequences.
- **Persistent Simulation:** The world runs and changes whether

  the player acts or not.
- **Legible Complexity:** Deep systemic interactions that remain

  understandable through good UI and feedback.
- **Meaningful Agency:** Small player actions can cascade into

  large-scale societal outcomes.

---

## Progress Log (Updated 2025-11-30)

- ✅ **Phase 5 M5.3 – Pacing & lifecycle polish** shipped: the
NarrativeDirector
  now enforces deterministic lifecycle states (`primed → active → resolving
→
archived`), applies per-seed and global quiet timers, records
  `director_pacing` + lifecycle history snapshots, and exposes the new
  telemetry in CLI/service/headless surfaces so designers can audit pacing
  without replaying logs.
- ✅ **Phase 5 M5.4 – Post-mortems** shipped: deterministic recaps now flow
  through the CLI `postmortem` command, service `/state?detail=post-mortem`,
  and the headless telemetry `post_mortem` block. Reviewer workflows cite the
  canonical 200-tick artifact (`build/feature-m5-4-post-mortem.json`) and the
  `jq '.post_mortem'` diff snippet so designers can compare epilogues without
  re-running the sim.
- ✅ **Phase 7 M7.2 – Explanations** shipped: queryable timelines and causal
  summaries are now available via the `ExplanationsManager`. New CLI commands
  (`timeline`, `explain`, `why`) surface event causality, agent reasoning
  summaries (e.g., "Joined protest because rent ↑, trust in Council ↓"), and
  metric explanations (e.g., "stability dropped due to high unrest, pollution").
  The system tracks causal chains between events each tick and persists them
  to game state metadata for querying.
- ✅ **Phase 7 M7.4 – Campaign UX** shipped: campaign management module at
  `gengine.echoes.campaign` provides persistent campaigns with autosave
  functionality. CLI commands (`campaign new/list/resume/end/status`) and
  the `--campaign <id>` flag enable campaign-based workflows. Autosaves
  trigger at configurable intervals (default 50 ticks), post-mortems are
  generated on campaign end, and campaign metadata persists across sessions.

## 2. Setting & Tone

**World:**
A mid-futuristic city-state built on a terraformed frontier world.

The city is surrounded by unstable wild zones filled with experimental ecologies

and derelict tech.

Inside the city, limited resources, competing ideologies, and

experimental AI governance

drive tension.

For an extended narrative introduction to the world of Neo Echo (geography, climate, factions, and social texture), see the lore document: [Neo Echo World Overview](../../docs/narrative/Neo_Echo.md).

**District Types:**

- **Civic Core:** Government, council chambers, AI governance centers.
- **Corporate Spires:** High-tech industry, R&D labs, financial institutions.
- **Commons & Tenements:** Dense housing, markets, cultural hubs.
- **Industrial Belt:** Power plants, processing facilities, logistics.
- **Perimeter Wilds:** Semi-controlled wilderness, terraforming sites, ruins.

**Tone:**
Reflective, grounded science fiction.

Emphasis on cause-and-effect, unintended consequences, and moral ambiguity

rather than clear-cut heroism.

**Temporal Structure:**

- Continuous simulated time divided into discrete ticks (e.g., minutes/hours).
- The city evolves: demographics, power structures, infrastructure,

and environment

change based on systemic interactions and player influence.

---

## 3. Core Gameplay Loop

1. **Observe**

- Explore districts through a text-based, conversational interface.

- Use natural-language prompts in the CLI (powered by an LLM) to talk to NPCs,

read news feeds, inspect dashboards and ASCII maps.

- Detect tensions: resource shortages, unrest,

ecological instability, political struggles.

1. **Decide & Intervene**

- Take narrative actions: side with characters, negotiate deals,

leak information, sabotage plans.

- Make systemic tweaks: advocate policies, influence resource routing,

back certain infrastructure projects.

- Target specific actors: befriend, recruit, blackmail,

or empower key agents.

1. **Simulate & Evolve**

- The underlying simulation advances:

- NPCs pursue goals, run schedules, and react to new information.

- Factions adjust strategies based on updated power balances.

- Economy, environment, and public sentiment shift.

1. **Reflect & Reinterpret**

- World feeds back:

- News stories, rumors, council bulletins, personal messages.

- Visual changes in districts, faction presence, and environmental state.

- New opportunities, conflicts, and narrative seeds unlock.

1. **Repeat**

- Each loop drives the city toward different macro-outcomes:

  stable technocracy, communal governance,

  soft authoritarianism, collapse, or mass exodus.

---

## 4. Systems Design (Emergence Focus)

### 4.1 Agent / NPC System

**Agent Model:**

- Each important NPC is an autonomous agent with:

- **Traits:** risk tolerance, empathy, ideology, greed, loyalty.

- **Needs:** survival, safety, belonging, status, autonomy.

- **Goals:** short-term tasks (e.g., attend meeting, secure supplies)

and long-term objectives (e.g., become district representative).

- **Memory:** records of key events, relationships, and player interactions.

**Decision-Making:**

- Utility-based AI or GOAP (Goal-Oriented Action Planning).
- Inputs:

- Personal state (needs, health, wealth, relationships).

- City blackboard: global facts such as resource prices, crime level,

pollution, policies.

- Social graph: relationships, trust, fear, obligations.

- Early-phase implementations guarantee at least one highly legible
  reconnaissance or negotiation action per tick so playtesters always see
  strategic agent beats in the log, even before deeper goal stacks ship.

**Examples of Emergent Behaviors:**

- A low-level worker becomes a whistleblower when stress, values alignment,

and trust in the player all cross a threshold.

- A former ally, repeatedly betrayed by the player, slowly drifts toward a rival

  faction and later leads efforts against the player.

- Small groups coalesce into a movement after repeated injustices
in the same district,

leading to spontaneous protests.

#### 4.1.1 Per-Agent Progression & Traits (Layered on Global Progression)

The **ProgressionSystem** tracks two complementary layers:

- **Global Player Progression** (already implemented):

  a single `ProgressionState` on `GameState`

  that represents the player profile –
  skill domains (diplomacy, investigation, economics,
  tactical, influence),
  faction reputation, and access tier (novice/established/elite).
- **Per-Agent Progression** (design intent in this section):

  a lightweight state for each field agent

  that reflects what they have been asked to do,
  how often they succeed, and how strained they feel.

Design goal: give agents a sense of personal history and specialization
that gently shapes odds and recommendations,

without turning the game into a micro-managed RPG party.

**Agent Progression State (Conceptual Model):**

Each important, player-facing field agent has
an `AgentProgressionState` keyed by `agent_id`
and containing:

- **Specialization:** a primary role tag (e.g., negotiator, investigator,
operator,
influencer)
aligned with the global skill domains.
- **Expertise Pips:** a tiny bounded track (0–5) per relevant action family
(e.g., negotiation,
reconnaissance,
covert ops)
that grows when an agent repeatedly succeeds at that kind of assignment.
- **Reliability:** a scalar in a bounded range (0–1)
that trends up with clean successes
and down with botched or abandoned missions.
- **Stress / Burnout:** a scalar in a bounded range that rises with failure,
overuse, and high-risk tasks,
and slowly recovers when the agent is rested or assigned low-risk work.
- **History Counters:** simple `missions_completed` / `missions_failed` counts
to support summaries and post-mortems.

All values are intentionally low-resolution (small integers or coarse buckets)
so players can read them at a glance
from CLI/service/headless surfaces.

**Inputs & Updates:**

The `ProgressionSystem.tick(...)` already consumes `agent_actions` reports from
the AgentSystem and writes to the global `ProgressionState`.
Per-agent progression layers onto this flow without changing the public
contract:

- Each agent action carries an `agent_id`, an `intent` (e.g.,
`NEGOTIATE_FACTION`, `INSPECT_DISTRICT`, `SABOTAGE_RIVAL`),
and a simple success flag or outcome rating.
- On each tick, for every action with an `agent_id`:
  - Ensure an `AgentProgressionState` exists for that `agent_id` on `GameState`.
  - Map `intent` to a domain family (negotiation, investigation, tactical,
influence) using the same mapping table
as global skills.
  - **On success:**
    - Increment the corresponding expertise pip up to a small cap (e.g., 0–5).
    - Nudge reliability upward, with diminishing returns as it approaches the
cap.
    - Apply a small stress bump only for hazardous or overextended assignments.
  - **On failure or aborted missions:**
    - Increment the relevant failure counter and raise stress/burnout.
    - Slightly reduce reliability, bounded so one bad mission does not erase a
long good
streak.
  - Record a compact telemetry event (e.g., `agent_progression` with agent id,
domain, expertise delta, stress delta)
for debugging and post-mortems.

The global `ProgressionState` continues to grant skill experience and adjust
faction reputation as it does today;
per-agent updates are an additive layer.

**Mechanical Effects & Tuning Envelope:**

- **Expertise Bonus:** agents with higher expertise in a domain contribute a
modest positive modifier to success odds for actions they personally execute
(e.g., ±5–10% around the base rate shaped by global skills + reputation).
This bonus should never exceed the effect of the global skill/reputation
combination.
- **Reliability:** can bias outcome variance – highly reliable agents produce
fewer wild swings (fewer critical failures/critical successes),
while unreliable agents are swingier but not strictly worse at the mean.
- **Stress / Burnout:** pushes in the opposite direction of expertise if
ignored:
  - At low to moderate levels, stress adds flavor text and gentle nudges but no
hard
blocks.
  - At high levels, it introduces small penalties to the agent’s effective
modifier and increases the chance of partial success or noisy outputs
from agent-AI tooling.
  - Stress should have **clear recovery paths** (time off, low-risk tasks) to
avoid irreversible
death spirals.

Safe tuning guidelines for early iterations:

- Cap expertise bonuses to a narrow band (e.g., `+0.05` to `+0.1` to the final
modifier at max expertise).
- Cap stress penalties similarly (e.g., `-0.05` to `-0.1` at worst), and ensure
they never stack with other maluses to make actions impossible.
- Ensure that even a brand-new, unstressed agent with no expertise still has a
viable chance to succeed when global skills and reputation are neutral.
- Prefer linear or gently diminishing gains over exponential curves so there is
no “god agent” that trivializes the game.

**Player-Facing Surfaces:**

- **Agent Summary Views:** when the player inspects an agent, they see:
  - Role label (e.g., "Veteran Negotiator", "Rookie Operative").
  - A small set of pips or bars for their key domain expertise.
  - A one- or two-word stress state ("calm", "strained", "burned out").
  - A short textual note referencing recent missions (pulled from history
counters/telemetry).
- **Assignment Decisions:**
  - When choosing who to send on a mission, players are nudged to balance using
their best specialists versus resting overstressed agents.
  - The system should **never** require pixel-perfect optimization; it should
reward intuitive choices (“send the calm negotiator to the tense council
hearing”) while keeping failure and surprise in play.
- **Post-Mortems & Explanations:** recap views (CLI `postmortem`,
timeline/explanation queries) include short notes such as:
  - "Agent ILYA’s long run of successful negotiations made this deal more
likely to succeed."
  - "Agent SERA was burned out, slightly reducing the odds of a clean
infiltration."

This per-agent layer lives firmly in the **moment-to-moment** ring (which agent
you send) and the **mid-term management** ring (how you rotate and care for
your roster), while the existing global progression continues to drive the
**long-term campaign arc** (which districts/commands unlock, how factions treat
you overall).

### 4.2 Faction & Institution System

**Factions:**

- Example factions:
  - **City Council:** formal political leadership.
  - **CoreCom Conglomerate:** dominant corporate bloc.
  - **Commons Assembly:** grassroots, community-driven organization.
  - **Network Underground:** information brokers, hackers, smugglers.
  - **Terraforming Guild:** manages external ecologies and infrastructure.

**Faction State:**

- Resources: credits, influence, technology level, territory, key agents.
- Ideology: axes like centralization vs. decentralization, AI autonomy vs.
human oversight, growth vs. sustainability.
- Stress/legitimacy: how secure and accepted their rule or presence is.

**Faction AI:**

- On each strategic tick, factions choose actions:
  - Lobby council, sponsor media campaigns.
  - Recruit or coerce agents.
  - Sabotage rivals (covert operations).
  - Invest in infrastructure or research.
- The current prototype implements lightweight versions of these behaviors:
  factions track legitimacy/resources, react to territory unrest, and emit
  structured logs (lobby, recruit, invest, sabotage) that mutate district
  modifiers and rival legitimacy so designers can trace macro shifts. Each tick
  also records per-faction legitimacy snapshots and deltas so CLI/service/
  telemetry outputs can spotlight the top movers even before narrative systems
  explain why a faction succeeded or failed.

**Emergent Faction Behaviors:**

- Temporary alliances when a single faction gets too dominant.
- Internal coups when leadership repeatedly fails or contradicts core ideology.
- Splinter groups forming new factions with more extreme positions, generating
fresh narrative threads.

### 4.3 Economy & Resource Simulation

**Key Resources:**

- Energy, food, clean water, housing capacity, security, data bandwidth, and
social capital.

**Model:**

- Each district has production, consumption, and storage values.
- The in-flight prototype now rebalances stocks every tick, tracks shortages
  that persist for multiple ticks, and feeds those counters into a lightweight
  market price layer recorded in `GameState.metadata`.
- Scarcity/abundance (plus the derived prices) feed into NPC and faction
  behavior (crime, migration, political pressure) while giving designers clear
  telemetry to tune against.
- A shared `economy` block in `content/config/simulation.yml` defines
  regeneration scale, demand weights, shortage thresholds, and price clamps
  (base/floor/ceiling). Designers can retune the knobs between playtests with no
  code changes, making it easy to explore harsh scarcity runs versus generous
  surplus scenarios.

**Emergent Economic Behaviors:**

- Black markets forming in response to strict regulation or shortages.
- Cycles of district decline and gentrification based on policies and shocks.
- Resource hoarding by elites, triggering unrest and factional conflict.

### 4.4 Environment & Ecology

**Zones & Variables:**

- Urban: pollution, heat, noise, population density.
- Industrial: emissions, waste leakage, power load.
- Perimeter: biodiversity, invasive species, terraforming stability.

**Simulation:**

- Simple local rules (growth/decay, diffusion) driving complex global patterns.
- Human activity (construction, extraction, neglect) alters environmental
variables.
- Resource scarcity now pipes through the EnvironmentSystem: the economy's
  shortage counters produce a configurable pressure signal that nudges district
  unrest/pollution and, in turn, global stability. Designers can modulate the
  coupling weights via the shared config to explore how harshly shortages
  should ripple into civic unrest or ecological decline. Pollution also diffuses
  toward a citywide mean each tick, while faction investments/sabotage inject
  relief or spikes that are logged in telemetry so narrative beats remain tied
  to systemic causes. A biodiversity gauge now complements pollution: scarcity
  drains biodiversity based on tunable weights, recovery pulls it toward a
  configurable baseline, and stability receives a feedback push/pull whenever
  biodiversity drifts past the midpoint. Falling below the alert threshold
  triggers warnings in CLI/service/headless surfaces so playtesters can respond
  before stability collapses. District modifiers now include a subtle
  mean-reversion step so long burns do not pin districts at the extremes, and
  faction AI prioritizes investment whenever unrest/security drift beyond safe
  margins while only allowing sabotage when a weaker faction has both the
  legitimacy gap and global stability to justify escalation. Latest tuning
  biases diffusion toward geographically adjacent neighbors via
  `diffusion_neighbor_bias`, clamps the per-tick drift with
  `diffusion_min_delta`/`diffusion_max_delta`, and records every tick's
  `environment_impact` payload with scarcity pressure, biodiversity values and
  deltas, stability feedback, faction deltas, average pollution, the districts
  holding the current min/max, and the top sampled diffusion deltas so
  telemetry, CLI summaries, and headless reports all expose the same
  diagnostics.

**Emergent Environmental Behaviors:**

- Invasive species outbreaks spreading from experimental sites into the city.
- Climate anomalies or infrastructure failures in response to overuse/neglect.
- Factions exploiting crises (e.g., climate emergencies) to justify power grabs.

### 4.5 Spatial Model & Adjacency Graph

- Districts gain explicit `coordinates` tuples (`x`, `y`, optional `z`) plus an
  `adjacent` list authored or auto-derived from those points so systems can add
  literal proximity on top of the existing population-ranked rings. Focus
  distance continues to consider ring order; the new data supplies a spatial
  modifier rather than a replacement.
- Spatial metadata unlocks hybrid mechanics: focus budgeting blends population
  rank with nearest-neighbor weighting, travel time for agents references the
  coordinates, and resource diffusion plus territory contiguity checks finally
  honor true neighbors even when a lightly populated district sits between two
  dense hubs.
- The same adjacency graph and coordinates now drive the travel planner used
  by the early narrative director module. Every tick, the director computes
  hop counts, distances, and estimated travel times between the current focus
  center and the highest-scored districts so story seeds can factor in actual
  movement costs instead of abstract ring distance alone.
- The first trio of authored seeds ships in
`content/worlds/default/story_seeds.yml`,
  and each evaluation pulls from the travel planner output plus the narrator's
  ranked archive to determine where those seeds should anchor.
- The validation pipeline will derive adjacency whenever coordinates change so
  content authors manage one truth while future navigation meshes, patrols, and
  blockade logic reuse the same graph. Tools will also emit warnings when
  spatial proximity and population priority diverge sharply so designers can
  tune the hybrid weights intentionally.

---

## 5. Narrative Design

### 5.1 Narrative Structure

**Story Seeds:**

- Authored narrative modules triggered by specific conditions:
  - Examples: "Energy Crisis," "AI Governance Vote," "Plague Cluster," "Rogue
Terraformer," "Citizen Referendum."
- Each seed defines:
  - Preconditions/Triggers (e.g., energy shortfall, pollution threshold,
faction stress).
  - Key roles (which agents or factions it prefers to attach to).
  - Stakes and possible trajectories.
  - Resolution templates (success, failure, partial, ambiguous).

**Narrative Director / Weaving Layer:**

- Monitors global metrics: stability, inequality, tech risk, environmental
health, factional polarization, player reputation.
- Activates seeds that are thematically and systemically appropriate.
- Seeds attach to **existing** agents and factions to avoid feeling bolted on.
- Balances pacing: prevents overload and ensures moments of calm reflection.
- The first implementation step is live: a `NarrativeDirector` component reads
  each tick's `director_feed`, selects the top-ranked hotspots, and evaluates
  adjacency-aware travel routes (hops, distance, travel time, reachability).
  The resulting `director_analysis` metadata (plus an accompanying
  `story_seeds` block) powers CLI/service/headless views so authors can inspect
  mobility pressure, suppressed counts, recommended focus shifts, and the
  specific seeds that attached to those hotspots each tick. Seeds now stay in
  the block for the duration of their cooldown and expose
  `cooldown_remaining`/`last_trigger_tick` so telemetry still shows the most
  recent beats even if the triggering tick already advanced.
- Phase 5.2 layers on `director_events`: every time a seed triggers, the
  director records a structured event that lists the tick, involved agents and
  factions, stakes, travel hints, and the referenced resolution templates.
  These events persist in a rolling history surfaced via CLI summary, the
  `director` command, FastAPI `/state?detail=summary`, and headless telemetry,
  giving designers a deterministic breadcrumb trail showing which authored
  beats fired and why without scrubbing logs.
- Phase 5.3 pacing guardrails add a deterministic lifecycle machine and expose
  its telemetry everywhere. Seeds now progress through `primed → active →
resolving → archived` with per-seed cooldown windows, per-seed quiet timers,
  and a global quiet span that caps how many crises overlap. The CLI summary,
  service payloads, and headless JSON each publish a `director_pacing` block
  alongside `story_seed_lifecycle`, `story_seed_lifecycle_history`, and a
  `director_quiet_until` timer so reviewers instantly see whether a beat is
  blocked by the max-active limit, a quiet period, or a lingering cooldown. The
  same block lists how many seeds are resolving versus active plus any blocked
  reasons, making pacing regressions visible without spelunking logs, and the
  values are tunable via the `director` section of `simulation.yml`.
  - `director_pacing` highlights `active_count`, `resolving_count`,
    `quiet_remaining_ticks`, and a `blocked_reasons` array so designers can tell
    whether overlap caps, per-seed quiet timers, or a global cool-down caused a
    lull. The rolling `story_seed_lifecycle` table mirrors the CLI display with
    columns for lifecycle state, ticks remaining, cooldown remaining, and the
    last trigger tick, giving authors a deterministic audit trail for every
    seed without digging through logs.
- Authoring guidelines (Phase 5): every seed carries `id`, `summary`,
  `stakes`, configurable `triggers` (thresholded metrics or boolean flags), a
  `roles` block that lists candidate agents/factions, a `travel_hint` that lets
  the director bias toward reachable districts, and `resolution_templates`
  describing success/failure/partial paths. Optional `followups` allow chained
  beats once the pacing system (M5.3) lands. These fields are now enforced by
  the loader, which validates every referenced district, agent, faction, and
  followup id (alongside the existing Pydantic checks) so designer errors
  surface before runtime.
- Lifecycle expectations: seeds move through `primed → active → resolving
→
archived`. Cooldowns and quiet-period rules throttle how many can be active
  per focus window, while telemetry/CLI history log each transition so
  playtesters can trace overlapping crises. Post-mortems (M5.4) already pull
  from the archived list plus the recorded director events to build the
  deterministic recap surfaced via the CLI `postmortem` command,
  `/state?detail=post-mortem`, and the headless telemetry block.

**Endgame & Outcomes:**

- No single canonical ending.
- Final state is a composition of:
  - Governance model: centralized, distributed, corporate, communal,
authoritarian.
  - Environmental status: recovering, stable, degraded, catastrophic.
  - Faction power: dominance, balance, fragmented chaos.
  - Key NPC fates and relationships.
- Endings are presented as narrated vignettes and visual snapshots of the city,
referencing specific events from the playthrough.

### 5.2 Player Role in the Story

**Identity:**

- The player is an **Intermediary**: a licensed mediator and systems analyst
able to move through multiple strata of society.

**Capabilities:**

- Dialogue choices that leverage knowledge, empathy, leverage, or threats.
- Investigation tools: data scraping, surveillance (with limits), physical
scouting.
- Policy influence: testify at hearings, lobby key figures, leak documents.
- Direct action: covert operations, rescue missions, sabotage.

**Narrative Agency:**

- Choose which crises to prioritize or ignore.
- Shape perceptions (rumors, public statements, media manipulation).
- Decide whether to work within existing structures, subvert them, or burn them
down.

---

## 6. Player Experience & UX

**Perspective & Controls:**

- **City Map:** ASCII grid of districts, control zones, environmental heatmaps
expressed via characters/shading.
- **Relationships Graph:** text lists and simple ASCII node-edge diagrams.
- **Faction Influence Map:** textual summaries and bar-like ASCII charts.
- **Event Feed:** scrolling log of headlines, rumors, and system alerts.
  Players can retarget their focus ring at any time, which in turn changes
  which beats surface in the digest versus the archived history so the feed
  stays legible even when dozens of subsystems emit events per tick. The
  narrator now ranks archived beats by severity plus focus distance and keeps
  a rolling history so UX surfaces can spotlight what was suppressed.
- **Gateway Sessions:** Phase 6 introduces `gengine.echoes.gateway`, a
  FastAPI/WebSocket host that mirrors the CLI shell experience for remote
  testers. The bundled `echoes-gateway-shell` connects over `/ws`, streams
  rendered output, and relies on the gateway’s session logger to capture
  focus/digest/history snapshots for QA without requiring terminal access to
  the simulation host.

**Legibility & Feedback:**

- "Why did this happen?" tools:
  - Event timelines showing key causes and effects.
  - Inspectable agents with summarized reasoning (e.g., "Joined protest because
rent ↑, trust in Council ↓, trust in Underground ↑").
  - Policy tooltips explaining projected and actual impacts.
- Focus manager UI: expose the current focus district, its prioritized
  neighbors, the number of beats allocated to the ring vs. the global pool, and
  how many events were archived each tick so designers/testers understand what
  the narrator suppressed. Surface the ranked archive and history (latest
  ticks, top scored beats) so testers can drill into "why wasn't this shown?"
- Director feed bridge: record each tick's spatial weights, ranked archive, and
  suppression counts into a `director_feed` metadata block (plus a rolling
  history) so the narrative director can ingest deterministic inputs without
  re-scoring events.

**Session Structure:**

- One campaign spans several in-game weeks.
- Auto-save and timeline snapshots to review major turning points.

**Meta-Progression:**

- Unlock new starting configurations, factions, and story seeds by completing
campaigns.
- Optional modifiers (e.g., hard mode, ecology focus, minimal governance) for
advanced players.

---

## 7. Progression & Motivation

**Short-Term Goals:**

- Help a specific NPC with an immediate problem.
- Secure housing or resources for a neighborhood.
- Gain access to restricted infrastructure or data.

**Mid-Term Goals:**

- Stabilize a district or reduce unrest.
- Shift a key vote or policy outcome.
- Change factional balance in a sector.

**Long-Term Goals:**

- Guide the city toward a target sociopolitical equilibrium (e.g., egalitarian
commons, efficient technocracy, pluralistic balance).
- Ensure survival of particular values or communities across crises.

**Progression Systems:**

- **Skills:** negotiation, investigation, systems hacking, logistics, stealth.
- **Access:** higher security clearance, new districts, deeper network layers.
- **Reputation:** recognised as trustworthy, radical, technocrat, populist,
manipulator, etc.

---

## 8. Failure, Risk, and Replayability

**Failure States:**

- Personal: arrest, exile, injury, or death.
- Systemic: city collapse, ecological disaster, hard authoritarian lock-in.

**Design Principle:**

- Failure should reveal how the system works rather than simply punish.
- Post-mortem screen visualizes key causal chains leading to failure (e.g.,
policies passed, crises mishandled, alliances broken).

**Replayability Drivers:**

- Different starting conditions and alliances.
- Randomized agent traits, relationships, and hidden agendas.
- Story seeds that may or may not trigger in a given run.
- Multiple viable long-term equilibria.

---

## 9. Technical & Implementation Notes (High-Level)

**Architecture:**

- Discrete-time simulation with modular subsystems:
  - Agent AI
  - Faction AI
  - Economy
  - Environment
  - Narrative Director
- Presentation tier now includes the **gateway service**:
`gengine.echoes.gateway`
  fronts the simulation service with a WebSocket endpoint, provisions
  `EchoesShell` instances per session, proxies commands via `SimServiceClient`,
  and streams ASCII output plus exit flags back to clients. It runs alongside
  the existing FastAPI simulation service and shares the same safeguards and
  config roots via `ECHOES_GATEWAY_SERVICE_URL`.

**Data-Driven Content:**

- Agents, factions, districts, events, and story seeds defined in external data
files (e.g. YAML) for ease of iteration by design.

**Performance Strategy:**

- Level of Detail (LOD) for simulation:
  - Detailed simulation in the players current and adjacent districts.
  - Coarser approximations in distant or inactive regions.
- Important agents get deeper reasoning passes; background populations are
approximated statistically.
- Safeguards and profiling: `content/config/simulation.yml` configures the LOD
  mode (detailed/balanced/coarse), engine/service tick caps, CLI run/script
  limits, and the profiling window. A dedicated TickCoordinator now sequences
  agents → factions → economy → environment, captures per-subsystem
timings,
  highlights the slowest subsystem, and tags anomalies (subsystem errors or
  event-budget clamps) in shared metadata so the CLI summary, FastAPI
  `/metrics`, and headless telemetry all surface the same block without extra
  tooling. A guardrail regression matrix (documented in the plan/README)
  ties each cap to a pytest so QA can prove safeguards still trigger after any
  tuning passes, while the new `content/config/sweeps/profiling-history/`
  variant (history window = 240 ticks) lets designers sweep long burns to study
  percentile drift without editing the baseline config.
- Headless regression driver: `scripts/run_headless_sim.py` executes long burns
  in capped batches, prints batch diagnostics, and emits JSON summaries (tick
  percentiles, slowest subsystem snapshots, anomaly totals/examples, faction
  legitimacy, economy tables, environment snapshots, and the narrator digest
  (`visible`, `suppressed`, focus budget allocation) so designers can compare
  macro metrics between builds or automated sweeps.
- Telemetry visualization: `scripts/plot_environment_trajectories.py` reads the
  `director_history` timelines embedded in sweep telemetry artifacts and plots
  pollution/unrest overlays across multiple configs (for example cushioned vs.
  high-pressure vs. profiling-history). Designers should bump
  `focus.history_length` to at least the intended tick budget before capturing
  telemetry so the plot spans the full run, then use the resulting PNG to
  review how diffusion clamps or scarcity weights reshape curves before
  iterating on config knobs.

**LLM Integration:**

- The CLI is backed by a large language model that interprets free-form player
text into structured in-game intents (movement, inspection, dialogue, policy
actions, covert operations).
- All LLM-generated text (NPC dialogue, headlines, summaries) is grounded in
and constrained by the current simulation state to avoid contradictions.
- The game exposes a clearly defined "action API" that the LLM can call; the
simulation remains the single source of truth for world changes.
- LLM context is scoped to relevant slices of state (for example, current
district, involved agents and factions, active story seeds) to balance
coherence, performance, and cost.

**Save/Load:**

- Entire simulation state is serializable to support long campaigns and
experiment-focused players.

**AI Player for Testing and Validation:**

- A programmatic AI player (distinct from in-game agent AI) exercises the game
  APIs to validate balance, discover edge cases, and test narrative coherence.
- Observer mode analyzes simulation state without intervention, generating
  structured commentary and trend detection for QA workflows.
- Actor mode (requires Phase 6 action system) applies rule-based or
  LLM-enhanced strategies to verify that player actions produce meaningful
  cascading effects.
- Tournament mode runs parallel games with varied strategies and configs,
  aggregating win rates, stability curves, and content coverage to guide balance
  iteration.
- The AI player uses only public APIs available to human players, ensuring test
  validity and preventing privileged shortcuts.
- Implementation lives under `src/gengine/ai_player/` to avoid confusion with
  in-game agent systems. See Phase 9 in the implementation plan for the staged
  rollout (observer → rule-based actor → LLM enhancement → tournaments).

---

## 10. Open Design Questions

- How transparent should agent decision-making be to preserve mystery while
maintaining fairness?
- What is the ideal ratio of authored story content to fully emergent
situations?
- Should there be a "main" narrative spine or purely emergent story arcs?
- How hard should it be for the player to drive the city toward an ideal
outcome vs. accepting messy compromises?
- How much simulation depth can we expose without overwhelming new players?

---

_This document is intended as a foundation. Future iterations should expand
into production-focused sections such as controls, camera, UI flow, content
pipelines, audio direction, art style, and technical stack once the core
simulation and narrative design are validated._
