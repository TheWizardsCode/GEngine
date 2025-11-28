---
mode: agent
model: GPT-5
tools: ["codebase", "openSimpleBrowser", "fetch", "editFiles"]
description: "Create a new TODO item in TODO.md"
---

# TODO.md Slash Command Prompt

## Goal

Provide a safe, discoverable slash-command interface for managing the repository `TODO.md`. This prompt equips an automated agent to add, update, close, list, find, archive, reject, and otherwise manage TODO entries while following the repository conventions.

## Overview — supported commands

The agent should implement the following slash-style commands:

- /todo add
- /todo next
- /todo update
- /todo close
- /todo list
- /todo find
- /todo archive
- /todo reject
- /todo template

Each command must operate on `TODO.md` and follow the file's template, ID rules, classification matrix, and maintenance guidelines.

## Key repository conventions (must preserve)

- ID numbers are three digits, never reused, and the current `Next Available ID` is stored in the file preamble.
- TODO items use a third-level heading with the ID and a short title: `### [001] Short Actionable Title`.
- Each item must include Status, Created date, Description, optional Subtasks, Stakeholders, Notes, and (optionally) Acceptance Criteria.
- Items are grouped by priority quadrants: HI/U, HI/NU, LI/U, LI/NU. Place new items into the appropriate section.
- When moving items to complete or rejected, preserve original metadata and add them to Completed or Rejected archive sections.

## Command behaviors and input requirements

/todo add

- Required: --title, --stakeholders (comma-separated), --description (outcome-focused)
- Optional: --priority (HI/U|HI/NU|LI/U|LI/NU) default HI/NU, --subtasks (newline or semicolon-separated), --acceptance (newline-separated), --created (YYYY-MM-DD, default today), --commit (bool)
- Behavior: Read `Next Available ID`, insert new item under the correct priority section using the TODO Item Template, update `Next Available ID` to the next integer, add a changelog line. If `--commit` is provided, include a suggested commit message: `todo: add [ID] {short-title}`.
- Output: status summary and suggested commit message.

/todo next

- Behavior: Return the next 3 highest priority actionable item from each of the currently in progress TODO items. If there are no in progress items, suggest up to three items from the backlog based on priority order.
- Output: a markdown list of status summaries `- [ID] {short-title}]\n Task:{task summary}`.

/todo update

- Required: --id (e.g., 001) OR --identifier (exact heading text), and at least one field to update: --title, --description, --status, --subtasks, --stakeholders, --notes, --acceptance, --priority
- Behavior: Locate the item by ID or heading, apply updates in-place (preserve other fields), and if priority changed, move the item to the corresponding section. Do not change the ID. If status becomes `closed` or `rejected`, suggest using `/todo close` or `/todo reject` flows which perform archival.
- Output: status summary and commit message suggestion `todo: update [ID] {short-title}`.

/todo close

- Required: --id OR --identifier, optional --resolution-note
- Behavior: Mark item Status: closed, add a short resolution note to Notes, and move the full item (preserving metadata) to `## Completed Items Archive`. Do not renumber. Update Changelog with closure entry and date.
- Output: status summary and commit message `todo: close [ID] {short-title}`.

/todo reject

- Required: --id OR --identifier, required --reason
- Behavior: Mark item Status: rejected, add reason to Notes, move entry to `## Rejected Items Archive`, update Changelog with rejection line and date.
- Output: status summary and commit message `todo: reject [ID] {short-title}`.

/todo archive

- Required: --section (Completed|Rejected) OR --id list
- Behavior: Create archive sections if missing and move specified items there (used for bulk archival). Provide a short archive summary and changelog entries.

/todo list

- Optional: --priority (HI/U|HI/NU|LI/U|LI/NU), --status (open|In Progress|closed|rejected), --format (markdown|json|plain). Default: list open items across all priorities in markdown.
- Behavior: Return requested list (no file changes) and a short status indicating number of items in each category returned. Add the line number in TODO.md where the item can be found (in the form '(Lxxx)'). Do not include the full descriptions and notes.

/todo find

- Required: --query (string)
- Optional: --field (title|description|stakeholders|notes|all), case-insensitive substring matches
- Behavior: Return matching items with context. Support limiting results: --limit N.

/todo template

- Behavior: Return the canonical TODO Item Template (exact snippet from `TODO.md`) so callers can copy/paste. No file changes.

## Agent behavior rules and safety

- Always read the current `TODO.md` from disk before making edits. If the file changed since the last read, re-run parsing and validation.
- Preserve file structure, existing whitespace, and unrelated content. Do not reorder sections except when moving an item to another priority or archive as part of an explicit command.
- Never reuse IDs. When adding, use the `Next Available ID` and then increment it in the file preamble.
- When moving items to Completed or Rejected archives, keep the original heading and metadata and append a one-line archival note including date (YYYY-MM-DD).
- For any destructive operation (move/remove), produce a patch and run a read-after-write validation: re-open `TODO.md` and confirm the intended changes and that no unrelated lines were removed.
- If the `##` section expected is missing or the file is unparsable, do not perform edits; instead return a repair patch suggestion that creates missing sections and explain the proposed changes.
- For conflicts (e.g., duplicate title/ID), fail with a clear message and a suggested diff to reconcile; require `--overwrite` to proceed.

## Validation & Acceptance Criteria

- After an edit: the agent must reopen `TODO.md` and confirm the new entry or change exists, `Next Available ID` has been updated when appropriate, and no unrelated deletions occurred. Report PASS/FAIL.
- For add/update/close/reject/archive: include in the response: Operation, target ID(s), file path, suggested commit message, and validation result.

## Examples

- Add:
  /todo add --title "Improve AKS onboarding docs" --stakeholders "AKS PM, SRE" --description "Publish an onboarding playbook + 72-hour runbook in wiki" --priority HI/NU --subtasks "Draft;Review;Publish" --commit

- Update status:
  /todo update --id 001 --status "In Progress" --notes "Assigned to PM" --commit

- Close:
  /todo close --id 001 --resolution-note "Playbook published and signed-off by SRE" --commit

- List open HI/NU items in JSON:
  /todo list --priority HI/NU --format json

- Find by stakeholder:
  /todo find --query "SRE" --field stakeholders

## Safety and conflict handling

- If an operation would unintentionally overwrite another field or item, fail and return a suggested diff and clear instructions.
- Do not change the `## Changelog` historical lines except to append new changelog entries.

## Changelog / Maintenance

- When updating this prompt, keep compatibility with existing slash commands. Add flags only with clear backward-compatible defaults.

---

TODO Item Template (canonical):

### [ID] Short Actionable Title

**Status:** open | closed | rejected | In Progress
**Created:** YYYY-MM-DD

#### Description

(Clear problem / outcome statement)

Subtasks (optional):

- [ ] Step 1
- [ ] Step 2

#### Stakeholders

(individuals and teams contributing to or needing this task completed)

#### Notes

(Context, links, decisions, progress made)

#### Acceptance Criteria

- First thing that must be true for this task to be complete
- Second thing that must be true for this task to be complete

## Example changelog entry format (agent should append):

- 2025-08-27: [001] Short Actionable Title — added to TODO register (HI/NU).

---

Validation: After applying edits the agent must re-open `TODO.md` and confirm the presence of the expected changes and that `Next Available ID` was incremented when a new item was added.
