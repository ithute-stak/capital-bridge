import unittest
from contextlib import contextmanager
from unittest.mock import Mock, patch, call
from uuid import UUID

from api.login_db import LoginDatabaseSettings
from api.login_service import LoginService
from api.oidc_exchange import OidcProvider
from api.oidc_verify import TrustedIdentity


class LoginServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = LoginDatabaseSettings("tx-dsn", "identity-dsn", "session-dsn")
        self.provider = OidcProvider(
            "https://idp.example.test", "https://idp.example.test/token",
            "https://idp.example.test/jwks", "capitalbridge",
            "https://capitalbridge.example/callback",
        )
        self.service = LoginService(
            self.db, self.provider, "https://idp.example.test/authorize", Mock(),
        )
        self.events = []

    def connections(self):
        events = self.events

        @contextmanager
        def connection(dsn, *, purpose, readonly=False):
            events.append("enter:" + purpose)
            yield Mock()
            events.append("commit:" + purpose)
        return connection

    def test_valid_flow_consumes_before_exchange(self):
        with patch("api.login_service.authentication_connection", side_effect=self.connections()), \
             patch("api.login_service.consume", return_value=Mock()) as consume, \
             patch("api.login_service.exchange_and_verify", return_value=TrustedIdentity("https://idp.example.test", "subject")) as exchange, \
             patch("api.login_service.resolve_registered_user", return_value=UUID("22222222-2222-4222-8222-222222222222")), \
             patch("api.login_service.issue", return_value="opaque-session"):
            exchange.side_effect = lambda *args, **kwargs: (
                self.events.append("exchange") or TrustedIdentity("https://idp.example.test", "subject")
            )
            result = self.service.complete(state="state", code="code", browser_binding="binding")
        self.assertEqual(result.cookie, "opaque-session")
        self.assertEqual(self.events, [
            "enter:transactions", "commit:transactions", "exchange",
            "enter:identities", "commit:identities", "enter:sessions", "commit:sessions",
        ])
        consume.assert_called_once()

    def test_invalid_transaction_never_calls_identity_provider(self):
        with patch("api.login_service.authentication_connection", side_effect=self.connections()), \
             patch("api.login_service.consume", return_value=None), \
             patch("api.login_service.exchange_and_verify") as exchange, \
             patch("api.login_service.issue") as issue:
            self.assertIsNone(self.service.complete(state="wrong", code="x", browser_binding="binding"))
        exchange.assert_not_called()
        issue.assert_not_called()

    def test_unknown_user_never_issues_session(self):
        with patch("api.login_service.authentication_connection", side_effect=self.connections()), \
             patch("api.login_service.consume", return_value=Mock()), \
             patch("api.login_service.exchange_and_verify", return_value=TrustedIdentity("https://idp.example.test", "unknown")), \
             patch("api.login_service.resolve_registered_user", return_value=None), \
             patch("api.login_service.issue") as issue:
            self.assertIsNone(self.service.complete(state="state", code="x", browser_binding="binding"))
        issue.assert_not_called()
        self.assertNotIn("enter:sessions", self.events)

    def test_untrusted_authorization_endpoint_rejected(self):
        with self.assertRaises(ValueError):
            LoginService(self.db, self.provider, "https://attacker.example.test/authorize", Mock())


if __name__ == "__main__":
    unittest.main()
