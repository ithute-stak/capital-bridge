import unittest
from uuid import UUID
from unittest.mock import patch

from fastapi.testclient import TestClient
from api.main import app, authenticate

COMPANY = UUID("11111111-1111-4111-8111-111111111111")
USER = UUID("22222222-2222-4222-8222-222222222222")

class ClientRegistryTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.path = f"/api/v1/companies/{COMPANY}/clients"

    def test_anonymous_directory_denied(self):
        self.assertEqual(self.client.get(self.path).status_code, 401)

    def test_invalid_limit_rejected(self):
        self.assertEqual(self.client.get(self.path + "?limit=10000").status_code, 401)

    def test_company_must_be_checked_before_reading_clients(self):
        app.dependency_overrides[authenticate] = lambda: USER
        try:
            class Cursor:
                def fetchall(self):
                    return [{"id": UUID("33333333-3333-4333-8333-333333333333"),
                             "client_code": "CB-01", "legal_name": "Example",
                             "email": None, "phone": None, "status": "active"}]
            class Connection:
                def __init__(self): self.queries = []
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def transaction(self): return self
                def execute(self, sql, args):
                    self.queries.append((sql,args))
                    return Cursor()
            conn=Connection()
            with patch("api.clients.config", return_value=("issuer","aud","keys","dsn")), patch(
                "api.clients.psycopg.connect",return_value=conn
            ), patch("api.clients.validate_company") as access:
                result=self.client.get(self.path)
            self.assertEqual(result.status_code,200)
            access.assert_called_once_with(COMPANY,USER,conn)
            self.assertEqual(conn.queries[0][1][0],COMPANY)
            self.assertEqual(result.json()["clients"][0]["code"],"CB-01")
        finally:
            app.dependency_overrides.clear()

if __name__=="__main__":
    unittest.main()
