# Project Task Tracker

**Last Updated:** 2025-12-05T05:54:00Z

## Quick Status Dashboard

| Phase | Status | Complete | Remaining | Priority | Next Action |
|-------|--------|----------|-----------|----------|-------------|
| **1-10** | ✅ Complete | 51/51 | 0 | - | Maintenance only |
| **11** | 🚧 In Progress | 3/6 | 3 | High | Start 11.5.1 (CI Integration) |
| **12** | 📋 Planned | 0/5 | 5 | Medium | Await prioritization decision |


**Active Tasks:**

- ✅ **11.3.1** - Analysis and Balance Reporting - **COMPLETED** (merged 2025-12-04)
- 🆕 **10.1.9** - Comprehensive Scripts Test Coverage - **READY** (Issue #65 created)

**Next Recommended Tasks:**

1. **11.5.1** - CI Integration for Balance Validation (depends on 11.3.1 ✅)
2. **10.1.9** - Scripts Test Coverage (ready to assign to test_agent)
3. **11.4.1** - Strategy Parameter Optimization (lower priority)


## Comprehensive Project Status Report

### Executive Summary

**Project Health: ✅ EXCELLENT** - All core implementation phases complete, 849 tests at 90.95% coverage, zero critical blockers.

**Recent Achievements:**

- ✅ **Task 11.3.1** (Analysis and Balance Reporting): MERGED 2025-12-04 - 1667 lines of statistical analysis + 695 lines of tests
- ✅ Phase 8 (Deployment): COMPLETE - All 6 tasks including K8s validation, resource tuning, metrics, and content pipeline
- ✅ Phase 9 (AI Testing): COMPLETE - Observer, rule-based actor, and LLM-enhanced decisions all shipped
- ✅ Phase 10 (Test Coverage): COMPLETE - Epic 10.1.1 and all 7 child tasks delivered, 849 tests at 90.95% coverage
- ✅ Phase 7 (Player Experience): COMPLETE - Progression, campaigns, explanations, difficulty tuning all shipped

**Current State:**

- Total tests: 849 (stable, high quality)
- Coverage: 90.95% overall, critical modules at 94-98%
- Open issues: 1 (Issue #65 - Scripts test coverage, just created)
- Recent commits: 20+ commits in past 24 hours, excellent delivery pace
- Repository hygiene: Excellent - clean issue backlog, well-documented
- **Phase 11 Progress:** 3 of 6 milestones complete (11.1 Batch Sweeps, 11.2 Result Aggregation, 11.3 Analysis & Reporting)
- **Phase 12 Status:** 5 milestones planned, awaiting prioritization vs. Phase 11 completion

## Status Summary

**Recent Progress (since last update):**

- 🎉 **Task 11.3.1 (Analysis and Balance Reporting) COMPLETED** - GitHub Issue [#63](https://github.com/TheWizardsCode/GEngine/issues/63) ✅ **MERGED** (2025-12-04)
  - Script `scripts/analyze_balance.py` with comprehensive statistical analysis framework (1667 lines)
  - 695 lines of tests covering all report types, statistical calculations, edge cases
  - Balance reports identify dominant strategies, underperforming mechanics, unused content
  - Statistical functions: win rate deltas, significance testing, trend detection, regression analysis
  - Updated documentation in `docs/gengine/ai_tournament_and_balance_analysis.md`
  - Exceeded acceptance criteria: 695 lines of tests vs. requirement of 12+ tests
  - **Phase 11 Progress: 3/6 milestones complete (11.1, 11.2, 11.3)**
- 🆕 **Task 10.1.9 (Comprehensive Scripts Test Coverage) ADDED** - NEW TASK (2025-12-05)
  - Ensures all `/scripts` utilities have comprehensive test coverage
  - Currently 9/13 scripts have tests; 4 missing (eoe_dump_state, plot_environment_trajectories, run_ai_observer, plus helpers)
  - Will update pytest.ini to include scripts in coverage reports
  - Target: 80% coverage for scripts module with ~15 new tests
  - Assigned to test_agent for implementation
  - Addresses gap: scripts currently excluded from coverage tracking despite being critical utilities
- 🆕 **Phase 12 (UI Implementation) PLANNED** - NEW PHASE (2025-12-05)
  - 5 new milestones added based on UI design document (`docs/simul/game_ui_design.md`)
  - M12.1: Core Playability UI (status bar, city map, event feed, context panel, command bar)
  - M12.2: Management Depth UI (agent roster, faction overview, focus management, heat maps)
  - M12.3: Understanding & Reflection UI (explanations, timeline view, campaign hub, post-mortem)
  - M12.4: Polish & Accessibility (animations, keyboard navigation, accessibility audit, help system)
  - M12.5: UI Testing & Validation (success metrics tracking, automated tests, user testing)
  - Moves from CLI-only to rich terminal interface with visual feedback and progressive disclosure
  - Reference: Implementation plan Section 6 describes CLI gateway foundation for UI layer
  - **Status:** Planning phase - awaiting prioritization decision vs. Phase 11 completion
- 🎉 **Task 11.3.1 (Analysis and Balance Reporting) IN PROGRESS** - GitHub Issue [#63](https://github.com/TheWizardsCode/GEngine/issues/63)
  - Script `scripts/analyze_balance.py` with statistical analysis framework
  - 1667 lines of implementation + 695 lines of comprehensive tests
  - Statistical functions for win rate deltas, significance testing, trend detection
  - Balance report generation with dominant strategies, underperforming mechanics, unused content
  - Parameter sensitivity analysis and regression detection
  - Ready for final review and merge
- 🎉 **Task 11.2.1 (Result Aggregation and Storage) COMPLETED** - GitHub Issue [#61](https://github.com/TheWizardsCode/GEngine/issues/61)
  - Script `scripts/aggregate_sweep_results.py` with SQLite database storage
  - Versioned schema with indexes for efficient querying
  - Ingest, query, stats, and runs subcommands via CLI
  - Historical tracking with git commit hash and timestamp metadata
  - Aggregation computes win rates, stability metrics, seed activation rates, action frequencies
  - 26 comprehensive tests covering schema, ingestion, queries, aggregation, CLI
  - Exceeded acceptance criteria: 26 tests delivered (requirement was 8+)
- 📋 **Implementation Plan Updated (2025-12-04)** - Section 10 added
  - New section "Strategy Parameter Tuning (Future)" describes long-term vision for AI behavior refinement
  - Extends task 11.4.1 scope with future work: internal parameter exposure (aggression thresholds, risk tolerance, resource prioritization)
  - Enables dynamic strategy adjustment and more granular AI control
  - Tracker updated to reference this future work in task 11.4.1
- 🎉 **Task 11.1.1 (Batch Simulation Sweep Infrastructure) COMPLETED** - GitHub Issue [#58](https://github.com/TheWizardsCode/GEngine/issues/58)
  - Script `run_batch_sweeps.py` with multi-dimensional parameter grids
  - Parallel execution support using multiprocessing (configurable worker count)
  - JSON output with game results, telemetry, and full metadata
  - Configuration file `content/config/batch_sweeps.yml` for sweep definitions
  - 37 comprehensive tests covering grid generation, execution, output validation
  - Documentation updated in README and how-to-play guide
- 🎉 **Task 9.3.1 (LLM-Enhanced AI Decisions) COMPLETED** - GitHub Issue [#34](https://github.com/TheWizardsCode/GEngine/issues/34)
  - HybridStrategy implementation routes routine decisions to rules and complex choices to LLM
  - Budget enforcement via LLMStrategyConfig prevents runaway costs
  - 91 new tests covering hybrid strategy, LLM decision layer, and complexity evaluation
  - Telemetry tracks decision_source ("rule" vs "llm"), call counts, latency, and fallback rates
  - Coverage at 94% for AI player module
  - Documentation updated in README with examples and configuration guide
- 🎉 **Task 8.3.2 (K8s Validation CI Job) COMPLETED** - GitHub Issue [#31](https://github.com/TheWizardsCode/GEngine/issues/31)
  - CI workflow `.github/workflows/k8s-validation.yml` validates all K8s manifests
  - kubectl apply --dry-run=server validation using Kind cluster
  - kubeconform linting for schema validation
  - Validates base manifests and both local/staging overlays
  - Workflow runs on K8s manifest changes and blocks PRs on failures
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

- 🎉 **Task 11.1.1 (Batch Simulation Sweep Infrastructure) COMPLETED** - GitHub Issue [#58](https://github.com/TheWizardsCode/GEngine/issues/58)
  - Script `run_batch_sweeps.py` with multi-dimensional parameter grids
  - Parallel execution support using multiprocessing (configurable worker count)
  - JSON output with game results, telemetry, and full metadata
  - Configuration file `content/config/batch_sweeps.yml` for sweep definitions
  - 37 comprehensive tests covering grid generation, execution, output validation
  - Documentation updated in README and how-to-play guide
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

1. ✅ **Phase 8 Deployment** - COMPLETE! All 6 tasks delivered (containerization, K8s, observability, content pipeline)
2. ✅ **Phase 10 Test Coverage** - COMPLETE! Epic 10.1.1 and all 7 child tasks delivered, 849 tests at 90.95% coverage
3. ✅ **Phase 9 AI Testing Core** - COMPLETE! All 4 tasks delivered (observer, action layer, LLM-enhanced, tournaments)
4. 🚧 **Phase 11 Balance Tooling** - 50% COMPLETE (Milestones 11.1, 11.2, 11.3 done; moving to 11.5.1 CI Integration)
5. 🆕 **Phase 12 UI Implementation** - PLANNED (5 milestones for terminal-based visual interface; prioritization decision needed)
6. 🆕 **Task 10.1.9 Scripts Testing** - READY (Issue #65 created; ready to assign to test_agent)

**Immediate Next Steps (Recommended):**

1. **Assign Task 10.1.9 to test_agent** - Scripts test coverage gap needs attention (9/13 scripts tested)
2. **Begin Task 11.5.1** - CI Integration for Balance Validation (unblocked by 11.3.1 completion)
3. **Prioritization Decision** - Choose between:
   - **Option A:** Complete Phase 11 (tasks 11.4, 11.5, 11.6) for clean deliverable
   - **Option B:** Start Phase 12 UI work in parallel with Phase 11 completion

## Risks & Blockers

### 🟢 Current Blockers: NONE

All tasks are either complete or unblocked and ready to start.

### ⚠️ Active Risks

| Risk | Severity | Impact | Mitigation Status |
|------|----------|--------|-------------------|
| **Scripts test coverage gap** | Medium | Untested utilities may have hidden bugs; coverage metrics incomplete | ✅ Issue #65 created, ready to assign |
| **Phase prioritization unclear** | Low | Resource allocation between Phase 11 completion vs. Phase 12 start | 🟡 Awaiting PM decision |
| **UI implementation scope large** | Medium | Phase 12 has 5 substantial milestones; may need dedicated sprint | 📋 Planned, not yet started |
| **Balance CI integration complexity** | Low | Task 11.5.1 requires careful baseline management and threshold tuning | 📋 Documented in task, ready to start |

### 🔄 Monitoring

- **Test Coverage:** Stable at 90.95%; will improve with task 10.1.9 completion
- **Issue Backlog:** Clean (1 open issue, just created)
- **PR Queue:** Empty - excellent merge velocity
- **Documentation Drift:** None detected - docs updated with each milestone

**Project Status: 📊 Phase 11 Balance Tooling - 50% Complete (3/6 milestones) | Phase 12 UI Implementation Planned**

Phases 1-10 complete. **Phase 11 (Balance Tooling Enhancements)** at 50% completion with milestones 11.1, 11.2, and 11.3 delivered. Remaining: 11.4 (optimization), 11.5 (CI integration), 11.6 (designer tooling). **Phase 12 (UI Implementation)** planned with 5 milestones covering terminal-based visual interface - awaiting prioritization decision. Implementation plan updated with Section 10 (Strategy Parameter Tuning - Future) describing long-term vision for internal strategy parameter exposure and optimization.

## Discrepancies Between Plan and Actual State

### ✅ No Major Discrepancies Found

The project has closely followed the implementation plan with excellent tracking and documentation:

1. **Implementation Plan vs. README.md**: Fully aligned
   - All completed milestones documented in both locations
   - Phase progress logs match across documents
   - Feature descriptions consistent

2. **Tracker vs. GitHub Issues**: Minor administrative lag only
   - Task 8.4.1 completed but Issue #56 still open (should be closed)
   - Task 9.4.1 completed but not reflected in all docs until now
   - All other issues properly closed

3. **Test Coverage**: Exceeds targets
   - Plan target: ≥90% coverage for core systems
   - Actual: 90.95% overall, 94-98% for critical modules
   - 849 tests vs. ~600-700 estimated

4. **Feature Completeness**: All phases delivered
   - Phases 1-6: Foundation and core systems ✅
   - Phase 7: Player experience ✅
   - Phase 8: Deployment ✅
   - Phase 9: AI testing ✅
   - Phase 10: Test coverage ✅

### Minor Documentation Gaps (Not Blockers)

1. **Task 9.4.1 Status**: Marked "not-started" in tracker despite completion
   - **Impact**: None - work is done and documented
   - **Fix**: Updated in this tracker revision

2. **Issue #56 Open**: Should be closed as task 8.4.1 is complete
   - **Impact**: Cosmetic only - no functional impact
   - **Fix**: Recommend closing via GitHub

3. **Implementation Plan Phase Log**: Could be updated to reflect Phase 9-10 completion
   - **Impact**: Minor - README is current, plan is slightly behind
   - **Fix**: Consider updating `docs/simul/emergent_story_game_implementation_plan.md`

## Phase-by-Phase Completion Summary

| Phase | Description | Planned Tasks | Completed | Status |
|-------|-------------|---------------|-----------|--------|
| 1 | Foundations & Data Model | 5 | 5 | ✅ 100% |
| 2 | Early CLI Shell & Tick Loop | 4 | 4 | ✅ 100% |
| 3 | Simulation Core & Service API | 5 | 5 | ✅ 100% |
| 4 | Agents/Factions/Economy | 7 | 7 | ✅ 100% |
| 5 | Narrative Director & Story Seeds | 4 | 4 | ✅ 100% |
| 6 | CLI Gateway & LLM Integration | 4 | 4 | ✅ 100% |
| 7 | Player Experience | 4 | 4 | ✅ 100% |
| 8 | Deployment (Docker/K8s) | 6 | 6 | ✅ 100% |
| 9 | AI Testing & Validation | 4 | 4 | ✅ 100% |
| 10 | Test Coverage Improvements | 9 | 8 | 🚧 89% |
| 11 | Automated Balance Workflow | 6 | 3 | 🚧 50% |
| 12 | UI Implementation | 5 | 0 | 📋 Planned |
| **TOTAL** | **All Phases** | **63** | **54** | **⚙️ 86%** |

**In-Progress Tasks:**
- **10.1.9** - Scripts test coverage (Issue #65, ready to assign)
- **11.4.1** - Strategy parameter optimization (not started)
- **11.5.1** - CI integration for balance (ready to start, unblocked)
- **11.6.1** - Designer feedback tooling (not started)

**Optional Polish Tasks** (not included in phase counts):

- 8.3.5: K8s smoke test CI integration
- 10.2.1: Difficulty sweep hardening  
- 10.2.2: AI player LLM robustness

## Detailed Phase Analysis

### Phase 1-6: Foundation & Core Systems ✅ COMPLETE

- **Status:** All milestones delivered and tested
- **Key Achievements:**
  - Data models, content loading, snapshot persistence
  - CLI shell with 12+ commands (summary, run, map, focus, campaign, explain, timeline, etc.)
  - Simulation service (FastAPI) + gateway service (WebSocket) + LLM service
  - Agent AI (utility-based decision logic), Faction AI (strategic actions)
  - Economy subsystem (supply/demand, markets, shortages)
  - Environment subsystem (pollution, diffusion, biodiversity, stability)
  - Narrative director with story seeds, pacing, lifecycle management
  - LLM integration (OpenAI, Anthropic providers) with intent parsing

### Phase 7: Player Experience ✅ COMPLETE (100%)

- **Status:** All 4 milestones shipped
- **Progress:** 4/4 tasks complete
- **Milestones:**
  - ✅ M7.1: Progression systems (skills, access tiers, reputation)
  - ✅ M7.1.2: Per-agent progression (specialization, expertise, reliability, stress)
  - ✅ M7.1.3: Per-agent modifiers enabled by default
  - ✅ M7.2: Explanations & causal queries (timeline, explain, why commands)
  - ✅ M7.3: Tuning & replayability (5 difficulty presets, sweep tooling)
  - ✅ M7.4: Campaign UX (create, resume, autosave, end-of-campaign post-mortems)
- **Outstanding:** None

### Phase 8: Deployment ✅ COMPLETE (100%)

- **Status:** All containerization and K8s work delivered
- **Progress:** 6/6 tasks complete
- **Milestones:**
  - ✅ M8.1: Containerization (Docker + docker-compose for all 3 services)
  - ✅ M8.2: Kubernetes manifests (base + local/staging overlays, ingress, health checks)
  - ✅ M8.3.1: Observability (Prometheus annotations, ServiceMonitors, K8s smoke tests)
  - ✅ M8.3.2: K8s validation CI (kubectl dry-run + kubeconform linting)
  - ✅ M8.3.3: Resource sizing (differentiated allocations per service/environment)
  - ✅ M8.3.4: Gateway/LLM Prometheus metrics (/metrics endpoints with prometheus_client)
  - ✅ M8.4: Content pipeline tooling (build_content.py, CI validation, designer workflow docs)
- **Outstanding:**
  - 8.3.5: K8s smoke test CI integration (LOW priority, 1 day effort)

### Phase 9: AI Testing & Validation ✅ COMPLETE (100%)

- **Status:** All AI testing infrastructure delivered
- **Progress:** 4/4 tasks complete
- **Milestones:**
  - ✅ M9.1: AI Observer foundation (local + service modes, trend detection, 37 tests)
  - ✅ M9.2: Rule-based AI action layer (3 strategies, actor, 75 tests)
  - ✅ M9.3: LLM-enhanced AI decisions (HybridStrategy with budget controls, 91 tests)
  - ✅ M9.4: AI tournaments & balance tooling (scripts exist, documented in README Section 13)
- **Outstanding:** None

### Phase 10: Test Coverage ✅ COMPLETE (100%)

- **Status:** Epic and all child tasks delivered
- **Progress:** 8/8 tasks complete
- **Coverage Improvements:**
  - Overall: 90.95% (exceeds 90% threshold)
  - SimEngine: 85% → 98%
  - AI/LLM modules: 0-20% → 74-97%
  - Test count: 683 → 849 (+166 new tests)
- **Milestones:**
  - ✅ 10.1.1: Epic - Core systems test coverage improvements
  - ✅ 10.1.2: AgentSystem decision logic tests (trait influence, edge cases)
  - ✅ 10.1.3: SimEngine API tests (41 new tests for views, director, progression)
  - ✅ 10.1.4: FactionSystem RNG decoupling (DeterministicRNG, no magic seeds)
  - ✅ 10.1.5: Persistence fidelity (17 round-trip tests, backwards compatibility)
  - ✅ 10.1.6: Integration scenarios (7 cross-system tests with @integration marker)
  - ✅ 10.1.7: Performance guardrails (14 timing/limit tests with @slow marker)
  - ✅ 10.1.8: AI/LLM mocking (78 tests, ConfigurableMockProvider, CI-friendly)
- **Outstanding:**
  - 10.2.1: Difficulty sweep hardening (LOW priority, 2-3 day effort)
  - 10.2.2: AI player LLM robustness (LOW priority, future enhancement)

### Phase 11: Automated Balance Workflow ⚙️ IN PLANNING (0%)

- **Status:** Phase defined, tasks planned but not yet started
- **Progress:** 0/6 tasks complete
- **Objective:** Build advanced automation for data-driven balance iteration and strategy tuning
- **Milestones:**
  - ⬜ 11.1.1: Batch simulation sweep infrastructure
  - ⬜ 11.2.1: Result aggregation and storage
  - ⬜ 11.3.1: Analysis and balance reporting
  - ⬜ 11.4.1: Strategy parameter optimization
  - ⬜ 11.5.1: CI integration for continuous validation
  - ⬜ 11.6.1: Designer feedback loop and tooling
- **Dependencies:** Phase 9 (AI tournaments and balance tooling already exists)
- **Outstanding:** All 6 tasks not yet started

## Outstanding Work Analysis

### Issue #56: Content Pipeline CI Integration (M8.4)

- **GitHub Issue:** [#56](https://github.com/TheWizardsCode/GEngine/issues/56) - OPEN
- **Actual Status:** ✅ **COMPLETED BUT ISSUE NOT CLOSED**
- **Evidence:**
  - ✅ Task 8.4.1 marked COMPLETED in tracker (2025-12-02)
  - ✅ CI workflow exists: `.github/workflows/content-validation.yml`
  - ✅ Build script exists: `scripts/build_content.py` with 17 passing tests
  - ✅ Documentation exists: `docs/gengine/content_designer_workflow.md`
  - ✅ Workflow triggers on content file changes
  - ✅ Clear error messages and exit codes implemented
- **Blocking Dependencies:** None - all acceptance criteria met
- **Recommendation:** Close Issue #56 as completed (work was delivered in task 8.4.1)
- **Impact:** Zero - this is purely administrative cleanup

### Remaining Optional Tasks

**8.3.5 - Integrate K8s Smoke Test into CI**

- **Priority:** LOW
- **Effort:** 1 day
- **Status:** not-started
- **Blocker:** None - K8s smoke test script exists and works, just not automated in CI
- **Rationale:** Manual K8s smoke tests are sufficient for current deployment cadence
- **Recommendation:** Defer unless K8s deployments become frequent

**9.4.1 - AI Tournaments & Balance Tooling**

- **Priority:** LOW
- **Effort:** Already completed
- **Status:** ✅ **COMPLETED** (verified 2025-12-04)
- **Evidence:**
  - ✅ Scripts exist: `scripts/run_ai_tournament.py` and `scripts/analyze_ai_games.py`
  - ✅ Documentation exists: README Section "AI Tournaments & Balance Tooling"
  - ✅ Dedicated docs: `docs/gengine/ai_tournament_and_balance_analysis.md`
  - ✅ CI workflow: `.github/workflows/ai-tournament.yml` for nightly runs
- **Recommendation:** Mark task 9.4.1 as COMPLETED in tracker (already done above)

**10.2.1 - Harden Difficulty Sweep Runtime & Monitoring**

- **Priority:** LOW
- **Effort:** 2-3 days
- **Status:** not-started
- **Blocker:** None - existing difficulty sweeps work well
- **Recommendation:** Defer as polish/enhancement work

**Recommended Next Actions:**

1. **Administrative Cleanup (Priority: HIGH, Effort: 5 minutes)**
   - Close Issue #56 (Content Pipeline CI) - work already completed in task 8.4.1
   - Verify task 9.4.1 completion is reflected in implementation plan docs

2. **Optional Polish Tasks (Priority: LOW, Total: 3-4 days)**
   - 8.3.5: K8s smoke test CI integration (1 day) - automate existing manual tests
   - 10.2.1: Difficulty sweep hardening (2-3 days) - improve robustness and monitoring
   - 10.2.2: AI player LLM robustness (future enhancement) - better failure handling

3. **Consider Project Complete** 🎉
   - All planned phases (1-10) are functionally complete
   - 849 tests at 90.95% coverage
   - Full feature set delivered: CLI, services, K8s deployment, AI testing, player progression
   - Only optional polish and future enhancements remain
   - Strong foundation for future expansion

**Key Risks:**

- ✅ **Phase 8 deployment COMPLETE** - All 6 tasks done: containerization (8.1.1), K8s manifests (8.2.1), observability (8.3.1), K8s validation CI (8.3.2), resource sizing (8.3.3), metrics (8.3.4), content pipeline (8.4.1)
- ✅ **Phase 9 core AI COMPLETE** - All 4 tasks shipped: observer (9.1.1), actor (9.2.1), LLM-enhanced (9.3.1), tournaments (9.4.1)
- ✅ **Phase 10 test coverage COMPLETE** - Epic 10.1.1 and all 7 child tasks (10.1.2–10.1.8) completed; 849 tests at 90.95% coverage
- ✅ **Phase 7 delivery risk eliminated** - All core player features complete and tested, per-agent modifiers enabled by default
- ✅ **Repository hygiene excellent** - Clean issue backlog (only Issue #56 open, which is actually completed work)
- 🟢 **No major blockers** - All planned work complete; only optional polish tasks remain (3-4 days total effort)
- 🟢 **Project delivery SUCCESS** - All phases 1-10 functionally complete with comprehensive test coverage

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
| 8.3.2 | K8s Validation CI Job (M8.3.x)                  | completed   | Medium   | copilot            | 2025-12-04 |
| 8.3.3 | K8s Resource Sizing & Tuning (M8.3.y)           | completed   | Medium   | devops-agent       | 2025-12-02 |
| 8.3.4 | Gateway/LLM Prometheus Metrics (M8.3.x)         | completed   | Medium   | copilot            | 2025-12-03 |
| 8.3.5 | Integrate K8s Smoke Test into CI (M8.3.x)       | not-started | Low      | TBD (ask Ross)     | 2025-12-03 |
| 8.4.1 | Content pipeline tooling & CI (M8.4)            | completed   | Medium   | devops-agent       | 2025-12-02 |
| 9.1.1 | AI Observer foundation acceptance (M9.1)        | completed   | Medium   | gamedev-agent      | 2025-11-30 |
| 9.2.1 | Rule-based AI action layer (M9.2)               | completed   | Medium   | gamedev-agent      | 2025-12-01 |
| 9.3.1 | LLM-enhanced AI decisions (M9.3)                | completed   | Medium   | gamedev-agent      | 2025-12-04 |
| 9.4.1 | AI tournaments & balance tooling (M9.4)         | completed   | Low      | gamedev-agent      | 2025-12-04 |

| 10.1.1 | Core systems test coverage improvements (epic) | completed | High | Test Agent | 2025-12-03 |
| 10.1.2 | Strengthen AgentSystem decision logic tests | completed | High | Test Agent | 2025-12-03 |
| 10.1.3 | Expand SimEngine API and error-path tests | completed | High | Test Agent | 2025-12-03 |
| 10.1.4 | Stabilize FactionSystem tests (decouple RNG) | completed | Medium | Test Agent | 2025-12-03 |
| 10.1.5 | Persistence save/load fidelity tests | completed | Medium | Test Agent | 2025-12-03 |
| 10.1.6 | Cross-system integration scenario tests | completed | Medium | Test Agent | 2025-12-03 |
| 10.1.7 | Performance and tick-limit regression tests | completed | Low | Test Agent | 2025-12-03 |
| 10.1.8 | AI/LLM mocking and coverage for gateways | completed | Medium | Test Agent | 2025-12-03 |
| 11.1.1 | Batch simulation sweep infrastructure (M11.1) | ✅ completed | Medium | gamedev-agent | 2025-12-04 |
| 11.2.1 | Result aggregation and storage (M11.2) | ✅ completed | Medium | gamedev-agent | 2025-12-05 |
| 11.3.1 | Analysis and balance reporting (M11.3) | not-started | High | gamedev-agent | 2025-12-04 |
| 11.4.1 | Strategy parameter optimization (M11.4) | not-started | Low | gamedev-agent | 2025-12-04 |
| 11.5.1 | CI integration for continuous validation (M11.5) | not-started | Medium | gamedev-agent | 2025-12-04 |
| 11.6.1 | Designer feedback loop and tooling (M11.6) | not-started | Low | gamedev-agent | 2025-12-04 |
| 10.2.1 | Harden difficulty sweep runtime & monitoring | not-started | Low | Gamedev Agent | 2025-12-02 |
| 10.2.2 | AI player LLM robustness & failure telemetry | not-started | Low | Gamedev Agent | 2025-12-02 |

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
- **Responsible:** gamedev-agent
- **Status:** ✅ COMPLETED
- **Dependencies:** Rule-based and/or hybrid AI strategies; telemetry for outcomes.
- **Risks & Mitigations:**
  - Risk: Tournament runs are resource-intensive. Mitigation: Allow configurable scales and sampling.
- **Completion Notes:**
  - ✅ **Tournament Runner** (`scripts/run_ai_tournament.py`):
    - Runs configurable number of games with multiple strategies
    - Supports strategy selection (balanced, aggressive, diplomatic)
    - Configurable tick budgets and random seeds
    - JSON output with game results and telemetry
  - ✅ **Analysis Script** (`scripts/analyze_ai_games.py`):
    - Analyzes tournament results for win rate deltas
    - Identifies dominant/underperforming strategies
    - Detects unused story seeds and overpowered actions
    - Compares against authored story seeds for coverage
  - ✅ **Documentation**:
    - README.md includes "AI Tournaments & Balance Tooling" section with examples
    - Dedicated documentation in `docs/gengine/ai_tournament_and_balance_analysis.md`
    - Complete balance iteration workflow documented
  - ✅ **CI Integration**:
    - `.github/workflows/ai-tournament.yml` workflow for nightly runs
    - Configurable via GitHub Actions UI for manual triggers
    - Results archived as workflow artifacts
  - ✅ **Test Coverage**: Tournament and analysis scripts include comprehensive tests
- **Last Updated:** 2025-12-04

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

### 10.1.9 — Comprehensive Scripts Test Coverage (M10.2)

- **GitHub Issue:** [#65](https://github.com/TheWizardsCode/GEngine/issues/65)
- **Description:** Create comprehensive test coverage for all scripts in `/scripts` directory and include them in coverage reports. Currently, scripts have partial test coverage (9/13 scripts have tests) but are excluded from pytest coverage configuration. This task ensures all utility scripts are tested and their coverage is tracked.
- **Acceptance Criteria:**
  - All scripts in `/scripts` have corresponding test files in `/tests/scripts/test_*.py`
  - Missing test files created for: `eoe_dump_state.py`, `plot_environment_trajectories.py`, `run_ai_observer.py`, and any other untested scripts
  - pytest.ini updated to include `--cov=scripts` in coverage configuration
  - Scripts coverage included in coverage reports (terminal and XML)
  - Minimum 80% coverage achieved for scripts module
  - Tests cover main execution paths, CLI argument parsing, error handling, and edge cases
  - At least 15 new tests added for previously untested scripts
- **Priority:** Medium
- **Responsible:** test_agent (see `.github/agents/test.agent.md`)
- **Dependencies:** None (standalone task)
- **Risks & Mitigations:**
  - Risk: Scripts are tightly coupled to external systems or files. Mitigation: Use mocking and fixtures for file I/O and external dependencies.
  - Risk: Some scripts may be difficult to test in isolation. Mitigation: Refactor if needed to extract testable functions from main() blocks.
- **Next Steps:**
  1. Audit all scripts to identify untested code paths
  2. Create test files for `test_eoe_dump_state.py`, `test_plot_environment_trajectories.py`, `test_run_ai_observer.py`
  3. Update `pytest.ini` to add `--cov=scripts` to addopts
  4. Run coverage report and identify gaps
  5. Add tests to reach 80% coverage threshold
  6. Update CI to validate scripts coverage
- **Last Updated:** 2025-12-05

## Phase 11: Automated Balance Workflow

### 11.1.1 — Batch Simulation Sweep Infrastructure (M11.1)

- **GitHub Issue:** [#58](https://github.com/TheWizardsCode/GEngine/issues/58)
- **Status:** ✅ **COMPLETED** (2025-12-04)
- **Description:** Build infrastructure to run large batches of simulation sweeps with configurable parameter ranges (difficulty presets, strategy mixes, world variations, random seeds) and parallel execution. This extends existing tournament and difficulty sweep tooling to support broader parameter space exploration for balance analysis.
- **Acceptance Criteria:** ✅ ALL MET
  - ✅ Script `scripts/run_batch_sweeps.py` supports multi-dimensional parameter grids (strategies, difficulties, seeds, worlds, tick budgets).
  - ✅ Parallel execution using Python multiprocessing with configurable worker count.
  - ✅ JSON output per sweep run includes game results, telemetry, and parameter metadata.
  - ✅ Configuration file `content/config/batch_sweeps.yml` defines sweep parameter ranges and defaults.
  - ✅ Documentation describes sweep configuration format and execution workflow.
  - ✅ 37 tests covering parameter grid generation, parallel execution, output validation, and edge cases.
- **Priority:** Medium
- **Responsible:** gamedev-agent
- **Dependencies:** 9.4.1 (AI tournaments), 7.3.1 (difficulty sweeps), core simulation stability.
- **Completion Notes:**
  - Implemented via commits d67ccc4, 6325b0b, f252c65 merged in 7b9c029
  - Supports sampling modes to control grid density
  - Worker pool configuration prevents resource contention
  - Helper modules for grid generation and result formatting
- **Last Updated:** 2025-12-04

### 11.2.1 — Result Aggregation and Storage (M11.2)

- **GitHub Issue:** [#61](https://github.com/TheWizardsCode/GEngine/issues/61) ✅ **COMPLETED**
- **Description:** Implement result aggregation and storage layer that collects sweep outputs into a queryable database or structured file format. Support historical tracking of sweep runs to enable trend analysis and regression detection across balance iterations.
- **Acceptance Criteria:** ✅ All met and exceeded
  - ✅ Script `scripts/aggregate_sweep_results.py` ingests batch sweep JSON outputs and produces aggregated summary data.
  - ✅ SQLite database storage with versioned schema (SCHEMA_VERSION=1) supports querying by parameter combinations, timestamp, and result metrics.
  - ✅ Historical tracking preserves sweep metadata (git commit hash, timestamp, parameter ranges) for reproducibility.
  - ✅ Aggregation computes key statistics: win rates by strategy, average stability/unrest/pollution, story seed activation rates, action usage frequencies.
  - ✅ Query interface supports common lookups (strategy, difficulty, run_id, days, git commit) via CLI subcommands.
  - ✅ 26 comprehensive tests covering all requirements (exceeded 8+ requirement by 3.2x).
- **Priority:** Medium
- **Responsible:** gamedev-agent
- **Dependencies:** 11.1.1 (batch sweep infrastructure).
- **Completion Notes:**
  - **Database:** SQLite with `sweep_runs` (metadata) and `sweep_records` (individual games) tables
  - **CLI Subcommands:** `ingest`, `query`, `stats`, `runs` for full workflow coverage
  - **Indexes:** Optimized queries with indexes on strategy, difficulty, run_id, timestamp
  - **Tests:** 26 tests covering schema creation, ingestion, deduplication, querying, aggregation, CLI integration
  - **Output:** JSON format for aggregated statistics enabling downstream analysis
- **Last Updated:** 2025-12-05

### 11.3.1 — Analysis and Balance Reporting (M11.3)

- **GitHub Issue:** [#63](https://github.com/TheWizardsCode/GEngine/issues/63) ✅ **COMPLETED**
- **Status:** ✅ **COMPLETED** (2025-12-04)
- **Description:** Build analysis tooling that consumes aggregated sweep data and generates actionable balance reports identifying overpowered/underpowered mechanics, dominant strategies, unused content, and parameter sensitivity. Extend existing `analyze_ai_games.py` functionality with statistical rigor and trend detection.
- **Acceptance Criteria:** ✅ All met and exceeded
  - ✅ Script `scripts/analyze_balance.py` processes aggregated sweep results and produces HTML or Markdown balance reports.
  - ✅ Reports include sections for: dominant strategies (win rate deltas >10%), underperforming mechanics (actions/policies rarely chosen), unused story seeds, parameter sensitivity analysis (impact of difficulty/config changes).
  - ✅ Statistical analysis includes confidence intervals, significance testing (e.g., t-tests for win rate differences), and trend detection across historical runs.
  - ✅ Visual outputs (charts/graphs) showing win rate distributions, metric trends over time, and parameter correlations.
  - ✅ Report highlights regressions (new sweeps showing significant deviations from baseline).
  - ✅ Exceeded test requirement: 695 lines of tests covering all report types, statistical calculations, and edge cases (requirement was 12+ tests).
- **Priority:** High
- **Responsible:** gamedev-agent
- **Dependencies:** 11.2.1 (result aggregation and storage), 9.4.1 (analysis script foundation).
- **Completion Notes:**
  - **Implementation:** 1667 lines in `scripts/analyze_balance.py` merged in commit 0379779
  - **Tests:** 695 lines in `tests/scripts/test_analyze_balance.py` 
  - **Statistical Functions:** Win rate deltas, significance testing, trend detection, regression analysis
  - **Report Types:** Dominant strategies, underperforming mechanics, unused content, parameter sensitivity
  - **Documentation:** Updated `docs/gengine/ai_tournament_and_balance_analysis.md` with comprehensive guide
  - **Merge:** Completed 2025-12-04 via branch 'copilot/applicable-takin'
- **Last Updated:** 2025-12-05

### 11.4.1 — Strategy Parameter Optimization (M11.4)

- **Description:** Implement automated strategy parameter tuning using optimization algorithms (grid search, random search, or Bayesian optimization) to find well-balanced strategy configurations. Goal is to reduce dominant strategy win rate deltas and improve strategic diversity. Note: Implementation plan Section 10 describes future work to expose internal strategy parameters (aggression thresholds, risk tolerance, resource prioritization) for deeper tuning—this task focuses on optimizing existing high-level strategy behavior first.
- **Acceptance Criteria:**
  - Script `scripts/optimize_strategies.py` accepts strategy parameter ranges and optimization targets (e.g., minimize max win rate delta, maximize strategic diversity).
  - Supports multiple optimization algorithms: grid search (exhaustive), random search (sampling), and optionally Bayesian optimization (e.g., using `scikit-optimize`).
  - Optimization runs batches of sweep simulations with candidate parameter sets and evaluates fitness against targets.
  - Output includes Pareto frontier of optimal configurations (trade-offs between competing objectives like balance vs. difficulty).
  - Integration with result storage (11.2.1) to track optimization runs and outcomes.
  - Documentation describes optimization workflow, tuning targets, and how to interpret results.
  - At least 10 tests covering optimization algorithms, fitness evaluation, and parameter validation.
- **Priority:** Low
- **Responsible:** gamedev-agent
- **Dependencies:** 11.1.1 (batch sweeps), 11.2.1 (result storage), stable strategy parameter schema.
- **Risks & Mitigations:**
  - Risk: Optimization converges to local optima or overfits to specific scenarios. Mitigation: Use multiple random seeds and validation sets.
  - Risk: Computationally expensive for large parameter spaces. Mitigation: Start with coarse grid search, then refine with targeted searches.
- **Next Steps:**
  1. Define strategy parameter schema and tuning ranges.
  2. Implement fitness functions for balance objectives.
  3. Add optimization algorithms (start with grid/random search).
  4. Create test suite with small synthetic parameter spaces.
  5. (Future) Consider exposing internal strategy parameters per implementation plan Section 10.
- **Last Updated:** 2025-12-04

### 11.5.1 — CI Integration for Continuous Validation (M11.5)

- **Description:** Integrate balance sweep and analysis tooling into CI workflows to detect balance regressions automatically on every commit or nightly schedule. Failed balance checks should produce actionable reports and optionally block merges if regressions exceed thresholds.
- **Acceptance Criteria:**
  - GitHub Actions workflow `.github/workflows/balance-validation.yml` runs on schedule (nightly) and optionally on relevant file changes (strategy configs, game rules).
  - Workflow executes a representative subset of balance sweeps (smaller parameter grid than full exploratory sweeps for speed).
  - Analysis step compares current sweep results against baseline (stored historical data from main branch).
  - Regression detection identifies significant deviations (e.g., strategy win rate delta increased by >5%, unused content increased, metric variance spiked).
  - Workflow produces artifacts: balance report, comparison charts, regression summary.
  - Configurable thresholds control whether regressions are warnings vs. failures (blocking).
  - Documentation describes CI workflow configuration, baseline management, and interpreting regression reports.
  - At least 6 tests for workflow components (subset sweep execution, baseline comparison, threshold enforcement).
- **Priority:** Medium
- **Responsible:** gamedev-agent
- **Dependencies:** 11.1.1 (batch sweeps), 11.3.1 (analysis/reporting), CI infrastructure.
- **Risks & Mitigations:**
  - Risk: CI sweeps too slow and delay feedback. Mitigation: Use reduced parameter grid for CI, full sweeps run on-demand or nightly.
  - Risk: Baseline drift makes regressions noisy. Mitigation: Refresh baseline periodically (e.g., after intentional balance changes merged).
- **Next Steps:**
  1. Design CI sweep subset (e.g., 3 difficulty presets, 3 strategies, 5 seeds, 100 ticks).
  2. Implement baseline storage and comparison logic.
  3. Create workflow YAML with scheduled and manual triggers.
  4. Add regression threshold configuration and reporting.
- **Last Updated:** 2025-12-04

### 11.6.1 — Designer Feedback Loop and Tooling (M11.6)

- **Description:** Build designer-facing tools and workflows that make balance iteration accessible to non-engineers. Provide intuitive interfaces for running sweeps, viewing reports, and experimenting with tuning changes without requiring code changes.
- **Acceptance Criteria:**
  - Command-line tool `echoes-balance-studio` (or similar) provides guided workflows for designers: "Run exploratory sweep", "Compare two configs", "Test tuning change", "View historical reports".
  - Configuration changes can be tested via YAML overlays (similar to difficulty presets) without modifying base config files.
  - Interactive report viewer (HTML dashboard or Jupyter notebook) allows filtering, sorting, and drilling into sweep results.
  - Documentation includes designer-focused guides: "How to diagnose dominant strategies", "Iterating on action costs", "Testing narrative pacing changes".
  - Example workflows demonstrated with case studies (e.g., "Balancing the Industrial Tier faction").
  - At least 8 tests covering CLI commands, config overlay loading, and report generation.
- **Priority:** Low
- **Responsible:** gamedev-agent (with designer/PM feedback loop)
- **Dependencies:** 11.1.1 (batch sweeps), 11.3.1 (analysis/reporting), stable config system.
- **Risks & Mitigations:**
  - Risk: Tools too complex for non-technical users. Mitigation: Focus on simple, opinionated workflows with sensible defaults.
  - Risk: Designer changes break game systems. Mitigation: Include validation and safety checks in config overlays.
- **Next Steps:**
  1. Gather designer persona requirements and common use cases.
  2. Design CLI command structure and interactive workflows.
  3. Implement config overlay system for safe experimentation.
  4. Create designer documentation and tutorial walkthroughs.
- **Last Updated:** 2025-12-04

---

## Phase 12: UI Implementation (Terminal Interface)

**Status:** 🆕 **PLANNED** - New phase based on `docs/simul/game_ui_design.md`

This phase implements the terminal-based UI described in the Game UI Design document, moving from the current CLI-only interface to a rich, visual terminal experience with real-time updates, maps, and progressive disclosure.

**Reference Documents:**
- `docs/simul/game_ui_design.md` - Complete UI design specification
- `docs/simul/emergent_story_game_implementation_plan.md` - Section 6 (CLI Gateway)

### 12.1.1 — Core Playability UI (M12.1)

- **GitHub Issue:** TBD
- **Description:** Implement the fundamental UI elements needed for basic playability: global status bar, city map with district selection, event feed, context panel, and command bar. This establishes the core observe-decide-simulate loop with visual feedback.
- **Acceptance Criteria:**
  - Global status bar displays stability gauge, current tick, campaign name, and active alerts with color coding (green/yellow/red).
  - ASCII city map shows all districts with basic visualization (district names, boundaries).
  - District selection via map click/navigation highlights selected district and updates context panel.
  - Event feed displays recent events with severity coding and color indicators (critical/warning/info).
  - Context panel shows selected district info (name, stability, pollution, unrest, controlling faction).
  - Command bar with Next/Run/Save buttons functional and keyboard-navigable.
  - UI updates in real-time during batch tick execution (e.g., Run 10).
  - At least 15 tests covering UI rendering, district selection, event feed updates, and keyboard navigation.
- **Priority:** High
- **Responsible:** Development Team
- **Dependencies:** Existing simulation and gateway services (Phase 6), terminal rendering library selection.
- **Risks & Mitigations:**
  - Risk: Terminal rendering performance degrades with many updates. Mitigation: Use efficient rendering library (e.g., Rich, Textual) with delta updates.
  - Risk: ASCII map unreadable on small terminals. Mitigation: Implement responsive layout with minimum terminal size requirement.
- **Next Steps:**
  1. Evaluate terminal UI libraries (Rich, Textual, urwid) and select one.
  2. Implement global status bar component with reactive updates.
  3. Build ASCII city map renderer with district grid layout.
  4. Create event feed component with scrolling and filtering.
  5. Implement context panel with district data binding.
  6. Wire up command bar to existing simulation commands.
  7. Add comprehensive UI tests (rendering, interaction, updates).
- **Last Updated:** 2025-12-05

### 12.2.1 — Management Depth UI (M12.2)

- **Description:** Add UI panels for deeper strategic management: agent roster with assignment flow, faction overview, focus management, heat map overlays, and batch run summary panel. This enables players to make informed tactical decisions.
- **Acceptance Criteria:**
  - Agent roster view lists all agents with key stats (name, specialization, expertise, stress level, current assignment).
  - Agent assignment flow: select agent → view available districts → assign with visual confirmation.
  - Faction overview panel shows all factions with influence levels, relationships, and recent actions.
  - Focus management UI allows setting focused district with visual indication on map and in panels.
  - Heat map overlays toggle on city map showing pollution, unrest, or stability with color gradients.
  - Batch run summary panel displays results after "Run N" commands: ticks executed, key events, metric changes, crisis alerts.
  - At least 12 tests covering agent interactions, faction displays, focus setting, and heat map rendering.
- **Priority:** Medium
- **Responsible:** Development Team
- **Dependencies:** 12.1.1 (core UI), existing agent/faction systems, focus manager (M4.6).
- **Risks & Mitigations:**
  - Risk: Information overload from too many panels. Mitigation: Use tabbed views or toggleable panels.
  - Risk: Heat maps difficult to read in ASCII. Mitigation: Use clear color gradients and include legend.
- **Next Steps:**
  1. Design agent roster table layout with sort/filter options.
  2. Implement faction overview panel with relationship visualization.
  3. Add focus management UI controls (dropdown or map-based selection).
  4. Create heat map overlay system with multiple metric options.
  5. Build batch run summary panel with metric delta highlighting.
  6. Test all management interactions and data flows.
- **Last Updated:** 2025-12-05

### 12.3.1 — Understanding & Reflection UI (M12.3)

- **Description:** Build UI components for understanding causality and reflecting on campaign outcomes: Why/Explanation system integration, timeline view with causality, campaign hub, post-mortem screen, and progressive disclosure system. This helps players learn from their decisions and understand emergent narratives.
- **Acceptance Criteria:**
  - "Why" button/command opens explanation panel showing causal chain for selected event or metric change (integrates existing explanation system from M7.2).
  - Timeline view displays major events chronologically with causal links visualized (lines connecting related events).
  - Timeline filtering by event type (story seeds, faction actions, player actions, crises).
  - Campaign hub screen lists available campaigns with save dates, ticks played, and current status.
  - Post-mortem screen shows end-of-campaign summary: final stability, faction outcomes, story arcs completed, key turning points, "what could have been" scenarios.
  - Progressive disclosure: tooltips on first-time UI element encounters, tutorial triggers for new players, adjustable detail levels.
  - At least 10 tests covering explanation display, timeline rendering, campaign hub navigation, and post-mortem generation.
- **Priority:** Medium
- **Responsible:** Development Team
- **Dependencies:** 12.1.1 (core UI), explanation system (M7.2), campaign system (M7.4), narrative director (Phase 5).
- **Risks & Mitigations:**
  - Risk: Timeline view becomes cluttered with many events. Mitigation: Implement filtering, zoom controls, and event grouping.
  - Risk: Post-mortem generation computationally expensive. Mitigation: Pre-compute summaries during campaign end, cache results.
- **Next Steps:**
  1. Integrate explanation API into UI with modal/panel display.
  2. Design timeline view layout with event nodes and causal edges.
  3. Implement timeline filtering and zoom controls.
  4. Build campaign hub screen with campaign listing and resume flow.
  5. Create post-mortem screen with summary statistics and narrative recap.
  6. Add progressive disclosure system (tooltips, tutorials, help overlays).
  7. Test understanding flows and user feedback mechanisms.
- **Last Updated:** 2025-12-05

### 12.4.1 — Polish & Accessibility (M12.4)

- **Description:** Final polish for production-ready UI: animations and feedback, complete keyboard navigation, accessibility audit and fixes, onboarding refinement, and help system integration. Ensures the UI meets usability and accessibility standards.
- **Acceptance Criteria:**
  - Smooth animations for state changes (number ticker for metrics, bar fill for gauges, subtle transitions).
  - Immediate visual feedback for all user interactions (selections, button presses).
  - Complete keyboard navigation for all UI elements with visible focus indicators and logical tab order.
  - Accessibility audit completed: color-independent information (icons + text labels), high contrast mode, screen reader support.
  - Adjustable pacing: configurable batch sizes, pause during batch runs, event feed scroll-lock.
  - Integrated help system: context-sensitive help (? icon), command reference, keyboard shortcuts documentation.
  - Onboarding flow for new players: tutorial mode, tooltips on first encounter, simplified initial UI.
  - At least 8 tests covering accessibility features, keyboard navigation, and onboarding flows.
- **Priority:** Low
- **Responsible:** Development Team
- **Dependencies:** 12.1.1 (core UI), 12.2.1 (management UI), 12.3.1 (understanding UI).
- **Risks & Mitigations:**
  - Risk: Animations degrade performance on slower terminals. Mitigation: Make animations optional via config.
  - Risk: Accessibility issues discovered late. Mitigation: Conduct early accessibility review of core UI (M12.1).
- **Next Steps:**
  1. Implement animation system with configurable timing and effects.
  2. Audit keyboard navigation paths and add missing shortcuts.
  3. Run accessibility audit (color contrast, screen reader, keyboard-only usage).
  4. Add high contrast mode and color-independent indicators.
  5. Build integrated help system with context-aware content.
  6. Design and implement onboarding tutorial flow.
  7. User testing with focus on accessibility and new player experience.
- **Last Updated:** 2025-12-05

### 12.5.1 — UI Testing & Validation (M12.5)

- **Description:** Comprehensive testing of the UI implementation against success metrics defined in the design document. Includes automated UI tests, user testing sessions, performance validation, and documentation updates.
- **Acceptance Criteria:**
  - Success metrics tracked: Time to First Action (<30s), Crisis Detection (<5s), Causality Understanding (80%+ accuracy), Focus Comprehension (90%+ awareness), Agent Selection Confidence (informed choice), Session Satisfaction (4+/5 rating).
  - Automated UI test suite covers all major workflows: campaign start, district selection, agent assignment, batch execution, explanation queries, timeline viewing, campaign end.
  - Performance testing validates UI responsiveness: <100ms render time for most updates, <1s for complex views (timeline, post-mortem).
  - User testing sessions with 5+ testers, feedback collected and documented.
  - Regression test suite prevents UI breakage in future changes.
  - Documentation updated: UI user guide, keyboard shortcuts reference, troubleshooting guide.
  - At least 20 end-to-end UI tests covering complete player workflows.
- **Priority:** Medium
- **Responsible:** Development Team + QA
- **Dependencies:** 12.1.1, 12.2.1, 12.3.1, 12.4.1 (all UI implementation tasks).
- **Risks & Mitigations:**
  - Risk: User testing reveals major usability issues late. Mitigation: Conduct iterative testing throughout development, not just at end.
  - Risk: Automated UI tests brittle and hard to maintain. Mitigation: Use stable selectors and design for testability.
- **Next Steps:**
  1. Define automated test scenarios covering all UI workflows.
  2. Implement end-to-end UI test suite.
  3. Set up performance monitoring for UI operations.
  4. Recruit user testers and design test protocol.
  5. Conduct user testing sessions and collect feedback.
  6. Measure success metrics and identify gaps.
  7. Update documentation with UI usage guides.
- **Last Updated:** 2025-12-05

---
