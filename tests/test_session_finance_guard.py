import unittest
from contextlib import contextmanager
from unittest.mock import Mock, patch
from uuid import UUID
from fastapi import HTTPException
from api.login_db import LoginDatabaseSettings
from api.session_finance_guard import authorized_finance_session

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
USER=UUID("22222222-2222-4222-8222-222222222222")
SETTINGS=LoginDatabaseSettings("transaction","identity","session")

class SessionFinanceGuardTests(unittest.TestCase):
 def fake_connection(self):
  conn=Mock()
  conn.__enter__=Mock(return_value=conn)
  conn.__exit__=Mock(return_value=False)
  @contextmanager
  def transaction():
   yield
  conn.transaction=transaction
  return conn
 def test_missing_session_never_opens_finance_database(self):
  with patch("api.session_finance_guard.resolve_finance_session",side_effect=HTTPException(status_code=401)), \\
       patch("api.session_finance_guard.psycopg.connect") as connect:
   with self.assertRaises(HTTPException):
    with authorized_finance_session(company_id=COMPANY,cookie=None,session_settings=SETTINGS,finance_dsn="finance"):pass
   connect.assert_not_called()
 def test_company_membership_checked_before_finance_query(self):
  conn=self.fake_connection()
  with patch("api.session_finance_guard.resolve_finance_session",return_value=USER), \\
       patch("api.session_finance_guard.psycopg.connect",return_value=conn), \\
       patch("api.session_finance_guard.require_company_membership") as check:
   with authorized_finance_session(company_id=COMPANY,cookie="opaque",session_settings=SETTINGS,finance_dsn="finance") as db:
    self.assertIs(db,conn)
    check.assert_called_once_with(conn,company_id=COMPANY,user_id=USER)
 def test_unauthorized_company_yields_no_data(self):
  conn=self.fake_connection()
  with patch("api.session_finance_guard.resolve_finance_session",return_value=USER), \\
       patch("api.session_finance_guard.psycopg.connect",return_value=conn), \\
       patch("api.session_finance_guard.require_company_membership",side_effect=HTTPException(status_code=403)):
   with self.assertRaises(HTTPException) as exc:
    with authorized_finance_session(company_id=COMPANY,cookie="opaque",session_settings=SETTINGS,finance_dsn="finance"):
     conn.execute("SELECT protected data")
  self.assertEqual(exc.exception.status_code,403)
  conn.execute.assert_not_called()
if __name__=="__main__":unittest.main()
