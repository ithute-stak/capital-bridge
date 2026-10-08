# Finance reporting requirements and acceptance criteria

This work creates reporting functions over local SQLite prototype records, not a deployed API.

## Definitions
- **Invoiced in range**: sum of issued invoice gross totals whose issue date falls within the requested inclusive range.
- **Received in range**: sum of recorded receipt amounts whose received date falls within the requested inclusive range.
- **Outstanding as of end**: invoices issued on or before the range end, less receipts recorded on or before that end. This is not invoiced-in-range minus received-in-range.
- **Accepted quotation pipeline**: sum of accepted quotation gross totals created on or before the report end; unconverted quotations only.
- **Revenue by division**: invoice amounts excluding tax, grouped by originating service division; accounting policy and adjustments can affect recognized revenue. Before a production dashboard claims recognized revenue, use the posted revenue journal with appropriate accrual recognition and credit-note support.
- **Trial balance**: journal-derived debit and credit net per ledger account as of an inclusive date.

## Guardrails
- Reporting must become company-scoped before any company records are loaded.
- No unauthenticated HTTP endpoint may expose financial reports.
- All financial amounts are integer minor units (LSL in early single-currency prototype).
- All management reports require validation against journals, receipts, refunds, adjustments, allocations, and professional accounting policy before being described as statutory statements.
- API and frontend integration are a separate milestone.
