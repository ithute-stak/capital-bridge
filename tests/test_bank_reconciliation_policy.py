import pathlib
import unittest
from datetime import date
from api.bank_reconciliation_policy import BankMatchEvidence,BankMatchError,validate_bank_payment_match
ROOT=pathlib.Path(__file__).resolve().parents[1]
GOOD=dict(bank_amount_minor=15000,payment_amount_minor=15000,payment_status="verified",
 bank_currency="LSL",payment_currency="LSL",company_matches=True,
 payment_reference="CB-2026-001",bank_description="EFT CB-2026-001",
 bank_date=date(2026,10,10),payment_date=date(2026,10,9),actor_role="accountant")
class BankReconciliationTests(unittest.TestCase):
 def test_valid_bank_evidence(self):
  self.assertIsNone(validate_bank_payment_match(BankMatchEvidence(**GOOD)))
 def test_invalid_matches_are_rejected(self):
  for change in ({"company_matches":False},{"payment_status":"pending"},
   {"bank_amount_minor":14999},{"bank_amount_minor":-15000},
   {"bank_currency":"USD"},{"bank_description":"UNKNOWN"},
   {"bank_date":date(2026,11,10)},{"actor_role":"auditor"}):
   with self.subTest(change=change),self.assertRaises(BankMatchError):
    validate_bank_payment_match(BankMatchEvidence(**{**GOOD,**change}))
 def test_schema_uniqueness_and_rls(self):
  sql=(ROOT/"db/migrations/013_bank_reconciliation.sql").read_text()
  for constraint in ("UNIQUE(company_id,bank_account_ref,external_transaction_id)",
    "UNIQUE(company_id,bank_transaction_id)","UNIQUE(company_id,payment_id)",
    "FORCE ROW LEVEL SECURITY","FOREIGN KEY(company_id,payment_id) REFERENCES cb.client_payments(company_id,id)"):
   self.assertIn(constraint,sql)
if __name__=="__main__":unittest.main()
