import unittest
from uuid import UUID
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app, authenticate
from api.quotation_create_schema import QuotationCreateInput

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
USER=UUID("22222222-2222-4222-8222-222222222222")
CLIENT=UUID("33333333-3333-4333-8333-333333333333")
PAYLOAD={"client_id":str(CLIENT),"quotation_number":"CB-Q-01","title":"Advisory",
         "issued_on":"2026-10-09","valid_until":"2026-10-31",
         "lines":[{"description":"Consulting","quantity":2,"unit_price_minor":25000}]}

class QuotationCreationTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.url=f"/api/v1/companies/{COMPANY}/quotations"
 def tearDown(self):
  app.dependency_overrides.clear()
 def test_anonymous_denied(self):
  self.assertEqual(self.http.post(self.url,json=PAYLOAD).status_code,401)
 def test_client_cannot_set_totals_or_approval(self):
  for key in ("subtotal_minor","tax_minor","status","company_id","user_id"):
   with self.subTest(key=key),self.assertRaises(ValueError):
    QuotationCreateInput.model_validate({**PAYLOAD,key:123})
 def test_precise_minor_units_and_date_constraints(self):
  self.assertEqual(QuotationCreateInput.model_validate(PAYLOAD).subtotal_minor,50000)
  with self.assertRaises(ValueError):
   QuotationCreateInput.model_validate({**PAYLOAD,"valid_until":"2026-01-01"})
 def test_auditor_forbidden_before_writes(self):
  app.dependency_overrides[authenticate]=lambda: USER
  class Cursor:
   def fetchone(self):return {"role":"auditor"}
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor()
    raise AssertionError("No writes permitted")
  with patch("api.quotation_create.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.quotation_create.psycopg.connect",return_value=DB()),patch(
   "api.quotation_create.validate_company"):
   self.assertEqual(self.http.post(self.url,json=PAYLOAD).status_code,403)

if __name__=="__main__":unittest.main()
