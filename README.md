# GEngine: Echoes of Emergence

A staged simulation project that prototypes the "Echoes of Emergence" CLI + LLM
experience. The long-term goal is a service-first architecture (simulation
service, CLI gateway, LLM intent service) designed for Kubernetes. This README
summarizes the current state of development and the immediate workflows you can
run locally.

## Current Status (Phases 1–2)

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
  mode, and profiling toggles. `SimEngine` enforces these caps and logs tick
  timing when profiling is enabled.
- Headless regression driver (`scripts/run_headless_sim.py`) that advances
  batches of ticks, emits per-batch diagnostics, and writes JSON summaries for
  automated sweeps or CI regressions.
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
uv sync --all-extras --dev
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
uv run echoes-shell --world default --script "summary;next 3;map;save build/state.json;exit"
```

Both modes share the same in-process GameState and emit ASCII summaries/maps for
rapid iteration.

Available in-shell commands:

- `help` – list commands and syntax.
- `summary` – show city, tick, counts, stability.
- `next` – advance exactly one tick with the inline report. Use `run` for
  batches.
- `run <n>` – advance `n` ticks (must be provided) and show the combined report.
  The CLI enforces the safeguard defined in `limits.cli_run_cap` (default 50).
- `map [district_id]` – render ASCII table of all districts (includes an "ID"
  column) or details for one. Use `map` with no arguments to discover values
  such as `industrial-tier`.
- `save <path>` – write the current snapshot as JSON.
- `load world <name>` / `load snapshot <path>` – swap to a new authored world or
  on-disk snapshot (local engine mode only).
- `exit`/`quit` – leave the shell.

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
- `profiling`: flips the structured tick log on/off. When enabled, every
  `SimEngine.advance_ticks` call logs tick counts, duration (ms), and the active
  LOD mode via the `gengine.echoes.sim` logger so you can profile headless runs.

Edit the YAML, rerun the CLI/service, and the new safeguards apply immediately
without code changes.

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
diff.

```bash
uv run python scripts/run_headless_sim.py --world default --ticks 500 --lod coarse --output build/headless.json
```

Key flags:

- `--ticks/-t`: total ticks to run (chunked automatically).
- `--lod`: override `simulation.yml` LOD mode (`detailed|balanced|coarse`).
- `--seed`: deterministic runs for regression capture.
- `--snapshot`: start from a saved snapshot instead of content.
- `--config-root`: point at an alternate config folder (useful in CI).
- `--output`: path for the structured summary (includes tick counts, timing,
  LOD mode, and last environment metrics).

## Next Steps

- Phase 3: extract the tick engine into a FastAPI-based simulation service and
  add a thin HTTP client so the CLI can run in service mode.
- Phase 4: enrich agents/factions/economy/environment subsystems to feed the
  tick loop with deeper mechanics.

Progress is tracked in the implementation plan document; update this README as
new phases land (CLI tooling, services, Kubernetes manifests, etc.).
