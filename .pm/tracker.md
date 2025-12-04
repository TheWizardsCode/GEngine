# Project Task Tracker

**Last Updated:** 2025-12-03T03:45:00Z

## Status Summary

**Recent Progress (since last update):**

- 🎉 **Phase 10.1 (Core Systems Test Coverage) COMPLETED** - GitHub Issue [#45](https://github.com/TheWizardsCode/GEngine/issues/45)
  - All child tasks 10.1.2–10.1.8 completed
  - Test count increased from 683 to 849 tests (+166 new tests)
  - Overall coverage at 90.95% (exceeds 90% threshold)
  - SimEngine coverage increased from 85% to 98%
  - AI/LLM coverage increased from 0-20% to 74-97%
  - No flaky tests introduced
  - Test coverage report updated with completion status
- 🎉 **Task 10.1.3 (SimEngine API Tests) COMPLETED**
  - 41 new tests for SimEngine public APIs, error paths, and progression integration
  - Tests cover director_feed, explanations API, progression helpers, and all error conditions
- 🎉 **Task 10.1.4 (FactionSystem RNG Decoupling) COMPLETED**
  - DeterministicRNG class for mock injection
  - State transitions verified against configuration values
  - No more brittle magic seed dependencies
- 🎉 **Task 10.1.5 (Persistence Fidelity) COMPLETED**
  - 17 new round-trip tests for save/load cycles
  - All subsystems covered: city, factions, agents, environment, progression
  - Backwards compatibility tests included
- 🎉 **Task 10.1.6 (Integration Scenarios) COMPLETED**
  - 7 cross-system integration tests
  - Scenarios cover unrest cascades, scarcity, faction rivalry, feedback loops
  - Marked with @integration and @slow for selective execution
- 🎉 **Task 10.1.7 (Performance Guardrails) COMPLETED**
  - 14 tests for tick limits (engine, CLI, service)
  - Timing tests with generous thresholds
  - Marked with @slow for selective execution
- 🎉 **Task 10.1.8 (AI/LLM Mocking) COMPLETED**
  - 78 new tests with ConfigurableMockProvider and AIPlayerMockProvider
  - Gateway ↔ LLM ↔ Simulation flow fully tested
  - CI-friendly: no external API calls required
- 🎉 **Task 8.4.1 (Content Pipeline Tooling & CI) COMPLETED** - GitHub Issue [#23](https://github.com/TheWizardsCode/GEngine/issues/23)
  - Content build script (`scripts/build_content.py`) validates worlds, configs, and sweeps
  - CI workflow (`.github/workflows/content-validation.yml`) runs on content file changes
  - Designer workflow documented in `docs/gengine/content_designer_workflow.md`
  - 17 tests covering all validation paths, all passing
  - Clear error messages with entity reference validation
- 🎉 **Task 10.1.2 (Strengthen AgentSystem Tests) COMPLETED**
  - Refactored `AgentSystem` to extract scoring logic for testability.
  - Added unit tests verifying trait influence (empathy, cunning, resolve) on decision scoring.
  - Added tests for environment modifier influence and edge cases (missing data, no options).
  - Updated test coverage report.
- 🎉 **Task 8.3.3 (K8s Resource Sizing & Tuning) COMPLETED** - GitHub Issue [#33](https://github.com/TheWizardsCode/GEngine/issues/33)
  - Differentiated resource allocations for simulation, gateway, and LLM services
  - Base manifests updated with workload-appropriate requests/limits
  - Local overlay sized for Minikube (~50% of base)
  - Staging overlay sized for production-like testing (~2x base)
  - Documentation added with "Resource Sizing" section explaining rationale and tuning methodology
- 🎉 **Task 8.3.1 (Observability in Kubernetes) COMPLETED** - GitHub Issue [#22](https://github.com/TheWizardsCode/GEngine/issues/22)
  - Prometheus annotations added to all deployment manifests (simulation, gateway, llm)
  - ServiceMonitor resources for Prometheus Operator integration
  - Kubernetes smoke test script (`scripts/k8s_smoke_test.sh`) with health/metrics validation
  - Documentation updated with monitoring and troubleshooting sections
  - All acceptance criteria met for metrics scraping, smoke tests, and documentation
- 🎉 **Task 9.2.1 (Rule-Based AI Action Layer) COMPLETED** - GitHub Issue [#24](https://github.com/TheWizardsCode/GEngine/issues/24)
  - Strategies module with BalancedStrategy, AggressiveStrategy, DiplomaticStrategy
  - Actor module for action selection and submission via intent API
  - Telemetry captures decision rationale, priority, and state snapshots
  - 75 new tests (41 strategies + 34 actor), 112 total AI player tests
  - Documentation updated in README and implementation plan
  - Unblocks Task 9.3.1 (LLM-Enhanced AI Decisions)
- 🎉 **Task 8.2.1 (Kubernetes Manifests & Docs) COMPLETED** - GitHub Issue #21
  - Kubernetes manifests directory (`k8s/`) with base and overlay structure
  - Base manifests: namespace, configmap, deployments, services, ingress for all 3 services
  - Local overlay: Minikube-friendly with NodePort services (30000, 30100, 30001)
  - Staging overlay: Higher resource limits, ingress, Always pull policy
  - Executable documentation following existing Minikube patterns
  - Verification steps with health checks and troubleshooting guide
- 🎉 **Task 7.1.3 (Enable Per-Agent Modifiers) COMPLETED** - GitHub Issue [#25](https://github.com/TheWizardsCode/GEngine/issues/25)
  - Ran difficulty sweeps with modifiers enabled across all 5 presets
  - Validated balance: metrics identical before/after (no destabilization)
  - Updated config to set `enable_per_agent_modifiers: true`
  - Documented findings in gameplay guide Section 11.4
  - All 523 tests pass with modifiers enabled
- 🎉 **Task 7.1.2 (Per-Agent Progression) COMPLETED** - GitHub Issue [#17](https://github.com/TheWizardsCode/GEngine/issues/17)
  - AgentProgressionState model with specialization, expertise, reliability, stress
  - GameState integration with migration-safe defaults
  - ProgressionSystem processes agent_actions with agent_id
  - 43 comprehensive tests (all passing)
  - Configuration in simulation.yml with per_agent_progression section
  - Documentation updated in gameplay guide and implementation plan
- 🎉 **Task 9.1.1 (AI Observer Foundation) COMPLETED** - GitHub Issue [#19](https://github.com/TheWizardsCode/GEngine/issues/19)
  - Fixed bug in Observer._get_state() for service mode data unwrapping
  - Added 4 new integration tests for SimServiceClient mode
  - Enhanced README with comprehensive service mode examples
  - All acceptance criteria verified and met
  - Unblocks Task 9.2.1 (Rule-Based AI Action Layer)
- 🎉 **Phase 8 Containerization** - Tasks 8.1.1 and 8.2.1 COMPLETED!
  - ✅ Task 8.1.1 (Containerization) completed via PR #16 (Issue #15)
  - ✅ Task 8.2.1 (Kubernetes Manifests) completed
  - Multi-stage Dockerfile supporting simulation, gateway, and LLM services
  - docker-compose.yml orchestrating all services on shared network
  - Container smoke test script at `scripts/smoke_test_containers.sh` (all checks passing)
  - Full Python test suite passes (523 tests, 0 failures)
- 🎉 **Phase 7 COMPLETE** - All player experience features shipped!
  - ✅ Task 7.4.1 (Campaign UX) completed and merged via PR #14
  - ✅ Task 7.1.1 (Progression Systems) completed and merged via PR #12
  - ✅ Task 7.1.2 (Per-Agent Progression Layer) completed
  - ✅ Task 7.1.3 (Enable Per-Agent Modifiers) completed
  - ✅ Task 7.3.1 (Tuning & Replayability) completed
  - ✅ Task 7.2.1 (Explanations) completed
  - 📋 Issues #11, #13, #17, #25 closed
  

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

1. 🚀 **Phase 8 Deployment** - Nearly complete! Only K8s validation CI (8.3.2) remains
2. ✅ **Phase 10 Test Coverage** - COMPLETE! All child tasks 10.1.2–10.1.8 completed, 849 tests at 90.95% coverage
3. 🤖 **Phase 9 AI Testing** - Observer (9.1.1) and action layer (9.2.1) complete, LLM-enhanced (9.3.1) ready to start

**Recommended Next 3 Parallel Tasks:**

1. **9.3.1 - LLM-Enhanced AI Decisions** (Priority: MEDIUM, Effort: High) - Issue [#34](https://github.com/TheWizardsCode/GEngine/issues/34)
   - Why: Builds on completed AI foundation (9.1.1, 9.2.1) and new mock testing infrastructure (10.1.8)
   - Owner needed: AI/ML-focused agent with LLM experience
   - Parallelizable: AI/ML work, independent of deployment work
   - Impact: Enables advanced AI testing capabilities
   - Estimated time: 3-5 days

2. **8.3.2 - K8s Validation CI Job** (Priority: MEDIUM, Effort: Medium) - Issue [#31](https://github.com/TheWizardsCode/GEngine/issues/31)
   - Why: Catch K8s manifest errors early in CI
   - Owner needed: DevOps agent
   - Parallelizable: Independent CI work
   - Impact: Better deployment safety
   - Estimated time: 1-2 days

3. **9.4.1 - AI Tournaments & Balance Tooling** (Priority: LOW, Effort: High)
   - Why: Builds on completed AI action layer (9.2.1)
   - Owner needed: Gamedev agent
   - Parallelizable: Independent tooling work
   - Impact: Balance validation and AI testing at scale
   - Estimated time: 3-5 days

**Key Risks:**

- 🟡 **K8s CI validation missing** - Task 8.3.2 still pending but lower priority now that Phase 8 core is complete
- ⚠️ **Phase 9 LLM enhancement ready** - Rule-based AI complete, LLM-enhanced (9.3.1) unblocked but needs owner
- ✅ **Phase 8 deployment complete** - All core tasks done (8.1.1, 8.2.1, 8.3.1, 8.3.3, 8.4.1, metrics); only CI automation pending
- ✅ **Phase 10 test coverage COMPLETE** - Epic 10.1.1 and all child tasks (10.1.2–10.1.8) completed; 849 tests at 90.95% coverage
- ✅ **Phase 7 delivery risk eliminated** - All core player features complete and tested, per-agent modifiers enabled by default
- ✅ **Repository hygiene excellent** - Issues #23, #43, #45 addressed; clean issue backlog with clear priorities

|    ID | Task                                            | Status      | Priority | Responsible        | Updated    |
| ----: | ----------------------------------------------- | ----------- | -------- | ------------------ | ---------- |
| 1.1.1 | Create Tracker Agent                            | completed   | High     | Ross (PM)          | 2025-11-30 |
| 3.4.1 | Safeguards & LOD refresh follow-ups             | completed   | High     | Gamedev Agent      | 2025-11-30 |
| 4.1.1 | Implement Agent AI subsystem (M4.1)             | completed   | High     | Team               | 2025-11-30 |
| 4.2.1 | Implement Faction AI subsystem (M4.2)           | completed   | High     | Team               | 2025-11-30 |
| 4.3.1 | Finalize Economy subsystem & tests (M4.3)       | completed   | High     | Team               | 2025-11-30 |
| 4.4.1 | Complete Environment dynamics coverage (M4.4)   | completed   | Medium   | Team               | 2025-11-30 |
| 4.5.1 | Finalize Tick orchestration & telemetry (M4.5)  | completed   | High     | Team               | 2025-11-30 |
| 4.7.1 | Tune spatial adjacency & seed thresholds (M4.7) | completed   | Medium   | Team               | 2025-11-30 |
| 5.1.1 | Story seed schema & loading (M5.1)              | completed   | High     | Team               | 2025-11-30 |
| 5.2.1 | Director hotspot analysis (M5.2)                | completed   | High     | Team               | 2025-11-30 |
| 5.3.1 | Director pacing & lifecycle (M5.3)              | completed   | High     | Team               | 2025-11-30 |
| 5.4.1 | Post-mortem generator (M5.4)                    | completed   | Medium   | Team               | 2025-11-30 |
| 6.1.1 | Gateway service (M6.1)                          | completed   | High     | Team               | 2025-11-30 |
| 6.3.1 | LLM service skeleton (M6.3)                     | completed   | High     | Team               | 2025-11-30 |
| 6.5.1 | Gateway ↔ LLM ↔ sim integration (M6.5)          | completed   | High     | Team               | 2025-11-30 |
| 6.6.1 | Implement real LLM providers (M6.6)             | completed   | High     | Team               | 2025-11-30 |
| 7.1.1 | Design & build progression systems (M7.1)       | completed   | High     | gamedev-agent      | 2025-11-30 |
| 7.1.2 | Implement per-agent progression layer (M7.1.x)  | completed   | Low      | gamedev-agent      | 2025-12-01 |
| 7.1.3 | Default per-agent success modifiers to enabled  | completed   | Medium   | gamedev-agent      | 2025-12-01 |
| 7.2.1 | Explanations & causal queries (M7.2)            | completed   | High     | Team               | 2025-11-30 |
| 7.3.1 | Tuning & replayability sweeps (M7.3)            | completed   | High     | Gamedev Agent      | 2025-11-30 |
| 7.4.1 | Campaign UX flows (M7.4)                        | completed   | Medium   | gamedev-agent      | 2025-11-30 |
| 8.1.1 | Containerization (Docker + compose) (M8.1)      | completed   | High     | copilot            | 2025-12-01 |
| 8.2.1 | Kubernetes manifests & docs (M8.2)              | completed   | Medium   | devops-agent       | 2025-12-01 |
| 8.3.1 | Observability in Kubernetes (M8.3)              | completed   | Medium   | devops-infra-agent | 2025-12-01 |
| 8.3.2 | K8s Validation CI Job (M8.3.x)                  | not-started | Medium   | TBD (ask Ross)     | 2025-12-03 |
| 8.3.3 | K8s Resource Sizing & Tuning (M8.3.y)           | completed   | Medium   | devops-agent       | 2025-12-02 |
| 8.3.4 | Gateway/LLM Prometheus Metrics (M8.3.x)         | completed   | Medium   | copilot            | 2025-12-03 |
| 8.3.5 | Integrate K8s Smoke Test into CI (M8.3.x)       | not-started | Low      | TBD (ask Ross)     | 2025-12-03 |
| 8.4.1 | Content pipeline tooling & CI (M8.4)            | completed   | Medium   | devops-agent       | 2025-12-02 |
| 9.1.1 | AI Observer foundation acceptance (M9.1)        | completed   | Medium   | gamedev-agent      | 2025-11-30 |
| 9.2.1 | Rule-based AI action layer (M9.2)               | completed   | Medium   | gamedev-agent      | 2025-12-01 |
| 9.3.1 | LLM-enhanced AI decisions (M9.3)                | not-started | Medium   | TBD (ask Ross)     | 2025-11-30 |
| 9.4.1 | AI tournaments & balance tooling (M9.4)         | not-started | Low      | TBD (ask Ross)     | 2025-11-30 |

| 10.1.1 | Core systems test coverage improvements (epic) | completed | High | Test Agent | 2025-12-03 |
| 10.1.2 | Strengthen AgentSystem decision logic tests | completed | High | Test Agent | 2025-12-03 |
<<<<<<< HEAD
| 10.1.3 | Expand SimEngine API and error-path tests | completed | High | Test Agent | 2025-12-03 |
| 10.1.4 | Stabilize FactionSystem tests (decouple RNG) | completed | Medium | Test Agent | 2025-12-03 |
| 10.1.5 | Persistence save/load fidelity tests | completed | Medium | Test Agent | 2025-12-03 |
| 10.1.6 | Cross-system integration scenario tests | completed | Medium | Test Agent | 2025-12-03 |
| 10.1.7 | Performance and tick-limit regression tests | completed | Low | Test Agent | 2025-12-03 |
| 10.1.8 | AI/LLM mocking and coverage for gateways | completed | Medium | Test Agent | 2025-12-03 |
=======
| 10.1.3 | Expand SimEngine API and error-path tests | not-started | High | Test Agent | 2025-12-03 |
| 10.1.4 | Stabilize FactionSystem tests (decouple RNG) | not-started | Medium | Test Agent | 2025-12-02 |
| 10.1.5 | Persistence save/load fidelity tests | not-started | Medium | Test Agent | 2025-12-02 |
| 10.1.6 | Cross-system integration scenario tests | not-started | Medium | Test Agent | 2025-12-02 |
| 10.1.7 | Performance and tick-limit regression tests | not-started | Low | Test Agent | 2025-12-02 |
| 10.1.8 | AI/LLM mocking and coverage for gateways | not-started | Medium | Test Agent | 2025-12-02 |
| 10.2.1 | Harden difficulty sweep runtime & monitoring | not-started | Low | Gamedev Agent | 2025-12-02 |
| 10.2.2 | AI player LLM robustness & failure telemetry | not-started | Low | Gamedev Agent | 2025-12-02 |
>>>>>>> origin/main

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

### 7.1.2 — Implement Per-Agent Progression Layer (M7.1.x)
- **GitHub Issue:** [#17](https://github.com/TheWizardsCode/GEngine/issues/17) - CLOSED
- **Description:** Implement the per-agent progression layer described in GDD §4.1.1 and the implementation plan (M7.1.x), adding a lightweight `AgentProgressionState` keyed by `agent_id` on top of the existing global `ProgressionState`. Wire it into `GameState`, `ProgressionSystem.tick(...)`, configuration, and minimal CLI/service surfaces while keeping effects bounded and optional.
- **Acceptance Criteria:**
  - ✅ `AgentProgressionState` model exists with specialization, expertise pips, reliability, stress, and mission counters.
  - ✅ `GameState` can persist and restore `agent_progression` without breaking old snapshots.
  - ✅ `ProgressionSystem` updates per-agent state when `agent_actions` include `agent_id`, without changing existing global progression behavior.
  - ✅ New config knobs in `simulation.yml` control expertise/stress/reliability deltas and max bonus/penalty envelope.
  - ✅ Optional success-modifier wrapper for per-agent bonuses is gated behind a config flag (`enable_per_agent_modifiers`).
  - ✅ At least a couple of CLI/service/explanation surfaces can display basic per-agent summaries.
  - ✅ Tests cover model behavior, tick integration, and snapshot round-tripping (43 new tests).
- **Priority:** Low
- **Responsible:** gamedev-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** 7.1.1 (global progression systems), Phase 4 agent system, stable `agent_actions` payloads.
- **Completion Notes:**
  - **Per-Agent Progression Model** (`src/gengine/echoes/core/progression.py`):
    - `AgentSpecialization` enum: negotiator, investigator, analyst, operator, influencer
    - `AgentProgressionState` model: specialization, expertise (0-5 pips), reliability (0-1), stress (0-1)
    - Mission tracking: total_missions, successful_missions, hazardous_actions
  - **GameState Integration** (`src/gengine/echoes/core/state.py`):
    - Optional `agent_progression: Dict[str, AgentProgressionState]` field
    - Helper methods: `ensure_agent_progression()`, `get_agent_progression()`
    - Migration-safe defaults for backward compatibility
  - **ProgressionSystem Updates** (`src/gengine/echoes/systems/progression.py`):
    - Processes `agent_actions` with `agent_id` field
    - Updates expertise based on mission outcomes
    - Tracks stress for hazardous actions
    - Calculates reliability from success rate
  - **Success Modifier Integration**:
    - `calculate_agent_modifier()` combines global + per-agent bonuses
    - Gated behind `enable_per_agent_modifiers` config flag (currently `false`)
  - **Configuration** (`content/config/simulation.yml`):
    - New `per_agent_progression` section with tunable parameters
    - Expertise gain/loss rates, stress accumulation/decay, reliability tracking
  - **Test Coverage**: 43 new tests in `tests/echoes/test_progression.py`
    - Model tests for AgentProgressionState
    - System tests for tick processing and agent tracking
    - Integration tests for GameState persistence
    - Scenario tests for progression over time
  - **Documentation**: Updated `docs/gengine/how_to_play_echoes.md` with:
    - Section 11.4: Per-Agent Progression
    - Specialization descriptions
    - Expertise pip mechanics
    - Stress and reliability tracking
  - **Note:** Task 7.1.3 completed to enable per-agent modifiers by default

### 7.1.3 — Enable Per-Agent Success Modifiers by Default (M7.1.x)
- **GitHub Issue:** [#25](https://github.com/TheWizardsCode/GEngine/issues/25)
- **Description:** Enable per-agent progression modifiers by default in `content/config/simulation.yml` after validating balance through scenario testing.
- **Acceptance Criteria:**
  - ✅ Run scenario tests with `enable_per_agent_modifiers: true` across all difficulty presets
  - ✅ Validate that per-agent bonuses/penalties don't destabilize difficulty balance
  - ✅ Update `content/config/simulation.yml` to set `enable_per_agent_modifiers: true`
  - ✅ Document any observed balance impacts in gameplay guide
  - ✅ All existing tests pass with modifiers enabled
- **Priority:** Medium
- **Responsible:** gamedev-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** 7.1.2 (Per-Agent Progression Layer), 7.3.1 (Difficulty Sweeps)
- **Completion Notes:**
  - **Scenario Testing:** Ran difficulty sweeps with `enable_per_agent_modifiers: true` across all 5 presets
  - **Balance Validation:** Compared before/after results - metrics identical across all difficulty levels
    - Stability, unrest, pollution, anomalies, and suppressed events unchanged
    - The ±10% bonus/penalty envelope is intentionally small to avoid destabilizing balance
  - **Configuration Update:** Set `enable_per_agent_modifiers: true` in `content/config/simulation.yml`
  - **Documentation:** Updated `docs/gengine/how_to_play_echoes.md` Section 11.4 with:
    - Config example now shows `enable_per_agent_modifiers: true`
    - Added note explaining scenario testing confirmed balance stability
  - **Test Results:** All 523 tests pass with modifiers enabled

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

### 8.1.1 — Containerization (Docker + Compose) (M8.1)
- **GitHub Issue:** [#15](https://github.com/TheWizardsCode/GEngine/issues/15)
- **GitHub PR:** [#16](https://github.com/TheWizardsCode/GEngine/pull/16)
- **Description:** Create Dockerfiles and docker-compose configuration for simulation, gateway, and LLM services.
- **Acceptance Criteria:** All three services can be built and run via Docker/compose; basic README instructions exist; environment configuration is shared via env vars.
- **Priority:** High
- **Responsible:** copilot
- **Status:** ✅ COMPLETED
- **Completion Notes:**
  - **Dockerfile**: Multi-stage build with Python 3.12 + uv:
    - Single image supporting all services via `SERVICE` env var
    - Non-root user for security
    - Development stage with dev dependencies
  - **docker-compose.yml**: Service orchestration:
    - simulation (8000), gateway (8100), llm (8001)
    - Bridge network with service-name DNS
    - Health checks, dependency ordering, content volume mount
  - **.env.sample**: Documented environment variable contracts
  - **README.md**: Docker usage section with quick start, configuration, development mode
  - **Container Smoke Tests**: `scripts/smoke_test_containers.sh`:
    - Builds Docker images
    - Starts all services via compose
    - Polls /healthz endpoints with timeout
    - Verifies HTTP 200 responses
    - Cleans up on completion
  - **Test Coverage**: Full Python suite passes (476 tests, 0 failures)
- **Dependencies:** Stable service boundaries (✅ Phase 6 complete), configuration contracts (✅ complete).
- **Risks & Mitigations:**
  - Risk: Divergence between local and container configs. Mitigation: Use shared env var contracts and sample env files.
  - Risk: Port conflicts or networking issues. Mitigation: Use docker-compose networking with service names.
- **Current Status:** In progress (implementation under review in PR #16; all Python tests passing via `uv run --group dev pytest`).
- **Completion Notes (so far):**
  - Dockerfile added with multi-stage `uv`-based build and a single image parameterized by `SERVICE` env var to run simulation, gateway, or LLM services.
  - `docker-compose.yml` added to orchestrate `simulation` (8000), `gateway` (8100), and `llm` (8001) services on a shared network with service-name-based URLs.
  - `.env.sample` added documenting shared env var contracts between services.
  - README updated with Docker usage and health-check examples.
- **Next Steps:**
  1. Assign owner for Docker/DevOps work and merge PR #16 after review/CI.
  2. Add a container smoke test that builds the image, runs `docker compose up -d`, and verifies `/healthz` endpoints for simulation, gateway, and LLM.
  3. Flip Task 8.1.1 to COMPLETED in `.pm/tracker.md` once containers are smoke-tested and merged.

### 8.2.1 — Kubernetes Manifests & Docs (M8.2)
- **GitHub Issue:** [#21](https://github.com/TheWizardsCode/GEngine/issues/21)
- **Description:** Define Kubernetes Deployments/Services/ConfigMaps/Ingress for simulation, gateway, and LLM services, plus supporting documentation.
- **Acceptance Criteria:** Manifests support local (Minikube) and staging deployments; exec doc explains setup mirroring existing Minikube patterns.
- **Priority:** Medium
- **Responsible:** devops-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** Container images, stable service ports and env contracts.
- **Risks & Mitigations:**
  - Risk: Overcomplicated manifests. Mitigation: Start minimal, iterate for staging/prod needs.
- **Completion Notes:**
  - **Kubernetes Manifests** (`k8s/base/`):
    - `namespace.yaml`: Dedicated gengine namespace with standard labels
    - `configmap.yaml`: Shared configuration for all services with K8s DNS URLs
    - `simulation-deployment.yaml` & `simulation-service.yaml`: Core simulation (port 8000)
    - `gateway-deployment.yaml` & `gateway-service.yaml`: WebSocket gateway (port 8100)
    - `llm-deployment.yaml` & `llm-service.yaml`: LLM processor (port 8001)
    - `ingress.yaml`: NGINX ingress for external access
    - `kustomization.yaml`: Base kustomization with common labels
  - **Environment Overlays** (`k8s/overlays/`):
    - `local/kustomization.yaml`: Minikube overlay with NodePort services (30000, 30100, 30001), imagePullPolicy: Never
    - `staging/kustomization.yaml`: Staging overlay with higher resource limits, ingress, imagePullPolicy: Always
  - **Resource Configuration**:
    - Local: 256Mi/250m requests, 512Mi/500m limits
    - Staging: 512Mi/500m requests, 1Gi/1000m limits
  - **Health Probes**: Readiness and liveness probes on /healthz for all services
  - **Documentation** (`docs/gengine/Deploy_GEngine_To_Kubernetes.md`):
    - Executable document following existing Minikube patterns
    - Prerequisites, environment setup, deployment steps
    - Verification section with health checks and API tests
    - Troubleshooting guide for common issues
    - Cleanup instructions


### 8.3.1 — Observability in Kubernetes (M8.3)
- **GitHub Issue:** [#22](https://github.com/TheWizardsCode/GEngine/issues/22)
- **Description:** Add Prometheus scraping, resource sizing, and basic load smoke tests for K8s deployments.
- **Acceptance Criteria:** Metrics scraped for all services; resource requests/limits tuned for expected load; smoke tests runnable via `kubectl` or scripts.
- **Priority:** Medium
- **Responsible:** devops-infra-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** K8s manifests (✅ 8.2.1 complete) and running cluster.
- **Risks & Mitigations:**
  - Risk: Mis-sized resources causing instability. Mitigation: Start conservative and adjust based on telemetry.
- **Completion Notes:**
  - **Prometheus Annotations** (`k8s/base/`):
    - Added `prometheus.io/scrape: "true"` to all deployment manifests
    - Added `prometheus.io/port` for each service (8000, 8100, 8001)
    - Added `prometheus.io/path` annotations (/metrics for simulation, /healthz for gateway/llm)
  - **ServiceMonitor Resources** (`k8s/base/servicemonitor.yaml`):
    - Created ServiceMonitor resources for Prometheus Operator integration
    - Optional inclusion via kustomization.yaml (commented by default)
  - **Kubernetes Smoke Test** (`scripts/k8s_smoke_test.sh`):
    - Pod health checks and status verification
    - Health and metrics endpoint validation
    - Prometheus annotation verification
    - Optional load testing with `--load` flag
  - **Documentation** (`docs/gengine/Deploy_GEngine_To_Kubernetes.md`):
    - Added Monitoring and Observability section
    - Prometheus scraping verification steps
    - ServiceMonitor/Prometheus Operator integration guide
    - Troubleshooting for metrics issues
- **Resource Sizing Status:** This PR does **not** change Kubernetes resource `requests`/`limits`; existing manifest resource settings remain as they were in 8.2.1. As a result, this work fully covers observability (Prometheus annotations, ServiceMonitors) and Kubernetes smoke tests, but **only partially** addresses the original “resource sizing” acceptance criterion. Resource tuning for expected load will be completed in a follow-up task/PR.
- **Last Updated:** 2025-12-01

### 8.3.2 — K8s Validation CI Job (M8.3.x)
- **GitHub Issue:** [#31](https://github.com/TheWizardsCode/GEngine/issues/31)
- **Description:** Add a dedicated CI job that validates Kubernetes manifests using `kubectl apply --dry-run=server` for both base and overlays, plus automated linting with kube-linter or kubeconform to catch misconfigurations before deployment.
- **Acceptance Criteria:** 
  - CI workflow validates all manifests under `k8s/base` and `k8s/overlays/*` with `kubectl apply --dry-run=server -k`
  - K8s linter (kube-linter or kubeconform) runs on all manifests with reasonable ruleset
  - Validation failures block PR merge
  - Documentation explains validation workflow and how to run locally
  - Workflow runs on K8s manifest changes (paths: `k8s/**/*.yaml`, `.github/workflows/k8s-*.yml`)
- **Priority:** High
- **Responsible:** TBD (ask Ross)
- **Dependencies:** K8s manifests (✅ 8.2.1 complete), CI infrastructure
- **Risks & Mitigations:**
  - Risk: Bad manifests or misconfigurations take down deployment despite green unit tests. Mitigation: Server-side dry-run catches deployment-time errors early.
  - Risk: K8s validation adds significant CI time. Mitigation: Run only on manifest changes, use fast linter like kubeconform.
  - Risk: False positives from overly strict linting. Mitigation: Start with default ruleset, tune based on team feedback.
- **Next Steps:**
  1. Create `.github/workflows/k8s-validation.yml` workflow
  2. Set up kubectl with a K8s version matching production/staging (e.g., kind cluster or k3s)
  3. Add validation steps for base + all overlays (local, staging)
  4. Integrate kube-linter or kubeconform with reasonable defaults
  5. Document local validation workflow in K8s deployment docs
  6. Test workflow with intentional manifest errors to verify blocking behavior
- **Rationale:** A bad K8s manifest or misconfigured deployment can bring down the entire system even when all unit/integration tests pass. These issues easily slip through without automation. Catching K8s breakage early in CI protects every environment and typically delivers the best reliability gain per unit of effort.
- **Last Updated:** 2025-12-01

### 8.3.3 — K8s Resource Sizing & Tuning (M8.3.y)
- **GitHub Issue:** [#33](https://github.com/TheWizardsCode/GEngine/issues/33)
- **Description:** Complete the resource sizing acceptance criterion from task 8.3.1 by tuning Kubernetes resource requests/limits based on smoke test data and expected load patterns. Update manifests for all three services (simulation, gateway, LLM) in both base and overlay configurations.
- **Acceptance Criteria:**
  - ✅ Resource `requests` and `limits` tuned for simulation, gateway, and LLM services
  - ✅ Settings based on smoke test observations and expected load patterns
  - ✅ Both base and overlay configs updated (local/staging)
  - ✅ Documentation explains resource rationale and tuning methodology
  - ✅ Smoke tests validate updated resource constraints don't cause instability
- **Priority:** Medium
- **Responsible:** devops-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** 8.3.1 smoke test data (✅ complete)
- **Completion Notes:**
  - **Base Manifest Updates** (`k8s/base/`):
    - Simulation: 384Mi/300m requests, 768Mi/750m limits (highest - game logic, tick processing)
    - Gateway: 192Mi/150m requests, 384Mi/400m limits (lowest - WebSocket routing)
    - LLM: 320Mi/200m requests, 640Mi/500m limits (memory-focused for context)
  - **Local Overlay** (`k8s/overlays/local/`):
    - ~50% of base resources for Minikube compatibility
    - Simulation: 256Mi/200m requests, 512Mi/500m limits
    - Gateway: 128Mi/100m requests, 256Mi/250m limits
    - LLM: 192Mi/100m requests, 384Mi/300m limits
  - **Staging Overlay** (`k8s/overlays/staging/`):
    - ~2x base resources for production-like load testing
    - Simulation: 768Mi/600m requests, 1536Mi/1500m limits
    - Gateway: 384Mi/300m requests, 768Mi/800m limits
    - LLM: 640Mi/400m requests, 1280Mi/1000m limits
  - **Documentation** (`docs/gengine/Deploy_GEngine_To_Kubernetes.md`):
    - Added comprehensive "Resource Sizing" section
    - Service resource profiles and workload characteristics
    - Default allocations table for all environments
    - Sizing methodology explanation
    - Tuning guidelines and common scenarios
- **Last Updated:** 2025-12-02
- **Rationale:** Task 8.3.1 deferred resource tuning to keep the observability PR focused. Completing this work ensures production deployments are properly sized to prevent resource exhaustion or pod instability.
- **Estimated Effort:** 4-6 hours
- **Last Updated:** 2025-12-01

### 8.3.4 — Gateway/LLM Prometheus Metrics (M8.3.x)
- **GitHub Issue:** [#39](https://github.com/TheWizardsCode/GEngine/issues/39) - **COMPLETED**
- **Description:** Expose true Prometheus-style metrics for the gateway and LLM services (separate from `/healthz`), and update annotations/ServiceMonitors to scrape those endpoints.
- **Acceptance Criteria:**
  - ✅ Gateway service exposes a `/metrics` endpoint with key HTTP/latency/error/LLM-call metrics.
  - ✅ LLM service exposes a `/metrics` endpoint with request counts, latencies, error breakdowns, and provider-level stats.
  - ✅ Implementation uses `prometheus_client` library for standard Prometheus format.
  - ✅ Tests added for metrics endpoint functionality.
- **Priority:** Medium
- **Responsible:** copilot
- **Dependencies:** Existing gateway/LLM services, Prometheus annotations and ServiceMonitor wiring from 8.3.1.
- **Status:** COMPLETED via commit 659f19c (merged 2025-12-03)
- **Last Updated:** 2025-12-03

### 8.3.5 — Integrate K8s Smoke Test into CI (M8.3.x)
- **Description:** Integrate the Kubernetes smoke test script (`scripts/k8s_smoke_test.sh`) into the automated testing workflow so that basic cluster health and metrics checks run in CI or a gated pipeline.
- **Acceptance Criteria:**
  - A CI job runs `scripts/k8s_smoke_test.sh` (or an adapted variant) against a disposable or shared test cluster on demand (e.g., nightly or on `main`).
  - Failures in the smoke test job clearly surface in CI and block the pipeline for that environment.
  - The job is scoped so it does not run on every PR by default (to avoid heavy K8s usage), but is easily triggerable (e.g., on `main`, nightly, or with a label).
  - Documentation explains when/how the smoke tests run in CI and how to invoke them locally with the same settings.
- **Priority:** Medium
- **Responsible:** TBD (ask Ross)
- **Dependencies:** K8s manifests (✅ 8.2.1 complete), observability (✅ 8.3.1 complete), CI infrastructure capable of reaching a test cluster.
- **Risks & Mitigations:**
  - Risk: Running smoke tests against real clusters is slow or flaky. Mitigation: Start with targeted, low-frequency runs (nightly or on `main`) and use generous timeouts.
  - Risk: K8s cluster credentials/contexts in CI are hard to manage. Mitigation: Reuse existing cluster access patterns; document any secrets/config needed.
- **Next Steps:**
  1. Decide on the triggering policy for smoke tests (nightly, `main` only, or manual).
  2. Create a CI workflow (e.g., `.github/workflows/k8s-smoke-test.yml`) that provisions KUBECONFIG/namespace and calls `scripts/k8s_smoke_test.sh` with appropriate flags.
  3. Ensure logs from the smoke test script are captured and surfaced in CI for debugging.
  4. Update K8s deployment docs to describe the CI smoke test job and how to replicate it locally.
- **Last Updated:** 2025-12-01

### 8.4.1 — Content Pipeline Tooling & CI (M8.4)
- **GitHub Issue:** [#23](https://github.com/TheWizardsCode/GEngine/issues/23)
- **Description:** Implement content build tooling (`scripts/build_content.py`), CI validation hooks, and documentation so designers can author/test YAML and story seeds efficiently.
- **Acceptance Criteria:**
  - ✅ Content build step produces artifacts consumed by simulation
  - ✅ CI validates content on change (schema, references, integrity)
  - ✅ Designer workflow documented
  - ✅ Clear error messages for content validation failures
- **Priority:** Medium
- **Responsible:** devops-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** Stable content schema and directory structure (✅ complete).
- **Risks & Mitigations:**
  - Risk: Pipeline friction slows content iteration. Mitigation: Optimize for designer ergonomics, provide quick local commands.
- **Completion Notes:**
  - **Build Script** (`scripts/build_content.py`):
    - Validates world definitions (`world.yml` and `story_seeds.yml`) with entity reference checking
    - Validates simulation configuration (`simulation.yml`) against Pydantic schema
    - Validates difficulty sweep configurations (`content/config/sweeps/*/`)
    - Outputs JSON manifest with validation results and file lists
    - Clear error messages with icons (❌/✓) and bullet-point formatting
    - Exit codes: 0 (success), 1 (validation errors), 2 (file/config errors)
  - **CI Workflow** (`.github/workflows/content-validation.yml`):
    - Triggers on push to main and PRs that modify content files
    - Monitors: `content/**/*.yml`, `content/**/*.yaml`, `scripts/build_content.py`, `.github/workflows/content-*.yml`
    - Runs validation via `uv run python scripts/build_content.py --verbose --output content-manifest.json`
    - Uploads content manifest artifact for debugging
    - Blocks PR merge on validation failures
  - **Designer Documentation** (`docs/gengine/content_designer_workflow.md`):
    - Content types and structure (worlds, configs, sweeps)
    - YAML schema examples with annotations
    - Local validation instructions with exit codes
    - CI/CD validation details and artifact retrieval
    - Troubleshooting section with common validation errors
    - Best practices for content authors
  - **Test Coverage** (`tests/scripts/test_build_content.py`):
    - 17 tests covering all validation paths
    - Tests for valid content, missing files, invalid schemas, bad entity references
    - Integration tests validating real repository content
    - All tests passing
- **Last Updated:** 2025-12-02

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

### 9.2.1 — Rule-Based AI Action Layer (M9.2)
- **GitHub Issue:** [#24](https://github.com/TheWizardsCode/GEngine/issues/24)
- **Description:** Implement rule-based AI strategies and actor that submit intents, log decisions, and support deterministic 100-tick runs.
- **Acceptance Criteria:** Strategies (balanced/aggressive/diplomatic) implemented; AI actor submits valid intents and handles responses; regression test shows stabilization behavior; telemetry captures decision rationale.
- **Priority:** Medium
- **Responsible:** gamedev-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** Action routing, intent schema, observer foundation.
- **Risks & Mitigations:**
  - Risk: Rules overfit specific scenarios. Mitigation: Test across multiple configs and seeds.
- **Completion Notes:**
  - **Strategies Module** (`src/gengine/ai_player/strategies.py`):
    - `StrategyType` enum: BALANCED, AGGRESSIVE, DIPLOMATIC
    - `StrategyConfig` dataclass with configurable thresholds
    - `StrategyDecision` dataclass for tracking decisions with telemetry
    - `BalancedStrategy`: Moderate intervention (stability 0.6, faction 0.4)
    - `AggressiveStrategy`: Frequent actions, higher thresholds, larger deployments
    - `DiplomaticStrategy`: Prefers negotiation, relationship building
    - `create_strategy()` factory function
  - **Actor Module** (`src/gengine/ai_player/actor.py`):
    - `ActorConfig` dataclass for actor configuration
    - `ActionReceipt` dataclass for tracking submitted actions
    - `ActorReport` dataclass for session summaries with telemetry
    - `AIActor` class: `run()`, `select_action()`, `submit_intent()`, `act()` methods
    - Decision logging captures rationale, priority, and state snapshot
    - Factory functions: `create_actor_from_engine()`, `create_actor_from_service()`
  - **Test Coverage**: 
    - 41 new tests for strategies in `tests/ai_player/test_strategies.py`
    - 34 new tests for actor in `tests/ai_player/test_actor.py`
    - Includes 100-tick regression tests with deterministic seeds
    - Total AI player tests: 112 (all passing)
  - **Documentation**: Updated README with AI Player Actor section, updated implementation plan

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

### 10.1.1 — Core systems test coverage improvements (epic)

- **Description:** Umbrella task to implement the test coverage and quality improvements described in `docs/gengine/test_coverage_report.md` across core systems (SimEngine, AgentSystem, FactionSystem, EconomySystem, EnvironmentSystem, ProgressionSystem) and integration surfaces (AI player, gateway, LLM).
- **Acceptance Criteria:** Child tasks 10.1.2–10.1.8 are completed and passing; coverage thresholds for core systems meet or exceed current levels with improved branch/behavior coverage; no new flaky tests introduced; report updated to reflect new coverage and gaps.
- **Priority:** High
- **Responsible:** Test Agent
- **Dependencies:** None (epic/parent task)
- **Risks & Mitigations:**
  - Risk: Overly prescriptive tests make refactoring hard. Mitigation: Focus on behavior and contracts, not implementation details.
  - Risk: Increased CI runtime. Mitigation: Group heavier tests under separate markers.
- **Next Steps:**
  1. Implement child tasks 10.1.2–10.1.8.
  2. Re-run coverage and update `docs/gengine/test_coverage_report.md`.
  3. Tag heavier tests for selective execution (e.g., `slow`, `integration`).
- **Last Updated:** 2025-12-02

### 10.1.2 — Strengthen AgentSystem decision logic tests

- **Description:** Improve `AgentSystem` tests so they validate decision logic and trait effects (empathy, cunning, resolve), not just deterministic output sequences.
- **Acceptance Criteria:**
  - Unit tests for `_decide` or equivalent logic verify option scoring under controlled inputs (e.g., high unrest + high empathy → higher `STABILIZE_UNREST` weight).
  - Edge-case tests cover agents with missing districts/factions and cases where total option weight is non-positive.
  - Tests remain deterministic by injecting a fake RNG or by checking scoring and choice logic separately.
- **Priority:** High
- **Responsible:** Test Agent
- **Dependencies:** 4.1.1 (Agent AI subsystem) – already completed.
- **Risks & Mitigations:**
  - Risk: Tests rely on fragile internal details. Mitigation: Prefer public behavior and scoring contracts over internal data structures.
- **Next Steps:**
  1. Introduce a small fake RNG helper or refactor to accept a sampling strategy.
  2. Add targeted tests for trait and environment influences.
  3. Add edge-case tests for missing data and no-option scenarios.
- **Status:** Completed
- **Last Updated:** 2025-12-02

### 10.1.3 — Expand SimEngine API and error-path tests

- **Description:** Add tests for all public `SimEngine` APIs (views, focus, director, explanations, progression) and error handling paths.
- **Acceptance Criteria:**
  - Tests cover: `initialize_state` validation, `query_view` with all view names and invalid names, `director_feed`, all explanations helpers, and progression helpers (`progression_summary`, `calculate_success_chance`, etc.).
  - Error paths tested: using engine before initialization, requesting too many ticks, and unknown views.
  - At least one test validates that progression state is updated when ticks advance.
- **Priority:** High
- **Responsible:** Test Agent
- **Dependencies:** 4.5.1 (Tick orchestration) and 7.1.x progression tasks – completed.
- **Risks & Mitigations:**
  - Risk: Tests become brittle to representation details. Mitigation: Assert on high-level contracts and key fields only.
- **Next Steps:**
  1. Extend `tests/echoes/test_sim_engine.py` with new API coverage.
  2. Add explicit error-path tests for invalid inputs and state.
  3. Wire progression expectations through existing fixtures.
- **Last Updated:** 2025-12-02

### 10.1.4 — Stabilize FactionSystem tests (decouple RNG)

- **Description:** Refactor faction system tests so they do not rely on fragile `random.Random` seeds and instead use deterministic control over decision paths.
- **Acceptance Criteria:**
  - Tests no longer depend on magic seed values; they either inject a fake RNG or isolate decision logic such that choices can be forced.
  - Existing behavioral assertions (lobby, sabotage, invest, recruit) remain covered.
  - Tests remain green even if internal action ordering changes, as long as behavior contracts hold.
- **Priority:** Medium
- **Responsible:** Test Agent
- **Dependencies:** 4.2.1 (Faction AI subsystem) – completed.
- **Risks & Mitigations:**
  - Risk: Refactoring tests requires minor code changes for better injection points. Mitigation: Keep production changes minimal and backwards compatible.
- **Next Steps:**
  1. Identify RNG usage in `FactionSystem` and add injection seams if needed.
  2. Replace seed-based tests with fake RNG or deterministic strategies.
  3. Re-run coverage to confirm unchanged or improved coverage.
- **Last Updated:** 2025-12-02

### 10.1.5 — Persistence save/load fidelity tests

- **Description:** Add high-confidence tests that `GameState` snapshots and related persistence components can be saved and loaded without data loss, including progression and per-agent state.
- **Acceptance Criteria:**
  - Round-trip tests (`save → load → save`) confirm structural and critical-field equivalence for snapshots.
  - Tests cover key subsystems: city/districts, factions, agents, environment, progression, agent progression, and metadata.
  - At least one test asserts backwards compatibility with older snapshot versions if applicable.
- **Priority:** Medium
- **Responsible:** Test Agent
- **Dependencies:** Persistence module and snapshot format stabilized.
- **Risks & Mitigations:**
  - Risk: Exact byte-level equality is brittle. Mitigation: Compare semantic equality rather than raw file bytes where appropriate.
- **Next Steps:**
  1. Identify canonical snapshot fixtures.
  2. Implement semantic comparison helpers.
  3. Add tests to `tests/echoes/test_snapshot_persistence.py` or equivalent.
- **Last Updated:** 2025-12-02

### 10.1.6 — Cross-system integration scenario tests

- **Description:** Create end-to-end scenario tests that exercise chains of behavior across systems (agents → districts → factions → economy/environment) over multiple ticks.
- **Acceptance Criteria:**
  - At least one scenario test encodes a reproducible narrative (e.g., unrest spike leading to faction interventions and economic shifts).
  - Tests assert on key metrics and state transitions rather than exact per-tick logs.
  - Scenario tests are marked as `integration` or `slow` for selective CI execution.
- **Priority:** Medium
- **Responsible:** Test Agent
- **Dependencies:** Core systems for agents, factions, economy, environment fully implemented (Phase 4 complete).
- **Risks & Mitigations:**
  - Risk: Scenario expectations become invalid as tuning evolves. Mitigation: Assert broad behavior ranges and trends instead of exact numbers.
- **Next Steps:**
  1. Design 1–2 representative scenarios.
  2. Implement scenario harness using existing fixtures.
  3. Add assertions on cross-system outcomes.
- **Last Updated:** 2025-12-02

### 10.1.7 — Performance and tick-limit regression tests

- **Description:** Add basic performance and guardrail regression tests to ensure engine tick times and tick-limit enforcement remain within expected bounds.
- **Acceptance Criteria:**
  - Tests verify that configured tick limits (engine, CLI, service) are enforced via existing APIs.
  - At least one test captures rough timing for a multi-tick run and asserts it remains under a generous threshold on CI hardware.
  - Tests can be skipped or marked `slow` to avoid flakiness.
- **Priority:** Low
- **Responsible:** Test Agent
- **Dependencies:** Guardrail configuration from 3.4.1, SimEngine tick loop.
- **Risks & Mitigations:**
  - Risk: Performance tests flaky across hardware. Mitigation: Use conservative thresholds and optional markers.
- **Next Steps:**
  1. Reuse existing guardrail tests as a base.
  2. Add timing checks where feasible.
  3. Tag as `slow` or `perf` for selective runs.
- **Last Updated:** 2025-12-02

### 10.1.8 — AI/LLM mocking and coverage for gateways

- **Description:** Implement robust mocking for LLM providers and gateway integrations so that AI player, LLM service, and gateway logic can be tested without real API calls.
- **Acceptance Criteria:**
  - Mock providers for OpenAI/Anthropic exist and are used in tests for `gengine.echoes.llm` and `gengine.ai_player`.
  - Gateway and LLM service tests cover success, failure, and timeout paths.
  - No external network calls are made during tests; CI-friendly without credentials.
- **Priority:** Medium
- **Responsible:** Test Agent (with support from AI-focused agent if available)
- **Dependencies:** 6.5.1, 6.6.1, and 9.2.1/9.3.1 implementations.
- **Risks & Mitigations:**
  - Risk: Mocks diverge from real provider behavior. Mitigation: Keep mocks simple and driven by the same intent schema.
- **Next Steps:**
  1. Add mock provider classes and fixtures.
  2. Expand tests in `tests/echoes/test_llm_*` and gateway tests.
  3. Ensure CI configuration does not require real API keys.
- **Last Updated:** 2025-12-02


