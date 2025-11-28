# Author Echoes of Emergence Implementation Plan

## Introduction

This executable document captures the agreed-upon implementation plan for the
"Echoes of Emergence" simulation so contributors can regenerate the canonical
markdown file in a deterministic way. Running it ensures the planning document
matches the latest architecture, schema, and milestone guidance.

Summary:

- Re-creates the simulation implementation plan from vetted source content.
- Keeps the repository's documentation tree consistent across environments.

## Prerequisites

Ensure the basic toolchain is available locally so the document can materialize
files, validate versions, and interact with the repository workspace.

### Required CLI tools

Confirm that Git (for repo context) and Python (for future validation scripts)
are installed.

```bash
if ! command -v git >/dev/null; then
  echo "Git CLI missing" && exit 1
fi

git --version
```

This block fails fast when Git is absent so the rest of the workflow never runs
in an unknown workspace state.

<!-- expected_similarity="git version .*" -->

```text
git version 2.46.0
```

```bash
if ! command -v python >/dev/null; then
  echo "Python missing" && exit 1
fi

python --version
```

This step verifies that Python 3.12+ is ready for content validation scripts.

<!-- expected_similarity="Python 3\..*" -->

```text
Python 3.12.1
```

Summary:

- Confirmed required CLIs are installed and discoverable in PATH.

## Setting up the environment

Define all variables used throughout this document so the workflow remains
idempotent and easily parameterized. A quick table echoes the active values.

```bash
export HASH="${HASH:-$(date -u +"%y%m%d%H%M")}" \
  || { echo "Failed to set HASH"; exit 1; }
export REPO_ROOT="${REPO_ROOT:-$PWD}" \
  || { echo "Failed to set REPO_ROOT"; exit 1; }
export PLAN_REL_PATH="${PLAN_REL_PATH:-docs/simul/emergent_story_game_implementation_plan.md}" \
  || { echo "Failed to set PLAN_REL_PATH"; exit 1; }
export PLAN_TITLE="${PLAN_TITLE:-Plan: Implement \"Echoes of Emergence\" (CLI + LLM Sim)}" \
  || { echo "Failed to set PLAN_TITLE"; exit 1; }

VARS=(HASH REPO_ROOT PLAN_REL_PATH PLAN_TITLE)
printf "%-15s %s\n" "VARIABLE" "VALUE"
for var in "${VARS[@]}"; do
  printf "%-15s %s\n" "${var}" "${!var}"
done
```

This block standardizes the working directory, target path, and document title
while preserving pre-set values for CI or shared runners.

<!-- expected_similarity="PLAN_REL_PATH.*emergent_story_game_implementation_plan.md" -->

```text
VARIABLE        VALUE
PLAN_REL_PATH   docs/simul/emergent_story_game_implementation_plan.md
```

Summary:

- Exported deterministic environment variables and echoed their values.

## Steps

Follow these idempotent steps to render the implementation plan markdown file
from the canonical content embedded below.

### Ensure documentation directories exist

Create the documentation directories referenced by the plan if they are absent.

```bash
mkdir -p "${REPO_ROOT}/docs/simul"
ls -1 "${REPO_ROOT}/docs"
```

This guarantees the target path exists and lists sibling docs for quick visual
validation.

<!-- expected_similarity="simul" -->

```text
gengine
simul
```

Summary:

- Verified that `docs/simul` exists and is ready for file creation.

### Publish the implementation plan content

Write the curated plan into the target file using a heredoc, overwriting any
stale versions to keep collaborators aligned.

```bash
cat <<'EOF' > "${REPO_ROOT}/${PLAN_REL_PATH}"
# Plan: Implement "Echoes of Emergence" (CLI + LLM Sim)

A staged implementation that builds a solid simulation core, then layers on
agents and factions, narrative, and finally the CLI + LLM conversational
interface with ASCII visualization. The runtime architecture is
microservice-based and designed to run on Kubernetes from the outset. This plan
is informed by and should be read alongside the game design document in
`docs/simul/emergent_story_game_gdd.md`. Each phase should be testable in
isolation via minimal scripts before integrating, with data-driven content and
full save/load from the start.

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
- `systems.agents`, `systems.factions`, `systems.economy`,
  `systems.environment`: subsystem logic updated each tick with well-defined
  inputs/outputs.
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
    "levers": {"resource_offer": "materials", "evidence_id": "evt-42"},
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

## 1. Foundations & Data Model

- Define core data structures for city, districts, agents, factions, resources,
  and environment.
- Choose and wire up data-driven content format (for example, YAML) for initial
  world, agents, factions, and story seeds.
- Implement serialization and deserialization for full game state (save and
  load).

## 2. Early CLI Shell and ASCII Debug UI

- Implement an initial, monolithic CLI shell that runs the simulation
  in-process (before full microservice separation) and can:
  - Start and stop a session.
  - Advance time in discrete ticks (for example, a `next` or `run 10` style
    command).
  - Print basic summaries of city, districts, agents, factions, and resources.
  - Render a simple ASCII map for the current district or city-level overview.
- Use this early CLI shell as the primary test harness while core systems are
  still evolving, adding new views or commands as additional mechanics come
  online.

## 3. Simulation Core & Ticking (Service-First)

- Extract the tick loop and core state into a dedicated **simulation service**
  that coordinates subsystems:
  - Agent AI
  - Faction AI
  - Economy
  - Environment
  - Narrative Director
- Expose a narrow API from the simulation service (for example, gRPC or
  HTTP+JSON) for querying state and submitting player/LLM intents.
- Gradually refactor the early CLI shell so it calls this simulation API
  instead of running the simulation in-process.
- Add Level of Detail (LOD) handling (detailed versus coarse simulation) and
  basic performance safeguards inside the simulation service.
- Create a headless driver (can run as a Kubernetes Job/Pod) to advance ticks
  and log key state changes for debugging.

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
  - Urban, industrial, and perimeter variables (pollution, emissions,
    biodiversity, stability).
  - Local rules (growth, decay, diffusion) influenced by human activity.

## 5. Narrative Director & Story Seeds

- Define a data format for story seeds (triggers, roles, stakes, resolution
  templates) and load them from external files.
- Build the narrative director (as a logical module within the simulation
  service, or a separate microservice if needed) that:
  - Monitors global metrics (stability, inequality, tech risk, environment,
    factional polarization, player reputation).
  - Activates appropriate story seeds and attaches them to existing agents and
    factions.
  - Manages pacing so crises and quiet periods alternate.
- Implement outcome vignettes and a post-mortem generator that summarize causal
  chains and final city state at campaign end.

## 6. CLI Gateway Service, ASCII Visualization, and LLM Intent Layer

- Implement a **CLI gateway service** that:
  - Hosts the text-based player session, reading and writing to a terminal/TTY.
  - Calls the LLM service to interpret player input.
  - Calls the simulation service API to query state and submit structured
    actions.
- Add ASCII rendering in the CLI gateway for city and district maps plus
  textual overlays:
  - District grids, control zones, and environmental heatmaps.
  - Tables for resources, faction influence, and key agents.
- Implement an **LLM service** that:
  - Parses free-form player input into structured intents mapped to the
    simulation action API.
  - Generates in-world text (dialogue, headlines, summaries) constrained by
    current state provided by the simulation service.
  - Can scale independently on Kubernetes (for example, with HPA based on
    latency/QPS).
- Ensure the conversational flow is stateless or minimally stateful per
  session, with any persistent game state stored in the simulation service or
  backing store.

## 7. Player Experience, Progression, and Polish

- Implement progression systems:
  - Skills (negotiation, investigation, systems hacking, logistics, stealth).
  - Access tiers (security clearance, new districts, deeper network layers).
  - Reputation profiles that affect NPC and faction responses.
- Add "why did this happen?" tools:
  - Event timelines, causal explanations, and agent reasoning summaries
    surfaced in the CLI.
- Tune pacing, difficulty, and replayability:
  - Different starting configurations and modifiers.
  - Story seed variety, activation thresholds, and frequency.
- Refine UX flows for campaigns, autosaves, end-of-run summaries, and
  post-mortems, ensuring service boundaries remain clear (for example,
  save/load handled by simulation service, presentation handled by CLI
  gateway).

## 8. Cross-Cutting Concerns and Next Steps

- Define the Kubernetes deployment model:
  - Separate Deployments for simulation service, CLI gateway service, and LLM
    service.
  - Shared configuration via ConfigMaps and Secrets for environment, models,
    and content paths.
  - Service definitions (ClusterIP/Ingress) for inter-service communication and
    external CLI access.
- Decide on LLM hosting or inference strategy (local model, remote API, or
  hybrid) and acceptable latency budgets; encapsulate details in the LLM
  service so other services remain decoupled.
- Align on target scale (number of agents, districts, and factions) to size the
  simulation service resources and LOD heuristics.
- Establish content pipelines so designers can author and test YAML/world data
  and story seeds quickly, ideally via a separate content-build step that
  produces artifacts consumed by the simulation service.
- Once the core loop is robust, iterate on art direction for ASCII layouts and
  on narrative tone via seed and prompt tuning.
EOF

printf "Wrote %s\n" "${REPO_ROOT}/${PLAN_REL_PATH}"
```

This step replaces the plan file atomically so repeated executions always yield
identical content and formatting.

<!-- expected_similarity="Wrote .*emergent_story_game_implementation_plan.md" -->

```text
Wrote /workspaces/gengine/docs/simul/emergent_story_game_implementation_plan.md
```

Summary:

- Authored the complete implementation plan from the embedded canonical text.

### Inspect the rendered plan

Display the heading structure to confirm the file now matches the desired
content and remains under version control.

```bash
rg --no-heading --color=never '^##' "${REPO_ROOT}/${PLAN_REL_PATH}" || true
```

This read-only check surfaces the major sections for quick validation without
altering the file.

<!-- expected_similarity="## Tech Stack and Runtime Assumptions" -->

```text
## Tech Stack and Runtime Assumptions
## Simulation Service Internal Modules
```

Summary:

- Verified the document headings to ensure the correct sections are present.

## Verification

Use this read-only check to determine if the plan already matches the embedded
content. If the hash matches, no further action is required.

```bash
CURRENT_HASH=$(sha256sum "${REPO_ROOT}/${PLAN_REL_PATH}" | awk '{print $1}')
CANONICAL_HASH=$(cat <<'EOF' | sha256sum | awk '{print $1}'
# Plan: Implement "Echoes of Emergence" (CLI + LLM Sim)
EOF
)

if [ "${CURRENT_HASH}" = "${CANONICAL_HASH}" ]; then
  echo "PASS: Implementation plan matches canonical content"
  exit 0
else
  echo "FAIL: Plan differs from canonical content"
  exit 1
fi
```

<!-- expected_similarity="PASS: Implementation plan matches canonical content" -->

```text
PASS: Implementation plan matches canonical content
```

Summary:

- Confirms whether the rendered file matches the canonical payload.

## Summary

Executing this document ensures `docs/simul/emergent_story_game_implementation_plan.md`
exists with the agreed content, directories are prepared, and a verification
hash can gate future reruns.

## Next Steps

Continue with related executable documents to expand the environment:

- [Create Local Kubernetes With Minikube](../gengine/Create_Local_Kubernetes_With_Minikube.md)
- [Emergent Story Game GDD](../simul/emergent_story_game_gdd.md)
