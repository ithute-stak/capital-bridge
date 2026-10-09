import unittest
from fastapi import HTTPException, FastAPI
from fastapi.testclient import TestClient
from api.oidc_callback_guards import (
 validate_callback,callback_cookie_settings,callback_response_headers
)
from api.oidc_callback_routes import router

class CallbackGuardTests(unittest.TestCase):
 def test_valid_shape(self):
  item=validate_callback(state="s"*32,code="opaque-code",browser_binding="b"*32)
  self.assertEqual(item.code,"opaque-code")

 def test_invalid_callback_fails_closed(self):
  cases=[
   dict(state=None,code="code",browser_binding="b"*32),
   dict(state="s"*32,code=None,browser_binding="b"*32),
   dict(state="s"*32,code="code",browser_binding=None),
   dict(state="s"*32,code="bad\\ncode",browser_binding="b"*32),
   dict(state="s"*32,code="c"*4097,browser_binding="b"*32),
   dict(state="s"*32,code="code",browser_binding="b"*32,error="access_denied"),
  ]
  for case in cases:
   with self.subTest(case=case),self.assertRaises(HTTPException):
    validate_callback(**case)

 def test_cookie_and_response_flags(self):
  opts=callback_cookie_settings()
  self.assertTrue(opts["secure"])
  self.assertTrue(opts["httponly"])
  self.assertEqual(opts["samesite"],"lax")
  self.assertEqual(opts["max_age"],300)
  headers=callback_response_headers()
  self.assertEqual(headers["Cache-Control"],"no-store")
  self.assertEqual(headers["Referrer-Policy"],"no-referrer")

 def test_staging_endpoint_never_creates_session(self):
  app=FastAPI()
  app.include_router(router)
  client=TestClient(app)
  r=client.get("/api/v1/oidc/callback",params={"state":"s"*32,"code":"test"},
   cookies={"__Host-cb_oidc":"b"*32})
  self.assertEqual(r.status_code,503)
  self.assertNotIn("__Host-cb_session",r.headers.get("set-cookie",""))

if __name__=="__main__": unittest.main()
