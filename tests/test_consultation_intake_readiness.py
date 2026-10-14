import unittest
from fastapi.testclient import TestClient
from api.main import app


class IntakeReadinessTests(unittest.TestCase):
    def test_online_submission_not_activated(self):
        response=TestClient(app).get("/api/v1/consultations/intake/readiness")
        self.assertEqual(response.status_code,200)
        payload=response.json()
        self.assertIs(payload["online_submission_available"],False)
        self.assertEqual(payload["delivery_method"],"user_reviewed_email")
        self.assertNotIn("secret",str(payload).lower())

    def test_public_submission_fails_closed_by_default(self):
        response=TestClient(app).post("/api/v1/consultations",json={"name":"Visitor"})
        self.assertEqual(response.status_code,503)
