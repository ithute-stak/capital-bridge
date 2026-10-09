import unittest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.ithute_oidc_router import make_ithute_oidc_router
from api.login_service import LoginService


class IthuteRouterTests(unittest.TestCase):
    def app(self, factory):
        app = FastAPI()
        app.include_router(make_ithute_oidc_router(factory))
        return TestClient(app, follow_redirects=False)

    def test_no_service_fails_closed(self):
        client = self.app(lambda: None)
        result = client.get("/api/v1/oidc/start")
        self.assertEqual(result.status_code, 503)

    def test_start_uses_request_scoped_service_and_binding_cookie(self):
        service = object.__new__(LoginService)
        service.begin = Mock(return_value=Mock(
            authorization_url="https://auth.ithute.co.ls/oauth/authorize?state=test",
            browser_binding="binding-" + "x" * 32,
        ))
        client = self.app(lambda: service)
        response = client.get("/api/v1/oidc/start")
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers["location"].startswith("https://auth.ithute.co.ls/"))
        self.assertIn("Secure", response.headers["set-cookie"])
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        service.begin.assert_called_once_with()

    def test_invalid_callback_rejected_before_service_resolution(self):
        factory = Mock(return_value=None)
        client = self.app(factory)
        response = client.get("/api/v1/oidc/complete?state=x&code=y")
        self.assertEqual(response.status_code, 400)
        factory.assert_not_called()

    def test_callback_rejects_unknown_identity_without_session_cookie(self):
        service = object.__new__(LoginService)
        service.complete = Mock(return_value=None)
        client = self.app(lambda: service)
        response = client.get(
            "/api/v1/oidc/complete?state=" + "a" * 32 + "&code=valid-code",
            cookies={"__Host-cb_oidc": "b" * 32},
        )
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("__Host-cb_session", response.headers.get("set-cookie", ""))
        service.complete.assert_called_once()


if __name__ == "__main__":
    unittest.main()
