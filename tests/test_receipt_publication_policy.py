import pathlib
import unittest
from api.receipt_publication_policy import ReceiptEvidence,ReceiptPublicationError,validate_receipt_evidence
ROOT=pathlib.Path(__file__).resolve().parents[1]
GOOD=dict(payment_minor=12000,receipt_minor=12000,payment_status="verified",
 journal_status="posted",journal_company_matches=True,payment_company_matches=True,actor_role="accountant")
class ReceiptEvidenceTests(unittest.TestCase):
 def test_verified_posted_payment_eligible(self):
  self.assertIsNone(validate_receipt_evidence(ReceiptEvidence(**GOOD)))
 def test_reject_unverified_unposted_cross_company_or_mismatched_receipts(self):
  for bad in ({"payment_status":"pending"},{"payment_status":"reversed"},
   {"journal_status":"draft"},{"journal_company_matches":False},
   {"payment_company_matches":False},{"actor_role":"finance_clerk"},
   {"receipt_minor":12001},{"receipt_minor":0}):
   with self.subTest(bad=bad),self.assertRaises(ReceiptPublicationError):
    validate_receipt_evidence(ReceiptEvidence(**{**GOOD,**bad}))
 def test_database_isolation_and_unique_receipts(self):
  sql=(ROOT/"db/migrations/012_payment_receipts.sql").read_text()
  for required in ("UNIQUE(company_id,payment_id)","UNIQUE(company_id,receipt_number)",
    "FOREIGN KEY(company_id,payment_id) REFERENCES cb.client_payments(company_id,id)",
    "FOREIGN KEY(journal_id,company_id) REFERENCES cb.journals(id,company_id)",
    "FORCE ROW LEVEL SECURITY"):
   self.assertIn(required,sql)
if __name__=="__main__": unittest.main()
