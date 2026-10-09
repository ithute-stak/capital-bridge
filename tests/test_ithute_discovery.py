import unittest
from unittest.mock import Mock, patch

from api.ithute_discovery import verify_ithute_discovery, DISCOVERY_URL


class IthuteDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            "issuer": "https://auth.ithute.co.ls",
            "authorization_endpoint": "https://auth.ithute.co.ls/oauth/authorize",
            "token_endpoint": "https://auth.ithute.co.ls/oauth/token",
            "jwks_uri": "https://auth.ithute.co.ls/.well-known/jwks.json",
            "code_challenge_methods_supported": ["S256"],
            "response_types_supported": ["code"],
        }
        self.env = {"CB_ITHUTE_OIDC_REDIRECT_URI": "https://capitalbridge.co.ls/api/v1/oidc/complete"}

    def verify(self, metadata):
        client = Mock()
        client.get.return_value.json.return_value = metadata
        with patch.dict("os.environ", self.env, clear=True):
            result = verify_ithute_discovery(client)
        client.get.assert_called_once_with(
            DISCOVERY_URL, headers={"Accept": "application/json"},
            timeout=5.0, follow_redirects=False,
        )
        return result

    def test_exact_trusted_discovery_accepted(self):
        self.assertEqual(self.verify(self.metadata).provider.client_id, "capitalbridge")

    def test_wrong_issuer_endpoints_and_missing_pkce_denied(self):
        for field, bad in [
            ("issuer", "https://evil.test"),
            ("authorization_endpoint", "https://evil.test/oauth/authorize"),
            ("token_endpoint", "https://evil.test/oauth/token"),
            ("jwks_uri", "https://evil.test/keys"),
            ("code_challenge_methods_supported", ["plain"]),
            ("response_types_supported", ["token"]),
        ]:
            with self.subTest(field=field):
                with self.assertRaises(RuntimeError):
                    self.verify({**self.metadata, field: bad})

    def test_missing_redirect_denied_without_remote_request(self):
        client = Mock()
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                verify_ithute_discovery(client)
        client.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
