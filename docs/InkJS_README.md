InkJS README — M0 web scaffold

Purpose
This README documents the InkJS-based M0 web scaffold: where the demo lives, how to run it locally, where to put Ink stories, save/load guidance, and minimal telemetry hook examples.

Repo layout (suggested)
- web/               ← web/demo app & build artifacts
  - demo/            ← demo static files (optional)
  - stories/         ← .ink story files (e.g., demo.ink)
  - package.json     ← web build scripts (if present)
- docs/              ← documentation (this file)
- history/unity-archive/ ← archived Unity artifacts and docs

Running the demo (developer)
- Dev server (recommended)
  - cd web
  - npm ci
  - npm start
  - Open http://localhost:3000 (or port indicated by runner)
- Static artifact (no server)
  - Open web/demo/index.html in a browser
  - Or serve with a static server: npx serve web/demo

Where to place Ink stories
- Place story source files in web/stories/ (e.g., web/stories/demo.ink).
- Build process should copy compiled JSON (if any) into the runtime assets directory as documented in web/README or build scripts.

InkJS usage
- Runtime: InkJS (Node / browser). We use a fork of InkJS (link or note).
- Typical integration: demo app loads compiled Ink JSON or .ink as supported by our fork and invokes the Ink runtime to drive UI.

Save / load (single-slot)
- Implement single-slot save using localStorage or downloadable save files:
  - Save: localStorage.setItem('m0_save', JSON.stringify(saveData))
  - Load: JSON.parse(localStorage.getItem('m0_save'))
- Document format expectations if a separate serializer is used.

Telemetry hooks (examples)
- The demo should expose clear hook points for telemetry. Example hook names:
  - story_start(event)
  - choice_selected(event)
  - story_complete(event)
- Example (console):
  - console.log({event: 'story_start', story: 'demo.ink', ts: Date.now()})

Artifact & binary policy
- Do not commit large Unity binaries into the mainline. For legacy Unity files, use history/unity-archive/ or an external artifact store.
- CI artifacts: CI should build and archive web/demo static artifacts for smoke validation.

Legacy Unity note
- If docs/Unity_README.md or Unity project files exist, they are legacy and have been archived at history/unity-archive/docs/Unity_README.md.

Contact / ownership
- Owner: <team/person>
- For runtime/test infra questions, contact @patch / @ship
