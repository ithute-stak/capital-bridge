import unittest
from pathlib import Path
from uuid import UUID
from fastapi.testclient import TestClient
from api.main import app
from api.receipt_pdf import OfficialReceipt,render_receipt_pdf

class ReceiptPdfTests(unittest.TestCase):
 def setUp(self):
  self.receipt=OfficialReceipt(number="CB-R-001",company="CapitalBridge Consultancy (Pty) Ltd",
   client="Test Client",payment_reference="PAY-001",payment_date="2026-10-09",
   issued_date="2026-10-09",payment_method="bank_transfer",amount_minor=18000,
   currency="LSL",journal_status="posted")
 def test_missing_logo_blocks_publication(self):
  with self.assertRaisesRegex(ValueError,"Approved CapitalBridge logo"):
   render_receipt_pdf(self.receipt,approved_logo_path=Path("/no-such-logo.png"))
 def test_unposted_journal_blocks_publication(self):
  x=OfficialReceipt(**{**self.receipt.__dict__,"journal_status":"draft"})
  with self.assertRaises(ValueError):
   render_receipt_pdf(x,approved_logo_path=Path("/no-such-logo.png"))
 def test_invalid_amount_blocks_publication(self):
  x=OfficialReceipt(**{**self.receipt.__dict__,"amount_minor":-50})
  with self.assertRaises(ValueError):
   render_receipt_pdf(x,approved_logo_path=Path("/no-such-logo.png"))
 def test_anonymous_download_denied(self):
  client=TestClient(app)
  response=client.get("/api/v1/companies/11111111-1111-4111-8111-111111111111/receipts/22222222-2222-4222-8222-222222222222/pdf")
  self.assertEqual(response.status_code,401)
if __name__=="__main__":unittest.main()
