---
mode: agent
model: GPT-5
tools:
  - "runCommands"
  - "edit/createFile"
  - "edit/createDirectory"
  - "edit/editFiles"
  - "search"
  - "runTests"
  - "changes"
  - "openSimpleBrowser"
  - "fetch"
description: "Execute the commands in an executable document and verify the results."
---

# Executable Document Execution and Verification Prompt

## Goal

Execute the commands in an executable document, verify the results, and ensure the intended outcomes are achieved.

## Overview

This prompt equips an automated agent to read through an executable document, run the commands step-by-step, and confirm that each step produces the expected results.

Supported prompt commands are:

- /execute
  Execute the current document as an executable document.
- /execute documentPath.md
  Execute the named document as an executable document.

## Execution Steps

Follow these steps to execute and verify the commands in the executable document:

1. **Read the Executable Document**: Parse the document to extract commands and their intended outcomes. Always read the latest version of the document to ensure accuracy. Environment variables should be set using the appropriate fenced code blocks, unless told otherwise.
2. **Set Up Execution Environment**: Use the same environment to execute each code block and set the environment variables once only, unless required otherwise by the code itself. Ensure all necessary tools and dependencies are available. Including executing any pre-requisite document linked.
3. **Test if Document needs to be executed**: Determine if the document has already been executed successfully or if re-execution is necessary by executing the commands in the Validation, or Verification section (if present).
4. **Execute Commands**: Run each command sequentially, capturing output and errors. Fenced code blocks that are contained in HTML comments should be ignored. Do not execute commands that are not in the document unless they are in an attempt to debug a failure.
5. **Handle Errors**: If a command fails, attempt to diagnose and fix the issue before proceeding. See author.prompt.msd for guidance on authoring/fixing executable documents.
6. **Verify Outputs**: Compare the actual outputs against the expected results.
7. **Log Results**: Document the execution process, including any issues encountered.
8. **Summarize Execution**: Provide a final report on the success of the execution.

## Key Considerations

- Ensure that the execution environment is properly configured to run the commands in the document.
- Handle errors gracefully, providing clear feedback on what went wrong and potential fixes.
- Maintain a detailed log of all actions taken, outputs received, and verifications performed.
- Provide a final summary that clearly indicates whether the executable document was successfully executed and verified.
