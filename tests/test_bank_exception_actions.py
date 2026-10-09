import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app
from api.bank_exception_actions import ExceptionAction
class BankExceptionActionTests(unittest.TestCase):
 def test_status_and_note_validation(self):
  for status,note in (("open","enough notes"),("resolved","short"),("investigating","   ")):
   with self.subTest(status=status,note=note),self.assertRaises(ValueError):
    ExceptionAction.model_validate({"status":status,"note":note})
 def test_no_browser_actor_or_company_override(self):
  for key in ("company_id","actor_user_id","resolved_by"):
   with self.subTest(key=key),self.assertRaises(ValueError):
    ExceptionAction.model_validate({"status":"investigating","note":"Review bank evidence",key:"forged"})
 def test_unauthenticated_denied(self):
  r=TestClient(app).post(
   "/api/v1/companies/11111111-1111-4111-8111-111111111111/bank/exceptions/22222222-2222-4222-8222-222222222222/actions",
   json={"status":"investigating","note":"Investigate unmatched EFT"})
  self.assertEqual(r.status_code,401)
 def test_migration_has_company_isolation(self):
  sql=(Path(__file__).resolve().parents[1]/"db/migrations/015_bank_exception_actions.sql").read_text()
  self.assertIn("FORCE ROW LEVEL SECURITY",sql)
  self.assertIn("FOREIGN KEY(company_id,exception_id)",sql)
if __name__=="__main__":unittest.main()
