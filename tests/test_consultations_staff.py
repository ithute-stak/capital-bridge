import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient

from api.main import app, authenticate

COMPANY = "11111111-1111-4111-8111-111111111111"
USER = UUID("22222222-2222-4222-8222-222222222222")


class FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def transaction(self): return self
    def execute(self, query, args):
        self.calls.append((query, args))
        return self
    def fetchall(self): return self.rows


class ConsultationStaffTests(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_auth_required(self):
        response = TestClient(app).get(f"/api/v1/companies/{COMPANY}/consultations")
        self.assertEqual(response.status_code, 401)

    def test_company_membership_required_before_query(self):
        from fastapi import HTTPException
        app.dependency_overrides[authenticate] = lambda: USER
        db = FakeDB([])
        with patch("api.consultations.config", return_value=("iss", "aud", "jwks", "dsn")), \
             patch("api.consultations.psycopg.connect", return_value=db), \
             patch("api.consultations.validate_company", side_effect=HTTPException(status_code=403, detail="Denied")):
            response = TestClient(app).get(f"/api/v1/companies/{COMPANY}/consultations")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(db.calls, [])

    def test_company_filter_and_bounded_result(self):
        app.dependency_overrides[authenticate] = lambda: USER
        db = FakeDB([])
        with patch("api.consultations.config", return_value=("iss", "aud", "jwks", "dsn")), \
             patch("api.consultations.psycopg.connect", return_value=db), \
             patch("api.consultations.validate_company"):
            response = TestClient(app).get(f"/api/v1/companies/{COMPANY}/consultations?limit=20")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["company_id"], COMPANY)
        self.assertEqual(len(db.calls), 1)
        sql, args = db.calls[0]
        self.assertIn("WHERE company_id=%s", sql)
        self.assertEqual(args, (UUID(COMPANY), 20))

    def test_limit_cannot_exceed_100(self):
        app.dependency_overrides[authenticate] = lambda: USER
        response = TestClient(app).get(f"/api/v1/companies/{COMPANY}/consultations?limit=500")
        self.assertEqual(response.status_code, 422)
