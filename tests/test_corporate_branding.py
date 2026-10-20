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
                self.assertIn("capitalbridge-original-mark.png", (WEB / name).read_text())

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

    def test_client_back_link_labels_destination_correctly(self):
        clients = (WEB / "clients.html").read_text()
        self.assertIn('href="./index.html">← Public website</a>', clients)
        self.assertNotIn('href="./index.html">← Finance workspace</a>', clients)

    def test_public_navigation_targets_existing_sections(self):
        homepage = (WEB / "index.html").read_text()
        anchors = set(re.findall(r'id="([^"]+)"', homepage))
        for target in ("top", "about", "services", "mobility", "approach",
                       "consultation", "contact"):
            with self.subTest(anchor=target):
                self.assertIn(target, anchors)
                self.assertIn('href="#' + target + '"', homepage)

    def test_corporate_logo_asset_exists(self):
        self.assertTrue((WEB / "capitalbridge-original-mark.png").is_file())

    def test_company_profile_has_four_pillars(self):
        html = (WEB / "index.html").read_text()
        self.assertIn('id="company-profile"', html)
        match = re.search(r'<div class="profile-pillars">(.*?)</div>', html, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).count("<article>"), 4)


if __name__ == "__main__":
    unittest.main()
