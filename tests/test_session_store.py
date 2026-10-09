import unittest
from datetime import datetime,timedelta,timezone
from uuid import UUID
from unittest.mock import patch

from api.session_store import issue,resolve,revoke,purge_expired
from api.sessions import SESSION_TTL


class FakeCursor:
    def __init__(self, row=None, count=1):
        self.row=row
        self.rowcount=count
    def fetchone(self): return self.row


class FakeDB:
    def __init__(self):
        self.rows={}
    def execute(self, query, params):
        if query.startswith("INSERT"):
            key,subject,created,expires=params
            self.rows[key]=[subject,created,expires,None]
            return FakeCursor()
        if query.startswith("SELECT"):
            key,now=params
            row=self.rows.get(key)
            if row and row[3] is None and row[2]>now:
                return FakeCursor(row[:3])
            return FakeCursor()
        if query.startswith("UPDATE"):
            now,key=params
            row=self.rows.get(key)
            if row and row[3] is None:
                row[3]=now
                return FakeCursor(count=1)
            return FakeCursor(count=0)
        if query.startswith("DELETE"):
            now=params[0]
            keys=[key for key,row in self.rows.items() if row[2]<=now or row[3] is not None]
            for key in keys: del self.rows[key]
            return FakeCursor(count=len(keys))
        raise AssertionError(query)


class SessionStoreTests(unittest.TestCase):
    def setUp(self):
        self.db=FakeDB()
        self.now=datetime(2026,10,9,tzinfo=timezone.utc)
        self.subject=UUID("22222222-2222-4222-8222-222222222222")

    def test_issue_resolve_and_revoke(self):
        token=issue(self.db,self.subject,self.now)
        self.assertEqual(resolve(self.db,token,self.now),self.subject)
        self.assertTrue(revoke(self.db,token,self.now+timedelta(minutes=1)))
        self.assertIsNone(resolve(self.db,token,self.now+timedelta(minutes=2)))
        self.assertFalse(revoke(self.db,token,self.now+timedelta(minutes=2)))

    def test_expiry_and_purge(self):
        token=issue(self.db,self.subject,self.now)
        self.assertIsNone(resolve(self.db,token,self.now+SESSION_TTL))
        self.assertEqual(purge_expired(self.db,self.now+SESSION_TTL),1)

    def test_invalid_identifier_fails_closed(self):
        self.assertIsNone(resolve(self.db,""))
        self.assertFalse(revoke(self.db,""))
        self.assertIsNone(resolve(self.db,"x"*300))

    def test_db_only_stores_hashed_token(self):
        token=issue(self.db,self.subject,self.now)
        self.assertNotIn(token,self.db.rows)
        self.assertEqual(len(next(iter(self.db.rows))),64)

if __name__=="__main__":
    unittest.main()
