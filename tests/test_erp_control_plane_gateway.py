"""The ERP owner control-plane gateway must remain disabled by default."""
import unittest
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.erp_control_plane_gateway import router
from api.main import app as finance_app, authenticate

OPERATOR = UUID("22222222-2222-4222-8222-222222222222")


class GatewaySecurityTests(unittest.TestCase):
    def test_not_mounted_on_finance_application(self):
        paths = {route.path for route in finance_app.routes if hasattr(route, 'path')}
        self.assertNotIn("/api/v1/platform/tenants", paths)
        self.assertNotIn("/api/v1/platform/tenants/{tenant_id}/transition", paths)

    def test_gateway_fails_closed_even_with_verified_identity(self):
        isolated = FastAPI()
        isolated.include_router(router)
        isolated.dependency_overrides[authenticate] = lambda: OPERATOR
        client = TestClient(isolated)
        response = client.post("/api/v1/platform/tenants",
                               json={"legal_name": "Bank Test", "slug": "bank-test",
                                     "deployment_mode": "dedicated_stack"})
        self.assertEqual(response.status_code, 503)
        response = client.post(
            "/api/v1/platform/tenants/11111111-1111-4111-8111-111111111111/transition",
            json={"expected_status": "pending", "target_status": "active"},
        )
        self.assertEqual(response.status_code, 503)

    def test_invalid_request_parameters_are_rejected(self):
        isolated = FastAPI()
        isolated.include_router(router)
        isolated.dependency_overrides[authenticate] = lambda: OPERATOR
        client = TestClient(isolated)
        response = client.post("/api/v1/platform/tenants",
                               json={"legal_name": "Test", "slug": "test-tenant",
                                     "deployment_mode": "unrecognized"})
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
