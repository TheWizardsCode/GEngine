# Plan: Implement "Echoes of Emergence" (CLI + LLM Sim)

A staged implementation that builds a solid simulation core, then layers on agents and factions, narrative, and finally the CLI + LLM conversational interface with ASCII visualization. The runtime architecture is microservice-based and designed to run on Kubernetes from the outset. This plan is informed by and should be read alongside the game design document in `docs/simul/emergent_story_game_gdd.md`. Each phase should be testable in isolation via minimal scripts before integrating, with data-driven content and full save/load from the start.

## Progress Log (Updated 2025-11-27)

- ✅ Phase 1 (Foundations & Data Model): core models, YAML loader, snapshots, smoke tests.
- ✅ Phase 2 (Early CLI Shell & Tick Loop): in-process `echoes-shell` CLI with summary/next/run/map/save/load commands plus a deterministic tick engine.
- ⚙️ Phase 3 (Simulation Core & Service API): **M3.1 SimEngine abstraction
  landed**; CLI now routes through `SimEngine` while FastAPI service plus HTTP
  client remain in-flight.
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
  that simulate multi-day campaigns.
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
- **M3.2 FastAPI service** (1 day): expose `/tick`, `/state`, `/actions`, and
  `/metrics`; publish OpenAPI spec and add typed client in `src/echoes/client/`.
- **M3.3 CLI service mode** (1 day): allow CLI to target either in-process or
  HTTP client via config/env vars; add integration tests using FastAPI
  TestClient.
- **M3.4 LOD + safeguards** (1 day): cap loop iterations, add configs in
  `content/config/`, and emit metrics/logs for profiling.
- **M3.5 Headless driver** (0.5 day): script `scripts/run_headless_sim.py`
  advances ticks and logs diagnostics for regression tracking.

### Phase 4 – Agents, Factions, Economy, Environment

- **M4.1 Agent AI** (1-1.5 days): extend agent traits/goals and implement
  utility-based choices in `systems/agents.py` with reproducible seeds.
- **M4.2 Faction AI** (1-1.5 days): resources, ideology, legitimacy, territory
  plus strategic actions at lower cadence.
- **M4.3 Economy** (1-1.5 days): production/consumption, market price loop, and
  conservation tests to guard against runaway resource inflation.
- **M4.4 Environment** (1 day): pollution/emissions/biodiversity dynamics tied
  to economy + agent actions.
- **M4.5 Tick orchestration** (0.5-1 day): explicitly order subsystem updates,
  emit traces per subsystem, and run smoke scenarios via headless driver.

### Phase 5 – Narrative Director and Story Seeds

- **M5.1 Seed schema** (0.5 day): YAML format + validator under
  `content/worlds/<name>/story_seeds.yml`.
- **M5.2 Director core** (1-1.5 days): monitors metrics, activates seeds, logs
  timeline events.
- **M5.3 Pacing/resolution** (0.5-1 day): cooldowns, quiet periods, event
  lifecycle tracking so crises do not overlap chaotically.
- **M5.4 Post-mortem** (0.5 day): deterministic text summaries callable from
  CLI and gateway.

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
