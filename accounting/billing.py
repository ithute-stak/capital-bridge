"""Minimal service-invoicing workflow, sharing the accounting database transaction.

An invoice posts AR/revenue/tax when issued; settlement posts bank/AR.
Amounts are integer minor units. Tax is configurable; no tax rate is assumed.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from accounting.ledger import LedgerError, Posting, post_journal

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
 id INTEGER PRIMARY KEY,
 number TEXT NOT NULL UNIQUE,
 client_reference TEXT NOT NULL,
 division TEXT NOT NULL,
 description TEXT NOT NULL,
 net_minor INTEGER NOT NULL CHECK(net_minor > 0),
 tax_minor INTEGER NOT NULL CHECK(tax_minor >= 0),
 issued_on TEXT NOT NULL,
 due_on TEXT NOT NULL,
 journal_id INTEGER NOT NULL UNIQUE REFERENCES journals(id)
);
CREATE TABLE IF NOT EXISTS receipts (
 id INTEGER PRIMARY KEY,
 reference TEXT NOT NULL UNIQUE,
 invoice_id INTEGER NOT NULL REFERENCES invoices(id),
 amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
 received_on TEXT NOT NULL,
 journal_id INTEGER NOT NULL UNIQUE REFERENCES journals(id)
);
"""

@dataclass(frozen=True)
class Invoice:
    number: str
    client_reference: str
    division: str
    description: str
    net_minor: int
    tax_minor: int
    issued_on: str
    due_on: str


def initialise_billing(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


def _positive_int(value: int, label: str, zero_allowed: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < (0 if zero_allowed else 1):
        raise LedgerError(f"{label} must be integer minor units")


def issue_invoice(
    connection: sqlite3.Connection,
    invoice: Invoice,
    receivable_account: str,
    revenue_account: str,
    tax_payable_account: str | None = None,
) -> int:
    _positive_int(invoice.net_minor, "net_minor")
    _positive_int(invoice.tax_minor, "tax_minor", zero_allowed=True)
    if not all((invoice.number.strip(), invoice.client_reference.strip(),
                invoice.division.strip(), invoice.description.strip())):
        raise LedgerError("invoice details cannot be blank")
    if date.fromisoformat(invoice.due_on) < date.fromisoformat(invoice.issued_on):
        raise LedgerError("due date cannot precede issue date")
    if invoice.tax_minor and not tax_payable_account:
        raise LedgerError("tax payable account is required for taxable invoices")
    amount = invoice.net_minor + invoice.tax_minor
    lines = [
        Posting(receivable_account, debit_minor=amount, division=invoice.division),
        Posting(revenue_account, credit_minor=invoice.net_minor, division=invoice.division),
    ]
    if invoice.tax_minor:
        lines.append(Posting(tax_payable_account, credit_minor=invoice.tax_minor, division=invoice.division))
    # The caller's connection is local to this operation; rollback invoice journal
    # if the invoice insert fails, via a SAVEPOINT within the outer transaction.
    connection.execute("SAVEPOINT invoice_issue")
    try:
        jid = post_journal(connection, invoice.issued_on, "INV:" + invoice.number,
                           "Invoice " + invoice.number + ": " + invoice.description, lines)
        cursor = connection.execute(
            "INSERT INTO invoices(number,client_reference,division,description,net_minor,tax_minor,"
            "issued_on,due_on,journal_id) VALUES (?,?,?,?,?,?,?,?,?)",
            (invoice.number, invoice.client_reference, invoice.division, invoice.description,
             invoice.net_minor, invoice.tax_minor, invoice.issued_on, invoice.due_on, jid))
        connection.execute("RELEASE SAVEPOINT invoice_issue")
        return int(cursor.lastrowid)
    except Exception:
        connection.execute("ROLLBACK TO SAVEPOINT invoice_issue")
        connection.execute("RELEASE SAVEPOINT invoice_issue")
        raise


def record_receipt(
    connection: sqlite3.Connection, invoice_id: int, reference: str, amount_minor: int,
    received_on: str, bank_account: str, receivable_account: str,
) -> int:
    _positive_int(amount_minor, "amount_minor")
    if not reference.strip():
        raise LedgerError("receipt reference required")
    invoice = connection.execute(
        "SELECT division,net_minor+tax_minor FROM invoices WHERE id=?", (invoice_id,)
    ).fetchone()
    if invoice is None:
        raise LedgerError("invoice not found")
    paid = connection.execute(
        "SELECT COALESCE(SUM(amount_minor),0) FROM receipts WHERE invoice_id=?", (invoice_id,)
    ).fetchone()[0]
    if amount_minor > invoice[1] - paid:
        raise LedgerError("receipt exceeds unpaid invoice balance")
    connection.execute("SAVEPOINT receipt_create")
    try:
        jid = post_journal(
            connection, received_on, "RCT:" + reference, "Receipt for invoice " + str(invoice_id),
            [Posting(bank_account, debit_minor=amount_minor, division=invoice[0]),
             Posting(receivable_account, credit_minor=amount_minor, division=invoice[0])])
        cursor = connection.execute(
            "INSERT INTO receipts(reference,invoice_id,amount_minor,received_on,journal_id)"
            " VALUES (?,?,?,?,?)", (reference, invoice_id, amount_minor, received_on, jid))
        connection.execute("RELEASE SAVEPOINT receipt_create")
        return int(cursor.lastrowid)
    except Exception:
        connection.execute("ROLLBACK TO SAVEPOINT receipt_create")
        connection.execute("RELEASE SAVEPOINT receipt_create")
        raise


def outstanding_minor(connection: sqlite3.Connection, invoice_id: int) -> int:
    row = connection.execute(
        "SELECT (i.net_minor+i.tax_minor)-COALESCE(SUM(r.amount_minor),0) "
        "FROM invoices i LEFT JOIN receipts r ON i.id=r.invoice_id WHERE i.id=? GROUP BY i.id",
        (invoice_id,)).fetchone()
    if row is None:
        raise LedgerError("invoice not found")
    return int(row[0])
