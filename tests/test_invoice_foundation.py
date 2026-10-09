import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
class InvoiceFoundationTests(unittest.TestCase):
 def test_invoice_ownership_and_company_links(self):
  sql=(ROOT/"db/migrations/010_invoices.sql").read_text()
  for value in (
   "FOREIGN KEY(company_id,client_id) REFERENCES cb.clients(company_id,id)",
   "FOREIGN KEY(company_id,quotation_id) REFERENCES cb.quotations(company_id,id)",
   "FOREIGN KEY(company_id,invoice_id) REFERENCES cb.invoices(company_id,id)",
   "UNIQUE(company_id,invoice_number)",
   "FORCE ROW LEVEL SECURITY",
   "GENERATED ALWAYS AS",
   "CHECK(due_on>=issued_on)",
  ):
   with self.subTest(value=value): self.assertIn(value,sql)
 def test_no_browser_pdf_generation(self):
  src=(ROOT/"docs/backend-pdf-architecture.md").read_text()
  self.assertIn("all official CapitalBridge ONE PDF bytes are composed by trusted backend services",src)
if __name__=="__main__":unittest.main()
