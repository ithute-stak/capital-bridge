import unittest
from unittest.mock import Mock,patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.oidc_http_flow import router,configure_for_testing,TrustedRuntime

app=FastAPI()
app.include_router(router)

class HttpOidcFlowTests(unittest.TestCase):
 def tearDown(self): configure_for_testing(None)
 def test_unconfigured_start_fails_closed(self):
  configure_for_testing(None)
  r=TestClient(app).get("/api/v1/oidc/start",follow_redirects=False)
  self.assertEqual(r.status_code,503)
  self.assertNotIn("set-cookie",r.headers)
 def test_unconfigured_callback_fails_closed(self):
  configure_for_testing(None)
  r=TestClient(app).get("/api/v1/oidc/complete?state=xyz&code=test",follow_redirects=False)
  self.assertEqual(r.status_code,503)
 def test_failed_callback_does_not_issue_session(self):
  mock=Mock()
  runtime=TrustedRuntime("https://identity.example/authorize","test-public",
    "https://capitalbridge.example/api/v1/oidc/complete",mock,mock,mock,mock,mock)
  configure_for_testing(runtime)
  with patch("api.oidc_http_flow.complete_verified_login",return_value=None) as login:
   r=TestClient(app).get("/api/v1/oidc/complete?state="+("a"*32)+"&code=valid",
     cookies={"__Host-cb_oidc":"b"*32},follow_redirects=False)
  self.assertEqual(r.status_code,401)
  login.assert_called_once()
  self.assertNotIn("__Host-cb_session",r.headers.get("set-cookie",""))
 def test_bad_state_is_rejected_before_exchange(self):
  mock=Mock()
  configure_for_testing(TrustedRuntime("https://identity.example/authorize","id",
    "https://capitalbridge.example/api/v1/oidc/complete",mock,mock,mock,mock,mock))
  with patch("api.oidc_http_flow.complete_verified_login") as login:
   r=TestClient(app).get("/api/v1/oidc/complete?state=no&code=valid",
     cookies={"__Host-cb_oidc":"b"*32})
  self.assertEqual(r.status_code,400)
  login.assert_not_called()

if __name__=="__main__":unittest.main()
