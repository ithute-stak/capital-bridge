import unittest
from unittest.mock import MagicMock,patch
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app,authenticate

COMPANY=UUID("22222222-2222-4222-8222-222222222222")
USER=UUID("11111111-1111-4111-8111-111111111111")
OTHER=UUID("33333333-3333-4333-8333-333333333333")

class NotificationApiTests(unittest.TestCase):
 def setUp(self): self.client=TestClient(app)
 def tearDown(self): app.dependency_overrides.clear()
 def test_anonymous_denied_without_database_access(self):
  with patch("api.realtime_notifications.psycopg.connect") as connect:
   response=self.client.get(f"/api/v1/companies/{COMPANY}/realtime/notifications")
  self.assertEqual(response.status_code,401)
  connect.assert_not_called()
 def test_invalid_company_membership_denied(self):
  from fastapi import HTTPException
  app.dependency_overrides[authenticate]=lambda:USER
  db=MagicMock();db.__enter__.return_value=db;db.transaction.return_value.__enter__.return_value=db
  with patch("api.realtime_notifications.config",return_value=("a","b","c","dsn")),patch(
   "api.realtime_notifications.psycopg.connect",return_value=db),patch(
   "api.realtime_notifications.validate_company",side_effect=HTTPException(403,"denied")):
   response=self.client.get(f"/api/v1/companies/{OTHER}/realtime/notifications")
  self.assertEqual(response.status_code,403)
 def test_success_query_is_tenant_scoped(self):
  app.dependency_overrides[authenticate]=lambda:USER
  db=MagicMock();db.__enter__.return_value=db;db.transaction.return_value.__enter__.return_value=db
  db.execute.return_value.fetchall.return_value=[]
  with patch("api.realtime_notifications.config",return_value=("a","b","c","dsn")),patch(
   "api.realtime_notifications.psycopg.connect",return_value=db),patch(
   "api.realtime_notifications.validate_company") as guard:
   response=self.client.get(f"/api/v1/companies/{COMPANY}/realtime/notifications")
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.json()["notifications"],[])
  guard.assert_called_once_with(COMPANY,USER,db)
  self.assertIn("WHERE company_id=%s",db.execute.call_args.args[0])
 def test_unknown_cursor_rejected(self):
  app.dependency_overrides[authenticate]=lambda:USER
  db=MagicMock();db.__enter__.return_value=db;db.transaction.return_value.__enter__.return_value=db
  db.execute.return_value.fetchone.return_value=None
  with patch("api.realtime_notifications.config",return_value=("a","b","c","dsn")),patch(
   "api.realtime_notifications.psycopg.connect",return_value=db),patch(
   "api.realtime_notifications.validate_company"):
   response=self.client.get(f"/api/v1/companies/{COMPANY}/realtime/notifications?after_id={OTHER}")
  self.assertEqual(response.status_code,400)
if __name__=="__main__":unittest.main()
