import unittest
from uuid import UUID
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app,authenticate
from api.bank_manual_match import MatchBankTransaction

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
TRANSACTION=UUID("33333333-3333-4333-8333-333333333333")
PAYMENT=UUID("44444444-4444-4444-8444-444444444444")
USER=UUID("22222222-2222-4222-8222-222222222222")

class ManualBankMatchTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.path=f"/api/v1/companies/{COMPANY}/bank/transactions/{TRANSACTION}/match"
 def tearDown(self):app.dependency_overrides.clear()
 def test_unauthenticated_denied(self):
  self.assertEqual(self.http.post(self.path,json={"payment_id":str(PAYMENT)}).status_code,401)
 def test_browser_cannot_set_actor_amount_or_match_status(self):
  for field in ("matched_by","amount_minor","company_id","status"):
   with self.subTest(field=field),self.assertRaises(ValueError):
    MatchBankTransaction.model_validate({"payment_id":str(PAYMENT),field:"spoof"})
 def test_auditor_denied_before_bank_queries(self):
  app.dependency_overrides[authenticate]=lambda:USER
  class Cursor:
   def fetchone(self):return {"role":"auditor"}
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    if "SELECT role" in sql:return Cursor()
    raise AssertionError("No transaction matching allowed")
  with patch("api.bank_manual_match.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.bank_manual_match.psycopg.connect",return_value=DB()),patch(
   "api.bank_manual_match.validate_company"):
   response=self.http.post(self.path,json={"payment_id":str(PAYMENT)})
  self.assertEqual(response.status_code,403)
if __name__=="__main__":unittest.main()
