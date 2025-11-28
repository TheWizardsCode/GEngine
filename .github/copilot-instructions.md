## AI Agent Operating Guide (Concise)

Purpose: Provide immediately actionable knowledge for coding agents in this repository (MCPaaS + dynamic FastMCP server `innovation-engine-mcp`). Keep output factual, concise, and aligned with existing conventions.

### Architecture Essentials

- Root `innovation-engine-mcp/` is a FastMCP server. Entry: `src/main.py` parses --transport (stdio|http) and runs at path `/mcp` in HTTP mode.
- Dynamic tool discovery: `core/server.py` loads every `*.py` in `src/tools/` (except `__init__.py`) and expects each file to register at least one `@mcp.tool()` function; fail-fast if any tool errors.
- Configuration: `kmcp.yaml` feeds tool/env config via helper in `core/utils.py` (keep keys stable; add new tool config under `tools:`).
- HTTP transport endpoint expects JSON-RPC initialize with keys `client` and `protocol.version` (current FastMCP), not `clientInfo` or `protocolVersion`.

### Key Workflows

- Environment & deps: Use `uv sync --group dev` (no manual venv management). Tests & lint rely on uv.
- Run server: `uv run python src/main.py` (stdio) or `uv run python src/main.py --transport http --host 0.0.0.0 --port 3000`.
- Tasks (VS Code): use predefined tasks (labels start with `uv:`) instead of custom commands when possible.
- Tests: `scripts/test.sh` or task `uv: pytest (verbose)`. Add new tests under `innovation-engine-mcp/tests/` mirroring existing patterns (see `test_tools.py`, `test_server.py`).
- Tool addition: create new file `src/tools/<name>.py` with a function decorated by `@mcp.tool()` returning serializable types (prefer plain dict/str). Restart server to load.

### Patterns & Conventions

- One tool per file; filename becomes logical handle. Keep side effects minimal at import time (only decorator registration).
- Exec Docs (`docs/*.md`): structure as Introduction, Prerequisites, Setting up the environment, Steps, Summary, Next Steps. All command parameters passed via ALL_CAPS env vars; include `HASH=$(date -u +"%y%m%d%H%M")` for uniqueness.
- When an Exec Doc depends on other executable documents, define and export
  all environment variables in the "Setting up the environment" section
  before invoking or referencing those prerequisites so that a single,
  consistent environment is available to all linked documents.
- HTTP initialize example (correct schema): `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"client":{"name":"demo","version":"0.0.1"},"protocol":{"version":"2024-10-22"},"capabilities":{}}}`.
- Keep lines <=80 chars, use spaces for indentation, avoid em dashes (use hyphen).
- Prefer fast failure: if a tool cannot import or register, exit with non-zero (do not silently ignore).

### Modification Guidance

- Adding capabilities: update initialize handling only after verifying FastMCP supports new keys; document schema change in Exec Docs.
- Extending configuration: append to `kmcp.yaml` under `tools:<toolname>`; access via helper functions (avoid hard-coded env lookups sprinkled through code).
- Error handling: log and abort startup for load failures; inside tools return structured error text rather than raising unhandled exceptions.

### Testing & Quality

- For new tool: add a pytest asserting discovery (`server.get_tools_sync()` contains name) and behavior (simple args round-trip).
- Run `uv run pytest -k <toolname>` for focused iteration.
- Code quality: optional (only if needed) `uv run ruff check .`, `uv run mypy .`, `uv run black .`.

### Common Pitfalls

- Wrong initialize schema (clientInfo/protocolVersion) causes missing `mcp-session-id` header; ensure client/protocol keys.
- Forgetting to restart after adding tool => tool not loaded.
- Adding non-serializable return types from a tool (e.g. complex objects) -> JSON encoding errors.

### External Integration

- Kubernetes deployment uses KMCP controller via Exec Docs; treat those markdown files as runnable specs (do not hard-code values; rely on env vars).
- When updating deployment steps, keep variable-driven approach (no inline literal cluster names).
- When the user asks to "execute" an Exec Doc, assume it should be run
  via the innovation engine CLI and respond with the appropriate
  `ie execute <relative/path/to/doc.md>` command from the repo root,
  rather than attempting to re-interpret or manually replay individual
  code blocks.

### References

- Core server: `innovation-engine-mcp/src/core/server.py`
- Entry point: `innovation-engine-mcp/src/main.py`
- Tools examples: `innovation-engine-mcp/src/tools/echo.py`, `execute.py`
- Tests: `innovation-engine-mcp/tests/`
- Exec Doc example: `docs/OpenWebSearch_On_K8s_Local.md`

Clarifications or missing patterns should be surfaced before large refactors.
