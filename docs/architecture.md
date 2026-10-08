# CapitalBridge ONE — architecture decisions (initial)
 
## Domain boundaries
Immigration and mobility, consultancy, IT, engineering, training, and administration produce independently validated business events. A central accounting service owns posted journal entries. Modules do not write directly to ledger tables.

## Accounting invariants
- All money uses integer minor units and an explicit currency at external interfaces. Current core assumes a single configured currency; multi-currency posting and FX are not implemented.
- Each journal contains two or more lines, all individually debit-only or credit-only, with equal aggregate debits and credits.
- Journals and their lines cannot be edited or deleted after posting; post a reversal to correct an error.
- Posting is transactional and requires an open, non-overlapping accounting period.
- Journal reference is unique, enabling rejection of duplicate external references (later extend to scoped idempotency keys).
- Account type and division attribution are explicit.
- Trial balance reads ledger journal lines, not an independently maintained total.

## Planned next work
1. Replace single-file SQLite prototype with PostgreSQL migrations and durable per-company ledger separation before production use.
2. Add authenticated Go or Python API, permissions, staff and business entities, and posting approvals.
3. Add document and invoicing workflows with separate receivables/payables subledgers and account reconciliation.
4. Add reconciliations, financial statements, company-level audit trails and tax configuration with professional accountant review.
5. Build the branded web dashboard and client portal, then connect immigration cases.
6. Expand tests with concurrency, property checks, backups, restore drills and security assessment.

## Security and deployment
This repository is **not ready for production or real customer/financial data**. It presently has a demonstrable local accounting library, not an authenticated financial API. No credentials or sensitive source documents should be committed.

## Reference
Accounting concepts are informed by Frank Wood's Business Accounting, 15th ed. (Sangster and Gordon), particularly chapters 1–6, 11–16, 19–26, 28, 35–39. Local law, tax, payroll, retention and professional standards need separate verification.
