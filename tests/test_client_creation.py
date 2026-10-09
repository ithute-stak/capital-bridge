import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app, authenticate
from api.client_schemas import ClientCreate

COMPANY = UUID("11111111-1111-4111-8111-111111111111")
USER = UUID("22222222-2222-4222-8222-222222222222")

class ClientCreationTests(unittest.TestCase):
 def setUp(self):
  self.client=TestClient(app)
  self.url=f"/api/v1/companies/{COMPANY}/clients"
 def tearDown(self):
  app.dependency_overrides.clear()
 def test_anonymous_create_is_denied(self):
  self.assertEqual(self.client.post(self.url,json={"client_code":"C01","legal_name":"Example"}).status_code,401)
 def test_invalid_fields_rejected(self):
  with self.assertRaises(ValueError):
   ClientCreate(client_code=" ",legal_name="Example")
  with self.assertRaises(ValueError):
   ClientCreate(client_code="C01",legal_name="Example",company_id=str(COMPANY))
 def test_auditor_cannot_create(self):
  app.dependency_overrides[authenticate]=lambda: USER
  class Cursor:
   def fetchone(self): return {"role":"auditor"}
  class Conn:
   def __enter__(self): return self
   def __exit__(self,*args): return False
   def transaction(self): return self
   def execute(self,*args): return Cursor()
  with patch("api.clients.psycopg.connect",return_value=Conn()),patch(
   "api.clients.validate_company"
  ),patch("api.clients.config",return_value=("issuer","aud","keys","dsn")):
   result=self.client.post(self.url,json={"client_code":"C01","legal_name":"Example"})
  self.assertEqual(result.status_code,403)

if __name__ == "__main__":
 unittest.main()
