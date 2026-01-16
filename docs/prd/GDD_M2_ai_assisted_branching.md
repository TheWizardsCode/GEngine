# Product Requirements Document

## Introduction

### One-liner
Add M2: AI-assisted branching support to enable runtime integration of AI-proposed story branches with an automated policy and sanitization guardrail.

### Problem statement
At runtime, players will be able to drive the story into unscripted flows. The priority is the player's experience: the AI Director guides unscripted branching so the story remains coherent and returns the narrative to the scripted path within a defined number of player choice points. An AI Writer will dynamically author story content using recorded LORE, character definitions, and the player's recent actions as inputs. The system must ensure the emergent branches remain playable, on-theme, and do not create dead-ends or permanent divergence from the intended story arc.

### Goals
- Define a clear design for accepting AI-proposed branches, running automated policy checks and sanitization, and integrating approved branches into the runtime story state.
- Provide acceptance criteria and testable validation for the policy pipeline and serialization schema for proposals.
- Produce integration guidance for runtime hooks and developer UX for approving and reverting branches.

### Non-goals
- This PRD does not mandate specific LLM providers or runtime hosting choices.
- This PRD does not require human-in-loop approval (the chosen guardrail model is automated policy and sanitization).

## Users

### Primary users
Internal producers and tooling engineers who will generate and validate AI-proposed branches for demo stories.

### Secondary users (optional)
Writers and designers who may later review, accept, or refine AI-proposed branches.

### Key user journeys
- Propose branch: an authoring tool or automated process generates candidate branches for a given story context and submits them to the validation pipeline.
- Validate branch: automated policy and sanitization checks run; if the branch passes, it is marked `validated` and becomes eligible for integration.
- Integrate branch: runtime hooks apply the validated branch into story state; the branch can be persisted and surfaced in telemetry.
- Revert branch: if issues are discovered post-integration, a rollback mechanism removes or disables the branch.

## Requirements

### Functional requirements (MVP)

#### Branch proposal interface
- Define a stable JSON schema for branch proposals that includes metadata (source, model version, confidence), story context, and branch content (Ink fragment or delta).
- Provide an API endpoint or CLI command for submitting proposals for validation.

#### Policy & sanitization pipeline
- Implement automated policy checks (profanity, disallowed categories, length limits, prohibited patterns) configurable via a ruleset.
- Implement sanitization transforms (strip unsafe HTML, normalize whitespace, enforce encoding) and a deterministic sanitizer to reduce variance.
- Produce a validation report schema indicating pass/fail and rule-level diagnostics.

#### Validation outcome and lifecycle
- Store proposals with states: `submitted`, `validated`, `rejected`, `sanitized`, `integrated`, `reverted`.
- Attach validation reports and timestamps to proposals; make them queryable via API.

#### Runtime integration hooks (design only)
- Design hook points where validated branch content can be applied into the running story state with clear transaction boundaries.
- Define rollback semantics and persistence model for integrated branches.

#### AI Director and AI Writer (design inputs)
- AI Director
  - Runtime control component responsible for steering emergent AI-generated flows toward coherence.
  - Enforces a configurable 'return window' (maximum number of player choice points before forcing a return to scripted path).
  - Evaluates player context, branch proposals, pacing, and risk metrics before triggering integration.
- AI Writer
  - Dynamically authors branch content using recorded LORE, character definitions, and recent player actions.
  - Produces proposals that conform to the branch proposal schema and include provenance metadata.

#### Observability
- Emit telemetry events for proposal submission, validation result, integration, reversion, and Director decisions with a minimal schema.

### Non-functional requirements

#### Determinism
- Validation pipeline should be deterministic given the same input and ruleset version.

#### Performance
- Validation should complete within a target (e.g., < 2s) for small proposals to allow near-interactive workflows.
- Director decisions should meet a lower-latency target appropriate for player-facing flows.

#### Configurability
- Policy rulesets, sanitizers, and the Director's 'return window' should be configurable without code changes.

#### Auditability
- All proposals, validation reports, and Director decisions must be retained with versioning for audits.

### Integrations
- The PRD is provider-agnostic: allow pluggable LLMs or authoring tools to submit proposals via a standard schema.
- Validation ruleset should be compatible with existing telemetry and logging systems.

### Security & privacy
- Security note: treat proposal content as untrusted input; run sanitizers and Writer/Director processing in isolated execution environments and validate encoding before applying to runtime.
- Privacy note: redact or avoid storing PII in proposals; if storing is required, ensure encryption-at-rest and limited access.

## Release & Operations

### Rollout plan
#### Phase 0 — Design
- Final PRD approval and schema definitions; spike validation pipeline prototypes in dev.

#### Phase 1 — Validation-only
- Implement pipeline and run validation on proposals; no automatic runtime integration.

#### Phase 2 — Integration
- Enable runtime hooks for auto-integration of validated branches (behind feature flag) and pilot the Director/Writer in controlled stories.

#### Phase 3 — Monitor & iterate
- Gather telemetry, refine rulesets and Director heuristics, and consider adding human-in-loop for safety-sensitive content.

### Quality gates / definition of done
- Proposal schema defined and documented.
- Policy and sanitization ruleset implemented and tested against a corpus of example proposals.
- Validation pipeline deterministic and passing an agreed test suite.
- Director design specifies 'return window' semantics and test cases; Writer produces example proposals that preserve LORE and character consistency.

### Risks & mitigations
#### Risk: Director fails to return to scripted path within the window
- Mitigation: add fail-safe that forces a deterministic fallback to scripted content after the window expires and log the event for analysis.

#### Risk: Writer produces content that drifts off-theme
- Mitigation: enforce strong contextualization using LORE and character constraints and add style/content tests in the validation suite.

#### Risk: Performance bottleneck in validation or Director decisioning
- Mitigation: profile and set size/complexity limits; consider async validation for large proposals.

## Open Questions

### Runtime constraints
- What should the Director 'return window' be (number of player choice points)?

### Policy
- What are concrete rule categories for the policy (e.g., profanity, sexual content, political content)?

### Storage & access
- What retention period and access controls should apply to proposal storage?

### Validation UX
- Should validation run synchronously in authoring tools, or should large proposals be validated asynchronously?

### Authoring visibility
- Should sanitized diffs be exposed automatically to downstream writers for review?

## Open Questions (Technical Consistency Notes)
- Document states automated-only; mentions human-in-loop elsewhere but not as requirement; adding Open Question to clarify if human-in-loop may be added later
