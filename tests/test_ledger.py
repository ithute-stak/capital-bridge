import sqlite3
import unittest

from accounting.ledger import (
    LedgerError, Posting, add_account, close_period, initialise,
    open_period, post_journal, reverse_journal, trial_balance,
)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        initialise(self.db)
        add_account(self.db, "1000", "Bank", "asset")
        add_account(self.db, "4000", "Consultancy revenue", "revenue")
        self.period = open_period(self.db, "2026-01-01", "2026-12-31")

    def tearDown(self):
        self.db.close()

    def record(self, ref="CB-1"):
        return post_journal(
            self.db, "2026-10-08", ref, "Client paid",
            [Posting("1000", debit_minor=12500, division="consultancy"),
             Posting("4000", credit_minor=12500, division="consultancy")]
        )

    def test_balanced_posting_and_trial_balance(self):
        self.record()
        balances = {code: (debit, credit) for code, _, debit, credit in trial_balance(self.db)}
        self.assertEqual(balances["1000"], (12500, 0))
        self.assertEqual(balances["4000"], (0, 12500))
        self.assertEqual(sum(v[0] for v in balances.values()), sum(v[1] for v in balances.values()))

    def test_reject_unbalanced_and_preserve_empty_database(self):
        with self.assertRaises(LedgerError):
            post_journal(self.db, "2026-10-08", "bad", "bad",
                         [Posting("1000", debit_minor=12500),
                          Posting("4000", credit_minor=12499)])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM journals").fetchone()[0], 0)

    def test_closed_period_blocks_posting(self):
        close_period(self.db, self.period)
        with self.assertRaises(LedgerError):
            self.record()

    def test_duplicate_source_reference_blocks_second_posting(self):
        self.record()
        with self.assertRaises(sqlite3.IntegrityError):
            self.record()
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM journals").fetchone()[0], 1)

    def test_posted_entries_immutable_and_reversible(self):
        original = self.record()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM journal_lines WHERE journal_id=?", (original,))
        reverse_journal(self.db, original, "2026-10-09", "CB-1-REV")
        self.assertTrue(all((debit, credit) == (0, 0) for _, _, debit, credit in trial_balance(self.db)))
        with self.assertRaises(sqlite3.IntegrityError):
            reverse_journal(self.db, original, "2026-10-09", "CB-1-REV2")

    def test_negative_and_zero_or_double_sided_lines_rejected(self):
        for bad in (Posting("1000", debit_minor=-1),
                    Posting("1000"),
                    Posting("1000", debit_minor=1, credit_minor=1)):
            with self.assertRaises(LedgerError):
                post_journal(self.db, "2026-10-08", "bad", "bad",
                             [bad, Posting("4000", credit_minor=1)])

    def test_overlapping_period_not_allowed(self):
        with self.assertRaises(LedgerError):
            open_period(self.db, "2026-06-01", "2027-01-01")


if __name__ == "__main__":
    unittest.main()
