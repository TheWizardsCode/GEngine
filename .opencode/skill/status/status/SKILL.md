---
name: status
description: "Provide concise project / bead status and run Beads/waif helpers to augment results. Trigger on user queries such as: 'What is the current status?', 'Status of the project?', 'What is the status of <bead-id>?', 'audit', 'audit <bead-id>'"
---

# Status

## Overview

Provide a concise, human-friendly summary of project status or a specific bead. When no bead id is provided, run `waif in-progress --json` and summarize current work in progress. When a bead id is provided, run `bs show <bead-id> --json` and provide a detailed explanation of that bead (title, status, assignee, description, blockers, and related links).

## When To Use

- User asks general project status (e.g., "What is the current status?", "Status of the project?", "audit the project", "audit").
- User asks about a specific bead id (e.g., "What is the status of bd-123?", "audit bd-123").

## Behavior

1. Detect whether the user provided a bead id in the request.
2. If no bead id is provided:
   - Run `waif in-progress --json` (or use `scripts/run_status.py waif`) to fetch in-progress work.
   - Parse the returned JSON and produce a short summary including:
     - Number of in-progress beads
     - Highest-priority items and their assignees
     - Any items in a blocked state or missing assignees
     - A one-line suggestion for next action (e.g., "Review bd-123 assigned to @alice")
3. If a bead id is provided:
   - Run `bd show <bead-id> --json` (or use `scripts/run_status.py bd <bead-id>`) to fetch bead details.
   - Parse and present: title, status, assignee, priority, description, blockers, dependencies, comments count, and relevant links.
4. Handle errors gracefully: if `waif` or `bs` are not available or return invalid JSON, present a helpful error and possible remediation steps.

## Scripts

- `scripts/run_status.py` - helper script to run `waif` and `bs` commands and return JSON. Use this script to avoid re-implementing command execution logic.

## Examples

- "Status of the project?" → run `waif in-progress --json`, then summarize results and list 3 top in-progress beads.
- "What is the status of bd-42?" → run `bs show bd-42 --json`, then return full bead details.

## Notes

- Prefer using the helper script in `scripts/` to ensure consistent command invocation and JSON parsing.
- Keep the output concise and actionable for quick human consumption.
