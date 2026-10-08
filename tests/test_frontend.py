import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class FrontendChecks(unittest.TestCase):
    def test_assets_exist(self):
        for name in ("index.html", "styles.css", "app.js"):
            self.assertTrue((ROOT / "web" / name).is_file(), name)

    def test_demo_warning_visible(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("DEMONSTRATION MODE", html)
        self.assertIn("EXAMPLE DATA", html)
        self.assertIn("not connected to a production database", html)

    def test_navigation_targets_present(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        for section in ("overview", "quotations", "invoices", "receipts", "ledger"):
            self.assertIn('data-section="' + section + '"', html)

if __name__ == "__main__":
    unittest.main()
