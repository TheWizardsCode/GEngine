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
