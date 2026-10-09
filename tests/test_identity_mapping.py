import unittest
from uuid import UUID
from api.identity_mapping import resolve_registered_user
from api.oidc_verify import TrustedIdentity

class FakeDb:
 def __init__(self,entries):self.entries=entries
 def execute(self,query,parameters):
  self.query=query
  self.parameters=parameters
  return self
 def fetchone(self):
  user=self.entries.get(tuple(self.parameters))
  return (user,) if user else None

class MappingTests(unittest.TestCase):
 def test_known_exact_issuer_and_subject(self):
  user=UUID("22222222-2222-4222-8222-222222222222")
  db=FakeDb({("https://identity.example.test","abc"):user})
  self.assertEqual(resolve_registered_user(db,TrustedIdentity("https://identity.example.test","abc")),user)
  self.assertIn("issuer=%s AND subject=%s",db.query)
 def test_unknown_subject_fails_closed(self):
  db=FakeDb({})
  self.assertIsNone(resolve_registered_user(db,TrustedIdentity("https://identity.example.test","abc")))
 def test_same_subject_different_issuer_denied(self):
  user=UUID("22222222-2222-4222-8222-222222222222")
  db=FakeDb({("https://identity.example.test","abc"):user})
  self.assertIsNone(resolve_registered_user(db,TrustedIdentity("https://other.example.test","abc")))
 def test_bad_identity_is_not_queried(self):
  db=FakeDb({})
  self.assertIsNone(resolve_registered_user(db,TrustedIdentity("http://other.example.test","abc")))
  self.assertFalse(hasattr(db,"query"))

if __name__=="__main__": unittest.main()
