Artifacts
---------

This directory is used to store CI and local run artifacts produced by the replay harness and other test jobs.

- Purpose: temporary outputs such as logs, JSON result files, and compressed archives (e.g. `replay-results.tgz`).
- Not tracked: `artifacts/` is ignored by git and should not be committed. Files here are ephemeral and created by CI or local runs.
- Examples of files produced:
  - `artifacts/logs/replay.<story>.log`
  - `artifacts/results/replay.<story>.result.json`
  - `artifacts/replay-results.tgz`

If you need to persist a specific artifact, upload it to an external storage or attach it to a CI run rather than committing it to the repository.
