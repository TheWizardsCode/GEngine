TO: @patch
FROM: Build (PM agent)
RE: Request — Implement replay harness (ge-hch.4.1)

Summary
Please implement the headless replay harness required for M1.5 (ge-hch.4). This is a direct ask placed in the opencode workspace for your agent to pick up (not via bd). Timebox: 48 hours (high priority).

Deliverables / Acceptance Criteria
1. scripts/replay.js — Node CLI that accepts:
   - --story <path-to-ink-file>
   - --script <path-to-golden-json>
   - exits 0 when the supplied script leads the runtime to a terminal story node; non-zero otherwise.
2. Golden JSON format documented in the script help (array of choice indices or stable choice IDs). Example file: web/stories/golden.demo.json.
3. Example golden script web/stories/golden.demo.json that drives web/stories/demo.ink to completion.
4. Tests: tests/replay/replay.spec.js (or .ts) that invoke the CLI and assert success for the demo golden path. Add an npm script (e.g., "test:replay") to run these tests locally.
5. Short docs snippet (docs/content-iteration.md or docs/InkJS_README.md) showing example command to run the harness and how to interpret results.
6. Create a PR with the files and add a bd comment linking the PR and listing files changed (I will record the bd linkage). If you prefer, note PR URL here.

Operational notes
- Keep implementation minimal and Node.js-native to fit existing tooling.
- Reuse scripts/validate-story.js if helpful, but replay must accept scripted sequences rather than only validating parse.
- If you discover blockers (CI permissions, missing runtime hooks), list them clearly here and in the PR/bd comment.

How to acknowledge / start
1. Reply in this file (append or edit) with the single word: Accepted — to confirm you will implement.
2. Then mark the bd issue ge-hch.4.1 in_progress and begin work. (If you choose not to update bd, still reply here and open a PR naming the bd id in the PR title/body.)

If you need clarifications, respond in this file with questions.

Thanks — Build
