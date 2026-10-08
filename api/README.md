# Finance API — initial authenticated read endpoint

This is an **initial** backend service, not production-ready. It uses verified OIDC RS256 JWTs (issuer, audience, signature and token lifetime) and looks up the caller's UUID `sub` as a company membership. All finance queries use PostgreSQL row-level-security context scoped to a single transaction.

## Configuration

Set secrets through a secret manager, never commit credentials:

- `CB_OIDC_ISSUER` — trusted HTTPS identity issuer
- `CB_OIDC_AUDIENCE` — exact expected token audience
- `CB_OIDC_JWKS_URL` — trusted HTTPS keyset endpoint (do not derive from user input)
- `CB_DATABASE_URL` — PostgreSQL DSN for a *non-owner, non-superuser, non-BYPASSRLS* application role

```sh
pip install -r api/requirements.txt
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### API

`GET /api/v1/companies/{company_id}/finance/trial-balance?as_of=2026-10-08`

Requires `Authorization: Bearer <OIDC token>`, and a matching record in `cb.memberships`.

## Production blockers

- Provision and verify a narrowly granted runtime DB role; migration-owner credentials must never be used as the API runtime.
- Enforce permitted roles and authorisation for each eventual write operation.
- Run integration tests with two independent company identities, including forbidden access cases.
- Add operation/audit logging, request limits, OIDC key caching strategy and reliability tests.
- Connect authenticated UI requests; the current dashboard continues to display demonstration data.
- Audit account reporting query planning, financial standards and currency configuration.

No real financial records should be loaded until these safeguards are completed and verified.
