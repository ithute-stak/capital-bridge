"""Regression checks for public CapitalBridge branding and enquiry routing."""
from pathlib import Path
import re
import unittest

WEB = Path(__file__).resolve().parents[1] / "web"


class CorporateBrandingTests(unittest.TestCase):
    def test_public_pages_use_company_mark(self):
        for name in ("index.html", "signin.html", "finance.html",
                     "clients.html", "staff-enquiries.html"):
            with self.subTest(page=name):
                self.assertIn("capitalbridge-logo.svg", (WEB / name).read_text())

    def test_official_emails_are_displayed(self):
        homepage = (WEB / "index.html").read_text()
        self.assertIn("mailto:info@capitalbridge.co.ls", homepage)
        self.assertIn("mailto:tjlepekola@capitalbridge.co.ls", homepage)

    def test_consultation_fallback_uses_official_inbox(self):
        js = (WEB / "consultation.js").read_text()
        self.assertIn("mailto:info@capitalbridge.co.ls", js)
        self.assertIn("tjlepekola%40capitalbridge.co.ls", js)

    def test_old_personal_email_not_exposed_in_public_assets(self):
        for path in WEB.glob("*"):
            if path.suffix.lower() not in (".html", ".js", ".css", ".svg"):
                continue
            with self.subTest(file=path.name):
                self.assertNotIn("tjlepekola@gmail.com", path.read_text())

    def test_company_profile_has_four_pillars(self):
        html = (WEB / "index.html").read_text()
        self.assertIn('id="company-profile"', html)
        match = re.search(r'<div class="profile-pillars">(.*?)</div>', html, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).count("<article>"), 4)


if __name__ == "__main__":
    unittest.main()
