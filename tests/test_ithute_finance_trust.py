import unittest
from unittest.mock import patch
from api.main import config

class IthuteFinanceTrustTests(unittest.TestCase):
    def setUp(self):
        self.correct = {
            "CB_OIDC_ISSUER": "https://auth.ithute.co.ls",
            "CB_OIDC_AUDIENCE": "capitalbridge",
            "CB_OIDC_JWKS_URL": "https://auth.ithute.co.ls/.well-known/jwks.json",
            "CB_DATABASE_URL": "postgresql://restricted@localhost/test",
        }

    def test_only_ithute_provider_and_capitalbridge_client_allowed(self):
        with patch.dict("os.environ", self.correct, clear=True):
            self.assertEqual(config(), (
                self.correct["CB_OIDC_ISSUER"], "capitalbridge",
                self.correct["CB_OIDC_JWKS_URL"], self.correct["CB_DATABASE_URL"],
            ))

    def test_rejects_modified_trust_or_missing_finance_database(self):
        changes = [
            ("CB_OIDC_ISSUER", "https://forged.example.org"),
            ("CB_OIDC_AUDIENCE", "loanhub"),
            ("CB_OIDC_JWKS_URL", "https://keys.attacker.test/jwks"),
            ("CB_DATABASE_URL", ""),
        ]
        for field, value in changes:
            with self.subTest(field=field), patch.dict(
                "os.environ", {**self.correct, field:value}, clear=True
            ):
                with self.assertRaises(RuntimeError):
                    config()

if __name__ == "__main__":
    unittest.main()
