### [docs/InkJS_README.md](./docs/InkJS_README.md)

```
# InkJS Demo and Smoke Trigger
This document explains how to run the InkJS-based smoke demo and where to find its assets.
## Layout
- `web/demo/index.html` — lightweight static page that runs the InkJS story and UI.
- `web/demo/js/inkrunner.js` — small runner that loads the story, renders choices, handles telemetry, and save/load.
- `web/demo/js/smoke.js` — dependency-free smoke visual (canvas-based).
- `web/stories/demo.ink` — the demo Ink story with the `#smoke` tag.
- `web/demo/assets/` — optional placeholder assets (currently empty).
- `web/demo/vendor/ink.js` — vendored InkJS compiler build (ink-full). Replace this file to update version. **Serve from repo root or web/ so this file and /stories/demo.ink are exposed.**
## Running the demo
```

### [docs/prd/GDD_M1_dynamic_interactive_story_engine.md](./docs/prd/GDD_M1_dynamic_interactive_story_engine.md)

```
# Product Requirements Document
## Introduction
- One-liner
  - Build an InkJS runtime narrative engine for story-first games, starting with a text-only Ink-powered MVP that runs in browsers (desktop and mobile) and Node.
- Problem statement
  - We need a repeatable way to ship immersive interactive stories with a runtime-ready vertical slice (story runtime + player UX + save/load + runtime telemetry) that supports fast iteration.
- Goals
  - MVP (M1) delivers a complete playable text-only story with branching choices.
  - Provide VN-style player UX for reading + choice selection.
  - Support single-slot autosave + manual save/load (best-effort portability in M1; portable in later milestones).
```

## How to query live state

- Beads issues: bd ready --json
- Current in-progress: bd list --status=in_progress --json