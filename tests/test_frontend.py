import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class FrontendChecks(unittest.TestCase):
    def test_assets_exist(self):
        for name in ("index.html", "landing.css", "landing.js", "finance.html", "styles.css", "app.js", "signin.html", "signin.js"):
            self.assertTrue((ROOT / "web" / name).is_file(), name)

    def test_public_home_has_staff_login_and_company_profile_sections(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="./signin.html"', html)
        for section in ("about", "services", "mobility", "approach", "contact"):
            self.assertIn('id="' + section + '"', html)
        for service in ("Business Consultancy", "Information", "Engineering", "Capacity Building",
                        "Business Support", "Global Mobility"):
            self.assertIn(service, html)
        self.assertIn("MN Immigration Services", html)
        self.assertIn("Company No. 102323", html)
        self.assertIn("Visa and immigration decisions", html)

    def test_demo_warning_preserved_on_separate_finance_page(self):
        html = (ROOT / "web" / "finance.html").read_text(encoding="utf-8")
        self.assertIn("DEMONSTRATION MODE", html)
        self.assertIn("EXAMPLE DATA", html)
        self.assertIn("not connected to a production database", html)

    def test_demo_navigation_preserved(self):
        html = (ROOT / "web" / "finance.html").read_text(encoding="utf-8")
        for section in ("overview", "quotations", "invoices", "receipts", "ledger"):
            self.assertIn('data-section="' + section + '"', html)

if __name__ == "__main__":
    unittest.main()
