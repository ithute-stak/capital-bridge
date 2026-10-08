"""CapitalBridge ONE accounting core. Monetary amounts are integer minor units."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class Posting:
    account_code: str
    debit_minor: int = 0
    credit_minor: int = 0
    division: str = "central"


class LedgerError(ValueError):
    pass


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS accounts (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('asset','liability','equity','revenue','expense')),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1))
);
CREATE TABLE IF NOT EXISTS accounting_periods (
    id INTEGER PRIMARY KEY,
    starts_on TEXT NOT NULL,
    ends_on TEXT NOT NULL,
    is_closed INTEGER NOT NULL DEFAULT 0 CHECK(is_closed IN (0,1)),
    CHECK (starts_on <= ends_on)
);
CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY,
    posted_on TEXT NOT NULL,
    period_id INTEGER NOT NULL REFERENCES accounting_periods(id),
    reference TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    reversal_of INTEGER UNIQUE REFERENCES journals(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS journal_lines (
    id INTEGER PRIMARY KEY,
    journal_id INTEGER NOT NULL REFERENCES journals(id),
    account_code TEXT NOT NULL REFERENCES accounts(code),
    division TEXT NOT NULL,
    debit_minor INTEGER NOT NULL DEFAULT 0 CHECK (debit_minor >= 0),
    credit_minor INTEGER NOT NULL DEFAULT 0 CHECK (credit_minor >= 0),
    CHECK ((debit_minor > 0 AND credit_minor = 0) OR
           (credit_minor > 0 AND debit_minor = 0))
);
CREATE INDEX IF NOT EXISTS ix_lines_account ON journal_lines(account_code, journal_id);
CREATE TRIGGER IF NOT EXISTS no_journal_delete BEFORE DELETE ON journals
BEGIN SELECT RAISE(ABORT, 'posted journals cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS no_journal_update BEFORE UPDATE ON journals
BEGIN SELECT RAISE(ABORT, 'posted journals cannot be edited'); END;
CREATE TRIGGER IF NOT EXISTS no_line_delete BEFORE DELETE ON journal_lines
BEGIN SELECT RAISE(ABORT, 'posted journal lines cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS no_line_update BEFORE UPDATE ON journal_lines
BEGIN SELECT RAISE(ABORT, 'posted journal lines cannot be edited'); END;
"""


def initialise(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


def add_account(connection: sqlite3.Connection, code: str, name: str, kind: str) -> None:
    if kind not in {"asset", "liability", "equity", "revenue", "expense"}:
        raise LedgerError("invalid account kind")
    with connection:
        connection.execute("INSERT INTO accounts(code,name,kind) VALUES (?,?,?)", (code, name, kind))


def open_period(connection: sqlite3.Connection, starts_on: str, ends_on: str) -> int:
    start, end = date.fromisoformat(starts_on), date.fromisoformat(ends_on)
    if start > end:
        raise LedgerError("period start must precede its end")
    if connection.execute(
        "SELECT 1 FROM accounting_periods WHERE NOT (ends_on < ? OR starts_on > ?)",
        (starts_on, ends_on),
    ).fetchone():
        raise LedgerError("overlapping accounting period")
    with connection:
        cursor = connection.execute(
            "INSERT INTO accounting_periods(starts_on,ends_on) VALUES (?,?)",
            (starts_on, ends_on),
        )
    return int(cursor.lastrowid)


def close_period(connection: sqlite3.Connection, period_id: int) -> None:
    with connection:
        if connection.execute(
            "UPDATE accounting_periods SET is_closed=1 WHERE id=? AND is_closed=0",
            (period_id,),
        ).rowcount != 1:
            raise LedgerError("period not open")


def post_journal(
    connection: sqlite3.Connection,
    posted_on: str,
    reference: str,
    description: str,
    lines: Iterable[Posting],
    reversal_of: int | None = None,
) -> int:
    day = date.fromisoformat(posted_on).isoformat()
    entries = tuple(lines)
    if len(entries) < 2:
        raise LedgerError("journal needs at least two lines")
    if not reference.strip() or not description.strip():
        raise LedgerError("reference and description required")
    for entry in entries:
        if (not isinstance(entry.debit_minor, int) or isinstance(entry.debit_minor, bool)
            or not isinstance(entry.credit_minor, int) or isinstance(entry.credit_minor, bool)
            or entry.debit_minor < 0 or entry.credit_minor < 0
            or (entry.debit_minor > 0) == (entry.credit_minor > 0)
            or not entry.division.strip()):
            raise LedgerError("each line must contain exactly one positive debit or credit")
    if sum(line.debit_minor for line in entries) != sum(line.credit_minor for line in entries):
        raise LedgerError("journal debits and credits do not balance")

    # BEGIN IMMEDIATE serializes writers so period closing and posting cannot race.
    connection.execute("BEGIN IMMEDIATE")
    try:
        periods = connection.execute(
            "SELECT id FROM accounting_periods WHERE starts_on<=? AND ends_on>=? AND is_closed=0",
            (day, day),
        ).fetchall()
        if len(periods) != 1:
            raise LedgerError("posting date requires exactly one open accounting period")
        if reversal_of is not None:
            original = connection.execute("SELECT id FROM journals WHERE id=?", (reversal_of,)).fetchone()
            if original is None:
                raise LedgerError("original journal does not exist")
        for entry in entries:
            if connection.execute(
                "SELECT 1 FROM accounts WHERE code=? AND enabled=1", (entry.account_code,)
            ).fetchone() is None:
                raise LedgerError(f"unknown or disabled account: {entry.account_code}")
        cursor = connection.execute(
            "INSERT INTO journals(posted_on,period_id,reference,description,reversal_of)"
            " VALUES (?,?,?,?,?)",
            (day, periods[0][0], reference, description, reversal_of),
        )
        journal_id = int(cursor.lastrowid)
        connection.executemany(
            "INSERT INTO journal_lines(journal_id,account_code,division,debit_minor,credit_minor)"
            " VALUES (?,?,?,?,?)",
            [(journal_id, e.account_code, e.division, e.debit_minor, e.credit_minor) for e in entries],
        )
        connection.commit()
        return journal_id
    except Exception:
        connection.rollback()
        raise


def reverse_journal(connection: sqlite3.Connection, original_id: int, posted_on: str, reference: str) -> int:
    original = connection.execute("SELECT description FROM journals WHERE id=?", (original_id,)).fetchone()
    if original is None:
        raise LedgerError("original journal not found")
    entries = connection.execute(
        "SELECT account_code,division,debit_minor,credit_minor FROM journal_lines WHERE journal_id=? ORDER BY id",
        (original_id,),
    ).fetchall()
    return post_journal(
        connection, posted_on, reference, f"Reversal of journal {original_id}: {original[0]}",
        [Posting(code, credit, debit, division) for code, division, debit, credit in entries],
        reversal_of=original_id,
    )


def trial_balance(connection: sqlite3.Connection) -> list[tuple[str, str, int, int]]:
    """Return account code, name, debit total, credit total (minor units)."""
    return [
        (code, name, max(net, 0), max(-net, 0))
        for code, name, net in connection.execute(
            "SELECT a.code,a.name,COALESCE(SUM(l.debit_minor-l.credit_minor),0) "
            "FROM accounts a LEFT JOIN journal_lines l ON l.account_code=a.code "
            "GROUP BY a.code,a.name ORDER BY a.code"
        )
    ]
