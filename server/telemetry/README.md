Telemetry Receiver Prototype

Run locally:

- Node (>= 14) is required
- Start the receiver:

  PORT=4005 node server/telemetry/receiver.js

It listens on `/` for HTTP POST JSON payloads.

Only events with `type: "director_decision"` (or `event_type` or nested `event.type`) are accepted and persisted to `server/telemetry/events.ndjson`.

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
- Events are appended to `server/telemetry/events.ndjson` as newline-delimited JSON lines with `received_at` timestamp.
