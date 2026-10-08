import sqlite3
import unittest
from accounting.ledger import LedgerError, add_account, initialise, open_period, trial_balance
from accounting.billing import initialise_billing, outstanding_minor
from accounting.quotations import (
    Quotation, initialise_quotations, create_quotation, transition,
    convert_to_invoice, quotation_summary
)

class QuotationTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:",isolation_level=None)
        initialise(self.db)
        initialise_billing(self.db)
        initialise_quotations(self.db)
        for code,name,kind in [
            ("1100","AR","asset"),("4000","Revenue","revenue"),("2200","Tax","liability")
        ]:
            add_account(self.db,code,name,kind)
        open_period(self.db,"2026-01-01","2026-12-31")

    def tearDown(self):
        self.db.close()

    def quote(self):
        return create_quotation(self.db,Quotation(
            "Q-001","C-001","immigration","Visa assessment",10000,1500,
            "2026-10-08","2026-10-31"))

    def accept(self, q):
        transition(self.db,q,"approve","2026-10-08")
        transition(self.db,q,"accept","2026-10-09")

    def test_create_and_approve_does_not_post_financial_entry(self):
        q=self.quote()
        transition(self.db,q,"approve","2026-10-08")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM journals").fetchone()[0],0)
        self.assertEqual(quotation_summary(self.db),[("approved",1,11500)])

    def test_convert_accepted_quote_to_invoice(self):
        q=self.quote()
        self.accept(q)
        invoice_id=convert_to_invoice(self.db,q,"INV-001","2026-10-10","2026-10-24",
                                      "1100","4000","2200")
        self.assertEqual(outstanding_minor(self.db,invoice_id),11500)
        self.assertEqual(quotation_summary(self.db),[("invoiced",1,11500)])
        balances={c:(d,cr) for c,_,d,cr in trial_balance(self.db)}
        self.assertEqual(balances["1100"],(11500,0))
        self.assertEqual(balances["4000"],(0,10000))
        self.assertEqual(balances["2200"],(0,1500))

    def test_conversion_only_once(self):
        q=self.quote()
        self.accept(q)
        convert_to_invoice(self.db,q,"INV-001","2026-10-10","2026-10-24","1100","4000","2200")
        with self.assertRaises(LedgerError):
            convert_to_invoice(self.db,q,"INV-002","2026-10-10","2026-10-24","1100","4000","2200")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM invoices").fetchone()[0],1)

    def test_reject_or_expire_cannot_convert(self):
        q=self.quote()
        transition(self.db,q,"approve","2026-10-08")
        transition(self.db,q,"reject","2026-10-09")
        with self.assertRaises(LedgerError):
            convert_to_invoice(self.db,q,"INV-001","2026-10-10","2026-10-24","1100","4000","2200")

    def test_failed_invoice_conversion_rolls_back(self):
        q=self.quote()
        self.accept(q)
        with self.assertRaises(LedgerError):
            convert_to_invoice(self.db,q,"INV-001","2026-10-10","2026-10-24","1100","4000")
        self.assertEqual(self.db.execute("SELECT status FROM quotations WHERE id=?",(q,)).fetchone()[0],"accepted")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM invoices").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM journals").fetchone()[0],0)

    def test_approved_financial_terms_locked(self):
        q=self.quote()
        transition(self.db,q,"approve","2026-10-08")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE quotations SET net_minor=1 WHERE id=?",(q,))

    def test_expired_quote_cannot_be_accepted(self):
        q=self.quote()
        transition(self.db,q,"approve","2026-10-08")
        with self.assertRaises(LedgerError):
            transition(self.db,q,"accept","2026-11-01")

if __name__=="__main__":
    unittest.main()
