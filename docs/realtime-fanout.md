# Finance real-time fanout boundary

Phase 88 adds a process-local registry that routes `finance.changed` invalidation notifications by `company_id`.

The registry is **not a broker and is not connected to browser WebSockets**. It is deliberately not exposed as an HTTP publish endpoint. Financial record contents do not travel through it; notified browsers will need to re-fetch their own authorised API state.

Requirements before production activation:

1. Consume accepted committed events from the authenticated Go ingress through a durable, authenticated cross-process transport (Redis Streams, PostgreSQL LISTEN/NOTIFY with recovery, or equivalent).
2. Ensure replay receipt recording is not confused with durable downstream fanout acceptance.
3. Recheck the user session and current company membership before every WebSocket send, with origin protection.
4. Drop/reconnect slow consumers; clients resynchronise from company-authorised APIs on reconnect.
5. Add multi-instance integration tests proving company boundaries, duplicate handling and failure recovery.

No production deployment or user-visible screen refresh is claimed in this phase.
