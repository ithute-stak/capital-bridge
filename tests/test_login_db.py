import unittest
from unittest.mock import Mock,patch
from api.login_db import LoginDatabaseSettings,authentication_connection

class ConnectionBoundaryTests(unittest.TestCase):
 def test_missing_database_credentials_fail_closed(self):
  with patch.dict("os.environ",{},clear=True):
   with self.assertRaises(RuntimeError): LoginDatabaseSettings.from_environment()
 def test_shared_database_credentials_denied(self):
  values={"CB_OIDC_TRANSACTION_DATABASE_URL":"postgres://same",
          "CB_IDENTITY_DATABASE_URL":"postgres://same",
          "CB_SESSION_DATABASE_URL":"postgres://other"}
  with patch.dict("os.environ",values,clear=True):
   with self.assertRaises(RuntimeError): LoginDatabaseSettings.from_environment()
 def test_independent_credentials_accepted(self):
  values={"CB_OIDC_TRANSACTION_DATABASE_URL":"postgres://transactions",
          "CB_IDENTITY_DATABASE_URL":"postgres://identities",
          "CB_SESSION_DATABASE_URL":"postgres://sessions"}
  with patch.dict("os.environ",values,clear=True):
   result=LoginDatabaseSettings.from_environment()
  self.assertNotEqual(result.transactions,result.sessions)
 def test_connection_commit_on_success(self):
  conn=Mock()
  conn.__enter__=Mock(return_value=conn)
  conn.__exit__=Mock(return_value=False)
  with patch("api.login_db.psycopg.connect",return_value=conn):
   with authentication_connection("postgres://test") as db:
    self.assertIs(db,conn)
  conn.commit.assert_called_once()
  conn.rollback.assert_not_called()
 def test_connection_rollback_on_failure(self):
  conn=Mock()
  conn.__enter__=Mock(return_value=conn)
  conn.__exit__=Mock(return_value=False)
  with patch("api.login_db.psycopg.connect",return_value=conn):
   with self.assertRaises(ValueError):
    with authentication_connection("postgres://test"):
     raise ValueError("failure")
  conn.rollback.assert_called_once()
  conn.commit.assert_not_called()

if __name__=="__main__":unittest.main()
