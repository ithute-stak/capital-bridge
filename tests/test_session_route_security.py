import unittest
from contextlib import contextmanager
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.session_routes import router

class SessionRouteSecurityTests(unittest.TestCase):
    def setUp(self):
        app=FastAPI()
        app.include_router(router)
        self.client=TestClient(app)
    def test_logout_rejects_missing_or_untrusted_origin(self):
        with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://bridge.example.org"},clear=True):
            self.assertEqual(self.client.post("/api/v1/session/logout").status_code,403)
            self.assertEqual(self.client.post("/api/v1/session/logout",headers={"Origin":"https://evil.example.org"}).status_code,403)
    def test_logout_revoke_uses_restricted_session_role(self):
        seen=[]
        @contextmanager
        def connect(dsn,*,purpose):
            seen.append((dsn,purpose))
            yield object()
        with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://bridge.example.org"}), patch(
            "api.session_routes.LoginDatabaseSettings.from_environment"
        ) as settings, patch(
            "api.session_routes.authentication_connection",side_effect=connect
        ), patch("api.session_routes.revoke",return_value=True) as revoke:
            settings.return_value.sessions="postgresql://restricted/session"
            result=self.client.post("/api/v1/session/logout",
                headers={"Origin":"https://bridge.example.org"},
                cookies={"__Host-cb_session":"opaque-cookie"})
        self.assertEqual(result.status_code,200)
        self.assertEqual(seen,[("postgresql://restricted/session","sessions")])
        revoke.assert_called_once()
        self.assertIn("__Host-cb_session",result.headers["set-cookie"])
    def test_status_does_not_expose_user_id(self):
        @contextmanager
        def connect(dsn,*,purpose):
            yield object()
        with patch("api.session_routes.LoginDatabaseSettings.from_environment") as settings, patch(
            "api.session_routes.authentication_connection",side_effect=connect
        ), patch("api.session_routes.resolve",return_value="private-user"):
            settings.return_value.sessions="restricted-session-dsn"
            result=self.client.get("/api/v1/session/status",cookies={"__Host-cb_session":"opaque"})
        self.assertEqual(result.json(),{"authenticated":True})

if __name__=="__main__":
 unittest.main()
