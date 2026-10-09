import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class IthuteSignInEntryTests(unittest.TestCase):
 def test_ithute_brand_and_no_password_form(self):
  html=(ROOT/"web/signin.html").read_text()
  self.assertIn("Sign in with Ithute Auth",html)
  self.assertNotIn('type="password"',html)
 def test_only_exact_server_gated_same_origin_start_path(self):
  js=(ROOT/"web/signin.js").read_text()
  self.assertIn('state.provider === "ithute"',js)
  self.assertIn('state.start_path === "/api/v1/oidc/start"',js)
  self.assertIn('window.location.assign("/api/v1/oidc/start")',js)
  self.assertNotIn("window.location.assign(state.start_path)",js)
  self.assertIn("button.disabled = true",js)
 def test_live_auth_still_disabled_server_side(self):
  main=(ROOT/"api/main.py").read_text()
  self.assertIn('"sign_in_available": False',main)

if __name__ == "__main__":
 unittest.main()
