# Git-Based Agent-Driven Development Workflow

## Introduction
This document outlines a concise Git-centered workflow for AI and human agents collaborating on development tasks, ensuring traceable changes and synchronized issue tracking.

## Prerequisites
- Git installed and configured with commit signing if required.
- Access to the repository remote and permissions to push branches and open pull requests.
- [Beads](https://github.com/SorraTheOrc/beads) (`bd`) installed and initialized for issue tracking in this repository.
- [Perles](https://github.com/SorraTheOrc/perles) (`perles`) installed and initialized for Kanban view of Beads.
- Familiarity with the tooling and quality gates described in `docs/dev/tooling-and-quality-gates.md`.

## Setting up the environment
Define the following environment variables before running commands. Defaults are provided and may be adjusted to your context.

```bash
# Time-derived hash for uniqueness
HASH=$(date +%y%m%d%H%M)

# Repository and work context
REPO_URL="git@github.com:example/gengine.git"
WORKTREE_ROOT="$HOME/workspaces/gengine_${HASH}"
REMOTE_NAME="origin"
BASE_BRANCH="master"
BRANCH_NAME="feature/agent-work_${HASH}"
BD_ACTOR="copilot"
ISSUE_ID="TBD"
```

- `HASH`: Time-based hash in YYMMDDHHMM used for unique names.
- `REPO_URL`: Git remote URL for cloning/fetching.
- `WORKTREE_ROOT`: Local path for the working copy.
- `REMOTE_NAME`: Git remote name to use for pushing/pulling (defaults to `origin`).
- `BASE_BRANCH`: Base branch to branch from.
- `BRANCH_NAME`: Feature branch name suffixed with `_${HASH}` for uniqueness.
- `BD_ACTOR`: Actor name for bd audit trails (defaults to `$BD_ACTOR` or `$USER`).
- `ISSUE_ID`: bd issue or epic ID the branch tracks.

## Steps
1. **Clone or fetch**: `git clone "$REPO_URL" "$WORKTREE_ROOT"` (or `git fetch` if already cloned).
2. **Select an issue**: Use `bd ready --json` to pick an unblocked item; export its ID to `$ISSUE_ID`.
3. **Verify remote**: Ensure the expected remote exists (required for pushing/PRs).
	```bash
	git remote -v
	# If missing, add it:
	git remote add "$REMOTE_NAME" "$REPO_URL"
	```
4. **Create branch**: From the base branch, run `git checkout -b "$BRANCH_NAME" "$BASE_BRANCH"`.

5. **Link work to bd**: Update the relevant bd issue (`$ISSUE_ID`) to `in_progress` and record the branch via a comment. If the work changes gameplay/design, create or update the GDD using the template in `docs/dev/gdd-template.md`, and link it from the issue. Example:
	```bash
	bd update "$ISSUE_ID" --status in_progress
	bd comment "$ISSUE_ID" --body "Working on branch $BRANCH_NAME"
	```

6. **Develop in small commits**: Make focused changes; before committing, ensure `.beads/issues.jsonl` is up to date.
	- Prefer `bd sync --flush-only` (exports DB → JSONL, no git operations) or rely on the pre-commit hook.
	- Use full `bd sync` for multi-device syncing when a remote is configured.
7. **Test and lint**: Run project quality gates locally before pushing (see `docs/dev/tooling-and-quality-gates.md` for commands and expectations).
8. **Push branch**: `git push -u "$REMOTE_NAME" "$BRANCH_NAME"` to set upstream for collaboration and CI.
9. **Open PR**: Create a pull request referencing `$ISSUE_ID`, summarizing changes, risks, test results and guidance for manual testing when appropriate. Capture the PR URL in `$PR_URL` and record it on the issue. Example:
	```bash
	PR_URL="https://github.com/example/gengine/pull/123"  # set from your PR
	bd comment "$ISSUE_ID" --body "PR opened: $PR_URL"
	```

10. **Review loop**: Address review feedback in follow-up commits; keep bd issue status updated through completion.
11. **Merge and clean up**: After approval and green checks, merge, then prune the local branch. Record a final comment summarizing the work with the PR link, and close the issue. Example:
	```bash
	bd comment "$ISSUE_ID" --body "Merged changes from $PR_URL; summary: <brief bullets on fixes/feature>"
	bd close "$ISSUE_ID" --reason "Done. Merged from $PR_URL"
	```

## Summary
This workflow keeps AI/human collaboration auditable: every branch ties to a bd issue, commits remain small and test-verified, and PRs capture decisions before merge.

## Next Steps
- Automate branch creation, bd updates, and PR templates via helper scripts.
- Add CI jobs to enforce `bd sync` and lint/test gates before merge.
- Extend this guide with project-specific commands and quality bars as they evolve.
