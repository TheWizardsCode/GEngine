# Plan: Implement "Echoes of Emergence" (CLI + LLM Sim)

A staged implementation that builds a solid simulation core, then layers on agents and factions, narrative, and finally the CLI + LLM conversational interface with ASCII visualization. The runtime architecture is microservice-based and designed to run on Kubernetes from the outset. This plan is informed by and should be read alongside the game design document in `docs/simul/emergent_story_game_gdd.md`. Each phase should be testable in isolation via minimal scripts before integrating, with data-driven content and full save/load from the start.

## Progress Log (Updated 2025-11-28)

- ✅ Phase 1 (Foundations & Data Model): core models, YAML loader, snapshots, smoke tests.
- ✅ Phase 2 (Early CLI Shell & Tick Loop): in-process `echoes-shell` CLI with summary/next/run/map/save/load commands plus a deterministic tick engine.
- ⚙️ Phase 3 (Simulation Core & Service API): **M3.1 SimEngine abstraction
  landed**, **M3.2 FastAPI service + typed client shipped**, **M3.3 CLI service
  mode running**, **M3.4 safeguards + LOD shipped**, and **M3.5 headless driver
  online**.
- ⚙️ Phase 4 (Agents/Factions/Economy): **M4.1 Agent AI** and **M4.2 Faction AI**
  shipped; **M4.3 Economy** now includes the subsystem, designer-facing config
  knobs, legitimacy/market telemetry, and expanded tests. **M4.4 Environment**
  now routes scarcity pressure into unrest/pollution, biases diffusion toward
  adjacent districts with configurable neighbor weights/min/max clamps, tracks
  biodiversity health (scarcity decay, configurable recovery baseline, stability
  coupling, alert threshold), and captures richer telemetry (average pollution,
  extremes, sampled diffusion deltas, biodiversity/stability snapshots) that
  surfaces in CLI/service/headless summaries. Remaining Phase 4 work focuses on
  long scenario sweeps plus director UX polish before merging back to main.
- ⏳ Phases 3–8: pending (simulation service, subsystems, narrative, LLM gateway, Kubernetes).

## Tech Stack and Runtime Assumptions

- Primary language: Python 3.12 managed via `uv`, using FastAPI for HTTP
  services, Typer/Rich for CLI tooling, and Pydantic for shared schemas.
- Storage: in-memory state during early phases, then persisted snapshots to
  SQLite (dev) and Postgres (prod) via SQLModel; static YAML lives under
  `content/` and is validated on load.
- Data formats: YAML for authored content, JSON for service APIs, MessagePack
  for compact save files once persistence is needed.
- Runtime profiles: single-process "all-in-one" mode for local iteration,
  docker-compose for multi-service dev, and Kubernetes (Helm chart) for shared
  staging/prod; all environments use the same env var contract.

## Simulation Service Internal Modules

- `core.state`: canonical city/district/agent/faction/resource models and
  serialization helpers.
- `systems.agents`, `systems.factions`, `systems.economy`, `systems.environment`:
  subsystem logic updated each tick with well-defined inputs/outputs.
- `narrative.director`: monitors metrics, activates story seeds, and writes
  events into the timeline log consumed by UI services.
- `actions.router`: validates structured intents, resolves conflicts, and
  forwards to subsystems.
- `persistence.snapshot`: handles save/load, versioning, and schema migration.
- `api.routes`: FastAPI layer exposing tick control, state queries, and action
  submission endpoints; depends only on Pydantic DTOs to keep boundaries clear.

## Simulation API Contract (Draft)

- `POST /tick` `{"ticks": 1}` -> `{ "ticks_advanced": 1, "duration_ms": 42 }`.
- `GET /state/snapshot?detail=city|district|agent` -> trimmed state payloads
  sized for CLI consumption.
- `GET /district/{district_id}` -> snapshot plus recent events for that area.
- `POST /actions` -> accepts intent array (see schema below) and returns action
  receipts with success, failure, or defer reasons.
- `GET /metrics` -> aggregate stats (stability, inequality, env, agent counts)
  plus tick timing metrics for observability.
- `POST /sessions` -> creates or resumes campaigns; returns session id used by
  CLI gateway and LLM service when scoping requests.
- Error format: `{ "error": { "code": "INVALID_INTENT", "detail": ... } }`
  with HTTP 4xx/5xx codes mapped to actionable client guidance.

## Data Schemas and Content Pipeline

- Authoring folder structure: `content/worlds/<name>/districts.yml`,
  `agents.yml`, `factions.yml`, `story_seeds.yml`, plus optional overrides per
  campaign variant.
- Validation: Pydantic models executed via `uv run scripts/validate_content.py`
  during CI and when content authors save files (pre-commit hook).
- Sample district schema:
  ```yaml
  id: industrial-tier
  name: Industrial Tier
  population: 120000
  resources:
    energy: { capacity: 80, current: 60 }
    materials: { capacity: 50, current: 30 }
  modifiers:
    pollution: 0.7
    unrest: 0.3
  factions:
    - union_of_flux
    - cartel_of_mist
  ```
- Story seed schema includes `id`, `triggers` (metrics + thresholds), `roles`
  (agent/faction selectors), `stakes`, `beats`, and `resolutions`, enabling the
  narrative director to ground prompts deterministically.
- Build pipeline: `uv run scripts/build_content.py --world default` emits a
  frozen JSON bundle hashed by `HASH` env var for deployment; CLI can reload by
  sending `POST /admin/reload-content` when running locally.

## Intent Schema and LLM Prompt Strategy

- Intents are JSON objects produced by the LLM service and validated by the
  simulation service before execution:
  ```json
  {
    "intent": "NEGOTIATE",
    "session_id": "abc123",
    "targets": ["union_of_flux"],
    "levers": { "resource_offer": "materials", "evidence_id": "evt-42" },
    "narrative_context": "Broker truce over refinery protest"
  }
  ```
- Core intent types: `INSPECT`, `NEGOTIATE`, `DEPLOY_RESOURCE`, `PASS_POLICY`,
  `COVERT_ACTION`, `INVOKE_AGENT`, `REQUEST_REPORT`; each documents required
  fields so the CLI gateway can surface correct affordances.
- Prompt scaffolding: CLI gateway packages the latest state slice, recent
  events, and allowed intents into a system prompt; LLM responses are parsed via
  function-calling schema to enforce structure and minimize hallucinations.
- Guardrails: add regex + JSON Schema validation plus fallback canned intents
  if parsing fails more than twice in a session; log failures to an audit topic
  for tuning prompts later.

## Testing, Observability, and MVP Milestones

- Testing: unit tests per subsystem (agents, economy, etc.), property tests for
  conservation rules, contract tests for `/tick` and `/actions`, golden-master
  tests for ASCII renderings, and scenario scripts (`scripts/run_scenario.py`)
  that simulate multi-day campaigns. After every full pytest run, capture the
  canonical telemetry artifact via
  `scripts/run_headless_sim.py --world default --ticks 200 --lod balanced --seed 42 --output build/m4-3-economy-telemetry.json`
  so regressions always include a comparable metrics snapshot (now including
  faction legitimacy snapshots/deltas and the last economy table).
- Observability: structured JSON logs with session/tick ids, Prometheus metrics
  for tick latency, agent counts, LLM latency, and intent failure rates, plus
  OpenTelemetry tracing that links CLI requests to LLM calls and simulation
  actions.
- Persistence: snapshot files written every N ticks with schema versions stored
  inside metadata; `uv run scripts/migrate_save.py` upgrades snapshots when
  models change.
- MVP vertical slice: 3 districts, 2 factions, 20 agents, 5 story seeds, ASCII
  city map with overlays, intents limited to inspect/negotiate/deploy_resource,
  and local single-process mode only; target completion by end of Phase 3.
- Content pipeline ergonomics: document hot-reload steps, add `content.watch`
  task that rebuilds bundles on save, and ensure designers can run `uv run
python src/tools/preview_seed.py --seed blackout-01` to preview story beats.

## Implementation Roadmap

### Phase 1 – Foundations and Data Model

- **M1.1 Repo skeleton** (0.5-1 day): establish Python 3.12 project under
  `src/echoes/`, configure `uv`, pytest, Ruff, and pre-commit hooks.
- **M1.2 Domain models** (1-2 days): implement serializable city/district/
  agent/faction/resource/environment models plus unit tests in
  `src/echoes/core/state.py`.
- **M1.3 Content loaders** (0.5-1 day): parse YAML world files from
  `content/worlds/` using Pydantic validators and surface schema errors early.
- **M1.4 GameState + save/load** (0.5-1 day): wrap state plus tick metadata in
  `core.state.GameState`, add snapshot serde (JSON for now, MessagePack later)
  and a helper script under `scripts/eoe_dump_state.py`.

### Phase 2 – Early CLI Shell and ASCII Debug UI

- **M2.1 Typer CLI scaffold** (0.5 day): commands for `new`, `load`, `next`,
  `run N`, and `summary`, executing sim entirely in-process.
- **M2.2 Tick driver + summaries** (0.5-1 day): extract `tick()` with hooks for
  future subsystems and print city/district/agent tables using Rich.
- **M2.3 ASCII rendering** (0.5 day): render grids and overlays via
  `src/echoes/cli/ascii_map.py`, with golden tests to lock visuals.

### Phase 3 – Simulation Core and Service API

- **M3.1 Engine abstraction** (complete): `SimEngine` now lives in
  `src/gengine/echoes/sim/engine.py`, centralizing `initialize_state`,
  `advance_ticks`, `apply_action`, and `query_view` for both in-process and
  service deployments.
- **M3.2 FastAPI service** (complete): `create_app()` under
  `src/gengine/echoes/service/app.py` exposes `/tick`, `/state`, `/metrics`, and
  `/actions`, with a synchronous `SimServiceClient` in
  `src/gengine/echoes/client/service.py` for downstream tooling.
- **M3.3 CLI service mode** (complete): the `echoes-shell` now accepts
  `--service-url` to steer through `SimServiceClient`, with unit tests covering
  both `LocalBackend` and `ServiceBackend` flows.
- **M3.4 LOD + safeguards** (complete): `content/config/simulation.yml`
  establishes reusable limits (engine cap, CLI run cap, script guard, service
  tick cap), exposes `ECHOES_CONFIG_ROOT`, and tunes LOD modes (detailed,
  balanced, coarse) that scale volatility plus an event budget per tick.
  `SimEngine` now enforces the guardrails, logs tick metrics, and the CLI/service
  surface friendly warnings when requests exceed the configured caps.
- **M3.5 Headless driver** (complete): `scripts/run_headless_sim.py` runs
  long-form burns by chunking work into `engine_max_ticks`, prints per-batch
  diagnostics, and writes JSON summaries (tick counts, timing, LOD mode,
  environment snapshot) for regression diffs or CI sweeps. Supports snapshot
  bootstrap, seed overrides, and alternate config roots.

#### M3.4 Safeguards & LOD – Refresh Prep

- Audit every guardrail surface (SimEngine caps, CLI `run` guard, service tick
  limits, headless script batches) against the latest config to confirm the
  values align with Phase 4 loads and note any deltas that need designer signoff.
- Extend profiling hooks so the CLI/service/headless summaries capture tick
  duration percentiles plus subsystem timing, enabling faster detection of
  runaway scenarios before LOD shifts.
- Draft a regression matrix that pairs each safeguard with a pytest or scenario
  test (for example, CLI caps, service HTTP 400 responses, long-run script
  throttling) so reopening the milestone has a clear verification checklist.
- Stage documentation updates (README, gameplay guide, Exec Docs) that explain
  how to tune the guardrails per environment; once the refresh lands, the docs
  can be merged without scrambling for context.

Instrumentation deliverables:

- `SimEngine` tracks per-tick durations (p50/p95/max) plus subsystem timings
  using the configurable profiling window so CLI/service/headless summaries all
  surface the same performance block without extra tooling.
- Dedicated profiling sweeps: `content/config/sweeps/profiling-history/` mirrors
  the balanced baseline while expanding `profiling.history_window` to 240 ticks
  so nightly headless runs can compare short-window versus long-window
  percentile smoothing without editing the default config.
- TickCoordinator: orchestrates agents → factions → economy → environment in a
  single module, captures subsystem timings, names the slowest subsystem, and
  emits anomaly tags (subsystem errors/event-budget hits) that flow into the
  CLI summary, `/metrics`, and headless telemetry payloads.
- Guardrail verification matrix:

  | Surface / Safeguard      | Config knob                     | Enforcement behavior                   | Regression hook                                                                  |
  | ------------------------ | ------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------- |
  | Engine tick requests     | `limits.engine_max_ticks`       | Raises `ValueError` when exceeded      | `tests/echoes/test_tick.py::test_engine_enforces_tick_limit`                     |
  | CLI `run` batches        | `limits.cli_run_cap`            | Prefixes output with safeguard warning | `tests/echoes/test_cli_shell.py::test_shell_run_command_is_clamped`              |
  | CLI scripted sequences   | `limits.cli_script_command_cap` | Halts scripts once cap is reached      | `tests/echoes/test_cli_shell.py::test_run_commands_respects_script_cap`          |
  | FastAPI `/tick` endpoint | `limits.service_tick_cap`       | Returns HTTP 400 with detail message   | `tests/echoes/test_service_api.py::test_tick_endpoint_rejects_large_requests`    |
  | Headless batch execution | `limits.engine_max_ticks`       | Auto-chunks to stay beneath engine cap | `tests/scripts/test_run_headless_sim.py::test_run_headless_sim_supports_batches` |

Documenting this table (and keeping it in sync with the README) lets QA pick a
single row to validate whenever a guardrail knob changes.

- Telemetry visualization assists: `scripts/plot_environment_trajectories.py`
  plots pollution/unrest trajectories from multiple sweep captures by reading
  their `director_history` payloads. Before running the script, ensure sweeps
  were captured with `focus.history_length` ≥ the tick budget so the timeline
  covers the full run. Use the tool to compare cushioned, high-pressure, and
  profiling-history presets (or any custom `--run label=path` inputs) whenever
  diffusion weights or scarcity knobs change.

### Phase 4 – Agents, Factions, Economy, Environment

- **M4.1 Agent AI** (1-1.5 days): extend agent traits/goals and implement
  utility-based choices in `systems/agents.py` with reproducible seeds.
- **M4.2 Faction AI** (1-1.5 days): resources, ideology, legitimacy, territory
  plus strategic actions at lower cadence.
- **M4.3 Economy** (1-1.5 days): production/consumption, market price loop, and
  conservation tests to guard against runaway resource inflation.
- **M4.4 Environment** (1 day): pollution/emissions/biodiversity dynamics tied
  to economy + agent actions, adjacency-aware diffusion with configurable
  neighbor bias/min/max clamps, and telemetry that records scarcity pressure,
  faction deltas, and averaged/min/max pollution metrics per tick.
- **M4.5 Tick orchestration** (0.5-1 day): explicitly order subsystem updates,
  emit traces per subsystem, and run smoke scenarios via headless driver.
- **M4.6 Focus-Aware Narration** (complete): shipped the FocusManager module,
  CLI/service `focus` controls, hybrid event budgets (ring + global pools), the
  severity + focus-distance scoring stack, ranked archives, CLI `history`
  browsing, FastAPI focus payloads, and telemetry (`last_event_digest`,
  `focus_budget`, suppressed counts) that records both digest and archive data.
  Long-run mitigation sweeps (baseline, profiling-history, soft-scarcity)
  proved anomaly budgets stay below 100 per 1000 ticks once mean-reversion and
  faction gating landed, so the curator now keeps summaries legible without
  starving distant districts.
- **M4.7 Spatial Coordinates & Adjacency Graph** (in progress): district
  schemas now include planar `coordinates` plus an `adjacent` list. The content
  loader auto-derives symmetric neighbors, the FocusManager blends population
  rank with distance + adjacency bonuses, and tick telemetry/CLI overlays show
  the resulting weights so designers can see when a distant but populous
  district still outranks a nearby low-density one. The narrator's ranked
  digest now feeds a deterministic `director_feed` snapshot (and rolling
  history) so the new `NarrativeDirector` module can consume the same spatial
  weights, ranked archive, and suppressed counts without reimplementing the
  curator. The director now selects the highest-scoring districts, evaluates
  adjacency-aware travel routes (hop counts, distances, estimated travel
  times, reachability), matches authored seeds from
  `content/worlds/<world>/story_seeds.yml`, and publishes both
  `director_analysis` and `story_seeds` metadata that shows hotspot mobility,
  recommended focus handoffs, and the seeds ready to fire. The director caches
  the latest payload for each seed so the `story_seeds` block now tracks
  `cooldown_remaining`/`last_trigger_tick`, keeping matches visible for the
  duration of their cooldowns in CLI/service/headless surfaces. Upcoming work focuses on
  tuning the seed trigger thresholds, adding more authored seeds, and wiring
  resolution/cooldown UX before moving to Phase 5 pacing features.

### Phase 5 – Narrative Director and Story Seeds

- **M5.1 Seed schema** (0.5 day): Formalize the YAML contract in
  `content/worlds/<name>/story_seeds.yml`, including trigger expressions,
  tagging, cooldown defaults, travel hints, and resolution templates. Extend
  the loader plus `StorySeed` model validations so malformed seeds are caught
  at import time, and add regression fixtures in `tests/content` that cover
  both happy-path and failure cases. Refresh the GDD/README with an explicit
  authoring checklist and bake the canonical seeds into the default world so
  telemetry immediately shows populated entries during balanced 200-tick runs.
- **M5.2 Director core** (1-1.5 days): Replace the current scaffolding with a
  fully stateful controller that reads the cached `story_seeds` payloads,
  evaluates triggers against hotspot metrics/travel time, and emits structured
  `director_events` that reference specific agents/factions. Wire the outcomes
  into CLI `summary`/`director` commands, `/state?detail=summary`, and headless
  telemetry so every surface shows which seeds fired, why, and what resolution
  path they are on. Add focused unit tests for trigger evaluation plus an
  integration test that asserts deterministic seed activation for the default
  world/seed combo.
- **M5.3 Pacing/resolution** (0.5-1 day): Layer deterministic cooldown loops
  (per-seed and global quiet periods), add lifecycle tracking (`primed →
  active → resolving → archived`), and expose pacing controls via
  `simulation.yml`. Telemetry and CLI history should capture lifecycle changes
  so long burns prove that crises do not overlap excessively. Extend tests to
  ensure cooldown math survives save/load and that quiet-period enforcement is
  observable via the ranked archive.
- **M5.4 Post-mortem** (0.5 day): Generate deterministic, referenceable
  summaries that stitch together the highest-impact seeds, faction swings, and
  environment trends into a readable epilogue. Provide a CLI command and
  service endpoint that dump the summary for LLM/gateway consumption, and add
  golden outputs tied to the canonical 200-tick telemetry to guard against
  accidental narrative drift.

### Phase 6 – CLI Gateway, Visualization, LLM Intent Layer

- **M6.1 Gateway service** (1 day): FastAPI/WS service that hosts terminal
  sessions and proxies requests to sim service.
- **M6.2 Enhanced ASCII views** (1 day): richer overlays and tabular panels
  reused between CLI and gateway.
- **M6.3 LLM service skeleton** (1-1.5 days): HTTP endpoints for
  `/parse_intent` and `/narrate`, configurable provider adapter, stub mode for
  offline tests.
- **M6.4 Intent schema + prompts** (1 day): JSON schema + prompt templates with
  function-calling enforcement.
- **M6.5 Gateway integration** (1-1.5 days): user text -> LLM intents -> sim
  actions -> narrative response with retry/fallback logic.

### Phase 7 – Player Experience, Progression, Polish

- **M7.1 Progression systems** (1-1.5 days): skills, access tiers, reputation
  influencing success rates and dialogue.
- **M7.2 Explanations** (0.5-1 day): queryable timelines and causal summaries.
- **M7.3 Tuning + replayability** (1-2 days): scenario sweeps, difficulty
  modifiers, config exposure.
- **M7.4 Campaign UX** (0.5-1 day): autosaves, campaign picker, clean
  end-of-run flow in both CLI and gateway.

### Phase 8 – Cross-Cutting Concerns and Next Steps

- **M8.1 Containerization** (0.5-1 day): Dockerfiles + docker-compose for sim,
  gateway, LLM service.
- **M8.2 Kubernetes manifests** (1-2 days): Deployments/Services/ConfigMaps,
  plus Exec Doc `docs/gengine/Echoes_On_K8s_Local.md` mirroring Minikube
  patterns.
- **M8.3 Observability in K8s** (0.5-1 day): Prometheus scraping, resource
  sizing, load smoke tests via `kubectl`.
- **M8.4 Content pipeline** (1-2 days): `scripts/build_content.py` bundles,
  documentation for designers, validation CI hook.

## 1. Foundations & Data Model

- Define core data structures for city, districts, agents, factions, resources, and environment.
- Choose and wire up data-driven content format (for example, YAML) for initial world, agents, factions, and story seeds.
- Implement serialization and deserialization for full game state (save and load).

## 2. Early CLI Shell and ASCII Debug UI

- Implement an initial, monolithic CLI shell that runs the simulation in-process (before full microservice separation) and can:
  - Start and stop a session.
  - Advance time in discrete ticks (for example, a `next` or `run 10` style command).
  - Print basic summaries of city, districts, agents, factions, and resources.
  - Render a simple ASCII map for the current district or city-level overview.
- Use this early CLI shell as the primary test harness while core systems are still evolving, adding new views or commands as additional mechanics come online.

## 3. Simulation Core & Ticking (Service-First)

- Extract the tick loop and core state into a dedicated **simulation service** that coordinates subsystems:
  - Agent AI
  - Faction AI
  - Economy
  - Environment
  - Narrative Director
- Expose a narrow API from the simulation service (for example, gRPC or HTTP+JSON) for querying state and submitting player/LLM intents.
- Gradually refactor the early CLI shell so it calls this simulation API instead of running the simulation in-process.
- Add Level of Detail (LOD) handling (detailed versus coarse simulation) and basic performance safeguards inside the simulation service.
- Create a headless driver (can run as a Kubernetes Job/Pod) to advance ticks and log key state changes for debugging.

## 4. Agents, Factions, Economy, and Environment

- Implement agent AI:
  - Traits, needs, goals, and memory.
  - Utility or GOAP-style decision-making that reads and writes shared state.
- Implement faction AI:
  - Resources, ideology, legitimacy, and territory.
  - Strategic actions such as lobbying, recruitment, sabotage, investment.
- Implement economy subsystem:
  - District-level production, consumption, and storage of key resources.
  - Global market layer that adjusts prices and incentives.
- Implement environment and ecology subsystem:
  - Urban, industrial, and perimeter variables (pollution, emissions, biodiversity, stability).
  - Local rules (growth, decay, diffusion) influenced by human activity.

#### Phase 4 Execution Plan

- **M4.1 Agent AI (Deliverable: `systems/agents.py`)**

  - Expand YAML schema to capture needs/goals/memory slots; update validation script + fixtures.
  - Implement deterministic agent brain (utility model with seeded randomness) that consumes `GameState` slices and emits intents (inspect, negotiate, deploy_resource) recorded in a per-tick log.
  - Guarantee each tick surfaces at least one "strategic" action (inspect or negotiate) so CLI/service/headless outputs always include a high-signal agent beat.
  - Surface agent telemetry in headless summaries (`run_headless_sim.py`) to validate aggregate behavior.
  - Tests: unit tests for decision scoring, property tests for deterministic outputs given identical seeds, CLI regression snapshot ensuring summaries reference new agent activity counts.

- **M4.2 Faction AI (Deliverable: `systems/factions.py`)**

  - Model faction resources/legitimacy deltas per tick and implement strategic actions (lobby, recruit, sabotage, invest) with cooldowns.
  - Add conflict resolution layer so faction actions can transform agent/faction state and city modifiers.
  - Emit structured events for the CLI/service to surface (extend `/state?detail=summary`) and feed telemetry via `faction_actions` counts/breakdowns.
  - Tests: scenario tests where a faction loses legitimacy after repeated unrest, API contract tests ensuring `/metrics` reflects faction deltas, and validation that headless telemetry records faction behavior alongside agent intents.

- **M4.3 Economy Subsystem (Deliverable: `systems/economy.py`)**

  - Introduce production/consumption matrices per district resource, plus global market prices derived from supply/demand curves. **Status:** subsystem live with district rebalancing, shortage counters, and CLI/service/telemetry surfacing of legitimacy + prices.
  - Wire conservation checks into tick loop to prevent negative stocks; raise warnings when shortages persist N ticks.
  - Persist economic config knobs via the `economy` block inside `content/config/simulation.yml` (regen scale, demand weights, shortage thresholds, price floors/ceilings) so designers can retune without code changes.
  - Tests: expanded regression/property-style unit tests covering price floors/ceilings, shortage-triggered price hikes, and long-run conservation. Scenario sweeps remain on the backlog to complement the new fast unit coverage.

- **M4.4 Environment Dynamics (Deliverable: `systems/environment.py`)**

  - Implemented the EnvironmentSystem scaffolding plus config weights that turn
    economy shortages into district unrest/pollution deltas, drive adjacency-
    aware diffusion (neighbor bias + min/max caps), and translate faction
    investments/sabotage into pollution relief or spikes that appear in
    telemetry/CLI summaries. Biodiversity health now threads through the same
    loop: scarcity pressure erodes the new `EnvironmentState.biodiversity`
    field, recovery pulls it toward a configurable baseline, stability coupling
    provides feedback when biodiversity dips below the midpoint, and CLI/service
    summaries alert whenever the value falls beneath the configured threshold.
  - Integrate with LOD settings so coarse mode aggregates environment updates
    while detailed mode runs district-level diffusion (baseline diffusion now
    implemented via EnvironmentSystem; future work tunes per LOD).
  - Extend CLI `summary`/`map` output with new environment indicators and
    warnings plus telemetry surfacing of `environment_impact` (summary block now
    live with scarcity pressure, faction deltas, biodiversity/stability
    snapshots, average pollution, min/max districts, and sampled diffusion
    deltas; map warnings pending dedicated environment events).
  - Config exposure: the shared `environment` block in
    `content/config/simulation.yml` now includes biodiversity knobs
    (`biodiversity_baseline`, `biodiversity_recovery_rate`,
    `scarcity_biodiversity_weight`, `biodiversity_stability_weight`,
    `biodiversity_stability_midpoint`, `biodiversity_alert_threshold`) so
    designers can tune how fast ecosystems erode, how quickly they rebound, and
    how hard they tug on stability without touching code. Document default
    values in README/gameplay guide and mirror them across sweep configs.
  - Tests: maintain targeted regression/property tests for the coupling and add
    scenario coverage for pollution emergencies, diffusion telemetry,
    biodiversity scarcity/recovery loops, stability feedback, and CLI messaging.

- **M4.5 Tick Orchestration & Telemetry (Deliverable: updated `SimEngine.advance_ticks`)**
  - Define subsystem execution order (agents → factions → economy → environment → narrative hooks) with clear contracts and shared context objects.
  - Add OpenTelemetry-style trace hooks or structured logs capturing per-subsystem duration, errors, and key metrics; expose aggregates via `/metrics`.
  - Update headless driver summary to include subsystem durations and detected anomalies, enabling nightly sweeps.
  - Tests: integration suite running multi-tick scenarios ensuring subsystem order is deterministic, coverage for telemetry payloads, and failure-path tests verifying safeguards halt the tick with actionable errors.
  - Long-run soak: after adding mean-reversion to district modifiers and gating sabotage so only low-legitimacy factions strike when stability is healthy, the baseline (`build/focus-baseline-1000tick.json`), profiling-history (`build/profiling-history-1000tick.json`), and soft-scarcity (`build/profiling-history-soft-scarcity-1000tick.json`) configs each cleared 1000 ticks with **0** `event_budget` anomalies. Baseline stability now bottoms out around **0.57** while the profiling-history and soft-scarcity variants remain at **1.0**, giving the narrator ample ranked inventory every tick.
  - Mitigation sweeps: keep the dedicated profiles under `content/config/sweeps/` for targeted validation. The profiling-history variant (history window 240) offers a long rolling percentile reference, the soft-scarcity preset highlights how low pressure plus reduced volatility keeps suppressed events under 300, and the high-budget profile (`.../profiling-history-high-budget/`) is still available when you need to raise `lod.max_events_per_tick` for stress tests even though the baseline burn no longer requires it.
  - Introduce a phased plan for dynamic event budgets: short term, raise `lod.max_events_per_tick` cautiously for regression sweeps; medium term (M4.6, now delivered) add a "focus manager" so the TickCoordinator grants higher per-tick budgets to the player’s focused district plus its neighbors while leaving a smaller global pool for the rest of the city. This keeps summaries legible as the world grows (more districts/agents/factions) and preserves anomaly tags as meaningful signals. Document the API surface (CLI `focus` command, service session focus) and ensure telemetry exposes both global and focus-aware clamps.
    - Narrator integration: once the focus manager allocates beats deterministically, the narrator layer can score every event by relevance (focus distance, severity, novelty) and promote the top 3–5 into the player-facing digest while pushing the rest into an append-only history buffer in `state.metadata`. The CLI/gateway will surface the digest by default and expose `history` commands so testers can browse suppressed beats after the fact.
    - Gameplay impact: exceeding ~100 `event_budget` anomalies per 1000 ticks means ~20% of ticks lose at least one story beat before curation, so the narrator cannot explain causality reliably. Likewise, the high-budget preset (20 events/tick) eliminates anomalies but crashes stability after ~350 ticks, producing repetitive crisis beats that overwhelm the narrator. The focus-aware plan must therefore (1) keep anomalies <100 without destabilizing the world and (2) give the narrator enough ranked inventory each tick to pick high-signal beats while archiving the rest for later discovery.
    - Telemetry tasks: extend the profiling payload with `focus_budget` vs. `global_budget` counters plus `suppressed_events` per tick so QA can confirm the curator is working even when the player only sees a handful of beats. Headless captures should store both the digest (what the player saw) and the archival log so we can diff narrative exposure over long soaks.
  - Status: the focus manager + CLI/service command now exist, TickCoordinator
    emits `focus_budget` payloads per tick, suppressed/archived events flow into
    metadata and headless telemetry (`last_event_digest`), config files gain a
    dedicated `focus` block (`default_district`, neighborhood sizing, budget
    ratio, digest/history lengths), narrator scoring ranks every event by
    severity + focus distance, and the CLI/gateway expose the ranked history.
    Current focus defaults keep anomalies <100 during 1000-tick soaks; future
    tuning will pair spatial weighting (M4.7) and narrative director hooks with
    the delivered curator.

**Dependencies & Tooling Notes**

- Content updates for traits/factions/resources must land before subsystem code to keep validation green.
- Reuse the newly added safeguards + headless driver for soak testing after each milestone; target ≥500 ticks per run without instability.
- Maintain ≥90% coverage for new modules; critical decision logic must hit 100% where feasible.
- Document every milestone in README + gameplay guide once the corresponding subsystem becomes player-visible.

## 5. Narrative Director & Story Seeds

- Define a data format for story seeds (triggers, roles, stakes, resolution templates) and load them from external files.
- Build the narrative director (as a logical module within the simulation service, or a separate microservice if needed) that:
  - Monitors global metrics (stability, inequality, tech risk, environment, factional polarization, player reputation).
  - Activates appropriate story seeds and attaches them to existing agents and factions.
  - Manages pacing so crises and quiet periods alternate.
- Implement outcome vignettes and a post-mortem generator that summarize causal chains and final city state at campaign end.

## 6. CLI Gateway Service, ASCII Visualization, and LLM Intent Layer

- Implement a **CLI gateway service** that:
  - Hosts the text-based player session, reading and writing to a terminal/TTY.
  - Calls the LLM service to interpret player input.
  - Calls the simulation service API to query state and submit structured actions.
- Add ASCII rendering in the CLI gateway for city and district maps plus textual overlays:
  - District grids, control zones, and environmental heatmaps.
  - Tables for resources, faction influence, and key agents.
- Implement an **LLM service** that:
  - Parses free-form player input into structured intents mapped to the simulation action API.
  - Generates in-world text (dialogue, headlines, summaries) constrained by current state provided by the simulation service.
  - Can scale independently on Kubernetes (for example, with HPA based on latency/QPS).
- Ensure the conversational flow is stateless or minimally stateful per session, with any persistent game state stored in the simulation service or backing store.

## 7. Player Experience, Progression, and Polish

- Implement progression systems:
  - Skills (negotiation, investigation, systems hacking, logistics, stealth).
  - Access tiers (security clearance, new districts, deeper network layers).
  - Reputation profiles that affect NPC and faction responses.
- Add "why did this happen?" tools:
  - Event timelines, causal explanations, and agent reasoning summaries surfaced in the CLI.
- Tune pacing, difficulty, and replayability:
  - Different starting configurations and modifiers.
  - Story seed variety, activation thresholds, and frequency.
- Refine UX flows for campaigns, autosaves, end-of-run summaries, and post-mortems, ensuring service boundaries remain clear (for example, save/load handled by simulation service, presentation handled by CLI gateway).

## 8. Cross-Cutting Concerns and Next Steps

- Define the Kubernetes deployment model:
  - Separate Deployments for simulation service, CLI gateway service, and LLM service.
  - Shared configuration via ConfigMaps and Secrets for environment, models, and content paths.
  - Service definitions (ClusterIP/Ingress) for inter-service communication and external CLI access.
- Decide on LLM hosting or inference strategy (local model, remote API, or hybrid) and acceptable latency budgets; encapsulate details in the LLM service so other services remain decoupled.
- Align on target scale (number of agents, districts, and factions) to size the simulation service resources and LOD heuristics.
- Establish content pipelines so designers can author and test YAML/world data and story seeds quickly, ideally via a separate content-build step that produces artifacts consumed by the simulation service.
- Once the core loop is robust, iterate on art direction for ASCII layouts and on narrative tone via seed and prompt tuning.
