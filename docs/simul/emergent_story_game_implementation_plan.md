## 9. Automated Balance Workflow and Strategy Tuning

To ensure robust game balance and support data-driven strategy design, implement an automated workflow:

- **Batch Simulation Sweeps:** Run large numbers of simulations with varied parameters, world configs, and strategy settings using the AI tournament tooling.
- **Result Aggregation:** Collect and store outcomes (win rates, stability, actions, story seeds, etc.) for each run in structured files or a database.
- **Analysis & Reporting:** Use scripts to analyze aggregated results, identify dominant strategies, balance issues, and underutilized content.
- **Strategy Evolution:** Automatically tune or generate new strategy parameters based on analysis (e.g., via optimization, evolutionary algorithms, or machine learning).
- **Continuous Integration:** Integrate this workflow into CI pipelines to regularly validate game balance and surface regressions.
- **Designer Feedback Loop:** Surface actionable insights to designers for manual tuning, scenario creation, and content iteration.

This approach enables rapid, repeatable balance iteration and supports both manual and automated strategy development.
# Plan: Implement "Echoes of Emergence" (CLI + LLM Sim)

A staged implementation that builds a solid simulation core, then layers on
agents and factions, narrative, and finally the CLI + LLM conversational
interface with ASCII visualization. The runtime architecture is
microservice-based and designed to run on Kubernetes from the outset. This
plan is informed by and should be read alongside the game design document in
`docs/simul/emergent_story_game_gdd.md`. Each phase should be testable in
isolation via minimal scripts before integrating, with data-driven content
and full save/load from the start.

## Progress Log (Updated 2025-11-29)

- ✅ Phase 1 (Foundations & Data Model): core models, YAML loader,
  snapshots, smoke tests.
- ✅ Phase 2 (Early CLI Shell & Tick Loop): in-process `echoes-shell` CLI with
  summary/next/run/map/save/load commands plus a deterministic tick engine.
- ⚙️ Phase 3 (Simulation Core & Service API): **M3.1 SimEngine abstraction
  landed**, **M3.2 FastAPI service + typed client shipped**, **M3.3 CLI service
  mode running**, **M3.4 safeguards + LOD shipped**, and **M3.5 headless driver
  online**.
- ⚙️ Phase 4 (Agents/Factions/Economy): **M4.1 Agent AI** and **M4.2 Faction
 AI**
  shipped; **M4.3 Economy** now includes the subsystem, designer-facing config
  knobs, legitimacy/market telemetry, and expanded tests. **M4.4 Environment**
  now routes scarcity pressure into unrest/pollution, biases diffusion toward
  adjacent districts with configurable neighbor weights/min/max clamps, tracks
  biodiversity health (scarcity decay, configurable recovery baseline, stability
  coupling, alert threshold), and captures richer telemetry (average pollution,
  extremes, sampled diffusion deltas, biodiversity/stability snapshots) that
  surfaces in CLI/service/headless summaries. Remaining Phase 4 work focuses on
  long scenario sweeps plus director UX polish before merging back to main.
- ✅ Phase 5 (Narrative Director & Story Seeds): **M5.1 story seed schema**,
  **M5.2 director events**, **M5.3 pacing/lifecycle**, and **M5.4 post-mortems**
  are merged to `main`. Lifecycle guardrails ship with deterministic telemetry
  (`director_pacing`, lifecycle tables/history, quiet timers), and the
  post-mortem generator now surfaces identical recaps through the CLI,
  FastAPI, and headless telemetry using the documented canonical artifact
  (`build/feature-m5-4-post-mortem.json`) plus `jq '.post_mortem'` diff
  workflow so reviewers can compare runs without replaying ticks.
- ⚙️ Phase 6 (CLI Gateway, Visualization, LLM intent layer): **M6.1 gateway
  service** ships with `gengine.echoes.gateway`, a FastAPI/WebSocket host that
  proxies CLI commands to the simulation service, logs focus/digest/history
  snapshots per session, and exposes the `echoes-gateway-service` runner plus
  an `echoes-gateway-shell` client. Regression tests cover `/ws` round-trips
  and malformed payloads, docs explain the WebSocket contract, and the new
  dependency (`websockets`) is wired through `uv sync --group dev` so local
  - CI environments can exercise remote sessions immediately. **M6.2 enhanced
    ASCII views** adds `gengine.echoes.cli.display` with Rich-based rendering
    (styled tables, color-coded panels, formatted story seed/director displays),
    integrated via `--rich` flag in `echoes-shell`, with 9 new regression tests
    covering display formatting and shell integration. **M6.3 LLM service
    skeleton** ships with `gengine.echoes.llm` module providing `/parse_intent`
    and `/narrate` endpoints, environment-variable configuration, abstract
    provider pattern (with `StubProvider` for offline testing), and
    `echoes-llm-service` CLI entry point. 31 new tests cover settings,
    providers, and FastAPI endpoints (243 tests total, 94% coverage).
- ⚙️ Phase 7 (Player Experience): **M7.1 Progression** shipped with
  `ProgressionState` models (skills, access tiers, reputation),
  `ProgressionSystem` for per-tick updates, configuration in `simulation.yml`,
  and 48 new tests. **M7.1.2 Per-Agent Progression** shipped with
  `AgentProgressionState` model (specialization, expertise pips, reliability,
  stress, mission counters), GameState integration with `ensure_agent_progressio
n()`
  and `get_agent_progression()` helpers, per-agent tick processing in
  `ProgressionSystem`, configuration via `per_agent_progression` block with
  `enable_per_agent_modifiers` toggle, `calculate_agent_modifier()` success
  wrapper, and 43 new tests. **M7.2 Explanations** shipped with
  `ExplanationsManager`, CLI commands (`timeline`, `explain`, `why`), causal
  chain tracking, and agent reasoning summaries. **M7.4 Campaign UX** shipped
  with `gengine.echoes.campaign` module providing campaign creation, autosave,
  resume, and end-of-campaign flows with post-mortem integration. Remaining:
  M7.3 tuning.

### M7.1.x – Per-Agent Progression Layer (shipped)

Design reference: GDD §4.1.1 "Per-Agent Progression & Traits".

Objective: add a lightweight, bounded **per-agent progression** state keyed by `
agent_id`

that layers on top of the existing global `ProgressionState` without changing pu
blic APIs

or overwhelming players with micromanagement.

Implementation checklist (completed):

1. ✅ **Core model: `AgentProgressionState`**
   - Add a new Pydantic model in `src/gengine/echoes/core/progression.py` or a
     sibling module, representing:
     - `agent_id: str`
     - `specialization: Literal[...]` or `Enum` aligned to the existing `SkillDo
main`
       families (e.g., negotiator/investigator/operator/influencer).
     - `expertise: Dict[str, int]` with small integer pips (0–5) per
       domain family.
     - `reliability: float` and `stress: float` in bounded ranges (e.g., 0.0–1
.0) with
       helper methods that clamp values.
     - `missions_completed: int`, `missions_failed: int` counters.
   - Include a `summary()` method that returns a compact dict suitable for CLI/s
ervice
     displays (role label, expertise pips, stress word, history snapshot).

2. ✅ **GameState integration**
   - Extend `GameState` in `src/gengine/echoes/core/__init__.py` (or appropriate
     module) to include:
     - `agent_progression: Dict[str, AgentProgressionState] = {}` (optional,
       defaults to empty).
   - Add a helper `ensure_agent_progression(agent_id: str) -> AgentProgressionSt
ate`
     that:
     - Returns an existing state if present, otherwise creates a new one with a
       default specialization and neutral stats.
   - Ensure snapshot serialization/deserialization persists `agent_progression`
     without breaking backward compatibility (old snapshots should treat it as
     absent/empty).

3. ✅ **Wire into `ProgressionSystem.tick(...)`**
   - Update `ProgressionSystem` in `src/gengine/echoes/systems/progression.py` t
o
     optionally handle per-agent updates:
     - **Do not change** the existing signature or behavior of global
       `ProgressionState` updates.
     - In `_process_agent_action(...)`, after applying global skill XP:
       - Read `agent_id` and `success`/`outcome` fields from each `agent_actions
` entry if present.
       - Call `state.ensure_agent_progression(agent_id)` to get per-agent state.
       - Map `intent` to a domain family using the existing `ACTION_SKILL_MAP` t
able.
       - Increment expertise pips and adjust reliability/stress according to the
 GDD rules (bounded, small deltas).
     - Append an `agent_progression` event into metadata/telemetry, mirroring ho
w `progression_history` works today (keep last N entries).

4. ✅ **Config surface and safe defaults**
   - Add a new `per_agent_progression` section under `content/config/simulation.
yml` with knobs such as:
     - `expertise_max_pips`, `expertise_gain_per_success`.
     - `stress_gain_per_failure`, `stress_recovery_per_rest_tick`.
     - `reliability_gain_per_success`, `reliability_loss_per_failure`.
     - `max_expertise_bonus`, `max_stress_penalty` for success modifiers.
   - Wire these into a small `PerAgentProgressionSettings` dataclass used by `Pr
ogressionSystem`, defaulting to very conservative values so turning the feature
on has minimal balance impact initially.

5. ✅ **Success modifier integration (optional, behind a flag)**
   - Introduce a helper (e.g., `calculate_agent_modifier(global_progression, age
nt_progression, skill_domain, faction_id, settings) -> float`) that:
     - Wraps the existing `calculate_success_modifier` and then applies a limite
d agent-specific tweak within the configured bounds.
   - Gate usage of this helper behind a config flag (`enable_per_agent_modifiers
`) so early experiments can be run without destabilizing existing tests/scenario
s.

6. ✅ **Surfaces: CLI/service/explanations**
   - Extend existing summary/detail endpoints and CLI views to optionally show p
er-agent:
     - Specialization/role label.
     - Expertise pips per domain family.
     - Stress state word and very short history blurb.
   - Feed one- or two-sentence agent progression notes into the explanations/pos
t-mortem surfaces when relevant (e.g., “agent burnout slightly reduced odds he
re”).

7. ✅ **Tests and telemetry**
   - Add unit tests for `AgentProgressionState` (creation, clamping, expertise g
rowth, stress/reliability updates) alongside existing progression tests in `test
s/echoes/test_progression.py`.
   - Add scenario tests that:

     - Run a small number of ticks with repeated agent actions and assert that a
gent expertise/stress move in the expected direction while global progression st
ill behaves as before.
     - Verify that snapshots round-trip `agent_progression` cleanly.
     - Extend headless telemetry captures (e.g., `build/feature-m7-1-progression
-agent.json`) with a small, documented `agent_progression` block to validate tun
ing over time.

   - ⏳ Phase 8: pending (containerization, Kubernetes).## Tech Stack and Runti
me Assumptions

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

- `systems.agents`, `systems.factions`, `systems.economy`, `systems.environment`
:
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
- `GET /state?detail=summary|snapshot|district|post-mortem` -> trimmed state
  payloads sized for CLI consumption, including the deterministic post-mortem
  recap used by the CLI `postmortem` command and headless telemetry.
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
  `scripts/run_headless_sim.py --world default --ticks 200 --lod balanced --seed
 42 --output build/feature-m5-4-post-mortem.json`
  so regressions always include a comparable metrics snapshot (now including
  faction legitimacy snapshots/deltas, the last economy table, and the new
  `post_mortem` recap that CLI/service surfaces share).
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
  `SimEngine` now enforces the guardrails, logs tick metrics, and the CLI/servic
e
  surface friendly warnings when requests exceed the configured caps.
- **M3.5 Headless driver** (complete): `scripts/run_headless_sim.py` runs
  long-form burns by chunking work into `engine_max_ticks`, prints per-batch
  diagnostics, and writes JSON summaries (tick counts, timing, LOD mode,
  environment snapshot) for regression diffs or CI sweeps. Supports snapshot
  bootstrap, seed overrides, and alternate config roots.

#### M3.4 Safeguards & LOD – Refresh Prep

- Audit every guardrail surface (SimEngine caps, CLI `run` guard, service tick
  limits, headless script batches) against the latest config to confirm the
  values align with Phase 4 loads and note any deltas that need designer signoff
.
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
- TickCoordinator: orchestrates agents → factions → economy → environment
in a
  single module, captures subsystem timings, names the slowest subsystem, and
  emits anomaly tags (subsystem errors/event-budget hits) that flow into the
  CLI summary, `/metrics`, and headless telemetry payloads.
- Guardrail verification matrix:
<!-- markdownlint-disable MD013 -->
| Surface        | Config                        | Behavior                      | Test                                      |
| -------------- | ----------------------------- | ----------------------------- | ----------------------------------------- |
| Engine ticks   | limits.engine_max_ticks       | Raises ValueError if exceeded | test_engine_enforces_tick_limit           |
| CLI run        | limits.cli_run_cap            | Warns on cap                  | test_shell_run_command_is_clamped         |
| CLI scripts    | limits.cli_script_command_cap | Halts on cap                  | test_run_commands_respects_script_cap     |
| /tick endpoint | limits.service_tick_cap       | HTTP 400                      | test_tick_endpoint_rejects_large_requests |
| Headless       | limits.engine_max_ticks       | Auto-chunks                   | test_run_headless_sim_supports_batches    |
<!-- markdownlint-enable MD013 -->

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
  duration of their cooldowns in CLI/service/headless surfaces. Upcoming work fo
cuses on
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
  `director_events` that reference specific agents/factions plus their
  resolution templates. Wire the outcomes into CLI `summary`/`director`
  commands, `/state?detail=summary`, and headless telemetry so every surface
  shows which seeds fired, why, which participants are attached, and what
  resolution path they are on. Add focused unit tests for trigger evaluation
  plus an integration test that asserts deterministic seed activation for the
  default world/seed combo.
- **M5.3 Pacing/resolution** (shipped): implements the lifecycle state machine
  plus user-facing telemetry so pacing regressions show up immediately.
  - `DirectorSettings` now exposes `max_active_seeds`, `global_quiet_ticks`,
    `seed_active_ticks`, `seed_resolve_ticks`, `seed_quiet_ticks`, and
    `lifecycle_history_limit` knobs in every config variant (baseline and sweep
    folders) so designers can dial overlap, dwell time, and history depth
    without touching code.
  - `NarrativeDirector` records lifecycle state per seed, enforces per-seed
    cooldowns and quiet timers, respects the global quiet span, and writes the
    resulting metadata to `story_seed_lifecycle`, `story_seed_lifecycle_history`
,
    `director_pacing`, and `director_quiet_until`. CLI summary, the `director`
    command, FastAPI `/state?detail=summary`, and headless telemetry inherit the
    new payloads so playtesters see why a seed is blocked (max-active,
    seed quiet, global quiet) alongside remaining durations.
  - The `director_pacing` payload spells out `active_count`, `resolving_count`,
    `blocked_reasons`, and `quiet_remaining_ticks` so reviewers can diff pacing
    regressions between telemetry captures without replaying the run. The
    companion `story_seed_lifecycle` table lists each seed id, lifecycle state,
    ticks remaining in that state, cooldown timers, and the last trigger tick,
    matching what the CLI renders for rapid troubleshooting.
  - Regression coverage now includes
    `tests/echoes/test_story_seeds.py::test_summary_includes_pacing_and_lifecycl
e_metadata`
    for summary rendering plus
    `tests/echoes/test_story_seeds.py::test_story_seed_lifecycle_transitions_and
_persists`
    to assert `primed → active → resolving → archived` transitions survive
    snapshot save/load.

  - `scripts/run_headless_sim.py` emits the same pacing data (`director_pacing`,
    lifecycle tables/history, and quiet timer), so nightly sweeps can diff
    cooldown math against previous artifacts. Canonical validation remains the
    balanced 200-tick run: `uv run python scripts/run_headless_sim.py --world
default --ticks 200 --lod balanced --seed 42 --output
build/feature-m5-3-director-pacing.json` after a full
    `uv run --group dev pytest` sweep.
  - Documentation updates (README, GDD, gameplay guide) now explain how to read
    the new `director_pacing` block, where to tune the pacing knobs, and how to
    capture reviewer telemetry so test plans stay reproducible.
- **M5.4 Post-mortem** (shipped): The `generate_post_mortem_summary` helper
  stitches environment start/end/deltas, top faction legitimacy swings, the
  most recent director events, and a ranked story-seed recap into a
  deterministic payload cached under `state.metadata["post_mortem"]`. The CLI
  exposes it via the `postmortem` command, the FastAPI service returns the same
  data with `GET /state?detail=post-mortem`, and the headless driver embeds it
  inside every telemetry JSON so QA/LLM tooling can diff epilogues without
  rehydrating snapshots. Regression coverage now locks the CLI + service
  schemas to prevent silent field drift, and all reviewer surfaces cite the
  canonical balanced capture below.
  - Canonical telemetry capture mirrors the README instruction: `uv run python
scripts/run_headless_sim.py --world default --ticks 200 --lod balanced
--seed 42 --output build/feature-m5-4-post-mortem.json`. Reviewers diff the
    `.post_mortem` sections between runs (for example,
    `jq '.post_mortem' build/feature-m5-4-post-mortem.json`) to isolate recap
    deltas without the rest of the telemetry noise.

### Phase 6 – CLI Gateway, Visualization, LLM Intent Layer

- **M6.1 Gateway service** (shipped): FastAPI/WebSocket host (`/ws` +
  `/healthz`) that provisions an `EchoesShell` per connection, proxies each
  command to the simulation service via `SimServiceClient`, streams rendered
  output back to the client, and logs focus/digest/history snapshots through
  `gengine.echoes.gateway`. Ships with the `echoes-gateway-service` runner,
  JSON-based WebSocket contract documentation, unit tests covering happy-path
  sessions + malformed payloads, and a `echoes-gateway-shell` companion CLI
  that reuses the same prompt/script workflows as `echoes-shell`.
- **M6.2 Enhanced ASCII views** (shipped): `gengine.echoes.cli.display` module
  provides Rich-based rendering with styled tables (`render_summary_table`),
  color-coded panels for environment/focus/digest (`_render_environment_panel`,
  etc.), and formatted director/map overlays. Integrated into `EchoesShell` via
  `enable_rich` parameter and `--rich` CLI flag. 9 new regression tests cover
  display formatting and shell integration. All display functions are reusable
  by gateway and future visualization tools.
- ✅ **M6.3 LLM service skeleton** (1-1.5 days): HTTP endpoints for
  `/parse_intent` and `/narrate`, configurable provider adapter, stub mode for
  offline tests. **Shipped:** `gengine.echoes.llm` module with FastAPI service,
  environment-variable configuration (`LLMSettings`), abstract provider pattern
  with `StubProvider` for offline testing, CLI entry point
  (`echoes-llm-service`), and 31 tests covering settings, providers, and
  endpoints (243 tests total, 94% coverage maintained). **M6.4 intent schema +
  prompts** ships with `gengine.echoes.llm.intents` defining 7 Pydantic intent
  types (INSPECT, NEGOTIATE, DEPLOY_RESOURCE, PASS_POLICY, COVERT_ACTION,
  INVOKE_AGENT, REQUEST_REPORT) with field validation and type-safe parsing,
  plus `gengine.echoes.llm.prompts` providing OpenAI function calling schemas,
  Anthropic structured output schemas, system prompts with game world context,
  and dynamic prompt builders for context injection. 55 new tests cover intent
  validation and prompt template generation (298 tests total, 94% coverage,
  new modules at 100%).
- **M6.5 Gateway integration** (1-1.5 days): user text -> LLM intents -> sim
  actions -> narrative response with retry/fallback logic.
- **M6.6 Real LLM providers** (1-1.5 days): Implement `OpenAIProvider` and
  `AnthropicProvider` with function calling/structured outputs, integrate with
  intent schemas and prompt templates from M6.4, add configuration for API
  keys and model selection, include retry logic and error handling, write
  integration tests with mocked API responses.

### Phase 7 – Player Experience, Progression, Polish

- ✅ **M7.1 Progression systems** (1-1.5 days): skills, access tiers, reputatio
n
  influencing success rates and dialogue. Implemented in
  `gengine.echoes.core.progression` (ProgressionState, SkillDomain, AccessTier,
  ReputationState) and `gengine.echoes.systems.progression` (ProgressionSystem).
  Skills (diplomacy, investigation, economics, tactical, influence) gain
  experience from agent/faction actions each tick. Access tiers unlock at averag
e
  skill levels 50 (Established) and 100 (Elite). Faction reputation (-1.0 to 1.0
)
  affects action success rates. Configuration exposed via `progression` block in
  `simulation.yml`. GameState includes optional `progression` field that persist
s
  across snapshots. SimEngine integrates progression updates after each tick and
  exposes `progression_summary()` and `calculate_success_chance()` APIs.
  Comprehensive test suite (48 tests) covers models, system, and integration.
  Documentation updated in gameplay guide with progression mechanics explanation
.
- ✅ **M7.2 Explanations** (0.5-1 day): queryable timelines and causal summarie
s.
  Implemented via `ExplanationsManager` in `gengine.echoes.sim.explanations`
  which tracks causal chains between events, builds agent reasoning summaries,
  and provides query interfaces for metrics/factions/agents/districts. CLI
  commands `timeline`, `explain`, and `why` surface this data to testers. The
  system captures per-tick environment deltas, faction legitimacy changes, agent
  actions with inferred reasoning factors, and story seed activations into a
  rolling timeline that persists in game state metadata.
- **M7.3 Tuning + replayability** (1-2 days): scenario sweeps, difficulty
  modifiers, config exposure.
- ✅ **M7.4 Campaign UX** (shipped): Campaign management module at
  `gengine.echoes.campaign` provides:
  - `CampaignManager` for campaign lifecycle (create, list, load, save, end)
  - `Campaign` model tracking name, world, tick, created/saved timestamps
  - `CampaignSettings` configuration via `simulation.yml` campaign block
  - Autosave functionality at configurable tick intervals with cleanup
  - Post-mortem generation on campaign end
  - CLI commands: `campaign new/list/resume/end/status`
  - `--campaign <id>` CLI flag for direct campaign resumption
  - 23 new tests covering campaign management and integration

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

### Phase 9 – AI Player Testing and Validation

AI player implementation lives under `src/gengine/ai_player/` to distinguish it
from the in-game agent AI systems (`src/gengine/echoes/systems/agents.py`). The
AI player is a testing and validation tool that exercises the game APIs
programmatically, enabling automated balance tuning, edge case discovery, and
playthrough validation.

- **M9.1 Observer AI foundation** (1-2 days): Implement `ai_player/observer.py`
  that connects via `SimServiceClient` or local `SimEngine`, advances ticks,
  analyzes state snapshots, and generates structured commentary or insights.
  Create `scripts/run_ai_observer.py` to execute AI-observed sessions with
  configurable tick budgets and output formats (JSON summaries, natural language
  logs). Add integration tests under `tests/ai_player/` that validate the
  observer can parse telemetry, detect trends (stability drops, faction swings),
  and surface narrative coherence metrics. Document observer modes and output
  schemas in the README.

  **Acceptance Criteria:**

  - Observer connects to both local and service-mode simulations
  - Generates tick-by-tick analysis capturing stability trends, faction
    legitimacy shifts, and story seed activations
  - Outputs structured JSON plus optional natural language commentary
  - Integration test asserts observer detects a scripted stability crash
  - README includes observer invocation examples and use cases

- ✅ **M9.2 Rule-based action layer** (shipped): Extended `ai_player/strategies
.py`
  with heuristic decision logic (emergency responses for low stability, resource
  rebalancing, faction support). Implemented `ai_player/actor.py` that wraps
  observer analysis with action selection, submits intents via the action API,
  and logs decisions for replay. Added regression tests that run 100-tick games
  with AI interventions and assert deterministic outcomes under fixed seeds.
  Telemetry captures AI decision rationale alongside simulation state.

  **Acceptance Criteria (all met):**

  - ✅ Rule-based strategies (balanced, aggressive, diplomatic) implemented
  - ✅ AI actor submits valid intents and handles API responses/errors
  - ✅ Regression test shows AI can stabilize a failing city
  - ✅ Telemetry captures AI decision rationale alongside game state
  - ✅ Documentation covers strategy tuning and custom rule authoring

- **M9.3 LLM-enhanced decisions** (COMPLETED):
  `ai_player/llm_strategy.py` and `HybridStrategy` in `strategies.py` delegate
  complex narrative choices to the LLM service when story seeds trigger or
  critical thresholds are crossed. Budget controls via `LLMStrategyConfig`
  (max LLM calls per session, cost tracking) with automatic fallback to
  rule-based logic when quota exhausted. Scenario tests compare rule-only vs.
  hybrid AI performance. Telemetry tracks `decision_source` ("rule"/"llm").

  **Acceptance Criteria (all met):**

  - ✅ Hybrid strategy routes routine actions to rules, complex choices to LLM
  - ✅ Budget enforcement prevents runaway API costs
  - ✅ Scenario tests compare rule-only vs hybrid behavior
  - ✅ Documentation includes prompt and trade-off guidance
  - ✅ Telemetry distinguishes rule-based vs. LLM-driven decisions

- ✅ **M9.4 AI tournaments and balance tooling** (COMPLETED): Created
  `scripts/run_ai_tournament.py` that executes N parallel games with varied AI
  strategies, world configs, and random seeds. Aggregates results into
  comparative reports (win rates, average stability curves, story seed coverage,
  resource efficiency). Added `scripts/analyze_ai_games.py` that identifies
  dominant strategies, balance outliers, and underutilized content. Documented
  tournament workflow and balance iteration loops in gameplay guide.

  **Acceptance Criteria (all met):**

  - ✅ Tournament script runs 100+ games in parallel with configurable strategies
  - ✅ Comparative reports surface win rate deltas and balance anomalies
  - ✅ Analysis identifies unused story seeds or overpowered actions
  - ✅ Documentation guides designers through balance iteration workflow
  - ✅ CI integration runs nightly tournaments and archives results

**Phase 9 Dependencies:**

- M9.1 (Observer) can start immediately with existing simulation APIs
- M9.2 (Rule-based actions) requires Phase 6 action routing and intent schema
- M9.3 (LLM enhancement) requires Phase 6 LLM service integration ✅
- M9.4 (Tournaments) requires M9.2 at minimum, benefits from M9.3

**Folder Structure:**

```text
src/gengine/ai_player/
  __init__.py
  observer.py       # State analysis and commentary generation
  actor.py          # Action selection and submission
  strategies.py     # Rule-based decision heuristics
  llm_strategy.py   # LLM-enhanced narrative choices
scripts/
  run_ai_observer.py   # Execute observer-only sessions
  run_ai_actor.py      # Run AI player with actions
  run_ai_tournament.py # Multi-game comparative analysis
  analyze_ai_games.py  # Balance and coverage reports
tests/ai_player/
  test_observer.py
  test_strategies.py
  test_actor.py
  test_llm_strategy.py
```

**Key Design Principles:**

- AI player uses the same public APIs as human players (no privileged access)
- Clear separation from in-game agent AI to avoid confusion
- Deterministic rule-based core with opt-in LLM enhancement
- Telemetry captures AI reasoning for debugging and analysis
- Designed as a development/QA tool, not a shipped game feature

## 1. Foundations & Data Model

- Define core data structures for city, districts, agents, factions, resources,
and environment.
- Choose and wire up data-driven content format (for example, YAML) for initial
world, agents, factions, and story seeds.
- Implement serialization and deserialization for full game state (save and load
).

## 2. Early CLI Shell and ASCII Debug UI

- Implement an initial, monolithic CLI shell that runs the simulation in-process
 (before full microservice separation) and can:
  - Start and stop a session.
  - Advance time in discrete ticks (for example, a `next` or `run 10` style comm
and).
  - Print basic summaries of city, districts, agents, factions, and resources.
  - Render a simple ASCII map for the current district or city-level overview.
- Use this early CLI shell as the primary test harness while core systems are st
ill evolving, adding new views or commands as additional mechanics come online.

## 3. Simulation Core & Ticking (Service-First)

- Extract the tick loop and core state into a dedicated **simulation service** t
hat coordinates subsystems:
  - Agent AI
  - Faction AI
  - Economy
  - Environment
  - Narrative Director
- Expose a narrow API from the simulation service (for example, gRPC or HTTP+JSO
N) for querying state and submitting player/LLM intents.
- Gradually refactor the early CLI shell so it calls this simulation API instead
 of running the simulation in-process.
- Add Level of Detail (LOD) handling (detailed versus coarse simulation) and bas
ic performance safeguards inside the simulation service.
- Create a headless driver (can run as a Kubernetes Job/Pod) to advance ticks an
d log key state changes for debugging.

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
  - Urban, industrial, and perimeter variables (pollution, emissions, biodiversi
ty, stability).
  - Local rules (growth, decay, diffusion) influenced by human activity.

### Phase 4 Execution Plan

- **M4.1 Agent AI (Deliverable: `systems/agents.py`)**

  - Expand YAML schema to capture needs/goals/memory slots; update validation sc
ript + fixtures.
  - Implement deterministic agent brain (utility model with seeded randomness) t
hat consumes `GameState` slices and emits intents (inspect, negotiate, deploy_re
source) recorded in a per-tick log.
  - Guarantee each tick surfaces at least one "strategic" action (inspect or neg
otiate) so CLI/service/headless outputs always include a high-signal agent beat.
  - Surface agent telemetry in headless summaries (`run_headless_sim.py`) to val
idate aggregate behavior.
  - Tests: unit tests for decision scoring, property tests for deterministic out
puts given identical seeds, CLI regression snapshot ensuring summaries reference
 new agent activity counts.

- **M4.2 Faction AI (Deliverable: `systems/factions.py`)**

  - Model faction resources/legitimacy deltas per tick and implement strategic a
ctions (lobby, recruit, sabotage, invest) with cooldowns.
  - Add conflict resolution layer so faction actions can transform agent/faction
 state and city modifiers.
  - Emit structured events for the CLI/service to surface (extend `/state?detail
=summary`) and feed telemetry via `faction_actions` counts/breakdowns.
  - Tests: scenario tests where a faction loses legitimacy after repeated unrest
, API contract tests ensuring `/metrics` reflects faction deltas, and validation
 that headless telemetry records faction behavior alongside agent intents.

- **M4.3 Economy Subsystem (Deliverable: `systems/economy.py`)**

  - Introduce production/consumption matrices per district resource, plus global
 market prices derived from supply/demand curves. **Status:** subsystem live wit
h district rebalancing, shortage counters, and CLI/service/telemetry surfacing o
f legitimacy + prices.
  - Wire conservation checks into tick loop to prevent negative stocks; raise wa
rnings when shortages persist N ticks.
  - Persist economic config knobs via the `economy` block inside `content/config
/simulation.yml` (regen scale, demand weights, shortage thresholds, price floors
/ceilings) so designers can retune without code changes.
  - Tests: expanded regression/property-style unit tests covering price floors/c
eilings, shortage-triggered price hikes, and long-run conservation. Scenario swe
eps remain on the backlog to complement the new fast unit coverage.

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

- **M4.5 Tick Orchestration & Telemetry (Deliverable: updated `SimEngine.advance
_ticks`)**
  - Define subsystem execution order (agents → factions → economy → enviro
nment → narrative hooks) with clear contracts and shared context objects.
  - Add OpenTelemetry-style trace hooks or structured logs capturing per-subsyst
em duration, errors, and key metrics; expose aggregates via `/metrics`.
  - Update headless driver summary to include subsystem durations and detected a
nomalies, enabling nightly sweeps.
  - Tests: integration suite running multi-tick scenarios ensuring subsystem ord
er is deterministic, coverage for telemetry payloads, and failure-path tests ver
ifying safeguards halt the tick with actionable errors.
  - Long-run soak: after adding mean-reversion to district modifiers and gating
sabotage so only low-legitimacy factions strike when stability is healthy, the b
aseline (`build/focus-baseline-1000tick.json`), profiling-history (`build/profil
ing-history-1000tick.json`), and soft-scarcity (`build/profiling-history-soft-sc
arcity-1000tick.json`) configs each cleared 1000 ticks with **0** `event_budget`
 anomalies. Baseline stability now bottoms out around **0.57** while the profili
ng-history and soft-scarcity variants remain at **1.0**, giving the narrator amp
le ranked inventory every tick.
  - Mitigation sweeps: keep the dedicated profiles under `content/config/sweeps/
` for targeted validation. The profiling-history variant (history window 240) of
fers a long rolling percentile reference, the soft-scarcity preset highlights ho
w low pressure plus reduced volatility keeps suppressed events under 300, and th
e high-budget profile (`.../profiling-history-high-budget/`) is still available
when you need to raise `lod.max_events_per_tick` for stress tests even though th
e baseline burn no longer requires it.
  - Introduce a phased plan for dynamic event budgets: short term, raise `lod.ma
x_events_per_tick` cautiously for regression sweeps; medium term (M4.6, now deli
vered) add a "focus manager" so the TickCoordinator grants higher per-tick budge
ts to the player’s focused district plus its neighbors while leaving a smaller
 global pool for the rest of the city. This keeps summaries legible as the world
 grows (more districts/agents/factions) and preserves anomaly tags as meaningful
 signals. Document the API surface (CLI `focus` command, service session focus)
and ensure telemetry exposes both global and focus-aware clamps.
    - Narrator integration: once the focus manager allocates beats deterministic
ally, the narrator layer can score every event by relevance (focus distance, sev
erity, novelty) and promote the top 3–5 into the player-facing digest while pu
shing the rest into an append-only history buffer in `state.metadata`. The CLI/g
ateway will surface the digest by default and expose `history` commands so teste
rs can browse suppressed beats after the fact.
    - Gameplay impact: exceeding ~100 `event_budget` anomalies per 1000 ticks me
ans ~20% of ticks lose at least one story beat before curation, so the narrator
cannot explain causality reliably. Likewise, the high-budget preset (20 events/t
ick) eliminates anomalies but crashes stability after ~350 ticks, producing repe
titive crisis beats that overwhelm the narrator. The focus-aware plan must there
fore (1) keep anomalies <100 without destabilizing the world and (2) give the na
rrator enough ranked inventory each tick to pick high-signal beats while archivi
ng the rest for later discovery.
    - Telemetry tasks: extend the profiling payload with `focus_budget` vs. `glo
bal_budget` counters plus `suppressed_events` per tick so QA can confirm the cur
ator is working even when the player only sees a handful of beats. Headless capt
ures should store both the digest (what the player saw) and the archival log so
we can diff narrative exposure over long soaks.
  - Status: the focus manager + CLI/service command now exist, TickCoordinator
    emits `focus_budget` payloads per tick, suppressed/archived events flow into
    metadata and headless telemetry (`last_event_digest`), config files gain a
    dedicated `focus` block (`default_district`, neighborhood sizing, budget
    ratio, digest/history lengths), narrator scoring ranks every event by
    severity + focus distance, and the CLI/gateway expose the ranked history.
    Current focus defaults keep anomalies <100 during 1000-tick soaks; future
    tuning will pair spatial weighting (M4.7) and narrative director hooks with
    the delivered curator.

### Dependencies & Tooling Notes

- Content updates for traits/factions/resources must land before subsystem code
to keep validation green.
- Reuse the newly added safeguards + headless driver for soak testing after each
 milestone; target ≥500 ticks per run without instability.
- Maintain ≥90% coverage for new modules; critical decision logic must hit 100
% where feasible.
- Document every milestone in README + gameplay guide once the corresponding sub
system becomes player-visible.

## 5. Narrative Director & Story Seeds

- Define a data format for story seeds (triggers, roles, stakes, resolution temp
lates) and load them from external files.
- Build the narrative director (as a logical module within the simulation servic
e, or a separate microservice if needed) that:
  - Monitors global metrics (stability, inequality, tech risk, environment, fact
ional polarization, player reputation).
  - Activates appropriate story seeds and attaches them to existing agents and f
actions.
  - Manages pacing so crises and quiet periods alternate.
- Implement outcome vignettes and a post-mortem generator that summarize causal
chains and final city state at campaign end.

## 6. CLI Gateway Service, ASCII Visualization, and LLM Intent Layer

- Implement a **CLI gateway service** that now ships as
  `gengine.echoes.gateway`:
  - FastAPI/WebSocket host with `/ws` + `/healthz`, provisioning an
    `EchoesShell` per session and proxying each command to the simulation
    service via `SimServiceClient` (default target `ECHOES_GATEWAY_SERVICE_URL`)
.
  - Streams rendered CLI output + `should_exit` flags back to clients that send
    JSON `{"command": "..."}` frames, enabling any WebSocket tooling (or the
    bundled `echoes-gateway-shell`) to replay the deterministic terminal
    experience.
  - Logs `focus` / `focus_digest` / `focus_history` snapshots via the
    `gengine.echoes.gateway` logger whenever players issue `summary`, `focus`,
    `history`, or `director` commands, creating an audit trail for remote QA.
  - Ships with regression tests (`tests/echoes/test_gateway_service.py`) that
    cover WebSocket round-trips and malformed payload handling, plus updated
    documentation (README + gameplay guide) describing the WebSocket contract
    and new console scripts (`echoes-gateway-service`, `echoes-gateway-shell`).
- Add ASCII rendering in the CLI gateway for city and district maps plus textual
 overlays:
  - District grids, control zones, and environmental heatmaps.
  - Tables for resources, faction influence, and key agents.
- Implement an **LLM service** that:
  - Parses free-form player input into structured intents mapped to the simulati
on action API.
  - Generates in-world text (dialogue, headlines, summaries) constrained by curr
ent state provided by the simulation service.
  - Can scale independently on Kubernetes (for example, with HPA based on latenc
y/QPS).
- Ensure the conversational flow is stateless or minimally stateful per session,
 with any persistent game state stored in the simulation service or backing stor
e.

## 7. Player Experience, Progression, and Polish

- Implement progression systems:
  - Skills (negotiation, investigation, systems hacking, logistics, stealth).
  - Access tiers (security clearance, new districts, deeper network layers).
  - Reputation profiles that affect NPC and faction responses.
- Add "why did this happen?" tools:
  - Event timelines, causal explanations, and agent reasoning summaries surfaced
 in the CLI.
- Tune pacing, difficulty, and replayability:
  - Different starting configurations and modifiers.
  - Story seed variety, activation thresholds, and frequency.
- Refine UX flows for campaigns, autosaves, end-of-run summaries, and post-morte
ms, ensuring service boundaries remain clear (for example, save/load handled by
simulation service, presentation handled by CLI gateway).

## 8. Cross-Cutting Concerns and Next Steps

- Define the Kubernetes deployment model:
  - Separate Deployments for simulation service, CLI gateway service, and LLM se
rvice.
  - Shared configuration via ConfigMaps and Secrets for environment, models, and
 content paths.
  - Service definitions (ClusterIP/Ingress) for inter-service communication and
external CLI access.
- Decide on LLM hosting or inference strategy (local model, remote API, or hybri
d) and acceptable latency budgets; encapsulate details in the LLM service so oth
er services remain decoupled.
- Align on target scale (number of agents, districts, and factions) to size the
simulation service resources and LOD heuristics.
- Establish content pipelines so designers can author and test YAML/world data a
nd story seeds quickly, ideally via a separate content-build step that produces
artifacts consumed by the simulation service.
- Once the core loop is robust, iterate on art direction for ASCII layouts and o
n narrative tone via seed and prompt tuning.
