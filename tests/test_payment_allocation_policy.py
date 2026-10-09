import pathlib
import unittest
from api.payment_allocation_policy import validate_allocation, AllocationError
ROOT=pathlib.Path(__file__).resolve().parents[1]
OK=dict(payment_status="verified",payment_minor=15000,previously_allocated_minor=4000,
        proposed_minor=6000,invoice_status="issued",invoice_total_minor=12000,
        invoice_allocated_minor=2000,same_company=True,same_client=True)
class PaymentReconciliationFoundationTests(unittest.TestCase):
 def test_exact_balances(self):
  self.assertEqual(validate_allocation(**OK),(5000,4000))
 def test_invalid_cross_tenant_duplicate_or_excessive_allocations(self):
  for change in ({"same_company":False},{"same_client":False},{"payment_status":"pending"},
   {"payment_status":"reversed"},{"invoice_status":"draft"},{"proposed_minor":11001},
   {"proposed_minor":0},{"proposed_minor":-1},{"invoice_allocated_minor":10000},
   {"proposed_minor":1.5}):
   with self.subTest(change=change),self.assertRaises(AllocationError):
    validate_allocation(**{**OK,**change})
 def test_payment_schema_company_and_invoice_constraints(self):
  s=(ROOT/"db/migrations/011_payments_reconciliation.sql").read_text()
  for required in ("FOREIGN KEY(company_id,payment_id) REFERENCES cb.client_payments(company_id,id)",
                   "FOREIGN KEY(company_id,invoice_id) REFERENCES cb.invoices(company_id,id)",
                   "UNIQUE(company_id,payment_reference)","FORCE ROW LEVEL SECURITY",
                   "payment_reconciliation_events"):
   self.assertIn(required,s)
if __name__=="__main__":unittest.main()
