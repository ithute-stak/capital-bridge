import unittest
from datetime import datetime,timedelta,timezone
from urllib.parse import urlsplit,parse_qs
from api.oidc_login import begin,verify_callback,challenge

class OidcLoginTests(unittest.TestCase):
 def setUp(self): self.now=datetime(2026,10,9,tzinfo=timezone.utc)
 def start(self): return begin("https://identity.example.test/authorize","cb-public",
    "https://capitalbridge.example/callback",now=self.now)
 def test_pkce_and_random_transactions(self):
  url,tx=self.start()
  params=parse_qs(urlsplit(url).query)
  self.assertEqual(params["code_challenge_method"],["S256"])
  self.assertEqual(params["code_challenge"],[challenge(tx.verifier)])
  self.assertEqual(params["nonce"],[tx.nonce])
  self.assertEqual(params["state"],[tx.state])
  self.assertNotEqual(self.start()[1].state,tx.state)
 def test_valid_callback(self):
  _,tx=self.start()
  self.assertEqual(verify_callback(tx,tx.state,"code",self.now),tx.verifier)
 def test_rejects_missing_or_changed_state(self):
  _,tx=self.start()
  for state in ("", "attacker"):
   with self.assertRaises(ValueError): verify_callback(tx,state,"code",self.now)
  with self.assertRaises(ValueError): verify_callback(tx,tx.state,"",self.now)
 def test_expired_and_future_transactions(self):
  _,tx=self.start()
  for time in (self.now+timedelta(minutes=6),self.now-timedelta(seconds=1)):
   with self.assertRaises(ValueError): verify_callback(tx,tx.state,"code",time)
 def test_requires_https(self):
  with self.assertRaises(ValueError):
   begin("http://idp.invalid/authorize","cb","https://app.example/callback")

if __name__=="__main__":unittest.main()
