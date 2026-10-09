import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ClientUIAssetsTests(unittest.TestCase):
    def test_live_directory_separate_from_demo(self):
        html=(ROOT/"web/clients.html").read_text()
        js=(ROOT/"web/clients.js").read_text()
        self.assertIn('id="company"',html)
        self.assertIn('id="client-rows"',html)
        self.assertIn('role="status"',html)
        self.assertIn('window.capitalBridgeIdentity',js)
        self.assertIn('/me/companies',js)
        self.assertIn('/clients?limit=100',js)
        self.assertIn('result.company_id !== company',js)
        self.assertIn('request !== version',js)
        self.assertIn('td.textContent =',js)
        self.assertNotIn('innerHTML',js)
        self.assertNotIn('localStorage',js)
        self.assertNotIn('demoClients',js)
    def test_ui_requires_real_identity_bridge(self):
        js=(ROOT/"web/clients.js").read_text()
        self.assertIn('typeof identity.getAccessToken !== "function"',js)
        self.assertIn('credentials: "same-origin"',js)
        self.assertIn('redirect: "error"',js)
        self.assertIn('companySelect.disabled = true',js)
if __name__=="__main__":
    unittest.main()
