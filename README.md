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
  resources, districts, and environment metrics each tick.
- CLI shell (`echoes-shell`) that runs the sim in-process, supports
  `summary`, `next`, `run`, `map`, `save`, and `load` commands, and can run in
  interactive or scripted mode.
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
- `map [district_id]` – render ASCII table of all districts (includes an "ID"
  column) or details for one. Use `map` with no arguments to discover values
  such as `industrial-tier`.
- `save <path>` – write the current snapshot as JSON.
- `load world <name>` / `load snapshot <path>` – swap to a new authored world or
  on-disk snapshot.
- `exit`/`quit` – leave the shell.

## Next Steps

- Phase 3: extract the tick engine into a FastAPI-based simulation service and
  add a thin HTTP client so the CLI can run in service mode.
- Phase 4: enrich agents/factions/economy/environment subsystems to feed the
  tick loop with deeper mechanics.

Progress is tracked in the implementation plan document; update this README as
new phases land (CLI tooling, services, Kubernetes manifests, etc.).
