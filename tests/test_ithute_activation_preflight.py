import unittest
from unittest.mock import patch

from api.ithute_activation_preflight import check_static_ithute_auth_prerequisites


class ActivationPreflightTests(unittest.TestCase):
    def setUp(self):
        self.valid = {
            "CB_ITHUTE_OIDC_REDIRECT_URI": "https://capitalbridge.co.ls/api/v1/oidc/complete",
            "CB_OIDC_TRANSACTION_DATABASE_URL": "postgresql://tx",
            "CB_IDENTITY_DATABASE_URL": "postgresql://identities",
            "CB_SESSION_DATABASE_URL": "postgresql://sessions",
        }

    def test_configured_prerequisites_are_only_manual_review_ready(self):
        with patch.dict("os.environ", self.valid, clear=True):
            state = check_static_ithute_auth_prerequisites()
        self.assertTrue(state.ready_for_manual_e2e_review)
        self.assertEqual(state.callback, "https://capitalbridge.co.ls/api/v1/oidc/complete")

    def test_wrong_callback_missing_and_shared_role_configuration_rejected(self):
        for values in [
            {**self.valid, "CB_ITHUTE_OIDC_REDIRECT_URI": "https://evil.test/api/v1/oidc/complete"},
            {**self.valid, "CB_SESSION_DATABASE_URL": ""},
            {**self.valid, "CB_IDENTITY_DATABASE_URL": self.valid["CB_OIDC_TRANSACTION_DATABASE_URL"]},
        ]:
            with self.subTest(values=values), patch.dict("os.environ", values, clear=True):
                with self.assertRaises(RuntimeError):
                    check_static_ithute_auth_prerequisites()

    def test_api_readiness_stays_disabled(self):
        from api.main import authentication_readiness
        self.assertIs(authentication_readiness()["sign_in_available"], False)


if __name__ == "__main__":
    unittest.main()
