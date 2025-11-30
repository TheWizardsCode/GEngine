# Project Task Tracker

**Last Updated:** 2025-11-30T23:15:00Z

## Status Summary

**Recent Progress (since last update):**

- 🎉 **Task 9.1.1 (AI Observer Foundation) COMPLETED** - GitHub Issue [#19](https://github.com/TheWizardsCode/GEngine/issues/19)
  - Fixed bug in Observer._get_state() for service mode data unwrapping
  - Added 4 new integration tests for SimServiceClient mode
  - Enhanced README with comprehensive service mode examples
  - All acceptance criteria verified and met
  - Unblocks Task 9.2.1 (Rule-Based AI Action Layer)
- 🎉 **Phase 7 COMPLETE** - All player experience features shipped!
  - ✅ Task 7.4.1 (Campaign UX) completed and merged via PR #14
  - ✅ Task 7.1.1 (Progression Systems) completed and merged via PR #12
  - ✅ Task 7.3.1 (Tuning & Replayability) completed
  - ✅ Task 7.2.1 (Explanations) completed
  - 📋 Issues #11, #13 closed
- 🆕 **Phase 8 initiated** - Task 8.1.1 (Containerization) created
  - 📋 GitHub Issue [#15](https://github.com/TheWizardsCode/GEngine/issues/15) created
  - Status: Not started, awaiting assignment

**Previous Updates:**

- ✅ Task 7.4.1 (Campaign UX Flows) **COMPLETED** by gamedev-agent (2025-11-30)
  - Campaign module with create/list/resume/end/autosave functionality
  - CLI commands: campaign new/list/resume/end/status plus --campaign flag
  - 23 comprehensive tests (all passing), configuration in simulation.yml
  - Documentation updated in GDD, implementation plan, and gameplay guide
- ✅ Task 7.1.1 (Progression Systems) **COMPLETED** by gamedev-agent (2025-11-30)
  - Core progression module with skills, access tiers, reputation implemented
  - ProgressionSystem integrated with SimEngine tick loop
  - 48 comprehensive tests (all passing), configuration in simulation.yml
  - Documentation updated in GDD, implementation plan, and gameplay guide
- ✅ Task 7.3.1 (Tuning & Replayability Sweeps) **COMPLETED** by gamedev-agent
  - 5 difficulty presets created (easy, normal, hard, brutal, tutorial)
  - Sweep runner and analysis scripts implemented with full test coverage
  - Documentation updated in gameplay guide

**Current Priorities:**

1. 🚀 **Phase 8 Deployment** - Task 8.1.1 in progress (Issue #15, PR #16)
2. 🤖 **Phase 9 AI Testing** - Task 9.2.1 next (Rule-Based AI Action Layer)
3. 🔧 **Optional Polish** - Task 7.1.2 in progress (Issue #17, PR #18)

**Key Risks:**

- ✅ **Phase 9 M9.1 complete** - AI Observer foundation verified and documented
- ⚠️ **Phase 8 requires ownership assignment** - Who handles Docker/K8s work? (Ross to assign)
- ✅ **Phase 7 delivery risk eliminated** - All core player features complete and tested

| ID | Task | Status | Priority | Responsible | Updated |
|---:|---|---|---|---|---|
| 1.1.1 | Create Tracker Agent | completed | High | Ross (PM) | 2025-11-30 |
| 3.4.1 | Safeguards & LOD refresh follow-ups | completed | High | Gamedev Agent | 2025-11-30 |
| 4.1.1 | Implement Agent AI subsystem (M4.1) | completed | High | Team | 2025-11-30 |
| 4.2.1 | Implement Faction AI subsystem (M4.2) | completed | High | Team | 2025-11-30 |
| 4.3.1 | Finalize Economy subsystem & tests (M4.3) | completed | High | Team | 2025-11-30 |
| 4.4.1 | Complete Environment dynamics coverage (M4.4) | completed | Medium | Team | 2025-11-30 |
| 4.5.1 | Finalize Tick orchestration & telemetry (M4.5) | completed | High | Team | 2025-11-30 |
| 4.7.1 | Tune spatial adjacency & seed thresholds (M4.7) | completed | Medium | Team | 2025-11-30 |
| 5.1.1 | Story seed schema & loading (M5.1) | completed | High | Team | 2025-11-30 |
| 5.2.1 | Director hotspot analysis (M5.2) | completed | High | Team | 2025-11-30 |
| 5.3.1 | Director pacing & lifecycle (M5.3) | completed | High | Team | 2025-11-30 |
| 5.4.1 | Post-mortem generator (M5.4) | completed | Medium | Team | 2025-11-30 |
| 6.1.1 | Gateway service (M6.1) | completed | High | Team | 2025-11-30 |
| 6.3.1 | LLM service skeleton (M6.3) | completed | High | Team | 2025-11-30 |
| 6.5.1 | Gateway ↔ LLM ↔ sim integration (M6.5) | completed | High | Team | 2025-11-30 |
| 6.6.1 | Implement real LLM providers (M6.6) | completed | High | Team | 2025-11-30 |
| 7.1.1 | Design & build progression systems (M7.1) | completed | High | gamedev-agent | 2025-11-30 |
| 7.1.2 | Implement per-agent progression layer (M7.1.x) | not-started | Low | gamedev-agent | 2025-11-30 |
| 7.2.1 | Explanations & causal queries (M7.2) | completed | High | Team | 2025-11-30 |
| 7.3.1 | Tuning & replayability sweeps (M7.3) | completed | High | Gamedev Agent | 2025-11-30 |
| 7.4.1 | Campaign UX flows (M7.4) | completed | Medium | gamedev-agent | 2025-11-30 |
| 8.1.1 | Containerization (Docker + compose) (M8.1) | not-started | High | TBD (ask Ross) | 2025-11-30 |
| 8.2.1 | Kubernetes manifests & docs (M8.2) | not-started | Medium | TBD (ask Ross) | 2025-11-30 |
| 8.3.1 | Observability in Kubernetes (M8.3) | not-started | Medium | TBD (ask Ross) | 2025-11-30 |
| 8.4.1 | Content pipeline tooling & CI (M8.4) | not-started | Medium | TBD (ask Ross) | 2025-11-30 |
| 9.1.1 | AI Observer foundation acceptance (M9.1) | completed | Medium | gamedev-agent | 2025-11-30 |
| 9.2.1 | Rule-based AI action layer (M9.2) | not-started | Medium | TBD (ask Ross) | 2025-11-30 |
| 9.3.1 | LLM-enhanced AI decisions (M9.3) | not-started | Medium | TBD (ask Ross) | 2025-11-30 |
| 9.4.1 | AI tournaments & balance tooling (M9.4) | not-started | Low | TBD (ask Ross) | 2025-11-30 |

## Task Details

### 1.1.1 — Create Tracker Agent
- **Description:** Implement a tracker agent that maintains the project task tracker at `.pm/tracker.md`. The agent should produce daily timestamped updates, identify and surface risks with mitigation suggestions, summarize progress for stakeholders, and keep task statuses current.
- **Acceptance Criteria:** Adds/updates `.pm/tracker.md` programmatically or via an agreed workflow; includes a summary table; records timestamped updates; lists risks and suggested mitigations; shows responsible party and next steps for each task.
-- **Priority:** High
- **Responsible:** Ross (PM)
- **Dependencies:** Agreement on assignment and expected cadence; access to repository write permissions for automated updates (if automation is planned).
- **Risks & Mitigations:**
  - Risk: Agent writes incomplete or inaccurate updates. Mitigation: Require human review step before publish.
  - Risk: Unauthorized automated commits. Mitigation: Use a service account with limited permissions and require PRs if needed.
- **Next Steps:**
  1. Use tracker agent to keep `.pm/tracker.md` current as work progresses.
  2. Review tracker weekly to adjust priorities, risks, and ownership.
- **Last Updated:** 2025-11-29

### 3.4.1 — Safeguards & LOD Refresh Follow-Ups
- **Description:** Complete the remaining M3.4 safeguard and LOD refresh work: audit all guardrail surfaces against current config, extend profiling hooks so CLI/service/headless share a common performance block, maintain the guardrail verification matrix, and ensure docs explain tuning per environment.
- **Acceptance Criteria:** Guardrail audit completed and documented; profiling block with tick percentiles + subsystem timings appears consistently in CLI/service/headless summaries; regression matrix entries exist with passing tests; README/gameplay docs describe guardrails and tuning.
- **Priority:** High
- **Responsible:** Gamedev Agent
- **Status:** ✅ COMPLETED
- **Completion Notes:**
  - **Config Audit:** Verified `content/config/simulation.yml` limits align with Phase 4 loads:
    - `limits.engine_max_ticks`: 200 (allows full baseline captures)
    - `limits.cli_run_cap`: 50 (reasonable for interactive sessions)
    - `limits.cli_script_command_cap`: 200 (supports comprehensive scripted tests)
    - `limits.service_tick_cap`: 100 (balanced for load protection)
  - **Profiling Block Consistency:** Verified that tick percentiles (p50/p95/max), subsystem timings, slowest_subsystem, and anomalies appear consistently in:
    - CLI summary via `_render_summary()`
    - Service `/metrics` endpoint
    - Headless JSON output via `summary["profiling"]`
  - **Regression Matrix:** All 5 guardrail regression tests pass:
    - `test_engine_enforces_tick_limit`
    - `test_shell_run_command_is_clamped`
    - `test_run_commands_respects_script_cap`
    - `test_tick_endpoint_rejects_large_requests`
    - `test_run_headless_sim_supports_batches`
  - **Documentation:** README.md and `docs/gengine/how_to_play_echoes.md` describe guardrails and tuning per environment.
- **Last Updated:** 2025-11-30

### 4.1.1 — Implement Agent AI Subsystem (M4.1)
- **Description:** Deliver Phase 4 agent AI: extend content schema for needs/goals/memory, implement a deterministic agent brain that emits per-tick intents, guarantee at least one strategic action per tick, and surface aggregate agent telemetry in headless summaries.
- **Acceptance Criteria:** Updated YAML schema and validation fixtures; `systems/agents.py` implements utility-based decision logic with seeded determinism; per-tick strategic agent actions visible in CLI/service/headless outputs; tests cover scoring, determinism, and summary counts.
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Stable GameState model and content schema; tick orchestration hooks.
- **Risks & Mitigations:**
  - Risk: Non-deterministic behavior breaks tests. Mitigation: Centralize RNG seeding and document usage.
  - Risk: Agent actions overwhelm summaries. Mitigation: Coordinate with FocusManager/narrator budgets.
- **Next Steps:**
  1. Design and document agent traits/needs/goals schema.
  2. Implement utility model and plumb into tick loop.
  3. Add telemetry fields and regression tests.
- **Last Updated:** 2025-11-29

### 4.2.1 — Implement Faction AI Subsystem (M4.2)
- **Description:** Implement faction AI with resources, legitimacy, territory, and strategic actions that operate at a slower cadence, emitting structured events and telemetry for summaries and metrics.
- **Acceptance Criteria:** `systems/factions.py` models faction resources/legitimacy and actions with cooldowns; conflict resolution mutates agent/faction/city state; `/state?detail=summary` and `/metrics` expose faction deltas; tests cover legitimacy loss scenarios and telemetry encoding.
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Agent system, economy/environment hooks, content definitions for factions.
- **Risks & Mitigations:**
  - Risk: Faction actions destabilize economy/environment too aggressively. Mitigation: Add config knobs and scenario sweeps.
  - Risk: Telemetry becomes noisy. Mitigation: Aggregate at appropriate granularity.
- **Next Steps:**
  1. Finalize faction resource/ideology schema.
  2. Implement faction actions and conflict resolution.
  3. Extend summaries/metrics and add scenario tests.
- **Last Updated:** 2025-11-29

### 4.3.1 — Finalize Economy Subsystem & Tests (M4.3)
- **Description:** Complete remaining economy subsystem work: conservation checks, shortage handling, config knob exposure, and expanded regression/property tests plus scenario sweeps.
- **Acceptance Criteria:** No negative resource stocks under normal operation; persistent shortages raise warnings; economy knobs live under `economy` in `simulation.yml` and sweeps; tests cover floors/ceilings, shortage responses, and long-run conservation.
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Existing economy implementation, config system, and test harness.
- **Risks & Mitigations:**
  - Risk: Conservation rules over-constrain scenarios. Mitigation: Allow tuned thresholds and document trade-offs.
  - Risk: Sweeps are slow. Mitigation: Start with shorter runs and scale up.
- **Next Steps:**
  1. Implement conservation checks and shortage warnings.
  2. Wire economy knobs through configs and docs.
  3. Add unit/property tests and scenario sweeps.
- **Last Updated:** 2025-11-29

### 4.4.1 — Complete Environment Dynamics Coverage (M4.4)
- **Description:** Finish environment subsystem validation with scenario coverage for pollution emergencies, diffusion telemetry, biodiversity scarcity/recovery loops, stability feedback, and CLI messaging, plus any pending environment map warnings.
- **Acceptance Criteria:** Scenario tests cover key environment behaviors; telemetry and CLI clearly surface environment impacts; environment map warnings/events added where planned.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Existing EnvironmentSystem, economy/faction hooks, telemetry plumbing.
- **Risks & Mitigations:**
  - Risk: Environment tests become brittle to numeric tuning. Mitigation: Use ranges and qualitative assertions where possible.
- **Next Steps:**
  1. Identify missing environment scenarios.
  2. Implement tests and map warnings.
  3. Update docs with environment telemetry guidance.
- **Last Updated:** 2025-11-29

### 4.5.1 — Finalize Tick Orchestration & Telemetry (M4.5)
- **Description:** Ensure tick orchestration (subsystem ordering, anomaly handling) and telemetry (durations, errors, focus budgets, suppressed events) are complete, observable via `/metrics` and headless summaries.
- **Acceptance Criteria:** Deterministic subsystem order documented and enforced; telemetry includes per-subsystem durations, anomalies, focus/global budgets, and suppressed events; integration tests cover multi-tick scenarios and failure paths.
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** All major subsystems (agents, factions, economy, environment, narrator) and FocusManager.
- **Risks & Mitigations:**
  - Risk: Telemetry overhead affects performance. Mitigation: Configurable sampling/windows.
- **Next Steps:**
  1. Document and lock in subsystem order.
  2. Verify telemetry fields across CLI/service/headless.
  3. Add or extend integration tests.
- **Last Updated:** 2025-11-29

### 4.7.1 — Tune Spatial Adjacency & Seed Thresholds (M4.7)
- **Description:** Tune the spatial adjacency graph and narrative seed thresholds using new spatial weights and director feeds; expand authored seeds and wire resolution/cooldown UX across all surfaces.
- **Acceptance Criteria:** Seed triggers and adjacency weights produce stable, interesting hotspot mobility; additional seeds authored and visible in telemetry; CLI/service/headless surfaces show clear resolution/cooldown states.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** FocusManager, director feed, story seed schema.
- **Risks & Mitigations:**
  - Risk: Overfitting tuning to a single world. Mitigation: Test against multiple configs.
- **Next Steps:**
  1. Run sweeps to observe hotspot behavior.
  2. Adjust thresholds/weights and author seeds.
  3. Polish UX for resolution/cooldown states.
- **Last Updated:** 2025-11-29

### 6.5.1 — Gateway ↔ LLM ↔ Sim Integration (M6.5)
- **Description:** Wire full loop from user text through LLM intent parsing into simulation actions and back to narrative responses, including retry/fallback flows.
- **Acceptance Criteria:** Gateway can accept natural language commands, obtain intents from LLM service, apply actions via sim API, and return coherent responses; retries handle parse/action failures; integration tests exercise end-to-end flow.
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** LLM intent schema/prompts (M6.4), LLM service skeleton, simulation action routing.
- **Risks & Mitigations:**
  - Risk: Unclear error modes between services. Mitigation: Standardize error payloads and logging.
- **Next Steps:**
  1. Define end-to-end interaction contract.
  2. Implement gateway orchestration logic.
  3. Add stub-based integration tests.
- **Last Updated:** 2025-11-29

### 6.6.1 — Implement Real LLM Providers (M6.6)
- **Description:** Implement `OpenAIProvider` and `AnthropicProvider` wired to intent schema and prompts, with configuration, retries, and error handling.
- **Acceptance Criteria:** Providers selectable via settings; integration tests with mocked responses; clear docs for API keys/models and operational guidance.
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** LLM service, intent schema/prompt modules.
- **Risks & Mitigations:**
  - Risk: Cost/latency spikes. Mitigation: Budget controls and timeouts.
- **Next Steps:**
  1. Implement provider adapters.
  2. Add configuration + docs.
  3. Write mocked integration tests.
- **Last Updated:** 2025-11-29

### 7.1.1 — Design & Build Progression Systems (M7.1)
- **GitHub Issue:** [#11](https://github.com/TheWizardsCode/GEngine/issues/11)
- **Description:** Implement skills, access tiers, and reputation systems that influence success rates and dialogue, integrated with existing metrics and narrative systems.
- **Acceptance Criteria:** Progression mechanics visible in gameplay surfaces; config-driven tuning; tests validate key progression flows.
- **Priority:** High
- **Responsible:** gamedev-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** Narrative director (✅ Phase 5), agent/faction systems (✅ Phase 4).
- **Risks & Mitigations:**
  - Risk: Progression overwhelms core simulation complexity. Mitigation: Start with minimal viable progression and iterate.
  - Risk: Balancing progression curves is time-consuming. Mitigation: Use config-driven tuning and existing difficulty sweep infrastructure.
- **Completion Notes:**
  - **Core Progression Module** (`src/gengine/echoes/core/progression.py`):
    - `SkillDomain` enum: diplomacy, investigation, economics, tactical, influence
    - `AccessTier` enum: novice, established, elite
    - `SkillState` model: level (1-100), experience tracking, level-up calculations
    - `ReputationState` model: -1.0 to 1.0 value, relationship labels (hostile to allied)
    - `ProgressionState` model: complete player progression with skills, reputation, tier
    - `calculate_success_modifier()`: combines skill and reputation for action success rates
  - **Progression System** (`src/gengine/echoes/systems/progression.py`):
    - `ProgressionSystem` class processes agent/faction actions each tick
    - Grants skill experience based on action types
    - Modifies reputation based on faction actions (positive/negative)
    - Tracks progression events for telemetry
    - `ProgressionSettings` dataclass with config-driven tuning
  - **GameState Integration**: Optional `progression` field persists across snapshots
  - **SimEngine Integration**: Progression updates after each tick batch
  - **Configuration** (`content/config/simulation.yml`):
    - New `progression` section with all tunable parameters
    - Experience rates, domain multipliers, reputation rates, tier thresholds
  - **Test Coverage**: 48 new tests in `tests/echoes/test_progression.py`
    - Model tests for SkillState, ReputationState, ProgressionState
    - System tests for tick processing, reputation changes
    - Integration tests for SimEngine and GameState
    - Scenario tests for progression over time
  - **Documentation**: Updated `docs/gengine/how_to_play_echoes.md` with:
    - Section 11: Player Progression System
    - Skill domain descriptions
    - Access tier unlock criteria
    - Reputation effects on success rates
    - Configuration reference
- **Last Updated:** 2025-11-30

### 7.1.2 — Implement Per-Agent Progression Layer (M7.1.x)
- **GitHub Issue:** [#17](https://github.com/TheWizardsCode/GEngine/issues/17)
- **Description:** Implement the per-agent progression layer described in GDD §4.1.1 and the implementation plan (M7.1.x), adding a lightweight `AgentProgressionState` keyed by `agent_id` on top of the existing global `ProgressionState`. Wire it into `GameState`, `ProgressionSystem.tick(...)`, configuration, and minimal CLI/service surfaces while keeping effects bounded and optional.
- **Acceptance Criteria:**
  - `AgentProgressionState` model exists with specialization, expertise pips, reliability, stress, and mission counters.
  - `GameState` can persist and restore `agent_progression` without breaking old snapshots.
  - `ProgressionSystem` updates per-agent state when `agent_actions` include `agent_id`, without changing existing global progression behavior.
  - New config knobs in `simulation.yml` control expertise/stress/reliability deltas and max bonus/penalty envelope.
  - Optional success-modifier wrapper for per-agent bonuses is gated behind a config flag.
  - At least a couple of CLI/service/explanation surfaces can display basic per-agent summaries.
  - Tests cover model behavior, tick integration, and snapshot round-tripping.
- **Priority:** Low
- **Responsible:** gamedev-agent
- **Status:** not-started
- **Dependencies:** 7.1.1 (global progression systems), Phase 4 agent system, stable `agent_actions` payloads.
- **Risks & Mitigations:**
  - Risk: Per-agent bonuses/penalties destabilize difficulty. Mitigation: Keep modifiers small, config-gated, and covered by scenario tests.
  - Risk: Roster UX becomes too fiddly. Mitigation: Limit tracked stats and ensure agent summaries remain legible in CLI/gateway views.
- **Next Steps:**
  1. Implement `AgentProgressionState` and integrate `agent_progression` into `GameState` with migration-safe defaults.
  2. Extend `ProgressionSystem.tick(...)` to update per-agent progression from `agent_actions` and emit minimal telemetry.
  3. Add config knobs, basic UX surfaces, and regression tests as outlined in the implementation plan.
- **Last Updated:** 2025-11-30

### 7.3.1 — Tuning & Replayability Sweeps (M7.3)
- **Description:** Implement scenario sweeps, difficulty modifiers, and config exposure to tune pacing, difficulty, and replayability.
- **Acceptance Criteria:** Sweep scripts/configs exist; difficulty presets produce distinct experiences; analysis scripts compare difficulty profiles.
- **Priority:** Medium
- **Responsible:** Gamedev Agent
- **Status:** ✅ COMPLETED
- **Completion Notes:**
  - **Difficulty Presets:** Created 5 difficulty configs in `content/config/sweeps/difficulty-{preset}/`:
    - `tutorial`: Very forgiving, max regen (1.2x), minimal demand, slow pacing
    - `easy`: Relaxed settings, strong regen (1.0x), moderate pacing
    - `normal`: Balanced challenge, standard regen (0.8x), intended gameplay
    - `hard`: Reduced regen (0.7x), increased demand, fast pacing, 2 active seeds
    - `brutal`: Minimal regen (0.6x), maximum demand, relentless pacing, 3 active seeds
  - **Sweep Runner Script:** `scripts/run_difficulty_sweeps.py` executes all presets
    and captures telemetry to `build/difficulty-{preset}-sweep.json`
  - **Analysis Script:** `scripts/analyze_difficulty_profiles.py` compares profiles:
    - Stability trends, faction balance, economic pressure, narrative density
    - Generates findings about difficulty progression and tuning issues
    - Identifies gaps in differentiation between adjacent difficulties
  - **Telemetry Captures:** All 5 difficulty levels captured with seed=42, 200 ticks
  - **Test Coverage:** 17 new tests for sweep runner and analysis scripts
  - **Documentation:** Updated `docs/gengine/how_to_play_echoes.md` with difficulty
    guidance, tuning workflow, and recommended playtesting steps
- **Dependencies:** Stable core systems, story seeds, and telemetry.
- **Risks & Mitigations:**
  - Risk: Large sweep runs slow. Mitigation: Stage runs (smoke vs deep sweeps).
- **Last Updated:** 2025-11-30

### 7.4.1 — Campaign UX Flows (M7.4)
- **GitHub Issue:** [#13](https://github.com/TheWizardsCode/GEngine/issues/13)
- **Description:** Refine UX flows for campaigns, autosaves, campaign picker, and end-of-run summaries in both CLI and gateway.
- **Acceptance Criteria:** Players can manage campaigns (start, resume, end) with autosaves; end-of-run flow cleanly surfaces post-mortems and summaries; responsibilities between services are clearly documented.
- **Priority:** Medium
- **Responsible:** gamedev-agent
- **Status:** ✅ COMPLETED
- **Completion Notes:**
  - **Campaign Module** (`src/gengine/echoes/campaign/`):
    - `Campaign` model: ID, name, world, timestamps, tick, ended status
    - `CampaignManager` class: create, list, load, save, autosave, end campaigns
    - `CampaignSettings` dataclass: configurable via simulation.yml
    - Autosave at configurable intervals with automatic cleanup
    - Post-mortem generation and persistence on campaign end
  - **CLI Commands:**
    - `campaign list` - show all saved campaigns
    - `campaign new <name> [world]` - create new campaign
    - `campaign resume <id>` - resume existing campaign
    - `campaign end` - end campaign with post-mortem
    - `campaign status` - show active campaign details
    - `--campaign <id>` CLI flag for direct campaign resumption
  - **Configuration** (`content/config/simulation.yml`):
    - New `campaign` section with campaigns_dir, autosave_interval, max_autosaves, generate_postmortem_on_end
  - **Test Coverage:** 23 new tests in `tests/echoes/test_campaign.py`
    - CampaignSettings tests
    - Campaign model serialization tests
    - CampaignManager lifecycle tests
    - Integration tests with LocalBackend
  - **Documentation:** Updated gameplay guide, README, GDD, implementation plan
- **Dependencies:** Snapshot persistence (✅ complete), post-mortem generator (✅ complete), CLI/gateway surfaces (✅ complete).
- **Last Updated:** 2025-11-30

### 8.1.1 — Containerization (Docker + Compose) (M8.1)
- **GitHub Issue:** [#15](https://github.com/TheWizardsCode/GEngine/issues/15)
- **Description:** Create Dockerfiles and docker-compose configuration for simulation, gateway, and LLM services.
- **Acceptance Criteria:** All three services can be built and run via Docker/compose; basic README instructions exist; environment configuration is shared via env vars.
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Stable service boundaries (✅ Phase 6 complete), configuration contracts (✅ complete).
- **Risks & Mitigations:**
  - Risk: Divergence between local and container configs. Mitigation: Use shared env var contracts and sample env files.
  - Risk: Port conflicts or networking issues. Mitigation: Use docker-compose networking with service names.
- **Next Steps:**
  1. Assign owner for Docker/DevOps work.
  2. Draft Dockerfiles for each service (simulation, gateway, LLM).
  3. Add docker-compose orchestration with networking.
  4. Test multi-service startup and inter-service communication.
  5. Document usage in README.
- **Last Updated:** 2025-11-30

### 8.2.1 — Kubernetes Manifests & Docs (M8.2)
- **Description:** Define Kubernetes Deployments/Services/ConfigMaps/Ingress for simulation, gateway, and LLM services, plus supporting documentation.
- **Acceptance Criteria:** Manifests support local (Minikube) and staging deployments; exec doc explains setup mirroring existing Minikube patterns.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Container images, stable service ports and env contracts.
- **Risks & Mitigations:**
  - Risk: Overcomplicated manifests. Mitigation: Start minimal, iterate for staging/prod needs.
- **Next Steps:**
  1. Draft base manifests.
  2. Test on local K8s.
  3. Refine and document.
- **Last Updated:** 2025-11-29

### 8.3.1 — Observability in Kubernetes (M8.3)
- **Description:** Add Prometheus scraping, resource sizing, and basic load smoke tests for K8s deployments.
- **Acceptance Criteria:** Metrics scraped for all services; resource requests/limits tuned for expected load; smoke tests runnable via `kubectl` or scripts.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** K8s manifests and running cluster.
- **Risks & Mitigations:**
  - Risk: Mis-sized resources causing instability. Mitigation: Start conservative and adjust based on telemetry.
- **Next Steps:**
  1. Add ServiceMonitor/PodMonitor or annotations.
  2. Define load smoke test.
  3. Iterate on resource sizing.
- **Last Updated:** 2025-11-29

### 8.4.1 — Content Pipeline Tooling & CI (M8.4)
- **Description:** Implement content build tooling (`scripts/build_content.py`), CI validation hooks, and documentation so designers can author/test YAML and story seeds efficiently.
- **Acceptance Criteria:** Content build step produces artifacts consumed by simulation; CI validates content on change; designer workflow documented.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Stable content schema and directory structure.
- **Risks & Mitigations:**
  - Risk: Pipeline friction slows content iteration. Mitigation: Optimize for designer ergonomics, provide quick local commands.
- **Next Steps:**
  1. Implement build script.
  2. Wire into CI.
  3. Document designer workflow.
- **Last Updated:** 2025-11-29

### 9.1.1 — AI Observer Foundation Acceptance (M9.1)
- **GitHub Issue:** [#19](https://github.com/TheWizardsCode/GEngine/issues/19)
- **Description:** Ensure AI observer implementation and tooling fully meet M9.1 acceptance criteria across both local and service-mode sims, with tests and documentation.
- **Acceptance Criteria:** Observer connects via both SimEngine and SimServiceClient; generates structured JSON and optional natural language commentary; integration tests validate trend detection; README documents usage.
- **Priority:** Medium
- **Responsible:** gamedev-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** Stable simulation APIs and telemetry (✅ complete).
- **Risks & Mitigations:**
  - Risk: Observer outputs too verbose/noisy. Mitigation: Provide configurable output levels.
- **Completion Notes:**
  - **Acceptance Criteria Verified:**
    - ✅ Observer connects via both SimEngine and SimServiceClient
    - ✅ Generates structured JSON and optional natural language commentary
    - ✅ Integration tests validate trend detection (4 new SimServiceClient tests added)
    - ✅ README documents usage with comprehensive examples
  - **Bug Fix:** Fixed `_get_state()` to properly unwrap service response `data` field when using SimServiceClient
  - **Tests Added:** 4 new integration tests for SimServiceClient mode:
    - `test_observer_with_service_client_observes_ticks`
    - `test_observer_with_service_client_detects_trends`
    - `test_observer_with_service_client_generates_commentary`
    - `test_observer_with_service_client_json_output`
  - **README Enhanced:** Added remote SimServiceClient mode programmatic example with comprehensive trend detection and faction swing monitoring
  - **Total AI Observer Tests:** 37 tests (all passing)
- **Last Updated:** 2025-11-30

### 9.2.1 — Rule-Based AI Action Layer (M9.2)
- **Description:** Implement rule-based AI strategies and actor that submit intents, log decisions, and support deterministic 100-tick runs.
- **Acceptance Criteria:** Strategies (balanced/aggressive/diplomatic) implemented; AI actor submits valid intents and handles responses; regression test shows stabilization behavior; telemetry captures decision rationale.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Action routing, intent schema, observer foundation.
- **Risks & Mitigations:**
  - Risk: Rules overfit specific scenarios. Mitigation: Test across multiple configs and seeds.
- **Next Steps:**
  1. Design strategy rules.
  2. Implement actor integration.
  3. Add regression tests and telemetry fields.
- **Last Updated:** 2025-11-29

### 9.3.1 — LLM-Enhanced AI Decisions (M9.3)
- **Description:** Implement LLM-enhanced AI strategy layer that calls LLM service for complex choices with budget controls and fallbacks.
- **Acceptance Criteria:** Hybrid strategy routes routine actions to rules and complex choices to LLM; budget enforcement prevents runaway costs; scenario tests compare rule-only vs hybrid; telemetry distinguishes rule vs LLM decisions; docs cover prompts and trade-offs.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** LLM service integration, rule-based strategies.
- **Risks & Mitigations:**
  - Risk: LLM decisions nondeterministic or low quality. Mitigation: Constrain prompts, use structured outputs, log examples.
- **Next Steps:**
  1. Define LLM decision triggers and prompts.
  2. Implement hybrid strategy layer.
  3. Add scenario tests and telemetry.
- **Last Updated:** 2025-11-29

### 9.4.1 — AI Tournaments & Balance Tooling (M9.4)
- **Description:** Build AI tournament and analysis tooling to run many games in parallel and surface balance/anomaly reports.
- **Acceptance Criteria:** `run_ai_tournament.py` runs 100+ games with configurable strategies/worlds/seeds; `analyze_ai_games.py` produces comparative reports; docs describe workflow; CI integration runs nightly tournaments and archives results.
- **Priority:** Low
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Rule-based and/or hybrid AI strategies; telemetry for outcomes.
- **Risks & Mitigations:**
  - Risk: Tournament runs are resource-intensive. Mitigation: Allow configurable scales and sampling.
- **Next Steps:**
  1. Implement tournament runner and analysis scripts.
  2. Add reporting format.
  3. Integrate into CI for periodic runs.
- **Last Updated:** 2025-11-29


