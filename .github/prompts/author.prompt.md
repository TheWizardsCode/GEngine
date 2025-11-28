# Executable Document Authoring Prompt

## Goal

Guide authors to create high-quality, repeatable executable documents that
follow the established structure and style used in `docs/Create_AKS.md` and
other infrastructure playbooks. Documents produced with this prompt should be
directly runnable, idempotent, and verifiable.

## Overview

Invoke this prompt to scaffold or refine an executable document. It enforces:

- Standard section layout (Introduction, Prerequisites, Setting up the
  environment, Steps, Verification (optional), Summary, Next Steps)
- Clear, concise paragraphs (wrap at <=80 chars)
- Consistent environment variable pattern (UPPER_SNAKE_CASE + defaults)
- Timestamp uniqueness using `HASH` (`YYMMDDHHMM`)
- Idempotent, defensive commands (check before create/update/delete)
- A Summary paragraph at end of every section
- Verification section to allow `/execute` fast re-run to skip full execution (see `execute.prompt.md` for details)
- Plain Bash fenced code blocks (`bash`) with only variable-driven values
- Short, self-contained code blocks with tightly related commands only
  (avoid long monolithic blocks).
- Every code block must be immediately followed by:
  - an HTML `expected_similarity` test comment, and
  - a fenced `text` sample output block. The similarity regex must match
    the sample output shown. The `expected_similarity` attribute value
    must be a regular expression (not the literal string `regex`).
- Similarity tests must validate successful execution paths (do not
  match failure-only outputs).

## Supported Commands

- `/author` – Provide interactive guidance and a blank template
- `/author New_Doc_Name.md` – Generate a starter file with the given name
- `/author docs/path/CustomDoc.md --title "Title" --desc "Short purpose"` –
  Scaffold with custom metadata
- `/author refine CurrentDoc.md` – Analyze an existing doc and output
  remediation suggestions (missing summaries, long lines, etc.)

## Authoring Checklist

Before finalizing, ensure:

1. Every section starts with a short explanatory paragraph.
2. A fenced `bash` block holds all commands; avoid inline shell besides code
   blocks.
3. All parameters are environment variables documented in the environment
   section.
4. Each command block is idempotent (checks existence before creating).
5. `HASH` is defined exactly: `export HASH="${HASH:-$(date -u +"%y%m%d%H%M")}"`.
6. No hard-coded sensitive values (subscription IDs, client IDs) outside vars.
7. Lines do not exceed ~80 chars (soft wrap allowed in paragraphs).
8. Each Step subsection ends with a one-line Summary starting with `Summary:`.
9. Verification section only reads/validates state; it must not mutate.
10. Code blocks are short and self-contained, containing only tightly
    related commands.
11. After every code block, include an `<!-- expected_similarity="regex" -->`
    test comment and a fenced `text` sample output block. Replace `regex`
    with an actual regular expression that matches the sample output and
    represents successful execution (e.g., `<!-- expected_similarity="^tools OK$" -->`).

## Environment Variable Conventions

- Always export variables with defaults using `${VAR:-default}` form.
- Use clear grouping comments (Scope, Resource naming, Sizing, etc.).
- Prefer determinism over randomness (timestamp uniqueness is sufficient).
- Example pattern:

```bash
export HASH="${HASH:-$(date -u +"%y%m%d%H%M")}"  # YYMMDDHHMM
export LOCATION="${LOCATION:-eastus2}"
export RESOURCE_GROUP="${RESOURCE_GROUP:-rg_example_${HASH}}"
export WORKSPACE_NAME="${WORKSPACE_NAME:-ws_${HASH}}"
```

## Section Structure Template

Below is the canonical template. Replace placeholders but keep ordering and
summary pattern.

````markdown
# <Document Title>

## Introduction

<Explain the overall purpose, what resources or outcomes are produced, and
why this is needed. Keep to 3–6 lines.>

Summary: <One sentence restating outcome.>

## Prerequisites

<List required tools, permissions, prior documents. Include quick checks.>

```bash
if command -v az >/dev/null && command -v kubectl >/dev/null; then
  echo "tools OK"
fi
```

<!-- expected_similarity="^tools OK$" -->

```text
tools OK
```

Summary: <Confirms readiness to proceed.>

## Setting up the environment

<Describe all environment variables, their role, and uniqueness strategy.>

```bash
export HASH="${HASH:-$(date -u +"%y%m%d%H%M")}"  # YYMMDDHHMM
# Scope
export LOCATION="${LOCATION:-eastus2}"
export RESOURCE_GROUP="${RESOURCE_GROUP:-rg_example_${HASH}}"
# Feature-specific
export FEATURE_FLAG="${FEATURE_FLAG:-false}"
echo "Environment variables exported"
```

<!-- expected_similarity="^Environment variables exported$" -->

```text
Environment variables exported
```

Summary: <Variables defined for repeatable execution.>

### Verify environment variable values

```bash
VARS=(HASH LOCATION RESOURCE_GROUP FEATURE_FLAG)
for v in "${VARS[@]}"; do printf "%s=%s\n" "$v" "${!v}"; done
```

<!-- expected_similarity="^HASH=\\d{10}\\nLOCATION=.*\\nRESOURCE_GROUP=.*\\nFEATURE_FLAG=(true|false)$" -->

```text
HASH=2511131958
LOCATION=eastus2
RESOURCE_GROUP=rg_example_2511131958
FEATURE_FLAG=false
```

Summary: <Printed active values for confirmation.>

## Steps

<Each subsection follows: short purpose paragraph, bash block, summary line.>

### <Action Title>

<Explain rationale and any idempotence logic.>

```bash
# Example idempotent create
if az group show --name "${RESOURCE_GROUP}" >/dev/null 2>&1; then
  echo "Resource group ${RESOURCE_GROUP} already exists"
else
  az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output table
fi
```

<!-- expected_similarity="^(Resource group .* already exists|.*provisioningState\\s*Succeeded.*)$" -->

```text
Resource group rg_example_2511131958 already exists
```

Summary: <Outcome sentence.>

### <Next Action>

<...>

```bash
# Commands
echo "Completed successfully"
```

<!-- expected_similarity="^Completed successfully$" -->

```text
Completed successfully
```

Summary: <Outcome sentence.>

## Verification

<Only validation commands. Should allow `/execute` to skip if already good.>

```bash
FAILED=0
# State check examples
az group show --name "${RESOURCE_GROUP}" --query "{name:name,location:location}" -o table || { echo "[ERROR] RG missing" >&2; FAILED=1; }
# Add further non-mutating queries
if [ "$FAILED" -ne 0 ]; then echo "[RESULT] Verification FAILED"; else echo "[RESULT] Verification PASSED"; fi
```

<!-- expected_similarity="^\\[RESULT\\] Verification PASSED$" -->

```text
[RESULT] Verification PASSED
```

Summary: <States successful validation criteria.>

## Summary

<Condense what was created/verified in bullet or short paragraph form.>

## Next Steps

- <Follow-on doc or action>
- <Integration, cleanup, monitoring guidance>

Summary: <Transition to broader workflows.>
````

## Quality & Style Rules

- Avoid em dashes; use hyphen.
- Keep commands minimal; prefer Azure CLI idempotent patterns.
- Do not embed secrets; instruct use of env vars or prerequisite docs.
- Use tables (`--output table`) only for human readability, not parsing.
- Provide explicit echo statements for ambiguous actions.
- Keep code blocks short and self-contained; group only tightly related
  commands and place unrelated steps in separate blocks.
- After each code block, include an `expected_similarity` test and a
  fenced `text` sample output to support quick verification. Ensure the
  regex matches the sample output. The `expected_similarity` value must
  be an actual regular expression, not the literal word `regex`.
- Similarity tests should validate successful execution outputs; avoid
  matching failure-only messages.

## Refinement Guidance (`/author refine`)

When refining an existing doc:

1. List missing sections or summaries.
2. Flag lines >80 chars.
3. Detect hard-coded identifiers (subscription IDs) outside variables.
4. Suggest idempotent guards where missing.
5. Recommend adding a Verification block if absent.

## Example Invocation

```

/author docs/incubation/Deploy_Feature_X.md --title "Deploy Feature X" --desc "Provision and validate Feature X components"

```

Expected response: A filled template with placeholders expanded using provided
`--title` and `--desc`.

## Output Expectations

The authoring assistant should return:

1. A proposed document (full markdown) ready to commit.
2. A remediation list (if refining) with actionable per-line guidance.
3. Zero ambiguous resource names without `${HASH}` if uniqueness needed.

## Non-Goals

- Does not execute commands (use `/execute` prompt for that).
- Does not generate diagrams or architecture images.
- Does not manage secrets or credential issuance.

## Summary

This prompt standardizes authoring of executable documents with predictable
sections, reproducible variable-driven commands, and built-in verification to
support automation and safe re-runs.

```

```
