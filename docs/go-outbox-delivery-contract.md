# Committed finance event delivery contract

Phase 77 establishes a Go validation boundary for events originating in `cb.finance_outbox`. It **does not** deploy a relay, subscribe clients, expose WebSockets, or authorize a user. A successful envelope parse must never be interpreted as permission to access a company.

- Python financial services insert outbox rows in the **same PostgreSQL transaction** as the business action; only committed rows are eligible for delivery.
- The prospective dispatcher will read pending rows using a dedicated least-privilege database role and `FOR UPDATE SKIP LOCKED` with retry/backoff and delivery idempotency. This dispatcher is **not implemented**.
- Go accepts a version-1 event with a unique event ID, company ID, aggregate ID and a strict allowlisted event type. Nonconforming events are rejected.
- Future subscribers must authenticate via Ithute and have company membership checked server-side before receiving events. A `company_id` inside the message is not sufficient authorisation.
- Outbox events are notifications, not financial truth: consumers must refresh the appropriate authorised API record and must tolerate duplicate/out-of-order messages.

Remaining: authenticated internal transport, dispatcher, retry/dead-letter handling, server-side subscriber authorisation, and end-to-end integration tests.
