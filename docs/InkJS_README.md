# InkJS Demo and Smoke Trigger

This document explains how to run the InkJS-based smoke demo and where to find its assets.

## Layout
- `web/demo/index.html` — lightweight static page that runs the InkJS story and UI.
- `web/demo/js/inkrunner.js` — small runner that loads the story, renders choices, handles telemetry, and save/load.
- `web/demo/js/smoke.js` — dependency-free smoke visual (canvas-based).
- `web/stories/demo.ink` — the demo Ink story with the `#smoke` tag.
- `web/stories/demo.ink.json` — precompiled story JSON (generated via inkjs CLI) copied to `web/demo/story.json` for HTTP/local use.
- `web/demo/assets/` — optional placeholder assets (currently empty).
- `web/demo/vendor/ink.js` — vendored InkJS compiler build (ink-full). Replace this file to update version.

## Running the demo
1. Serve over HTTP to avoid CORS for story loading (recommended):
   ```bash
   npx http-server web/demo
   # or any static server rooted at web/demo
   ```
   Then open the served URL. The runner will load `story.json` (precompiled).
2. If opened via `file://`, fetch will fail; the runner falls back to the embedded compiled JSON. Telemetry still works, but running over HTTP is preferred.
3. InkJS is vendored locally at `web/demo/vendor/ink.js` (offline-safe). If you prefer CDN, swap the script tag in `web/demo/index.html` to `https://unpkg.com/inkjs/dist/ink-full.js` (or desired version).
4. On page load you should see the story text and available choices. Console logs will show `story_start` once the story begins.

## Interacting
- Click or tap choices to advance. A `choice_selected` telemetry log is emitted for every choice.
- When the story line with tag `#smoke` is presented, the runner emits `smoke_triggered` and starts the smoke effect using the current control values.
- Control panel: adjust smoke duration (seconds) and intensity (1–10). Save and Load buttons persist and restore story plus smoke state.
- Save/load uses `localStorage` key `ge-hch.smoke.save`. Saved data includes Ink story state JSON, smoke state, and control settings.

## Telemetry hook locations
- `story_start` — emitted when the InkJS story is initialized (see `loadStory()` in `inkrunner.js`).
- `choice_selected` — emitted when a choice button is clicked before advancing the story.
- `story_complete` — emitted when the story has no further content or choices.
- `smoke_triggered` — emitted when current tags include `smoke` and the smoke effect is started.

Example calls (console-based):
```js
console.log('story_start');
console.log('choice_selected');
console.log('story_complete');
console.log('smoke_triggered');
```

## Manual validation checklist
- Open `web/demo/index.html` in browser with devtools console.
- Observe `story_start` log on load and initial text displayed.
- When the `#smoke` tagged line appears, observe `smoke_triggered` and visible smoke that fades out over ~3s.
- Click choices; ensure `choice_selected` logs and text updates. When no choices remain, `story_complete` should log.
- Click Save, refresh or click Load; state should restore, including position and smoke config. If the previous smoke was running, it restarts.

## Notes
- Keep assets lightweight; avoid large binaries. Placeholder visuals are acceptable for this demo.
- If replacing CDN with a vendored copy, prefer a minified build and update documentation accordingly.
