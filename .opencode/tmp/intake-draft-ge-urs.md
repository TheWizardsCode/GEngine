Title: Make all agents use deny-by-default permissions

Problem
-------
Agent definitions in .opencode/agent/*.md currently include permissive or wildcard bash permission entries (e.g. "*": allow) that grant agents broader runtime capabilities than necessary. This increases risk of accidental or malicious repository changes, leaking secrets, or executing destructive commands from downstream agents.

Users
-----
- Repository maintainers and Producers who rely on safe, auditable agent behavior
- Agent authors (Forge) who will update agent definitions
- Implementation agents (Patch, Probe) who may need to run commands during sessions

Success criteria (testable)
---------------------------
1. All agent definition files under .opencode/agent/ contain explicit, least-privilege permission rules. No agent grants a blanket "*": allow for bash. Any previously present "*": allow is either:
   - replaced with a minimal explicit allow-list of permitted bash patterns, or
   - replaced with "*": ask (or removed entirely) where interactive confirmation is required.
2. A repository-level policy document is added at .opencode/agent/PERMISSIONS.md describing the deny-by-default model, recommended minimal granted patterns, and the review process for changes.
3. Changes are made on a feature branch named feature/ge-urs-<short> and submitted as a PR. The PR references bd#ge-urs and contains a short summary of edits per-agent.
4. Automated check: run a script (or rg) to assert no .opencode/agent/*.md file contains the pattern '"*": allow' (failure if found). This check is run locally before creating the PR.

Constraints
-----------
- Do not change runtime/CI behavior beyond permissions metadata in .opencode/agent/*.md (no edits to CI, runtime code, or other repository policies without explicit Producer approval).
- Keep each agent's permissions minimal and documented in the agent file's rationale section.
- Avoid disruptive or large diffs; prefer per-agent small edits and PRs grouped logically.

Existing state
--------------
- Agent files are present in .opencode/agent/*.md. Some agents currently have permissive entries (e.g., Build had "*": allow; Forge had "*": ask).
- A bd issue exists: ge-urs (in_progress) assigned to forge.

Desired change (high-level)
--------------------------
- Adopt deny-by-default: remove blanket allow rules and replace with specific minimal patterns or explicit "ask" where necessary.
- Add a short PERMISSIONS.md to describe the convention and provide examples.
- Provide a small automated assertion script (scripts/check-agent-permissions.sh) that returns non-zero if a wildcard allow is present.

Likely duplicates / related docs
-------------------------------
- .opencode/agent/*.md (the files to change)
- AGENTS.md and .github/copilot-instructions.md (guidance and rules)
- bd issue: ge-urs

Related issues
--------------
- ge-urs (current task)

Recommended next step
---------------------
1. Confirm scope: approve this intake draft or request edits.
2. If approved, I will:
   - Create a feature branch feature/ge-urs-permissions and update agent files conservatively (one commit per agent file changed).
   - Add .opencode/agent/PERMISSIONS.md and scripts/check-agent-permissions.sh.
   - Run the local check and open a PR referencing bd#ge-urs.

Questions / open items
----------------------
- Confirm whether you want a single PR updating all agents, or multiple smaller PRs (per-agent). Recommended: a single PR limited to metadata-only changes for speed.
- Confirm whether replacing "*": allow with specific patterns should be done automatically (best-effort) or manually per agent with human review for each pattern.

