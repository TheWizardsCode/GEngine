Telemetry receiver (dev prototype)

This lightweight receiver accepts POST JSON events and persists director_decision events to `server/telemetry/events.ndjson`.

Run locally:

```bash
node server/telemetry/receiver.js
# listens on :4005 by default
```

Test with curl (valid director_decision event):

```bash
curl -X POST http://localhost:4005/ -H 'Content-Type: application/json' -d '{"type":"director_decision","proposal_id":"p1","decision":"approve","riskScore":0.12}'
```

Invalid payload (non-director_decision) returns 400.

Notes:
- This is a dev prototype; production hardening (SQLite persistence, auth, schema validation) tracked in `ge-apq.1`.
