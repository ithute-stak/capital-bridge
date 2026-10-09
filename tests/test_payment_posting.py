import unittest
from uuid import UUID
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app,authenticate
from api.payment_posting import PostPayment

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
PAYMENT=UUID("33333333-3333-4333-8333-333333333333")
USER=UUID("22222222-2222-4222-8222-222222222222")
DATA={"period_id":"44444444-4444-4444-8444-444444444444",
      "deposit_account":"1000","receivable_account":"1100","division":"consultancy"}

class PaymentPostingTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.path=f"/api/v1/companies/{COMPANY}/payments/{PAYMENT}/post"
 def tearDown(self):
  app.dependency_overrides.clear()
 def test_anonymous_denied(self):
  self.assertEqual(self.http.post(self.path,json=DATA).status_code,401)
 def test_no_browser_amount_override(self):
  for field in ("amount_minor","status","company_id","actor_id"):
   with self.subTest(field=field),self.assertRaises(ValueError):
    PostPayment.model_validate({**DATA,field:"spoof"})
 def test_auditor_denied_before_journal_creation(self):
  app.dependency_overrides[authenticate]=lambda:USER
  class Cursor:
   def fetchone(self):return {"role":"auditor"}
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor()
    raise AssertionError("Unauthorized user cannot read or post payment")
  with patch("api.payment_posting.config",return_value=("issuer","aud","keys","dsn")),patch(
   "api.payment_posting.psycopg.connect",return_value=DB()),patch(
   "api.payment_posting.validate_company"):
   self.assertEqual(self.http.post(self.path,json=DATA).status_code,403)
if __name__=="__main__":unittest.main()
