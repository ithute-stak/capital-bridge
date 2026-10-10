# Go notification ingress runtime

The Go package now exposes `ServeIngress(ctx, listener, tlsCertificate, ingress)`.

It binds the authenticated `/internal/events` handler on a TLS listener with request and idle timeouts, rejects missing TLS credentials, short signing secrets and replay-only stores, and supports graceful shutdown.

**Important limitation:** This is a runtime component, not a deployed executable. An operations entrypoint must create a restricted PostgreSQL connection, load/rotate service certificates and HMAC secrets, inject `AtomicNotificationStore`, bind an appropriate listener, and invoke `ServeIngress`. PostgreSQL driver dependency, observability, controlled server startup and end-to-end deployment acceptance remain pending.

Never expose this endpoint publicly without network policy controls; the handler requires a valid timestamped HMAC signature but does not itself authenticate the network peer with mutual TLS.
