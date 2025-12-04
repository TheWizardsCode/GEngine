# How to Play Echoes of Emergence


This guide explains how to run the current Echoes of Emergence prototype, interpret its outputs, and iterate on the simulation while new systems are under construction. It assumes you have cloned the repository and installed all runtime/dev dependencies via `uv sync --group dev`.

**New!** For large-scale AI playtesting and balance iteration, see [Section 13: AI Tournament & Balance Analysis](./ai_tournament_and_balance_analysis.md).

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

| Command                       | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `help`                        | Lists all available commands.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `summary`                     | Shows city/tick stats, faction legitimacy, current market prices, the latest `environment_impact` snapshot (scarcity pressure, faction deltas, avg/min/max pollution, biodiversity value/deltas, stability feedback, diffusion samples), and the shared profiling block (tick ms p50/p95/max, last subsystem timings, the slowest subsystem, and anomaly tags). Also surfaces `story_seeds`, `director_events`, and a `director pacing` block that lists how many seeds are active versus resolving, whether a quiet timer is in effect, and which guardrails (max-active, seed quiet, global quiet) blocked fresh matches. |
| `next`                        | Advances the simulation exactly 1 tick and prints an inline report (no arguments). Use `run` for larger batches.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `run <n>`                     | Advances the simulation by `n` ticks (must be provided) and prints the aggregate report.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `map [district_id]`           | Without arguments, prints a city-wide ASCII table plus a geometry overlay (coordinates + neighbor list). Provide an ID to see a detailed panel with modifiers, coordinates, and adjacency hints for that district.                                                                                                                                                                                                                                                                                                                                                                                                          |
| `focus [district\|clear]`     | Shows the current focus ring (district plus prioritized neighbors) or retargets it. The focus manager allocates more narrative budget to the selected ring; use `focus clear` to fall back to the default rotation.                                                                                                                                                                                                                                                                                                                                                                                                         |
| `history [count]`             | Prints the ranked narrator history (latest entries first). Each entry shows the focus center, suppressed count, and the top scored archived beats; provide an optional count to limit how many entries are shown.                                                                                                                                                                                                                                                                                                                                                                                                           |
| `postmortem`                  | Prints a deterministic recap: environment trend deltas, the three largest faction legitimacy swings, the latest director events, and the most recent story seed states. Use it before quitting to capture an epilogue without exporting the entire snapshot.                                                                                                                                                                                                                                                                                                                                                                |
| `timeline [count]`            | Prints the causal timeline showing key events and their causes/effects. Each tick entry lists stability shifts, faction actions, story seed activations, and agent reasoning summaries. Useful for understanding "what happened and why".                                                                                                                                                                                                                                                                                                                                                                                   |
| `explain <type> <id>`         | Query detailed explanations for entities. Types: `faction`, `agent`, `district`, `metric`. Examples: `explain faction union-of-flux` (shows legitimacy trend, recent actions), `explain agent agent-1` (reasoning factors, needs), `explain metric stability` (causes and delta history).                                                                                                                                                                                                                                                                                                                                   |
| `why <query>`                 | Answer "why did this happen?" style queries. Examples: `why stability`, `why did unrest rise`, `why union-of-flux`. The system searches for matching entities/metrics and returns causal explanations with contributing factors.                                                                                                                                                                                                                                                                                                                                                                                            |
| `save <path>`                 | Writes the current `GameState` snapshot to disk as JSON.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `load world <name>`           | Reloads an authored world from `content/worlds/<name>/world.yml` (local engine mode only).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `load snapshot <path>`        | Restores state from a JSON snapshot created via `save` (local engine mode only).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `campaign list`               | Lists all saved campaigns with their IDs, names, worlds, tick counts, and status (active/ended).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `campaign new <name> [world]` | Creates a new campaign with the given name, optionally specifying a world (defaults to "default"). Initializes the world and saves an initial snapshot.                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `campaign resume <id>`        | Resumes a saved campaign by ID. Loads the campaign's snapshot and continues from where you left off.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `campaign end`                | Ends the active campaign, saves a final snapshot, generates a post-mortem summary, and marks the campaign as complete.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `campaign status`             | Shows the status of the currently active campaign including name, world, current tick, and autosave interval.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `exit` / `quit`               | Leave the shell.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |

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
  samples captured during the tick),
  profiling stats (tick duration percentiles plus the last
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
  0 and 1, and triggers "District protests intensify" when it crosses 0.75.
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

## 9. Difficulty Presets and Tuning

The simulation includes five difficulty presets that adjust resource regeneration,
demand pressure, scarcity effects, and narrative pacing to create measurably
distinct gameplay experiences. Each preset lives in
`content/config/sweeps/difficulty-{preset}/simulation.yml`.

### Available Difficulty Levels

| Preset   | Description                                   | Stability | Pacing     |
| -------- | --------------------------------------------- | --------- | ---------- |
| Tutorial | Very forgiving, maximum regen, minimal demand | High      | Slow       |
| Easy     | Relaxed settings for learning core systems    | High      | Moderate   |
| Normal   | Balanced challenge, intended gameplay         | Moderate  | Balanced   |
| Hard     | Reduced regen, increased demand pressure      | Low       | Fast       |
| Brutal   | Maximum challenge, overlapping crises         | Very Low  | Relentless |

### Running Difficulty Sweeps

To compare all difficulty levels programmatically:

```bash
uv run python scripts/run_difficulty_sweeps.py --ticks 200 --seed 42 --output-dir build
```

The sweep runner:

- Executes simulations for each difficulty preset
- Captures telemetry to `build/difficulty-{preset}-sweep.json`
- Outputs a comparison table showing stability, unrest, pollution, and anomalies

Key flags:

- `--ticks/-t`: Number of ticks per preset (default: 200)
- `--seed`: RNG seed for deterministic comparisons (default: 42)
- `--preset/-p`: Specific preset(s) to run (can be repeated)
- `--json`: Output results as JSON instead of a table

### Analyzing Difficulty Profiles

After capturing sweep telemetry, analyze and compare the profiles:

```bash
uv run python scripts/analyze_difficulty_profiles.py --telemetry-dir build
```

The analysis script:

- Loads telemetry from each difficulty capture
- Compares stability trends, faction balance, economic pressure, and narrative density
- Generates findings about difficulty progression and potential tuning issues

Example analysis output identifies:

- Whether stability decreases correctly with difficulty
- If unrest/pollution scale as expected
- Adjacent difficulties that need more differentiation
- Presets where stability collapses (may need tuning)

### Tuning Difficulty Presets

Each difficulty config adjusts several key parameters:

**Economy block:**

- `regen_scale`: Resource regeneration multiplier (higher = easier)
- `demand_*_weight`: Consumption pressure (lower = easier)
- `shortage_threshold`: When shortages register (higher = more forgiving)

**Environment block:**

- `scarcity_*_weight`: How scarcity affects unrest/pollution (lower = gentler)
- `biodiversity_recovery_rate`: Ecosystem bounce-back (higher = more resilient)
- `faction_sabotage_pollution_spike`: Sabotage severity (lower = less punishing)

**Director block:**

- `max_active_seeds`: Overlapping crises (fewer = calmer)
- `global_quiet_ticks`: Buffer between crises (more = breathing room)
- `seed_*_ticks`: How long story arcs stay active (longer = more deliberate)

### Recommended Playtesting Workflow

1. Run the tutorial preset to verify systems work as expected
2. Progress through easy → normal to confirm intended challenge curve
3. Run hard/brutal to stress-test failure cascades
4. Use the analysis script to identify gaps in difficulty progression
5. Adjust config values and re-run sweeps to validate changes

## 10. What Comes Next

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

## 11. Player Progression System

The progression system (Phase 7, M7.1) tracks player growth across five skill
domains, manages access tier unlocks, and monitors reputation with each faction.
These metrics influence action success rates and unlock new gameplay options.

### Skill Domains

Players develop expertise in five core skill domains:

| Domain        | Description                                     | Key Actions                 |
| ------------- | ----------------------------------------------- | --------------------------- |
| Diplomacy     | Faction negotiations and dialogue effectiveness | Negotiate, lobby            |
| Investigation | District inspections and information gathering  | Inspect, request reports    |
| Economics     | Resource management and trade optimization      | Invest, economic actions    |
| Tactical      | Security operations and covert actions          | Stabilize, support security |
| Influence     | Story seed triggers and NPC reactions           | Recruit, general influence  |

Skills range from level 1 (novice) to level 100 (master). Experience is gained
through actions, with multipliers per domain configurable in `simulation.yml`.

### Access Tiers

As average skill levels increase, players unlock higher access tiers:

| Tier        | Average Level | Unlocks                                      |
| ----------- | ------------- | -------------------------------------------- |
| Novice      | 0             | Default access, basic districts and commands |
| Established | 50            | Advanced districts, some restricted actions  |
| Elite       | 100           | Full access to all districts and commands    |

The CLI `summary` command shows current tier and average skill level.

### Faction Reputation

Reputation with each faction ranges from -1.0 (hostile) to +1.0 (allied):

| Range          | Relationship | Effect on Actions   |
| -------------- | ------------ | ------------------- |
| 0.75 to 1.0    | Allied       | +25% success chance |
| 0.25 to 0.75   | Friendly     | +10% success chance |
| -0.25 to 0.25  | Neutral      | No modifier         |
| -0.75 to -0.25 | Unfriendly   | -10% success chance |
| -1.0 to -0.75  | Hostile      | -25% success chance |

Reputation changes based on faction actions each tick. Positive actions
(lobbying, investing) improve reputation, while sabotage hurts reputation with
the target faction.

### Progression in CLI Summary

After running ticks, the `summary` command displays progression state:

```text
progression:
  access_tier: novice
  average_level: 1.2
  total_experience: 45.5
  actions_taken: 15
  skills:
    diplomacy: { level: 2, experience: 5.0 }
    investigation: { level: 1, experience: 8.0 }
    economics: { level: 1, experience: 0.0 }
    tactical: { level: 1, experience: 2.5 }
    influence: { level: 2, experience: 0.0 }
  reputation:
    union-of-flux: { value: 0.15, relationship: neutral }
    cartel-of-mist: { value: -0.05, relationship: neutral }
```

### Configuring Progression

Tune progression rates via the `progression` block in
`content/config/simulation.yml`:

```yaml
progression:
  base_experience_rate: 1.0      # Global experience multiplier
  experience_per_action: 10.0   # Base experience per action
  experience_per_inspection: 5.0
  experience_per_negotiation: 15.0
  diplomacy_multiplier: 1.0     # Per-domain scaling
  investigation_multiplier: 1.0
  economics_multiplier: 1.0
  tactical_multiplier: 1.0
  influence_multiplier: 1.0
  reputation_gain_rate: 0.05    # Reputation delta per positive action
  reputation_loss_rate: 0.03    # Reputation delta per negative action
  skill_cap: 100                # Maximum skill level
  established_threshold: 50     # Average level for Established tier
  elite_threshold: 100          # Average level for Elite tier
```

Increase experience rates to speed up progression for tutorials or decrease them
for more challenging campaigns.

### Per-Agent Progression (M7.1.2)

Beyond global player progression, each field agent can develop individual
expertise, reliability, and stress levels. This adds a tactical layer where
you choose which agent to send on missions based on their specialization and
current condition.

#### Agent Specializations

Each agent has a primary specialization aligned with the skill domains:

| Specialization | Primary Domain | Best Used For                         |
| -------------- | -------------- | ------------------------------------- |
| Negotiator     | Diplomacy      | Faction talks, council lobbying       |
| Investigator   | Investigation  | District inspections, intelligence    |
| Analyst        | Economics      | Resource management, trade operations |
| Operator       | Tactical       | Security ops, covert actions          |
| Influencer     | Influence      | Story seeds, NPC manipulation         |

#### Agent Stats

Each agent tracks:

- **Expertise** (0-5 pips per domain): Grows with successful missions
- **Reliability** (0.0-1.0): Increases on success, decreases on failure
- **Stress** (0.0-1.0): Rises with failures and hazardous missions, slowly recovers

Stress labels help quickly assess agent condition:

- **Calm** (0-20%): Ready for any mission
- **Focused** (20-50%): Normal operational state
- **Strained** (50-75%): Consider lighter assignments
- **Burned out** (75-100%): High risk of failure, needs rest

#### Agent Progression in CLI

The `summary` command shows agent progression when available:

```text
agent_progression:
  agent-1:
    role: Experienced Investigator
    expertise: { investigation: 3, diplomacy: 1 }
    reliability: 0.72
    stress: 0.25
    stress_label: focused
    missions_completed: 12
    missions_failed: 2
```

#### Per-Agent Success Modifiers

When `enable_per_agent_modifiers: true` is set in the config, agent stats
contribute to action success rates:

- **Expertise bonus**: Up to +10% for max expertise in the relevant domain
- **Stress penalty**: Up to -10% when severely stressed (above 50%)

These modifiers are intentionally small to avoid making the game feel like
micro-managing an RPG party. The best strategy is intuitive: send calm,
specialized agents to important missions.

#### Configuring Per-Agent Progression

Tune per-agent progression via the `per_agent_progression` block in
`content/config/simulation.yml`:

```yaml
per_agent_progression:
  enable_per_agent_modifiers: true   # Toggle agent success modifiers
  expertise_max_pips: 5              # Maximum expertise per domain
  expertise_gain_per_success: 1      # Pips gained per success
  reliability_gain_per_success: 0.05 # Reliability boost per success
  reliability_loss_per_failure: 0.08 # Reliability drop per failure
  stress_gain_per_failure: 0.1       # Stress increase per failure
  stress_gain_per_hazardous: 0.05    # Extra stress for risky missions
  stress_recovery_per_tick: 0.02     # Natural stress recovery
  max_expertise_bonus: 0.1           # Max success chance bonus
  max_stress_penalty: 0.1            # Max stress-induced penalty
```

Per-agent modifiers are enabled by default (`enable_per_agent_modifiers: true`).
Scenario testing across all difficulty presets confirmed that the ±10% bonus/
penalty envelope does not destabilize game balance. Disable the flag if you want
to remove the tactical layer around agent selection.

## 12. Campaign Management

The CLI supports persistent campaigns with autosave functionality. Instead of
manually saving/loading snapshots, you can create named campaigns that track
your progress automatically.

### Starting a New Campaign

```bash
# Start with campaign commands in the shell
uv run echoes-shell --world default
(echoes) campaign new "My First Campaign" default
```

Or resume an existing campaign directly:

```bash
uv run echoes-shell --campaign abc123
```

### Campaign Commands

| Command                       | Description                                          |
| ----------------------------- | ---------------------------------------------------- |
| `campaign list`               | Show all saved campaigns with IDs, names, and status |
| `campaign new <name> [world]` | Create a new campaign (world defaults to "default")  |
| `campaign resume <id>`        | Resume a saved campaign by its ID                    |
| `campaign end`                | End the active campaign and generate a post-mortem   |
| `campaign status`             | Show details about the currently active campaign     |

### Autosave

When a campaign is active, the system automatically saves your progress at
regular intervals. Configure the autosave behavior in
`content/config/simulation.yml`:

```yaml
campaign:
  campaigns_dir: campaigns       # Where campaign data is stored
  autosave_interval: 50          # Ticks between autosaves (0 = disabled)
  max_autosaves: 3               # Keep only the N most recent autosaves
  generate_postmortem_on_end: true  # Generate recap when campaign ends
```

Autosaves are created in the campaign's directory alongside the main snapshot.
The most recent autosaves are kept (based on `max_autosaves`), older ones are
automatically cleaned up.

### Campaign Workflow Example

```bash
uv run echoes-shell --world default
(echoes) campaign new "Stability Run" default
Created campaign 'Stability Run' (ID: a1b2c3d4)
World: default

(echoes) run 100
# ... play the simulation ...

(echoes) campaign status
Active campaign: Stability Run (ID: a1b2c3d4)
World: default
Current tick: 100
Autosave interval: every 50 ticks

# Exit and resume later
(echoes) exit
```

To resume the campaign:

```bash
uv run echoes-shell --campaign a1b2c3d4
Resumed campaign 'Stability Run' at tick 100
```

### Ending a Campaign

When you're done with a campaign, end it formally to generate a complete
post-mortem summary:

```bash
(echoes) campaign end
Campaign 'Stability Run' ended at tick 250

Post-mortem summary:
  - Stability improved from 0.56 to 0.89 (+0.33)
  - Union of Flux gained legitimacy (+0.15)
  - Energy crisis resolved through investment
```

The post-mortem is saved alongside the campaign data for later review. Ended
campaigns can still be resumed if you want to continue playing.

## 13. AI Tournaments & Balance Tooling

The repository includes AI tournament infrastructure for automated balance
testing and validation. Tournaments run multiple AI players with different
strategies in parallel, then aggregate results to identify balance anomalies.

### Running Tournaments

Run a tournament with default settings:

```bash
uv run python scripts/run_ai_tournament.py \
    --games 100 --ticks 100 --output build/tournament.json
```

The tournament script supports several options:

| Flag           | Description                                          |
| -------------- | ---------------------------------------------------- |
| `--games/-g`   | Total number of games to run (default: 100)          |
| `--ticks/-t`   | Ticks per game (default: 100)                        |
| `--strategies` | Strategies to test (balanced, aggressive, diplomatic)|
| `--seed`       | Base random seed for deterministic runs (default: 42)|
| `--workers`    | Max parallel workers (default: auto)                 |
| `--output/-o`  | Path to write JSON results                           |
| `--verbose/-v` | Print progress during tournament                     |

Example output shows win rates and stability metrics per strategy:

```
================================================================================
AI TOURNAMENT RESULTS
================================================================================

Games: 100/100 completed (0 failed)
Total duration: 45.2s

Strategy     Win Rate   Avg Stab   Min Stab   Max Stab   Avg Actions
--------------------------------------------------------------------------------
balanced        65.0%      0.720      0.450      1.000          5.2
aggressive      72.0%      0.680      0.380      1.000          8.1
diplomatic      58.0%      0.750      0.520      1.000          3.4
--------------------------------------------------------------------------------
```

### Analyzing Results

After running a tournament, analyze the results for balance insights:

```bash
uv run python scripts/analyze_ai_games.py \
    --input build/tournament.json --world default
```

The analysis script:

- Compares win rates across strategies
- Identifies dominant strategies (win rate delta > 15%)
- Flags unused or underused story seeds
- Detects overpowered actions
- Generates actionable recommendations

Example analysis output:

```
================================================================================
AI TOURNAMENT ANALYSIS REPORT
================================================================================

Tournament: 100 games, 100 ticks each
Strategies: balanced, aggressive, diplomatic

--------------------------------------------------------------------------------
WIN RATE ANALYSIS
--------------------------------------------------------------------------------
Best strategy: aggressive (72.0%)
Worst strategy: diplomatic (58.0%)
Win rate delta: 14.0%
Balance status: ✓ Balanced

--------------------------------------------------------------------------------
ACTION ANALYSIS
--------------------------------------------------------------------------------
Most used: INSPECT (450 times)
Least used: NEGOTIATE (120 times)

--------------------------------------------------------------------------------
RECOMMENDATIONS
--------------------------------------------------------------------------------
1. No significant balance issues detected - system appears well-tuned
================================================================================
```

### Balance Iteration Workflow

When tuning game balance, follow this workflow:

1. **Run baseline tournament**: Capture initial metrics with `--seed 42` for
   reproducibility.

   ```bash
   uv run python scripts/run_ai_tournament.py \
       --games 100 --output build/baseline.json
   ```

2. **Analyze baseline**: Review strategy balance, action distribution, and seed
   coverage.

   ```bash
   uv run python scripts/analyze_ai_games.py \
       --input build/baseline.json --world default
   ```

3. **Adjust parameters**: Based on analysis findings, modify config values in
   `content/config/simulation.yml`:

   - Strategy thresholds affect AI decision-making
   - Economy settings influence resource pressure
   - Director pacing controls narrative density

4. **Run comparison tournament**: Use the same seed for deterministic comparison.

   ```bash
   uv run python scripts/run_ai_tournament.py \
       --games 100 --output build/tuned.json --seed 42
   ```

5. **Compare results**: Diff the analysis reports to validate improvements.

   ```bash
   # Compare win rates between runs
   python scripts/analyze_ai_games.py --input build/baseline.json --json > /tmp/a.json
   python scripts/analyze_ai_games.py --input build/tuned.json --json > /tmp/b.json
   diff /tmp/a.json /tmp/b.json
   ```

6. **Iterate**: Repeat steps 3-5 until balance metrics fall within acceptable
   ranges.

### CI Integration

The repository includes a GitHub Actions workflow (`.github/workflows/ai-tournament.yml`)
that runs nightly tournaments:

- Executes 100 games with all strategies
- Archives results as artifacts for 90 days
- Prints analysis summary in the job log

To trigger a manual tournament run, use the GitHub Actions UI and select
"Run workflow" with optional game/tick counts.

### Interpreting Anomalies

The analysis script flags several types of balance issues:

| Anomaly Type         | Severity | Meaning                                    |
| -------------------- | -------- | ------------------------------------------ |
| `dominant_strategy`  | High     | One strategy wins > 20% more than others   |
| `strategy_imbalance` | Medium   | Win rate delta between 15-20%              |
| `dominant_action`    | Medium   | One action accounts for > 50% of all uses  |
| `unused_story_seeds` | High/Low | Story seeds never triggered during games   |
| `low_seed_coverage`  | Medium   | Less than 50% of seeds were activated      |
| `low_activity`       | Low      | A strategy averages < 1 action per game    |

Recommendations are generated automatically based on detected anomalies. Use
them as starting points for parameter tuning rather than prescriptive fixes.
