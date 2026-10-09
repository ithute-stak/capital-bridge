import unittest
from unittest.mock import patch
from api.ithute_auth_provider import IthuteAuthConfiguration

class IthuteAuthProviderTests(unittest.TestCase):
 def test_pinned_trust(self):
  uri="https://capitalbridge.co.ls/api/v1/oidc/complete"
  with patch.dict("os.environ",{"CB_ITHUTE_OIDC_REDIRECT_URI":uri},clear=True):
   result=IthuteAuthConfiguration.from_environment()
  self.assertEqual(result.provider.issuer,"https://auth.ithute.co.ls")
  self.assertEqual(result.provider.client_id,"capitalbridge")
  self.assertEqual(result.provider.redirect_uri,uri)
  self.assertEqual(result.provider.jwks_url,"https://auth.ithute.co.ls/.well-known/jwks.json")
  self.assertEqual(result.authorization_endpoint,"https://auth.ithute.co.ls/oauth/authorize")
 def test_missing_redirect_denied(self):
  with patch.dict("os.environ",{},clear=True):
   with self.assertRaises(RuntimeError):
    IthuteAuthConfiguration.from_environment()
 def test_untrusted_callback_patterns_denied(self):
  for uri in [
   "http://capitalbridge.example.org/api/v1/oidc/complete",
   "https://capitalbridge.example.org/api/v1/oidc/complete",
   "https://capitalbridge.co.ls/other",
   "https://capitalbridge.co.ls/api/v1/oidc/complete?next=https://evil.invalid",
   "https://capitalbridge.co.ls/api/v1/oidc/complete#fragment",
   "https://user:password@capitalbridge.example.org/api/v1/oidc/complete",
  ]:
   with self.subTest(uri=uri),patch.dict("os.environ",{"CB_ITHUTE_OIDC_REDIRECT_URI":uri},clear=True):
    with self.assertRaises(RuntimeError):
     IthuteAuthConfiguration.from_environment()
if __name__=="__main__":unittest.main()
