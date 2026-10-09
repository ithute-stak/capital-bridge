import unittest
from datetime import datetime,timedelta,timezone
from api.oidc_login import LoginTransaction
from api.oidc_transaction_store import digest,store,consume,new_binding,LOGIN_MAX_AGE

class Cursor:
 def __init__(self,row): self.row=row
 def fetchone(self):return self.row

class DB:
 def __init__(self):self.entries={}
 def execute(self,sql,params):
  if sql.startswith("INSERT"):
   sh,bh,nonce,verifier,created,expires=params
   self.entries[sh]=[bh,nonce,verifier,created,expires,None]
   return Cursor(None)
  if sql.startswith("UPDATE"):
   now,sh,bh,low,high=params
   item=self.entries.get(sh)
   if item and item[0]==bh and item[5] is None and item[3]<=now<item[4]:
    item[5]=now
    return Cursor((item[1],item[2],item[3]))
   return Cursor(None)
  raise AssertionError(sql)

class SingleUseLoginTests(unittest.TestCase):
 def setUp(self):
  self.db=DB()
  self.now=datetime(2026,10,9,tzinfo=timezone.utc)
  self.tx=LoginTransaction("random-state","nonce","pkce-verifier",self.now)
  self.binding=new_binding()
  store(self.db,self.tx,self.binding)
 def test_valid_login_can_be_consumed_only_once(self):
  self.assertEqual(consume(self.db,self.tx.state,self.binding,self.now),self.tx)
  self.assertIsNone(consume(self.db,self.tx.state,self.binding,self.now))
 def test_different_browser_cannot_consume(self):
  self.assertIsNone(consume(self.db,self.tx.state,new_binding(),self.now))
  self.assertEqual(consume(self.db,self.tx.state,self.binding,self.now),self.tx)
 def test_expired_state_rejected(self):
  self.assertIsNone(consume(self.db,self.tx.state,self.binding,self.now+LOGIN_MAX_AGE))
 def test_invalid_state_rejected(self):
  self.assertIsNone(consume(self.db,"",self.binding,self.now))
  self.assertIsNone(consume(self.db,"wrong",self.binding,self.now))
 def test_raw_binding_not_persisted(self):
  entry=next(iter(self.db.entries.values()))
  self.assertNotEqual(entry[0],self.binding)
  self.assertEqual(len(entry[0]),64)
if __name__=="__main__":unittest.main()
