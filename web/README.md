# CapitalBridge ONE — Finance UI preview

This is a responsive **demonstration-only** browser interface. It displays sample financial data and offers navigation, client/reference search, status filtering, and CSV export of the currently displayed demonstration records.

It does **not** connect to the accounting database, authenticate users, generate real quotations or invoices, or store client records. Do not treat it as a live financial system.

## Run locally

From the repository root:

```sh
python3 -m http.server 8080 --directory web --bind 127.0.0.1
```

Open http://127.0.0.1:8080 in your browser. Use Ctrl+C to stop.

## Planned integration

Replace static records with authenticated, tenant-scoped read endpoints, then add server-side accounting authorization, validated write workflows, durable audit logs, bank reconciliation, and production-ready accessibility/security tests.

The financial transaction processing prototype lives under `accounting/`. The PostgreSQL schema groundwork is in `db/migrations/`. These components are not yet connected.
