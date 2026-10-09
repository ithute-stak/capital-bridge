import unittest
from datetime import datetime,timedelta,timezone
from uuid import UUID
from api.sessions import (
 SESSION_COOKIE,SESSION_TTL,create_session,session_key,session_active,
 cookie_options,check_same_origin,
)

class SessionSecurityTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,10,9,tzinfo=timezone.utc)
  self.subject=UUID("22222222-2222-4222-8222-222222222222")

 def test_random_cookie_not_stored_in_clear(self):
  cookie,key,s=create_session(self.subject,self.now)
  self.assertNotEqual(cookie,key)
  self.assertEqual(session_key(cookie),key)
  other,other_key,_=create_session(self.subject,self.now)
  self.assertNotEqual(cookie,other)
  self.assertNotEqual(key,other_key)
  self.assertEqual(s.subject,self.subject)

 def test_expiration_is_enforced(self):
  _,_,s=create_session(self.subject,self.now)
  self.assertTrue(session_active(s,self.now))
  self.assertFalse(session_active(s,self.now+SESSION_TTL))
  self.assertFalse(session_active(s,self.now-timedelta(seconds=1)))

 def test_cookie_security_flags(self):
  opts=cookie_options()
  self.assertTrue(opts["secure"])
  self.assertTrue(opts["httponly"])
  self.assertEqual(opts["samesite"],"strict")
  self.assertEqual(opts["path"],"/")
  self.assertTrue(SESSION_COOKIE.startswith("__Host-"))

 def test_mutation_origin_requires_https_same_origin(self):
  trusted="https://capitalbridge.example"
  self.assertTrue(check_same_origin(trusted,trusted))
  for origin in (None,"http://capitalbridge.example","https://evil.example",
                 "https://capitalbridge.example.evil.example","https://capitalbridge.example?test=1"):
   self.assertFalse(check_same_origin(origin,trusted))

if __name__=="__main__":
 unittest.main()
