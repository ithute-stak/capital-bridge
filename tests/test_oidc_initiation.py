import unittest
from unittest.mock import Mock,patch
from urllib.parse import urlsplit,parse_qs
from api.oidc_initiation import initiate_login

class InitiationTests(unittest.TestCase):
 def setUp(self):
  self.db=Mock()
 def test_persists_before_redirect(self):
  with patch("api.oidc_initiation.store") as save:
   result=initiate_login(db=self.db,
     authorization_endpoint="https://idp.example.test/authorize",
     client_id="capitalbridge-public",
     redirect_uri="https://capitalbridge.example/callback")
   self.db.commit.assert_called_once()
   save.assert_called_once()
   params=parse_qs(urlsplit(result.authorization_url).query)
   self.assertEqual(params["code_challenge_method"],["S256"])
   self.assertEqual(params["response_type"],["code"])
   self.assertGreaterEqual(len(result.browser_binding),32)
 def test_http_identity_provider_rejected(self):
  with self.assertRaises(ValueError):
   initiate_login(db=self.db,authorization_endpoint="http://unsafe.example/authorize",
     client_id="app",redirect_uri="https://capitalbridge.example/callback")
  self.db.commit.assert_not_called()
