# How to Play Echoes of Emergence

This guide explains how to run the current Echoes of Emergence prototype,
interpret its outputs, and iterate on the simulation while new systems are
under construction. It assumes you have cloned the repository and installed all
runtime/dev dependencies via `uv sync --all-extras --dev`.

## 1. Launching the Shell

The CLI shell is the primary way to interact with the simulation today.

```bash
uv run echoes-shell --world default
```

- `--world` selects the authored content folder under `content/worlds/`.
- Use `--snapshot path/to/save.json` to load a previously saved state.
- For scripted runs (handy for CI or quick experiments):
  ```bash
  uv run echoes-shell --world default --script "summary;next 5;map;exit"
  ```

On startup the shell prints a world summary and shows the prompt `(echoes)`.
Type commands listed in the next section to explore the world, advance time,
and persist state.

## 2. Shell Commands

| Command                | Description                                                                                                                                                      |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `help`                 | Lists all available commands.                                                                                                                                    |
| `summary`              | Shows city name, tick count, number of districts/factions/agents, and global stability.                                                                          |
| `next`                 | Advances the simulation exactly 1 tick and prints an inline report. Use `run` for larger batches.                                                                |
| `run <n>`              | Advances the simulation by `n` ticks (must be provided) and prints the aggregate report.                                                                         |
| `map [district_id]`    | With no argument, prints a city-wide ASCII table including **district IDs** (e.g., `industrial-tier`). Provide an ID to see an in-depth panel for that district. |
| `save <path>`          | Writes the current `GameState` snapshot to disk as JSON.                                                                                                         |
| `load world <name>`    | Reloads an authored world from `content/worlds/<name>/world.yml`.                                                                                                |
| `load snapshot <path>` | Restores state from a JSON snapshot created via `save`.                                                                                                          |
| `exit` / `quit`        | Leave the shell.                                                                                                                                                 |

Command arguments are whitespace-separated; wrap file paths containing spaces in
quotes. The shell ignores blank lines and repeats the prompt after each command.

## 3. Simulation Concepts

The CLI now routes every command through the shared `SimEngine` abstraction.
This is the same interface that the upcoming simulation service will expose,
so all outputs you see in the shell mirror what remote clients will receive.

If you prefer to drive the sim over HTTP, run `uv run python -m
gengine.echoes.service.main` and issue requests to `/tick`, `/state`, and
`/metrics` (or use the bundled `SimServiceClient`). The CLI gateway planned for
Phase 3 will talk to this exact API.

### Ticks and Reports

- Each `next`/`run` command calls the simulation tick loop.
- Every tick adjusts district resources, drifts district modifiers (unrest,
  pollution, prosperity, security), and updates the global environment metrics
  (stability, unrest, pollution, security, climate risk).
- The tick report shows the tick number, global metrics, and notable events
  (e.g., "Industrial Tier pollution spike detected").

### District Overview

- `map` with no arguments prints an ASCII table:
  - **District ID** (used for commands and content files)
  - Display name, population, and current modifier values.
- `map <district_id>` dives deeper into one district, showing population and
  modifier values with two-decimal precision. Use this to track unrest spikes or
  pollution drift while tuning the sim.

### Agents, Factions, and Environment

- Agents and factions are currently static data loaded from the world YAML.
  Future phases will add AI behaviors, but you can inspect the roster via
  `scripts/eoe_dump_state.py --world default` or by examining the content files.
- Environment metrics (stability/unrest/pollution/security) evolve slightly each
  tick based on district modifiers. Watch the tick reports for tipping-point
  messages.

## 4. World and District Parameters

The world YAML defines both global city metadata and per-district stats. The
shell surfaces the same data so you can reason about how each parameter affects
the simulation loop.

| Parameter           | Scope    | Gameplay impact                                                           |
| ------------------- | -------- | ------------------------------------------------------------------------- |
| Stability           | World    | Measures governance health; drops when unrest is above midpoint.          |
| Unrest              | World    | Tracks civic tension; high values spawn warnings and erode stability.     |
| Pollution           | World    | Captures environmental stress; spills into security penalties.            |
| Security            | World    | Describes city-wide order; declining security signals looming disruption. |
| Climate Risk        | World    | Long-term exposure baseline; narrative lever for future disaster hooks.   |
| Population          | District | Indicates resident scale; future systems will scale events by population. |
| District Unrest     | District | Local protests; averages feed the global unrest metric every tick.        |
| District Pollution  | District | Local environmental damage; influences global pollution each tick.        |
| District Prosperity | District | Economic confidence; upcoming AI behaviors will lean on this signal.      |
| District Security   | District | Local orderliness; low scores raise the odds of protest events.           |
| Resource Capacity   | District | Hard cap for each resource stock; bounds how much supply exists.          |
| Resource Current    | District | Live amount of a resource; shortages trigger tick log entries.            |
| Resource Regen      | District | Intended replenishment speed; ready for deeper economy integrations.      |

### World (City + Environment)

- **City metadata**: `id`, display `name`, and optional `description` identify
  the playable scenario and appear in the shell banner.
- **Environment metrics**: `stability`, `unrest`, `pollution`, `security`, and
  `climate_risk` track macro health in the `EnvironmentState`. Each value ranges
  from 0.0 to 1.0 and drifts every tick based on district modifiers.
- **Factions and agents**: Listed under the world file for narrative flavor and
  future AI hooks. Today they are informative only but still appear in summary
  dumps.

### Districts

- **Identifiers**: Every district has a machine-friendly `id` (used in CLI
  commands), a `name`, and optional flavor text in the content file.
- **Population**: Integer count representing the scale of residents. Higher
  populations amplify modifier effects during ticks.
- **Resources**: Each stock lists `capacity`, `current`, and `regen`. The tick
  loop nudges `current` toward capacity while consuming or regenerating based on
  scripted rules, so shortages show up in tick reports.
- **Modifiers**: Continuous values between 0.0 and 1.0 for `pollution`,
  `unrest`, `prosperity`, and `security`. These drift slightly per tick and feed
  into environment changes. Spikes here usually trigger event log warnings.

Keeping these parameters consistent between YAML content and the shell output
helps you detect data-entry mistakes quickly (e.g., mismatched IDs or runaway
modifier values).

## 5. Game Parameters

Each tracked parameter plays a specific role inside the tick loop. Use this
section to understand what the number represents in gameplay terms and what can
move it during a tick.

### Stability

- **Role:** City-wide governance resilience that frames every summary and
  determines how fragile the setting feels.
- **Tick influences:** After district updates, stability is adjusted via
  `stability -= (unrest - 0.5) * 0.04`, so high global unrest steadily chips
  away until warnings fire below 0.4.

### Unrest

- **Role:** Aggregated civic tension; high values warn you that protests or
  lockdowns are imminent.
- **Tick influences:** Computed from average district unrest and a small random
  jitter. Sustained district unrest above 0.5 pushes the global number upward
  and triggers the "Civic tension is rising" event when it exceeds 0.7.

### Pollution

- **Role:** Measures systemic environmental strain that can bleed into other
  systems.
- **Tick influences:** Uses district pollution averages to drift toward higher
  or lower values. Crossing 0.7 emits "Pollution breaches critical thresholds"
  and sets up security losses.

### Security

- **Role:** Reflects the city's ability to enforce order.
- **Tick influences:** Updated as `security -= (pollution - 0.5) * 0.02`, so
  escalating pollution erodes security while cleaner conditions let it rebound
  toward the midpoint.

### Climate Risk

- **Role:** Encodes long-term exposure to storms, droughts, or other systemic
  threats; useful for narrative framing.
- **Tick influences:** Static in the current prototype. Author it per scenario
  and expect future disaster systems to pivot off the value.

### Population

- **Role:** Signals how big a district is and how impactful events there should
  feel.
- **Tick influences:** Population does not change automatically yet; treat it
  as a balancing lever while upcoming subsystems begin scaling effects by
  district size.

### District Unrest

- **Role:** Localized protest energy.
- **Tick influences:** Receives a -0.02 to 0.02 random drift, is clamped between
  0 and 1, and triggers "<District> protests intensify" when it crosses 0.75.
  The average also feeds the global unrest calculation.

### District Pollution

- **Role:** Local environmental degradation that bubbles up to city-wide stats.
- **Tick influences:** Similar random drift (-0.015 to 0.015) with clamping. At
  > 0.75 it logs a pollution spike and raises the global pollution average.

### District Prosperity

- **Role:** Economic confidence indicator meant to guide agent behavior and
  event payoff.
- **Tick influences:** Random drift between -0.02 and 0.02 without secondary
  effects yet; track it now to spot districts that may need tuning.

### District Security

- **Role:** Local enforcement strength.
- **Tick influences:** Shares the -0.02 to 0.02 drift pattern. Future crime or
  faction systems will hook into it, so keep values within believable bounds.

### Resource Capacity

- **Role:** Defines the maximum stock level for commodities like energy or
  water.
- **Tick influences:** Static, but the resource update routine clamps `current`
  to the capacity so overflows never occur.

### Resource Current

- **Role:** Represents real-time supply and is the primary scarcity signal.
- **Tick influences:** Each tick nudges the value toward half of capacity,
  applies a small random fluctuation, and logs a tick event when the change is
  greater than three units.

### Resource Regen

- **Role:** Documents how quickly a resource should refill when deeper economy
  systems arrive.
- **Tick influences:** Not yet used during ticks, but populating it in YAML
  keeps the data model ready for advanced rules.

## 6. Saving, Loading, and Hot-Swapping Worlds

- Use `save build/state.json` to capture the entire state at any tick.
- Reload later with `load snapshot build/state.json`.
- To iterate on content, edit `content/worlds/default/world.yml` (or create a
  new folder) and run `load world your_world_name` to start over without
  restarting the shell.

Snapshots are plain JSON; you can inspect or version them to track different
simulation branches.

## 7. Tips for Playtesting

1. Run short bursts (`next 5`) to monitor how modifiers drift, then longer runs
   (`run 50`) to see macro trends.
2. Save before experimenting so you can quickly reload if the metrics diverge.
3. Use the scripted mode to reproduce issues: store sequences like
   `summary;next 10;map;save tmp.json;exit` in a shell alias or task runner.
4. Keep an eye on the tick event logs—early warnings like "Civic tension is
   rising" indicate metrics approaching thresholds.

## 8. What Comes Next

The shell currently operates entirely in-process. Upcoming phases of the plan
will:

- Extract the tick engine into a FastAPI simulation service.
- Introduce deeper agent/faction/economy subsystems feeding the tick loop.
- Add a gateway service plus LLM-driven intent parsing for richer interaction.

As those milestones land, this guide will expand with new sections covering
service endpoints, intent schemas, and multi-service orchestration.
