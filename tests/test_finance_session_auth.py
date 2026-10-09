import unittest
from unittest.mock import patch, Mock
from contextlib import contextmanager
from uuid import UUID
from fastapi import HTTPException
from api.finance_session_auth import resolve_finance_session
from api.login_db import LoginDatabaseSettings

class FinanceSessionTests(unittest.TestCase):
 def setUp(self):
  self.config=LoginDatabaseSettings("tx-dsn","identity-dsn","session-dsn")
  self.user=UUID("22222222-2222-4222-8222-222222222222")
 def test_missing_cookie_rejected_without_query(self):
  with patch("api.finance_session_auth.authentication_connection") as db:
   with self.assertRaises(HTTPException) as exc:
    resolve_finance_session(None,settings=self.config)
  self.assertEqual(exc.exception.status_code,401)
  db.assert_not_called()
 def test_revoked_session_rejected(self):
  @contextmanager
  def connection(dsn,*,purpose):
   self.assertEqual(dsn,"session-dsn")
   self.assertEqual(purpose,"sessions")
   yield Mock()
  with patch("api.finance_session_auth.authentication_connection",side_effect=connection), \
       patch("api.finance_session_auth.resolve",return_value=None):
   with self.assertRaises(HTTPException) as exc:
    resolve_finance_session("unrecognised-cookie",settings=self.config)
  self.assertEqual(exc.exception.status_code,401)
 def test_valid_session_resolves_server_identity(self):
  @contextmanager
  def connection(dsn,*,purpose):
   self.assertEqual(purpose,"sessions")
   yield Mock()
  with patch("api.finance_session_auth.authentication_connection",side_effect=connection), \
       patch("api.finance_session_auth.resolve",return_value=self.user) as verified:
   actual=resolve_finance_session("opaque-cookie",settings=self.config)
  self.assertEqual(actual,self.user)
  verified.assert_called_once()
if __name__=="__main__":unittest.main()
