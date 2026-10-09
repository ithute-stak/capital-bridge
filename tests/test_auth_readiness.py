import unittest
from fastapi.testclient import TestClient
from api.main import app

class ReadinessTests(unittest.TestCase):
 def test_sign_in_fails_closed_without_identity_provider(self):
  result=TestClient(app).get("/api/v1/auth/readiness")
  self.assertEqual(result.status_code,200)
  self.assertEqual(result.json()["sign_in_available"],False)
  self.assertNotIn("secret",str(result.json()).lower())
 def test_login_endpoint_remains_unavailable(self):
  result=TestClient(app).post("/api/v1/session/login")
  self.assertIn(result.status_code,(404,503))

if __name__=="__main__":
 unittest.main()
