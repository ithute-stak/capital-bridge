# Distributed consultation intake rate limit — implementation foundation

The helper in `api/consultation_rate_limit.py` uses one atomic Redis Lua script to
count requests per pseudonymised trusted client IP across all API replicas.
The temporary counter expires after 600 seconds from its first increment.
Limit: five requests per IP per window; rejected requests also consume
counter increments. This is a **fixed** window, not a sliding-window limiter.

The required `secret` must be a strong, deployment-protected value. The
client IP MUST be resolved by a correctly configured trusted ingress, not
copied from an arbitrary `X-Forwarded-For` request header. Do not disclose the
secret or expose internal Redis keys in user-facing errors.

Redis failure or an untrusted/missing IP is a denial, never an allow. Do not
use in-memory per-process counters in production.

## Still missing before enabling public POST

- Integrate with a dedicated intake route, after trusted proxy IP resolution
- Deploy and secure Redis with application-specific credentials and capacity
- Add global and network-level budgets, bot controls, and alerting
- Enforce actual body bounds, origin checks, strict schema and consent
- Implement server-owned tenant write mediation under PostgreSQL RLS
- Perform real multi-worker and outage integration tests
- Approve privacy, retention, notices and delivery mechanisms

The public website must continue using its reviewed email workflow; no
unauthenticated submission route is enabled by this change.
