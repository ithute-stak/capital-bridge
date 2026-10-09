import unittest
from pathlib import Path
from uuid import UUID
from fastapi.testclient import TestClient
from api.invoice_pdf import IssuedInvoice,render_issued_invoice_pdf
from api.quotation_pdf import QuotationLine
from api.main import app

class InvoicePdfTests(unittest.TestCase):
    def setUp(self):
        self.invoice=IssuedInvoice(
            reference="CB-I-001",company_name="CapitalBridge Consultancy (Pty) Ltd",
            client_name="Example",issued_on="2026-10-09",due_on="2026-11-09",
            currency="LSL",status="issued",subtotal_minor=12500,tax_minor=0,
            lines=(QuotationLine("Consultancy",1,12500),))
    def test_draft_invoice_never_published(self):
        draft=IssuedInvoice(**{**self.invoice.__dict__,"status":"draft"})
        with self.assertRaisesRegex(ValueError,"Only issued"):
            render_issued_invoice_pdf(draft,approved_logo_path=Path("/missing/logo.png"))
    def test_unreconciled_invoice_never_published(self):
        invalid=IssuedInvoice(**{**self.invoice.__dict__,"subtotal_minor":1})
        with self.assertRaisesRegex(ValueError,"subtotal"):
            render_issued_invoice_pdf(invalid,approved_logo_path=Path("/missing/logo.png"))
    def test_missing_official_logo_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"approved CapitalBridge logo"):
            render_issued_invoice_pdf(self.invoice,approved_logo_path=Path("/missing/logo.png"))
    def test_anonymous_download_denied(self):
        c=TestClient(app)
        self.assertEqual(c.get("/api/v1/companies/11111111-1111-4111-8111-111111111111/invoices/22222222-2222-4222-8222-222222222222/pdf").status_code,401)
if __name__=="__main__":unittest.main()
