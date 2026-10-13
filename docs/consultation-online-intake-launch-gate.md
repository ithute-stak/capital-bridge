# Public consultation intake: launch gate

The public consultation form currently prepares a user-reviewed email. It must not report a successful server submission, or silently store personal information.

## Prerequisites before activating online submission

1. Configure a trusted, server-owned mapping from the public CapitalBridge website to the one approved company ID. Never accept a caller-selected `company_id` in an unauthenticated request.
2. Implement a dedicated, restricted intake database principal with permission only to insert approved enquiry fields for the mapped tenant. The staff capability role is **not** the public intake role. Keep RLS forced, and verify real PostgreSQL execution with no membership leakage.
3. Add an edge-enforced per-IP/per-origin abuse budget with bounded request bodies, spam controls, and observability. A permissive client-side timer is not rate limiting.
4. Approve privacy wording, retention periods, deletion/export process and notification recipients before processing real customer data.
5. Set up a durable delivery path for staff alerts with idempotency, audit logs and retries, without making notification success a prerequisite for persistence.
6. Add browser/API integration tests: valid submission, consent rejection, malformed body, injected tenant, repeated requests, cross-tenant access, rate limits, network failure and mobile UX.
7. Verify TLS, actual deployment health and staff authorization with production configuration before changing the published form from `mailto:` to API POST.

Until all these gates pass, `GET /api/v1/consultations/intake/readiness` deliberately returns `online_submission_available=false`, and no anonymous submission route is registered.
