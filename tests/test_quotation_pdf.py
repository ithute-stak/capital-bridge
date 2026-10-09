import tempfile
import unittest
from pathlib import Path

from api.quotation_pdf import ApprovedQuotation, QuotationLine, render_approved_quotation_pdf


def quotation(status="approved"):
    return ApprovedQuotation(
        reference="CB-Q-2026-001", company_name="CapitalBridge Consultancy (Pty) Ltd",
        client_name="Example Customer", issued_on="2026-10-09", valid_until="2026-10-31",
        currency="LSL", status=status, tax_minor=0,
        lines=(QuotationLine("Business advisory", 2, 35000),),
    )


class BackendQuotationPDFTests(unittest.TestCase):
    def test_logo_required_before_official_document(self):
        with self.assertRaisesRegex(ValueError, "approved CapitalBridge logo"):
            render_approved_quotation_pdf(
                quotation(), approved_logo_path=Path("/nonexistent/official-logo.png")
            )

    def test_draft_cannot_be_issued_even_with_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            logo = Path(tmp) / "logo.png"
            logo.write_bytes(b"not actually an image")
            with self.assertRaisesRegex(ValueError, "Only approved"):
                render_approved_quotation_pdf(quotation("draft"), approved_logo_path=logo)

    def test_negative_or_empty_lines_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            logo = Path(tmp) / "logo.png"
            logo.write_bytes(b"not actually an image")
            bad = ApprovedQuotation(**{
                **quotation().__dict__,
                "lines": (QuotationLine("service", -1, 100),),
            })
            with self.assertRaisesRegex(ValueError, "Invalid quotation item"):
                render_approved_quotation_pdf(bad, approved_logo_path=logo)

    def test_rendering_stays_in_backend(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "api/quotation_pdf.py").exists())
        client_js = (root / "web/clients.js").read_text()
        self.assertNotIn("jsPDF", client_js)
        self.assertNotIn("html2pdf", client_js)


if __name__ == "__main__":
    unittest.main()
