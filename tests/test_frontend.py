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

    def test_mobile_bottom_navigation_is_accessible(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "web" / "landing.css").read_text(encoding="utf-8")
        js = (ROOT / "web" / "landing.js").read_text(encoding="utf-8")
        self.assertIn('aria-label="Mobile quick navigation"', html)
        self.assertIn('class="mobile-bottom-nav"', html)
        for target in ("#top", "#services", "#mobility", "#contact", "./signin.html"):
            self.assertIn('href="' + target + '"', html)
        self.assertIn("safe-area-inset-bottom", css)
        self.assertIn("@media(max-width:350px)", css)
        self.assertIn("aria-current", js)
        self.assertIn("IntersectionObserver", js)

    def test_consultation_enquiry_is_user_reviewed(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "web" / "consultation.js").read_text(encoding="utf-8")
        self.assertIn('id="consultation-form"', html)
        self.assertIn('href="#consultation"', html)
        self.assertIn('name="consent"', html)
        self.assertIn('name="service"', html)
        self.assertIn("mailto:tjlepekola@gmail.com", js)
        self.assertIn("this website has not submitted it", js)
        self.assertIn('online_submission_available !== true', js)
        self.assertIn('result.received !== true', js)
        self.assertNotIn("localStorage", js)

    def test_staff_enquiry_view_respects_identity_and_safe_rendering(self):
        html = (ROOT / "web" / "staff-enquiries.html").read_text(encoding="utf-8")
        js = (ROOT / "web" / "staff-enquiries.js").read_text(encoding="utf-8")
        css = (ROOT / "web" / "staff-enquiries.css").read_text(encoding="utf-8")
        self.assertIn("enquiry-company", html)
        self.assertIn("enquiry-rows", html)
        self.assertIn("getAccessToken", js)
        self.assertIn("encodeURIComponent(id)", js)
        self.assertIn("result.company_id!==id", js)
        self.assertIn("textContent", js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("localStorage", js)
        self.assertIn("@media(max-width:650px)", css)

    def test_director_status_actions_are_guarded(self):
        js = (ROOT / "web" / "staff-enquiries.js").read_text(encoding="utf-8")
        html = (ROOT / "web" / "staff-enquiries.html").read_text(encoding="utf-8")
        self.assertIn('roles.get(companyId)!=="director"', js)
        self.assertIn('roles.get(id)==="director"', js)
        self.assertIn('method:"PATCH"', js)
        self.assertIn("status:next", js)
        self.assertIn("forward={new:'in_review',in_review:'responded',responded:'closed'}", js)
        self.assertIn("<th>Action</th>", html)
        self.assertNotIn("innerHTML", js)

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
