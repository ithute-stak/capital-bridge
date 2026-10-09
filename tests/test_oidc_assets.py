import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
class OidcAssetTests(unittest.TestCase):
    def test_opt_in_no_persistent_token_storage(self):
        source = (ROOT/"web/oidc-session.js").read_text()
        self.assertIn("if (!settings) return", source)
        self.assertIn("code_challenge_method", source)
        self.assertIn("S256", source)
        self.assertIn("crypto.getRandomValues", source)
        self.assertIn("transaction.state !== url.searchParams.get", source)
        self.assertNotIn('localStorage', source)
        self.assertNotIn('sessionStorage.setItem("access_token"', source)
    def test_config_is_example_only(self):
        config = (ROOT/"web/oidc-config.example.js").read_text()
        self.assertNotIn("clientSecret:", config)
        self.assertIn("EXAMPLE ONLY", config)

if __name__=="__main__":
    unittest.main()
