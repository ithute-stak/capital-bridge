import pathlib
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
class QuotationFoundationChecks(unittest.TestCase):
    def test_company_scoped_foreign_keys_and_rls(self):
        sql=(ROOT/"db/migrations/008_client_quotations.sql").read_text()
        self.assertIn("FOREIGN KEY(company_id,client_id) REFERENCES cb.clients(company_id,id)",sql)
        self.assertIn("FOREIGN KEY(company_id,quotation_id) REFERENCES cb.quotations(company_id,id)",sql)
        self.assertIn("FORCE ROW LEVEL SECURITY",sql)
        self.assertIn("UNIQUE(company_id,quotation_number)",sql)
        self.assertIn("GENERATED ALWAYS AS",sql)
    def test_verified_brand_requirements(self):
        rules=(ROOT/"docs/official-pdf-design-standard.md").read_text()
        self.assertIn("official approved CapitalBridge logo",rules)
        self.assertIn("block final publication",rules)
        self.assertIn("SHA-256",rules)
        self.assertIn("A4 portrait",rules)
if __name__=="__main__": unittest.main()
