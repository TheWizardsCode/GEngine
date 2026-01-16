# Product Requirements Document

## Introduction

One-liner

Add M2: AI-assisted branching support to enable runtime integration of AI-proposed story branches with an automated policy and sanitization guardrail.

Problem statement

Authors and producers need a safe, repeatable way to propose and integrate AI-generated branches without introducing unsafe, incoherent, or policy-violating content.

Goals

Define a clear design for accepting AI-proposed branches, running automated policy checks and sanitization, and integrating approved branches into the runtime story state. Provide acceptance criteria and testable validation for the policy pipeline and serialization schema for proposals. Produce integration guidance for runtime hooks and developer UX for approving and reverting branches.

Non-goals

This PRD does not mandate specific LLM providers or runtime hosting choices. This PRD does not require human-in-loop approval (the chosen guardrail model is automated policy and sanitization).

## Users

Primary users

Internal producers and tooling engineers who will generate and validate AI-proposed branches for demo stories.

Secondary users (optional)

Writers and designers who may later review, accept, or refine AI-proposed branches.

Key user journeys

Propose branch: an authoring tool or automated process generates candidate branches for a given story context and submits them to the validation pipeline.

Validate branch: automated policy and sanitization checks run; if the branch passes, it is marked `validated` and becomes eligible for integration.

Integrate branch: runtime hooks apply the validated branch into story state; the branch can be persisted and surfaced in telemetry.

Revert branch: if issues are discovered post-integration, a rollback mechanism removes or disables the branch.

## Requirements

Functional requirements (MVP)

Branch proposal interface

Define a stable JSON schema for branch proposals that includes metadata (source, model version, confidence), story context, and branch content (Ink fragment or delta). Provide an API endpoint or CLI command for submitting proposals for validation.

Policy and sanitization pipeline

Implement automated policy checks (profanity, disallowed categories, length limits, prohibited patterns) configurable via a ruleset. Implement sanitization transforms (strip unsafe HTML, normalize whitespace, enforce encoding) and a deterministic sanitizer to reduce variance. Produce a validation report schema indicating pass/fail and rule-level diagnostics.

Validation outcome and lifecycle

Store proposals with states: `submitted`, `validated`, `rejected`, `sanitized`, `integrated`, `reverted`. Attach validation reports and timestamps to proposals; make them queryable via API.

Runtime integration hooks (design only)

Design hook points where validated branch content can be applied into the running story state with clear transaction boundaries. Define rollback semantics and persistence model for integrated branches.

Observability

Emit telemetry events for proposal submission, validation result, integration, and reversion with a minimal schema.

Non-functional requirements

Determinism: the validation pipeline should be deterministic given the same input and ruleset version.

Performance: validation should complete within a target (e.g., < 2s) for small proposals to allow near-interactive workflows.

Configurability: policy rulesets and sanitizers should be configurable without code changes.

Auditability: all proposals and validation reports must be retained with versioning for audits.

Integrations

The PRD is provider-agnostic: allow pluggable LLMs or authoring tools to submit proposals via a standard schema. Validation ruleset should be compatible with existing telemetry and logging systems.

Security & privacy

Security note: treat proposal content as untrusted input; run sanitizers in an isolated execution environment and validate encoding before applying to runtime.

Privacy note: redact or avoid storing PII in proposals; if storing is required, ensure encryption-at-rest and limited access.

## Release & Operations

Rollout plan

Phase 0 (Design): final PRD approval and schema definitions; spike validation pipeline prototypes in dev.

Phase 1 (Validation-only): implement pipeline and run validation on proposals; no automatic runtime integration.

Phase 2 (Integration): enable runtime hooks for auto-integration of validated branches (behind feature flag).

Phase 3 (Monitor & iterate): gather telemetry, refine rulesets, and consider adding human-in-loop if necessary.

Quality gates / definition of done

Proposal schema defined and documented. Policy and sanitization ruleset implemented and tested against a corpus of example proposals. Validation pipeline deterministic and passing an agreed test suite. Rollback semantics documented and a revert mechanism exists in design (implementation optional for design phase).

Risks & mitigations

Risk: Over-restrictive ruleset rejects useful branches.
Mitigation: keep ruleset configurable and provide clear diagnostics for tuning.

Risk: Sanitization alters story intent.
Mitigation: log diffs between original and sanitized content and provide developer-visible diagnostics.

Risk: Performance bottleneck in validation.
Mitigation: profile and set size limits; consider async validation for large proposals.

## Open Questions

What are concrete rule categories for the policy (e.g., profanity, sexual content, political content)?

What retention period and access controls should apply to proposal storage?

Should validation run synchronously in authoring tools, or should large proposals be validated asynchronously?

Should sanitized diffs be exposed automatically to downstream writers for review?

## Open Questions (Technical Consistency Notes)

Document states automated-only; mentions human-in-loop elsewhere but not as requirement; adding Open Question to clarify if human-in-loop may be added later
