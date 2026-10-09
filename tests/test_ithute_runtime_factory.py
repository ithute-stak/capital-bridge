import unittest
from contextlib import contextmanager
from unittest.mock import Mock, patch

from api.ithute_runtime_factory import ithute_login_service
from api.login_db import LoginDatabaseSettings


class FactoryTests(unittest.TestCase):
    def test_missing_credentials_prevent_remote_calls(self):
        with patch.dict("os.environ", {}, clear=True), patch(
            "api.ithute_runtime_factory.httpx.Client"
        ) as client:
            with self.assertRaises(RuntimeError):
                with ithute_login_service():
                    pass
        client.assert_not_called()

    def test_verified_provider_and_separate_connection_settings(self):
        db = LoginDatabaseSettings("tx", "identity", "sessions")
        provider = Mock()
        provider.issuer = "https://auth.ithute.co.ls"
        provider.client_id = "capitalbridge"
        provider.validate = Mock()
        config = Mock(provider=provider, authorization_endpoint="https://auth.ithute.co.ls/oauth/authorize")
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        with patch("api.ithute_runtime_factory.LoginDatabaseSettings.from_environment", return_value=db), patch(
            "api.ithute_runtime_factory.httpx.Client", return_value=client
        ), patch("api.ithute_runtime_factory.verify_ithute_discovery", return_value=config) as verify:
            with ithute_login_service() as service:
                self.assertIs(service.db, db)
                self.assertIs(service.http_client, client)
                self.assertIs(service.provider, provider)
        verify.assert_called_once_with(client)
        client.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
