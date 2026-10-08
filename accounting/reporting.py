"""Read-only finance reporting from actual posted ledger and invoices.

This module is not a network API. It deliberately performs no identity checks;
a future authenticated service must scope records to a company before exposure.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from accounting.ledger import LedgerError


@dataclass(frozen=True)
class FinanceSummary:
    invoiced_minor: int
    received_minor: int
    outstanding_minor: int
    quotation_pipeline_minor: int


def financial_summary(db: sqlite3.Connection, start: str, end: str) -> FinanceSummary:
    from datetime import date
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise LedgerError("invalid reporting period")
    invoiced = db.execute(
        "SELECT COALESCE(SUM(net_minor+tax_minor),0) FROM invoices WHERE issued_on BETWEEN ? AND ?",
        (start, end),
    ).fetchone()[0]
    received = db.execute(
        "SELECT COALESCE(SUM(amount_minor),0) FROM receipts WHERE received_on BETWEEN ? AND ?",
        (start, end),
    ).fetchone()[0]
    # Outstanding is an as-of snapshot, not 'invoiced less receipts in range':
    # include all invoices issued by end and all corresponding receipts by end.
    outstanding = db.execute(
        """SELECT COALESCE(SUM(i.net_minor+i.tax_minor-COALESCE(p.paid,0)),0)
           FROM invoices i LEFT JOIN (
             SELECT invoice_id,SUM(amount_minor) AS paid
             FROM receipts WHERE received_on<=? GROUP BY invoice_id
           ) p ON p.invoice_id=i.id
           WHERE i.issued_on<=?""",
        (end, end),
    ).fetchone()[0]
    pipeline = db.execute(
        "SELECT COALESCE(SUM(net_minor+tax_minor),0) FROM quotations "
        "WHERE status='accepted' AND created_on<=?",
        (end,),
    ).fetchone()[0]
    return FinanceSummary(int(invoiced), int(received), int(outstanding), int(pipeline))


def division_revenue(db: sqlite3.Connection, start: str, end: str) -> list[tuple[str, int]]:
    """Revenue by division, excluding tax; issued invoices only."""
    from datetime import date
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise LedgerError("invalid reporting period")
    return [(name, int(value)) for name, value in db.execute(
        "SELECT division,SUM(net_minor) FROM invoices WHERE issued_on BETWEEN ? AND ? "
        "GROUP BY division ORDER BY division", (start, end),
    )]


def trial_balance_as_of(db: sqlite3.Connection, end: str) -> list[tuple[str, str, int, int]]:
    """Trial balance for journals posted through the specified inclusive date."""
    from datetime import date
    date.fromisoformat(end)
    return [
        (code, name, max(net, 0), max(-net, 0))
        for code, name, net in db.execute(
            "SELECT a.code,a.name,COALESCE(SUM(l.debit_minor-l.credit_minor),0) "
            "FROM accounts a LEFT JOIN journal_lines l ON l.account_code=a.code "
            "LEFT JOIN journals j ON j.id=l.journal_id AND j.posted_on<=? "
            "GROUP BY a.code,a.name ORDER BY a.code",
            (end,),
        )
    ]
