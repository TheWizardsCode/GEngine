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

## GitHub Pages demo
When a commit lands on `main`, GitHub Pages publishes the static demo from `web/demo` at:

- https://thewizardscode.github.io/GEngine/demo/

Notes:
- Assets (stories) are fetched relative to the repo path, so the demo works from both local `http://127.0.0.1:8080/demo/` and Pages.

## Tests (web demo)
Playwright tests run against the hosted demo.

```
npm test
```

If Playwright browsers are not installed yet:
```
npx playwright install
```

## Key docs
- `docs/InkJS_README.md`
- `docs/prd/GDD_M1_dynamic_interactive_story_engine.md`
- `docs/prd/GDD_M2_ai_assisted_branching.md` — AI Writer design
- `docs/dev/Workflow.md`

## AI Writer (Milestone 2)

The demo includes an experimental AI Writer that generates additional story choices at each decision point using OpenAI's API.

### How to use

1. Click **AI Settings** in the demo header
2. Enter your OpenAI API key (stored locally in browser)
3. Enable AI-generated choices
4. Play the story — AI choices appear with a distinctive style at each decision point

### Features
- **LORE Context Assembly**: Extracts player state and narrative context from the Ink runtime
- **Two Prompt Templates**: Dialogue and exploration templates for different narrative contexts
- **Naive Branch Injection**: AI choices appear at every choice point (Director filtering coming in M3)
- **Safety Validation**: Basic profanity filter and schema validation
- **Configurable**: Toggle AI, adjust creativity, change choice styling

### Configuration
- **Creativity**: 0.0 (deterministic) to 1.0 (creative) — maps to temperature 0.0-2.0
- **Choice Style**: Distinct (highlighted with AI badge) or Normal (blends in)
- **Loading Indicator**: Show/hide while AI generates

### Modules
| Module | Path | Description |
|--------|------|-------------|
| LORE Assembler | `web/demo/js/lore-assembler.js` | Extracts context from Ink runtime |
| Prompt Engine | `web/demo/js/prompt-engine.js` | Builds prompts for the LLM |
| LLM Adapter | `web/demo/js/llm-adapter.js` | OpenAI API integration |
| API Key Manager | `web/demo/js/api-key-manager.js` | Key storage and settings UI |
| Proposal Validator | `web/demo/js/proposal-validator.js` | Schema and safety validation |

