import unittest
from uuid import UUID
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app, authenticate
from api.invoice_creation import InvoiceFromQuotation

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
QUOTATION=UUID("33333333-3333-4333-8333-333333333333")
USER=UUID("22222222-2222-4222-8222-222222222222")
PAYLOAD={"quotation_id":str(QUOTATION),"invoice_number":"CB-INV-001",
         "issued_on":"2026-10-09","due_on":"2026-11-09"}

class InvoiceCreationTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.url=f"/api/v1/companies/{COMPANY}/invoices/from-quotation"
 def tearDown(self):
  app.dependency_overrides.clear()
 def test_anonymous_invoice_denied(self):
  self.assertEqual(self.http.post(self.url,json=PAYLOAD).status_code,401)
 def test_browser_cannot_set_invoice_amounts_or_approval(self):
  for field in ("client_id","subtotal_minor","tax_minor","total_minor","status","company_id"):
   with self.subTest(field=field),self.assertRaises(ValueError):
    InvoiceFromQuotation.model_validate({**PAYLOAD,field:999})
 def test_date_validation(self):
  with self.assertRaises(ValueError):
   InvoiceFromQuotation.model_validate({**PAYLOAD,"due_on":"2026-01-01"})
 def test_auditor_cannot_create_invoice(self):
  app.dependency_overrides[authenticate]=lambda: USER
  class Cursor:
   def fetchone(self):return {"role":"auditor"}
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor()
    raise AssertionError("No quotation or invoice SQL after auditor denial")
  with patch("api.invoice_creation.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.invoice_creation.psycopg.connect",return_value=DB()),patch(
   "api.invoice_creation.validate_company"):
   self.assertEqual(self.http.post(self.url,json=PAYLOAD).status_code,403)
if __name__=="__main__": unittest.main()
