import unittest
from uuid import UUID
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app,authenticate

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
QUOTATION=UUID("33333333-3333-4333-8333-333333333333")
USER=UUID("22222222-2222-4222-8222-222222222222")

class TransitionTests(unittest.TestCase):
 def setUp(self):
  self.http=TestClient(app)
  self.url=f"/api/v1/companies/{COMPANY}/quotations/{QUOTATION}/transition"
 def tearDown(self):
  app.dependency_overrides.clear()
 def test_anonymous_transition_denied(self):
  self.assertEqual(self.http.post(self.url,json={"target_status":"approved"}).status_code,401)
 def test_reject_client_submitted_actor_or_company(self):
  for field in ("actor_user_id","company_id","previous_status"):
   result=self.http.post(self.url,json={"target_status":"approved",field:"spoof"})
   self.assertEqual(result.status_code,401)
 def test_company_denied_before_database_read(self):
  from fastapi import HTTPException
  app.dependency_overrides[authenticate]=lambda: USER
  class DB:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,*args):raise AssertionError("Database query before company verification")
  with patch("api.quotation_transitions.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.quotation_transitions.psycopg.connect",return_value=DB()),patch(
   "api.quotation_transitions.validate_company",side_effect=HTTPException(status_code=403)):
   result=self.http.post(self.url,json={"target_status":"approved"})
  self.assertEqual(result.status_code,403)
 def test_auditor_cannot_approve_or_generate_event(self):
  app.dependency_overrides[authenticate]=lambda: USER
  class Cursor:
   def __init__(self,row):self.row=row
   def fetchone(self):return self.row
  class DB:
   def __init__(self):self.sql=[]
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def transaction(self):return self
   def execute(self,sql,args):
    self.sql.append(sql)
    if "SELECT role" in sql:return Cursor({"role":"auditor"})
    if "FROM cb.quotations" in sql:return Cursor({"status":"draft","subtotal_minor":500,"issued_on":"x","valid_until":"y"})
    if "COUNT(*)" in sql:return Cursor({"line_count":1,"calculated_minor":500})
    raise AssertionError("Unauthorised mutation")
  db=DB()
  with patch("api.quotation_transitions.config",return_value=("issuer","aud","jwks","dsn")),patch(
   "api.quotation_transitions.psycopg.connect",return_value=db),patch(
   "api.quotation_transitions.validate_company"):
   result=self.http.post(self.url,json={"target_status":"approved"})
  self.assertEqual(result.status_code,409)
  self.assertFalse(any(sql.startswith("UPDATE") or sql.startswith("INSERT") for sql in db.sql))

if __name__=="__main__":unittest.main()
