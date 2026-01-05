# Doc Draft — ge-hch.1.2.4 (Docs: Smoke)

> Temp, evolving draft created by `/doc ge-hch.1.2.4`
>
> **Do not delete.** This file is revised during implementation.

## Seed context

- Docs issue: **ge-hch.1.2.4** — *Docs: Smoke* (task)
  - Acceptance: docs explain how to **run, test, and validate** the Smoke feature.
  - Minimal implementation: add section to docs or feature README.
- Parent feature: **ge-hch.1.2** — *Project scaffold* (feature)
- Related epic: **ge-hch.1** — *M0 — Scaffold / Smoke Demo* (epic)
  - Epic success signals include: scene displays pages and advances with input; desktop + WebGL builds load without fatal runtime errors; telemetry console/file (TBD).

Authoritative existing docs reviewed:
- `docs/Unity_README.md` (Unity 6.2; open steps; M0 scene path; LFS guidance)
- `docs/dev/Workflow.md` (PRD-driven workflow; references `/doc`, “releasable main” quality gates)
- `docs/dev/git_workflow.md` (branching + handoff rules; bd comment expectations)

## Proposed doc changes (minimal file list)

### User docs (`docs/`)
- **Update** `docs/Unity_README.md`
  - Add: **Smoke Runbook (M0 Scaffold)**
  - Content: run + validate steps, build validation (desktop + WebGL), what “pass” looks like, common failures.

### Developer docs (`docs/dev/`)
- **New** `docs/dev/implementation_notes.md`
  - Add section: **Smoke (M0 Scaffold) — run/test/validate contract**
  - Content: definition of Smoke behavior, validation checklist, expected automated test coverage notes, troubleshooting, observability touchpoints.

### Temp draft (`docs/dev/tmp/`)
- **New** `docs/dev/tmp/doc_ge-hch.1.2.4_20260104220744.md` (this file)

## Draft content blocks (ready to paste)

### 1) `docs/Unity_README.md` — add section

> Placement suggestion: after “M0 Scene Path” and before “Unity Binary Handling & LFS Guidance”.

```md
## Smoke Runbook (M0 Scaffold)

This runbook defines the minimum “Smoke” validation for the M0 scaffold. Use it to:
- verify a local editor run behaves as expected
- produce a basic Desktop and WebGL build
- confirm the build loads and runs without fatal runtime errors

### Preconditions

- Unity **6.2** installed.
- Project opens without requiring a forced upgrade (if upgrades are required, do them on a branch).
- The M0 scene exists at: `Assets/Scenes/M0_Scaffold.unity`.

### Run in Editor (happy path)

1. Open the project in Unity.
2. Open the M0 scene: `Assets/Scenes/M0_Scaffold.unity`.
3. Press **Play**.

#### Expected results (definition of “Smoke”)

At minimum, the scene should behave like a tiny VN-style reader scaffold:
- render *something user-visible* immediately on play (typically a text panel or placeholder UI)
- explain in UI copy what would normally be present once real story content exists (e.g., “Story text will appear here”)
- accept at least one input method to advance the state:
  - mouse click / touch tap
  - keyboard (e.g., Space/Enter)
- advance to a visibly different state on input (e.g., new page text, page counter change, or a visible "advanced" indicator)
- run for at least ~30 seconds without throwing fatal errors or spamming exceptions

> NOTE: The exact UI and interactions are refined by `ge-hch.1.2.2` (Implement: Smoke). This runbook is the testable contract. Update it if the implementation chooses a different interaction model.

### Desktop build validation

1. In Unity: **File > Build Settings…**
2. Select your desktop platform (Windows/Mac/Linux) and choose **Switch Platform** if needed.
3. Confirm the **Scenes In Build** list includes `Assets/Scenes/M0_Scaffold.unity`.
4. Click **Build And Run**.

#### Pass criteria

- App launches and loads the M0 scene.
- The same “Expected results” above are observed.
- No fatal errors (crash, hard hang, empty window forever).

### WebGL build validation

1. In Unity: **File > Build Settings…**
2. Select **WebGL** and choose **Switch Platform**.
3. Confirm `Assets/Scenes/M0_Scaffold.unity` is in **Scenes In Build**.
4. Click **Build And Run**.

#### Pass criteria

- The browser loads the WebGL build.
- The scene renders.
- Input works (mouse + touch if on a touch device).
- No fatal runtime errors.

### How to report a Smoke failure

When reporting a failure in `bd` issues, include:
- Unity version string (from Unity Hub)
- platform (Editor/Desktop/WebGL)
- what step failed
- error text (Console for editor; browser console for WebGL)
```

### 2) `docs/dev/implementation_notes.md` — new doc

```md
# Implementation Notes (Developer)

This document collects implementation-oriented notes, runbooks, and validation checklists for features as they evolve.

## Smoke (M0 Scaffold) — run/test/validate contract (ge-hch.1.2)

This section defines what “Smoke” means for M0 validation. It is intended to keep implementation, tests, and docs aligned.

### Definition

A build is considered **Smoke-passing** if:

1. **Editor run:** `Assets/Scenes/M0_Scaffold.unity` runs in Play Mode and:
   - displays a visible UI state immediately
   - accepts at least one input method (mouse/touch/keyboard) that advances the UI state
   - does not crash/hard hang
   - does not emit unbounded exception spam

2. **Desktop build:** A desktop build (any Unity-supported desktop OS) can load and run the same scene with the same baseline interactions.

3. **WebGL build:** A WebGL build loads in a browser and supports at least mouse input, ideally both mouse and touch.

### Manual validation checklist

For PR review (or local development), record results in `bd` comments:
- Unity 6.2 used
- Scene path exists: `Assets/Scenes/M0_Scaffold.unity`
- Editor Play Mode: UI visible; can advance; no fatal errors
- Desktop build: loads and runs; can advance; no fatal errors
- WebGL build: loads and runs; can advance; no fatal errors

### Automated test expectations (ties to `ge-hch.1.2.3`)

At least one PlayMode test should exist that:
- loads the M0 scene
- asserts that expected UI root objects exist (or other minimal stable indicators)
- simulates an input event (or directly triggers the state advance) and asserts the visible state changes

### Observability / logging

Telemetry is **deferred** to `ge-hch.1.3`.

For Smoke validation until then:
- Editor: use the Unity Console for errors/exceptions.
- WebGL: use the browser DevTools console for errors/exceptions.
- Desktop build: use the target OS's standard output / player log (exact path varies by OS and Unity version).

Once telemetry is implemented, update this section with:
- where telemetry files/streams are emitted in Editor/Desktop/WebGL
- the expected schema/format
- what constitutes a telemetry error vs. acceptable early placeholders

### Troubleshooting

Symptom → likely cause → fix:

- **Scene missing (`Assets/Scenes/M0_Scaffold.unity` not found)** → scene not created yet or not available from artifact store → create the scene at that path or fetch it from the agreed artifact mechanism.
- **Project fails to open / endless reimport** → Unity version mismatch or corrupted Library cache → confirm Unity 6.2; delete `Library/` (local-only) and reopen; avoid upgrading editor version on `main`.
- **Build runs but shows blank/empty screen** → scene not included in build or camera/UI not wired → confirm `Assets/Scenes/M0_Scaffold.unity` is in **Scenes In Build**; check Console for missing references.
- **WebGL build fails** → platform not switched, unsupported setting/package, or shader/graphics incompatibility → switch to WebGL before building; re-resolve packages; check Editor console and browser console.

```

## Open Questions

1) What is the **exact intended Smoke interaction loop** (text pages? choices? placeholder UI)?
2) Which **desktop OS targets** are in-scope for Smoke validation (Windows/macOS/Linux, or simply “any desktop supported by Unity”)?
3) Is there already a decided **telemetry/logging sink** path/format for Smoke validation, or is it deferred to `ge-hch.1.3`?

## Changelog

- 2026-01-04: Initial draft created in `docs/dev/tmp/`.
