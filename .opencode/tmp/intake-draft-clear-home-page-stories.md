# Clear Home Page: Stories List

Problem
- Players landing on the demo don’t have a single, discoverable page that lists available stories and lets them quickly start playing.

Users
- New and returning players who want to pick a story and begin quickly
- Developers and playtesters who need to launch the demo with different story files

Success criteria
- A responsive stories index page is available under `/demo/` that lists available stories with a `Play` button for each
- Clicking `Play` opens the existing demo runner at `/demo/` with a query parameter specifying the story (e.g. `/demo/?story=/stories/foo.ink`). The runner must continue to work unchanged and read the `story` query parameter to load that story.
- Story entries show Title and a clear "AI (experimental)" badge when applicable (generated stories); the badge is shown only when `generated: true` is present in the manifest.
- Page includes ARIA labels for accessibility and is mobile responsive; follow demo UI styles and use semantic markup (ul/li, buttons)
- A simple manifest file `web/stories/manifest.json` drives the list; manifest can mark stories as `generated: true` and include optional `tags`/`description`
- Playwright smoke test verifies list load, play button operation, ARIA attributes, and that the runner loads the provided story path

Constraints
- Do not change the canonical `web/stories/demo.ink` runtime path; the runner expects stories under `/stories/`
- The demo runner UI should remain unchanged; the stories list only navigates to it with the `story` query parameter
- Respect story size and validation guidance from `docs/InkJS_README.md` for which stories to list
- Generated stories must be clearly labeled; do not auto-promote experimental stories without explicit `generated: true` flag in manifest

Existing state
- Demo runner exists at `web/demo/index.html` and accepts story path from its internal `STORY_PATH` mechanism (current code expects `/stories/demo.ink` by default)
- Story assets live under `web/stories/` (notes mention `web/stories/generated/` in repo history)
- Related/config work exists: `ge-hch.4.2` (Feature: story-swap CLI & manifest) which intends a manifest/CLI for swapping stories

Desired change
- Add a new stories index page at `web/demo/stories.html` (or `web/demo/index-stories.html`) served under `/demo/` that reads `web/stories/manifest.json` and renders the list
- Provide a small client-side script to fetch/parse the manifest and render entries (Title + Play). Play button navigates to `/demo/?story=<path>`.
- Include a small manifest schema (example below). Manifest must support `title`, `path`, `description?`, `tags?`, `generated?: boolean`.

Manifest example (informal)
{
  "stories": [
    { "title": "Demo", "path": "/stories/demo.ink", "generated": false },
    { "title": "Generated Test", "path": "/stories/generated/test.ink", "generated": true }
  ]
}

Formal JSON Schema (added at `web/stories/manifest.schema.json`):
- Fields: `title` (string), `path` (string, must start with `/stories/` and end with `.ink`), `description` (optional string), `tags` (optional string[]), `generated` (optional boolean, default false).
- The schema enforces the top-level `stories` array and disallows additional properties.

Likely duplicates / related docs
- web/demo/index.html — existing demo runner (player)
- web/stories/demo.ink — canonical demo story
- docs/InkJS_README.md — serving & story conventions
- docs/prd/GDD_M2_ai_assisted_branching.md — AI story guidance and labeling
- docs/dev/m2-design/demo-return-targets.md — return path considerations
- history/plan_ge-hch.3_agent_story_gen.md — notes referencing `web/stories/generated/`

Related issues (Beads ids)
- ge-hch.4.2 (Feature: story-swap CLI & manifest) — related work; manifest/CLI overlap
- ge-hch.5.19 (Validation Test Corpus & Tuning) — new/large test stories
- ge-hch.5.20 (Feature-Flagged Release) — release context

Recommended next step
- NEW PRD at: `docs/prd/stories_home_PRD.md`

Suggested next step (implementation)
- Create `web/stories/manifest.json` and validate against `web/stories/manifest.schema.json`
- Add `web/demo/stories.html` + `web/demo/js/stories-index.js` to render the manifest-driven list
- Add a small Playwright smoke test `tests/playwright/stories-list.spec.ts`

Areas that may need follow-up (placeholders)
- Naming/location: confirm new page filename and whether to add a header link from existing `index.html`
- Manifest ownership: decide CI or manual maintenance of `web/stories/manifest.json` (assume manual for initial implementation)
- Styling: draft a small style guide to match the demo theme

Risks & assumptions
- Risk: If manifest is maintained manually it can become stale; consider a CI validation step that fails on invalid manifest format (lint/CI check).
- Risk: Generated stories may contain invalid Ink or large stories that break the runner; assume maintainers will validate generated stories with `node scripts/validate-story.js` before adding to manifest.
- Assumption: The demo runner will accept the `story` query parameter at runtime or can be minimally updated to read it without changing behavior for existing uses.
- Assumption: Playwright tests can reuse existing smoke scripts to reduce test maintenance.

Files likely to be created/edited
- `web/demo/stories.html` (new index page)
- `web/demo/js/stories-index.js` (client script to render list)
- `web/stories/manifest.json` (manifest driving list)
- `tests/playwright/stories-list.spec.ts` (smoke test)
- Small CSS additions or responsive tweaks in `web/demo/index.html` or new CSS file

Acceptance tests / Definition of Done
- Manual: Visit `http://.../demo/stories.html` on desktop and mobile → page lists stories, `Play` opens the demo with selected story and the runner loads that story to completion of a smoke path
- Automated: Playwright test confirms list present, `Play` navigates to `/demo/?story=...` and the runner loads the specified story (use existing smoke script where applicable)
- Accessibility: key interactive elements have ARIA attributes and pass basic a11y checks (role, labels). Add minimal axe-core check in the Playwright test if feasible.
- Manifest validation: `web/stories/manifest.json` validates against `web/stories/manifest.schema.json` in CI or via a small validation script


Saved-artifact
- This draft saved to: `.opencode/tmp/intake-draft-clear-home-page-stories.md`


---

Final headline (1–2 sentences)
- Add a responsive stories index page at `/demo/` that lists available stories from `web/stories/manifest.json` and lets players open the demo runner with a selected story. Generated (AI) stories are clearly labeled as experimental; the manifest is schema-validated and the page is ARIA-accessible and mobile-responsive.

Please review and approve this final draft so I can create the Beads issue. If you'd like edits, list them now (filenames, manifest schema, tests, or PRD path).