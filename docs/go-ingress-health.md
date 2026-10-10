# Go ingress health endpoint

Phase 106 adds GET /internal/health to the TLS ingress server when backed by AtomicNotificationStore. It uses a two-second bounded PostgreSQL ping and returns HTTP 200 only when connectivity is available; database outage gives 503, without exposing credentials. Non-GET methods receive 405.

The endpoint must be limited to trusted internal networks by firewall or reverse-proxy policy. It is not a proof that notifications are reaching browsers or that an outbox worker is running. Use a separate end-to-end synthetic delivery test before enabling production traffic.
