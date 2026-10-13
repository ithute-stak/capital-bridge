import unittest
from unittest.mock import patch
from uuid import UUID
from fastapi import HTTPException
from api.consultations import ConsultationStatusChange, update_consultation_status


COMPANY=UUID("11111111-1111-4111-8111-111111111111")
ENQUIRY=UUID("22222222-2222-4222-8222-222222222222")
USER=UUID("33333333-3333-4333-8333-333333333333")


class FakeDb:
    def __init__(self, role="director", state="new"):
        self.role=role
        self.state=state
        self.statements=[]
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def transaction(self):return self
    def execute(self, query, params):
        self.statements.append((query,params))
        return self
    def fetchone(self):
        query=self.statements[-1][0]
        if "FROM cb.memberships" in query:return {"role":self.role}
        if "FROM cb.consultation_enquiries" in query:return {"status":self.state}
        return None


class ConsultationStatusTests(unittest.TestCase):
    def run_change(self, db, next_state):
        with patch("api.consultations.config",return_value=("iss","aud","jwks","dsn")), \
             patch("api.consultations.psycopg.connect",return_value=db), \
             patch("api.consultations.validate_company"):
            return update_consultation_status(COMPANY,ENQUIRY,ConsultationStatusChange(status=next_state),USER)

    def test_valid_transition_writes_audit_in_same_transaction(self):
        db=FakeDb()
        result=self.run_change(db,"in_review")
        self.assertEqual(result["status"],"in_review")
        self.assertEqual(len(db.statements),4)
        self.assertIn("UPDATE cb.consultation_enquiries",db.statements[2][0])
        self.assertIn("INSERT INTO cb.consultation_status_audit",db.statements[3][0])
        self.assertEqual(db.statements[3][1][-1],USER)

    def test_non_director_may_not_update(self):
        db=FakeDb(role="accountant")
        with self.assertRaises(HTTPException) as error:self.run_change(db,"in_review")
        self.assertEqual(error.exception.status_code,403)
        self.assertEqual(len(db.statements),1)

    def test_status_cannot_skip_or_reverse(self):
        for current,target in (("new","closed"),("responded","in_review"),("closed","in_review")):
            db=FakeDb(state=current)
            with self.subTest(current=current,target=target),self.assertRaises(HTTPException) as error:
                self.run_change(db,target)
            self.assertEqual(error.exception.status_code,409)
            self.assertEqual(len(db.statements),2)
