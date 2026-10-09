import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.session_routes import router

app=FastAPI()
app.include_router(router)

class SessionRouteTests(unittest.TestCase):
 def setUp(self): self.client=TestClient(app)
 def test_missing_session_reports_signed_out(self):
  r=self.client.get("/api/v1/session/status")
  self.assertEqual(r.status_code,200)
  self.assertEqual(r.json(),{"authenticated":False})
 def test_login_fails_closed(self):
  r=self.client.post("/api/v1/session/login")
  self.assertEqual(r.status_code,503)
 def test_logout_rejects_missing_origin(self):
  r=self.client.post("/api/v1/session/logout")
  self.assertEqual(r.status_code,403)
 def test_logout_rejects_cross_origin(self):
  with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://capitalbridge.example"}):
   r=self.client.post("/api/v1/session/logout",
       headers={"Origin":"https://attacker.example"})
  self.assertEqual(r.status_code,403)
 def test_logout_without_cookie_clears_cookie(self):
  with patch.dict("os.environ",{"CB_PUBLIC_ORIGIN":"https://capitalbridge.example"}):
   r=self.client.post("/api/v1/session/logout",
       headers={"Origin":"https://capitalbridge.example"})
  self.assertEqual(r.status_code,200)
  self.assertIn("__Host-cb_session=",r.headers.get("set-cookie",""))
  self.assertEqual(r.headers.get("cache-control"),"no-store")

if __name__=="__main__":
 unittest.main()
