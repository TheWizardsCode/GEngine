---
name: implement-skill
description: Skill to implement an existing Beads issue by id. Reproduces the full behaviour of the legacy `/implement` command so the repository can safely remove the command and rely on this skill.
---

# Implement Skill

Purpose

- Implement an existing Beads issue by id and reproduce the legacy `/implement` command behaviour in a standalone skill. The skill validates readiness, claims the issue, creates a working branch, performs implementation with tests and self-reviews, opens a PR, and updates the Beads issue without creating new beads unless explicitly required.

Invocation

- Invoke the skill with a single beads id argument:
  - `implement ge-hch.3`

Argument parsing

- Parse the first argument as a single Beads id (for example `ge-hch.3`).
- If no id is present or more than one argument is provided, stop and return a clear error message asking the user to re-run with a single bead id.

Project rules (must follow)

- Use `bd` for ALL task tracking; do not create markdown TODOs.
- Keep changes between `git push` invocations minimal and scoped to the issue.
- Validate changes with the most relevant tests/commands available.
- Use a git branch + PR workflow (no direct-to-main changes).
- Ensure the working branch is pushed to `origin` before you finish.
- Do NOT close the Beads issue until the PR is merged.

Live context tokens (available when executing)

- Current issue JSON: run `bd show <id> --json` to obtain the issue payload.
- Git status: run `git status --porcelain=v1 -b` to inspect the working tree.
- Current branch: run `git rev-parse --abbrev-ref HEAD`.
- Origin remote: run `git remote get-url origin`.

Process (procedural steps)

0) Safety gate: handle dirty working tree

- Check whether the working tree is clean (`git status --porcelain=v1 -b`).
- If any uncommitted changes exist (modified, staged, or untracked files), pause and ask the user what to do. Offer explicit choices: carry changes into the issue branch, commit current changes first, stash changes (and whether to pop later), revert/discard changes (explicit confirmation required), or abort implementation to let the user inspect.

1) Understand the issue

- Read and restate the acceptance criteria and constraints from the issue JSON.
- Inspect dependencies and blockers on the issue and surface missing requirements.
- Review the issue `description`, `notes`, and `comments` for linked PRDs, plans, or docs; open and read those sources before proceeding.
- Confirm what tests or validation the issue expects.

1.1) Definition gate (must pass before implementation)

- Verify minimum definition checklist:
  - Clear scope: what is in-scope vs out-of-scope.
  - Concrete acceptance criteria (testable).
  - Constraints and compatibility expectations.
  - Unknowns captured as explicit questions.
- If the issue is not well-defined, stop and perform the intake brief interview to update the existing issue (do not create a new bead). Update the issue `description` and/or `acceptance` field with the intake output (for example: `bd update <id> --description "<intake brief markdown>" --json`).

2) Create a working branch

- If already on an appropriate topic branch, use it.
- Otherwise create a new branch named `feature/<id>-<short>` or `bug/<id>-<short>` (include the bead id).
- Do not commit directly to `main`.

3) Claim the issue

- Claim the issue with: `bd update <id> --status in_progress --assignee "$USER" --json` (omit `--assignee` if not accepted in environment).

4) Implement

- Identify the smallest set of files to change.
- Make incremental changes that satisfy acceptance criteria.
- If additional work is discovered, create linked issues: `bd create "<title>" --deps discovered-from:<id> --json`.

5) Validate

- Author and run appropriate tests.
- Run the most specific checks available for the changed area (lint/test/build).
- If tests fail, fix before proceeding.
- Pause for user confirmation after tests pass if requested by workflow.

6) Update the docs

- Update any linked PRDs or relevant README sections documenting usage or configuration changes.
- Add short notes in the PR describing how to test the change locally.

7) Automated self-review stages (sequential, may apply minimal edits)

- Run five self-review passes (completeness, dependencies & safety, scope & regression, tests & acceptance, polish & handoff). For each pass, produce a short note and apply only minimal, clearly-scoped edits that do not change intent. If a review uncovers a change that alters intent, create an Open Question and stop automatic edits.

8) Commit, push and create PR

- Commit with a message that includes the beads id and a clear summary of the change.
- Push the branch to `origin`.
- Create a Pull Request against the default branch. In the PR description include a summary of changes, a reference to the beads issue (e.g., `Closes bd#<id>`), and instructions for reviewers.

9) Update Beads (do not close)

- Add a label to indicate PR status (for example: `bd update <id> --add-label "Status: PR Created" --json`).
- Update the bead with the PR URL using `--external-ref` or `--notes`.
- Keep the bead's status as `in_progress` until the PR is merged.
- Run `bd sync` before ending the session.

Error responses (verbatim where possible)

- "Error: missing bead id. Run `implement <bead-id>`."
- "Error: bead <id> is not actionable — missing acceptance criteria. Run the intake interview to update the bead before implementing."

Notes

- This skill reproduces the full procedural behaviour of the previous `/implement` command but does so as a standalone skill invoked via `implement <bead-id>`. The implement command may be removed from the repository once this skill is deployed and adopted.

Files that may be created/edited

- Implementation code files relevant to the bead
- Tests for the implemented behaviour
- docs/ and README updates describing usage
- PR branch and commit history

Acceptance criteria (for the skill changes themselves)

- The SKILL.md provides sufficient procedural instructions for an agent to implement a bead end-to-end without relying on the legacy `/implement` command.
- Argument parsing, safety gate, intake rules, branch/claim/implement/validate/PR/update-beads workflow, and automated self-review stages are documented.

Examples of how to invoke the skill

- `implement ge-hch.3`

---

# Implement Skill

To run this skill, invoke the agent with a command like:

- `implement ge-hch.3`

Behavior:

- Parse the first argument as a single Beads id (e.g., `ge-hch.3`). If no id is provided or more than one argument is present, return a clear error asking the user to re-run with a single bead id.
- Fetch the bead JSON with `bd show <id> --json` and evaluate whether the bead is actionable per the project implement workflow.
- If the bead is actionable, claim it and update it using `bd update <id> --status in_progress --assignee "$USER" --json` (or the minimal accepted form in this environment). Do NOT create a new bead.
- If the bead is not actionable (missing acceptance criteria or scope), respond with a clear message describing which fields are missing and stop. Do NOT create a new bead in this case.


Examples of error responses (agent should use verbatim-style messages):

- "Error: missing bead id. Run `implement <bead-id>`."
- "Error: bead ge-hch.3 is not actionable — missing acceptance criteria. Run the intake interview to update the bead before implementing."

