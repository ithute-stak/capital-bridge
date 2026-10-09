import unittest
from uuid import UUID
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app,authenticate
from api.bank_import import BankImportRequest

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
USER=UUID("22222222-2222-4222-8222-222222222222")
ROW={"account_reference":"CB-BANK-01","transaction_reference":"BANK-00001",
     "transaction_date":"2026-10-09","description":"Client EFT",
     "amount_minor":16000,"currency":"LSL"}

class BankImportTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.path=f"/api/v1/companies/{COMPANY}/bank/statement-imports"
 def tearDown(self):app.dependency_overrides.clear()
 def test_anonymous_denied(self):
  self.assertEqual(self.http.post(self.path,json={"rows":[ROW]}).status_code,401)
 def test_spoofed_company_match_and_status_denied(self):
  for field in ("company_id","matched_payment_id","status","verified"):
   with self.subTest(field=field),self.assertRaises(ValueError):
    BankImportRequest.model_validate({"rows":[{**ROW,field:"forged"}]})
 def test_zero_amount_rejected(self):
  with self.assertRaises(ValueError):
   BankImportRequest.model_validate({"rows":[{**ROW,"amount_minor":0}]})
 def test_auditor_denied_before_import(self):
  app.dependency_overrides[authenticate]=lambda:USER
  class Cursor:
   def fetchone(self):return {"role":"auditor"}
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor()
    raise AssertionError("Auditor cannot import bank data")
  with patch("api.bank_import.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.bank_import.psycopg.connect",return_value=DB()),patch(
   "api.bank_import.validate_company"):
   self.assertEqual(self.http.post(self.path,json={"rows":[ROW]}).status_code,403)
if __name__=="__main__": unittest.main()
