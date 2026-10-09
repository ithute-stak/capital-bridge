import unittest
from unittest.mock import patch, MagicMock
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app, authenticate

COMPANY=UUID("22222222-2222-4222-8222-222222222222")
USER=UUID("11111111-1111-4111-8111-111111111111")
class RealtimeEligibilityTests(unittest.TestCase):
 def setUp(self):
  self.client=TestClient(app)
 def tearDown(self):
  app.dependency_overrides.clear()
 def test_anonymous_request_denied_before_db(self):
  with patch("api.realtime_eligibility.psycopg.connect") as connect:
   response=self.client.get(f"/api/v1/companies/{COMPANY}/realtime/eligibility")
  self.assertEqual(response.status_code,401)
  connect.assert_not_called()
 def test_authenticated_membership_validated(self):
  app.dependency_overrides[authenticate]=lambda: USER
  db=MagicMock()
  db.__enter__.return_value=db
  db.transaction.return_value.__enter__.return_value=db
  with patch("api.realtime_eligibility.config",return_value=("issuer","aud","jwks","dsn")),patch(
    "api.realtime_eligibility.psycopg.connect",return_value=db),patch(
    "api.realtime_eligibility.validate_company") as validate:
   response=self.client.get(f"/api/v1/companies/{COMPANY}/realtime/eligibility")
  self.assertEqual(response.status_code,200)
  self.assertFalse(response.json()["websocket_enabled"])
  validate.assert_called_once_with(COMPANY,USER,db)
 def test_forged_company_membership_denied(self):
  from fastapi import HTTPException
  app.dependency_overrides[authenticate]=lambda: USER
  db=MagicMock()
  db.__enter__.return_value=db
  db.transaction.return_value.__enter__.return_value=db
  with patch("api.realtime_eligibility.config",return_value=("issuer","aud","jwks","dsn")),patch(
    "api.realtime_eligibility.psycopg.connect",return_value=db),patch(
    "api.realtime_eligibility.validate_company",side_effect=HTTPException(403,"Company access denied")):
   response=self.client.get(f"/api/v1/companies/{COMPANY}/realtime/eligibility")
  self.assertEqual(response.status_code,403)
if __name__=="__main__":unittest.main()
