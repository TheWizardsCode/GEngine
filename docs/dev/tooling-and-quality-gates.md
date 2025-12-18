# Tooling and Quality Gates for AI-Driven Development

## Introduction
This document defines the minimal tooling expectations and quality gates for AI + human collaborators working in this repository. It focuses on keeping AI-generated changes safe, reviewable, and reproducible, without assuming any particular language or engine yet.

## Prerequisites
Before applying these gates, ensure that the basic project and tooling setup is in place.

- Git is installed and configured for this repository.
- [`bd` (Beads)](https://github.com/SorraTheOrc/beads) is initialized and used for all issue tracking.
- [`perles`](https://github.com/SorraTheOrc/perles) is configured for Kanban-style views of bd issues.
- The Git-based workflow is understood: see `docs/dev/workflow.md`.

At this stage, we do not assume a specific test or build toolchain; instead, we standardize how such commands are configured and invoked via environment variables.

## Setting up the environment
Define the following environment variables before running commands in this document. Defaults are provided and may be adjusted to your context.

```bash
# Time-derived hash for uniqueness
HASH=$(date +%y%m%d%H%M)

# Repository and branch configuration
REPO_URL="git@github.com:example/gengine.git"
REMOTE_NAME="origin"
BASE_BRANCH="master"

# Actor and quality commands
BD_ACTOR="copilot"
TEST_CMD="echo 'TODO: define test command'"
LINT_CMD="echo 'TODO: define lint command'"
FORMAT_CMD="echo 'TODO: define format command'"
BUILD_CMD="echo 'TODO: define build command'"

# bd sync behavior
BD_SYNC_FLUSH_ARGS="sync --flush-only"
```

- `HASH`: Time-based hash in YYMMDDHHMM format used when unique values are needed.
- `REPO_URL`: Git remote URL for this repository.
- `REMOTE_NAME`: Git remote name used for pushing/pulling (defaults to `origin`).
- `BASE_BRANCH`: Base branch for feature branches.
- `BD_ACTOR`: Actor name for bd audit trails (defaults to `$BD_ACTOR` or `$USER` if unset).
- `TEST_CMD`: Command that runs the project test suite.
- `LINT_CMD`: Command that runs lint checks.
- `FORMAT_CMD`: Command that runs formatting checks or auto-formatting.
- `BUILD_CMD`: Command that runs any necessary build step.
- `BD_SYNC_FLUSH_ARGS`: Arguments passed to `bd` when flushing the database to JSONL without git operations.

## Steps
This section defines the concrete steps and expectations for local quality gates, bd integration, and reviews.

### 1. Local quality gates before commit
Before committing changes (especially AI-generated ones), run the local quality gates.

```bash
# From the repo root
$FORMAT_CMD   # Formatting (no-op until configured)
$LINT_CMD     # Linting (no-op until configured)
$TEST_CMD     # Tests (no-op until configured)
$BUILD_CMD    # Build (optional until needed)
```

These commands may initially be placeholders. As the codebase evolves, replace them with real commands (e.g., `pytest`, `npm test`, `go test ./...`). The expectation is that they pass locally before you push or open a PR.

### 2. Keep bd and JSONL in sync
Issue metadata must remain in sync with `.beads/issues.jsonl` so that agent and human activity is auditable.

```bash
# Flush bd changes to JSONL without git pull/push
bd $BD_SYNC_FLUSH_ARGS
```

- Use `bd sync --flush-only` before commits (or rely on the pre-commit hook installed via `bd hooks install`).
- Use full `bd sync` (without `--flush-only`) at session boundaries when a remote is configured and you want to synchronize across machines.

### 3. Branching conventions and PR requirements
Branching and PR expectations are defined in `docs/dev/workflow.md`; this section summarizes the gates.

- Branches are created from `$BASE_BRANCH` and should be named descriptively with a suffix using `$HASH` when uniqueness is needed.
- Each branch must be associated with exactly one primary bd issue.
- For each PR:
  - Reference the bd issue ID in the title or description.
  - Add a bd comment with the PR URL.
  - Summarize changes, risks, and how to run the quality gates locally.

This keeps bd, Git history, and PR discussions aligned.

### 4. Review rules (Producer vs agents)
Review rules determine when human Producer review is mandatory vs when agent-only review is acceptable.

- Changes that affect gameplay, player experience, monetization, or content shipped to players **must** be reviewed and approved by the `Producer`.
- Changes limited to internal tooling, docs, or experiments may be reviewed by agents alone, but the Producer remains accountable for accepting risk.
- For every PR, the reviewer (human or agent) should confirm:
  - Local quality gates were run and passed.
  - bd issue state and comments (branch, PR URL, final summary) are up to date.

These rules complement the RACI assignments in `docs/dev/team.md`.

### 5. Where templates and prompts live
To keep prompts and templates discoverable and versioned:

- Long-lived templates (e.g., the GDD template) live under `docs/dev/`.
- Ephemeral or exploratory prompt/design docs live under `history/`.
- bd issues should link to the relevant template or history files when they drive significant work.

This separation keeps the repository root clean while preserving a full audit trail of how AI prompts and processes evolved.

## Summary
This document defines how local quality gates, bd synchronization, branching, reviews, and documentation locations work together to keep AI-driven development safe and auditable. It is intentionally toolchain-agnostic, using environment variables to describe where test, lint, format, and build commands plug in.

## Next Steps
- Replace the placeholder `TEST_CMD`, `LINT_CMD`, `FORMAT_CMD`, and `BUILD_CMD` with real commands as the codebase grows.
- Introduce a CI pipeline that enforces these gates on every PR.
- Extend `docs/dev/workflow.md` and `docs/dev/team.md` as new tools and checks are added, keeping this document as the single source of truth for quality gates.