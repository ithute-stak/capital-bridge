import sqlite3
import unittest
from accounting.ledger import initialise, add_account, open_period
from accounting.billing import initialise_billing, Invoice, issue_invoice, record_receipt
from accounting.quotations import initialise_quotations, Quotation, create_quotation, transition
from accounting.reporting import financial_summary, division_revenue, trial_balance_as_of

class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:", isolation_level=None)
        initialise(self.db)
        initialise_billing(self.db)
        initialise_quotations(self.db)
        for code,name,kind in (("1000","Bank","asset"),("1100","AR","asset"),
                               ("4000","Income","revenue"),("2200","Tax","liability")):
            add_account(self.db,code,name,kind)
        open_period(self.db,"2026-01-01","2026-12-31")

    def tearDown(self):
        self.db.close()

    def test_real_transactions_feed_reporting(self):
        iid=issue_invoice(self.db,Invoice("I1","C1","immigration","Service",10000,1500,
            "2026-10-08","2026-10-20"),"1100","4000","2200")
        record_receipt(self.db,iid,"R1",4000,"2026-10-09","1000","1100")
        q=create_quotation(self.db,Quotation("Q1","C2","consultancy","Advice",5000,0,
            "2026-10-08","2026-10-31"))
        transition(self.db,q,"approve","2026-10-08")
        transition(self.db,q,"accept","2026-10-08")
        s=financial_summary(self.db,"2026-10-01","2026-10-31")
        self.assertEqual((s.invoiced_minor,s.received_minor,s.outstanding_minor,s.quotation_pipeline_minor),
            (11500,4000,7500,5000))
        self.assertEqual(division_revenue(self.db,"2026-10-01","2026-10-31"),
                         [("immigration",10000)])
        self.assertEqual(sum(r[2] for r in trial_balance_as_of(self.db,"2026-10-31")),
                         sum(r[3] for r in trial_balance_as_of(self.db,"2026-10-31")))

    def test_as_of_excludes_future_postings(self):
        issue_invoice(self.db,Invoice("I2","C1","consultancy","Advice",12000,0,
            "2026-10-08","2026-10-20"),"1100","4000")
        before=trial_balance_as_of(self.db,"2026-10-07")
        self.assertTrue(all((d,c)==(0,0) for _,_,d,c in before))
        after=trial_balance_as_of(self.db,"2026-10-08")
        self.assertEqual(sum(d for _,_,d,_ in after),12000)

if __name__=="__main__":
    unittest.main()
