# GEngine: Echoes of Emergence

A staged simulation project that prototypes the "Echoes of Emergence" CLI + LLM
experience. The long-term goal is a service-first architecture (simulation
service, CLI gateway, LLM intent service) designed for Kubernetes. This README
summarizes the current state of development and the immediate workflows you can
run locally.

## Current Status (Phases 1–4)

- Python 3.12 project skeleton managed via `uv` and packaged under
  `src/gengine`.
- Core domain models implemented with Pydantic (`City`, `District`, `Agent`,
  `Faction`, `EnvironmentState`, `GameState`).
- YAML-driven world content loader and JSON snapshot persistence with datetime
  serialization.
- Default world bundle in `content/worlds/default/world.yml` featuring three
  districts, two factions, and three agents.
- Simulation tick loop (`gengine.echoes.sim.advance_ticks`) that nudges
  resources, districts, and environment metrics each tick, now routed through
  the `SimEngine` abstraction for future service mode.
- `gengine.echoes.sim.SimEngine` centralizes `initialize_state`,
  `advance_ticks`, `query_view`, and placeholder `apply_action`, giving the
  CLI the same control surface the upcoming service layer will expose.
- FastAPI simulation service (`gengine.echoes.service.create_app`) exposing
  `/tick`, `/state`, `/metrics`, and `/actions`, plus a typed HTTP client in
  `gengine.echoes.client.SimServiceClient` for downstream tooling.
- CLI shell (`echoes-shell`) that runs the sim in-process, supports
  `summary`, `next`, `run`, `map`, `save`, and `load` commands, and can run in
  interactive or scripted mode. Pass `--rich` for enhanced ASCII views with
  styled tables, color-coded panels, and formatted overlays.
- Shared simulation config in `content/config/simulation.yml` that sets
  safeguards (CLI run cap, script limits, service tick cap), Level-of-Detail
  mode, profiling toggles, and an `economy` block that exposes regeneration,
  demand, and price knobs. `SimEngine` enforces the guardrails, and the
  economy subsystem reads the same file so designers can retune systems
  without touching code.
- Agent AI subsystem (Phase 4, M4.1) that evaluates authored agents each tick
  and emits utility-based intents (inspect districts, stabilize unrest,
  negotiate with factions). At least one reconnaissance/negotiation beat is
  forced into every tick so logs and telemetry always surface a strategic
  action. Summaries of these actions appear in tick logs,
  service responses, and headless regression outputs for easy inspection.
- Faction AI subsystem (Phase 4, M4.2) that models legitimacy/resources for
  authored factions, executes low-frequency strategic actions (lobby, recruit,
  invest, sabotage), and mutates district or faction state accordingly. These
  decisions are logged as structured `faction_actions` in tick reports,
  service responses, and telemetry captures.
- Economy subsystem (Phase 4, M4.3) that balances district production/
  consumption, tracks multi-tick shortages, updates a lightweight market price
  layer, and feeds the latest prices + shortage counters into tick reports,
  summaries, and telemetry. Faction legitimacy snapshots/deltas are surfaced
  alongside the market readout everywhere the reports appear so playtesters
  can connect systemic shifts to reported beats.
- Early environment plumbing (Phase 4, M4.4) that listens to economy
  shortages, diffuses extreme pollution pockets toward a citywide baseline,
  reacts to faction investments/sabotage with pollution relief/spikes, and now
  biases diffusion toward physically adjacent districts with configurable
  neighbor weight/min/max deltas. The loop also tracks a biodiversity gauge
  that falls under scarcity pressure, recovers toward a configurable baseline,
  and feeds stability through a tunable coupling so crashes surface in time.
  The subsystem captures the resulting `environment_impact` metadata (scarcity
  pressure, faction deltas, diffusion samples, biodiversity value/delta,
  stability effects, average pollution, and the latest max/min districts) for
  telemetry + CLI/service summaries.
- Focus-aware narrative budgeting (Phase 4, M4.6) with CLI/service `focus`
  commands, a deterministic digest/history, severity-distance ranking, and
  telemetry that records suppressed beats. Phase 4, M4.7 extends the same
  manager with spatial weighting so authored coordinates/adjacency graphs blend
  literal proximity with the population-ranked rings. The CLI summary now shows
  the blended scores, map overlays render coordinates + neighbor hints, and
  tick telemetry captures the combined weights for headless sweeps.
- Narrator-to-director bridge + narrative director scaffolding (Phase 4, M4.7)
  that captures each tick's ranked archive, suppressed counts, and spatial
  weights into a `director_feed` payload and then pipes it into the new
  `NarrativeDirector`. The director inspects hotspot severity, computes travel
  routes over the adjacency graph (hops, distances, travel time, reachability),
  and publishes a `director_analysis` block with hotspot previews and a
  recommended focus shift. The CLI `summary` + `director [count]` commands,
  service `/state?detail=summary`, and headless telemetry surface both the
  feed and the travel analysis so story-seed work can build atop deterministic
  mobility signals.
- Authored story seeds live in `content/worlds/<world>/story_seeds.yml` and are
  now loaded into `GameState.story_seeds`. Each director evaluation matches the
  seeds against the latest hotspots, caches the most recent payload for each
  seed, and records active matches (with `cooldown_remaining` +
  `last_trigger_tick`) inside the `story_seeds` metadata block plus the
  CLI/service/headless summaries. Whenever a seed fires, the director now emits
  a structured `director_events` entry that captures the tick, attached agents
  and factions, stakes, travel hint, and relevant resolution templates. The
  latest events persist in metadata (and show up in CLI summary, the
  `director` command, FastAPI `/state?detail=summary`, and headless telemetry)
  so designers can audit which beats triggered and why without digging through
  raw logs. The schema now requires explicit `stakes`, `resolution_templates`,
  optional `travel_hint`, and `followups`, and the content loader validates
  every referenced district, agent, faction, and followup id so malformed seeds
  are caught immediately during world import.
- Director pacing + lifecycle tracking (Phase 5, M5.3 prototype) adds
  configurable guardrails to the `NarrativeDirector`. Seeds now progress
  deterministically through `primed → active → resolving → archived`, with
  per-seed cooldowns, per-seed quiet timers, and a global quiet span that caps
  how many crises overlap. The CLI summary, FastAPI summaries, and headless
  telemetry each show a `director_pacing` block plus the latest lifecycle
  states so reviewers can see why a beat is blocked, how long a resolving arc
  has left, or when the director will reprime a seed after cooldown.
- Deterministic post-mortem generator (Phase 5, M5.4) stitches together the
  latest environment readings, trend deltas, faction legitimacy swings,
  director events, and story-seed lifecycle history into a shareable recap.
  The shell exposes it via the new `postmortem` command, the FastAPI service
  serves the same payload with `/state?detail=post-mortem`, and the headless
  driver now writes a `post_mortem` block into every telemetry artifact so QA
  can diff end-of-run summaries without rehydrating snapshots.
- Headless regression driver (`scripts/run_headless_sim.py`) that advances
  batches of ticks, emits per-batch diagnostics, and writes JSON summaries for
  automated sweeps or CI regressions. Summaries now include focus-budget
  telemetry (`last_event_digest`, suppressed counts, allocation stats) so QA
  can diff what players saw versus what was archived.
- Instrumented profiling that records per-tick durations (p50/p95/max),
  subsystem timing deltas, the slowest subsystem per tick, and anomaly tags
  (subsystem errors, event-budget hits) directly into `GameState.metadata`. The
  CLI summary, FastAPI `/metrics` response, and headless regression outputs all
  surface the same block so designers can spot runaway ticks without attaching
  a profiler. The profiling payload now also tracks focus-budget allocations
  and suppressed-event counts so reviewers can see whether anomaly pressure is
  coming from narrative volume or subsystem issues.
- Utility script `scripts/eoe_dump_state.py` for quick world inspection and
  snapshot exports.
- Test suite covering content loading, snapshot round-trip, tick behavior, and
  CLI scripts (`tests/echoes/`).

See `docs/simul/emergent_story_game_implementation_plan.md` for the full
multi-phase roadmap and `docs/gengine/how_to_play_echoes.md` for a gameplay guide.

## Progress Log (Updated 2025-12-01)

- ✅ **Phase 5 M5.3 – Pacing & lifecycle polish** shipped: deterministic
  lifecycle states with per-seed/global quiet timers now gate director overlap,
  CLI/service/headless surfaces show the new `director_pacing` +
  `story_seed_lifecycle` blocks, docs walk through the pacing knobs, and
  regression tests/telemetry guard the lifecycle history + cooldown math.
  through the CLI `postmortem` command, service `/state?detail=post-mortem`,
  and headless telemetry `post_mortem` block. The canonical
  `build/feature-m5-4-post-mortem.json` capture plus
  `jq '.post_mortem' ...` diff workflow is documented across README/GDD/how-to
  so reviewers can audit end-of-run deltas without replaying ticks.

- ✅ **Phase 6 M6.1 – Gateway service** shipped: `gengine.echoes.gateway`
  introduces a FastAPI/WebSocket host that proxies shell commands to the
  simulation service, logs focus/history payloads per session, exposes a
  `/ws` endpoint plus health checks, and ships with the
  `echoes-gateway-service` runner and `echoes-gateway-shell` client so remote
  reviewers can drive the sim without local access.
- ✅ **Phase 9 M9.1 – AI Player Observer** shipped: deterministic observer
  implementation at `src/gengine/ai_player/observer.py` connects via local
  `SimEngine` or remote `SimServiceClient`, advances ticks, analyzes stability
  trends and faction legitimacy swings, tracks story seed activations, and
  generates structured JSON reports with natural language commentary. The CLI
  runner at `scripts/run_ai_observer.py` supports configurable tick budgets,
  analysis intervals, and alert thresholds.
- ✅ **Phase 9 M9.2 – Rule-based action layer** shipped: AI actor at
  `src/gengine/ai_player/actor.py` wraps observer analysis with strategy-based
  action selection. Three strategies implemented (BALANCED, AGGRESSIVE,
  DIPLOMATIC) with configurable thresholds and action intervals. Actor submits
  intents via `SimEngine.apply_action` API and logs all decisions for telemetry
  replay. Regression tests validate 100-tick deterministic runs with AI
  interventions. Coverage at 94% for new modules.
- ✅ **Phase 9 M9.3 – LLM-enhanced decisions** shipped: `HybridStrategy` at
  `src/gengine/ai_player/strategies.py` routes routine decisions to rule-based
  logic and delegates complex choices (multiple stressed factions, critical
  stability, multiple story seeds) to the LLM service. Budget enforcement via
  `LLMStrategyConfig` prevents runaway costs with configurable `llm_call_budget`.
  Telemetry tracks `decision_source` ("rule" vs "llm"), call counts, latency,
  and fallback rates. Scenario tests compare rule-only vs hybrid behavior.
  46 new tests cover the hybrid strategy, LLM decision layer, and complexity
  evaluation. Coverage at 94% for AI player module.

## Repository Layout

```
content/                  Authored YAML worlds and (future) story seeds
scripts/                  Developer utilities (state dump, headless drivers, AI observer, ...)
src/gengine/ai_player/    AI Player testing/validation module
src/gengine/echoes/core   Data models and GameState container
src/gengine/echoes/sim    Tick loop and future subsystems
src/gengine/echoes/cli    CLI shell + helpers
tests/                    Pytest suites (content, tick loop, CLI shell, AI player)
```

## Prerequisites

- Python 3.12+
- `uv` (https://github.com/astral-sh/uv)
- Docker (for container workflows; e.g., Docker Desktop or Docker Engine)

## Setup

```bash
cd /home/rogardle/projects/gengine
uv sync --group dev
```

The first sync creates/updates `.venv` and installs runtime plus dev
dependencies.

## Docker / Container Setup

Task 8.1.1 adds official Docker support for the simulation, gateway, and LLM services. You only need Docker if you plan to run the stack via containers or use the container smoke tests.

- **Install Docker:**
  - Linux: `docker` and `docker compose` via your distro packages or https://docs.docker.com/engine/install/
  - macOS / Windows: Docker Desktop from https://www.docker.com/products/docker-desktop

- **Build and run containers:**

  ```bash
  # From the repo root
  docker compose up --build
  ```

  This starts:
  - simulation service on port 8000
  - gateway service on port 8100
  - LLM service on port 8001

- **Container smoke test (recommended):**

  ```bash
  bash scripts/smoke_test_containers.sh
  ```

  This script builds the images, brings up the stack with Docker Compose, polls `/healthz` for each service, and tears everything down when checks pass.

## Running Tests

```bash
uv run --group dev pytest
```

This runs the unit/integration tests for content loading, tick advancement, and
the CLI shell.

### Collecting Coverage

```bash
uv run --group dev pytest --cov=gengine --cov-report=term-missing
```

The command above enables `pytest-cov`, producing line-level coverage in the
terminal while reusing the same virtualenv/dev dependency group.

### Regression Telemetry

After every full pytest run, capture deterministic telemetry so reviewers can
diff agent/faction behavior over time:

```bash
uv run python scripts/run_headless_sim.py --world default --ticks 200 --lod balanced --seed 42 --output build/feature-m5-4-post-mortem.json
```

Archive `build/feature-m5-4-post-mortem.json` alongside the test results (commit
or attach in review) so the canonical seed/tick profile is always available for
comparison. The telemetry
now captures agent/faction breakdowns, per-faction legitimacy snapshots/deltas,
the `last_economy` block (price table + shortage counters), and
`last_director_analysis` (hotspot travel recommendations) for regression diffs.
The same JSON also embeds the `director_pacing` snapshot, the full
`story_seed_lifecycle` table, lifecycle history, and any active global quiet
timer so reviewers can diff cooldown math between builds without reproducing
ticks locally.
Every telemetry file now also includes a `post_mortem` block that mirrors the
CLI/service recap: environment start/end/delta, the top faction legitimacy
swings, the last few director events, a ranked story-seed recap, and the
generated post-mortem notes so endgame comparisons never require loading the
snapshot back into the sim.
To diff the post-mortem recap between runs, compare the `post_mortem` object in
two artifacts directly (for example,
`jq '.post_mortem' build/feature-m5-4-post-mortem.json`).
Use `summary` on any saved snapshot to inspect the last tick's
`environment_impact` block when diagnosing pollution swings or to review the
director's recommended focus hand-offs.

### Scenario Sweeps

- For environment tuning, dedicated config variants live under
  `content/config/sweeps/`. Example commands that match the Phase 4
  biodiversity close-out captures:

  ```bash
  uv run python scripts/run_headless_sim.py --world default --ticks 400 --lod balanced --seed 42 --config-root content/config/sweeps/high-pressure --output build/feature-m4-7-biodiversity-high-pressure.json
  uv run python scripts/run_headless_sim.py --world default --ticks 400 --lod balanced --seed 42 --config-root content/config/sweeps/cushioned --output build/feature-m4-7-biodiversity-cushioned.json
  uv run python scripts/run_headless_sim.py --world default --ticks 400 --lod balanced --seed 42 --config-root content/config/sweeps/profiling-history --output build/feature-m4-7-biodiversity-profiling-history.json
  ```

- The high-pressure profile intentionally stress-tests scarcity by increasing
  pressure/diffusion weights, while the cushioned profile keeps pollution in
  check for longer playtests. The profiling-history profile leaves the economy
  and environment knobs alone but expands `profiling.history_window` to 240
  ticks so you can compare how longer rolling windows smooth the tick-duration
  percentiles and subsystem timings. Compare their telemetry outputs to map
  safe ranges before promoting new environment or profiling tweaks. While
  reviewing the JSON summaries, watch `environment_impact.biodiversity` and the
  `stability_effects` block to ensure the new eco-health signal stays above the
  alert threshold you configured.
- For anomaly-budget investigations, run a longer soak against the profiling-
  history config (history window 240) to see how safeguards behave deep into a
  burn:

  ```bash
  uv run python scripts/run_headless_sim.py --world default --ticks 1000 --lod balanced --seed 42 --config-root content/config/sweeps/profiling-history --output build/profiling-history-1000tick.json
  ```

  The latest baseline burn (`build/focus-baseline-1000tick.json`) surfaced **0**
  anomalies and held stability above **0.56** through tick 1000 thanks to the new
  faction gating and mean-reverting district modifiers, so the focus-aware
  curator can now rank a full digest without losing signal during long burns.

- Two mitigation-oriented presets now live under
  `content/config/sweeps/profiling-history-high-budget/` (higher
  `max_events_per_tick`) and `content/config/sweeps/profiling-history-soft-scarcity/`
  (reduced scarcity pressure/weights). Example commands:

  ```bash
  uv run python scripts/run_headless_sim.py --world default --ticks 1000 --lod balanced --seed 42 --config-root content/config/sweeps/profiling-history-high-budget --output build/profiling-history-high-budget-1000tick.json
  uv run python scripts/run_headless_sim.py --world default --ticks 1000 --lod balanced --seed 42 --config-root content/config/sweeps/profiling-history-soft-scarcity --output build/profiling-history-soft-scarcity-1000tick.json
  ```

  Both mitigation presets now double as validation anchors: the profiling-history
  variant (history window 240) finished 1000 ticks with **0** anomalies and
  stability pinned at **1.0**, while the soft-scarcity configuration (regen boost
  plus pressure damping) also logged **0** anomalies with stability pegged at
  **1.0** and fewer than 300 suppressed events. Use these captures to compare
  focus-budget allocations across different scarcity curves without touching the
  baseline config, and keep the high-budget preset handy if you ever need to
  raise `max_events_per_tick` for stress tests.

### Plotting Environment Trajectories

Once the cushioned, high-pressure, and profiling-history sweeps are captured you
can visualize their pollution/unrest curves with
`scripts/plot_environment_trajectories.py`. The script reads the
`director_history` entries embedded in each telemetry file, so bump
`focus.history_length` high enough (≥ the tick budget you plan to run) before
capturing if you need a full-length timeline instead of the latest window.

```bash
uv run python scripts/plot_environment_trajectories.py --output build/feature-m4-7-biodiversity-trajectories.png
```

- By default, the script looks for the three Phase 4 deepening sweep files under
  `build/feature-m4-7-biodiversity-*.json`. Pass `--run label=/path/to/file`
  multiple times to compare other telemetry captures.
- Omit `--output` to open an interactive window; specify it (as above) to save a
  PNG under `build/` for sharing in reviews.
- If a run only shows a couple of samples, regenerate telemetry with a larger
  `focus.history_length` so the director history covers the desired span.

## Inspecting the Default World

```bash
uv run python scripts/eoe_dump_state.py --world default --export build/default.json
```

The script prints a summary (city, ticks, counts) and optionally writes a JSON
snapshot for downstream tools.

## Running the CLI Shell

Interactive mode:

```bash
uv run echoes-shell --world default
```

**Enhanced ASCII Views** (tables, colors, panels):

```bash
uv run echoes-shell --world default --rich
```

The `--rich` flag enables enhanced formatting using the Rich library, providing:

- Styled tables for world status and performance metrics
- Color-coded panels for environment impact and focus state
- Formatted story seed and director event displays
- Better visual hierarchy and readability

- To target a running FastAPI simulation service, supply
  `--service-url http://localhost:8000`. When this flag is set the CLI routes
  through HTTP using `SimServiceClient`; `load world`/`load snapshot` will emit
  guidance because content swaps must happen server-side.
- To connect through the new gateway service instead of hitting the simulation
  service directly, run `uv run echoes-gateway-shell --gateway-url
ws://localhost:8100/ws` (pass `--script` for non-interactive workflows). The
  gateway client speaks the same WebSocket protocol that other tools can use by
  sending JSON messages with a `command` field.

Scripted mode (useful for CI/tests):

```bash
uv run echoes-shell --world default --script "summary;run 3;map;save build/state.json;exit"
```

Both modes share the same in-process GameState and emit ASCII summaries/maps for
rapid iteration.

Available in-shell commands:

- `help` – list commands and syntax.
- `summary` – show city, tick, counts, stability, faction legitimacy, latest
  market prices, the `environment_impact` block (now showing average pollution,
  extremal districts, the top diffusion samples, and the biodiversity snapshot
  with scarcity/recovery deltas plus the stability feedback it triggered), and
  the profiling payload (tick ms p50/p95/max, last subsystem timings, the
  slowest subsystem, and any anomaly tags) so you can gauge systemic pressure
  before advancing time again. The summary also surfaces the current focus
  configuration plus the last digest (up to 6 curated events), a suppressed
  count, and a severity-ranked preview of archived beats so you know exactly
  which stories were deferred by the focus manager that tick. When the
  narrative director matches authored story seeds, the summary prints a `story
seeds` block that lists which seeds attached, their target districts, and why
  they fired, mirroring the headless/service summaries for quick debugging. A
  neighboring `director pacing` block shows how many seeds are active versus
  resolving, how long remains on the global quiet timer, and which pacing
  guardrails blocked new matches, while the augmented seed entries include
  lifecycle states (`primed/active/resolving/archived`) plus their remaining
  durations and cooldowns.
  A neighboring `director events` block highlights the latest seeds that
  actually triggered, including their stakes and the first matching
  agent/faction so you can see who is on-stage without rerunning ticks.
- `next` – advance exactly one tick with the inline report (no arguments). Use
  `run` for batches.
- `run <n>` – advance `n` ticks (must be provided) and show the combined report.
  The CLI enforces the safeguard defined in `limits.cli_run_cap` (default 50).
- `map [district_id]` – render an ASCII table of all districts (includes an "ID"
  column) followed by a geometry overlay listing each district's coordinates
  and neighbor list. Provide a district id to see detailed modifiers plus the
  same coordinates/adjacency hints for that location.
- `focus [district|clear]` – display or update the active focus ring that the
  narrator budget prioritizes. Selecting a district allocates more per-tick
  event slots to that district and its top neighbors, while `focus clear`
  resets to the default rotation.
- `history [count]` – print the ranked narrator history captured over recent
  ticks (latest first). Each entry shows the focus center, suppressed count,
  and the top scored archived beats so testers can review what the curator
  held back during long burns. Provide an optional count to limit the tail.
- `postmortem` – dump a deterministic recap of the latest run. The output
  lists environment trend deltas, the three largest faction legitimacy swings,
  the last director events, and the most recent story seed outcomes so QA can
  grab an end-of-run epilogue without exporting the entire snapshot. It pulls
  from the same metadata surfaced via FastAPI `/state?detail=post-mortem` and
  headless telemetry.
- `timeline [count]` – show recent causal events in the simulation. Each tick
  entry lists key changes (stability shifts, faction actions, story seed
  activations) along with agent reasoning summaries so testers can trace
  what happened and why. This is part of the M7.2 explanations system.
- `explain <type> <id>` – query detailed explanations for a specific entity.
  Types include `faction`, `agent`, `district`, and `metric`. For example:
  - `explain faction union-of-flux` shows legitimacy trend, recent actions
  - `explain agent agent-1` shows reasoning factors, needs, goals
  - `explain district industrial-tier` shows modifiers, faction activity
  - `explain metric stability` shows contributing causes and delta history
- `why <query>` – answer a natural language style query about the simulation.
  Examples: `why stability`, `why did unrest rise`, `why union-of-flux`.
  The system searches for matching entities/metrics and returns causal
  explanations including contributing factors and recent events.
- `save <path>` – write the current snapshot as JSON.
- `load world <name>` / `load snapshot <path>` – swap to a new authored world or
  on-disk snapshot (local engine mode only).
- `campaign list` – list all saved campaigns with IDs, names, and status.
- `campaign new <name> [world]` – create a new campaign and initialize the world.
- `campaign resume <id>` – resume a saved campaign by its ID.
- `campaign end` – end the active campaign with a post-mortem summary.
- `campaign status` – show details about the currently active campaign.
- `exit`/`quit` – leave the shell.
- Tick reports now include agent activity lines such as "Aria Volt inspects
  Industrial Tier" plus faction beats like "Union of Flux invests in
  Industrial Tier", making it easier to follow systemic reactions. Below the
  environment summary you will also see a "faction legitimacy" block (top ±3
  deltas each tick) and a `market -> energy:1.05, food:0.98, …` line whenever
  the economy subsystem has published prices. Any subsystem anomalies (errors
  or event-budget clamps) are listed per tick so you can correlate warnings
  with the profiling block. Focus-budget stats also print per tick, showing how
  many curated events were delivered to the focus ring versus the global pool
  and how many were archived for the history log.
- `summary` now renders the latest `environment_impact` snapshot, the shared
  profiling block, and the focus digest preview. Together they show scarcity
  pressure, whether diffusion fired, pollution shifts from faction activity,
  tick-duration percentiles, the slowest subsystems, anomaly tags, and the
  slices of the narrative that were prioritized for the current focus ring.

If scripted sequences exceed `limits.cli_script_command_cap` (default 200) the
shell halts automatically and prints a safeguard warning so runaway loops do
not wedge CI runs.

## Simulation Config and Safeguards

- Configuration lives in `content/config/simulation.yml`. Override the folder by
  setting `ECHOES_CONFIG_ROOT=/path/to/configs` before running any tools.
- `limits`: controls `engine_max_ticks` (hard stop inside `SimEngine`),
  `cli_run_cap`, `cli_script_command_cap`, and the service-facing
  `service_tick_cap` (default 100). Exceeding a limit produces a friendly
  error/warning rather than stalling the process.
- `lod`: selects `detailed`, `balanced` (default), or `coarse` modes. Each mode
  tweaks volatility in the tick loop and caps the number of events emitted per
  tick to keep logs legible during long burns.
- `profiling`: controls tick logging plus the shared percentile window.
  `history_window` sets how many tick durations feed the rolling p50/p95/max
  calculations, `capture_subsystems` toggles per-system timing, and `log_ticks`
  still emits the logger message. The resulting profiling block appears in the
  CLI summary, FastAPI `/metrics`, and headless telemetry JSON so you can spot
  regressions without attaching a debugger.
- `focus`: declares the default focus center, how many neighbors should share
  its budget, the ratio reserved for the focus ring, the global floor, digest
  size, history length, suppressed preview size, and the new spatial weighting
  knobs (`spatial_population_weight`, `spatial_distance_weight`,
  `adjacency_bonus`, `spatial_falloff`). Adjust these values to tighten or
  loosen the narrator's per-tick budget and proximity bias without editing
  code; the CLI/service focus and history commands immediately reflect the
  updated defaults after a restart.
- `director`: tunes hotspot filtering (limit + score threshold), travel timing,
  story seed surfacing limits, and the pacing knobs (`max_active_seeds`,
  `global_quiet_ticks`, `seed_active_ticks`, `seed_resolve_ticks`,
  `seed_quiet_ticks`, `lifecycle_history_limit`) that govern the lifecycle
  state machine. Adjust these to dial how many crises can overlap, how long a
  seed stays active/resolving, and how noisy the lifecycle history should be in
  CLI/service/headless summaries.
- `economy`: exposes `regen_scale`, demand weights, shortage thresholds, base
  resource weights, and price tuning values (`base_price`, `price_increase_step`,
  `price_max_boost`, `price_decay`, `price_floor`). Adjust these numbers to
  explore different scarcity curves; the CLI, FastAPI service, and telemetry
  will immediately reflect the new market behavior after a restart or config
  reload.
- `environment`: couples scarcity pressure into unrest/pollution/stability via
  weights such as `scarcity_unrest_weight` and the district-level deltas. Tweak
  these values to control how sharply shortages erode stability or spike
  pollution; the EnvironmentSystem writes every tick's `environment_impact`
  block into metadata so telemetry and CLI summaries can trace the effect. The
  same block reports whether diffusion ran in the last tick, which districts
  hit the max/min pollution extremes, the blended neighbor/global target, and
  how faction investments/sabotage adjusted local pollution via the
  `faction_invest_pollution_relief` and `faction_sabotage_pollution_spike`
  knobs. New biodiversity settings—`biodiversity_baseline`,
  `biodiversity_recovery_rate`, `scarcity_biodiversity_weight`,
  `biodiversity_stability_weight`, `biodiversity_stability_midpoint`, and the
  `biodiversity_alert_threshold`—let you tune how quickly ecosystems erode,
  rebound, and start dragging stability down when neglected. The new
  `diffusion_neighbor_bias`, `diffusion_min_delta`, and `diffusion_max_delta`
  settings expose how aggressively pollution equalizes between adjacent
  districts versus the citywide mean.

Edit the YAML, rerun the CLI/service, and the new safeguards apply immediately
without code changes.

### Guardrail Regression Matrix

| Surface                    | Config knob                     | Enforcement path                                          | Regression coverage                                                              |
| -------------------------- | ------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `SimEngine.advance_ticks`  | `limits.engine_max_ticks`       | Raises `ValueError` when a request exceeds the engine cap | `tests/echoes/test_tick.py::test_engine_enforces_tick_limit`                     |
| CLI `run <n>` command      | `limits.cli_run_cap`            | Output is prefixed with a safeguard warning and capped    | `tests/echoes/test_cli_shell.py::test_shell_run_command_is_clamped`              |
| CLI scripted sequences     | `limits.cli_script_command_cap` | Script halts once the command budget is consumed          | `tests/echoes/test_cli_shell.py::test_run_commands_respects_script_cap`          |
| FastAPI `/tick` endpoint   | `limits.service_tick_cap`       | Returns HTTP 400 detailing the configured limit           | `tests/echoes/test_service_api.py::test_tick_endpoint_rejects_large_requests`    |
| Headless regression driver | `limits.engine_max_ticks`       | Automatically chunks batches so no call exceeds the cap   | `tests/scripts/test_run_headless_sim.py::test_run_headless_sim_supports_batches` |

Run these tests (or the equivalent CLI/service commands) whenever knobs change
to keep safeguard behavior reproducible across environments.

## Running the Simulation Service

The FastAPI service wraps the same `SimEngine` interface and is the next step
toward remote clients and the CLI gateway.

```bash
uv run python -m gengine.echoes.service.main
```

Environment variables:

- `ECHOES_SERVICE_HOST` – bind address (default `0.0.0.0`).
- `ECHOES_SERVICE_PORT` – port (default `8000`).
- `ECHOES_SERVICE_WORLD` – world name to load at startup (default `default`).
- `ECHOES_CONFIG_ROOT` – optional root for `simulation.yml` when deploying with
  external configuration management.

You can integrate with the API using the bundled client:

```python
from gengine.echoes.client import SimServiceClient

with SimServiceClient("http://localhost:8000") as client:
  client.tick(5)
  summary = client.state("summary")
  focus_payload = client.focus_state()  # {"focus": {...}, "digest": {...}, "history": [...]}
  client.set_focus("industrial-tier")
  post_mortem = client.state("post-mortem")  # deterministic recap for LLM/export flows
```

Or, run the CLI shell against the service without restarting:

```bash
uv run echoes-shell --service-url http://localhost:8000 --script "summary;run 5;map;exit"

Use `detail=post-mortem` whenever you need the deterministic recap JSON (same
payload as the CLI `postmortem` command and headless telemetry `post_mortem`
block). The response pairs the metadata with the current tick so downstream
tools can archive end-of-run notes without replaying ticks.
```

## Gateway Service

Phase 6 M6.1 adds a WebSocket gateway that hosts remote CLI sessions and
proxies every command to the FastAPI simulation service via
`SimServiceClient`. Launch it with:

```bash
uv run echoes-gateway-service
```

Environment variables:

- `ECHOES_GATEWAY_SERVICE_URL` – base URL for the simulation service the
  gateway should proxy to (default `http://localhost:8000`).
- `ECHOES_GATEWAY_HOST` / `ECHOES_GATEWAY_PORT` – bind settings for the
  gateway itself (default `0.0.0.0:8100`).

The gateway exposes `/healthz` plus a `/ws` endpoint. Each WebSocket session
creates a dedicated `ServiceBackend` + `EchoesShell`, logs a welcome summary,
and records focus/digest/history telemetry to the `gengine.echoes.gateway`
logger every time a client runs `summary`, `focus`, `history`, or `director`.
Clients send JSON messages like `{"command": "summary"}` and receive the
rendered shell output plus a `should_exit` flag mirroring the local CLI.

You can interact with the gateway using the bundled client:

```bash
uv run echoes-gateway-shell --gateway-url ws://localhost:8100/ws --script "summary;run 3;exit"
```

The client prints the same ASCII output as `echoes-shell`, making it easy to
drive a remote sim session without SSH access. Any WebSocket tool can connect
as long as it sends UTF-8 JSON with a `command` field.

### Gateway-LLM Integration (Phase 6 M6.5)

The gateway now supports natural language commands through integration with the LLM service:

```bash
# Configure gateway to use LLM service
export ECHOES_GATEWAY_LLM_URL=http://localhost:8001
uv run echoes-gateway-service
```

When configured, the gateway enhances WebSocket messages with natural language processing:

**Enhanced WebSocket Protocol:**
```json
{"command": "show me unrest in the industrial district", "natural_language": true}
```

The gateway:
1. Builds context from current simulation state (tick, district, recent events)
2. Calls LLM service `/parse_intent` to convert text to structured GameIntent
3. Maps intent to shell command using IntentMapper
4. Executes command through EchoesShell
5. Optionally narrates result using `/narrate` endpoint
6. Returns formatted output to client

**Fallback Behavior:**
- If LLM service is unavailable, falls back to keyword-based command matching
- Regular commands (without `natural_language: true`) work as before
- All commands track conversation history for context

The integration uses HTTP retry logic (2 retries by default) and handles LLM service health checks on session creation. This enables conversational gameplay where players use natural language instead of memorizing CLI commands.

## Headless Regression Driver

`scripts/run_headless_sim.py` advances long simulations without interactive
input. It chunks work to respect `limits.engine_max_ticks`, prints per-batch
diagnostics to stderr, and writes a JSON summary that downstream tools can
diff. The JSON mirrors the CLI/service profiling block (tick percentiles,
slowest subsystem, anomaly tags) and now captures per-batch `tick_ms`,
slowest-subsystem snapshots, and anomaly lists so nightly sweeps surface
performance spikes immediately.

```bash
uv run python scripts/run_headless_sim.py --world default --ticks 500 --lod coarse --output build/headless.json
```

Key flags:

- `--ticks/-t`: total ticks to run (chunked automatically).
- `--lod`: override `simulation.yml` LOD mode (`detailed|balanced|coarse`).
- `--seed`: deterministic runs for regression capture.
- `--snapshot`: start from a saved snapshot instead of content.
- `--config-root`: point at an alternate config folder (useful in CI).
- `--output`: path for the structured summary (includes tick counts, timing
  percentiles, LOD mode, agent/faction action breakdowns, faction legitimacy
  snapshot, anomaly totals/examples, the last economy report, the shared
  profiling block with subsystem timings + slowest/anomaly metadata, and the
  `last_event_digest` payload that documents which events were shown, which
  were archived, how the focus budget was allocated, and the severity-ranked
  archive used by the narrator, plus the new `post_mortem` recap that mirrors
  the CLI/service `postmortem` output).

## AI Player Observer

The AI Player Observer (`src/gengine/ai_player/observer.py`) is a testing and
validation tool that programmatically analyzes simulation dynamics. It connects
via `SimServiceClient` (remote) or local `SimEngine`, advances ticks, and
generates structured reports on:

- **Stability trends**: Tracks overall city stability with configurable alert
  thresholds
- **Faction legitimacy swings**: Monitors faction influence changes and flags
  significant shifts
- **Story seed activations**: Records which narrative seeds trigger during
  observation

### Running the AI Observer

Basic observation with JSON output:

```bash
uv run python scripts/run_ai_observer.py --world default --ticks 100 --output build/observation.json
```

Verbose mode with natural language commentary:

```bash
uv run python scripts/run_ai_observer.py --world default --ticks 50 --verbose
```

Connect to a running simulation service:

```bash
uv run python scripts/run_ai_observer.py --service-url http://localhost:8000 --ticks 50
```

### Observer Configuration

Key flags:

- `--ticks/-t`: Number of ticks to observe (default: 100)
- `--analysis-interval`: Ticks between state snapshots (default: 10)
- `--stability-threshold`: Alert when stability drops below this (default: 0.5)
- `--legitimacy-threshold`: Alert when faction swings exceed this (default: 0.1)
- `--output/-o`: Path to write JSON report
- `--verbose/-v`: Print natural language commentary

### Programmatic Usage

**Local SimEngine mode:**

```python
from gengine.ai_player import Observer, ObserverConfig
from gengine.ai_player.observer import create_observer_from_engine

# Create observer with custom config
config = ObserverConfig(
    tick_budget=50,
    analysis_interval=10,
    stability_alert_threshold=0.5,
)
observer = create_observer_from_engine(world="default", config=config)
report = observer.observe()

# Access structured analysis
print(report.stability_trend.to_dict())
print(report.commentary)
```

**Remote SimServiceClient mode:**

```python
from gengine.ai_player import Observer, ObserverConfig
from gengine.ai_player.observer import create_observer_from_service

# Connect to a running simulation service
observer = create_observer_from_service(
    base_url="http://localhost:8000",
    config=ObserverConfig(
        tick_budget=100,
        analysis_interval=10,
        stability_alert_threshold=0.6,
        legitimacy_swing_threshold=0.15,
    )
)

try:
    report = observer.observe()
    
    # Check for critical alerts
    if report.alerts:
        print("ALERTS:", report.alerts)
    
    # Examine trend detection results
    print(f"Stability: {report.stability_trend.trend}")
    print(f"  Start: {report.stability_trend.start_value:.3f}")
    print(f"  End: {report.stability_trend.end_value:.3f}")
    
    # Review faction dynamics
    for faction_id, trend in report.faction_swings.items():
        if trend.alert:
            print(f"Faction swing detected: {trend.alert}")
    
    # Get structured JSON output
    import json
    print(json.dumps(report.to_dict(), indent=2))
finally:
    # Always close the client when done
    observer._client.close()
```

The Observer output includes:

- `stability_trend`: Start/end values, delta, trend direction, alert status
- `faction_swings`: Per-faction legitimacy changes with swing detection
- `story_seeds_activated`: List of triggered narrative seeds with tick numbers
- `alerts`: Critical warnings (e.g., stability crash)
- `commentary`: Natural language summary of the observation period
- `environment_summary`: Final environment metrics (stability, economy, agents)

## AI Player Actor (Phase 9 M9.2)

The AI Player Actor (`src/gengine/ai_player/actor.py`) extends the Observer with
rule-based action selection and submission. It uses configurable strategies to
autonomously interact with the simulation for automated testing and balance
validation.

### Strategies

Four built-in strategies are available:

- **BALANCED**: Moderate intervention, stabilizes at 0.6, supports factions at 0.4
- **AGGRESSIVE**: Frequent actions, higher thresholds, larger resource deployments
- **DIPLOMATIC**: Prefers negotiation, builds faction relationships, lower intervention thresholds
- **HYBRID**: Combines rule-based and LLM-enhanced decisions with budget controls

### Running the AI Actor

**Basic local mode:**

```python
from gengine.ai_player import AIActor, ActorConfig
from gengine.ai_player.strategies import StrategyType

from gengine.echoes.sim import SimEngine

engine = SimEngine()
engine.initialize_state(world="default")

config = ActorConfig(
    strategy_type=StrategyType.BALANCED,
    tick_budget=100,
    actions_per_observation=1,
)
actor = AIActor(engine=engine, config=config)
report = actor.run()

print(f"Actions taken: {report.actions_taken}")
print(f"Final stability: {report.final_stability}")
print(f"Telemetry: {report.telemetry}")
```

**With custom strategy:**

```python
from gengine.ai_player import AIActor
from gengine.ai_player.strategies import AggressiveStrategy, StrategyConfig

strategy = AggressiveStrategy(
    session_id="test-session",
    config=StrategyConfig(
        stability_low=0.75,
        action_interval=3,
    ),
)
actor = AIActor(engine=engine, strategy=strategy)
report = actor.run(ticks=50)
```

### Hybrid Strategy (LLM-Enhanced Decisions)

The **HYBRID** strategy combines rule-based heuristics with LLM-enhanced decisions
for complex situations. It routes routine decisions to fast rule-based logic and
delegates complex choices to the LLM service.

**Complex situations that trigger LLM:**
- Multiple factions with low legitimacy (< 0.4)
- Critical stability crisis (< 0.5)
- Multiple active story seeds
- Large legitimacy spread between factions

**Budget controls prevent runaway costs:**
- Configurable `llm_call_budget` limits total LLM calls per session
- Falls back to rules when budget exhausted
- Tracks estimated costs and latency

```python
from gengine.ai_player import AIActor, ActorConfig, HybridStrategy, LLMStrategyConfig
from gengine.echoes.sim import SimEngine

engine = SimEngine()
engine.initialize_state(world="default")

# Configure LLM budget and complexity thresholds
llm_config = LLMStrategyConfig(
    llm_call_budget=10,  # Max 10 LLM calls per session
    complexity_threshold_stability=0.5,  # Trigger LLM below this stability
    complexity_threshold_factions=2,  # Trigger if >= 2 stressed factions
    cost_per_call_estimate=0.01,  # Track estimated costs
)

# Create hybrid strategy
hybrid = HybridStrategy(
    session_id="hybrid-test",
    llm_config=llm_config,
)

# Run actor with hybrid strategy
config = ActorConfig(tick_budget=100)
actor = AIActor(engine=engine, config=config, strategy=hybrid)
report = actor.run()

# Check hybrid-specific telemetry
print(f"Rule decisions: {hybrid.telemetry['rule_decisions']}")
print(f"LLM decisions: {hybrid.telemetry['llm_decisions']}")
print(f"LLM calls used: {hybrid.llm_budget.calls_used}")
print(f"Estimated cost: ${hybrid.llm_budget.estimated_cost:.4f}")
```

**Decision source tracking:**

Every `StrategyDecision` now includes a `decision_source` field indicating
whether it came from rules ("rule") or LLM ("llm"). This enables telemetry
analysis comparing rule-only vs hybrid behavior.

```python
decisions = hybrid.evaluate(state, tick)
for d in decisions:
    print(f"{d.intent.intent.value}: source={d.decision_source}")
```

### Actor Configuration

- `strategy_type`: Which strategy to use (BALANCED, AGGRESSIVE, DIPLOMATIC, HYBRID)
- `tick_budget`: Total ticks to run (default: 100)
- `actions_per_observation`: Max actions per analysis interval (default: 1)
- `analysis_interval`: Ticks between strategy evaluations (default: 10)
- `log_decisions`: Enable decision logging (default: True)

### Strategy Customization

Custom strategies can be created by subclassing `BaseStrategy`:

```python
from gengine.ai_player.strategies import BaseStrategy, StrategyDecision, StrategyType

class CustomStrategy(BaseStrategy):
    strategy_type = StrategyType.BALANCED  # or create your own

    def evaluate(self, state: dict, tick: int) -> list[StrategyDecision]:
        decisions = []
        stability = state.get("stability", 1.0)
        
        if stability < 0.5:
            # Create and return decisions based on your rules
            pass
        
        return sorted(decisions, key=lambda d: d.priority, reverse=True)
```

### Telemetry Output

The actor report includes:

- `ticks_run`: Total ticks executed
- `actions_taken`: Number of actions submitted
- `decisions`: Full list of strategy decisions with rationales and decision_source
- `receipts`: Action submission receipts with status
- `final_stability`: City stability at end of session
- `telemetry`: Action counts, priority stats, rationales

For hybrid strategies, additional telemetry is available via `strategy.telemetry`:
- `rule_decisions`: Count of rule-based decisions
- `llm_decisions`: Count of LLM-based decisions
- `llm_budget`: Budget tracking (calls_used, estimated_cost, fallback_count)

## LLM Service (Phase 6 M6.3)

The LLM service provides natural language processing for intent parsing and narrative generation. It runs as a separate FastAPI service and communicates with the gateway/CLI.

### Running the LLM Service

Start the service (defaults to port 8001):

```bash
uv run echoes-llm-service
```

### Configuration

Configure via environment variables:

```bash
export ECHOES_LLM_PROVIDER=stub          # Provider: stub, openai, anthropic
export ECHOES_LLM_API_KEY=your-key-here  # Required for openai/anthropic
export ECHOES_LLM_MODEL=gpt-4            # Model name (provider-specific)
export ECHOES_LLM_TEMPERATURE=0.7        # Sampling temperature (0.0-1.0)
export ECHOES_LLM_MAX_TOKENS=500         # Max tokens in response
export ECHOES_LLM_TIMEOUT=30             # Request timeout in seconds
export ECHOES_LLM_MAX_RETRIES=2          # Number of retries on API errors
```

The `stub` provider is the default and requires no API key. It uses deterministic keyword matching for testing without API costs.

#### Provider Configuration

**Stub Provider** (default, no API key required):
```bash
export ECHOES_LLM_PROVIDER=stub
```
Uses keyword-based intent detection for offline testing without API costs.

**OpenAI Provider** (Phase 6 M6.6):
```bash
export ECHOES_LLM_PROVIDER=openai
export ECHOES_LLM_API_KEY=sk-...                  # Your OpenAI API key
export ECHOES_LLM_MODEL=gpt-4-turbo-preview       # Or gpt-4, gpt-3.5-turbo
```
Uses OpenAI function calling API for structured intent parsing. The provider sends game context and available actions as function definitions, allowing the model to return type-safe intent objects.

**Anthropic Provider** (Phase 6 M6.6):
```bash
export ECHOES_LLM_PROVIDER=anthropic
export ECHOES_LLM_API_KEY=sk-ant-...              # Your Anthropic API key
export ECHOES_LLM_MODEL=claude-3-5-sonnet-20241022  # Or other Claude models
```
Uses Anthropic Messages API with structured outputs. The provider includes intent schemas in prompts and parses JSON responses into validated intent objects.

Both real providers include retry logic for rate limits and transient errors, with configurable `max_retries` (default: 2).

### API Endpoints

**GET /healthz**

- Health check endpoint
- Returns `{"status": "ok", "provider": "stub"}`

**POST /parse_intent**

- Converts natural language to game intents
- Request: `{"text": "stabilize the industrial tier"}`
- Response: `{"intent": "stabilize", "confidence": 0.9, "parameters": {...}}`

**POST /narrate**

- Generates story text from simulation events
- Request: `{"events": [...], "context": {...}}`
- Response: `{"narration": "...", "tone": "neutral"}`

### Testing with Stub Provider

The stub provider uses keyword matching for deterministic testing:

```python
import httpx

async with httpx.AsyncClient() as client:
    # Parse intent
    response = await client.post(
        "http://localhost:8001/parse_intent",
        json={"text": "inspect the perimeter hollow district"}
    )
    print(response.json())
    # {"intent": "inspect", "confidence": 0.8, "parameters": {"district": "perimeter hollow"}}

    # Generate narration
    response = await client.post(
        "http://localhost:8001/narrate",
        json={
            "events": ["Agent recruited", "Pollution increased"],
            "context": {"district": "Industrial Tier"}
        }
    )
    print(response.json())
    # {"narration": "Recent events unfolded...", "tone": "neutral"}
```

### Intent Schema (Phase 6 M6.4)

The LLM service uses structured Pydantic models to represent game intents. All intents inherit from `GameIntent` and include type-safe validation.

#### Intent Types

1. **INSPECT** - Examine simulation entities with optional focus areas
2. **NEGOTIATE** - Broker deals with factions using levers and goals
3. **DEPLOY_RESOURCE** - Allocate materials or energy to districts
4. **PASS_POLICY** - Enact city-wide policies with parameters
5. **COVERT_ACTION** - Execute hidden operations with risk levels
6. **INVOKE_AGENT** - Direct agent actions with targets
7. **REQUEST_REPORT** - Query simulation state with filters

#### Example Intent Usage

```python
from gengine.echoes.llm import (
    InspectIntent, NegotiateIntent, DeployResourceIntent,
    parse_intent, IntentType
)

# Create typed intents
inspect = InspectIntent(
    target_type="district",
    target_id="industrial-tier",
    focus_areas=["pollution", "unrest"]
)

negotiate = NegotiateIntent(
    targets=["union-of-flux"],
    levers=["policy_support"],
    goals=["reduce_unrest"]
)

deploy = DeployResourceIntent(
    resource_type="materials",
    amount=100,
    target_district="perimeter-hollow"
)

# Parse from dictionary (used by LLM service)
intent_data = {
    "intent_type": "INSPECT",
    "target_type": "district",
    "target_id": "industrial-tier"
}
intent = parse_intent(intent_data)  # Returns InspectIntent instance
```

#### Prompt Templates

The `gengine.echoes.llm.prompts` module provides:

- **OpenAI function calling schemas** (`OPENAI_INTENT_FUNCTIONS`) for structured responses
- **Anthropic structured output schema** (`ANTHROPIC_INTENT_SCHEMA`) for Claude models
- **System prompts** with game world context and intent descriptions
- **Dynamic prompt builders** for context injection:

```python
from gengine.echoes.llm.prompts import (
    build_intent_parsing_prompt,
    build_narration_prompt
)

# Build intent parsing prompt with context
prompt = build_intent_parsing_prompt(
    command="stabilize the industrial tier",
    available_actions=["inspect", "negotiate", "deploy_resource"],
    district="industrial-tier",
    tick=42,
    recent_events=["Pollution increased", "Unrest rising"]
)

# Build narration prompt from events
narration_prompt = build_narration_prompt(
    events=["Agent recruited", "Policy passed"],
    context={"district": "Perimeter Hollow", "tick": 42}
)
```

The intent schemas enable the LLM service to convert natural language into type-safe game actions with validation, while the prompt templates ensure consistent LLM behavior across different providers.

## Docker

The project includes Docker support for containerized deployment of all three
services (simulation, gateway, LLM).

### Prerequisites

- Docker 20.10+ with BuildKit support
- Docker Compose V2 (included with Docker Desktop)

### Quick Start

```bash
# Build and start all services
docker compose up --build

# Or start in detached mode
docker compose up -d --build

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Service URLs

When running via Docker Compose, services are available at:

| Service    | URL                     | Description                              |
| ---------- | ----------------------- | ---------------------------------------- |
| Simulation | http://localhost:8000   | Core simulation API                      |
| Gateway    | http://localhost:8100   | WebSocket gateway for CLI sessions       |
| LLM        | http://localhost:8001   | Natural language processing service      |

### Configuration

Copy the sample environment file and customize as needed:

```bash
cp .env.sample .env
```

Key configuration options in `.env`:

```bash
# Port mappings (host ports)
SIMULATION_PORT=8000
GATEWAY_PORT=8100
LLM_PORT=8001

# World to load (available in content/worlds/)
ECHOES_SERVICE_WORLD=default

# LLM provider: stub (default), openai, or anthropic
ECHOES_LLM_PROVIDER=stub

# For real LLM providers (OpenAI/Anthropic)
ECHOES_LLM_API_KEY=your-api-key
ECHOES_LLM_MODEL=gpt-4-turbo-preview
```

### Running Individual Services

```bash
# Start only the simulation service
docker compose up simulation

# Start simulation + gateway (no LLM)
docker compose up simulation gateway
```

### Connecting from Host

Use the gateway shell client to connect to containerized services:

```bash
# Connect to gateway via WebSocket
uv run echoes-gateway-shell --gateway-url ws://localhost:8100/ws

# Or connect directly to simulation service
uv run echoes-shell --service-url http://localhost:8000
```

### Development Mode

For development with hot-reload of source code, create a `docker-compose.dev.yml`
file to mount the source directory and use dev dependencies:

```yaml
# docker-compose.dev.yml - Development overrides
services:
  simulation:
    build:
      target: development
    volumes:
      - ./src:/app/src:ro
      - ./content:/app/content:ro

  gateway:
    build:
      target: development
    volumes:
      - ./src:/app/src:ro
      - ./content:/app/content:ro

  llm:
    build:
      target: development
    volumes:
      - ./src:/app/src:ro
      - ./content:/app/content:ro
```

Then run with the override file:

```bash
# Build with dev dependencies
docker compose -f docker-compose.yml -f docker-compose.dev.yml build

# Run with source mounted
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Health Checks

All services expose health check endpoints at `/healthz`:

- Simulation: `GET /healthz`
- Gateway: `GET /healthz`
- LLM: `GET /healthz`

Docker Compose configures automatic health checks with 30-second intervals.

### Container Smoke Tests

A smoke test script validates the entire Docker/Compose setup:

```bash
# Run the container smoke test
./scripts/smoke_test_containers.sh
```

The script will:
1. Build the Docker image
2. Start all services via `docker compose up`
3. Poll `/healthz` endpoints for simulation, gateway, and LLM
4. Verify HTTP 200 responses
5. Clean up containers on completion

Exit codes: 0 (success), 1 (build failed), 2 (health check timeout), 3 (verification failed).

### Networking

Services communicate via the `echoes-network` Docker bridge network using
service names as hostnames:

- Gateway → Simulation: `http://simulation:8000`
- Gateway → LLM: `http://llm:8001`

## AI Tournaments & Balance Tooling

Phase 9 M9.4 provides tournament infrastructure for automated balance testing:

### Running Tournaments

```bash
# Run 100 games with default strategies
uv run python scripts/run_ai_tournament.py --games 100 --output build/tournament.json

# Run with specific strategies and more ticks
uv run python scripts/run_ai_tournament.py \
    --games 50 --ticks 200 --strategies balanced aggressive diplomatic --verbose
```

### Analyzing Results

```bash
# Analyze tournament results
uv run python scripts/analyze_ai_games.py --input build/tournament.json

# Compare against authored story seeds
uv run python scripts/analyze_ai_games.py --input build/tournament.json --world default
```

The analysis identifies:
- Win rate deltas between strategies
- Dominant or underperforming strategies
- Unused story seeds
- Overpowered actions

### CI Integration

The `.github/workflows/ai-tournament.yml` workflow runs nightly tournaments
and archives results. Trigger manual runs via the GitHub Actions UI.

See `docs/gengine/how_to_play_echoes.md` Section 13 for the complete balance
iteration workflow.

## Next Steps

1. **Phase 8 – Kubernetes Deployment** – create Kubernetes manifests for local
   minikube deployment, enabling multi-container orchestration and service
   discovery. Docker containerization is complete (see Docker section above).

Progress is tracked in the implementation plan document; update this README as
new phases land (CLI tooling, services, Kubernetes manifests, etc.).
