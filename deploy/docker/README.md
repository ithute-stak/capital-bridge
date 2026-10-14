# CapitalBridge ONE image deployment (Ithute/LoanHub-style pull)

Two independently versioned GHCR images are published from a single git SHA:
`ghcr.io/ithute-stak/capital-bridge-api:sha-<40hex>` and
`ghcr.io/ithute-stak/capital-bridge-web:sha-<40hex>`.
The image workflow runs on changes to `main` or manually via GitHub Actions.

## VPS setup (Linux + Docker Compose v2)

Use a dedicated folder, e.g. `/opt/capitalbridge`, and copy the files in
`deploy/docker` there; retain the exact names. Do not run inside the existing
Ithute/LoanHub directory. Use the existing host Nginx as an external TLS proxy.
CapitalBridge web binds **127.0.0.1:3204**, API binds **127.0.0.1:8204**.
Check those ports are unused before deployment.

1. In GitHub Actions, run **Build and publish CapitalBridge images** after merge,
   and check BOTH image jobs are green. Their tags start with `sha-` followed by
   the publishing commit's full 40-character git SHA.
2. Authenticate the VPS to GHCR with an appropriately scoped read-only package
   token if packages are private: `docker login ghcr.io`. Never save a token in
   this repository or paste it into chat. Public images may be pulled anonymously.
3. `cd /opt/capitalbridge && cp .env.example .env && chmod 600 .env`
4. Edit `.env` to set a **real published image SHA** and authenticated finance
   database DSN. Leave both public-intake flags **false** until launch approval.
5. Make the deployment helper executable once, then run:
   `chmod +x pull-capitalbridge.sh && ./pull-capitalbridge.sh`
6. Add the supplied `vps-host-nginx.example.conf` server blocks to the EXISTING
   host Nginx configuration without replacing Ithute/LoanHub vhosts. Issue valid
   TLS certificates and validate `sudo nginx -t` before reloading.
7. Test `https://capitalbridge.co.ls/`,
   `https://capitalbridge.co.ls/health` (if separately routed),
   `https://capitalbridge.co.ls/api/v1/consultations/intake/readiness`,
   and the disabled state of public POST.
8. Provision distinct non-superuser database principals, migrations 028–030,
   Redis with protected credentials, approved Ithute Auth, and mail delivery.
   Only after passing staging smoke/security tests should an operator approve
   and enable public intake; see
   `docs/consolidated-159-167-release-handoff.md`.

The container running API intentionally does **not** create a database or run
migrations on startup. Failed database/auth connectivity cannot silently fall
back to an unsafe demo service. Service secrets belong in the VPS `.env`, not
the container image.

## Updating

Set `CB_IMAGE_TAG=sha-<new published SHA>` in `.env`, then run
`./pull-capitalbridge.sh`. Docker Compose pulls new pinned images and
recreates only the CapitalBridge services.

## Rollback

Retain your prior image tag securely. Change `CB_IMAGE_TAG` back to that
known-good value and rerun the helper. Database schema rollbacks need a
separately tested migration recovery plan; image rollback does not undo schema
changes.
