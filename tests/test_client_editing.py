import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient

from api.main import app, authenticate
from api.client_update_schema import ClientUpdate

COMPANY = UUID("11111111-1111-4111-8111-111111111111")
CLIENT = UUID("33333333-3333-4333-8333-333333333333")
USER = UUID("22222222-2222-4222-8222-222222222222")


class ClientEditingTests(unittest.TestCase):
    def setUp(self):
        self.http = TestClient(app)
        self.url = f"/api/v1/companies/{COMPANY}/clients/{CLIENT}"
        self.payload = {"legal_name": "Updated Name", "email": "client@example.org",
                        "phone": "+26650000000", "status": "active"}

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_anonymous_edit_denied(self):
        self.assertEqual(self.http.put(self.url, json=self.payload).status_code, 401)

    def test_ownership_and_client_reference_cannot_be_changed(self):
        for forbidden in ("company_id", "client_code", "id"):
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(ValueError):
                    ClientUpdate.model_validate({**self.payload, forbidden: "altered"})

    def test_auditor_edit_denied_without_update_sql(self):
        app.dependency_overrides[authenticate] = lambda: USER

        class Cursor:
            def fetchone(self):
                return {"role": "auditor"}

        class Connection:
            def __init__(self):
                self.sql = []
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def transaction(self): return self
            def execute(self, statement, args):
                self.sql.append(statement)
                return Cursor()

        conn = Connection()
        with patch("api.clients.psycopg.connect", return_value=conn), patch(
            "api.clients.config", return_value=("issuer", "audience", "jwks", "dsn")
        ), patch("api.clients.validate_company") as access:
            response = self.http.put(self.url, json=self.payload)
        self.assertEqual(response.status_code, 403)
        access.assert_called_once_with(COMPANY, USER, conn)
        self.assertFalse(any("UPDATE cb.clients" in statement for statement in conn.sql))

    def test_authorized_edit_still_matches_company_and_client(self):
        app.dependency_overrides[authenticate] = lambda: USER

        class Cursor:
            def __init__(self, value): self.value = value
            def fetchone(self): return self.value

        class Connection:
            def __init__(self): self.calls = []
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def transaction(self): return self
            def execute(self, statement, args):
                self.calls.append((statement, args))
                if "SELECT role" in statement:
                    return Cursor({"role": "director"})
                return Cursor({"client_code": "CB-001"})

        conn = Connection()
        with patch("api.clients.psycopg.connect", return_value=conn), patch(
            "api.clients.config", return_value=("issuer", "audience", "jwks", "dsn")
        ), patch("api.clients.validate_company"):
            response = self.http.put(self.url, json=self.payload)
        self.assertEqual(response.status_code, 200)
        statement, args = conn.calls[-1]
        self.assertIn("WHERE company_id=%s AND id=%s", statement)
        self.assertEqual(args[-2:], (COMPANY, CLIENT))
        self.assertEqual(response.json()["code"], "CB-001")


if __name__ == "__main__":
    unittest.main()
