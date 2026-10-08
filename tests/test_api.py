import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        r=self.client.get("/health")
        self.assertEqual(r.status_code,200)

    def test_no_bearer_denied(self):
        r=self.client.get("/api/v1/companies/11111111-1111-4111-8111-111111111111/finance/trial-balance?as_of=2026-10-08")
        self.assertEqual(r.status_code,401)

    def test_malformed_bearer_denied(self):
        with patch.dict(os.environ,{"CB_OIDC_ISSUER":"https://example.invalid",
                                    "CB_OIDC_AUDIENCE":"capitalbridge",
                                    "CB_OIDC_JWKS_URL":"https://example.invalid/keys",
                                    "CB_DATABASE_URL":"postgres://none"},clear=False):
            r=self.client.get("/api/v1/companies/11111111-1111-4111-8111-111111111111/finance/trial-balance?as_of=2026-10-08",
                              headers={"Authorization":"Bearer not-a-jwt"})
            self.assertEqual(r.status_code,401)

    def test_invalid_reporting_date_denied(self):
        r=self.client.get("/api/v1/companies/11111111-1111-4111-8111-111111111111/finance/trial-balance?as_of=not-a-date")
        self.assertEqual(r.status_code,422)

if __name__=="__main__":
    unittest.main()
