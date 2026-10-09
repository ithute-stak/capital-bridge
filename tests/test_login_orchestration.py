import unittest
from unittest.mock import Mock, patch, call
from uuid import UUID
from api.login_orchestration import complete_verified_login
from api.oidc_verify import TrustedIdentity
from api.oidc_login import LoginTransaction
from datetime import datetime, timezone

class LoginOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.tx_db=Mock()
        self.user_db=Mock()
        self.session_db=Mock()
        self.http_client=Mock()
        self.transaction=LoginTransaction("state","nonce","verifier",datetime.now(timezone.utc))
        self.params=dict(tx_db=self.tx_db,user_db=self.user_db,session_db=self.session_db,
            provider=Mock(),browser_binding="binding",state="state",code="code",
            http_client=self.http_client)

    @patch("api.login_orchestration.issue")
    @patch("api.login_orchestration.resolve_registered_user")
    @patch("api.login_orchestration.exchange_and_verify")
    @patch("api.login_orchestration.consume")
    def test_success_issues_session_after_verified_lookup(self, consume, exchange, lookup, issue):
        consume.return_value=self.transaction
        exchange.return_value=TrustedIdentity("https://idp.example","subject")
        lookup.return_value=UUID("22222222-2222-4222-8222-222222222222")
        issue.return_value="opaque-cookie"
        result=complete_verified_login(**self.params)
        self.assertEqual(result.session_cookie,"opaque-cookie")
        self.tx_db.commit.assert_called_once()
        self.session_db.commit.assert_called_once()
        lookup.assert_called_once_with(self.user_db,exchange.return_value)

    @patch("api.login_orchestration.issue")
    @patch("api.login_orchestration.exchange_and_verify")
    @patch("api.login_orchestration.consume",return_value=None)
    def test_missing_or_replayed_transaction_rejected(self,consume,exchange,issue):
        self.assertIsNone(complete_verified_login(**self.params))
        exchange.assert_not_called()
        issue.assert_not_called()
        self.tx_db.commit.assert_not_called()

    @patch("api.login_orchestration.issue")
    @patch("api.login_orchestration.resolve_registered_user",return_value=None)
    @patch("api.login_orchestration.exchange_and_verify",return_value=TrustedIdentity("https://idp.example","unknown"))
    @patch("api.login_orchestration.consume")
    def test_unknown_verified_identity_cannot_issue_session(self,consume,exchange,lookup,issue):
        consume.return_value=self.transaction
        self.assertIsNone(complete_verified_login(**self.params))
        self.tx_db.commit.assert_called_once()
        issue.assert_not_called()
        self.session_db.commit.assert_not_called()

    @patch("api.login_orchestration.issue")
    @patch("api.login_orchestration.exchange_and_verify",side_effect=ValueError("bad ID token"))
    @patch("api.login_orchestration.consume")
    def test_bad_identity_fails_after_consuming_transaction(self,consume,exchange,issue):
        consume.return_value=self.transaction
        with self.assertRaises(ValueError):
            complete_verified_login(**self.params)
        self.tx_db.commit.assert_called_once()
        issue.assert_not_called()

if __name__=="__main__":
    unittest.main()
