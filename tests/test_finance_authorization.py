import unittest
from uuid import UUID
from fastapi import HTTPException
from api.finance_authorization import require_company_membership

COMPANY=UUID("11111111-1111-4111-8111-111111111111")
USER=UUID("22222222-2222-4222-8222-222222222222")

class FakeConn:
 def __init__(self, allowed):
  self.allowed=allowed
  self.calls=[]
 def execute(self,sql,params):
  self.calls.append((sql,params))
  return self
 def fetchone(self):
  return (1,) if self.allowed else None

class FinanceAuthorizationTests(unittest.TestCase):
 def test_explicit_membership_accepted(self):
  conn=FakeConn(True)
  require_company_membership(conn,company_id=COMPANY,user_id=USER)
  self.assertEqual(conn.calls[0][1],(str(COMPANY),))
  self.assertEqual(conn.calls[1][1],(str(USER),))
  self.assertEqual(conn.calls[2][1],(COMPANY,USER))
 def test_missing_membership_forbidden(self):
  conn=FakeConn(False)
  with self.assertRaises(HTTPException) as error:
   require_company_membership(conn,company_id=COMPANY,user_id=USER)
  self.assertEqual(error.exception.status_code,403)
 def test_context_is_transaction_local(self):
  conn=FakeConn(True)
  require_company_membership(conn,company_id=COMPANY,user_id=USER)
  self.assertTrue(all("true" in query.lower() for query,_ in conn.calls[:2]))
if __name__=="__main__":unittest.main()
