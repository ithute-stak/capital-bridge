import sqlite3
import unittest

from accounting.ledger import LedgerError, add_account, initialise, open_period, trial_balance
from accounting.billing import Invoice, initialise_billing, issue_invoice, record_receipt, outstanding_minor


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:",isolation_level=None)
        initialise(self.db)
        initialise_billing(self.db)
        for code,name,kind in [("1100","Receivables","asset"),("1000","Bank","asset"),
                               ("4000","Service income","revenue"),("2200","Tax payable","liability")]:
            add_account(self.db,code,name,kind)
        open_period(self.db,"2026-01-01","2026-12-31")

    def invoice(self, number="CB-001",tax=0):
        return Invoice(number,"CLIENT-1","immigration","Visa consultation",10000,tax,
                       "2026-10-08","2026-10-22")

    def test_invoice_posts_receivable_and_revenue(self):
        iid=issue_invoice(self.db,self.invoice(),"1100","4000")
        self.assertEqual(outstanding_minor(self.db,iid),10000)
        self.assertEqual(sum(x[2] for x in trial_balance(self.db)),10000)
        self.assertEqual(sum(x[3] for x in trial_balance(self.db)),10000)

    def test_partial_and_final_receipts(self):
        iid=issue_invoice(self.db,self.invoice(),"1100","4000")
        record_receipt(self.db,iid,"RC-1",3500,"2026-10-09","1000","1100")
        self.assertEqual(outstanding_minor(self.db,iid),6500)
        record_receipt(self.db,iid,"RC-2",6500,"2026-10-10","1000","1100")
        self.assertEqual(outstanding_minor(self.db,iid),0)
        with self.assertRaises(LedgerError):
            record_receipt(self.db,iid,"RC-3",1,"2026-10-10","1000","1100")

    def test_tax_separately_posted(self):
        iid=issue_invoice(self.db,self.invoice(tax=1500),"1100","4000","2200")
        self.assertEqual(outstanding_minor(self.db,iid),11500)
        b={code:(d,c) for code,_,d,c in trial_balance(self.db)}
        self.assertEqual(b["2200"],(0,1500))
        self.assertEqual(b["1100"],(11500,0))

    def test_duplicate_invoice_rolls_back_journal(self):
        issue_invoice(self.db,self.invoice(),"1100","4000")
        with self.assertRaises(sqlite3.IntegrityError):
            issue_invoice(self.db,self.invoice(),"1100","4000")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM journals").fetchone()[0],1)

    def test_missing_account_does_not_create_invoice(self):
        with self.assertRaises(LedgerError):
            issue_invoice(self.db,self.invoice(),"missing","4000")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM invoices").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM journals").fetchone()[0],0)

    def test_tax_requires_payable_account(self):
        with self.assertRaises(LedgerError):
            issue_invoice(self.db,self.invoice(tax=1500),"1100","4000")

    def test_invalid_dates_and_amounts(self):
        with self.assertRaises(LedgerError):
            issue_invoice(self.db,Invoice("x","c","d","s",0,0,"2026-10-08","2026-10-09"),"1100","4000")
        with self.assertRaises(LedgerError):
            issue_invoice(self.db,Invoice("x","c","d","s",1,0,"2026-10-09","2026-10-08"),"1100","4000")


if __name__ == "__main__":
    unittest.main()
