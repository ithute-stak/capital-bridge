# CapitalBridge ONE edge deployment (reference configuration)

File: `deploy/nginx/capitalbridge.example.conf`.

This is a **reviewable example only**, not a deployed or ready-to-enable virtual host. DNS A records supplied by the operator point `capitalbridge.co.ls` and `api.capitalbridge.co.ls` to `204.12.205.224`, but propagation, ports and server identity were **not** checked by this PR.

## Routing contract

- `https://capitalbridge.co.ls/` serves static `web/` assets; some of these are explicitly demonstration-only.
- `https://capitalbridge.co.ls/api/` reverse proxies to an independently protected finance API bound on private/loopback `127.0.0.1:8200`. Adjust to the actual secure listening port and verify user/auth/tenant protection before activation.
- `https://api.capitalbridge.co.ls/api/` and `/health` use that API; the API currently has a minimal `/health` response.
- `https://capitalbridge.co.ls/api/v1/realtime/events` reserves a distinct TLS-authenticated upstream on `127.0.0.1:8201`, with a trusted private CA. **This upstream route is not mounted by the Go service today**; do not enable until the SSE handler is wired to server-side session extraction, company authorization, journal replay, and listener supervision.
- Public `/internal/` is denied at both virtual hosts. Keep HMAC ingress on a separate private listener and enforce firewall policy. Also explicitly deny accidental alternative hostnames.

## Security prerequisites

1. Provision public certificates for both names, private keys restricted to the Nginx operator, and a separate upstream CA and certificate for the Go SSE service.
2. Ensure the Go upstream's certificate is valid for `realtime.internal.capitalbridge.co.ls`; it must receive a genuine TLS request because its originless-EventSource check requires verified TLS. If the client sends an Origin header, the proxy preserves it; it must **not manufacture** a trusted origin.
3. Run `nginx -t` against the installed, reviewed configuration and check that upstreams have actually been provisioned; never apply this example automatically.
4. Keep frontend auth and API route policies consistent. No bearer token should be embedded in a browser URL or stored in localStorage.
5. Ensure SSE read timeout and connection limits fit the application; protect against slow connections and unexpected event gaps. Consider separate limits and logging on this endpoint.
6. Evaluate proxy headers and scheme/Host checks for every auth boundary. Only trust headers from a known reverse proxy, and never rely on arbitrary forwarded headers to prove TLS or identity.
7. Reconcile existing company-scoped WebSocket client routes with the intended SSE stream before removing any protocol or shipping a connected UI.
8. Test cross-company replay and authorization before enabling CORS or permitting any new origin.

## Verification after provisioning

```sh
sudo nginx -t
curl -I https://capitalbridge.co.ls/
curl -fsS https://api.capitalbridge.co.ls/health
curl -i https://capitalbridge.co.ls/internal/events  # must be denied
curl -i https://api.capitalbridge.co.ls/internal/events # must be denied
```

The repository does not currently contain proof of production certificates, a bound SSE gateway, a deployed host, or live DNS validation. Do not describe this configuration as deployed.
