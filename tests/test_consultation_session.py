import os
import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app
from api.consultation_session import staff_session_subject

COMPANY="11111111-1111-4111-8111-111111111111"
ENQUIRY="22222222-2222-4222-8222-222222222222"
USER=UUID("33333333-3333-4333-8333-333333333333")
PATH=f"/api/v1/staff/consultations/companies/{COMPANY}/enquiries/{ENQUIRY}/status"

class StaffCookieSessionTests(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_staff_cookie_required(self):
        response=TestClient(app).get("/api/v1/staff/consultations/companies")
        self.assertEqual(response.status_code,401)

    def test_cross_site_status_update_denied(self):
        app.dependency_overrides[staff_session_subject]=lambda: USER
        with patch.dict(os.environ,{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}):
            with patch("api.consultation_session.update_consultation_status",
                       side_effect=AssertionError("must not update")):
                response=TestClient(app).patch(PATH,json={"status":"in_review"},
                          headers={"Origin":"https://untrusted.example"})
        self.assertEqual(response.status_code,403)

    def test_staff_status_change_requires_valid_origin(self):
        app.dependency_overrides[staff_session_subject]=lambda: USER
        with patch.dict(os.environ,{"CB_PUBLIC_ORIGIN":"https://capitalbridge.co.ls"}):
            with patch("api.consultation_session.update_consultation_status",
                       return_value={"id":ENQUIRY,"company_id":COMPANY,"status":"in_review"}):
                response=TestClient(app).patch(PATH,json={"status":"in_review"},
                          headers={"Origin":"https://capitalbridge.co.ls"})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["status"],"in_review")

    def test_staff_queue_is_authorized_server_side(self):
        app.dependency_overrides[staff_session_subject]=lambda: USER
        with patch("api.consultation_session.list_consultations",
                   return_value={"company_id":COMPANY,"enquiries":[]}) as getter:
            response=TestClient(app).get(
                f"/api/v1/staff/consultations/companies/{COMPANY}/enquiries?limit=10")
        self.assertEqual(response.status_code,200)
        self.assertEqual(getter.call_args.kwargs["user_id"],USER)
