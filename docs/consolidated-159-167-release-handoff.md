# CapitalBridge ONE — consolidated phases 159–167 release handoff

## Implemented on the consolidated branch

- Public `POST /api/v1/consultations` is explicitly gated by both
  `CB_PUBLIC_INTAKE_ENABLED=true` and `CB_PUBLIC_INTAKE_APPROVED=true`.
  Both default to disabled.
- Strict origin/JSON/8 KB streamed body checks, validated consent and service,
  Redis fixed-window per trusted-peer rate budget, and company mapping from
  `CB_CONSULTATION_COMPANY_ID` (never from the visitor payload).
- Dedicated `CB_CONSULTATION_INTAKE_DSN`, checked to be a non-superuser,
  non-BYPASSRLS PostgreSQL principal inheriting `cb_consultation_intake`.
- Database migration 028 checks the company against a DBA-owned
  `cb.consultation_intake_config` singleton under forced RLS; the intake role
  has no permission to change that record.
- Public form checks readiness and uses direct POST only when explicitly
  enabled; otherwise it opens the prepared email.
- DB migration 029 atomically stores notification intent in an outbox.
  An opt-in SMTP notification worker exists, but its read access must be
  reviewed under RLS before it is scheduled. Delivery is at-least-once.
- Staff queue refreshes authorised records while the tab is visible. This is
  polling, not true socket-based realtime; a durable multi-instance broker
  integration is still required.

## Operator-only deployment prerequisites

1. Apply migrations 028–030 **in order**, after prior migrations. Set
   `cb.consultation_intake_config` singleton company_id to the exact approved
   CapitalBridge company. The backend's environment tenant must match.
2. Provision a **dedicated LOGIN role** for public intake, with no superuser
   and no BYPASSRLS, and grant it the NOLOGIN `cb_consultation_intake`
   capability. Use a private DB DSN with TLS/credential rotation; do not
   reuse the finance or staff DB account.
3. Configure Redis with network isolation, authentication and persistence
   expectations. Set `CB_CONSULTATION_REDIS_URL` and a protected randomly
   generated `CB_CONSULTATION_RATE_SECRET` (32+ characters).
4. Reverse proxy must terminate TLS, enforce an 8 KB maximum request body,
   strictly control forwarded headers and provide a **verified peer IP** for
   rate limiting. The application currently reads `request.client.host`:
   without a trusted proxy/ASGI topology, all visitors may share one quota.
   Do not enable direct intake until a realistic proxy-to-API test passes.
5. Agree on customer privacy notice, consent, retention/deletion rules,
   spam protections, business notification recipient and email transport.
   Test customer-specific cases without real passports or identity records.
6. Verify approved production Ithute Auth configuration, credential
   lifecycle, bearer validation, staff permissions and responsive browser UI.
   Server-side staff login readiness is intentionally closed by default.
7. Run isolated browser/mobile tests, DB migrations/rollback tests,
   API integration tests against real Redis and PostgreSQL, security tests,
   email-delivery tests and resilience/load tests on staging.
8. Keep `CB_PUBLIC_INTAKE_ENABLED=false` and
   `CB_PUBLIC_INTAKE_APPROVED=false` until all operator checks pass.
   Never use the website JavaScript or a GitHub merge as the activation control.
9. Attach the optional notification worker only after a separate reviewed RLS
   dequeue capability and dedicated worker grants are in place.
10. Deploy to staging first, inspect health and logs, then authorize production
    rollout with a tested rollback path. CI passing is not proof of deployment.

## Remaining externally dependent work

True multi-instance WebSocket/SSE push for consultations, live Ithute session
activation, the outbound email worker's RLS dequeue interface, notification
recipient approval, production secrets, and verified DNS/TLS deployment remain
open gates. The code should not be scored 10/10 or called live until verified.
