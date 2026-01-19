Telemetry Receiver Prototype

Purpose:

This receiver is a development prototype for collecting telemetry events emitted by the Director and related runtime components. It is intended for local testing and experimentation only — not for production use. Use it to:

- Capture and inspect `director_decision` events emitted by the Director during playtests.
- Exercise telemetry payload shapes and validate downstream processing or analysis scripts.
- Provide a simple, disposable storage backend (newline-delimited JSON) for quick local debugging.

Do not rely on this receiver for production telemetry: it has no authentication, no retention/rotation, and minimal error handling.

Run locally:

- Node (>= 14) is required
- Start the receiver:

  PORT=4005 node server/telemetry/receiver.js

It listens on `/` for HTTP POST JSON payloads.

Accepted events:

Only events with `type: "director_decision"` (or `event_type` or nested `event.type`) are accepted and persisted to `server/telemetry/events.ndjson`.

Expected payload shape (example):

  {
    "type": "director_decision",
    "decision": "accept",
    "reason": "low_risk",
    "meta": { "user": "test" }
  }

Example curl test:

  curl -v -X POST \
    -H "Content-Type: application/json" \
    -d '{"type":"director_decision","decision":"accept","meta":{"user":"test"}}' \
    http://localhost:4005/

Expected responses:
- 200 {"ok":true} for valid director_decision events
- 400 {"error":"Invalid or unsupported event type"} for invalid event types
- 400 {"error":"Invalid JSON"} for malformed JSON
- 404 for non-POST or other paths

Storage:
- Events are appended to `server/telemetry/events.ndjson` as newline-delimited JSON lines with a `received_at` timestamp.

Notes / next steps:
- This is intentionally minimal. For follow-up work consider adding SQLite persistence, simple schema validation, or basic authentication before using in shared environments.
