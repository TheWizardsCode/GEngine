# GEngine

GEngine is an InkJS-based interactive story demo (static HTML/JS) with Playwright smoke tests.

## Repository layout (high-level)
- `docs/` — project docs, workflow notes, PRDs
- `web/` — InkJS demo (`/demo`) and stories (`/stories`)
- `tests/` — Playwright smoke tests

## Prerequisites

### Node.js
- Node.js + npm

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
- `docs/InkJS_README.md`
- `docs/prd/GDD_M1_dynamic_interactive_story_engine.md`
- `docs/dev/Workflow.md`
