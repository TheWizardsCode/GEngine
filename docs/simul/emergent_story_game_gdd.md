# Echoes of Emergence – Game Design Document

## 1. High-Level Concept

**Working Title:** Echoes of Emergence

**Elevator Pitch:**  
A story-driven simulation game where you act as a subtle catalyst inside a living, systemic city-state. The overarching narrative emerges from the interactions of autonomous factions, characters, and the environment, with authored story "seeds" that grow differently every playthrough.

**Core Fantasy:**  
You are a wanderer in a frontier city-state on the brink of transformation or collapse, nudging a complex society of NPCs, institutions, ecologies, and technologies toward different futures.

**Design Pillars:**

- **Emergent Narrative:** Stories arise primarily from systems rather than fixed linear sequences.
- **Persistent Simulation:** The world runs and changes whether the player acts or not.
- **Legible Complexity:** Deep systemic interactions that remain understandable through good UI and feedback.
- **Meaningful Agency:** Small player actions can cascade into large-scale societal outcomes.

---

## 2. Setting & Tone

**World:**  
A mid-futuristic city-state built on a terraformed frontier world. The city is surrounded by unstable wild zones filled with experimental ecologies and derelict tech. Inside the city, limited resources, competing ideologies, and experimental AI governance drive tension.

**District Types:**

- **Civic Core:** Government, council chambers, AI governance centers.
- **Corporate Spires:** High-tech industry, R&D labs, financial institutions.
- **Commons & Tenements:** Dense housing, markets, cultural hubs.
- **Industrial Belt:** Power plants, processing facilities, logistics.
- **Perimeter Wilds:** Semi-controlled wilderness, terraforming sites, ruins.

**Tone:**  
Reflective, grounded science fiction. Emphasis on cause-and-effect, unintended consequences, and moral ambiguity rather than clear-cut heroism.

**Temporal Structure:**

- Continuous simulated time divided into discrete ticks (e.g., minutes/hours).
- The city evolves: demographics, power structures, infrastructure, and environment change based on systemic interactions and player influence.

---

## 3. Core Gameplay Loop

1. **Observe**

- Explore districts through a text-based, conversational interface.
- Use natural-language prompts in the CLI (powered by an LLM) to talk to NPCs, read news feeds, inspect dashboards and ASCII maps.
- Detect tensions: resource shortages, unrest, ecological instability, political struggles.

2. **Decide & Intervene**

   - Take narrative actions: side with characters, negotiate deals, leak information, sabotage plans.
   - Make systemic tweaks: advocate policies, influence resource routing, back certain infrastructure projects.
   - Target specific actors: befriend, recruit, blackmail, or empower key agents.

3. **Simulate & Evolve**

   - The underlying simulation advances:
     - NPCs pursue goals, run schedules, and react to new information.
     - Factions adjust strategies based on updated power balances.
     - Economy, environment, and public sentiment shift.

4. **Reflect & Reinterpret**

   - World feeds back:
     - News stories, rumors, council bulletins, personal messages.
     - Visual changes in districts, faction presence, and environmental state.
   - New opportunities, conflicts, and narrative seeds unlock.

5. **Repeat**
   - Each loop drives the city toward different macro-outcomes: stable technocracy, communal governance, soft authoritarianism, collapse, or mass exodus.

---

## 4. Systems Design (Emergence Focus)

### 4.1 Agent / NPC System

**Agent Model:**

- Each important NPC is an autonomous agent with:
  - **Traits:** risk tolerance, empathy, ideology, greed, loyalty.
  - **Needs:** survival, safety, belonging, status, autonomy.
  - **Goals:** short-term tasks (e.g., attend meeting, secure supplies) and long-term objectives (e.g., become district representative).
  - **Memory:** records of key events, relationships, and player interactions.

**Decision-Making:**

- Utility-based AI or GOAP (Goal-Oriented Action Planning).
- Inputs:
  - Personal state (needs, health, wealth, relationships).
  - City blackboard: global facts such as resource prices, crime level, pollution, policies.
  - Social graph: relationships, trust, fear, obligations.

**Examples of Emergent Behaviors:**

- A low-level worker becomes a whistleblower when stress, values alignment, and trust in the player all cross a threshold.
- A former ally, repeatedly betrayed by the player, slowly drifts toward a rival faction and later leads efforts against the player.
- Small groups coalesce into a movement after repeated injustices in the same district, leading to spontaneous protests.

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
- Ideology: axes like centralization vs. decentralization, AI autonomy vs. human oversight, growth vs. sustainability.
- Stress/legitimacy: how secure and accepted their rule or presence is.

**Faction AI:**

- On each strategic tick, factions choose actions:
  - Lobby council, sponsor media campaigns.
  - Recruit or coerce agents.
  - Sabotage rivals (covert operations).
  - Invest in infrastructure or research.

**Emergent Faction Behaviors:**

- Temporary alliances when a single faction gets too dominant.
- Internal coups when leadership repeatedly fails or contradicts core ideology.
- Splinter groups forming new factions with more extreme positions, generating fresh narrative threads.

### 4.3 Economy & Resource Simulation

**Key Resources:**

- Energy, food, clean water, housing capacity, security, data bandwidth, and social capital.

**Model:**

- Each district has production, consumption, and storage values.
- Global market layer adjusts prices and incentives.
- Scarcity and abundance feed into NPC and faction behavior (crime, migration, political pressure).

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
- Human activity (construction, extraction, neglect) alters environmental variables.

**Emergent Environmental Behaviors:**

- Invasive species outbreaks spreading from experimental sites into the city.
- Climate anomalies or infrastructure failures in response to overuse/neglect.
- Factions exploiting crises (e.g., climate emergencies) to justify power grabs.

---

## 5. Narrative Design

### 5.1 Narrative Structure

**Story Seeds:**

- Authored narrative modules triggered by specific conditions:
  - Examples: "Energy Crisis," "AI Governance Vote," "Plague Cluster," "Rogue Terraformer," "Citizen Referendum."
- Each seed defines:
  - Preconditions/Triggers (e.g., energy shortfall, pollution threshold, faction stress).
  - Key roles (which agents or factions it prefers to attach to).
  - Stakes and possible trajectories.
  - Resolution templates (success, failure, partial, ambiguous).

**Narrative Director / Weaving Layer:**

- Monitors global metrics: stability, inequality, tech risk, environmental health, factional polarization, player reputation.
- Activates seeds that are thematically and systemically appropriate.
- Seeds attach to **existing** agents and factions to avoid feeling bolted on.
- Balances pacing: prevents overload and ensures moments of calm reflection.

**Endgame & Outcomes:**

- No single canonical ending.
- Final state is a composition of:
  - Governance model: centralized, distributed, corporate, communal, authoritarian.
  - Environmental status: recovering, stable, degraded, catastrophic.
  - Faction power: dominance, balance, fragmented chaos.
  - Key NPC fates and relationships.
- Endings are presented as narrated vignettes and visual snapshots of the city, referencing specific events from the playthrough.

### 5.2 Player Role in the Story

**Identity:**

- The player is an **Intermediary**: a licensed mediator and systems analyst able to move through multiple strata of society.

**Capabilities:**

- Dialogue choices that leverage knowledge, empathy, leverage, or threats.
- Investigation tools: data scraping, surveillance (with limits), physical scouting.
- Policy influence: testify at hearings, lobby key figures, leak documents.
- Direct action: covert operations, rescue missions, sabotage.

**Narrative Agency:**

- Choose which crises to prioritize or ignore.
- Shape perceptions (rumors, public statements, media manipulation).
- Decide whether to work within existing structures, subvert them, or burn them down.

---

## 6. Player Experience & UX

**Perspective & Controls:**

  - **City Map:** ASCII grid of districts, control zones, environmental heatmaps expressed via characters/shading.
  - **Relationships Graph:** text lists and simple ASCII node-edge diagrams.
  - **Faction Influence Map:** textual summaries and bar-like ASCII charts.
  - **Event Feed:** scrolling log of headlines, rumors, and system alerts.

**Legibility & Feedback:**

- "Why did this happen?" tools:
  - Event timelines showing key causes and effects.
  - Inspectable agents with summarized reasoning (e.g., "Joined protest because rent ↑, trust in Council ↓, trust in Underground ↑").
  - Policy tooltips explaining projected and actual impacts.

**Session Structure:**

- One campaign spans several in-game weeks.
- Auto-save and timeline snapshots to review major turning points.

**Meta-Progression:**

- Unlock new starting configurations, factions, and story seeds by completing campaigns.
- Optional modifiers (e.g., hard mode, ecology focus, minimal governance) for advanced players.

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

- Guide the city toward a target sociopolitical equilibrium (e.g., egalitarian commons, efficient technocracy, pluralistic balance).
- Ensure survival of particular values or communities across crises.

**Progression Systems:**

- **Skills:** negotiation, investigation, systems hacking, logistics, stealth.
- **Access:** higher security clearance, new districts, deeper network layers.
- **Reputation:** recognised as trustworthy, radical, technocrat, populist, manipulator, etc.

---

## 8. Failure, Risk, and Replayability

**Failure States:**

- Personal: arrest, exile, injury, or death.
- Systemic: city collapse, ecological disaster, hard authoritarian lock-in.

**Design Principle:**

- Failure should reveal how the system works rather than simply punish.
- Post-mortem screen visualizes key causal chains leading to failure (e.g., policies passed, crises mishandled, alliances broken).

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

**Data-Driven Content:**

- Agents, factions, districts, events, and story seeds defined in external data files (e.g. YAML) for ease of iteration by design.

**Performance Strategy:**

- Level of Detail (LOD) for simulation:
  - Detailed simulation in the players current and adjacent districts.
  - Coarser approximations in distant or inactive regions.
- Important agents get deeper reasoning passes; background populations are approximated statistically.
- Safeguards and profiling: `content/config/simulation.yml` configures the LOD
  mode (detailed/balanced/coarse), engine/service tick caps, CLI run/script
  limits, and tick-level logging so builds can hard-stop runaway loops while
  still emitting reproducible telemetry.
- Headless regression driver: `scripts/run_headless_sim.py` executes long burns
  in capped batches, prints batch diagnostics, and emits JSON summaries so
  designers can compare macro metrics between builds or automated sweeps.

**LLM Integration:**

- The CLI is backed by a large language model that interprets free-form player text into structured in-game intents (movement, inspection, dialogue, policy actions, covert operations).
- All LLM-generated text (NPC dialogue, headlines, summaries) is grounded in and constrained by the current simulation state to avoid contradictions.
- The game exposes a clearly defined "action API" that the LLM can call; the simulation remains the single source of truth for world changes.
- LLM context is scoped to relevant slices of state (for example, current district, involved agents and factions, active story seeds) to balance coherence, performance, and cost.

**Save/Load:**

- Entire simulation state is serializable to support long campaigns and experiment-focused players.

---

## 10. Open Design Questions

- How transparent should agent decision-making be to preserve mystery while maintaining fairness?
- What is the ideal ratio of authored story content to fully emergent situations?
- Should there be a "main" narrative spine or purely emergent story arcs?
- How hard should it be for the player to drive the city toward an ideal outcome vs. accepting messy compromises?
- How much simulation depth can we expose without overwhelming new players?

---

_This document is intended as a foundation. Future iterations should expand into production-focused sections such as controls, camera, UI flow, content pipelines, audio direction, art style, and technical stack once the core simulation and narrative design are validated._
