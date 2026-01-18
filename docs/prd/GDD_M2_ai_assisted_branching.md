# Product Requirements Document

## Introduction

### One-liner
Add M2: AI-assisted branching support to enable runtime integration of AI-proposed story branches with an automated policy and sanitization guardrail, with robust runtime integration, rollback semantics, and save/load compatibility.

### Problem statement
At runtime, players can drive the story into unscripted flows. The priority is the player's experience: the AI Director guides unscripted branching so the story remains coherent and returns the narrative to the scripted path within a defined number of player choice points. An AI Writer dynamically authors story content using recorded LORE, character definitions, and the player's recent actions as inputs. The system must ensure emergent branches remain playable, on-theme, and do not create dead-ends or permanent divergence from the intended story arc. This update focuses on formalizing runtime integration (ge-hch.5.16): state machine, checkpoint/rollback semantics, persistence for auditability, and save/load compatibility so branches survive reloads without corrupting saves.

### Goals
- Enable players to experience emergent, AI-generated story branches that feel coherent and on-theme without author hand-crafting every branch.
- Ensure the AI Director reliably steers unscripted flows back to the authored narrative within a configurable 'return window' (player choice points).
- Provide robust runtime integration: a formal state machine for branch injection, atomic checkpointing and rollback, persistence for branch history, and graceful recovery on failures.
- Provide producers and designers with tooling to monitor, validate, and refine emergent branching in production (audit logs, validation reports, branch metadata).

### Non-goals
- This PRD does not mandate specific LLM providers or runtime hosting choices.
- This PRD does not require human-in-loop approval for every branch proposal (the chosen guardrail model is automated policy and sanitization).
- This PRD does not cover complex multi-threaded world-state rewrites, permanent cross-save world changes, or dynamic character resurrection beyond the return-window semantics.

## Users

### Primary users
Players on desktop/mobile browsers who will experience emergent story branches during gameplay.

### Secondary users (optional)
- Producers and tooling engineers who generate and validate AI-proposed branches during development.
- Writers and designers who analyze branch performance and refine proposals between phases.
- Analytics and ops teams who monitor telemetry and handle incident response.

### Key user journeys
- Player journey: unscripted branching (trigger → Writer generates proposal → Director validates → branch injected → player experiences branch → branch returns to scripted path within return window). Success: no data corruption, save/load preserves branch state, graceful recovery on failure.
- Producer/designer journey: branch validation and refinement (generate candidates → validation pipeline → review diagnostics → mark eligible for runtime). Success: clear diagnostics and audit trails for tuning policy rules.
- Ops/incident journey: detection and recovery (fail-safe triggers or rollback events surface alerts; operators can inspect audit logs). Success: recover from branch failures with zero save corruption.

## Requirements

### Functional requirements (MVP)
- Player experience: unscripted branching at runtime
  - At runtime, when a player choice triggers an unscripted condition, the AI Writer produces a branch proposal conforming to the branch-proposal schema.
  - The Director validates and either approves or rejects the proposal. Approved proposals may be integrated into the running story at defined Hook Points.
  - Branches are injected with clear transaction boundaries (checkpoint before inject, commit after successful integration).
  - Branch history is persisted to save metadata so save/load cycles reproduce integrated branches.
  - If a branch fails during execution, automatic rollback reverts to the last safe checkpoint and displays a graceful player message ("The story encountered an issue. Returning to last save point.").

- Runtime integration (ge-hch.5.16 specifics)
  - Implement a 12-state integration state machine that formalizes the branch lifecycle from proposal acceptance through execution and terminal states.
  - Implement atomic checkpointing and rollback semantics: checkpoints capture necessary runtime state (player inventory, scene state, branch progress markers) and rollback restores to that checkpoint without corruption.
  - Persistence model: store branch integration logs and metadata (branch ID, proposal hash, timestamps, decision trace) to enable audit and reproducibility.
  - Save/load compatibility: integrated branches survive save/load cycles; loading a save with an in-progress branch resumes branch execution at the correct state or rolls back if corrupted.
  - Integration audit logging: log state transitions, decisions, and rollback events with sufficient context for debugging.

- Branch proposal validation pipeline
  - Automated policy checks (content safety, narrative consistency, return-path validity) and sanitization transforms run before runtime approval.
  - Validation reports include rule-level diagnostics and are retained per the retention policy.

- Telemetry and hooks
  - Emit telemetry events for proposal submission, validation outcome, Director decision, integration commit/rollback, and player outcome.
  - Provide a hook manager in `src/runtime/` where subsystems can register pre/post integration callbacks (telemetry emitters, UI updates, persistence actions).

### Non-functional requirements
- Determinism and reproducibility
  - Validation pipeline is deterministic for the same input and ruleset version.
  - Checkpointing/restore must deterministically restore play state for a successful branch replay.

- Performance and responsiveness (reliability-first)
  - Director decision latency is desirable but not mandatory—priority is reliability and zero data corruption. The PRD favors deterministic correctness over strict latency guarantees for runtime integration.
  - Proposal generation (Writer) target: 1–3s per beat (background) but runtime integration must not corrupt save files even if generation is slow.

- Reliability and safety
  - Atomic save/restore semantics: saves and checkpoints must be atomic and verifiable. A corrupted or partial branch integration must not render a save file unusable.
  - Rollback must restore a known-good state without data loss.

- Configurability
  - Policy rulesets, sanitizers, Director 'return window', and risk thresholds must be configurable without code changes.

- Auditability and retention
  - Retain proposals, validation reports, and Director decisions according to retention policy (see Storage & Access). Audit logs must include timestamps, actor, action, and outcome.

### Integrations
- Provider-agnostic LLM adapters (pluggable backends) and compatibility with existing Ink runtime and save/load systems.
- Telemetry and logging systems (event stream or analytics warehouse) for post-launch analysis.
- Hook points in `src/runtime/` (hook manager) for registering persistence, telemetry, and UI callbacks.

### Security & privacy
- Security note: treat proposal content as untrusted input; run sanitizers and validation in isolated execution contexts before applying to runtime.
- Privacy note: redact or avoid storing PII in proposals; store only policy-allowed metadata in audit logs; encrypt sensitive storage and enforce access controls.
- Safety note: failed branches and policy violations must be logged (not silently dropped) and include rule-level diagnostics for producers.

## Release & Operations

### Rollout plan
- Phase 0 — Design (this PRD update)
  - Finalize PRD for ge-hch.5.16 and update schema docs for save metadata and integration logs.

- Phase 1 — Validation-only
  - Implement validation pipeline and run against batch of example proposals; no runtime integration.

- Phase 2 — Limited integration (feature-flagged)
  - Implement runtime hook manager, 12-state state machine, checkpoint/rollback, integration logging, and save/load branch metadata for a controlled demo/story. Pilot with internal playtesters.

- Phase 3 — Soft launch and monitoring
  - Controlled rollout with kill-switch and operator alerts on rollback/failures. Monitor for save corruption or frequent rollbacks.

- Phase 4 — Scale and iterate
  - Expand to more stories, refine Director heuristics, and expose producer tooling for tuning.

### Quality gates / definition of done
- Runtime integration module (`src/runtime/`) implemented with hook manager and 12-state state machine.
- Checkpoint/rollback mechanism implemented and tested across save/load cycles; no save corruption in test suite.
- Integration audit logging present and queryable; branch history appears in save file metadata and reproduces branch state on load.
- Validation pipeline deterministic and passing acceptance test suite.
- Telemetry events emitted for proposal → decision → integration → outcome.
- Internal playtester coherence rating meets agreed target and no more than X% of pilot saves require operator intervention (X to be defined in Phase 2 planning).

### Risks & mitigations
- Risk: Branch integration corrupts save files
  - Mitigation: enforce atomic checkpoint/commit patterns; test save/restore thoroughly with fuzzed branch content; include migration/version checks on load.
- Risk: Frequent rollbacks reduce player trust
  - Mitigation: conservative policy defaults; restrict runtime integration to safe hook points and pre-validated structures for initial rollout.
- Risk: Audit logs leak sensitive data
  - Mitigation: redact PII, limit retention, and encrypt logs at rest.
- Risk: Director latency impacts UX
  - Mitigation: prioritize reliability; pre-compute or cache Director decisions where safe; surface a friendly loading state when generation is in progress.

## Open Questions
- Story-specific configuration: which story-specific policy overrides are required for the pilot demo? (e.g., genre-specific rule relaxations)
- Save metadata format: confirm exact fields required in save file metadata for branch history (proposal_id, proposal_hash, integration_state, timestamp, branch_progress).
- Operational readiness: who is on-call for Phase 2 pilot incidents and which alerting channels should be used?
- Rollback UX: should players see a toast only, or a short explanation + telemetry opt-in prompt after a rollback event?
- Pilot acceptance metric X: what is the acceptable operator-intervention rate for Phase 2 (replace X in Quality gates)?

---

Change log (this update):
- 2026-01-18: Updated PRD to include ge-hch.5.16 runtime integration specifics: 12-state integration state machine, atomic checkpoint/rollback semantics, persistence and audit logging, and save/load branch history (MVP set to include audit logging and save metadata per requested scope B). Emphasized reliability-first non-functional priorities.


This PRD update is saved at `docs/prd/GDD_M2_ai_assisted_branching.md`. Please review and indicate edits or approval. After you approve I'll run the automated five-stage review pipeline and finalize bead labels as instructed.