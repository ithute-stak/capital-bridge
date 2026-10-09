import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app,authenticate
from api.payment_allocations import AllocatePayment

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
PAYMENT=UUID("33333333-3333-4333-8333-333333333333")
USER=UUID("22222222-2222-4222-8222-222222222222")
INVOICE=UUID("44444444-4444-4444-8444-444444444444")
DATA={"invoice_id":str(INVOICE),"amount_minor":1500}

class PaymentAllocationAPITests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.path=f"/api/v1/companies/{COMPANY}/payments/{PAYMENT}/allocate"
 def tearDown(self):app.dependency_overrides.clear()
 def test_anonymous_denied(self):
  self.assertEqual(self.http.post(self.path,json=DATA).status_code,401)
 def test_forged_ownership_and_status_fields_forbidden(self):
  for key in ("company_id","payment_status","invoice_status","client_id","outstanding_minor"):
   with self.subTest(key=key),self.assertRaises(ValueError):
    AllocatePayment.model_validate({**DATA,key:"forged"})
 def test_negative_amount_denied(self):
  self.assertEqual(self.http.post(self.path,json={**DATA,"amount_minor":-1}).status_code,401)
 def test_auditor_denied_before_allocation(self):
  app.dependency_overrides[authenticate]=lambda:USER
  class Cursor:
   def fetchone(self):return {"role":"auditor"}
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor()
    raise AssertionError("No payment SQL permitted for auditor")
  with patch("api.payment_allocations.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.payment_allocations.psycopg.connect",return_value=DB()),patch(
   "api.payment_allocations.validate_company"):
   response=self.http.post(self.path,json=DATA)
  self.assertEqual(response.status_code,403)

if __name__=="__main__":unittest.main()
