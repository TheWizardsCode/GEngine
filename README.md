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
  reacts to faction investments/sabotage with pollution relief/spikes, and
  captures the resulting `environment_impact` metadata for telemetry + CLI/
  service summaries.
- Headless regression driver (`scripts/run_headless_sim.py`) that advances
  batches of ticks, emits per-batch diagnostics, and writes JSON summaries for
  automated sweeps or CI regressions.
- Instrumented profiling that records per-tick durations (p50/p95/max) and
  subsystem timing deltas directly into `GameState.metadata`. The CLI summary,
  FastAPI `/metrics` response, and headless regression outputs all surface the
  same block so designers can spot runaway ticks without attaching a profiler.
- Utility script `scripts/eoe_dump_state.py` for quick world inspection and
  snapshot exports.
- Test suite covering content loading, snapshot round-trip, tick behavior, and
  CLI scripts (`tests/echoes/`).

See `docs/simul/emergent_story_game_implementation_plan.md` for the full
multi-phase roadmap and `docs/gengine/how_to_play_echoes.md` for a gameplay guide.

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
and the `last_economy` block (price table + shortage counters) for regression
diffs. Use `summary` on any saved snapshot to inspect the last tick's
`environment_impact` block when diagnosing pollution swings.

### Scenario Sweeps

- For environment tuning, dedicated config variants live under
  `content/config/sweeps/`. Example commands:

  ```bash
  uv run python scripts/run_headless_sim.py --world default --ticks 400 --lod balanced --seed 42 --config-root content/config/sweeps/high-pressure --output build/sweep-high-pressure.json
  uv run python scripts/run_headless_sim.py --world default --ticks 400 --lod balanced --seed 42 --config-root content/config/sweeps/cushioned --output build/sweep-cushioned.json
  ```

- The high-pressure profile intentionally stress-tests scarcity by increasing
  pressure/diffusion weights, while the cushioned profile keeps pollution in
  check for longer playtests. Compare their telemetry outputs to map safe
  ranges before promoting new environment tweaks.

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
  market prices, the `environment_impact` block, and the new profiling payload
  (tick ms p50/p95/max plus the last subsystem timings) so you can gauge
  systemic pressure before advancing time again.
- `next` – advance exactly one tick with the inline report (no arguments). Use
  `run` for batches.
- `run <n>` – advance `n` ticks (must be provided) and show the combined report.
  The CLI enforces the safeguard defined in `limits.cli_run_cap` (default 50).
- `map [district_id]` – render ASCII table of all districts (includes an "ID"
  column) or details for one. Use `map` with no arguments to discover values
  such as `industrial-tier`.
- `save <path>` – write the current snapshot as JSON.
- `load world <name>` / `load snapshot <path>` – swap to a new authored world or
  on-disk snapshot (local engine mode only).
- `exit`/`quit` – leave the shell.
- Tick reports now include agent activity lines such as "Aria Volt inspects
  Industrial Tier" plus faction beats like "Union of Flux invests in
  Industrial Tier", making it easier to follow systemic reactions. Below the
  environment summary you will also see a "faction legitimacy" block (top ±3
  deltas each tick) and a `market -> energy:1.05, food:0.98, …` line whenever
  the economy subsystem has published prices.
- `summary` now renders the latest `environment_impact` snapshot and the shared
  profiling block. Together they show scarcity pressure, whether diffusion
  fired, pollution shifts from faction activity, plus tick-duration percentiles
  and the slowest subsystems from the most recent tick.

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
  same block reports whether diffusion ran in the last tick and how faction
  investments/sabotage adjusted local pollution via the
  `faction_invest_pollution_relief` and `faction_sabotage_pollution_spike`
  knobs.

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
```

Or, run the CLI shell against the service without restarting:

```bash
uv run echoes-shell --service-url http://localhost:8000 --script "summary;run 5;map;exit"
```

## Headless Regression Driver

`scripts/run_headless_sim.py` advances long simulations without interactive
input. It chunks work to respect `limits.engine_max_ticks`, prints per-batch
diagnostics to stderr, and writes a JSON summary that downstream tools can
diff. The JSON now mirrors the CLI/service profiling block so you can inspect
tick duration percentiles and the slowest subsystems alongside the usual
agent/faction metrics.

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
  snapshot, the last economy report, and the shared profiling block with the
  most recent subsystem timings).

## Next Steps

- Phase 4: continue deepening the subsystems (environment diffusion + telemetry
  surfacing refinements, environment diffusion tuning, scenario sweeps) and keep
  surfacing data so playtesters can see the
  cause/effect chain.
- Phase 5+: narrative director, intent gateway, and multiplayer/Gateway
  services per the implementation plan.

Progress is tracked in the implementation plan document; update this README as
new phases land (CLI tooling, services, Kubernetes manifests, etc.).
