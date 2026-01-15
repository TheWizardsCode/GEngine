---
name: implement-skill
description: Skill to implement an existing Beads issue by id. Invoked with the command `implement <bead-id>` and updates the specified bead rather than creating a new bead.
---

# Implement Skill

To run this skill, invoke the agent with a command like:

- `implement ge-hch.3`

Behavior:

- Parse the first argument as a single Beads id (e.g., `ge-hch.3`). If no id is provided or more than one argument is present, return a clear error asking the user to re-run with a single bead id.
- Fetch the bead JSON with `bd show <id> --json` and evaluate whether the bead is actionable per the project implement workflow.
- If the bead is actionable, claim it and update it using `bd update <id> --status in_progress --assignee "$USER" --json` (or the minimal accepted form in this environment). Do NOT create a new bead.
- If the bead is not actionable (missing acceptance criteria or scope), respond with a clear message describing which fields are missing and stop. Do NOT create a new bead in this case.

Notes for integrators:

- This SKILL.md provides the procedural instructions the agent needs to perform implement actions programmatically. The runtime that loads skills should ensure this skill is selected when user input begins with `implement` and the first token after the command looks like a beads id.


Examples of error responses (agent should use verbatim-style messages):

- "Error: missing bead id. Run `implement <bead-id>`."
- "Error: bead ge-hch.3 is not actionable — missing acceptance criteria. Run the intake interview to update the bead before implementing."

