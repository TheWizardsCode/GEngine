# Product Requirements Document

## Introduction

### One-liner
Add M2: AI-assisted branching support to enable runtime integration of AI-proposed story branches with an automated policy and sanitization guardrail, with robust runtime integration, rollback semantics, and save/load compatibility.

### Problem statement
Players should be able to drive stories into unscripted flows while preserving narrative coherence and playability. This update (ge-hch.5.16) focuses on runtime integration: formalizing a branch lifecycle state machine, atomic checkpoint/rollback semantics, persistence for auditability, and save/load compatibility so integrated branches survive reloads without corrupting saves.

### Goals
- Enable emergent, AI-generated story branches that feel coherent and on-theme without hand-crafting every branch.
- Ensure the AI Director steers unscripted flows back to scripted content within a configurable 'return window' of player choice points.
- Provide robust runtime integration: transaction-like injection with checkpoints, rollback support, audit logs, and graceful recovery on failures.
- Give producers and designers clear diagnostics and tooling to monitor, validate, and refine branching behavior.

### Non-goals
- Do not mandate specific LLM providers, hosting models, or backend architectures.
- Do not require human-in-loop approval for every branch proposal; M2 uses automated policy and sanitization for runtime decisions.
- Do not enable broad multi-threaded world-state rewrites or permanent cross-save world changes beyond return-window semantics.

## Users

### Primary users
Players on desktop and mobile browsers who encounter AI-generated branches during play.

### Secondary users (optional)
- Producers and tooling engineers validating branch proposals and tuning policy rules.
- Writers and designers analyzing branch performance and refining content.
- Analytics and ops teams monitoring telemetry and incident signals.

### Key user journeys
- Player journey: trigger → Writer generates proposal → Director validates → approved branch injected → player experiences branch → branch returns to scripted path within the configured window. Success: no save corruption; save/load preserves branch state; graceful recovery on failures.
- Producer/designer: generate candidate branches → run validation pipeline → inspect diagnostics → mark eligible content for runtime. Success: clear, queryable validation reports and audit logs.
- Ops: detect rollback or fail-safe events → inspect audit logs → remediate. Success: recover from branch failures without user-facing data loss.

## Requirements

### Functional requirements (MVP)
- Player experience: unscripted branching at runtime
  - When a player choice triggers an unscripted condition, the AI Writer produces a branch proposal conforming to the branch-proposal schema.
  - The Director validates and approves or rejects proposals; approved proposals may be integrated at defined Hook Points.
  - Integration uses explicit transaction boundaries: checkpoint before injection, commit after successful integration.
  - Branch history persists to save metadata so save/load cycles reproduce integrated branches.
  - If execution fails, automatic rollback restores the last safe checkpoint and shows a friendly message: "The story encountered an issue. Returning to last save point."

- Runtime integration (ge-hch.5.16 specifics)
  - Implement a 12-state integration state machine for the branch lifecycle from acceptance through execution and terminal states.
  - Implement atomic checkpointing and rollback: capture required runtime state (inventory, scene state, branch progress) and restore it deterministically on rollback.
  - Persist integration logs and metadata (branch ID, proposal hash, timestamps, decision trace) for audit and reproducibility.
  - Ensure save/load compatibility: in-progress branches resume correctly on load or roll back safely if corrupted.
  - Audit logging: record state transitions, decisions, commits, and rollback events with sufficient context for debugging.

- Branch proposal validation pipeline
  - Run automated policy checks and sanitization transforms before runtime approval (content safety, narrative consistency, return-path validity).
  - Produce validation reports with rule-level diagnostics and retain them per retention policy.

- Telemetry and hooks
  - Emit telemetry for proposal submission, validation outcome, Director decision, integration commit/rollback, and player outcome.
  - Provide a hook manager in `src/runtime/` for registering pre/post integration callbacks (telemetry, UI updates, persistence).

### Non-functional requirements
- Determinism and reproducibility
  - Validation results are deterministic for the same input and ruleset version.
  - Checkpoint/restore deterministically reproduces play state for successful branch replay.

- Performance and responsiveness (reliability-first)
  - Reliability and data integrity are the top priority; correctness takes precedence over aggressive latency targets for the runtime integration path.
  - Writer generation may take 1–3s per beat; integration must tolerate generation latency without corrupting saves.

- Reliability and safety
  - Saves and checkpoints must be atomic and verifiable; corrupted or partial integrations must not render a save unusable.
  - Rollback must restore a known-good state without data loss.

- Configurability
  - Policy rulesets, sanitizers, Director 'return window', and risk thresholds must be configurable at runtime or via configuration files.

- Auditability and retention
  - Retain proposals, validation reports, and Director decisions per retention policy. Audit logs must include timestamps, actor, action, and outcome.

### Integrations
- Pluggable LLM adapters (provider-agnostic) and compatibility with the Ink runtime and its save/load mechanism.
- Telemetry and analytics pipelines (event stream or warehouse) for post-launch analysis.
- Hook manager in `src/runtime/` for registering persistence, telemetry, and UI callbacks.

### Security & privacy
- Security note: treat proposal content as untrusted input; run sanitizers and validation in isolated execution environments before applying to runtime.
- Privacy note: redact or avoid storing PII in proposals; store only policy-allowed metadata in audit logs; encrypt sensitive storage and enforce access control.
- Safety note: failed branches and policy violations must be logged (not silently dropped) with rule-level diagnostics available to producers.

## Release & Operations

### Rollout plan
- Phase 0 — Design (this PRD update)
  - Finalize PRD for ge-hch.5.16 and update schema docs for save metadata and integration logs.

- Phase 1 — Validation-only
  - Implement and validate the policy pipeline against a corpus of example proposals; do not enable runtime injection.

- Phase 2 — Limited integration (feature-flagged)
  - Implement the runtime hook manager, 12-state integration state machine, checkpoint/rollback, integration logging, and save/load branch metadata for a controlled demo/story; pilot with internal playtesters.

- Phase 3 — Soft launch and monitoring
  - Controlled rollout with a kill-switch, operator alerts on rollback/failures, and monitoring for save corruption or frequent rollbacks.

- Phase 4 — Scale and iterate
  - Expand to additional stories, refine Director heuristics, and add producer tooling for tuning and remediation.

### Quality gates / definition of done
- `src/runtime/` implemented with hook manager and 12-state state machine.
- Checkpoint/rollback mechanism tested across save/load cycles with no save corruption in the test suite.
- Integration audit logging present and queryable; branch history appears in save metadata and reproduces branch state on load.
- Validation pipeline deterministic and passing acceptance tests.
- Telemetry events emitted for proposal → decision → integration → outcome.
- Internal playtester coherence rating meets agreed target and pilot saves require operator intervention no more than X% (to be defined in Phase 2 planning).

### Risks & mitigations
- Risk: Branch integration corrupts save files
  - Mitigation: use atomic checkpoint/commit patterns; run fuzz testing on save/restore; include migration/version checks on load.
- Risk: Frequent rollbacks reduce player trust
  - Mitigation: conservative policy defaults, restrict integration to safe hook points, and pre-validate structures for initial rollouts.
- Risk: Audit logs leak sensitive data
  - Mitigation: redact PII, limit retention, and encrypt logs at rest.
- Risk: Director latency impacts UX
  - Mitigation: prioritize reliability; cache safe decisions where appropriate and surface a friendly loading state during generation.

## Open Questions
- Which story-specific policy overrides are required for the pilot demo (genre-specific rule relaxations)?
- Confirm exact save metadata fields required for branch history (proposal_id, proposal_hash, integration_state, timestamp, branch_progress).
- Who is on-call for Phase 2 pilot incidents and what alerting channels should be used?
- Rollback UX: toast-only, short explanation, or explanation + telemetry opt-in prompt after a rollback event?
- Pilot acceptance metric X: what is the acceptable operator-intervention rate for Phase 2?

---

Change log (this update):
- 2026-01-18: Updated PRD to include ge-hch.5.16 runtime integration specifics: 12-state integration state machine, atomic checkpoint/rollback semantics, persistence and audit logging, and save/load branch history (MVP set to include audit logging and save metadata per requested scope B). Emphasized reliability-first non-functional priorities.

This PRD update is saved at `docs/prd/GDD_M2_ai_assisted_branching.md`. Please review and indicate edits or approval. After you approve I'll run the automated five-stage review pipeline and finalize bead labels as instructed.
