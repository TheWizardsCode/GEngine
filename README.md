# GEngine

GEngine is an interactive story engine project with:
- a Unity editor/runtime scaffold (VN-style reader UX)
- a lightweight InkJS web demo (static HTML/JS)
- Playwright smoke tests for the web demo

## Repository layout (high-level)
- `Assets/` — Unity project assets and scripts
- `docs/` — project docs, workflow notes, PRDs
- `web/` — InkJS demo (`/demo`) and stories (`/stories`)
- `tests/` — Playwright smoke tests

## Prerequisites

### Unity
- Unity **6.2** (see `docs/Unity_README.md`)

### Node.js (for web demo + tests)
- Node.js + npm

## Unity quickstart
1. Install Unity 6.2 (Unity Hub recommended).
2. In Unity Hub, **Add** the repository root (this folder).
3. Open the project using Unity 6.2.
4. Open the scaffold scene: `Assets/Scenes/M0_Scaffold.unity`.

More details: `docs/Unity_README.md`.

## InkJS web demo
The demo is a static site under `web/` that fetches `web/stories/demo.ink` at runtime.

### Run locally
```bash
npm install
npm run serve-demo
```

Then open:
- `http://127.0.0.1:8080/demo/`

Notes:
- Serve from repo root or `web/` so `/stories/demo.ink` is reachable.

More details: `docs/InkJS_README.md`.

## Tests (web demo)
Playwright tests run against the hosted demo.

```bash
npm test
```

If Playwright browsers are not installed yet:
```bash
npx playwright install
```

## Key docs
- `docs/Unity_README.md`
- `docs/InkJS_README.md`
- `docs/prd/GDD_M1_dynamic_interactive_story_engine.md`
- `docs/dev/Workflow.md`
