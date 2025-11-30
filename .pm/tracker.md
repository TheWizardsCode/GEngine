# Project Task Tracker

**Last Updated:** 2025-11-29

| ID | Task | Status | Priority | Responsible | Updated |
|---:|---|---|---|---|---|
| 1.1.1 | Create Tracker Agent | completed | High | Ross (PM) | 2025-11-29 |
| 3.4.1 | Safeguards & LOD refresh follow-ups | not-started | High | TBD (ask Ross) | 2025-11-29 |
| 4.1.1 | Implement Agent AI subsystem (M4.1) | not-started | High | TBD (ask Ross) | 2025-11-29 |
| 4.2.1 | Implement Faction AI subsystem (M4.2) | not-started | High | TBD (ask Ross) | 2025-11-29 |
| 4.3.1 | Finalize Economy subsystem & tests (M4.3) | not-started | High | TBD (ask Ross) | 2025-11-29 |
| 4.4.1 | Complete Environment dynamics coverage (M4.4) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 4.5.1 | Finalize Tick orchestration & telemetry (M4.5) | not-started | High | TBD (ask Ross) | 2025-11-29 |
| 4.7.1 | Tune spatial adjacency & seed thresholds (M4.7) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 6.5.1 | Gateway ↔ LLM ↔ sim integration (M6.5) | not-started | High | TBD (ask Ross) | 2025-11-29 |
| 6.6.1 | Implement real LLM providers (M6.6) | not-started | High | TBD (ask Ross) | 2025-11-29 |
| 7.1.1 | Design & build progression systems (M7.1) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 7.3.1 | Tuning & replayability sweeps (M7.3) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 7.4.1 | Campaign UX flows (M7.4) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 8.1.1 | Containerization (Docker + compose) (M8.1) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 8.2.1 | Kubernetes manifests & docs (M8.2) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 8.3.1 | Observability in Kubernetes (M8.3) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 8.4.1 | Content pipeline tooling & CI (M8.4) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 9.1.1 | AI Observer foundation acceptance (M9.1) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 9.2.1 | Rule-based AI action layer (M9.2) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 9.3.1 | LLM-enhanced AI decisions (M9.3) | not-started | Medium | TBD (ask Ross) | 2025-11-29 |
| 9.4.1 | AI tournaments & balance tooling (M9.4) | not-started | Low | TBD (ask Ross) | 2025-11-29 |

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
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Existing SimEngine, headless driver, and config files; test infrastructure in place.
- **Risks & Mitigations:**
  - Risk: Guardrail behavior diverges between surfaces. Mitigation: Maintain a single source-of-truth config and verification matrix.
  - Risk: Profiling overhead impacts performance. Mitigation: Make profiling window/config adjustable and validate via sweeps.
- **Next Steps:**
  1. Review current `simulation.yml` limits and corresponding code paths.
  2. Implement shared profiling/performance block and extend summaries.
  3. Fill in or update regression matrix and associated tests.
  4. Update docs with guardrail tuning guidance.
- **Last Updated:** 2025-11-29

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
- **Description:** Implement skills, access tiers, and reputation systems that influence success rates and dialogue, integrated with existing metrics and narrative systems.
- **Acceptance Criteria:** Progression mechanics visible in gameplay surfaces; config-driven tuning; tests validate key progression flows.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Narrative director, agent/faction systems.
- **Risks & Mitigations:**
  - Risk: Progression overwhelms core simulation complexity. Mitigation: Start with minimal viable progression and iterate.
- **Next Steps:**
  1. Define progression model and data schema.
  2. Integrate with simulation outcomes and narrative.
  3. Add tests and basic documentation.
- **Last Updated:** 2025-11-29

### 7.3.1 — Tuning & Replayability Sweeps (M7.3)
- **Description:** Implement scenario sweeps, difficulty modifiers, and config exposure to tune pacing, difficulty, and replayability.
- **Acceptance Criteria:** Sweep scripts/configs exist; difficulty presets produce distinct experiences; analysis scripts compare difficulty profiles.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Stable core systems, story seeds, and telemetry.
- **Risks & Mitigations:**
  - Risk: Large sweep runs slow. Mitigation: Stage runs (smoke vs deep sweeps).
- **Next Steps:**
  1. Define difficulty presets and sweep configs.
  2. Implement sweep scripts.
  3. Add basic analysis tooling.
- **Last Updated:** 2025-11-29

### 7.4.1 — Campaign UX Flows (M7.4)
- **Description:** Refine UX flows for campaigns, autosaves, campaign picker, and end-of-run summaries in both CLI and gateway.
- **Acceptance Criteria:** Players can manage campaigns (start, resume, end) with autosaves; end-of-run flow cleanly surfaces post-mortems and summaries; responsibilities between services are clearly documented.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Snapshot persistence, post-mortem generator, CLI/gateway surfaces.
- **Risks & Mitigations:**
  - Risk: UX complexity confuses testers. Mitigation: Provide guided flows and documentation.
- **Next Steps:**
  1. Design campaign flow diagrams.
  2. Implement autosaves and campaign picker.
  3. Polish end-of-run UX and docs.
- **Last Updated:** 2025-11-29

### 8.1.1 — Containerization (Docker + Compose) (M8.1)
- **Description:** Create Dockerfiles and docker-compose configuration for simulation, gateway, and LLM services.
- **Acceptance Criteria:** All three services can be built and run via Docker/compose; basic README instructions exist; environment configuration is shared via env vars.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Reasonably stable service boundaries and configuration contracts.
- **Risks & Mitigations:**
  - Risk: Divergence between local and container configs. Mitigation: Use shared env var contracts and sample env files.
- **Next Steps:**
  1. Draft Dockerfiles for each service.
  2. Add docker-compose orchestration.
  3. Document usage.
- **Last Updated:** 2025-11-29

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
- **Description:** Ensure AI observer implementation and tooling fully meet M9.1 acceptance criteria across both local and service-mode sims, with tests and documentation.
- **Acceptance Criteria:** Observer connects via both SimEngine and SimServiceClient; generates structured JSON and optional natural language commentary; integration tests validate trend detection; README documents usage.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** Stable simulation APIs and telemetry.
- **Risks & Mitigations:**
  - Risk: Observer outputs too verbose/noisy. Mitigation: Provide configurable output levels.
- **Next Steps:**
  1. Review current observer implementation/tests.
  2. Close any gaps vs acceptance criteria.
  3. Update README with examples.
- **Last Updated:** 2025-11-29

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


