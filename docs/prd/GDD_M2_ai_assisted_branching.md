# Product Requirements Document

## Introduction

### One-liner
Add M2: AI-assisted branching support to enable runtime integration of AI-proposed story branches with an automated policy and sanitization guardrail.

### Problem statement
At runtime, players will be able to drive the story into unscripted flows. The priority is the player's experience: the AI Director guides unscripted branching so the story remains coherent and returns the narrative to the scripted path within a defined number of player choice points. An AI Writer will dynamically author story content using recorded LORE, character definitions, and the player's recent actions as inputs. The system must ensure the emergent branches remain playable, on-theme, and do not create dead-ends or permanent divergence from the intended story arc.

### Goals
- Enable players to experience emergent, AI-generated story branches that feel coherent and on-theme without author hand-crafting every branch.
- Ensure the AI Director reliably steers unscripted flows back to the authored narrative within a configurable 'return window' (player choice points).
- Design a safe, policy-driven validation pipeline that prevents unsafe, incoherent, or off-theme content from reaching players.
- Provide producers and designers with tooling to monitor, validate, and refine emergent branching in production.

### Non-goals
- This PRD does not mandate specific LLM providers or runtime hosting choices.
- This PRD does not require human-in-loop approval for every branch proposal (the chosen guardrail model is automated policy and sanitization).
- This PRD does not cover complex branching scenarios (e.g., multi-threading, permanent world state changes, or dynamic character resurrection).

## Users

### Primary users (end-players)
Players on desktop/mobile browsers who will experience emergent story branches during gameplay.

### Secondary users (authoring and ops)
- Producers and tooling engineers who will generate and validate AI-proposed branches for demo stories.
- Writers and designers who may review, refine, or disable AI-generated branches post-launch.
- Runtime operators who monitor telemetry and Director performance.

### Key user journeys

#### Player journey: unscripted branching
- Player makes a story choice that triggers an unscripted condition.
- AI Writer generates a branch proposal based on LORE, character state, and player action.
- AI Director validates and evaluates the proposal against constraints and pacing.
- If approved, the branch is seamlessly integrated into the story; the player continues without interruption.
- The Director ensures the branch paces toward a return to the scripted path within the configured window.

#### Producer/designer journey: branch validation and refinement
- Authoring tool or batch process generates candidate branches for a given story context.
- Policy and sanitization pipeline automatically validates proposals (profanity, coherence, theme consistency).
- Producers review validation reports and can approve, reject, or request refinements.
- Approved branches are marked eligible for runtime integration; rejected branches are logged for analysis.

#### Runtime operator journey: monitoring and safety
- Operators observe telemetry events for branch proposals, Director decisions, and player outcomes.
- If a branch causes player confusion or breaks immersion (detected via telemetry or player feedback), operators can disable or revert it via feature flags for post-mortem analysis.
- Logs and audit trails track all decisions for retrospective analysis and improvement of policy rules and Director heuristics.
- **Note**: No human-in-loop approval is required at runtime; all acceptance decisions are automated (policy + Director).

## Requirements

### Functional requirements (MVP)

#### Player experience: unscripted branching at runtime
- At runtime, when a player choice triggers an unscripted condition, the system generates and integrates an AI-authored branch.
- The branch seamlessly continues the story without breaking immersion or narrative coherence.
- Players cannot distinguish between hand-authored and AI-generated branches (quality target).
- The system guarantees a return to the scripted narrative within the configured 'return window' (e.g., N player choice points).

#### AI Director (runtime governance)
- Evaluates incoming branch proposals from the AI Writer in real-time (latency target: < 500ms per decision).
- Applies risk metrics and coherence checks: thematic consistency, LORE adherence, character voice preservation, narrative pacing.
- Enforces the 'return window' constraint: ensures the proposed branch includes a bridging pathway back to scripted content.
- Provides a fail-safe mechanism: if the Director cannot find a coherent return path, it auto-reverts to scripted content and logs the event.
- Emits decision telemetry: proposal timestamp, approval/rejection reason, detected risk score.

#### AI Writer (runtime content generation)
- Generates branch proposals using recorded LORE, character definitions, and recent player actions as context.
- Proposal schema includes: metadata (confidence score, provenance), story context (current scene, player inventory, character state), branch content (Ink fragment or delta).
- Produces deterministic, reproducible output for the same inputs (same context + same LLM seed = same proposal).
- Outputs proposals that conform to the branch proposal schema and include provenance metadata (LLM model version, timestamp).

#### Branch proposal validation pipeline
- Automated policy checks: profanity, disallowed categories, length limits, prohibited narrative patterns.
- Sanitization transforms: strip unsafe HTML, normalize whitespace, enforce character encoding.
- Produces validation reports with pass/fail status and rule-level diagnostics (which rules triggered, which content was sanitized).
- Stores proposals with states: `submitted`, `validated`, `rejected`, `sanitized`, `integrated`, `reverted`.
- Allows queryable access to proposals and validation reports via API or database.

#### Runtime integration hooks
- Design hook points where validated branch content can be applied into the running story state with clear transaction boundaries.
- Define rollback semantics: if a branch causes a runtime error or player complaint, operators can safely revert it without corrupting save state.
- Persistence model: integrated branches are logged to ensure reproducibility and audit trails.

#### Observability for players, producers, and operators
- Emit telemetry events for each stage: proposal submission, validation result, Director decision, branch integration, player outcome.
- Minimal schema: event type, timestamp, branch ID, decision outcome, confidence/risk score.
- Player-facing telemetry: detect whether a player found a branch confusing or satisfying (via post-story survey or behavioral signals).
- Operator dashboard: real-time and historical views of branch success rates, Director decision latency, and policy violation patterns.

### Non-functional requirements

#### Determinism and reproducibility
- Validation pipeline must be deterministic: same input + same ruleset version → same validation result.
- AI Writer proposals should be reproducible: same LORE + same player context + same LLM seed → same proposal.

#### Performance and responsiveness
- Branch proposal validation: complete within 2s (authoring time, not latency-critical).
- AI Director decision: complete within 500ms (player-facing, latency-critical; must feel real-time).
- Proposal generation (AI Writer): target 1–3s per branch (background process; can be async).

#### Configurability
- Policy rulesets, sanitizers, and the Director's 'return window' should be configurable without code changes (e.g., via config file or runtime flags).
- Director risk thresholds and coherence weights should be tunable.

#### Auditability and logging
- All proposals, validation reports, and Director decisions must be retained with versioning for audits.
- Audit logs include timestamps, actor (system component), action, and outcome.
- Support historical analysis: "why did a branch get rejected?" or "when did the Director last fail to find a return path?"

### Integrations
- The PRD is provider-agnostic: allow pluggable LLMs (OpenAI, Claude, local models) or authoring tools to submit proposals via a standard schema.
- Validation ruleset should be compatible with existing telemetry and logging systems (e.g., event streaming, analytics warehouses).
- Support integration with the existing Ink runtime and save/load systems (branch state must not corrupt existing save files).

### Security & privacy
- Security note: treat proposal content as untrusted input; run sanitizers and Writer/Director processing in isolated execution environments and validate encoding before applying to runtime.
- Privacy note: redact or avoid storing PII in proposals; if storing is required, ensure encryption-at-rest and limited access.
- Safety note: failed branches and policy violations must be logged (not silently dropped) to detect potential attacks or author errors.

## Release & Operations

### Rollout plan
#### Phase 0 — Design (this PRD)
- Final PRD approval and schema definitions.
- Spike validation pipeline prototypes in dev.
- Prototype AI Director and AI Writer interfaces.
- Define 'return window' semantics and test cases.

#### Phase 1 — Validation-only
- Implement branch proposal validation pipeline.
- Run validation on candidate branches; collect statistics (acceptance rate, top policy violations).
- No automatic runtime integration; branches are validated but not yet served to players.
- Gather feedback from producers on policy ruleset tuning.

#### Phase 2 — Limited integration (feature-flagged)
- Enable runtime hooks for branch integration in a controlled story or demo.
- Implement AI Director with initial coherence heuristics and 'return window' enforcement.
- Implement AI Writer with basic LORE-based generation.
- Pilot with internal playtesters and gather telemetry on Director success rate, player coherence perception.

#### Phase 3 — Soft launch and monitoring
- Roll out to live players with feature flags and kill-switches.
- Gather player feedback, Director decision latency, and policy violation patterns.
- Refine rulesets, Director heuristics, and Writer LORE context based on telemetry.
- Plan for human-in-loop review if safety concerns emerge.

#### Phase 4 — Scale and iterate (post-M2)
- Expand to additional stories and narrative scenarios.
- Add player-facing UX signals (e.g., "this choice was AI-generated"; trust/transparency features).
- Continuous tuning of Director heuristics and Writer prompts based on production telemetry.

### Quality gates / definition of done
- Proposal schema defined, documented, and validated with at least 10 example proposals.
- Policy ruleset implemented and tested against a corpus of ≥100 example branches; documented ruleset with rationale for each rule.
- Validation pipeline deterministic and passing an agreed test suite (≥20 test cases covering edge cases).
- AI Director design specifies 'return window' semantics, risk-scoring algorithm, and fail-safe fallback; includes test cases for both success and failure scenarios.
- AI Writer produces ≥5 example proposals that preserve LORE consistency, character voice, and narrative coherence.
- Branch integration hooks designed with rollback semantics tested (e.g., corrupted branch can be safely reverted).
- Telemetry schema defined and emitted correctly in test environment.
- Player experience validation: internal playtesters rate merged (hand-authored + AI-generated) stories; coherence score ≥4/5 (arbitrary scale).

### Risks & mitigations

#### Risk: AI Director fails to return to scripted path within the window
- Impact: player gets stuck in an infinite or dead-end unscripted loop; breaks immersion and breaks the story.
- Mitigation: implement a deterministic fail-safe that forces a return to scripted content after the window expires; log the event with high priority (alert operators).
- Mitigation: test the Director's return-path logic exhaustively during Phase 1–2; profile common failure modes.

#### Risk: AI Writer produces content that drifts off-theme or contradicts LORE
- Impact: player experiences an incoherent or jarring branch; reduces trust in emergent storytelling.
- Mitigation: enforce strong LORE and character constraints in the Writer's prompt; include embeddings or semantic similarity checks in the validation suite.
- Mitigation: add style/content tests that flag branches differing >N% from the original story's tone; collect examples from playtesters.

#### Risk: Policy pipeline is over-restrictive or under-restrictive
- Impact: either rejects too many valid branches (reduces emergent variety) or allows policy violations (safety breach).
- Mitigation: keep ruleset configurable and provide diagnostics for each rule (why was this branch rejected?); gather feedback from producers in Phase 1.
- Mitigation: start with a conservative policy and loosen it iteratively based on playtest feedback.

#### Risk: Performance bottleneck in Director decision latency
- Impact: branch integration is delayed; player sees a stall or "thinking" state; breaks immersion.
- Mitigation: profile Director decision-making during Phase 2; optimize hot paths (risk scoring, return-path search).
- Mitigation: consider pre-computing Director decisions for likely player choices (offline analysis).

#### Risk: Emergent branches undermine authored narrative intent
- Impact: players explore unscripted content that diminishes the story's themes or message.
- Mitigation: include thematic alignment as a Director risk metric; require branches to include explicit narrative intent statements.
- Mitigation: empower producers with tools to review and disable problematic branches; maintain a "banned branches" list.

## Open Questions

### Runtime constraints
- What should the Director 'return window' be (number of player choice points)? (Suggested: 3–5 choices).
- What latency target should the Director and AI Writer meet? (Suggested: Director < 500ms; Writer 1–3s).

### AI Writer and LORE
- How is LORE recorded and updated at runtime (manual annotations, auto-extracted, hybrid)?
- What is the minimum context size (LORE + character state) needed for coherent Writer output?

### Policy and safety
- What are concrete rule categories for the policy (e.g., profanity, sexual content, political content, narrative red lines)?
- Should the policy be story-specific or global?

### Storage & access
- What retention period and access controls should apply to proposal storage?
- Should proposal data be encrypted or anonymized after a branch is deployed?

### Player experience metrics
- How should we measure player coherence perception (survey, behavioral signals, implicit feedback)?
- Should players be told when they encounter an AI-generated branch (transparency) or not (seamlessness)?

### Validation UX
- Should validation run synchronously in authoring tools, or should large proposals be validated asynchronously?
- Should sanitized diffs be exposed automatically to downstream writers for review?

## Clarification: No Human-in-Loop at M2 Runtime

**M2 is designed with automated validation only.** The PRD explicitly states (Non-goals, line 19) that "This PRD does not require human-in-loop approval for every branch proposal." All runtime acceptance decisions are made by the policy/sanitization pipeline and AI Director—no human approval is required.

**Post-launch human involvement** is limited to:
- Operators monitoring telemetry and disabling problematic branches via feature flags (after-the-fact)
- Producers refining policy rules and Director heuristics based on player feedback (between phases)
- Future phases (Phase 3+) may introduce human-in-loop if safety concerns emerge at scale
