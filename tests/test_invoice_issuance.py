import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app,authenticate
from api.invoice_issuance import IssueInvoice

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
INVOICE=UUID("33333333-3333-4333-8333-333333333333")
USER=UUID("22222222-2222-4222-8222-222222222222")
DATA={"period_id":"44444444-4444-4444-8444-444444444444",
      "receivable_account":"1100","revenue_account":"4000",
      "tax_account":"2100","division":"consultancy"}

class InvoiceIssuanceTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.url=f"/api/v1/companies/{COMPANY}/invoices/{INVOICE}/issue"
 def tearDown(self):app.dependency_overrides.clear()
 def test_anonymous_denied(self):
  self.assertEqual(self.http.post(self.url,json=DATA).status_code,401)
 def test_payload_cannot_override_amount_status_or_subject(self):
  for key in ("status","total_minor","user_id","company_id","journal_id"):
   with self.subTest(key=key),self.assertRaises(ValueError):
    IssueInvoice.model_validate({**DATA,key:"spoof"})
 def test_invalid_or_duplicate_accounts_rejected_before_journal_writes(self):
  app.dependency_overrides[authenticate]=lambda: USER
  class Cursor:
   def __init__(self,row):self.row=row
   def fetchone(self):return self.row
   def fetchall(self):return self.row
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor({"role":"accountant"})
    if "FROM cb.invoices" in sql:return Cursor({"status":"draft","issued_on":"2026-10-09","subtotal_minor":1000,"tax_minor":0})
    if "FROM cb.periods" in sql:return Cursor(None)
    if "COUNT(*)" in sql:return Cursor({"n":1,"subtotal":1000})
    raise AssertionError("No journal writes allowed")
  with patch("api.invoice_issuance.config",return_value=("i","a","j","dsn")),patch(
   "api.invoice_issuance.psycopg.connect",return_value=DB()),patch(
   "api.invoice_issuance.validate_company"):
   result=self.http.post(self.url,json={**DATA,"revenue_account":"1100"})
  self.assertEqual(result.status_code,409)
if __name__=="__main__":unittest.main()
