import unittest
from uuid import UUID
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app,authenticate
from api.receipt_issuance import IssueReceipt

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
USER=UUID("22222222-2222-4222-8222-222222222222")
PAYMENT=UUID("33333333-3333-4333-8333-333333333333")
JOURNAL=UUID("44444444-4444-4444-8444-444444444444")
DATA={"payment_id":str(PAYMENT),"journal_id":str(JOURNAL),"receipt_number":"CB-RCT-01"}

class ReceiptIssuanceTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app);self.url=f"/api/v1/companies/{COMPANY}/receipts"
 def tearDown(self):app.dependency_overrides.clear()
 def test_anonymous_denied(self):
  self.assertEqual(self.http.post(self.url,json=DATA).status_code,401)
 def test_forged_amount_actor_company_rejected(self):
  for field in ("amount_minor","issued_by","company_id","status"):
   with self.subTest(field=field),self.assertRaises(ValueError):
    IssueReceipt.model_validate({**DATA,field:"spoof"})
 def test_mismatched_payment_journal_denied_before_insert(self):
  app.dependency_overrides[authenticate]=lambda:USER
  class Cursor:
   def __init__(self,row):self.row=row
   def fetchone(self):return self.row
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor({"role":"accountant"})
    if "FROM cb.client_payments" in sql:return Cursor({"id":PAYMENT,"amount_minor":1000,"status":"verified"})
    if "FROM cb.journals" in sql:return Cursor({"id":JOURNAL,"status":"posted","reference":"UNRELATED"})
    raise AssertionError("Unmatched payment cannot create receipt")
  with patch("api.receipt_issuance.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.receipt_issuance.psycopg.connect",return_value=DB()),patch(
   "api.receipt_issuance.validate_company"):
   result=self.http.post(self.url,json=DATA)
  self.assertEqual(result.status_code,409)
if __name__=="__main__":unittest.main()
