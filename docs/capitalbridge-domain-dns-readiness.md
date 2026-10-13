# CapitalBridge domain and mail DNS deployment checklist

Proposed public application domain: **https://capitalbridge.co.ls**  
Proposed API domain: **https://api.capitalbridge.co.ls**  
User-supplied origin address: **204.12.205.224**

These are proposed DNS settings, **not proof of DNS propagation, certificate issuance, application deployment, or a working mail server**.

## DNS zone records (verify with authoritative DNS before deployment)

| Owner | Type | Data |
|---|---|---|
| capitalbridge.co.ls. | A | 204.12.205.224 |
| api.capitalbridge.co.ls. | A | 204.12.205.224 |
| capitalbridge.co.ls. | MX | 10 mail.ithute.co.ls. |
| capitalbridge.co.ls. | TXT | v=spf1 mx -all |
| _dmarc.capitalbridge.co.ls. | TXT | v=DMARC1; p=quarantine; adkim=s; aspf=s; pct=100 |
| _imaps._tcp.capitalbridge.co.ls. | SRV | 0 1 993 mail.ithute.co.ls. |
| _submission._tcp.capitalbridge.co.ls. | SRV | 0 1 587 mail.ithute.co.ls. |
| capitalbridge.co.ls. | NS | ns1.ithute.co.ls. |
| capitalbridge.co.ls. | NS | ns2.ithute.co.ls. |

**Important correction:** The supplied NS text `ns1.ithute.co.ls.ns2.ithute.co.ls.` appears to concatenate *two* name servers. Confirm delegation at the registrar and publish separate NS RRs. Verify `ns2.ithute.co.ls` actually exists and answers authoritatively before delegating to it; do not create an unreachable secondary.

## Mail authentication

- Verify that `mail.ithute.co.ls` has a public A/AAAA record and the intended mail transport on TCP 25, 587, and 993 is configured with valid TLS.
- Current SPF `v=spf1 mx -all` authorizes only hosts resolved from the **CapitalBridge MX** record. If outbound email is sent by different servers, update SPF with the mail administrator; do not guess IPs or relax SPF just to pass validation.
- Confirm a DKIM selector and TXT public key under `<selector>._domainkey.capitalbridge.co.ls.` with the mail system. The provided zone includes no DKIM record; do not invent one.
- With `adkim=s; aspf=s`, verify DKIM and SPF *strict* identifier alignment for real outgoing CapitalBridge messages before treating `p=quarantine` as fully configured.
- Verify the mail server accepts `@capitalbridge.co.ls` recipients and test authenticated SMTP submission and IMAPS separately.

## HTTPS, routing and real-time events

1. Issue trusted certificates that cover `capitalbridge.co.ls` and `api.capitalbridge.co.ls` before exposing production traffic.
2. Route `https://capitalbridge.co.ls` to the frontend and same-origin `/api/v1` paths to the authenticated backend. A separate `api.` host alone does **not** satisfy clients that call relative `/api/v1` endpoints.
3. Set `AllowedOrigin=https://capitalbridge.co.ls` for the SSE gateway only after the application host is verified.
4. The Go SSE guard accepts explicit matching HTTPS Origin, or an absent Origin **only when the Go HTTP request has verified TLS and the exact configured Host**. A TLS-terminating proxy forwarding plain HTTP to Go will not meet this fallback; use a trusted TLS upstream or another explicitly audited authentication/CSRF deployment design. Never trust arbitrary `X-Forwarded-Proto` headers.
5. The `/api/v1/realtime/events` endpoint is not mounted in the current production service. Do not enable the browser realtime client or advertise working realtime features before session-cookie extraction, company membership verification, journal replay and service startup are connected and tested.
6. Existing browser clients may still use company-scoped WebSocket routes. Keep their authentication and reverse-proxy Upgrade handling distinct from SSE routes; do not assume they share a protocol.
7. Maintain isolation between the API and the internal `/internal/events` ingress; that ingress must not be publicly reachable.

## Pre-deployment probes (run from an independent host)

```sh
dig +short NS capitalbridge.co.ls
dig +short A capitalbridge.co.ls
dig +short A api.capitalbridge.co.ls
dig +short MX capitalbridge.co.ls
dig +short TXT capitalbridge.co.ls
dig +short TXT _dmarc.capitalbridge.co.ls
dig +short SRV _imaps._tcp.capitalbridge.co.ls
dig +short SRV _submission._tcp.capitalbridge.co.ls
# Substitute the actual DKIM selector from the mail operator:
# dig +short TXT <selector>._domainkey.capitalbridge.co.ls
curl --fail-with-body --verbose https://capitalbridge.co.ls/
curl --fail-with-body --verbose https://api.capitalbridge.co.ls/health
```

Run authenticated session and tenant-security checks before enabling any write routes or realtime subscriptions. Do not consider DNS readiness equivalent to production readiness.
