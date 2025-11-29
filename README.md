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
  interactive or scripted mode.
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

## Progress Log (Updated 2025-11-29)

- ✅ **Phase 5 M5.3 – Pacing & lifecycle polish** shipped: deterministic
  lifecycle states with per-seed/global quiet timers now gate director overlap,
  CLI/service/headless surfaces show the new `director_pacing` +
  `story_seed_lifecycle` blocks, docs walk through the pacing knobs, and
  regression tests/telemetry guard the lifecycle history + cooldown math.
- ⚙️ **Phase 5 M5.4 – Post-mortems** remains in progress; upcoming work layers
  deterministic epilogue generation and golden narrative outputs on top of the
  archived lifecycle history before opening Phase 6 tooling.

## Repository Layout

```
content/                 Authored YAML worlds and (future) story seeds
scripts/                 Developer utilities (state dump, headless drivers, ...)
src/gengine/echoes/core  Data models and GameState container
src/gengine/echoes/sim   Tick loop and future subsystems
src/gengine/echoes/cli   CLI shell + helpers
tests/                   Pytest suites (content, tick loop, CLI shell)
```

## Prerequisites

- Python 3.12+
- `uv` (https://github.com/astral-sh/uv)

## Setup

```bash
cd /home/rogardle/projects/gengine
uv sync --group dev
```

The first sync creates/updates `.venv` and installs runtime plus dev
dependencies.

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
uv run python scripts/run_headless_sim.py --world default --ticks 200 --lod balanced --seed 42 --output build/m4-3-economy-telemetry.json
```

Archive the JSON alongside the test results (commit or attach in review) so the
canonical seed/tick profile is always available for comparison. The telemetry
now captures agent/faction breakdowns, per-faction legitimacy snapshots/deltas,
the `last_economy` block (price table + shortage counters), and
`last_director_analysis` (hotspot travel recommendations) for regression diffs.
The same JSON also embeds the `director_pacing` snapshot, the full
`story_seed_lifecycle` table, lifecycle history, and any active global quiet
timer so reviewers can diff cooldown math between builds without reproducing
ticks locally.
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

- To target a running FastAPI simulation service, supply
  `--service-url http://localhost:8000`. When this flag is set the CLI routes
  through HTTP using `SimServiceClient`; `load world`/`load snapshot` will emit
  guidance because content swaps must happen server-side.

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
- `save <path>` – write the current snapshot as JSON.
- `load world <name>` / `load snapshot <path>` – swap to a new authored world or
  on-disk snapshot (local engine mode only).
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
```

Or, run the CLI shell against the service without restarting:

```bash
uv run echoes-shell --service-url http://localhost:8000 --script "summary;run 5;map;exit"
```

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
  archive used by the narrator).

## Next Steps

1. **Phase 5 M5.3 – Pacing & lifecycle polish** – finish validating the director
  state machine (quiet spans, cooldown persistence, lifecycle history), keep
  the README/GDD/how-to docs aligned, and capture the balanced 200-tick
  telemetry artifact after each regression pass so reviewers can diff pacing
  metadata without rerunning the sim.
2. **Phase 5 M5.4 – Post-mortems** – layer deterministic epilogue generation on
  top of the archived story seeds + faction/environment deltas, surface it via
  CLI/service/headless endpoints, and add golden outputs tied to the canonical
  telemetry seed.
3. **Phase 9 M9.1 – AI Player Observer** (parallel track) – implement
  `src/gengine/ai_player/observer.py` plus its CLI runner so automated playtests
  can analyze stability trends, faction swings, and pacing logs. See the Phase 9
  section of the implementation plan for the full observer → actor → LLM
  roadmap.

Progress is tracked in the implementation plan document; update this README as
new phases land (CLI tooling, services, Kubernetes manifests, etc.).
