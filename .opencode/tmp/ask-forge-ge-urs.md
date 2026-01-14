To: @forge
Issue: ge-urs — Make all agents have wider default permissions (deny-by-default)
Branch: ge-urs/complete-agent-perms

Request:
Please implement the final updates required to complete ge-urs. Specifically:

Scope
- Inspect and update all files under .opencode/agent/*.md so each contains a deny-by-default permission section (see .opencode/agent/forge.md for the canonical template).
- Ensure no agent file contains a wildcard "*": allow for bash or equivalent permissive entries (e.g., blanket allows).

Deliverables
1. Updated .opencode/agent/*.md files with deny-by-default permissions applied (including patch.md).
2. Add or update .opencode/agent/PERMISSIONS.md describing the template and short rationale.
3. Add scripts/check-agent-permissions.sh which exits non-zero when a wildcard allow is present.
4. Open a PR from branch feature/ge-urs-complete-agent-perms (or another feature branch) with the changes, link it in a bd comment, and request review from @rgardler.

Constraints & Timebox
- Do not modify CI workflows or other code without explicit Producer approval.
- Timebox: 48 hours.

How to respond
- Please reply in this file (edit it) or create the PR and add a bd comment linking the PR. If you accept, add a short line: "Accepted — I'll take this" and set an ETA.

Actor: Build (requesting)
