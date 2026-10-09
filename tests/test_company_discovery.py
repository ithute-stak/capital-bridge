import pathlib
import unittest
from fastapi.testclient import TestClient
from api.main import app

ROOT = pathlib.Path(__file__).resolve().parents[1]

class CompanyDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_memberships_require_authentication(self):
        self.assertEqual(self.client.get("/api/v1/me/companies").status_code, 401)

    def test_company_discovery_sql_has_no_public_execute(self):
        sql = (ROOT / "db/migrations/002_company_discovery.sql").read_text()
        self.assertIn("REVOKE ALL ON FUNCTION cb.list_my_companies() FROM PUBLIC", sql)
        self.assertIn("m.user_id=requester", sql)

    def test_adapter_requires_host_identity(self):
        js = (ROOT / "web/finance-session-adapter.js").read_text()
        self.assertIn("identity.getAccessToken", js)
        self.assertIn("if (!identity", js)
        self.assertIn("selectedCompany", js)
        self.assertNotIn("localStorage.setItem", js)
        self.assertNotIn("sessionStorage.setItem", js)


if __name__ == "__main__":
    unittest.main()
