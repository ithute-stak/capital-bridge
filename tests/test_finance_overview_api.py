import os
import unittest
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient
from api.main import app


class FinanceOverviewTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.url = "/api/v1/companies/11111111-1111-4111-8111-111111111111/finance/overview?as_of=2026-10-09"

    def test_anonymous_cannot_read_overview(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_malformed_token_rejected(self):
        with patch.dict(os.environ, {
            "CB_OIDC_ISSUER":"https://identity.example.invalid",
            "CB_OIDC_AUDIENCE":"capitalbridge",
            "CB_OIDC_JWKS_URL":"https://identity.example.invalid/keys",
            "CB_DATABASE_URL":"postgresql://unused",
        }):
            result = self.client.get(self.url, headers={"Authorization":"Bearer invalid"})
        self.assertEqual(result.status_code, 401)

    def test_company_access_denied(self):
        from api.main import validate_company
        from fastapi import HTTPException

        class DeniedConn:
            def __init__(self): self.calls = []
            def execute(self, query, parameters):
                self.calls.append((query, parameters))
                return self
            def fetchone(self): return None

        conn = DeniedConn()
        with self.assertRaises(HTTPException) as ctx:
            validate_company(UUID("11111111-1111-4111-8111-111111111111"),
                             UUID("22222222-2222-4222-8222-222222222222"), conn)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(conn.calls[0][1][0], "11111111-1111-4111-8111-111111111111")
        self.assertEqual(conn.calls[1][1][0], "22222222-2222-4222-8222-222222222222")


if __name__ == "__main__":
    unittest.main()
