import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

class PublicConsultationEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        self.payload={
            "name":"Maseru Client","email":"client@example.com",
            "service":"Information Technology",
            "message":"Please contact me regarding this business project.",
            "consent":True,
        }
    def test_default_disabled_even_valid_data(self):
        with patch.dict(os.environ,{"CB_PUBLIC_INTAKE_ENABLED":"false"}):
            response=self.client.post("/api/v1/consultations",json=self.payload,
                headers={"Origin":"https://capitalbridge.co.ls"})
        self.assertEqual(response.status_code,503)
        self.assertNotIn("database",str(response.json()).lower())

    def test_invalid_origin_refused_before_backend_access(self):
        with patch.dict(os.environ,{"CB_PUBLIC_INTAKE_ENABLED":"true"}):
            with patch("api.consultation_public.intake_dependencies",side_effect=AssertionError("backend reached")):
                response=self.client.post("/api/v1/consultations",json=self.payload,
                    headers={"Origin":"https://untrusted.example"})
        self.assertEqual(response.status_code,400)

    def test_tenant_fields_are_not_accepted_by_payload_schema(self):
        from api.consultation_schema import ConsultationEnquiry
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ConsultationEnquiry.model_validate({**self.payload,"company_id":"random"})

    def test_enabled_without_dependencies_fails_closed(self):
        with patch.dict(os.environ,{"CB_PUBLIC_INTAKE_ENABLED":"true"},clear=True):
            response=self.client.post("/api/v1/consultations",json=self.payload,
                headers={"Origin":"https://capitalbridge.co.ls"})
        self.assertEqual(response.status_code,503)

    def test_readiness_never_discloses_configuration(self):
        with patch.dict(os.environ,{"CB_PUBLIC_INTAKE_ENABLED":"false"}):
            response=self.client.get("/api/v1/consultations/intake/readiness")
        self.assertFalse(response.json()["online_submission_available"])
