"""Quotation lifecycle and conversion into posted service invoices.

This prototype is a local SQLite domain layer. Authentication and authorization
must be supplied by a trusted application service before any real-world use.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from accounting.billing import Invoice, issue_invoice
from accounting.ledger import LedgerError

SCHEMA = """
CREATE TABLE IF NOT EXISTS quotations (
 id INTEGER PRIMARY KEY,
 number TEXT UNIQUE NOT NULL,
 client_reference TEXT NOT NULL,
 division TEXT NOT NULL,
 description TEXT NOT NULL,
 net_minor INTEGER NOT NULL CHECK(net_minor > 0),
 tax_minor INTEGER NOT NULL CHECK(tax_minor >= 0),
 created_on TEXT NOT NULL,
 expires_on TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'draft'
 CHECK(status IN ('draft','approved','accepted','rejected','expired','invoiced')),
 invoice_id INTEGER UNIQUE REFERENCES invoices(id)
);
CREATE TRIGGER IF NOT EXISTS quotation_lock_financial_terms
BEFORE UPDATE OF number,client_reference,division,description,net_minor,tax_minor,created_on,expires_on
ON quotations WHEN OLD.status <> 'draft'
BEGIN SELECT RAISE(ABORT,'approved quotation terms are immutable'); END;
"""

@dataclass(frozen=True)
class Quotation:
    number: str
    client_reference: str
    division: str
    description: str
    net_minor: int
    tax_minor: int
    created_on: str
    expires_on: str


def initialise_quotations(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)


def create_quotation(db: sqlite3.Connection, quote: Quotation) -> int:
    if not all((quote.number.strip(), quote.client_reference.strip(),
                quote.division.strip(), quote.description.strip())):
        raise LedgerError("quotation identifiers, division and description required")
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (quote.net_minor, quote.tax_minor)):
        raise LedgerError("amounts must be integer minor units")
    if quote.net_minor <= 0 or quote.tax_minor < 0:
        raise LedgerError("invalid quotation amounts")
    if date.fromisoformat(quote.expires_on) < date.fromisoformat(quote.created_on):
        raise LedgerError("expiry before quotation date")
    with db:
        cur = db.execute(
            "INSERT INTO quotations(number,client_reference,division,description,net_minor,"
            "tax_minor,created_on,expires_on) VALUES (?,?,?,?,?,?,?,?)",
            (quote.number,quote.client_reference,quote.division,quote.description,
             quote.net_minor,quote.tax_minor,quote.created_on,quote.expires_on))
    return int(cur.lastrowid)


def transition(db: sqlite3.Connection, quotation_id: int, action: str, today: str) -> None:
    flow = {"approve":("draft","approved"), "accept":("approved","accepted"),
            "reject":("approved","rejected"), "expire":("approved","expired")}
    if action not in flow:
        raise LedgerError("unsupported quotation action")
    valid_date = date.fromisoformat(today).isoformat()
    prior, new = flow[action]
    with db:
        row = db.execute("SELECT expires_on FROM quotations WHERE id=?", (quotation_id,)).fetchone()
        if row is None:
            raise LedgerError("quotation not found")
        if action == "accept" and valid_date > row[0]:
            raise LedgerError("cannot accept an expired quotation")
        if action == "expire" and valid_date <= row[0]:
            raise LedgerError("quotation has not expired")
        cur = db.execute("UPDATE quotations SET status=? WHERE id=? AND status=?",
                         (new,quotation_id,prior))
        if cur.rowcount != 1:
            raise LedgerError("invalid quotation status transition")


def convert_to_invoice(
    db: sqlite3.Connection, quotation_id: int, invoice_number: str,
    issued_on: str, due_on: str, receivable_account: str, revenue_account: str,
    tax_payable_account: str | None = None
) -> int:
    issued = date.fromisoformat(issued_on).isoformat()
    row = db.execute(
        "SELECT number,client_reference,division,description,net_minor,tax_minor,expires_on,status "
        "FROM quotations WHERE id=?", (quotation_id,)
    ).fetchone()
    if row is None or row[7] != "accepted":
        raise LedgerError("quotation must be accepted before conversion")
    if issued > row[6]:
        raise LedgerError("cannot convert an expired quotation")
    db.execute("SAVEPOINT convert_quotation")
    try:
        inv = Invoice(invoice_number,row[1],row[2],row[3],row[4],row[5],issued,due_on)
        invoice_id = issue_invoice(db,inv,receivable_account,revenue_account,tax_payable_account)
        count = db.execute(
            "UPDATE quotations SET status='invoiced',invoice_id=? WHERE id=? AND status='accepted'",
            (invoice_id,quotation_id)).rowcount
        if count != 1:
            raise LedgerError("quotation conversion conflict")
        db.execute("RELEASE SAVEPOINT convert_quotation")
        return invoice_id
    except Exception:
        db.execute("ROLLBACK TO SAVEPOINT convert_quotation")
        db.execute("RELEASE SAVEPOINT convert_quotation")
        raise


def quotation_summary(db: sqlite3.Connection) -> list[tuple[str,int,int]]:
    return list(db.execute(
        "SELECT status,COUNT(*),COALESCE(SUM(net_minor+tax_minor),0) "
        "FROM quotations GROUP BY status ORDER BY status"
    ))
