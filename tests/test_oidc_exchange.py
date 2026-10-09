import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from api.oidc_login import LoginTransaction
from api.oidc_exchange import OidcProvider,exchange_and_verify
from api.oidc_verify import TrustedIdentity

class OidcExchangeTests(unittest.TestCase):
 def setUp(self):
  self.provider=OidcProvider(
   issuer="https://idp.example.test",
   token_endpoint="https://idp.example.test/oauth/token",
   jwks_url="https://idp.example.test/keys",
   client_id="capitalbridge-public",
   redirect_uri="https://capitalbridge.example/oidc/callback")
  self.tx=LoginTransaction("random-state","random-nonce","random-verifier",datetime.now(timezone.utc))
  self.client=Mock()
  self.client.post.return_value.json.return_value={"id_token":"signed.test.token"}

 def test_valid_exchange_passes_only_verified_claims(self):
  with patch("api.oidc_exchange.verify_id_token",return_value=TrustedIdentity("https://idp.example.test","subject")) as verify:
   result=exchange_and_verify(self.provider,self.tx,"random-state","auth-code",client=self.client)
   self.assertEqual(result.subject,"subject")
   verify.assert_called_once()
   self.assertEqual(verify.call_args.kwargs["expected_nonce"],"random-nonce")
   request=self.client.post.call_args
   self.assertEqual(request.args[0],self.provider.token_endpoint)
   self.assertEqual(request.kwargs["data"]["code_verifier"],"random-verifier")
   self.assertFalse(request.kwargs["follow_redirects"])

 def test_mismatched_state_aborts_before_network(self):
  with self.assertRaises(ValueError):
   exchange_and_verify(self.provider,self.tx,"attacker","auth-code",client=self.client)
  self.client.post.assert_not_called()

 def test_http_response_without_id_token_denied(self):
  self.client.post.return_value.json.return_value={"access_token":"access-only"}
  with self.assertRaises(ValueError):
   exchange_and_verify(self.provider,self.tx,"random-state","auth-code",client=self.client)

 def test_untrusted_token_endpoint_denied(self):
  from dataclasses import replace
  malicious=replace(self.provider,token_endpoint="https://evil.example.test/token")
  with self.assertRaises(ValueError):
   exchange_and_verify(malicious,self.tx,"random-state","auth-code",client=self.client)
  self.client.post.assert_not_called()

if __name__=="__main__": unittest.main()
