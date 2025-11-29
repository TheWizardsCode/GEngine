# How to Play Echoes of Emergence

This guide explains how to run the current Echoes of Emergence prototype,
interpret its outputs, and iterate on the simulation while new systems are
under construction. It assumes you have cloned the repository and installed all
runtime/dev dependencies via `uv sync --group dev`.

## 1. Launching the Shell

The CLI shell is the primary way to interact with the simulation today.

```bash
uv run echoes-shell --world default
```

- `--world` selects the authored content folder under `content/worlds/`.
- Use `--snapshot path/to/save.json` to load a previously saved state.
- Use `--service-url http://localhost:8000` to target the FastAPI simulation
  service instead of running in-process (world/snapshot loads must then be
  triggered server-side).
- Use `--rich` to enable enhanced ASCII views with styled tables, color-coded
  panels, and improved readability (requires Rich library).
- For scripted runs (handy for CI or quick experiments):
  ```bash
  uv run echoes-shell --world default --script "summary;run 5;map;exit"
  ```
- For enhanced visualization during playtesting:
  ```bash
  uv run echoes-shell --world default --rich
  ```

On startup the shell prints a world summary and shows the prompt `(echoes)`.
Type commands listed in the next section to explore the world, advance time,
and persist state.

### Remote Sessions via the Gateway Service

Phase 6 introduces a WebSocket gateway so remote testers can drive the CLI
without SSH access. Launch the gateway alongside the FastAPI simulation
service:

```bash
uv run echoes-gateway-service
```

Then connect with the bundled client (or any WebSocket tool that sends JSON
`{"command": "..."}` frames):

```bash
uv run echoes-gateway-shell --gateway-url ws://localhost:8100/ws --script "summary;run 3;exit"
```

Each connection provisions a dedicated `EchoesShell`, proxies commands to the
simulation service configured via `ECHOES_GATEWAY_SERVICE_URL`, and logs
focus/digest/history snapshots via the `gengine.echoes.gateway` logger whenever
`summary`, `focus`, `history`, or `director` runs. The client prints the same
ASCII output as the local shell and honors `--script` for CI-friendly runs.

## 2. Shell Commands

| Command                   | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `help`                    | Lists all available commands.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `summary`                 | Shows city/tick stats, faction legitimacy, current market prices, the latest `environment_impact` snapshot (scarcity pressure, faction deltas, avg/min/max pollution, biodiversity value/deltas, stability feedback, diffusion samples), and the shared profiling block (tick ms p50/p95/max, last subsystem timings, the slowest subsystem, and anomaly tags). Also surfaces `story_seeds`, `director_events`, and a `director pacing` block that lists how many seeds are active versus resolving, whether a quiet timer is in effect, and which guardrails (max-active, seed quiet, global quiet) blocked fresh matches. |
| `next`                    | Advances the simulation exactly 1 tick and prints an inline report (no arguments). Use `run` for larger batches.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `run <n>`                 | Advances the simulation by `n` ticks (must be provided) and prints the aggregate report.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `map [district_id]`       | Without arguments, prints a city-wide ASCII table plus a geometry overlay (coordinates + neighbor list). Provide an ID to see a detailed panel with modifiers, coordinates, and adjacency hints for that district.                                                                                                                                                                                                                                                                                                                                                                                                          |
| `focus [district\|clear]` | Shows the current focus ring (district plus prioritized neighbors) or retargets it. The focus manager allocates more narrative budget to the selected ring; use `focus clear` to fall back to the default rotation.                                                                                                                                                                                                                                                                                                                                                                                                         |
| `history [count]`         | Prints the ranked narrator history (latest entries first). Each entry shows the focus center, suppressed count, and the top scored archived beats; provide an optional count to limit how many entries are shown.                                                                                                                                                                                                                                                                                                                                                                                                           |
| `postmortem`              | Prints a deterministic recap: environment trend deltas, the three largest faction legitimacy swings, the latest director events, and the most recent story seed states. Use it before quitting to capture an epilogue without exporting the entire snapshot.                                                                                                                                                                                                                                                                                                                                                                |
| `save <path>`             | Writes the current `GameState` snapshot to disk as JSON.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `load world <name>`       | Reloads an authored world from `content/worlds/<name>/world.yml` (local engine mode only).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `load snapshot <path>`    | Restores state from a JSON snapshot created via `save` (local engine mode only).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `exit` / `quit`           | Leave the shell.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |

Command arguments are whitespace-separated; wrap file paths containing spaces in
quotes. The shell ignores blank lines and repeats the prompt after each command.

## 3. Simulation Concepts

The CLI now routes every command through the shared `SimEngine` abstraction or,
when `--service-url` is provided, through the FastAPI simulation service using
`SimServiceClient`. Either way the outputs you see are consistent with what
remote clients receive.

Run `uv run python -m gengine.echoes.service.main` to host the service locally
and call `/tick`, `/state`, and `/metrics` with `SimServiceClient` or
`curl`. Phase 6's `echoes-gateway-service` sits on top of the same API,
forwarding every WebSocket command through `SimServiceClient`. Use
`GET /state?detail=post-mortem` (or the CLI `postmortem` command) whenever you
need the deterministic recap JSON that also appears in headless telemetry.

### Safeguards and Level of Detail

- The CLI clamps `run` commands to the value configured in
  `limits.cli_run_cap` (default 50). If you request more ticks you will see a
  `Safeguard: run limited...` prefix but still receive the resulting report.
- Scripts triggered via `--script` (or the `run_commands` helper in tests) are
  capped by `limits.cli_script_command_cap` (default 200). Once the limit is
  reached the shell prints a warning and exits the loop, preventing runaway CI
  jobs.
- The FastAPI `/tick` endpoint enforces `limits.service_tick_cap` (default 100)
  and responds with HTTP 400 if a client exceeds it.
- All limits live in `content/config/simulation.yml`. Override the config path
  with `ECHOES_CONFIG_ROOT` to inject environment-specific guardrails.
- Level-of-Detail settings (`lod` block) adjust how aggressively the tick loop
  drifts resources/modifiers. `balanced` dampens volatility compared to
  `detailed`, while `coarse` applies heavy smoothing and caps the number of
  per-tick events so long burns stay legible.
- When `profiling.log_ticks` is enabled, `SimEngine` emits log entries such as
  `ticks=5 duration_ms=4.1 lod=balanced` via the `gengine.echoes.sim` logger so
  you can measure performance of scripted runs or headless drivers. The same
  profiling settings now populate a shared metadata block (tick ms p50/p95/max
  plus the last subsystem timings) that appears in the CLI summary, FastAPI
  `/metrics`, and headless telemetry JSON.

### Ticks and Reports

- Each `next`/`run` command calls the simulation tick loop.
- Every tick adjusts district resources, drifts district modifiers (unrest,
  pollution, prosperity, security), and updates the global environment metrics
  (stability, unrest, pollution, security, climate risk).
- The tick report shows the tick number, global metrics, and notable events
  (e.g., "Industrial Tier pollution spike detected").
- `summary` mirrors those metrics without advancing time and now includes both
  the `environment_impact` block (scarcity pressure, faction pollution deltas,
  diffusion state, average pollution, the latest extreme districts, the
  biodiversity snapshot with scarcity/recovery deltas, and the top diffusion
  samples captured during the tick), profiling stats (tick duration percentiles plus the last
  subsystem timings), and the focus digest preview (up to six curated events
  plus a suppressed count). Use `focus` to retarget which districts receive the
  larger per-tick budget whenever you need to spotlight a different hotspot.
  When the narrative director matches an authored story seed, the summary also
  prints a `story seeds` block that lists the seed title, target district,
  severity score, trigger reason, and a `cooldown_remaining` countdown. Seeds
  stay visible for the duration of their cooldown, so telemetry and CLI runs
  still show the latest matches even if the triggering tick has already passed.
  A paired `director events` block highlights the seeds that actually fired
  (with stakes plus the first matching agent/faction) so you know who is on
  stage without replaying the tick log.
- Agent AI (Phase 4, M4.1) now contributes narrative lines such as "Aria Volt
  inspects Industrial Tier" or "Cassian Mire negotiates with Cartel of Mist";
  use these to understand how background characters are reacting to system
  pressures. The system ensures each tick includes at least one inspect or
  negotiate beat so the feed always surfaces a strategic highlight.
- Faction AI (Phase 4, M4.2) injects slower, strategic beats—"Union of Flux
  invests in Industrial Tier" or "Cartel of Mist undermines Union of Flux"—and
  directly tweaks legitimacy, resources, and district modifiers so the macro
  picture evolves even without player input.
- When legitimacy shifts are meaningful the shell prints a short "faction
  legitimacy" block showing the three largest deltas (signed) so you can track
  winners/losers at a glance. A `market -> energy:1.05, food:0.97, ...` line
  follows whenever the economy subsystem has published prices for the tick.
- Focus-aware narration: the tick log now prints a "focus budget" line that
  reports how many curated events went to the focus ring versus the global pool
  and how many additional beats were archived. The `focus` command exposes the
  current ring (center + neighbors) so you can retarget the curator before
  running long batches. Suppressed events remain available in metadata/telemetry
  for post-run analysis.

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

### Economy and Market Feedback

- The economy subsystem rebalances each district's resource stocks every tick,
  tracks shortages that persist beyond a configurable duration, and publishes a
  lightweight market table. Those prices and shortage counters are stored in
  the game state metadata so the CLI summary, service responses, and telemetry
  can all display the latest values consistently.
- When shortages linger you will see economy alerts in the tick log (e.g.,
  "Economy alert: energy shortage persists for 3 ticks"), giving you an early
  warning before unrest or faction pressure escalates.

### Tuning the Economy via Config

- Edit `content/config/simulation.yml` to tweak the `economy` block. Key knobs:
  - `regen_scale`: multiplier applied to every district's resource regeneration
    rate before random drift.
  - `demand_population_scale`, `demand_unrest_weight`, and
    `demand_prosperity_weight`: shape how population, unrest, and prosperity
    amplify consumption.
  - `base_resource_weights`: per-resource weighting that biases demand toward
    certain commodities.
  - `shortage_threshold` + `shortage_warning_ticks`: control when shortages are
    counted and surfaced in reports.
  - `base_price`, `price_increase_step`, `price_max_boost`, `price_decay`, and
    `price_floor`: define how market prices spike during shortages and glide
    back down when supply recovers.
- Restart the shell or service after editing the file (or point
  `ECHOES_CONFIG_ROOT` at an alternate folder) and the next tick will use the
  new parameters. Pair config tweaks with long `run` or headless sessions to
  see how scarcity curves and price ceilings change over time.

### Environment Coupling

- Scarcity signals now feed into the environment loop via `EnvironmentSystem`.
  When the economy subsystem reports sustained shortages, the system applies a
  configurable pressure value that drifts district unrest/pollution and, by
  extension, global stability while also draining biodiversity if the pressure
  persists.
- Tune the response curve through the `environment` block in
  `content/config/simulation.yml`. The `scarcity_*_weight` fields control how
  strongly shortages push on unrest or pollution, while `scarcity_event_threshold`
  decides when the shell prints explicit "Scarcity" alerts. Designers can also
  steer diffusion with `diffusion_neighbor_bias` (how much more heavily adjacent
  districts are weighted versus the citywide mean) plus
  `diffusion_min_delta`/`diffusion_max_delta` clamps that keep the per-tick drift
  inside predictable bounds. Biodiversity tuning lives in the same block via
  `biodiversity_baseline`, `biodiversity_recovery_rate`,
  `scarcity_biodiversity_weight`, `biodiversity_stability_weight`,
  `biodiversity_stability_midpoint`, and `biodiversity_alert_threshold`, giving
  you control over how quickly ecosystems erode, how fast they rebound, when
  warnings fire, and how hard stability responds once the gauge drifts below
  the midpoint.
- Pollution diffuses toward a citywide average each tick when `diffusion_rate`
  is non-zero, and faction actions now feed directly into the loop:
  `faction_invest_pollution_relief` eases pollution whenever a faction invests
  in one of its districts, while `faction_sabotage_pollution_spike` models the
  fallout from covert ops. District modifiers now include a gentle mean-
  reversion back toward the 0.5 midpoint, so long burns stay within believable
  bands while still leaving room for spikes. On top of that, factions now push
  toward `INVEST_DISTRICT` whenever unrest rises above ~0.4 or security dips
  below ~0.5, and sabotage is throttled so only the weaker faction can escalate
  (legitimacy gap ≥ 0.05) while stability is at least 0.45. The result is a
  steady rhythm of relief actions punctuated by rare sabotage beats instead of
  runaway crises every 300–400 ticks.
- Every tick writes an `environment_impact` block into the game state's
  metadata. Inspect it via headless telemetry or by dumping the snapshot to see
  the latest pressure, diffusion flag, faction effects, per-district deltas,
  the biodiversity value/deltas with scarcity vs. recovery attribution, the
  stability feedback applied that tick, the average pollution level, which
  districts held the min/max values, and up to three sampled diffusion deltas
  while you tune. The `summary` command now prints this block
  directly, alongside profiling metrics that include tick percentiles, the
  slowest subsystem, and any anomaly tags so designers can spot runaway
  pollution or suspicious subsystem spikes before advancing time.
- For rapid scenario sweeps, switch configs with
  `--config-root content/config/sweeps/high-pressure` (stress test),
  `.../cushioned` (long-form stability), or `.../profiling-history`
  (history window = 240 ticks) when running `scripts/run_headless_sim.py`.
- After capturing cushioned/high-pressure/profiling-history sweeps, run
  `uv run python scripts/plot_environment_trajectories.py --output build/<name>.png`
  to overlay their pollution/unrest trajectories. The script scans each
  telemetry file's `director_history`, so raise `focus.history_length` to at
  least the tick budget ahead of time if you need the full run plotted. Supply
  additional `--run label=/path/to/file` arguments to compare custom captures.
- Latest deterministic soaks (seed 42, 1000 ticks, balanced LOD) serve as
  guardrail captures:
  - **Baseline (`build/focus-baseline-1000tick.json`)** – 0 anomalies, stability
    bottoms out around 0.57 with ~2.4k suppressed events for the narrator to
    triage.
  - **Profiling-history (`build/profiling-history-1000tick.json`)** – history
    window raised to 240, 0 anomalies, stability locked at 1.0, unrest settles
    to 0.0 by the end of the burn.
  - **Soft-scarcity (`build/profiling-history-soft-scarcity-1000tick.json`)** –
    regen boost and lower pressure weights keep both pollution and unrest at 0
    with just 247 suppressed events. Use this preset to study how the narrator
    behaves when scarcity is dialed down without touching code.
- The shared config also includes a `focus` block (default district,
  neighborhood size, focus/global budget split, digest/history lengths). Tuning
  these settings lets you tighten or relax the curator without changing code.

### Focus Manager & Narrative Digest

- The focus manager guarantees that the player-selected district (plus a small
  ring of neighbors) receives a larger share of the per-tick narrative budget
  while the rest of the city competes for the global pool. This keeps long
  burns legible without starving distant districts entirely.
- Use `focus` with no arguments to see the current center/neighbors, with a
  district id to retarget the ring, or with `clear` to reset to the configured
  default. Every tick records a digest (what you saw), the full archive, and a
  suppressed preview in metadata so you can diff exposure later.
- The narrator now scores every archived beat by severity (scope + keywords)
  and focus distance, then records the ranked archive and suppression history
  so you can chase the most urgent beats first.
- Run `history [count]` to print the latest ranked entries (latest first).
  Each entry shows the focus center, suppressed count, and the highest ranked
  archived events so testers can quickly review what was trimmed.
- Run `director [count]` to inspect the director feed bridge _and_ the new
  travel-aware narrative director layer. The command prints the current focus
  center, allocation stats, spatial preview, highest-ranked archived beats,
  and now the travel planner output: hotspot routes (hops, travel time,
  reachability) plus any recommended focus shift based on suppressed pressure.
  Director output also includes a `seed matches` section so you can see which
  authored seeds attached to the listed hotspots without digging into the raw
  metadata.
- The CLI summary and tick reports show the digest preview and the latest
  focus-budget allocation so you always know whether anomalies are coming from
  raw subsystem volume or simply from the curator trimming noise.
- Spatial weighting now blends authored coordinates/adjacency with the
  population-ranked ring, so the focus output shows each district's
  coordinates, neighbor list, and blended score contribution. Use this readout
  to explain why a distant but populous district is still prioritized (or why
  a nearby low-density one falls out of the ring) before running long burns.
- Headless summaries now record `director_feed`, a rolling
  `director_history`, the `last_director_snapshot`, and the new
  `last_director_analysis` block so you can diff both the curator's ranked
  archive/spatial context _and_ the director's travel reasoning alongside
  suppressed counts in longer sweeps. The JSON payload also exposes a
  top-level `story_seeds` array with the most recent matches so telemetry
  captures which authored beats were live at the end of the run.

### Director Pacing & Lifecycles

- The director now runs a pacing state machine that moves each seed through
  `primed → active → resolving → archived`, tracking per-seed cooldowns, per-seed
  quiet timers, and a global quiet span. When pacing guardrails trip, the
  director defers new matches until either the max-active limit relaxes or the
  quiet timer expires.
- CLI and service summaries include a `director pacing` block plus rich seed
  entries so you can see how many crises are active versus resolving, how long
  remains on the global quiet timer, and whether the latest tick was blocked by
  `max_active`, `seed_quiet`, or `global_quiet`. Each visible seed lists its
  lifecycle state, remaining active/resolving duration, and `cooldown_remaining`
  so you know when it can fire again.
- The adjacent `story_seed_lifecycle` table mirrors the telemetry payload: per
  row you get the seed id, lifecycle state, ticks remaining in that state,
  cooldown remaining, and the `last_trigger_tick`. Use this view to explain why
  a beat is still resolving or why it dropped back to `primed` even if the
  director is quiet.
- Headless telemetry mirrors the same data via the `director_pacing`,
  `story_seed_lifecycle`, `story_seed_lifecycle_history`, and
  `director_quiet_until` keys. Diff these blocks between telemetry captures to
  reason about pacing regressions without replaying the session.
- Tune pacing under the `director` block in `content/config/simulation.yml`
  (and every sweep preset). `max_active_seeds` limits overlapping crises,
  `global_quiet_ticks` enforces a buffer after each activation, and the
  `seed_*` durations (`seed_active_ticks`, `seed_resolve_ticks`,
  `seed_quiet_ticks`) define how long a beat stays on stage before returning to
  `primed`. `lifecycle_history_limit` controls how much history stays in CLI and
  telemetry outputs for after-action reviews.

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
- **Coordinates & Adjacency**: Each district now defines a `coordinates` tuple
  plus an `adjacent` list (often auto-derived). Focus budgeting, diffusion, and
  future travel-aware stories combine literal neighbors with the population-
  ranked rings, and the `map` command visualizes the blended overlay so data
  mismatches surface immediately.

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

1. Run short bursts (`run 5`) to monitor how modifiers drift, then longer runs
   (`run 50`) to see macro trends.
2. Save before experimenting so you can quickly reload if the metrics diverge.
3. Use the scripted mode to reproduce issues: store sequences like
   `summary;run 10;map;save tmp.json;exit` in a shell alias or task runner.
4. Keep an eye on the tick event logs—early warnings like "Civic tension is
   rising" indicate metrics approaching thresholds.

## 8. Headless Regression Runs

For longer burns or CI sweeps, use `scripts/run_headless_sim.py`:

```bash
uv run python scripts/run_headless_sim.py --world default --ticks 400 --lod coarse --output build/regression.json
```

- The driver obeys the same safeguards by chunking work into
  `limits.engine_max_ticks` batches and printing per-batch diagnostics to
  stderr.
- Summaries include tick counts, total duration, LOD mode, the final
  environment snapshot, and the profiling block (tick ms p50/p95/max, slowest
  subsystem, and anomaly tags). The JSON now also tracks the number of agent
  actions, faction actions, their respective breakdowns, per-batch `tick_ms`
  plus slowest-subsystem snapshots, anomaly totals/examples, faction
  legitimacy snapshots, the `last_economy` block, and a `last_event_digest`
  payload (visible events, archived events, suppressed preview, focus budget)
  so you can audit what the curator showed versus what it archived, along with
  the new `post_mortem` recap that mirrors the CLI/service output for quick
  epilogues. Store the
  JSON outputs in version control to diff systemic changes over time.
- Use `--seed` for deterministic comparisons and `--config-root` to point at a
  CI-specific configuration folder (high-pressure, cushioned, and profiling-
  history presets now live under `content/config/sweeps/`).

For reviewer sign-off on Phase 5 M5.4, rerun the canonical balanced capture
after each regression sweep:

```bash
uv run python scripts/run_headless_sim.py --world default --ticks 200 --lod balanced --seed 42 --output build/feature-m5-4-post-mortem.json
```

Check the resulting `post_mortem` block with `jq '.post_mortem'
build/feature-m5-4-post-mortem.json` (or diff two captures by piping both
through `jq`) to confirm environment deltas, faction swings, director events,
and story-seed recaps stayed deterministic without replaying ticks.

## 9. What Comes Next

The local shell now has three front-ends—direct in-process state, HTTP service
mode, and the Phase 6 WebSocket gateway. Upcoming phases will:

- Extend the gateway/UI layer with richer ASCII overlays (shared `summary`
  tables, enhanced `map`/`director` panels) so remote sessions match the local
  CLI presentation exactly.
- Introduce deeper agent/faction/economy subsystems feeding the tick loop.
- Layer an LLM intent service on top of the gateway so free-form text can be
  parsed into structured actions before the simulation executes them.

As those milestones land, this guide will expand with new sections covering
service endpoints, intent schemas, and multi-service orchestration.
