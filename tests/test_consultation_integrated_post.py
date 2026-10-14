import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app

CID=UUID("11111111-1111-4111-8111-111111111111")
PAYLOAD={
    "name":"Maseru Client",
    "email":"client@example.com",
    "service":"Information Technology",
    "message":"Please contact us about our company systems.",
    "consent":True,
}
HEADERS={"Origin":"https://capitalbridge.co.ls"}
APPROVED={"CB_PUBLIC_INTAKE_ENABLED":"true","CB_PUBLIC_INTAKE_APPROVED":"true"}

class FakeDB:
    def __init__(self):
        self.calls=[]
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def transaction(self):return self
    def execute(self,sql,params=None):
        self.calls.append((sql,params))
        return self
    def fetchone(self):return (False,False,True)

class FakeCache:
    def close(self):pass

class IntegratedPublicIntakeTests(unittest.TestCase):
    def test_valid_submission_persists_with_approved_company_only(self):
        db=FakeDB()
        with patch("api.consultation_public.intake_enabled",return_value=True),\
             patch("api.consultation_public.intake_dependencies",return_value=("dsn","redis://cache","long-test-secret")),\
             patch("api.consultation_public.consultation_company_id",return_value=CID),\
             patch("api.consultation_public.redis.Redis.from_url",return_value=FakeCache()),\
             patch("api.consultation_public.allow_intake_request",return_value=True),\
             patch("api.consultation_public.psycopg.connect",return_value=db):
            response=TestClient(app).post("/api/v1/consultations",json=PAYLOAD,headers=HEADERS)
        self.assertEqual(response.status_code,201)
        self.assertTrue(response.json()["received"])
        self.assertEqual(len(db.calls),2)
        self.assertEqual(db.calls[1][1][1],CID)

    def test_rate_limit_exhaustion_prevents_database_open(self):
        with patch("api.consultation_public.intake_enabled",return_value=True),\
             patch("api.consultation_public.intake_dependencies",return_value=("dsn","redis://cache","long-test-secret")),\
             patch("api.consultation_public.consultation_company_id",return_value=CID),\
             patch("api.consultation_public.redis.Redis.from_url",return_value=FakeCache()),\
             patch("api.consultation_public.allow_intake_request",return_value=False),\
             patch("api.consultation_public.psycopg.connect",side_effect=AssertionError("DB should not open")):
            response=TestClient(app).post("/api/v1/consultations",json=PAYLOAD,headers=HEADERS)
        self.assertEqual(response.status_code,429)

    def test_public_cannot_choose_company(self):
        with patch("api.consultation_public.intake_enabled",return_value=True):
            response=TestClient(app).post("/api/v1/consultations",
                json={**PAYLOAD,"company_id":str(CID)},headers=HEADERS)
        self.assertEqual(response.status_code,400)
